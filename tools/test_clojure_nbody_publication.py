"""Clojure intake regression proofs; never launch Java or a timed program."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest

from qualification import import_clojure_nbody as admission


def put(root,path,value):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(admission.encoded(value) if isinstance(value,(dict,list)) else value)


class ProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=admission.load(admission.ROOT/admission.RESULTS)
        cls.catalog=admission.load(admission.ROOT/'data/benchmarks.json')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        paths={row['path'] for row in self.results['artifacts']}|{admission.PLAN,admission.RESULTS,admission.SOURCE}
        for path in paths:
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(admission.ROOT/path,target)
        self.foundation=admission.load(self.root/(admission.BASE+admission.FROZEN['foundation'][0]))
        self.full=admission.load(self.root/(admission.BASE+admission.FROZEN['full'][0]))
        parent=copy.deepcopy(self.catalog['programs'][admission.PARENT])
        benchmark=next(b for b in self.catalog['benchmarks'] if b['key']=='nbody')
        self.before=dict(programs={admission.PARENT:parent},program_inventory={admission.PARENT:copy.deepcopy(parent)},
            files={key:copy.deepcopy(self.catalog['files'][key]) for key in parent['files']},archive_paths={'sentinel':'sentinel'},
            benchmarks=[dict(key='nbody',baseline_loc=benchmark['baseline_loc'],baseline_seconds=benchmark['baseline_seconds'],
                groups=[dict(language='clojure',programs=[admission.PARENT],fast=admission.PARENT,small=admission.PARENT)])],
            reference_summary=[dict(lang='clojure',fast={},small={})],sentinel={'unchanged':[1,2,3]})

    def check(self,report=None):
        admission.check_processes(admission.shared.Evidence(self.root),report or self.full,'full',self.foundation,self.results['recorded_execution_root'])

    def test_archived_proof_relocates_without_jdk_or_classes(self):
        self.assertFalse((self.root/self.foundation['java']['path']).exists())
        self.assertEqual(admission.reconcile(self.root,local_artifacts=False),self.results)
        self.assertEqual(self.results['programs'][0]['median_seconds'],2.661471542)
        self.assertAlmostEqual(self.results['matched_control_speedup'],58.564193122227266)

    def test_all_full_and_bounded_observations_replay(self):
        self.check()
        bounded=admission.load(self.root/(admission.BASE+admission.FROZEN['bounded'][0]))
        self.assertEqual(len(bounded['cases']),30)
        admission.check_processes(admission.shared.Evidence(self.root),bounded,'bounded',self.foundation,self.results['recorded_execution_root'])

    def test_invalid_diagnostic_active_or_incomplete_cohort_rejects(self):
        for key,value in [('status','RUNNING'),('active',{}),('pins_unchanged',False),('diagnostic_profile',True),('full_workload',False),('chart_admission',True)]:
            with self.subTest(key=key):
                row=copy.deepcopy(self.full);row[key]=value
                with self.assertRaises(ValueError):self.check(row)
        row=copy.deepcopy(self.full);row['cases'].pop()
        with self.assertRaises(ValueError):self.check(row)

    def test_changed_process_command_workload_or_environment_rejects(self):
        for field,value in [('n',1000000),('command',['java','other']),('environment',{}),('source_sha256','0'*64),('output_valid',False),('common_mutex_inherited',False),('timed_out',True),('remaining_process_group',[123])]:
            with self.subTest(field=field):
                row=copy.deepcopy(self.full);row['cases'][0][field]=value
                with self.assertRaises(ValueError):self.check(row)

    def test_changed_process_receipt_or_power_rejects(self):
        row=copy.deepcopy(self.full);row['cases'][0]['pid']+=1
        with self.assertRaisesRegex(ValueError,'Raw'):self.check(row)
        row=copy.deepcopy(self.full);row['cases'][0]['power_after']['settings']='lowpowermode 1'
        with self.assertRaisesRegex(ValueError,'power'):self.check(row)

    def test_wrong_stream_exact_output_or_root_rejects(self):
        row=self.full['cases'][0];path=admission.relative(self.root,row['stdout']['path'],self.results['recorded_execution_root'])
        put(self.root,path,b'wrong\n')
        with self.assertRaisesRegex(ValueError,'Changed evidence'):self.check()
        shutil.copyfile(admission.ROOT/path,self.root/path)
        row['exact_reference_bytes']=False
        with self.assertRaisesRegex(ValueError,'exact'):self.check()
        row['exact_reference_bytes']=True;row['stdout']['path']='/unrelated/stdout.bin'
        with self.assertRaises(ValueError):self.check()

    def test_aggregate_or_shuffle_order_drift_rejects(self):
        row=copy.deepcopy(self.full);row['medians']['primitive-updates']=1.0
        with self.assertRaisesRegex(ValueError,'aggregates'):self.check(row)
        row=copy.deepcopy(self.full);row['orders'][0]['sources'].reverse()
        with self.assertRaisesRegex(ValueError,'order'):self.check(row)

    def test_source_count_controller_and_sealed_report_cannot_be_resealed(self):
        for path in [admission.SOURCE,admission.BASE+admission.FROZEN['ownership'][0],admission.BASE+admission.FROZEN['full'][0],admission.BASE+'selected-full-v1/run-v1/controllers/run_selected_full.py']:
            with self.subTest(path=path):
                original=(self.root/path).read_bytes();put(self.root,path,original+b'\n')
                put(self.root,admission.PLAN,admission.make_plan(self.root))
                with self.assertRaises(ValueError):admission.reconcile(self.root,local_artifacts=False)
                put(self.root,path,original)

    def test_catalog_addition_preserves_all_existing_records_and_fixed_axes(self):
        before=copy.deepcopy(self.before);after=admission.append_catalog(self.before,self.root)
        self.assertEqual(self.before,before)
        for pool in ['programs','program_inventory','files','archive_paths']:
            for key,value in before[pool].items():self.assertEqual(after[pool][key],value)
        self.assertEqual(after['sentinel'],before['sentinel'])
        group=after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'],admission.KEY);self.assertEqual(group['small'],admission.PARENT)
        row=after['programs'][admission.KEY]
        self.assertEqual((row['loc'],row['physical_loc']),(111,52));self.assertEqual(row['samples'],[2.661471542,2.714510416,2.658480875])
        self.assertEqual(row['files'],[admission.SOURCE_SHA,admission.SUPPORT_SHA])
        self.assertFalse(row['file_roles'][admission.SUPPORT_SHA]['included_in_application_loc'])

    def test_duplicate_bad_parent_or_new_global_baseline_rejects(self):
        after=admission.append_catalog(self.before,self.root)
        with self.assertRaisesRegex(ValueError,'Already'):admission.append_catalog(after,self.root)
        self.before['programs'][admission.PARENT]['loc']=49
        with self.assertRaisesRegex(ValueError,'parent'):admission.append_catalog(self.before,self.root)
        self.before['programs'][admission.PARENT]['loc']=109;self.before['benchmarks'][0]['baseline_seconds']=3
        with self.assertRaisesRegex(ValueError,'baseline'):admission.append_catalog(self.before,self.root)

    def test_authorship_binds_only_this_edit_without_invented_variant(self):
        after=admission.append_catalog(self.before,self.root);row=after['programs'][admission.KEY]
        self.assertEqual(row['authorship'],admission.bound_authorship(after,row,self.root))
        self.assertEqual(row['authorship']['ai']['models'],[]);self.assertIsNone(row['authorship']['ai']['exact_model'])
        row['source_provenance_record']['source_sha256']='0'*64
        with self.assertRaises(ValueError):admission.bound_authorship(after,row,self.root)


if __name__=='__main__':unittest.main()
