"""Pure three-cohort publication tests; only the remaining50 ledger is synthetic.

Saved source/runtime metadata and the actual stopped9+31 receipts are read.
No native subject, full runtime closure hashing, or catalog mutation occurs.
"""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def load(file,name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


i=load('import_prolog_remaining.py','remaining_publication_tested')
e,m,n=i.e,i.m,i.l
f=load('test_prolog_remaining_reconcile.py','remaining_publication_fixture')
old_catalog=load('test_import_prolog_linear.py','remaining_catalog_fixture').catalog


def digest(raw):return hashlib.sha256(raw).hexdigest()

def document_bytes(path,value):
    if not Path(path).is_relative_to(Path(n.PACKET/'run-v1')):
        raw=Path(path).read_bytes()
        assert json.loads(raw)==value
        return raw
    return json.dumps(value).encode()


class Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan,cls.prior,cls.original=f.saved()
        cls.originals=old_catalog();cls.release=json.loads(i.RELEASE.read_bytes())
        cls.source_bytes={}
        for manifest in cls.plan['manifests'].values():
            for row in manifest['profiles'][:2]:
                for source in row['source_bundle']:
                    retained=e.retained_source(source,cls.original['plan'],cls.plan['pins'])
                    raw=Path(retained['path']).read_bytes()
                    assert digest(raw)==retained['sha256'];cls.source_bytes[retained['path']]=raw
        previous=cls.original['plan']
        reader=m.f.m.Evidence(dict(previous,pins=cls.plan['pins']),
            json.loads(Path(previous['storage_manifest']['path']).read_bytes()))
        cls.docs={};cls.raw={}
        def raw(path,expected=None):
            result=reader.raw(path,expected);cls.raw[path]=result;return result
        def document(path,expected=None):
            result=json.loads(raw(path,expected));cls.docs[path]=result;return result
        cls.outcome=document(previous['sealed_source_outcome']['path'],n.r.OUTCOME_SHA)
        args=f.fixture(cls.plan,cls.prior,cls.original);review=cls.review(args)
        cls.metadata=m.inspect(cls.plan,cls.prior['plan'],previous,review,cls.outcome,document,raw)

    @classmethod
    def review(cls,args):
        review=n.reconcile(**args)
        pins={**cls.plan['pins'],str(m.RECONCILER):m.RECONCILER_SHA,str(n.HELPER):n.HELPER_SHA,
              str(n.r.HELPER):n.r.HELPER_SHA}
        raw={}
        for prefix in ('raw','supervised','outer','old_raw','old_supervised','old_outer','prior_artifacts'):
            for path,value in args[prefix].items():
                value=document_bytes(path,value);raw[path]=value;pins[path]=digest(value)
        cohorts=n.cohort_refs(args['report'],args['terminal'],'2'*64)
        review.update(status='full50-plus-retained40-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,verified_file_pins=pins,cohorts=cohorts,
            plan=e.ref(str(n.PLAN),n.PLAN_SHA),report=cohorts['linear-remaining50']['report'],
            terminal=cohorts['linear-remaining50']['terminal'])
        return review

    def fixture(self,failure=None,failure_round=1):
        args=f.fixture(self.plan,self.prior,self.original,failure,failure_round)
        review=self.review(args);pins=review['verified_file_pins']
        raw=dict(self.source_bytes)
        for prefix in ('raw','supervised','outer','old_raw','old_supervised','old_outer','prior_artifacts'):
            raw.update({path:document_bytes(path,value) for path,value in args[prefix].items()})
        metadata=copy.deepcopy(self.metadata)
        metadata.update(status='qualified-recorded-runtime-metadata',file_integrity_verified=True,
            runtime_publication_metadata_qualified=True,plan=review['plan'],cohorts=review['cohorts'],
            verified_file_pins=dict(pins,**{str(e.METADATA):e.METADATA_SHA}))
        metadata['profiles']=[v for v in metadata['profiles'] if review['profiles'][v['key']]['full_workload_qualified']]
        for row in metadata['profiles']:row['timing']=copy.deepcopy(review['profiles'][row['key']])
        return dict(plan=copy.deepcopy(self.plan),prior=copy.deepcopy(self.prior['plan']),
            previous=copy.deepcopy(self.original['plan']),review=review,metadata=metadata,
            read_raw=lambda path,digest:raw[path]),raw

    def build(self,failure=None,failure_round=1):
        values,_=self.fixture(failure,failure_round);candidate=e.build_candidate(**values)
        refs={key:dict(path='experiments/prolog/full50-remaining-v1/'+key+'.json',sha256='a'*64)
              for key in ('candidate','metadata','reconciliation','release','import_controller')}
        prepared,audit=i.build_publication(self.originals,candidate,self.release,refs,values['plan'])
        return candidate,json.loads(prepared[i.TARGETS[0]]),audit,prepared

    def test_three_actual_cohorts_and_mixed_profile(self):
        candidate,data,audit,_=self.build()
        self.assertEqual(audit['reused_qualified_samples'],40)
        self.assertEqual(len(candidate['program_inventory']),20)
        self.assertEqual(candidate['actual_full_native_processes'],90)
        mixed=[row for row in data['program_inventory'].values() if len(row['attempt_cohorts'])>1]
        self.assertTrue(mixed)
        for row in mixed:
            self.assertEqual(set(row['attempt_cohorts']),{'linear-full81','linear-remaining50'})
            self.assertEqual(set(row['sample_producer_cohorts']),set(row['attempt_cohorts']))
            self.assertTrue(row['report'].endswith('full50-remaining-v1/reconciliation.json'))
            for sample in row['sample_execution_metadata']:
                self.assertEqual(sample['producer_status'],'stopped-unqualified' if sample['attempt_cohort']=='linear-full81' else 'complete')
        for cohort in ('original-full90','linear-full81'):
            self.assertEqual(data['prolog_audit']['cohorts'][cohort]['status'],'stopped-unqualified')

    def test_existing_catalog_values_and_baselines_unchanged(self):
        _,data,_,_=self.build();before=json.loads(self.originals[i.TARGETS[0]])
        for field in ('programs','program_inventory','files','archive_paths'):
            self.assertEqual({k:data[field][k] for k in before[field]},before[field])
        for old,new in zip(before['benchmarks'],data['benchmarks']):self.assertEqual(old,dict(new,groups=new['groups'][:-1]))
        self.assertEqual(data['formatted_reference_summary'],before['formatted_reference_summary'])
        self.assertEqual(data['untouched'],before['untouched'])
        for row in data['program_inventory'].values():
            self.assertIsNone(row['formatted_loc']);self.assertIsNone(row['formatted_x'])
            self.assertFalse(row['distinct_optimization_claimed'])
            self.assertIsNone(row['timing_alias_of'])

    def test_bad_cohort_routing_rejected(self):
        values,_=self.fixture();row=next(v for v in values['review']['profiles'].values()
                                       if len({x['cohort'] for x in v['sample_evidence']})>1)
        row['sample_evidence'][-1]['cohort']='linear-full81'
        with self.assertRaises(ValueError):e.build_candidate(**values)

    def test_stopped_producer_cannot_be_marked_complete(self):
        values,_=self.fixture();values['review']['cohorts']['linear-full81']['status']='complete'
        with self.assertRaises(ValueError):e.build_candidate(**values)

    def test_duplicate_cross_profile_sample_rejected(self):
        candidate,_,_,_=self.build();rows=list(candidate['program_inventory'].values())
        rows[1]['sample_execution_metadata'][0]['attempt']=rows[0]['sample_execution_metadata'][0]['attempt']
        with self.assertRaises(ValueError):i.validate_candidate(candidate)

    def test_cancelled_original_attempt_cannot_be_published(self):
        candidate,_,_,_=self.build();row=candidate['program_inventory']['regexredux:prolog-regexredux-compact']
        row['sample_execution_metadata'][0]['attempt']=10
        with self.assertRaises(ValueError):i.validate_candidate(candidate)

    def test_changed_supervisor_bytes_rejected(self):
        values,raw=self.fixture();sample=values['review']['profiles']['pidigits:prolog-pidigits-compact']['sample_evidence'][0]
        raw[sample['supervisor']]+=b'\n'
        with self.assertRaises(ValueError):e.build_candidate(**values)

    def test_failed_subject_retains_partial_samples_without_median(self):
        key='mandelbrot:prolog-mandelbrot-compact'
        candidate,data,audit,_=self.build(key,2)
        row=data['program_inventory'][key]
        self.assertTrue(any(s['attempt_cohort']=='linear-full81' for s in row['sample_execution_metadata']))
        self.assertFalse(row['eligible_for_chart']);self.assertIsNone(row['seconds']);self.assertIsNone(row['timing_sd'])
        self.assertEqual(row['failed_cohort'],'linear-remaining50')
        self.assertNotIn(key,data['programs']);self.assertIn(key,candidate['failed_profiles'])

    def test_failed_control_omits_whole_workload(self):
        _,data,audit,_=self.build('fasta:prolog-full-study:mech-control')
        self.assertNotIn('fasta',audit['admitted_workloads'])
        for row in data['program_inventory'].values():
            if row['benchmark']=='fasta':
                self.assertFalse(row['eligible_for_chart']);self.assertIsNone(row['time_ratio_to_matched_mech'])

    def test_unqualified_metadata_rejected(self):
        values,_=self.fixture();values['metadata']['runtime_publication_metadata_qualified']=False
        with self.assertRaises(ValueError):e.build_candidate(**values)

    def test_source_alias_and_compiler_input_preserved(self):
        candidate,_,_,_=self.build()
        for row in candidate['program_inventory'].values():
            self.assertEqual(set(row['files']),set(row['file_roles']))
            self.assertEqual(row['loc'],sum(role['normalized_loc'] for role in row['file_roles'].values()))
            if row['variant']=='optimized':
                base=candidate['program_inventory'][row['benchmark']+':'+row['source_alias_of']]
                self.assertEqual(row['source_sha256'],base['source_sha256'])


class FailureClosure(unittest.TestCase):
    def test_writer_failure_removes_owned_complete_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json'
            with patch.object(m.os,'fsync',side_effect=OSError('synthetic disk error')):
                with self.assertRaisesRegex(OSError,'disk error'):m.write_new(path,{'status':'success'})
            self.assertFalse(path.exists())

    def test_late_metadata_failure_removes_receipt_before_lease_release(self):
        events=[]
        @contextmanager
        def context(*args,**kwargs):
            events.append('held')
            try:
                yield {'status':'synthetic'}
                kwargs['on_exit_failure']();events.append('removed');raise ValueError('changed evidence')
            finally:events.append('released')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json'
            args=type('Args',(),dict(reconciliation=Path(directory)/'reconciliation.json',reconciliation_sha256='1'*64))()
            with patch.object(m,'review_context',context):
                with self.assertRaisesRegex(ValueError,'changed evidence'):m.save_metadata(args,path)
            self.assertFalse(path.exists());self.assertEqual(events,['held','removed','released'])

    def test_metadata_consumer_runs_after_outer_reconciler_final_check(self):
        events=[];review=dict(plan={},new_full_native_processes=50,cohorts={},prior_producer_statuses={},
                             verified_file_pins={'storage.json':'1'*64})
        previous=dict(storage_manifest=dict(path='storage.json'),sealed_source_outcome=dict(path='outcome.json'))
        class Files:
            def __init__(self):self.verified={}
            def verify(self,path,digest):self.verified[path]=digest
            def document(self,path,digest):
                self.verify(path,digest)
                if path==str(n.PLAN):return {'pins':{}}
                if path==str(n.PRIOR/'plan-v1.json'):return {}
                if path==str(n.l.OLD_REFS['plan'][0]):return previous
                if path=='storage.json':return {}
                return review
        class Evidence:
            read_pins={}
            def __init__(self,*args):pass
            def document(self,*args):return {}
            def raw(self,*args):return b''
        @contextmanager
        def context(**kwargs):
            events.append('held')
            try:
                yield review
                events.append('outer-final-check');kwargs['final_consumer_check']()
            finally:events.append('released')
        def consumer():
            self.assertNotIn('released',events);events.append('consumer')
        with patch.object(m.n,'review_context',context),patch.object(m.r,'Files',Files), \
             patch.object(m.f.m,'Evidence',Evidence),patch.object(m,'inspect',return_value={}):
            with m.review_context(n.PACKET/'synthetic-review.json','1'*64,final_consumer_check=consumer):
                events.append('body')
        self.assertEqual(events,['held','body','consumer','outer-final-check','consumer','released'])

    def test_export_late_check_failure_removes_candidate_while_held(self):
        events=[];fresh={'synthetic':True}
        @contextmanager
        def context(*args,**kwargs):
            events.append('held')
            try:
                yield fresh
                kwargs['on_exit_failure']();events.append('removed');raise ValueError('changed evidence')
            finally:events.append('released')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'candidate.json'
            args=type('Args',(),dict(reconciliation=Path(directory)/'reconciliation.json',reconciliation_sha256='1'*64,
                                   metadata=Path(directory)/'metadata.json',metadata_sha256='2'*64))()
            def checked(name,digest):return json.dumps(fresh if name==args.metadata else {}).encode()
            with patch.object(m,'review_context',context),patch.object(e,'checked',checked), \
                 patch.object(e,'reproduced_candidate',return_value={'status':'synthetic'}):
                with self.assertRaisesRegex(ValueError,'changed evidence'):e.save_candidate(args,path)
            self.assertFalse(path.exists());self.assertEqual(events,['held','removed','released'])

    def test_restore_all_owned_targets_even_when_one_was_edited(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old={name:('old '+name).encode() for name in i.TARGETS}
            new={name:('new '+name).encode() for name in i.TARGETS};journal=list(i.TARGETS)
            for name,raw in new.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            (root/i.TARGETS[-1]).write_bytes(b'external edit')
            with self.assertRaises(BaseExceptionGroup):i.restore_prepared(root,new,old,journal)
            for name in i.TARGETS[:-1]:self.assertEqual((root/name).read_bytes(),old[name])
            self.assertEqual((root/i.TARGETS[-1]).read_bytes(),b'external edit')
            self.assertEqual(journal,[i.TARGETS[-1]])


if __name__=='__main__':unittest.main()
