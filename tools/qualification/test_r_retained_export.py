"""Pure retained R candidate checks; no native or physical-file phase."""
import copy
import importlib.util
from pathlib import Path
import unittest

def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

t=load('r_retained_fixture','test_r_retained_reconcile.py')
e=load('r_retained_export_test','r_retained_export.py')


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values=t.fixture();cls.sources=values['sources']
        cls.review=t.r.reconcile(**values,consumer=t.r.load_policy('consumer'),owners=t.r.load_policy('owners'))
        # Only the pure candidate transformation is exercised; no file-phase
        # receipt with these synthetic flags is ever saved.
        cls.review.update(status='27-saved-observations-reconciled-awaiting-publication-review',
            physical_file_integrity_verified=True,common_mutex_held=True)

    def test_exact_six_sources_and_27_distinct_observations(self):
        result=e.build_candidate(copy.deepcopy(self.review),copy.deepcopy(self.sources),t.r)
        self.assertEqual(len(result['program_inventory']),6);self.assertEqual(len(result['files']),6)
        self.assertEqual(sum(len(r['samples']) for r in result['program_inventory'].values()),18)
        self.assertEqual(sum(len(r['samples']) for r in result['matched_mech_controls'].values()),9)
        self.assertEqual(sum(len(g['programs']) for g in result['endpoints'].values()),5)
        self.assertFalse(result['chart_admission']);self.assertFalse(result['dataset_files_changed'])
        self.assertEqual(result['native_processes_started'],0)

    def test_canonical_counts_do_not_rewrite_retained_producer_counts(self):
        result=e.build_candidate(self.review,self.sources,t.r)
        row=result['program_inventory']['binarytrees:binarytrees-r-optimized']
        self.assertEqual((row['loc'],row['physical_loc'],row['original_producer_loc']),(21,20,20))
        self.assertIsNone(row['formatted_loc']);self.assertFalse(row['formatted_loc_qualified'])
        self.assertEqual(self.review['profiles'][row['key']]['loc'],20)

    def test_only_real_continuation_receipts_are_linked(self):
        result=e.build_candidate(self.review,self.sources,t.r)
        for row in result['program_inventory'].values():
            actual=[s['attempt'] for s in row['sample_evidence']['separate_continuation_receipts']]
            expected=[n for n in self.review['profiles'][row['key']]['attempts'] if n>=88]
            self.assertEqual(actual,expected)

    def test_changed_source_or_stats_and_unverified_file_phase_fail(self):
        key=next(iter(self.sources))
        for mutation in ('source','samples','file-phase'):
            review=copy.deepcopy(self.review);sources=copy.deepcopy(self.sources)
            if mutation=='source':sources[key]+=b'changed'
            elif mutation=='samples':review['profiles'][key]['samples_seconds'][0]*=2
            else:review['physical_file_integrity_verified']=False
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):e.build_candidate(review,sources,t.r)


if __name__=='__main__':unittest.main()
