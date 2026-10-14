"""Pure checks for reviewed Scala case/callback ownership using native evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('scala_source_units_reviewed.py')
SPEC = importlib.util.spec_from_file_location('tested_scala_reviewed', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ReviewedOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replay, cls.records = m.base.replay_native()

    def record(self, index):
        return copy.deepcopy(self.records[index][1])

    def result(self, index):
        return m.project(self.record(index), application=index >= 70)

    def mutate(self, record, operation):
        for key in ('stock_parser', 'observed_parser'):
            operation(record[key])

    def test_original_34_concrete_contracts_unchanged(self):
        for item, record in self.records[:41]:
            if item['fixture']['expected_owner_status'] == 'candidate':
                self.assertEqual(m.project(record)['normalized_loc'], item['fixture']['proposed_normalized_loc'])

    def test_tuple_callback_fixture_is_now_explicitly_three_units(self):
        result = self.result(33)
        self.assertEqual(result['normalized_loc'], 3)
        self.assertEqual([e['kind'] for e in result['canonical_events'] if e['units']],
                         ['pattern-callback-header', 'expression-statement', 'written-close'])
        self.assertEqual(result['canonical_events'][0]['source_text'],
                         'val result = pairs.map { case (key, value) =>')

    def test_actual_selector_match_has_twelve_units(self):
        result = self.result(73)
        begin, end = 502, 728
        events = [e for e in result['canonical_events'] if e['units'] and
                  e['utf16_span'][0] >= begin and e['utf16_span'][1] <= end]
        self.assertEqual(sum(e['units'] for e in events), 12)
        self.assertEqual([e['kind'] for e in events].count('match-header'), 1)
        self.assertEqual([e['kind'] for e in events].count('case-header'), 5)
        self.assertEqual([e['kind'] for e in events].count('written-close'), 1)
        self.assertTrue(any('throw new IllegalArgumentException' in e['source_text'] for e in events))

    def test_actual_chained_pattern_callbacks_both_visible(self):
        result = self.result(73)
        events = [e for e in result['canonical_events'] if e['units'] and
                  2624 <= e['utf16_span'][0] and e['utf16_span'][1] <= 2775]
        self.assertEqual(sum(e['units'] for e in events), 6)
        self.assertEqual([e['kind'] for e in events], ['pattern-callback-header',
            'expression-statement', 'written-close', 'pattern-callback-header',
            'expression-statement', 'written-close'])
        self.assertIn('.toArray.sortBy', events[3]['source_text'])
        self.assertEqual([e['node'] for e in events if e['kind'] == 'written-close'], [454, 466])

    def test_regex_assignment_callback_exposes_actual_body(self):
        result = self.result(77)
        events = [e for e in result['canonical_events'] if e['units'] and
                  1612 <= e['utf16_span'][0] and e['utf16_span'][1] <= 1756]
        self.assertEqual([e['kind'] for e in events], ['pattern-callback-header', 'statement', 'written-close'])
        self.assertIn('result = Pattern.compile(pattern)', events[1]['source_text'])

    def test_else_if_joins_one_actual_header(self):
        for index in (73, 78):
            result = self.result(index)
            events = [e for e in result['canonical_events'] if e['kind'] == 'else-if-header']
            self.assertEqual(len(events), 1)
            self.assertTrue(events[0]['source_text'].startswith('else if'))
            self.assertEqual(events[0]['units'], 1)

    def test_all_ten_candidate_maps_complete_but_admission_false(self):
        for index in range(70, 80):
            result = self.result(index)
            self.assertEqual(result['diagnostics'], [])
            self.assertTrue(result['all_meaningful_tokens_owned'])
            self.assertIsInstance(result['candidate_normalized_loc'], int)
            self.assertIsNone(result['normalized_loc'])
            self.assertFalse(result['canonical_LOC_admitted'])
            self.assertFalse(result['chart_admission'])

    def test_guarded_case_remains_explicitly_gated(self):
        result = self.result(32)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('guarded-case-owner-review', {d['kind'] for d in result['diagnostics']})

    def test_multiple_partial_function_cases_rejected(self):
        changed = self.record(33)
        def alter(graph):
            graph['nodes'][7]['fields'][1]['value'].append({'node': 9})
            graph['structural_edges'].append({'parent': 7, 'role': 'cases[1]', 'child': 9})
        self.mutate(changed, alter)
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('multiple-partial-function-cases-review', {d['kind'] for d in result['diagnostics']})

    def test_guarded_partial_function_is_not_ordinary_callback(self):
        changed = self.record(33)
        def alter(graph):
            graph['nodes'][9]['fields'][1]['value'] = {'node': 10}
            edge = next(e for e in graph['structural_edges'] if e['parent'] == 9 and e['role'] == 'guard')
            edge['child'] = 10
        self.mutate(changed, alter)
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('guarded-case-owner-review', {d['kind'] for d in result['diagnostics']})

    def test_missing_real_close_is_not_invented(self):
        changed = self.record(33)
        changed['token_capture']['physical_pieces'].pop()
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('match-written-close-review', {d['kind'] for d in result['diagnostics']})

    def test_arrow_span_mismatch_does_not_hide_body(self):
        changed = self.record(33)
        def alter(graph):
            graph['nodes'][13]['span']['start'] += 2
        self.mutate(changed, alter)
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('case-arrow-boundary-review', {d['kind'] for d in result['diagnostics']})

    def test_synthetic_body_metadata_cannot_erase_work_or_invent_close(self):
        changed = self.record(77)
        def alter(graph):
            graph['nodes'][179]['span'].update(synthetic=True, source_derived=False)
        self.mutate(changed, alter)
        original, altered = self.result(77), m.project(changed, application=True)
        self.assertEqual(original['candidate_normalized_loc'], altered['candidate_normalized_loc'])
        self.assertEqual(original['canonical_events'], altered['canonical_events'])
        self.assertEqual(altered['diagnostics'], [])

    def test_discarding_case_body_child_cannot_produce_count(self):
        changed = self.record(33)
        def alter(graph):
            graph['nodes'][13]['fields'][1]['value'] = {'node': 8}
            edge = next(e for e in graph['structural_edges'] if e['parent'] == 13 and e['role'] == 'expr')
            edge['child'] = 8
        self.mutate(changed, alter)
        with self.assertRaisesRegex(AssertionError, 'Detached'):
            m.project(changed)


if __name__ == '__main__':
    unittest.main()
