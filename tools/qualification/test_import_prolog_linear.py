"""Pure publication transforms and temporary-file rollback; no live cohort reads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def load(file,name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


i=load('import_prolog_linear.py','tested_prolog_import')
f=load('test_prolog_linear_export.py','prolog_import_fixture')


def catalog():
    source='old program\n';digest=hashlib.sha256(source.encode()).hexdigest();benches=[];programs={}
    language=dict(key='mech',label='Mech',family='mech')
    for name in i.r.BENCHES:
        key=name+':old-mech';programs[key]=dict(key=key,id='old-mech',language='mech',benchmark=name,
            loc=10,seconds=2,samples=[1,2,3],files=[digest],x=1,y=20)
        benches.append(dict(key=name,title=name,workload='saved',baseline_loc=10,baseline_formatted_loc=20,
            baseline_seconds=0.1,groups=[dict(language='mech',label='Mech',programs=[key],fast=key,small=key)]))
    data=dict(repository=dict(url='https://example.test/repo'),languages=[language],benchmarks=benches,
        programs=programs,program_inventory={},files={digest:dict(sha256=digest,code=source,name='old.mech',
            path='old/main.mech',archive_path='archive/old/main.mech')},archive_paths={'old/main.mech':'archive/old/main.mech'},
        reference_summary=[dict(lang='mech',label='Mech')],formatted_reference_summary=[dict(lang='mech',label='Mech',
            fast=dict(x=2,y=20),small=dict(x=2,y=20))],protocol={'old':'preserve'},
        language_groups=[dict(key=k,languages=['mech'] if k=='aot' else []) for k in ('aot','interpreted','dynamic')],
        untouched={'nested':[1,None,False]})
    metadata=dict(platform='native',runtime='Mech',execution=['aot'],typing='static',style=['functional'],
        memory=['rc'],note='existing',sources=['https://example.test'])
    originals={name:(json.dumps(value)+'\n').encode() for name,value in zip(i.TARGETS,(data,
        dict(languages={'mech':metadata},scope='old scope',audited_on='2026-01-01')))}
    originals[i.TARGETS[2]]=('// Preserved taxonomy\nexport const languageMetadata = '+json.dumps({'mech':metadata})+';\n').encode()
    return originals


class Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f.Candidate.setUpClass();cls.originals=catalog();cls.release=json.loads(i.RELEASE.read_bytes())

    def candidate(self,*args,**kwargs):
        values,_=f.Candidate().fixture(*args,**kwargs);return i.e.build_candidate(**values),values['plan']

    def build(self,*args,**kwargs):
        candidate,plan=self.candidate(*args,**kwargs)
        refs={name:dict(path='experiments/prolog/full81-linear-v1/'+name+'.json',sha256='a'*64)
              for name in ('candidate','reconciliation','metadata','release','import_controller')}
        prepared,audit=i.build_publication(self.originals,candidate,self.release,refs,plan)
        return json.loads(prepared[i.TARGETS[0]]),audit,candidate,prepared

    def test_exact_inventory_selected_endpoints_and_canonical_only(self):
        data,audit,_,_=self.build()
        self.assertEqual(len(data['program_inventory']),20);self.assertEqual(audit['imported_program_inventory'],20)
        self.assertEqual(len(audit['admitted_workloads']),10)
        for bench in data['benchmarks']:
            group=next(x for x in bench['groups'] if x['language']=='prolog')
            self.assertEqual(set(group['programs']),{group['fast'],group['small']})
            self.assertIsNone(group['formatted_fast']);self.assertIsNone(group['formatted_small'])
        for row in data['program_inventory'].values():
            self.assertIsNone(row['formatted_loc']);self.assertIsNone(row['formatted_x'])
            self.assertIn('timing_sd',row['publication_record'])

    def test_prior_values_baselines_and_formatted_summary_unchanged(self):
        old=json.loads(self.originals[i.TARGETS[0]]);data,_,_,_=self.build()
        for field in ('programs','program_inventory','files','archive_paths'):
            self.assertEqual({k:data[field][k] for k in old[field]},old[field])
        for a,b in zip(old['benchmarks'],data['benchmarks']):self.assertEqual(a,dict(b,groups=b['groups'][:-1]))
        self.assertEqual(data['formatted_reference_summary'],old['formatted_reference_summary'])
        self.assertEqual(data['untouched'],old['untouched']);self.assertEqual(data['protocol']['old'],'preserve')

    def test_per_sample_original_producer_links(self):
        data,_,_,_=self.build()
        for row in data['program_inventory'].values():
            old=row['benchmark']=='regexredux';prefix='experiments/prolog/full90-v1/' if old else 'experiments/prolog/full81-linear-v1/'
            self.assertTrue(row['report'].startswith(prefix))
            for sample in row['sample_execution_metadata']:
                self.assertTrue(sample['producer_report']['path'].startswith(prefix))
                self.assertFalse(Path(sample['raw_evidence']['path']).is_absolute())
        self.assertNotIn('revcomp:prolog-revcomp-compact',data['program_inventory'])

    def test_failed_subject_without_output_is_inventory_only(self):
        key='pidigits:prolog-pidigits-compact';data,_,_,_=self.build(key,True)
        row=data['program_inventory'][key]
        self.assertNotIn(key,data['programs']);self.assertFalse(row['eligible_for_chart'])
        self.assertIsNone(row['seconds']);self.assertIsNone(row['publication_record']['timing_sd'])
        self.assertIsNone(row['sample_execution_metadata'][0]['stdout_sha256'])

    def test_failed_control_omits_whole_workload_group(self):
        data,audit,_,_=self.build('pidigits:prolog-full-study:mech-control',True)
        bench=next(b for b in data['benchmarks'] if b['key']=='pidigits')
        self.assertFalse(any(g['language']=='prolog' for g in bench['groups']))
        self.assertNotIn('pidigits',audit['admitted_workloads'])

    def test_new_minimum_requires_separate_review(self):
        candidate,plan=self.candidate();originals=copy.deepcopy(self.originals)
        data=json.loads(originals[i.TARGETS[0]]);data['benchmarks'][0]['baseline_seconds']=1e9
        originals[i.TARGETS[0]]=json.dumps(data).encode()
        with self.assertRaises(ValueError):i.build_publication(originals,candidate,self.release,{},plan)

    def test_duplicate_admission_rejected(self):
        _,_,candidate,prepared=self.build();_,plan=self.candidate()
        with self.assertRaises(ValueError):i.build_publication(prepared,candidate,self.release,{},plan)

    def test_cancelled_sample_cannot_become_preserved_timing(self):
        candidate,_=self.candidate();row=candidate['program_inventory']['regexredux:prolog-regexredux-compact']
        row['sample_execution_metadata'][0]['attempt']=10
        with self.assertRaises(ValueError):i.validate_candidate(candidate)

    def test_formatted_count_invention_rejected(self):
        candidate,_=self.candidate();next(iter(candidate['program_inventory'].values()))['formatted_loc']=1
        with self.assertRaises(ValueError):i.validate_candidate(candidate)

    def test_candidate_inputs_not_mutated(self):
        candidate,plan=self.candidate();before=copy.deepcopy((candidate,plan))
        refs={name:dict(path='review/'+name+'.json',sha256='a'*64)
              for name in ('candidate','reconciliation','metadata','release','import_controller')}
        i.build_publication(self.originals,candidate,self.release,refs,plan)
        self.assertEqual((candidate,plan),before)

    def test_logic_group_added_without_changing_existing_members(self):
        old=json.loads(self.originals[i.TARGETS[0]]);data,_,_,_=self.build()
        self.assertEqual(data['language_groups'][-1],dict(key='logic',label='Logic',languages=['prolog']))
        for a,b in zip(old['language_groups'],data['language_groups']):
            self.assertEqual(a,dict(b,languages=[x for x in b['languages'] if x!='prolog']))


class Replacement(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.originals={name:('old '+name).encode() for name in i.TARGETS}
        self.prepared={name:('new '+name).encode() for name in i.TARGETS}
        self.pins={name:i.sha(raw) for name,raw in self.originals.items()};self.journal=[]
        for name,raw in self.originals.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)

    def test_three_file_replace_then_restore(self):
        i.apply_prepared(self.root,self.prepared,self.originals,self.pins,lambda:None,self.journal)
        self.assertEqual(self.journal,list(i.TARGETS))
        i.restore_prepared(self.root,self.prepared,self.originals,self.journal)
        self.assertEqual(self.journal,[])
        for name,raw in self.originals.items():self.assertEqual((self.root/name).read_bytes(),raw)

    def test_failure_after_first_replacement_restores_exact_originals(self):
        def verify():
            if self.journal:raise ValueError('injected evidence change')
        with self.assertRaises(ValueError):i.apply_prepared(self.root,self.prepared,self.originals,self.pins,verify,self.journal)
        self.assertEqual(self.journal,[])
        for name,raw in self.originals.items():self.assertEqual((self.root/name).read_bytes(),raw)

    def test_context_exit_failure_restores_prepared_targets(self):
        def recheck():raise ValueError('late evidence change')
        def restore():i.restore_prepared(self.root,self.prepared,self.originals,self.journal)
        with self.assertRaises(ValueError):
            with i.m._yield_verified({},recheck,restore):
                i.apply_prepared(self.root,self.prepared,self.originals,self.pins,lambda:None,self.journal)
        for name,raw in self.originals.items():self.assertEqual((self.root/name).read_bytes(),raw)

    def test_third_party_target_is_not_overwritten_on_restore(self):
        i.apply_prepared(self.root,self.prepared,self.originals,self.pins,lambda:None,self.journal)
        name=i.TARGETS[-1];(self.root/name).write_bytes(b'unrelated changed bytes')
        with self.assertRaises(ValueError):i.restore_prepared(self.root,self.prepared,self.originals,self.journal)
        self.assertEqual((self.root/name).read_bytes(),b'unrelated changed bytes')

    def test_changed_earlier_target_cannot_pass_later_apply_verify(self):
        def verify():
            if self.journal:
                name=self.journal[0];(self.root/name).write_bytes(self.originals[name])
        with self.assertRaisesRegex(ValueError,'Prepared publication target changed'):
            i.apply_prepared(self.root,self.prepared,self.originals,self.pins,verify,self.journal)
        for name,raw in self.originals.items():self.assertEqual((self.root/name).read_bytes(),raw)

    def test_target_mutation_during_final_evidence_check_restores(self):
        def recheck():
            name=i.TARGETS[0];(self.root/name).write_bytes(self.originals[name])
        def restore():i.restore_prepared(self.root,self.prepared,self.originals,self.journal)
        def consumer():i.verify_written(self.root,self.prepared,self.journal)
        with self.assertRaisesRegex(ValueError,'Prepared publication target changed'):
            with i.m._yield_verified({},recheck,restore,consumer):
                i.apply_prepared(self.root,self.prepared,self.originals,self.pins,lambda:None,self.journal)
        for name,raw in self.originals.items():self.assertEqual((self.root/name).read_bytes(),raw)

    def test_preexisting_temporary_file_is_never_deleted(self):
        path=self.root/i.TARGETS[0];temporary=path.with_name(path.name+'.prolog-linear-import.tmp')
        temporary.write_bytes(b'preexisting unrelated temporary')
        with self.assertRaises(FileExistsError):i.replace_bytes(path,b'new bytes','.prolog-linear-import.tmp')
        self.assertEqual(path.read_bytes(),self.originals[i.TARGETS[0]])
        self.assertEqual(temporary.read_bytes(),b'preexisting unrelated temporary')


if __name__=='__main__':unittest.main()
