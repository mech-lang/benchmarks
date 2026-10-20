"""Offline spectral admission proofs; no runtime/compiler/native benchmark runs."""
import copy
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
import sys
from unittest import mock

from qualification import import_bqn_spectral as admission


def put(root, path, value):
    target = root/path; target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(admission.encoded(value) if isinstance(value, (dict, list)) else value)
    return target


def copy_proof(root):
    paths = set(admission.REFS.values()) | {admission.PARENT_SOURCE}
    producer = admission.load(admission.ROOT/admission.REFS['producer_plan'])
    paths.update(ref['path'] for ref in producer['sources'].values())
    paths.update(ref['path'] for ref in producer['reference_files'])
    ownership = admission.load(admission.ROOT/admission.REFS['ownership'])
    paths.update(ownership['policies']['retained'][key] for key in ['source','saved_audit'])
    for mode in ['bounded','full']:
        report_path = admission.REFS[mode]; report = admission.load(admission.ROOT/report_path)
        directory = str(Path(report_path).parent); recorded = admission.recorded_root(report)
        paths.update(directory+'/sources/'+name+'.bqn' for name in admission.SOURCES)
        paths.update([directory+'/controllers/run_serial.py', directory+'/controllers/lean_run.py', directory+'/plan.json'])
        for row in report['cases']:
            for stream in ['stdout','stderr']:
                paths.add(admission.relative(admission.ROOT,row[stream]['path'],recorded))
            paths.add(str(Path(admission.relative(admission.ROOT,row['stdout']['path'],recorded)).parent/'process.json'))
    for path in paths:
        target = root/path; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(admission.ROOT/path,target)
    return producer


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.producer = copy_proof(self.root)
        self.report = admission.load(self.root/admission.REFS['full'])
        self.recorded = admission.recorded_root(self.report)

    def check(self, mode='full'):
        if mode == 'full': put(self.root,admission.REFS[mode],self.report)
        return admission.check_execution(admission.shared.Evidence(self.root),admission.pin(self.root,admission.REFS[mode]),
            mode,self.producer,self.recorded,local_artifacts=False)

    def test_actual_full_and_all_seven_bounded_cases_reconcile(self):
        self.assertEqual(self.check()['medians']['row-sum'],1.513197125)
        self.assertEqual(len(self.check('bounded')['cases']),21)

    def test_source_proof_relocates_without_executable_or_old_checkout(self):
        self.assertFalse((self.root/admission.shared.RUNTIME).exists())
        self.assertNotEqual(str(self.root),self.recorded)
        self.assertEqual(self.check()['cases'][0]['command'],self.report['cases'][0]['command'])

    def test_rejects_failed_active_or_diagnostic_cohort(self):
        original = copy.deepcopy(self.report)
        for key,value in [('status','RUNNING'),('active',{'source':'row-sum'}),('diagnostic_profile',True),('full_workload',False),('chart_admission',True)]:
            with self.subTest(key=key):
                self.report = copy.deepcopy(original);self.report[key]=value
                with self.assertRaises(ValueError):self.check()

    def test_rejects_missing_round_or_stale_aggregation(self):
        self.report['cases'].pop()
        with self.assertRaisesRegex(ValueError,'execution'):self.check()
        self.report = admission.load(admission.ROOT/admission.REFS['full']);self.report['medians']['row-sum']=1.0
        with self.assertRaisesRegex(ValueError,'aggregation'):self.check()

    def test_rejects_source_runtime_or_controller_drift(self):
        original=copy.deepcopy(self.report)
        for key in [admission.SOURCE,admission.shared.RUNTIME,admission.REFS['controller']]:
            with self.subTest(key=key):
                self.report=copy.deepcopy(original);self.report['pins'][key]='0'*64
                with self.assertRaisesRegex(ValueError,'pins'):self.check()

    def test_rejects_raw_process_or_power_mismatch(self):
        self.report['cases'][0]['pid']+=1
        with self.assertRaisesRegex(ValueError,'Raw'):self.check()
        self.report=admission.load(admission.ROOT/admission.REFS['full'])
        self.report['cases'][0]['power_after']['settings']='lowpowermode 1'
        with self.assertRaisesRegex(ValueError,'power'):self.check()

    def test_rejects_stream_change_and_wrong_command(self):
        row=self.report['cases'][0];path=admission.relative(self.root,row['stdout']['path'],self.recorded)
        put(self.root,path,b'wrong\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):self.check()
        shutil.copyfile(admission.ROOT/path,self.root/path)
        row['command'][2]='100'
        with self.assertRaisesRegex(ValueError,'command'):self.check()

    def test_mixed_prefixes_and_path_escape_reject(self):
        row=self.report['cases'][0];row['stdout']['path']=str(self.root/'other/stdout.bin')
        with self.assertRaisesRegex(ValueError,'recorded repository'):self.check()
        with self.assertRaises(ValueError):admission.relative(self.root,self.recorded+'/../outside',self.recorded)

    def test_snapshot_and_producer_plan_are_pinned(self):
        path=str(Path(admission.REFS['full']).parent)+'/sources/row-sum.bqn'
        put(self.root,path,b'1\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):self.check()
        with self.assertRaisesRegex(ValueError,'producer plan'):
            admission.check_producer_plan(admission.shared.Evidence(self.root),dict(path=admission.REFS['producer_plan'],sha256='0'*64))


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);copy_proof(self.root)
        self.receipt=admission.load(self.root/admission.REFS['ownership'])

    def check(self):
        put(self.root,admission.REFS['ownership'],self.receipt)
        return admission.check_ownership(admission.shared.Evidence(self.root),admission.pin(self.root,admission.REFS['ownership']))

    def test_exact_root_approved_parent_policy_is13_9(self):
        self.assertEqual(self.check()['application_loc'],13)

    def test_unapproved_count_or_changed_line_rejects(self):
        original=copy.deepcopy(self.receipt)
        for key,value in [('independent_review_approved',False),('application_loc',9),('source_sha256','0'*64)]:
            self.receipt=copy.deepcopy(original);self.receipt[key]=value
            with self.assertRaises(ValueError):self.check()
        self.receipt=original;self.receipt['line_ledger'][3]['source_text']+=' changed'
        with self.assertRaisesRegex(ValueError,'Stale'):self.check()

    def test_required_products_and_no_cache_review_cannot_change(self):
        self.receipt['required_work']['matrix_vector_products']=20
        with self.assertRaisesRegex(ValueError,'Required-work'):self.check()


class CompleteProofAndCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();copy_proof(self.root)
        put(self.root,admission.PLAN,admission.make_plan(self.root))
        self.results=admission.reconcile(self.root,local_artifacts=False)
        put(self.root,admission.RESULTS,self.results)
        parent=dict(key=admission.PARENT,id='array-bqn-faithful',benchmark='spectralnorm',language='bqn',files=[admission.PARENT_SHA],
            loc=13,physical_loc=9,seconds=2.166914167,samples=[2.163887875,2.179455458,2.166914167],x=13/9,y=25.,
            formatted_loc=None,formatted_x=None,formatted_loc_complete=False,authorship=dict(origin_status='unresolved',
                origin_gaps=['Predecessor unknown'],retained_sources=[],license=dict(status='unverified',licenses=[],unresolved=['Inherited terms unknown'])))
        self.before=dict(programs={admission.PARENT:parent},program_inventory={admission.PARENT:copy.deepcopy(parent)},
            files={admission.PARENT_SHA:dict(code='old source preserved',sha256=admission.PARENT_SHA)},archive_paths={'old':'old'},
            benchmarks=[dict(key='spectralnorm',baseline_loc=9,baseline_seconds=.08,groups=[dict(language='bqn',programs=[admission.PARENT],
                fast=admission.PARENT,small=admission.PARENT,formatted_fast=None,formatted_small=None)])],
            reference_summary=[dict(lang='bqn',fast={},small={})],formatted_reference_summary=[dict(lang='bqn',fast=None,small=None)],
            unrelated_sentinel={'preserve':[1,2,3]})

    def test_full_archived_proof_replays_without_native_runtime(self):
        self.assertEqual(self.results['programs'][0]['samples_seconds'],[1.491566,1.516066667,1.513197125])
        self.assertEqual(self.results['required_work']['weighted_contributions'],1210000000)
        self.assertFalse((self.root/admission.shared.RUNTIME).exists())

    def test_catalog_addition_preserves_history_and_reselects_equal_loc_small(self):
        original=copy.deepcopy(self.before);after=admission.append_catalog(self.before,self.root)
        self.assertEqual(self.before,original)
        for pool in ['programs','program_inventory','files','archive_paths']:
            for key,value in original[pool].items():self.assertEqual(after[pool][key],value)
        group=after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'],admission.KEY);self.assertEqual(group['small'],admission.KEY)
        self.assertEqual(after['formatted_reference_summary'],original['formatted_reference_summary'])
        self.assertEqual(after['unrelated_sentinel'],original['unrelated_sentinel'])
        row=after['programs'][admission.KEY]
        self.assertEqual(row['samples'],[1.491566,1.516066667,1.513197125])
        self.assertEqual(row['cwd'],self.results['recorded_execution_root'])
        self.assertEqual(row['loc'],13);self.assertEqual(row['physical_loc'],9)
        self.assertEqual(row['authorship']['license'],original['programs'][admission.PARENT]['authorship']['license'])

    def test_stale_results_changed_parent_or_new_global_minimum_reject(self):
        bad=copy.deepcopy(self.results);bad['programs'][0]['median_seconds']=1.0;put(self.root,admission.RESULTS,bad)
        with self.assertRaisesRegex(ValueError,'Stale'):admission.append_catalog(self.before,self.root)
        put(self.root,admission.RESULTS,self.results)
        self.before['programs'][admission.PARENT]['files'].append('0'*64)
        with self.assertRaisesRegex(ValueError,'parent'):admission.append_catalog(self.before,self.root)
        self.before['programs'][admission.PARENT]['files']=[admission.PARENT_SHA]
        self.before['benchmarks'][0]['baseline_seconds']=10
        with self.assertRaisesRegex(ValueError,'normalization'):admission.append_catalog(self.before,self.root)

    def test_authorship_is_exact_source_bound_without_invented_model(self):
        after=admission.append_catalog(self.before,self.root);row=after['programs'][admission.KEY]
        self.assertEqual(admission.bound_authorship(after,row,self.root),row['authorship'])
        self.assertIsNone(row['authorship']['ai']['exact_model']);self.assertEqual(row['authorship']['ai']['models'],[])
        row['source_provenance_record']['admission']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Unbound'):admission.bound_authorship(after,row,self.root)

    def test_changed_frozen_helper_or_cohort_is_not_resealed_by_plan(self):
        put(self.root,admission.REFS['shared_helpers'],b'changed helper\n')
        put(self.root,admission.PLAN,admission.make_plan(self.root))
        with self.assertRaisesRegex(ValueError,'frozen helper'):admission.reconcile(self.root,local_artifacts=False)


class PrepareRaceTests(unittest.TestCase):
    def test_prepare_rejects_concurrent_canonical_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);before={'original':'catalog'};put(root,'data/benchmarks.json',before)
            def changed(value):
                self.assertEqual(value,before)
                put(root,'data/benchmarks.json',{'changed':'concurrently'})
                return {'preview':'original input'}
            with mock.patch.object(admission,'ROOT',root),mock.patch.object(admission,'make_plan',return_value={}), \
                 mock.patch.object(admission,'reconcile',return_value={}),mock.patch.object(admission,'append_catalog',side_effect=changed), \
                 mock.patch.object(sys,'argv',['import_bqn_spectral.py','--prepare']):
                with self.assertRaisesRegex(ValueError,'Canonical changed during preview'):admission.main()


if __name__=='__main__':unittest.main()
