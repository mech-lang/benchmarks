"""Synthetic timing ledger plus retained small source metadata; no file phase."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

export=load('tested_scala_export',HERE/'scala_export.py')
synthetic=load('scala_export_ledger',HERE/'test_scala_reconcile.py')

def document(path):return json.loads(Path(path).read_bytes())

class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=synthetic.TEMPLATE_PLAN
        cls.work=document(plan['qualified_work']['path']);cls.counts=document(plan['qualified_source_counts']['path'])
        cls.metadata=document(export.RUNTIME_METADATA)
        cls.allowed=set(export.EXTRA_PINS)
        cls.allowed.add(cls.metadata['jdk_release_original']['path'])
        for row in plan['manifests'].values():
            for profile in row['profiles']:
                if profile['language']=='scala':
                    cls.allowed.update((profile['source'],profile['compiled_source']))

    def fixture(self,failure=None,failure_round=1,incomplete_failure=False):
        ledger=synthetic.fixture(failure,failure_round)
        if incomplete_failure:
            attempt=next(a for a in ledger['report']['attempts'] if not a['qualified'])
            attempt.update(error_type='TimeoutError',error='synthetic native deadline')
            for field in ('stdout_bytes','stdout_sha256','seconds','validation'):attempt.pop(field,None)
            ledger['report']['programs'][failure]['full_failure']=copy.deepcopy(attempt)
            ledger['raw'][attempt['result_path']]={k:copy.deepcopy(v) for k,v in attempt.items() if k not in synthetic.audit.p.SUPERVISOR_FIELDS}
            ledger['supervised'][attempt['supervisor_result_path']]=copy.deepcopy(attempt)
        review=synthetic.audit.reconcile(**ledger)
        self.synthetic_bytes={path:(json.dumps(value,sort_keys=True)+'\n').encode()
            for group in ('raw','supervised','outer') for path,value in ledger[group].items()}
        invented={path:hashlib.sha256(raw).hexdigest() for path,raw in self.synthetic_bytes.items()}
        review.update(status='full60-reconciled-awaiting-runtime-and-publication-review',file_integrity_verified=True,
            common_mutex_held=True,common_mutex_inode=synthetic.audit.p.LOCK_INODE,
            plan=dict(path=synthetic.PLAN,sha256=synthetic.SHA),
            report=dict(path='/synthetic/scala-export/report.json',sha256='f'*64),
            terminal=dict(path='/synthetic/scala-export/terminal.json',sha256='e'*64),
            verified_file_pins=dict(ledger['plan']['pins'],**{synthetic.PLAN:synthetic.SHA},**invented),
            source_evidence=dict(work=ledger['plan']['qualified_work'],counts=ledger['plan']['qualified_source_counts']))
        return dict(plan=ledger['plan'],review=review,work=copy.deepcopy(self.work),counts=copy.deepcopy(self.counts),
                    metadata=copy.deepcopy(self.metadata),read_raw=self.read_raw)

    def read_raw(self,path,digest):
        if path in self.synthetic_bytes:raw=self.synthetic_bytes[path]
        else:
            if path not in self.allowed:raise ValueError('Test refuses runtime or unplanned file: '+path)
            raw=Path(path).read_bytes()
            if len(raw)>1024*1024:raise ValueError('Unexpected large test input')
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Test input hash differs')
        return raw

    def build(self,**kwargs):return export.build_candidate(**self.fixture(**kwargs))

    def test_ten_real_sources_keep_complete_samples_and_counted_owner(self):
        value=self.build();self.assertEqual(len(value['program_inventory']),10)
        for bench in export.r.BENCHES:
            row=value['program_inventory'][bench+':scala-'+bench+'-jvm-v1']
            self.assertFalse(row['distinct_optimization_claimed'])
            self.assertIsNone(row['timing_alias_of']);self.assertIsNone(row['source_alias_of'])
            self.assertEqual(len(row['files']),1)
            self.assertEqual({v['role'] for v in row['file_roles'].values()},set(export.ROLES))
            self.assertEqual(row['loc'],sum(v['normalized_loc'] for v in row['file_roles'].values()))
            self.assertIsNone(row['formatted_loc']);self.assertFalse(row['formatted_loc_qualified'])
            self.assertEqual(len(row['samples']),3);self.assertEqual(row['seconds'],sorted(row['samples'])[1])
            endpoint=value['endpoint_proposals'][bench]
            self.assertEqual(endpoint['fast'],endpoint['small'])
            self.assertEqual(endpoint['programs'],[row['key']])

    def test_runtime_metadata_binds_jvm_flags_without_claiming_per_sample_probe(self):
        meta=self.build()['language_metadata']
        self.assertEqual(meta['platform'],'jvm');self.assertEqual(meta['execution'],['jit'])
        self.assertFalse(meta['observed_in_each_timed_process']);self.assertFalse(meta['gc_numeric_defaults_claimed'])
        self.assertIn('-XX:+UseG1GC',meta['runtime_policy']);self.assertIn('3.10.0',meta['runtime_policy'])

    def test_export_does_not_mutate_inputs_or_admit_chart(self):
        values=self.fixture();before=copy.deepcopy({k:v for k,v in values.items() if k!='read_raw'})
        out=export.build_candidate(**values)
        self.assertEqual(before,{k:v for k,v in values.items() if k!='read_raw'})
        self.assertFalse(out['chart_admission']);self.assertFalse(out['dataset_files_changed'])

    def test_unqualified_counts_runtime_mutation_and_incomplete_review_rejected(self):
        changes=[lambda x:x['counts'].update(formatted_loc=10),lambda x:x['counts'].update(canonical_loc_qualified=False),
            lambda x:x['metadata'].update(observed_in_each_timed_process=True),
            lambda x:x['review'].update(file_integrity_verified=False),lambda x:x['work'].update(source_work_qualified=False)]
        for change in changes:
            values=self.fixture();change(values)
            with self.subTest(change=change),self.assertRaises(ValueError):export.build_candidate(**values)

    def test_failed_subject_keeps_partial_samples_without_median(self):
        value=self.build(failure='scala-revcomp-jvm-v1',failure_round=3)
        row=value['program_inventory']['revcomp:scala-revcomp-jvm-v1']
        self.assertEqual(len(row['samples']),2);self.assertIsNone(row['seconds']);self.assertIsNone(row['timing_sd'])
        self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['time_ratio_to_matched_mech'])

    def test_failed_control_excludes_successful_subject_without_losing_samples(self):
        value=self.build(failure='revcomp:scala-full-study:mech-control',failure_round=2)
        row=value['program_inventory']['revcomp:scala-revcomp-jvm-v1']
        self.assertEqual(len(row['samples']),3);self.assertGreater(row['seconds'],0)
        self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['time_ratio_to_matched_mech'])

    def test_isolated_timeout_without_complete_output_fields_preserves_nulls(self):
        for failure in ('scala-revcomp-jvm-v1','revcomp:scala-full-study:mech-control'):
            value=self.build(failure=failure,incomplete_failure=True)
            subject=value['program_inventory']['revcomp:scala-revcomp-jvm-v1']
            row=subject if failure.startswith('scala-') else value['matched_mech_controls']['revcomp']
            receipt=next(s for s in row['sample_execution_metadata'] if not s['qualified'])
            for field in ('stdout_bytes','stdout_sha256','seconds','validation'):self.assertIsNone(receipt[field])
            self.assertFalse(subject['eligible_for_publication_review']);self.assertIsNone(subject['time_ratio_to_matched_mech'])

    def test_wrong_runtime_jar_and_source_identity_rejected(self):
        for change in (lambda x:x['metadata']['runtime_library_evidence'][0].update(sha256='0'*64),
                       lambda x:x['counts']['profiles'][0].update(source_sha256='0'*64)):
            values=self.fixture();change(values)
            with self.assertRaises(ValueError):export.build_candidate(**values)


class CandidateClosure(unittest.TestCase):
    def test_final_input_recheck_cannot_hide_candidate_mutation_or_replacement(self):
        import contextlib
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        Candidate.setUpClass();helper=Candidate();values=helper.fixture();fresh=values['review']
        for replace in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'candidate.json';saved=Path(directory)/'review.json'
                plan_path=Path(directory)/'plan.json';plan_path.write_text(json.dumps(values['plan']))
                saved.write_text(json.dumps(fresh));digest=hashlib.sha256(saved.read_bytes()).hexdigest()
                args=SimpleNamespace(plan=plan_path,plan_sha256=synthetic.SHA,
                    durable_directory=Path('/synthetic/closed'),reconciliation=saved,reconciliation_sha256=digest)
                @contextlib.contextmanager
                def context(*args,on_exit_failure,final_consumer_check):
                    yield fresh
                    if replace:
                        target.rename(target.with_suffix('.original'));target.write_bytes(b'external replacement')
                    else:target.write_bytes(b'external same-inode edit')
                    try:final_consumer_check()
                    except BaseException:
                        on_exit_failure();raise
                with patch.object(export.r,'review_files',context),patch.object(export,'build_candidate',return_value={'excluded_profiles':[]}):
                    with self.assertRaises(ValueError):export.save_candidate(args,target)
                self.assertEqual(target.read_bytes(),b'external replacement' if replace else b'external same-inode edit')

    def test_late_reconciliation_failure_removes_new_candidate_and_preserves_altered_bytes(self):
        import contextlib
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        Candidate.setUpClass();helper=Candidate();values=helper.fixture();fresh=values['review']
        for alter in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'candidate.json';saved=Path(directory)/'review.json'
                plan_path=Path(directory)/'plan.json';plan_path.write_text(json.dumps(values['plan']))
                saved.write_text(json.dumps(fresh));digest=hashlib.sha256(saved.read_bytes()).hexdigest()
                args=SimpleNamespace(plan=plan_path,plan_sha256=synthetic.SHA,
                    durable_directory=Path('/synthetic/closed'),reconciliation=saved,reconciliation_sha256=digest)
                @contextlib.contextmanager
                def context(*a,on_exit_failure=None,**kw):
                    yield fresh
                    if alter:target.write_bytes(b'altered external bytes')
                    on_exit_failure()
                    raise ValueError('late physical closure failure')
                with patch.object(export.r,'review_files',context),patch.object(export,'build_candidate',return_value={'excluded_profiles':[]}):
                    with self.assertRaises(ValueError):export.save_candidate(args,target)
                if alter:self.assertEqual(target.read_bytes(),b'altered external bytes')
                else:self.assertFalse(target.exists())

    def test_writer_fsync_failure_removes_owned_partial_or_complete_bytes(self):
        import tempfile
        from unittest.mock import patch
        for alter in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'candidate.json'
                def fail(_):
                    if alter:target.write_bytes(b'external replacement')
                    raise OSError('injected fsync failure')
                with patch.object(export.os,'fsync',fail),self.assertRaises(OSError):
                    export.write_new(target,{'status':'success'})
                if alter:self.assertEqual(target.read_bytes(),b'external replacement')
                else:self.assertFalse(target.exists())

    def test_publication_only_pin_failure_cleans_before_outer_context_exits(self):
        events=[]
        with self.assertRaisesRegex(ValueError,'metadata changed'):
            with export.guarded_closure(lambda:(_ for _ in ()).throw(ValueError('metadata changed')),
                                        lambda:events.append('cleanup')):
                events.append('written')
        self.assertEqual(events,['written','cleanup'])

if __name__=='__main__':unittest.main()
