"""Pure independent Scala manual-accounting regression checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('scala_application_owner_review.py')
SPEC = importlib.util.spec_from_file_location('tested_scala_manual_review', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ManualOwnerReviewTests(unittest.TestCase):
    def inputs(self, name):
        source = (m.ROOT/'experiments/scala/source-v1'/name/'Main.scala').read_bytes()
        projection = json.loads((m.PACKET/'results-v1'/('scala-'+name+'-jvm-v1.json')).read_text())
        return source, projection

    def test_all_ten_independent_row_accounts_replay(self):
        result = m.audit()
        self.assertEqual([c['canonical_loc'] for c in result['applications']],
                         [42, 123, 54, 97, 55, 100, 34, 48, 49, 60])
        self.assertTrue(all(c['all_application_owners_manually_reviewed'] for c in result['applications']))
        self.assertFalse(result['canonical_LOC_admitted'])

    def test_changed_total_is_not_accepted(self):
        source, projection = self.inputs('pidigits')
        projection['candidate_normalized_loc'] += 1
        with self.assertRaisesRegex(AssertionError, 'totals'):
            m.review_one('pidigits', source, projection)

    def test_body_ownership_cannot_be_dropped(self):
        source, projection = self.inputs('knucleotide')
        projection['canonical_events'].pop(5)
        with self.assertRaisesRegex(AssertionError, 'ownership'):
            m.review_one('knucleotide', source, projection)

    def test_token_cannot_be_assigned_to_different_event(self):
        source, projection = self.inputs('regexredux')
        projection['token_ownership'][0]['owner_event'] = 999
        with self.assertRaisesRegex(AssertionError, 'linkage'):
            m.review_one('regexredux', source, projection)

    def test_data_row_cannot_be_merged_without_manual_rule(self):
        source, projection = self.inputs('nbody')
        event = next(e for e in projection['canonical_events'] if e['kind'] == 'physical-data-rows')
        event['units'] -= 1
        event['reason']['physical_rows'].pop()
        with self.assertRaisesRegex(AssertionError, 'independent source review'):
            m.review_one('nbody', source, projection)

    def test_premature_admission_is_rejected(self):
        source, projection = self.inputs('binarytrees')
        projection['normalized_loc'] = projection['candidate_normalized_loc']
        with self.assertRaisesRegex(AssertionError, 'prematurely'):
            m.review_one('binarytrees', source, projection)


if __name__ == '__main__':
    unittest.main()
