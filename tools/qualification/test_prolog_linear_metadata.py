"""Saved metadata and synthetic future-ledger tests; no runtime hashes or native work."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import unittest


def load(file,name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


m=load('prolog_linear_metadata.py','tested_linear_metadata')
t=load('test_prolog_linear_reconcile.py','synthetic_linear_ledger')


class Metadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads(m.l.PLAN.read_bytes())
        cls.previous={key:json.loads(path.read_bytes()) for key,(path,_) in m.l.OLD_REFS.items()}
        cls.args=t.fixture(cls.plan,cls.previous)
        cls.reconciliation=m.l.reconcile(**cls.args)
        cls.reconciliation.update(
            status='full81-plus-retained9-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,plan=dict(path=str(m.l.PLAN),sha256=m.l.PLAN_SHA),
            verified_file_pins={**cls.plan['pins'],str(m.RECONCILER):m.RECONCILER_SHA,
                str(m.l.RECONCILER):m.l.RECONCILER_SHA,str(m.r.HELPER):m.r.HELPER_SHA})
        previous=cls.previous['plan']
        reader=m.m.Evidence(dict(previous,pins=cls.plan['pins']),
            json.loads(Path(previous['storage_manifest']['path']).read_bytes()))
        cls.bytes={};cls.docs={}
        def raw(path,expected=None):
            # Only the small metadata actually requested by semantic review;
            # no runtime binaries, full closure hashing, or native invocation.
            data=reader.raw(path,expected);cls.bytes[path]=data;return data
        def doc(path,expected=None):
            data=json.loads(raw(path,expected));cls.docs[path]=data;return data
        cls.outcome=doc(previous['sealed_source_outcome']['path'],m.r.OUTCOME_SHA)
        cls.result=m.inspect(cls.plan,previous,cls.reconciliation,cls.outcome,doc,raw)

    def setUp(self):
        self.data=copy.deepcopy((self.plan,self.previous['plan'],self.reconciliation,self.outcome,self.docs,self.bytes))

    def inspect(self):
        plan,previous,reconciliation,outcome,docs,raw=self.data
        return m.inspect(plan,previous,reconciliation,outcome,
            lambda path,expected=None:docs[path],lambda path,expected=None:raw[path])

    def rejects(self):
        with self.assertRaises((AssertionError,ValueError,KeyError)):self.inspect()

    def test_all20_saved_metadata_synthetic_future_timings(self):
        result=self.inspect()
        self.assertEqual(len(result['profiles']),20)
        self.assertEqual(result['excluded_profiles'],[])
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['file_integrity_verified'])
        self.assertFalse(result['runtime_publication_metadata_qualified'])
        rows={x['id']:x for x in result['profiles']}
        row=rows['prolog-revcomp-linear-optimized']
        self.assertEqual(row['source_alias_of'],'prolog-revcomp-linear-compact')
        self.assertEqual((row['canonical_loc'],row['physical_loc']),(242,146))
        self.assertEqual(len(row['qlf_artifact_pins']),1)
        self.assertEqual(row['declared_vendor_libraries'],[])
        self.assertEqual(rows['prolog-regexredux-compact']['timing']['attempt_cohort'],'preserved-full90')
        self.assertEqual(row['timing']['attempt_cohort'],'linear-full81')

    def test_draft_reconciliation_rejected(self):
        self.data[2]['file_integrity_verified']=False;self.rejects()

    def test_missing_reconciler_binding(self):
        del self.data[2]['verified_file_pins'][str(m.RECONCILER)];self.rejects()

    def test_changed_linear_alias(self):
        self.data[0]['manifests']['revcomp']['profiles'][1]['source_alias_of']=None;self.rejects()

    def test_runtime_gc_or_architecture_changed(self):
        config=self.data[4][m.CONFIG]
        self.data[4][config['actual_feature_probe']]['runtime']['gc']=False;self.rejects()

    def test_unbound_original_compiler_input(self):
        row=self.data[0]['manifests']['pidigits']['profiles'][0]
        self.data[4][row['compiler_bound_input_inventory']['path']]['source_sha256']='0'*64;self.rejects()

    def test_unknown_compiler_warning(self):
        path=str(m.l.LINEAR/'bounded-run-v1/compile/stderr.bin')
        self.data[5][path]+=b'Unrelated error\n';self.rejects()

    def test_compile_exit_one_is_not_expected_warning(self):
        path=str(m.l.LINEAR/'bounded-run-v1/compile/process.json')
        self.data[4][path]['exit_status']=1;self.rejects()

    def test_compiler_owner_birth_changed(self):
        path=str(m.l.LINEAR/'bounded-run-v1/inspect/process.json')
        self.data[4][path]['leader_identity_before_reap']['birth_microseconds']+=1;self.rejects()

    def test_compiler_cleanup_failure(self):
        path=str(m.l.LINEAR/'bounded-run-v1/compile/process.json')
        self.data[4][path]['remaining_process_group']=[{'pid':123}];self.rejects()

    def test_wrong_inspected_qlf(self):
        path=str(m.l.LINEAR/'bounded-run-v1/inspect/loaded-inputs.json')
        self.data[4][path]['target']='/another.qlf';self.rejects()

    def test_canonical_review_not_admitted(self):
        path=self.data[0]['linear_qualification']['source_count_review']['path']
        self.data[4][path]['canonical_LOC_admitted']=False;self.rejects()

    def test_canonical_projection_mismatch(self):
        path=self.data[0]['linear_qualification']['projection']['path']
        self.data[4][path]['projection']['normalized_loc']=241;self.rejects()

    def test_missing_owner_evidence(self):
        path=self.data[0]['linear_qualification']['source_count_review']['path']
        self.data[4][path]['pins']['missing-evidence.json']='0'*64;self.rejects()

    def test_failed_profile_excluded_with_partial_values(self):
        row=self.data[2]['profiles']['pidigits:prolog-pidigits-compact']
        row.update(full_workload_qualified=False,samples_seconds=[1.],median_seconds=None,failed_attempt=10)
        self.data[2]['failed_profiles'].append(row['key'])
        result=self.inspect()
        self.assertEqual(len(result['profiles']),19)
        self.assertEqual(result['excluded_profiles'],[dict(key=row['key'],reason='failed-full-workload',failed_attempt=10)])

    def test_unexplained_failure_rejected(self):
        self.data[2]['profiles']['pidigits:prolog-pidigits-compact']['full_workload_qualified']=False;self.rejects()


class ReviewLeaseExit(unittest.TestCase):
    def test_exit_failure_restores_before_outer_lease_release(self):
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try:yield
            finally:events.append('released')
        def check():
            self.assertNotIn('released',events)
            events.append('check');raise ValueError('changed evidence')
        def restore():
            self.assertNotIn('released',events);events.append('restored')
        with self.assertRaisesRegex(ValueError,'changed evidence'):
            with lease(),m._yield_verified({},check,restore):events.append('body')
        self.assertEqual(events,['held','body','check','restored','released'])

    def test_body_failure_still_checks_before_outer_release(self):
        events=[]
        with self.assertRaisesRegex(RuntimeError,'candidate failure'):
            with m._yield_verified({},lambda:events.append('checked'),None):
                raise RuntimeError('candidate failure')
        self.assertEqual(events,['checked'])

    def test_restoration_failure_preserves_both_errors(self):
        def check():raise ValueError('changed evidence')
        def restore():raise OSError('restore failed')
        with self.assertRaises(BaseExceptionGroup) as raised:
            with m._yield_verified({},check,restore):pass
        self.assertEqual([str(x) for x in raised.exception.exceptions],['changed evidence','restore failed'])

    def test_consumer_check_runs_after_evidence_and_restores_before_release(self):
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try:yield
            finally:events.append('released')
        def consumer():
            self.assertEqual(events,['held','body','evidence-checked'])
            events.append('consumer-checked');raise ValueError('publication changed')
        def restore():
            self.assertNotIn('released',events);events.append('restored')
        with self.assertRaisesRegex(ValueError,'publication changed'):
            with lease(),m._yield_verified({},lambda:events.append('evidence-checked'),restore,consumer):
                events.append('body')
        self.assertEqual(events,['held','body','evidence-checked','consumer-checked','restored','released'])


if __name__=='__main__':unittest.main()
