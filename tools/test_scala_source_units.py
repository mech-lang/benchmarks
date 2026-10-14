"""Bounded pure tests over retained native Scala captures; no Scala/JVM execution."""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('scala_source_units.py')
SPEC = importlib.util.spec_from_file_location('tested_scala_units', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class NativeOwnerProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review, cls.records = m.replay_native()

    def record(self, index):
        return copy.deepcopy(self.records[index][1])

    def result(self, index):
        return m.project(self.record(index), application=index >= 70)

    def kinds(self, index):
        return [e['kind'] for e in self.result(index)['canonical_events'] if e['units']]

    def mutate_node(self, record, node, update):
        for key in ('stock_parser', 'observed_parser'):
            update(record[key]['nodes'][node])

    def test_actual_v2_delta_and_all_transport_evidence(self):
        self.assertEqual((self.review['native_pairs'], self.review['complete_cases'],
                          self.review['expected_rejections']), (80, 72, 8))
        self.assertEqual(sum(self.review['native_no_type_classes'].values()), 93)
        self.assertEqual(self.review['token_audit_summary']['checked_intervals'], 9030)

    def test_all_41_contracts_are_recomputed_from_native_owners(self):
        concrete = 0
        for item, record in self.records[:41]:
            with self.subTest(item=item['id']):
                result = m.project(record)
                self.assertEqual(result['normalized_loc'], item['fixture']['proposed_normalized_loc'])
                if item['fixture']['expected_owner_status'] == 'candidate':
                    concrete += 1
                    self.assertEqual(result['diagnostics'], [])
                    self.assertTrue(result['all_meaningful_tokens_owned'])
                else:
                    self.assertTrue(result['diagnostics'])
        self.assertEqual(concrete, 34)

    def test_counts_do_not_read_fixture_expectations(self):
        result = self.result(0)
        self.assertEqual(result['normalized_loc'], 5)
        self.assertNotIn('proposed_normalized_loc', self.record(0))
        self.assertNotIn('fixture', self.record(0))

    def test_packed_and_expanded_owners_match(self):
        for left, right in ((0, 1), (7, 8), (13, 14)):
            self.assertEqual(self.kinds(left), self.kinds(right))
            self.assertEqual(self.result(left)['normalized_loc'], self.result(right)['normalized_loc'])

    def test_named_block_method_has_real_header_body_and_close(self):
        result = self.result(0)
        owners = [e for e in result['canonical_events'] if e['units']]
        self.assertEqual([e['source_text'] for e in owners],
                         ['def f(): Int = {', 'val x = 1', 'val y = 2', 'x + y', '}'])
        self.assertEqual([e['node'] for e in owners], [2, 5, 8, 11, 2])

    def test_constructor_fields_are_authored_parameters_only(self):
        self.assertEqual(self.kinds(5), ['constructor-field', 'constructor-field', 'type-or-object-header'])
        self.assertEqual(self.kinds(6), ['type-or-object-header'])
        self.assertEqual(self.kinds(7).count('expression-method'), 1)

    def test_destructuring_is_one_binding(self):
        self.assertEqual(self.kinds(11), ['binding'])
        self.assertEqual(self.result(11)['canonical_events'][0]['node'], 2)

    def test_callback_source_opener_does_not_disappear(self):
        self.assertEqual(self.kinds(13), ['braced-callback-header', 'binding',
                          'expression-statement', 'expression-statement', 'written-close'])
        self.assertEqual(self.kinds(15), ['braced-callback-header', 'expression-statement', 'written-close'])
        self.assertEqual(self.kinds(16), ['binding'])

    def test_while_updates_and_nested_written_closes(self):
        self.assertEqual(self.kinds(17), ['method-header', 'while-header',
            'expression-statement', 'expression-statement', 'written-close', 'written-close'])
        result = self.result(21)
        statements = [e['source_text'] for e in result['canonical_events'] if e['units']][1:-1]
        self.assertEqual(statements, ['a += 1', 'b *= 2', 'values(i) = x'])

    def test_statement_and_scalar_if_have_different_owners(self):
        self.assertEqual(self.kinds(18), ['method-header', 'if-header', 'expression-statement',
                                         'else-header', 'expression-statement', 'written-close'])
        self.assertEqual(self.kinds(19), ['binding'])

    def test_try_finally_separate_bodies_and_written_closes(self):
        self.assertEqual(self.kinds(20), ['method-header', 'try-header', 'expression-statement',
            'written-close', 'finally-header', 'expression-statement', 'written-close', 'written-close'])

    def test_indentation_does_not_invent_a_close(self):
        self.assertEqual(self.kinds(22), ['method-header', 'binding', 'expression-statement'])
        self.assertEqual(self.kinds(23), self.kinds(22)+['written-close'])

    def test_native_end_marker_not_identifier_spelling(self):
        self.assertIn('written-end-marker-owner-review', {d['kind'] for d in self.result(24)['diagnostics']})
        for index in (71, 79):  # Programs use an ordinary binding named `end`.
            self.assertNotIn('written-end-marker-owner-review', {d['kind'] for d in self.result(index)['diagnostics']})

    def test_data_wrapping_is_retained(self):
        self.assertEqual(self.result(25)['normalized_loc'], 4)
        self.assertEqual(self.result(26)['normalized_loc'], 1)
        event = self.result(25)['canonical_events'][0]
        self.assertEqual(event['reason']['physical_rows'], [1, 2, 3, 4])

    def test_application_literal_arrays_and_string_rows_are_visible(self):
        fasta = [e for e in self.result(72)['canonical_events'] if e['kind'] == 'physical-data-rows']
        nbody = [e for e in self.result(75)['canonical_events'] if e['kind'] == 'physical-data-rows']
        self.assertEqual([e['units'] for e in fasta], [7, 3, 2])
        self.assertEqual([e['units'] for e in nbody], [14])
        self.assertIn('GGCCGGGCGCGGTGG', fasta[0]['source_text'])
        self.assertIn('solarMass', nbody[0]['source_text'])

    def test_comments_and_literal_delimiters_remain_native(self):
        self.assertEqual(self.result(28)['normalized_loc'], 1)
        self.assertEqual(self.result(29)['normalized_loc'], 4)
        self.assertEqual(self.result(36)['normalized_loc'], 0)
        self.assertFalse(any(e['kind'] == 'written-close' for e in self.result(29)['canonical_events']))

    def test_interpolation_executable_work_stays_reviewed(self):
        self.assertEqual(self.result(30)['normalized_loc'], 1)
        self.assertIsNone(self.result(31)['normalized_loc'])
        self.assertIn('executable-interpolation-owner-review', {d['kind'] for d in self.result(31)['diagnostics']})

    def test_pattern_and_directive_gates_survive(self):
        for i, kind in ((32, 'pattern-owner-review'), (33, 'pattern-owner-review'),
                        (38, 'meaningful-directive-owner-review')):
            result = self.result(i)
            self.assertIsNone(result['normalized_loc'])
            self.assertIn(kind, {d['kind'] for d in result['diagnostics']})

    def test_source_is_never_evaluated(self):
        result = self.result(37)
        self.assertEqual(result['normalized_loc'], 1)
        self.assertIn('throw new IllegalStateException', result['canonical_events'][0]['source_text'])

    def test_all_applications_require_manual_review(self):
        for i in range(70, 80):
            result = self.result(i)
            self.assertIsNone(result['normalized_loc'])
            self.assertTrue(result['application_manual_owner_review_required'])
            self.assertFalse(result['canonical_LOC_admitted'])
            self.assertFalse(result['chart_admission'])
        for i in (73, 77):
            self.assertIsNone(self.result(i)['candidate_normalized_loc'])

    def test_all_owner_token_ids_are_unique_and_spans_replay(self):
        for i in list(range(39)) + list(range(70, 80)):
            result = self.result(i)
            seen = [token for event in result['canonical_events'] for token in event['token_ids']]
            self.assertEqual(len(seen), len(set(seen)))
            record = self.records[i][1]
            raw = record['decoded_text'].encode('utf-8')
            for event in result['canonical_events']:
                start, end = event['utf8_span']
                self.assertEqual(raw[start:end].decode(), event['source_text'])

    def test_supplementary_character_map_is_used(self):
        result = self.result(35)
        self.assertEqual(result['physical_loc'], 2)
        self.assertTrue(any(e['utf16_span'] != e['utf8_span'] for e in result['canonical_events']))
        changed = self.record(35)
        changed['utf16_to_utf8_byte_boundaries'][0] = 1
        with self.assertRaisesRegex(AssertionError, 'offset map'):
            m.project(changed)

    def test_changed_source_or_literal_text_rejected(self):
        changed = self.record(28)
        changed['decoded_text'] = changed['decoded_text'].replace('literal', 'altered')
        with self.assertRaisesRegex(AssertionError, 'identity'):
            m.project(changed)
        changed = self.record(28)
        changed['token_capture']['physical_pieces'][-1]['source_text'] = 'wrong'
        with self.assertRaisesRegex(AssertionError, 'piece/source'):
            m.project(changed)

    def test_missing_token_or_whitespace_cannot_be_silently_owned(self):
        for field in ('physical_pieces', 'whitespace_intervals'):
            changed = self.record(0)
            changed['token_capture'][field].pop(0)
            self.assertIsNone(m.project(changed)['normalized_loc'])

    def test_missing_edge_and_dangling_node_rejected(self):
        changed = self.record(0)
        changed['observed_parser']['structural_edges'].pop()
        with self.assertRaisesRegex(AssertionError, 'edge inventory'):
            m.project(changed)
        changed = self.record(0)
        self.mutate_node(changed, 0, lambda n: n['fields'][1].update(value=[{'node': 1000}]))
        with self.assertRaisesRegex(AssertionError, 'Dangling'):
            m.project(changed)

    def test_duplicate_node_and_unknown_product_rejected(self):
        changed = self.record(0)
        changed['observed_parser']['nodes'].append(copy.deepcopy(changed['observed_parser']['nodes'][0]))
        with self.assertRaisesRegex(AssertionError, 'identity'):
            m.project(changed)
        changed = self.record(0)
        self.mutate_node(changed, 7, lambda n: n.update(product='UnreviewedMacro'))
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('unsupported-native-node', {d['kind'] for d in result['diagnostics']})

    def test_unexpected_typed_node_rejected(self):
        changed = self.record(0)
        self.mutate_node(changed, 2, lambda n: n['tree_state'].update(has_type=True))
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('unexpected-typed-native-node', {d['kind'] for d in result['diagnostics']})

    def test_false_parity_or_native_problem_cannot_qualify(self):
        changed = self.record(0)
        changed['stock_parser']['nodes'][7]['fields'][0]['value'] = '9'
        self.assertIsNone(m.project(changed)['normalized_loc'])
        changed = self.record(0)
        changed['token_capture']['issues'].append({'kind': 'unknown-capture-error'})
        self.assertIsNone(m.project(changed)['normalized_loc'])

    def test_unexpected_field_layout_stays_null(self):
        changed = self.record(0)
        self.mutate_node(changed, 7, lambda n: n['fields'].append({'role': 'unreviewed', 'value': None}))
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('unexpected-native-field-roles', {d['kind'] for d in result['diagnostics']})

    def test_missing_written_close_is_not_inferred_from_ast(self):
        changed = self.record(0)
        changed['token_capture']['physical_pieces'].pop()
        result = m.project(changed)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('ambiguous-written-block-close', {d['kind'] for d in result['diagnostics']})


if __name__ == '__main__':
    unittest.main()
