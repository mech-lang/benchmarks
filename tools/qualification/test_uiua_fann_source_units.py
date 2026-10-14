"""Exact-identity and coverage regressions; no Uiua execution."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('uiua_units_test', HERE/'uiua_fann_source_units.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
SOURCES = HERE.parents[1]/'archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/sources'


class SourceOwners(unittest.TestCase):
    def test_complete_authored_owner_coverage(self):
        for variant, total, bindings in [('compact', 20, 14), ('fast', 21, 15)]:
            with self.subTest(variant=variant):
                value = u.count_source((SOURCES/(variant+'.ua')).read_bytes(), variant)
                self.assertEqual(value['canonical_loc'], total)
                self.assertEqual(value['independent_bindings'], bindings)
                self.assertEqual(value['record_declarations'], 4)
                self.assertEqual(value['output_statements'], 2)
                self.assertEqual([v['line'] for v in value['source_owners']], list(range(1, total+1)))
                self.assertEqual(value['unowned_noncomment_lines'], [])
                self.assertIsNone(value['formatted_loc'])
                self.assertFalse(value['generic_language_certificate'])
                self.assertFalse(value['chart_admission'])

    def test_source_cannot_be_relabelled_as_other_form(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            u.count_source((SOURCES/'compact.ua').read_bytes(), 'fast')

    def test_semantic_mutation_is_not_a_physical_line_fallback(self):
        source = (SOURCES/'compact.ua').read_bytes()
        for changed in [source.replace(b'1024', b'2048'), source + b'Other \xe2\x86\x90 1\n',
                        source.replace(b'\n', b'\r\n'), source.replace(b'Widths', b'Widths Other', 1)]:
            with self.subTest(changed=changed[-40:]):
                with self.assertRaisesRegex(ValueError, 'identity'):
                    u.count_source(changed, 'compact')

    def test_unknown_identity_and_nonbytes_rejected(self):
        for source, variant in [(b'', 'other'), ('N ← 12', 'compact'), (b'N <- 12\n', 'compact')]:
            with self.assertRaises(ValueError):
                u.count_source(source, variant)


if __name__ == '__main__':
    unittest.main()
