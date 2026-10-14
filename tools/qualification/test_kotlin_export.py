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

export=load('tested_kotlin_export',HERE/'kotlin_export.py')
synthetic=load('kotlin_export_ledger',HERE/'test_kotlin_reconcile.py')

def document(path):return json.loads(Path(path).read_bytes())

class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=synthetic.SAVED_PLAN
        cls.work=document(plan['qualified_work']['path']);cls.counts=document(plan['qualified_source_counts']['path'])
        cls.metadata=document(export.RUNTIME_METADATA)
        cls.allowed=set(export.EXTRA_PINS)
        for key in ('compiler_version_evidence','jdk_release_evidence','jdk_release_original'):
            cls.allowed.add(cls.metadata[key]['path'])
        cls.allowed.update(str(export.SOURCE_ROOT/identity/'source.kt') for identity in cls.counts['files'])

    def fixture(self,failure=None,failure_round=1):
        ledger=synthetic.fixture(failure,failure_round);review=synthetic.audit.reconcile(**ledger)
        self.synthetic_bytes={path:(json.dumps(value,sort_keys=True)+'\n').encode()
            for group in ('raw','supervised','outer') for path,value in ledger[group].items()}
        invented={path:hashlib.sha256(raw).hexdigest() for path,raw in self.synthetic_bytes.items()}
        review.update(status='full90-reconciled-awaiting-runtime-and-publication-review',file_integrity_verified=True,
            common_mutex_held=True,common_mutex_inode=synthetic.audit.p.LOCK_INODE,
            plan=dict(path=synthetic.PLAN,sha256=synthetic.audit.PLAN_SHA),
            report=dict(path='/synthetic/kotlin-export/report.json',sha256='f'*64),
            terminal=dict(path='/synthetic/kotlin-export/terminal.json',sha256='e'*64),
            verified_file_pins=dict(ledger['plan']['pins'],**{synthetic.PLAN:synthetic.audit.PLAN_SHA},**invented),
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

    def test_twenty_alias_forms_keep_independent_samples_and_two_counted_roles(self):
        value=self.build();self.assertEqual(len(value['program_inventory']),20)
        for bench in export.r.BENCHES:
            a,b=[value['program_inventory'][bench+':kotlin-'+bench+'-'+v] for v in ('compact','optimized')]
            self.assertEqual(a['files'],b['files']);self.assertNotEqual(a['sample_execution_metadata'],b['sample_execution_metadata'])
            for row in (a,b):
                self.assertFalse(row['distinct_optimization_claimed']);self.assertIsNone(row['timing_alias_of'])
                self.assertEqual(len(row['files']),2);self.assertEqual({v['role'] for v in row['file_roles'].values()},set(export.ROLES))
                self.assertEqual(row['loc'],sum(v['normalized_loc'] for v in row['file_roles'].values()))
                self.assertIsNone(row['formatted_loc']);self.assertFalse(row['formatted_loc_qualified'])
                self.assertEqual(len(row['samples']),3);self.assertEqual(row['seconds'],sorted(row['samples'])[1])

    def test_runtime_metadata_binds_jvm_flags_without_claiming_per_sample_probe(self):
        meta=self.build()['language_metadata']
        self.assertEqual(meta['platform'],'jvm');self.assertEqual(meta['execution'],['jit'])
        self.assertFalse(meta['observed_in_each_timed_process']);self.assertFalse(meta['gc_numeric_defaults_claimed'])
        self.assertIn('-XX:+UseG1GC',meta['runtime_policy']);self.assertIn('2.4.21',meta['runtime_policy'])

    def test_export_does_not_mutate_inputs_or_admit_chart(self):
        values=self.fixture();before=copy.deepcopy({k:v for k,v in values.items() if k!='read_raw'})
        out=export.build_candidate(**values)
        self.assertEqual(before,{k:v for k,v in values.items() if k!='read_raw'})
        self.assertFalse(out['chart_admission']);self.assertFalse(out['dataset_files_changed'])

    def test_unqualified_counts_runtime_mutation_and_incomplete_review_rejected(self):
        changes=[lambda x:x['counts'].update(formatted_loc=10),lambda x:x['counts'].update(canonical_loc_qualified=False),
            lambda x:x['metadata'].update(observed_in_each_timed_process=True),
            lambda x:x['review'].update(file_integrity_verified=False),lambda x:x['work']['profiles'][0].update(source_work_qualified=False)]
        for change in changes:
            values=self.fixture();change(values)
            with self.subTest(change=change),self.assertRaises(ValueError):export.build_candidate(**values)

    def test_failed_subject_keeps_partial_samples_without_median(self):
        value=self.build(failure='kotlin-revcomp-compact',failure_round=3)
        row=value['program_inventory']['revcomp:kotlin-revcomp-compact']
        self.assertEqual(len(row['samples']),2);self.assertIsNone(row['seconds']);self.assertIsNone(row['timing_sd'])
        self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['time_ratio_to_matched_mech'])

    def test_failed_control_excludes_successful_subject_without_losing_samples(self):
        value=self.build(failure='revcomp:kotlin-full-study:mech-control',failure_round=2)
        for variant in ('compact','optimized'):
            row=value['program_inventory']['revcomp:kotlin-revcomp-'+variant]
            self.assertEqual(len(row['samples']),3);self.assertGreater(row['seconds'],0)
            self.assertFalse(row['eligible_for_publication_review']);self.assertIsNone(row['time_ratio_to_matched_mech'])


class CandidateClosure(unittest.TestCase):
    def test_late_reconciliation_failure_removes_new_candidate_and_preserves_altered_bytes(self):
        import contextlib
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        Candidate.setUpClass();helper=Candidate();values=helper.fixture();fresh=values['review']
        for alter in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'candidate.json';saved=Path(directory)/'review.json'
                saved.write_text(json.dumps(fresh));digest=hashlib.sha256(saved.read_bytes()).hexdigest()
                args=SimpleNamespace(plan=Path(synthetic.PLAN),plan_sha256=synthetic.audit.PLAN_SHA,
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
