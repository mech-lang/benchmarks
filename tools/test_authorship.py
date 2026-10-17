"""Authorship is evidence metadata, independent of rankings and measurements."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit_authorship',Path(__file__).with_name('audit_authorship.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def fixture(url=None,local=None):
    code='// contributed by Example Contributor\nint main() { return 0; }\n';sha=hashlib.sha256(code.encode()).hexdigest()
    p=dict(key='test:p',id='p',language='test',benchmark='test',files=[sha],samples=[1,2,3],seconds=2)
    if url:p['source_url']=url
    if local is not None:p['local_adaptation']=local
    return {'programs':{'test:p':p},'files':{sha:{'code':code,'name':'main.c','path':'programs/test/main.c'}}}

class Authorship(unittest.TestCase):
    def test_published_source_preserves_author_and_does_not_claim_ai(self):
        data=fixture('https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/test-c-1.html')
        row=audit.audit(data,{})['test:p'];self.assertEqual(row['kind'],'upstream')
        self.assertEqual(row['ai']['status'],'not-applicable');self.assertIn('Example Contributor',row['attribution_notices'][0]['text'])
        self.assertEqual(row['license']['status'],'identified');self.assertEqual(row['license']['licenses'][0]['id'],'BSD-3-Clause')

    def test_workload_description_is_not_upstream_authorship_or_bsd_grant(self):
        data=fixture('https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/test.html',True)
        row=audit.audit(data,{})['test:p'];self.assertEqual(row['kind'],'ai-generated')
        self.assertEqual(row['sources'][0]['relationship'],'workload');self.assertEqual(row['ai']['models'],[])
        self.assertEqual([l['id'] for l in row['license']['licenses']],['Apache-2.0'])

    def test_unknown_upstream_license_stays_partial(self):
        row=audit.audit(fixture('https://example.test/source.c',True),{})['test:p']
        self.assertEqual(row['kind'],'ai-adapted');self.assertEqual(row['license']['status'],'partial')
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

    def test_real_inventory_complete_and_evidence_consistent(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text());catalog={**data.get('program_inventory',{}),**data['programs']}
        for key,p in catalog.items():
            a=p['authorship'];self.assertEqual(a['source_sha256'],p['files'],key)
            self.assertTrue(a['label']);self.assertIn(a['license']['status'],['identified','partial','unverified'])
            self.assertTrue(set(a['ai']['matched_source_files']).issubset(p['files']))
            for e in a['ai']['evidence']:self.assertIn(e['source_sha256'],p['files'])
            for path in a['evidence']:self.assertTrue((audit.ROOT/path).is_file(),path)
            for license in a['license']['licenses']:
                self.assertTrue((audit.ROOT/license['evidence']).is_file(),license['evidence'])
            self.assertNotIn('/Users/',json.dumps(a));self.assertNotIn('session_id',json.dumps(a))
        self.assertEqual(len(catalog),1013)

if __name__=='__main__':unittest.main()
