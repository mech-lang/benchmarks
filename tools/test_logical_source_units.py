"""Native logical ownership, exact-source scope and real-program regressions."""
import ast
import copy
import json
import unittest

import logical_source_units as logical


class PythonLogicalUnitTests(unittest.TestCase):
    def test_independent_semicolon_statements_and_literal_layout(self):
        for _, left, right, expected in logical.PYTHON_FIXTURE_PAIRS:
            a, b = logical.python_units(left), logical.python_units(right)
            self.assertEqual((a['logical_loc'], b['logical_loc']), (expected, expected))
            self.assertEqual(a['native_ast_sha256'], b['native_ast_sha256'])
            self.assertEqual(a['coverage']['unowned_significant_tokens'], 0)

    def test_true_tuple_binding_is_one_owner_and_chain_is_two(self):
        self.assertEqual(logical.python_units('x,y=(1,2)\n')['logical_loc'], 1)
        self.assertEqual(logical.python_units('x=y=1\n')['logical_loc'], 2)
        self.assertEqual(logical.python_units('x=1;y=2\n')['logical_loc'], 2)

    def test_definition_body_decorators_and_documentation(self):
        text = '@decorate\ndef f(x):\n """Documentation; # is literal data."""\n y=x+1\n return y\n'
        result = logical.python_units(text)
        self.assertEqual(result['logical_loc'], 3)
        self.assertEqual(result['owners'][0]['start'], 0)
        self.assertEqual(result['owners'][1]['units'], 0)
        self.assertEqual(result['coverage']['unowned_significant_tokens'], 0)

    def test_parse_errors_and_unqualified_native_syntax_fail_closed(self):
        for text in ['def f(\n', 'match x:\n case 1: pass\n', 'if (x:=f()): pass\n']:
            with self.assertRaises(logical.QualificationError):
                logical.python_units(text)

    def test_support_projection_retains_original_byte_coordinates(self):
        text = "λ='x'\r\nx=2\r\n"
        projected = logical.project_application(text, [dict(start=1, end=1)])
        self.assertEqual(len(projected.encode('utf-8')), len(text.encode('utf-8')))
        result = logical.python_units(projected)
        self.assertEqual(result['logical_loc'], 1)
        self.assertEqual(result['owners'][0]['start'], len("λ='x'\r\n".encode('utf-8')))


class RetainedSourceQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (logical.ROOT / 'data/benchmarks.json').read_bytes()
        cls.data = json.loads(cls.raw)
        cls.native, cls.receipt = logical.load_native(cls.data)
        cls.manifest = logical.julia_input_manifest(cls.data)
        cls.captures = {row['input']: row for row in cls.native['sources']}

    def julia_fixture(self, name):
        row = self.manifest['fixture:' + name]
        return logical.julia_units(row['text'], self.captures[row['input']])

    def test_native_accepted_matrix_and_statement_pairs_are_invariant(self):
        for left, right, expected in [('matrix-packed', 'matrix-wrapped', 1),
                                      ('semicolon-packed', 'semicolon-expanded', 2),
                                      ('loop-packed', 'loop-expanded', 3)]:
            self.assertEqual(self.julia_fixture(left)['logical_loc'], expected)
            self.assertEqual(self.julia_fixture(right)['logical_loc'], expected)

    def test_structural_and_literal_punctuation_is_not_new_statements(self):
        for name, expected in [('keyword-semicolon', 1), ('literal-punctuation', 1),
                               ('quoted-code', 1), ('expression-function', 1),
                               ('block-function', 3), ('nested-block', 3), ('macro-block', 2)]:
            self.assertEqual(self.julia_fixture(name)['logical_loc'], expected)

    def test_native_rejection_hash_drift_tree_corruption_and_unknown_macros(self):
        bad = self.manifest['fixture:invalid']
        with self.assertRaisesRegex(logical.QualificationError, 'parse rejected'):
            logical.julia_units(bad['text'], self.captures[bad['input']])
        row = self.manifest['fixture:macro-block']
        capture = copy.deepcopy(self.captures[row['input']])
        with self.assertRaisesRegex(logical.QualificationError, 'hash differs'):
            logical.julia_units(row['text'] + ' ', capture)
        capture['nodes'][1]['parent'] = 999
        with self.assertRaisesRegex(logical.QualificationError, 'tree edge'):
            logical.julia_units(row['text'], capture)
        capture = copy.deepcopy(self.captures[row['input']])
        text = row['text'].replace('@inbounds', '@notknown')
        capture['source_sha256'] = logical.sha(text.encode('utf-8'))
        with self.assertRaisesRegex(logical.QualificationError, 'Unqualified Julia macro'):
            logical.julia_units(text, capture)

    def test_iterator_subtrees_cannot_hide_unknown_native_syntax(self):
        row = self.manifest['fixture:loop-expanded']
        capture = copy.deepcopy(self.captures[row['input']])
        iteration = next(node for node in capture['nodes'] if node['kind'] == 'iteration')
        child = next(node for node in capture['nodes'] if node['parent'] == iteration['id'])
        child['kind'] = 'UnqualifiedIteratorSyntax'
        with self.assertRaisesRegex(logical.QualificationError, 'Unqualified Julia expression kind'):
            logical.julia_units(row['text'], capture)

    def test_literal_macros_are_explicitly_allowlisted(self):
        row = self.manifest['regexredux:regexredux-julia-3']
        capture = copy.deepcopy(self.captures[row['input']])
        node = next(node for node in capture['nodes'] if node['kind'] == 'StrMacroName')
        raw = bytearray(row['text'].encode('utf-8'))
        self.assertEqual(bytes(raw[node['start']:node['end']]), b'r')
        raw[node['start']:node['end']] = b'q'
        text = bytes(raw).decode('utf-8')
        capture['source_sha256'] = logical.sha(bytes(raw))
        with self.assertRaisesRegex(logical.QualificationError, 'Unqualified Julia literal macro'):
            logical.julia_units(text, capture)

    def test_real_python_packed_spectralnorm_has_native_owners(self):
        item = logical.application_inputs(self.data)['spectralnorm:spectralnorm-python3-8']
        result = logical.python_units(item['text'])
        for line in (25, 34):
            self.assertEqual(sum(owner['units'] for owner in result['owners'] if owner['line'] == line), 3)
        variant = ast.unparse(ast.parse(item['text'])) + '\n'
        self.assertEqual(result['native_ast_sha256'], logical.python_units(variant)['native_ast_sha256'])
        self.assertEqual(result['logical_loc'], logical.python_units(variant)['logical_loc'])

    def test_exact_source_subset_qualifies_without_mutating_catalog(self):
        before = copy.deepcopy(self.data)
        report = logical.qualify(self.data, self.raw, self.native, self.receipt)
        self.assertEqual(self.data, before)
        self.assertEqual(report['coverage']['profiles'], 52)
        self.assertEqual(report['coverage']['unowned_significant_tokens'], 0)
        self.assertEqual(report['coverage']['profiles_by_language'], {'python': 18, 'julia': 17, 'julia-aot': 17})
        self.assertFalse(report['coverage']['all_language_suite_complete'])
        self.assertTrue(all(row['passed'] for row in report['fixtures']))
        self.assertEqual(report['profiles']['spectralnorm:spectralnorm-python3-8']['logical_loc'], 32)
        self.assertEqual(report['profiles']['regexredux:regexredux-julia-3']['logical_loc'], 19)
        self.assertFalse(report['policy']['generic_language_certificate'])


if __name__ == '__main__':
    unittest.main()
