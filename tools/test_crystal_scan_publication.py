"""Crystal intake corruption, provenance and historical-preservation checks; no native commands."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from qualification import import_crystal_scan as admission


class CrystalAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=admission.load(admission.ROOT/admission.RESULTS)
        cls.catalog=admission.load(admission.ROOT/'data/benchmarks.json')

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name).resolve()
        paths={ref['path'] for ref in self.results['artifacts']}|{admission.PLAN,admission.RESULTS}
        for path in paths:
            dest=self.root/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(admission.ROOT/path,dest)
        self.review=admission.load(self.root/admission.FROZEN['review'][0])
        self.protocol=admission.load(self.root/admission.FROZEN['full_plan'][0])
        self.full=admission.load(self.root/admission.FROZEN['full'][0])
        parents={r['parent'] for r in self.results['programs']}
        programs={key:copy.deepcopy(self.catalog['programs'][key]) for key in parents}
        bench=next(b for b in self.catalog['benchmarks'] if b['key']=='regexredux')
        self.before=dict(programs=programs,program_inventory=copy.deepcopy(programs),
            files={sha:copy.deepcopy(self.catalog['files'][sha]) for row in programs.values() for sha in row['files']},
            archive_paths={'sentinel':'sentinel'},sentinel={'unchanged':[1,2]},
            benchmarks=[dict(key='regexredux',baseline_loc=bench['baseline_loc'],baseline_seconds=bench['baseline_seconds'],
                groups=[dict(language='crystal',programs=sorted(parents),fast=admission.CONTROL,small='regexredux:crystal-regexredux-compact')])],
            reference_summary=[dict(lang='crystal',fast={},small={})])

    def full_check(self,report=None,plan=None):
        evidence=admission.shared.Evidence(self.root)
        for ref in self.review['evidence']:
            if ref['path'].startswith(admission.BASE+'full-v1/run-v1/'):
                evidence.check(ref)
        return admission.check_full(evidence,plan or self.protocol,report or self.full,self.results['recorded_execution_root'])

    def test_saved_proof_replays_offline_without_native_artifacts(self):
        self.assertFalse((self.root/'experiments/implementation-audit/remaining-v1/.build').exists())
        self.assertEqual(admission.reconcile(self.root,local_artifacts=False),self.results)
        self.assertEqual(self.results['new_observations'],9)
        self.assertEqual([r['loc'] for r in self.results['programs']],[54,47,32])
        self.assertEqual([r['physical_loc'] for r in self.results['programs']],[46,41,28])
        self.assertIn('unavailable',self.results['source_size_scope'])

    def test_all_twelve_full_process_rows_reconcile(self):
        result=self.full_check()
        self.assertEqual(set(result),set(self.protocol['commands']))
        self.assertEqual([len(rows) for rows in result.values()],[3,3,3,3])

    def test_cohort_scope_incomplete_or_duplicate_samples_reject(self):
        for field,value in [('status','running'),('full_size_results',False),('chart_admission',True),
                            ('pins_unchanged',False),('lock_identity_unchanged',False),('plan_sha256','0'*64)]:
            report=copy.deepcopy(self.full);report[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.full_check(report)
        for rows in [self.full['observations'][:-1],self.full['observations']+[self.full['observations'][0]]]:
            report=copy.deepcopy(self.full);report['observations']=rows
            with self.assertRaises(ValueError):self.full_check(report)

    def test_input_size_hash_schedule_or_source_pool_drift_reject(self):
        for field,value in [('workload_size',1000),('input_bytes',1),('common_mutex_inode',123)]:
            plan=copy.deepcopy(self.protocol);plan[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.full_check(plan=plan)
        plan=copy.deepcopy(self.protocol);plan['cases'][0]['input']='/different/input'
        with self.assertRaises(ValueError):self.full_check(plan=plan)
        plan=copy.deepcopy(self.protocol);plan['order'].reverse()
        with self.assertRaises(ValueError):self.full_check(plan=plan)

    def test_saved_row_time_rss_and_aggregates_cannot_be_relabelled(self):
        for field,value in [('seconds',1.0),('maximum_rss_bytes',1),('directory','elsewhere')]:
            report=copy.deepcopy(self.full);report['observations'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.full_check(report)
        for field in ['samples','median_seconds','stdev_seconds','peak_rss_bytes']:
            report=copy.deepcopy(self.full);report['summary']['cr-parent'][field]=[1.0,2.0,3.0] if field=='samples' else 1.0
            with self.subTest(field=field),self.assertRaises(ValueError):self.full_check(report)

    def test_exact_stdout_raw_process_and_reviewed_library_bytes_are_required(self):
        paths=[admission.BASE+'full-v1/run-v1/00-cr-parent/stdout.bin',
               admission.BASE+'full-v1/run-v1/00-cr-parent/process.json',
               admission.ADMISSION+'runtime-source/string.cr']
        for path in paths:
            p=self.root/path;raw=p.read_bytes();p.write_bytes(raw+b'changed')
            with self.subTest(path=path),self.assertRaises(ValueError):admission.reconcile(self.root,local_artifacts=False)
            p.write_bytes(raw)

    def test_resealing_plan_cannot_waive_frozen_source_review_or_count(self):
        for path in [admission.FROZEN['review'][0],admission.SCAN+'source/block-parallel.cr',
                     admission.SCAN+'source-counts-v1/block-parallel.json',admission.FROZEN['full'][0]]:
            p=self.root/path;raw=p.read_bytes();p.write_bytes(raw+b'\n');admission.write(self.root/admission.PLAN,admission.make_plan(self.root))
            with self.subTest(path=path),self.assertRaises(ValueError):admission.reconcile(self.root,local_artifacts=False)
            p.write_bytes(raw)

    def test_append_retains_every_old_profile_source_sample_and_baseline(self):
        original=copy.deepcopy(self.before);after=admission.append_catalog(self.before,self.root)
        self.assertEqual(self.before,original)
        for pool in ['programs','program_inventory','files','archive_paths']:
            for key,row in original[pool].items():self.assertEqual(after[pool][key],row)
        self.assertEqual(after['sentinel'],original['sentinel'])
        for field in ['baseline_loc','baseline_seconds']:
            self.assertEqual(after['benchmarks'][0][field],original['benchmarks'][0][field])
        group=after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'],admission.key('block-parallel'))
        self.assertEqual(group['small'],admission.key('inline-compact'))
        self.assertEqual(len(after['programs'])-len(original['programs']),3)

    def test_new_source_has_own_observations_counts_and_mech_ratio(self):
        after=admission.append_catalog(self.before,self.root)
        for result in self.results['programs']:
            row=after['programs'][result['key']]
            self.assertEqual(row['samples'],result['samples_seconds'])
            self.assertEqual(row['files'],[result['source_sha256']])
            self.assertEqual(row['native_observations'],3)
            self.assertEqual(row['time_x_mech_aot'],row['seconds']/self.results['mech_aot_baseline']['seconds'])
            self.assertFalse(row['formatted_loc_complete'])
            self.assertIsNone(row['formatted_loc'])
            self.assertNotIn('source_metrics',row)

    def test_duplicate_parent_source_and_global_baseline_drift_reject(self):
        after=admission.append_catalog(self.before,self.root)
        with self.assertRaises(ValueError):admission.append_catalog(after,self.root)
        before=copy.deepcopy(self.before);before['programs'][admission.CONTROL]['files']=['0'*64]
        with self.assertRaises(ValueError):admission.append_catalog(before,self.root)
        before=copy.deepcopy(self.before);before['benchmarks'][0]['baseline_seconds']=10
        with self.assertRaises(ValueError):admission.append_catalog(before,self.root)

    def test_original_citations_licenses_and_unknown_exact_models_remain(self):
        from verify_repository import check_model_evidence
        after=admission.append_catalog(self.before,self.root)
        for result in self.results['programs']:
            row=after['programs'][result['key']];old=self.before['programs'][result['parent']]['authorship']
            self.assertEqual(row['authorship']['sources'],old['sources'])
            self.assertEqual(row['authorship']['license'],old['license'])
            self.assertEqual(row['authorship']['ai']['models'],[])
            self.assertIsNone(row['authorship']['ai']['exact_model'])
            self.assertEqual(admission.bound_authorship(after,row,self.root),row['authorship'])
            check_model_evidence(self.root,after,row['key'],row,{})
            row['authorship']['ai']['models']=['invented-model']
            with self.assertRaises(ValueError):check_model_evidence(self.root,after,row['key'],row,{})


if __name__=='__main__':unittest.main()
