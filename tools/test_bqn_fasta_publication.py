"""Offline BQN FASTA admission tests; no native runtime or benchmark executes."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from qualification import import_bqn_fasta as a


def put(root,path,value):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(a.encoded(value) if isinstance(value,(dict,list)) else value);return target


def copy_proof(root):
    paths=set(a.REFS.values())|{a.PARENT_SOURCE}
    producer=a.load(a.ROOT/a.REFS['producer_plan'])
    paths.update(ref['path'] for ref in producer['sources'].values())
    paths.update(ref['path'] for ref in producer['reference_files'])
    receipt=a.load(a.ROOT/a.REFS['ownership'])
    paths.update(receipt['policies']['retained'][key] for key in ['source','saved_audit'])
    for mode in ['bounded','full']:
        report_path=a.REFS[mode];report=a.load(a.ROOT/report_path);directory=str(Path(report_path).parent);recorded=a.recorded_root(report)
        paths.update(directory+'/sources/'+name+'.bqn' for name in a.SOURCES)
        paths.update(directory+'/'+path for path in ['controllers/run_serial.py','controllers/lean_run.py','tests/lookup-equivalence.bqn','execution-plan.json'])
        rows=report['cases']+([report['lookup_qualification']] if mode=='bounded' else [])
        for row in rows:
            if mode=='bounded':paths.add(a.relative(a.ROOT,row['stdout']['path'],recorded))
            stderr=a.relative(a.ROOT,row['stderr']['path'],recorded);paths.add(stderr);paths.add(str(Path(stderr).parent/'process.json'))
    for path in paths:
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.ROOT/path,target)
    return producer


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.producer=copy_proof(self.root);self.report=a.load(self.root/a.REFS['full']);self.recorded=a.recorded_root(self.report)

    def check(self,mode='full'):
        if mode=='full':put(self.root,a.REFS[mode],self.report)
        return a.check_execution(a.shared.Evidence(self.root),a.pin(self.root,a.REFS[mode]),mode,self.producer,self.recorded,False)

    def test_complete_actual_cohorts_reconcile_from_copied_proof(self):
        self.assertEqual(self.check()['medians']['bins-empty-safe'],10.348042625)
        bounded=self.check('bounded');self.assertEqual(len(bounded['cases']),48)
        self.assertFalse(bounded['lookup_qualification']['timing_admissible'])
        self.assertEqual(len(bounded['known_control_failures']),2)

    def test_archived_replay_needs_no_full_stdout_or_native_runtime(self):
        self.assertFalse((self.root/a.shared.RUNTIME).exists())
        for row in self.report['cases']:
            self.assertFalse((self.root/a.relative(self.root,row['stdout']['path'],self.recorded)).exists())
        self.assertEqual(self.check()['cases'][0]['command'],self.report['cases'][0]['command'])

    def test_local_full_verification_requires_actual_full_bytes(self):
        row=self.report['cases'][0];directory=str(Path(a.relative(self.root,row['stderr']['path'],self.recorded)).parent)
        additions={'source','n','sample','case','qualification_valid','output_valid','known_control_failure','source_sha256','runtime_sha256','power_before','power_after'}
        with self.assertRaises(FileNotFoundError):
            a.check_process(a.shared.Evidence(self.root),row,directory,a.FULL,self.recorded,additions,archive_full=True,local_artifacts=True)
        put(self.root,directory+'/stdout.bin',b'incomplete\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):
            a.check_process(a.shared.Evidence(self.root),row,directory,a.FULL,self.recorded,additions,archive_full=True,local_artifacts=True)

    def test_missing_full_raw_receipt_or_bounded_stream_is_fatal(self):
        row=self.report['cases'][0];path=Path(a.relative(self.root,row['stderr']['path'],self.recorded)).parent/'process.json'
        (self.root/path).unlink()
        with self.assertRaises(FileNotFoundError):self.check()
        bounded=a.load(self.root/a.REFS['bounded']);row=bounded['cases'][0]
        (self.root/a.relative(self.root,row['stdout']['path'],self.recorded)).unlink()
        with self.assertRaises(FileNotFoundError):self.check('bounded')

    def test_failed_active_diagnostic_or_nonfinite_sample_rejects(self):
        original=copy.deepcopy(self.report)
        for field,value in [('status','RUNNING'),('active',{}),('diagnostic_profile',True),('full_workload',False)]:
            self.report=copy.deepcopy(original);self.report[field]=value
            with self.assertRaises(ValueError):self.check()
        self.report=original;self.report['cases'][0]['elapsed_seconds']=True
        with self.assertRaisesRegex(ValueError,'nonfinite'):self.check()

    def test_missing_round_and_stale_median_rejects(self):
        self.report['cases'].pop()
        with self.assertRaisesRegex(ValueError,'case or round'):self.check()
        self.report=a.load(a.ROOT/a.REFS['full']);self.report['medians']['bins-empty-safe']=1.0
        with self.assertRaisesRegex(ValueError,'aggregation'):self.check()

    def test_changed_source_runtime_or_controller_pin_rejects(self):
        original=copy.deepcopy(self.report)
        for path in [a.SOURCE,a.shared.RUNTIME,a.REFS['controller']]:
            self.report=copy.deepcopy(original);self.report['pins'][path]='0'*64
            with self.assertRaisesRegex(ValueError,'source/runtime'):self.check()

    def test_raw_record_and_power_drift_rejects(self):
        self.report['cases'][0]['pid']+=1
        with self.assertRaisesRegex(ValueError,'Raw process'):self.check()
        self.report=a.load(a.ROOT/a.REFS['full']);self.report['cases'][0]['power_after']['settings']='lowpowermode 1'
        with self.assertRaisesRegex(ValueError,'power'):self.check()

    def test_strict_recorded_prefix_and_escape_checks(self):
        self.report['cases'][0]['stdout']['path']=str(self.root/'bad/stdout.bin')
        with self.assertRaisesRegex(ValueError,'recorded repository'):self.check()
        with self.assertRaises(ValueError):a.relative(self.root,self.recorded+'/../outside',self.recorded)
        self.report=a.load(a.ROOT/a.REFS['full']);self.report['cases'][0]['command'][1]=self.report['cases'][0]['command'][1].replace(self.recorded,'/other/root')
        with self.assertRaisesRegex(ValueError,'command'):self.check()

    def test_known_original_zero_failure_is_never_candidate_output_pass(self):
        report=a.load(self.root/a.REFS['bounded']);row=next(row for row in report['cases'] if row['known_control_failure'])
        self.assertFalse(row['output_valid']);row['output_valid']=True;put(self.root,a.REFS['bounded'],report)
        with self.assertRaisesRegex(ValueError,'process'):self.check('bounded')

    def test_exhaustive_lookup_cannot_be_missing_or_timed(self):
        report=a.load(self.root/a.REFS['bounded']);report['lookup_qualification']['timing_admissible']=True;put(self.root,a.REFS['bounded'],report)
        with self.assertRaisesRegex(ValueError,'lookup qualification'):self.check('bounded')


class OwnershipAndArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();copy_proof(self.root)
        put(self.root,a.PLAN,a.make_plan(self.root));self.results=a.reconcile(self.root,False);put(self.root,a.RESULTS,self.results)

    def test_root_approved24_24_and_no_full_output_artifact_claim(self):
        self.assertEqual(self.results['source_count_review']['application_loc'],24)
        self.assertFalse(self.results['full_stdout_archive']['retained_in_durable_repository'])
        self.assertEqual(len(self.results['full_stdout_archive']['files']),6)
        self.assertTrue(all(not ref['path'].endswith('/stdout.bin') or '/full-matched-v1/' not in ref['path'] for ref in self.results['artifacts']))
        self.assertEqual(self.results['bounded_validation']['candidate_cases'],16)

    def test_unapproved_counts_changed_owner_or_work_rejects(self):
        path=a.REFS['ownership'];original=a.load(self.root/path)
        for field,value in [('independent_review_approved',False),('application_loc',25)]:
            receipt=copy.deepcopy(original);receipt[field]=value;put(self.root,path,receipt)
            with self.assertRaises(ValueError):a.check_ownership(a.shared.Evidence(self.root),a.pin(self.root,path))
        receipt=copy.deepcopy(original);receipt['line_ledger'][14]['source_text']+=' changed';put(self.root,path,receipt)
        with self.assertRaisesRegex(ValueError,'Stale'):a.check_ownership(a.shared.Evidence(self.root),a.pin(self.root,path))
        receipt=original;receipt['required_work']['naive_lcg_updates_full']=1;put(self.root,path,receipt)
        with self.assertRaisesRegex(ValueError,'Required-work'):a.check_ownership(a.shared.Evidence(self.root),a.pin(self.root,path))

    def test_resealed_frozen_cohort_or_helper_change_rejects(self):
        put(self.root,a.REFS['shared_helpers'],b'changed helper\n');put(self.root,a.PLAN,a.make_plan(self.root))
        with self.assertRaisesRegex(ValueError,'frozen helper'):a.reconcile(self.root,False)

    def test_additive_catalog_preserves_history_selects_equal_loc_and_binds_authorship(self):
        parent=dict(key=a.PARENT,id='array-bqn-faithful',benchmark='fasta',language='bqn',files=[a.PARENT_SHA],loc=24,physical_loc=24,
            seconds=10.785043417,samples=[10.,11.,12.],x=2.,y=20.,authorship=dict(origin_status='unresolved',origin_gaps=['unknown predecessor'],
                retained_sources=[],license=dict(status='unverified',licenses=[],unresolved=['inherited terms unknown'])))
        before=dict(programs={a.PARENT:parent},program_inventory={a.PARENT:copy.deepcopy(parent)},files={a.PARENT_SHA:dict(code='retained source')},archive_paths={'old':'old'},
            benchmarks=[dict(key='fasta',baseline_loc=12,baseline_seconds=.5,groups=[dict(language='bqn',programs=[a.PARENT],fast=a.PARENT,small=a.PARENT,formatted_fast=None,formatted_small=None)])],
            reference_summary=[dict(lang='bqn',fast={},small={})],formatted_reference_summary=[dict(lang='bqn',fast=None,small=None)])
        original=copy.deepcopy(before);after=a.append_catalog(before,self.root);self.assertEqual(before,original)
        for pool in ['programs','program_inventory','files','archive_paths']:
            for key,value in original[pool].items():self.assertEqual(after[pool][key],value)
        group=after['benchmarks'][0]['groups'][0];self.assertEqual(group['fast'],a.KEY);self.assertEqual(group['small'],a.KEY)
        self.assertEqual(after['formatted_reference_summary'],original['formatted_reference_summary'])
        row=after['programs'][a.KEY];self.assertEqual(row['samples'],[10.155231542,10.348042625,10.381222792])
        self.assertEqual(a.bound_authorship(after,row,self.root),row['authorship']);self.assertIsNone(row['authorship']['ai']['exact_model'])
        self.assertEqual(row['authorship']['license'],parent['authorship']['license'])
        row['source_provenance_record']['admission']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Unbound'):a.bound_authorship(after,row,self.root)

    def test_stale_results_cannot_append(self):
        bad=copy.deepcopy(self.results);bad['programs'][0]['median_seconds']=1.;put(self.root,a.RESULTS,bad)
        with self.assertRaisesRegex(ValueError,'Stale'):a.append_catalog({},self.root)


class PrepareGuardTests(unittest.TestCase):
    def test_cli_prepare_rejects_concurrent_canonical_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);before={'old':'catalog'};put(root,'data/benchmarks.json',before)
            def changed(value):
                self.assertEqual(value,before);put(root,'data/benchmarks.json',{'concurrent':'change'});return {'preview':'old'}
            with mock.patch.object(a,'ROOT',root),mock.patch.object(a,'make_plan',return_value={}),mock.patch.object(a,'reconcile',return_value={}), \
                 mock.patch.object(a,'append_catalog',side_effect=changed),mock.patch.object(sys,'argv',['import_bqn_fasta.py','--prepare']):
                with self.assertRaisesRegex(ValueError,'Canonical changed during preview'):a.main()


if __name__=='__main__':unittest.main()
