"""Authorship is evidence metadata, independent of rankings and measurements."""
import copy,hashlib,importlib,importlib.util,json,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import source_lineage
spec=importlib.util.spec_from_file_location('audit_authorship',Path(__file__).with_name('audit_authorship.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

# Exact admitted applications only: family identity is not a per-file model event.
# Each frozen importer binds the source, predecessor and admission receipts.
FAMILY_ADMISSIONS={
    'knucleotide:array-bqn-occurrence-frame':'qualification.import_bqn_knucleotide',
    'knucleotide:nim-knucleotide-preencoded-v1':'qualification.import_nim_knucleotide',
    'spectralnorm:array-bqn-native-sum':'qualification.import_bqn_spectral',
    'fasta:array-bqn-bins':'qualification.import_bqn_fasta',
}

def fixture(url=None,local=None):
    code='// contributed by Example Contributor\nint main() { return 0; }\n';sha=hashlib.sha256(code.encode()).hexdigest()
    p=dict(key='test:p',id='p',language='test',benchmark='test',files=[sha],samples=[1,2,3],seconds=2)
    if url:p['source_url']=url
    if local is not None:p['local_adaptation']=local
    return {'programs':{'test:p':p},'files':{sha:{'code':code,'name':'main.c','path':'programs/test/main.c'}}}

class Authorship(unittest.TestCase):
    def assert_bound_family_authorship(self,data,p):
        module_name=FAMILY_ADMISSIONS.get(p['key'])
        if module_name is None:return None
        module=importlib.import_module(module_name)
        self.assertEqual(p['key'],module.KEY)
        self.assertEqual(p['authorship'],module.bound_authorship(data,p,audit.ROOT))
        ai=p['authorship']['ai']
        self.assertEqual(ai['status'],'family-identified-exact-model-unverified')
        self.assertEqual(ai['model_family'],'Codex GPT-6')
        self.assertEqual(ai['models'],[]);self.assertIsNone(ai['exact_model'])
        self.assertEqual(ai['matched_source_files'],[module.SOURCE_SHA])
        pins=[dict(path=path,sha256=hashlib.sha256((audit.ROOT/path).read_bytes()).hexdigest())
              for path in (module.PLAN,module.RESULTS)]
        self.assertEqual(ai['evidence'],pins)
        self.assertEqual(p['source_provenance_record']['admission'],pins[1])
        return module

    def test_published_source_preserves_author_and_does_not_claim_ai(self):
        data=fixture('https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/test-c-1.html')
        row=audit.audit(data,{})['test:p'];self.assertEqual(row['kind'],'upstream')
        self.assertEqual(row['ai']['status'],'not-applicable');self.assertIn('Example Contributor',row['attribution_notices'][0]['text'])
        self.assertEqual(row['license']['status'],'identified');self.assertEqual(row['license']['licenses'][0]['id'],'BSD-3-Clause')

    def test_workload_description_is_not_upstream_authorship_or_bsd_grant(self):
        data=fixture('https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/test.html',True)
        row=audit.audit(data,{})['test:p'];self.assertEqual(row['kind'],'local-origin-unverified')
        self.assertEqual(row['sources'][0]['relationship'],'workload');self.assertEqual(row['ai']['models'],[])
        self.assertEqual([l['id'] for l in row['license']['licenses']],['Apache-2.0'])

    def test_unknown_upstream_license_stays_partial(self):
        row=audit.audit(fixture('https://example.test/source.c',True),{})['test:p']
        self.assertEqual(row['kind'],'local-origin-unverified');self.assertEqual(row['license']['status'],'partial')
        self.assertTrue(row['license']['unresolved'])

    def test_model_is_bound_to_exact_source_not_neighboring_profile(self):
        data=fixture(local=True);p=data['programs']['test:p'];sha=p['files'][0]
        models={sha:[{'model':'gpt-6-astra','source_sha256':sha,'tool_call_sha256':'a'*64}]}
        row=audit.audit(data,models)['test:p'];self.assertEqual(row['ai']['models'],['gpt-6-astra'])
        self.assertEqual(row['ai']['status'],'verified-source-writes')
        p['files'].append('helper');data['files']['helper']={'code':'void helper() {}','name':'helper.c','path':'helper.c'}
        row=audit.audit(data,models)['test:p'];self.assertEqual(row['ai']['status'],'partial-source-writes')
        self.assertEqual(audit.audit(data,{'different':models[sha]})['test:p']['ai']['models'],[])

    def test_audit_leaves_source_and_measurements_unchanged(self):
        data=fixture(local=True);before=copy.deepcopy(data);audit.audit(data,{})
        self.assertEqual(data,before)

    def test_new_retained_sources_can_use_their_own_immutable_revision(self):
        data=fixture('https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/test-c-1.html',True)
        data['archive_paths']={};data['programs']['test:p']['retained_source_revision']='b'*40
        with patch.object(audit,'retained_path',return_value='programs/test/main.c'):
            row=audit.audit(data,{})['test:p']
        self.assertIn('/blob/'+'b'*40+'/',row['retained_sources'][0]['url'])
        self.assertEqual(row['ai']['models'],[])

    def test_retained_revision_must_be_a_commit_hash(self):
        data=fixture();data['programs']['test:p']['retained_source_revision']='main'
        with self.assertRaisesRegex(ValueError,'Invalid retained-source revision'):
            audit.audit(data,{})

    def test_collection_and_secondary_workload_are_not_original_source(self):
        data=fixture('https://github.com/example/project/tree/main',True)
        data['programs']['test:p']['upstream_source_url']='https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/test.html'
        row=audit.audit(data,{})['test:p']
        self.assertEqual(row['origin_status'],'unresolved')
        self.assertEqual([r['relationship'] for r in row['sources']],['source collection','workload'])
        self.assertNotIn('BSD-3-Clause',[r['id'] for r in row['license']['licenses']])

    def test_specific_translation_lineage_and_retained_source_pins(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text());cat={**data['program_inventory'],**data['programs']}
        ts=cat['fasta:typescript-fasta-v1']['authorship']
        self.assertTrue(any('/program/fasta-node-1.html' in r['url'] for r in ts['sources']))
        scala=cat['fasta:scala-fasta-jvm-v1']['authorship']
        self.assertTrue(any('/program/fasta-graalvmaot-2.html' in r['url'] for r in scala['sources']))
        crystal=cat['fasta:crystal-fasta-compact']['authorship']
        self.assertTrue(any('/bench/algorithm/fasta/1.cr' in r['url'] and r.get('upstream_sha256') for r in crystal['sources']))
        pony=cat['mandelbrot:pony-mandelbrot-compact']['authorship']
        self.assertTrue(any('/mandelbrot/main.pony' in r['url'] and r.get('upstream_sha256') for r in pony['sources']))
        self.assertTrue(any('/mandelbrot/mandelbrot.pony' in r['url'] and r.get('upstream_sha256') for r in pony['sources']))
        self.assertEqual(pony['origin_status'],'cited')
        self.assertIn('BSD-2-Clause',[r['id'] for r in pony['license']['licenses']])
        self.assertEqual(cat['nbody:lean4-nbody-native-v1']['authorship']['parent_programs'],['nbody:typescript-nbody-v1'])
        changed=cat['nbody:nbody-fsharpcore-4-static-output-aot']['authorship']
        self.assertEqual(changed['kind'],'ai-adapted')
        self.assertTrue(any(s['url'].endswith('/program/nbody-fsharpcore-4.html') for s in changed['sources']))
        for p in cat.values():
            self.assertEqual({s['source_sha256'] for s in p['authorship']['retained_sources']},set(p['files']))
            family=self.assert_bound_family_authorship(data,p)
            for s in p['authorship']['retained_sources']:
                if family is not None and s['source_sha256']!=family.SOURCE_SHA:
                    parent=cat[family.PARENT]
                    self.assertIn(s,parent['authorship']['retained_sources'])
                    self.assertIn(s['source_sha256'],parent['files'])
                else:
                    self.assertIn('/blob/'+p.get('retained_source_revision',audit.SOURCE_REVISION)+'/',s['url'])
            for s in p['authorship']['sources']:
                if s['relationship']=='implementation':self.assertTrue(audit.exact_source(s['url']),s)

    def test_real_inventory_complete_and_evidence_consistent(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text());catalog={**data.get('program_inventory',{}),**data['programs']}
        for key,p in catalog.items():
            a=p['authorship'];self.assertEqual(a['source_sha256'],p['files'],key)
            self.assertTrue(a['label']);self.assertIn(a['license']['status'],['identified','partial','unverified'])
            self.assertTrue(set(a['ai']['matched_source_files']).issubset(p['files']))
            if self.assert_bound_family_authorship(data,p) is None:
                for e in a['ai']['evidence']:self.assertIn(e['source_sha256'],p['files'])
            for path in a['evidence']:self.assertTrue((audit.ROOT/path).is_file(),path)
            for license in a['license']['licenses']:
                self.assertTrue((audit.ROOT/license['evidence']).is_file(),license['evidence'])
            self.assertNotIn('/Users/',json.dumps(a));self.assertNotIn('session_id',json.dumps(a))
        self.assertGreaterEqual(len(catalog),1013)

    def test_family_admission_compatibility_rejects_changed_evidence_and_source(self):
        original=json.loads((audit.ROOT/'data/benchmarks.json').read_text())
        for key in FAMILY_ADMISSIONS:
            with self.subTest(key=key,change='evidence'):
                data=copy.deepcopy(original);p={**data['program_inventory'],**data['programs']}[key]
                p['authorship']['ai']['evidence'][0]['sha256']='0'*64
                with self.assertRaises(AssertionError):self.assert_bound_family_authorship(data,p)
            with self.subTest(key=key,change='source'):
                data=copy.deepcopy(original);p={**data['program_inventory'],**data['programs']}[key]
                p['source_provenance_record']['source_sha256']='0'*64
                with self.assertRaises(ValueError):self.assert_bound_family_authorship(data,p)
        self.assertIsNone(self.assert_bound_family_authorship({},fixture()['programs']['test:p']))

    def test_explicit_prolog_predecessors_require_matching_source_bytes(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text())
        parents,_,evidence=audit.lineage(data)
        self.assertEqual(parents['fasta:prolog-fasta-compact'],['fasta:nim-fasta-compact'])
        self.assertEqual(parents['fasta:prolog-fasta-optimized'],['fasta:nim-fasta-compact'])
        self.assertNotIn('binarytrees:prolog-binarytrees-compact',parents)
        self.assertIn('archive/languages/prolog/20261013/PROVENANCE.md',evidence['fasta:prolog-fasta-compact'])
        data['programs']['fasta:nim-fasta-compact']['files']=['0'*64]
        data['program_inventory'].pop('fasta:nim-fasta-compact',None)
        self.assertNotIn('fasta:prolog-fasta-compact',audit.lineage(data)[0])
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text())
        catalog={**data['program_inventory'],**data['programs']}
        self.assertEqual(catalog['fasta:prolog-fasta-compact']['authorship']['origin_status'],'unresolved')
        self.assertIn('local predecessor',catalog['fasta:prolog-fasta-compact']['authorship']['label'])
        catalog['fasta:prolog-fasta-compact']['files']=['0'*64]
        self.assertNotIn('fasta:prolog-fasta-compact',audit.lineage(data)[0])

    def test_changed_origin_document_cannot_establish_predecessors(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text())
        original_read=source_lineage.read
        def changed(path):
            result=original_read(path)
            if path=='data/source-predecessor-evidence.json':
                next(iter(result['programs'].values()))['evidence']['sha256']='0'*64
            return result
        with patch.object(source_lineage,'read',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'Source-predecessor evidence changed'):
                audit.lineage(data)

    def test_specific_mojo_sources_preserve_declared_earlier_reference(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text())
        _,references,_=audit.lineage(data)
        nbody=references['nbody:mojo-nbody-compact']
        self.assertTrue(any(r['url'].endswith('/n_body_mojo/n_body.mojo') and r['upstream_sha256'] for r in nbody))
        spectral=references['spectralnorm:mojo-spectralnorm-small']
        earlier=next(r for r in spectral if r['url'].endswith('/program/spectralnorm-python3-6.html'))
        self.assertIn('spectral_norm.mojo',earlier['via_source'])
        self.assertIn('declaration_evidence',earlier);self.assertNotIn('upstream_sha256',earlier)
        self.assertNotIn('spectralnorm:mojo-spectralnorm',references)

if __name__=='__main__':unittest.main()
