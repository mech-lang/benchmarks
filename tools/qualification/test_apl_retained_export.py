"""Pure saved-evidence candidate checks; no full file replay or data writes."""
import copy
import importlib.util
from pathlib import Path
import unittest


def load(name,filename):
    path=Path(__file__).with_name(filename);spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


r=load('apl_export_test_reconciler','apl_retained_reconcile.py')
e=load('apl_export_under_test','apl_retained_export.py')
INDEX,D,RECORDS,SOURCES=r.metadata()


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=r.reconcile(INDEX,D,RECORDS,SOURCES)
        # File-phase flags are synthetic solely for exercising pure transforms;
        # this object is never written as an admission receipt.
        cls.review.update(status='five-completed-workloads-reconciled-awaiting-publication-review',
            file_integrity_verified=True,common_mutex_held=True)

    def build(self,review=None,sources=None,report=None):
        return e.build_candidate(self.review if review is None else review,SOURCES if sources is None else sources,
            INDEX,D['counts'],D['report'] if report is None else report)

    def test_nine_sources_27_subject_15_control_observations(self):
        v=self.build();self.assertEqual(len(v['files']),9);self.assertEqual(len(v['program_inventory']),11)
        self.assertEqual(sum(p['native_observations'] for p in v['program_inventory'].values()),27)
        self.assertEqual(sum(p['native_observations'] for p in v['matched_mech_controls'].values()),15)
        self.assertEqual(len(v['endpoints']),5);self.assertFalse(v['chart_admission']);self.assertFalse(v['complete_suite_qualified'])
        self.assertFalse(v['dataset_files_changed']);self.assertEqual(v['native_processes_started'],0)

    def test_aliases_reuse_owner_evidence_without_native_recount(self):
        v=self.build();aliases=[p for p in v['program_inventory'].values() if p['timing_alias_of']]
        self.assertEqual(len(aliases),2)
        for alias in aliases:
            owner=v['program_inventory'][alias['timing_alias_of']]
            self.assertEqual(alias['native_observations'],0);self.assertEqual(alias['files'],owner['files'])
            self.assertEqual(alias['sample_evidence'],owner['sample_evidence']);self.assertFalse(alias['distinct_optimization_claimed'])

    def test_failures_and_recovery_are_preserved_and_not_scored(self):
        v=self.build();self.assertEqual(v['original_report_status'],'partial');self.assertEqual(v['recovery_owner_status'],'complete')
        for number in ('58','75'):
            failed=v['preserved_failed_attempts'][number]
            self.assertFalse(failed['original_attempt']['qualified']);self.assertEqual(failed['original_attempt']['stdout_bytes'],0)
        fann=v['program_inventory'][r.KEY]
        sample=next(x for x in fann['sample_evidence'] if x['attempt']==84)
        self.assertEqual(sample['seconds'],7797.184570125);self.assertEqual(sample['provenance'],'kernel-exit-recovery')
        self.assertTrue(sample['supervisor']['path'].endswith('recovered-084.supervisor.json'))
        self.assertNotIn(r.TREE,v['program_inventory'])

    def test_control44_remains_report_only_and_formatted_counts_absent(self):
        v=self.build();sample=next(x for x in v['matched_mech_controls']['mandelbrot']['sample_evidence'] if x['attempt']==44)
        self.assertIsNone(sample['raw']);self.assertIsNone(sample['supervisor'])
        row=v['program_inventory'][r.KEY]
        self.assertEqual((row['loc'],row['original_producer_loc']),(38,37))
        for p in v['program_inventory'].values():self.assertIsNone(p['formatted_loc']);self.assertFalse(p['formatted_loc_qualified'])

    def test_unverified_work_or_file_phase_and_changed_source_fail(self):
        for field in ('source_work_qualified','canonical_loc_qualified','file_integrity_verified'):
            review=copy.deepcopy(self.review);review[field]=False
            with self.assertRaises(ValueError):self.build(review=review)
        sources=dict(SOURCES);sources[next(iter(sources))]+=b'changed'
        with self.assertRaises(ValueError):self.build(sources=sources)

    def test_changed_stats_or_alias_native_count_cannot_be_exported(self):
        review=copy.deepcopy(self.review);review['profiles'][r.KEY]['median_seconds']=1
        with self.assertRaises(ValueError):self.build(review=review)
        review=copy.deepcopy(self.review);review['profiles']['fannkuchredux:fannkuchredux-apl-optimized']['native_attempts']=[82,84,87]
        with self.assertRaises(ValueError):self.build(review=review)


if __name__=='__main__':unittest.main()
