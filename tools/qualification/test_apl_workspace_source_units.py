"""Pure exact-input and complete measured-bundle count checks."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('apl_workspace_owners', HERE / 'apl_workspace_source_units.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class Owners(unittest.TestCase):
    def setUp(self):
        self.sources = {identity: (a.ROOT / row['path']).read_bytes()
                        for identity, row in a.SOURCES.items()}

    def test_complete_bundle_includes_setup_without_multiplying_aliases(self):
        result = a.count_bundle(self.sources)
        self.assertEqual((result['canonical_loc'], result['original_physical_loc']), (41, 41))
        self.assertEqual([row['canonical_loc'] for row in result['sources']], [40, 1])
        self.assertEqual(result['source_forms'], ['compact', 'optimized'])
        self.assertEqual(result['distinct_authored_main_sources'], 1)
        self.assertEqual(result['distinct_source_bundles'], 1)
        self.assertIsNone(result['formatted_loc'])
        for flag in ('native_execution', 'generic_language_certificate', 'full_size_work_qualified',
                     'full_timing_qualified', 'chart_admission'):
            self.assertFalse(result[flag])

    def test_every_written_row_has_exactly_one_owner_or_exclusion(self):
        for identity, source in self.sources.items():
            with self.subTest(identity=identity):
                row = a.count_source(source, identity)
                coverage = [x['line'] for field in ('source_owners', 'excluded_rows') for x in row[field]]
                self.assertEqual(sorted(coverage), list(range(1, len(source.decode().splitlines()) + 1)))
        main = a.count_source(self.sources['binarytrees-main'], 'binarytrees-main')
        self.assertEqual(main['function_pairs'], [dict(header_line=5, close_line=12),
                                                 dict(header_line=13, close_line=17),
                                                 dict(header_line=18, close_line=38)])
        self.assertEqual(main['independent_statement_rows'], 34)
        self.assertEqual(main['excluded_rows'], [dict(line=1, reason='comment'), dict(line=40, reason='blank')])
        setup = a.count_source(self.sources['workspace-setup'], 'workspace-setup')
        self.assertEqual(setup['independent_statement_rows'], 1)
        self.assertEqual(setup['function_pairs'], [])

    def test_missing_or_extra_bundle_member_is_rejected(self):
        for sources in ({'binarytrees-main': self.sources['binarytrees-main']},
                        {**self.sources, 'unmeasured-helper': b'X\n'}, {}):
            with self.assertRaises(ValueError):
                a.count_bundle(sources)

    def test_modified_source_has_no_physical_fallback(self):
        for identity, source in self.sources.items():
            for changed in (source + b'X\n', source.replace(b'\n', b'\r\n'), source[:-1]):
                with self.subTest(identity=identity), self.assertRaises(ValueError):
                    a.count_source(changed, identity)
        with self.assertRaises(ValueError):
            a.count_source(self.sources['binarytrees-main'], 'workspace-setup')
        with self.assertRaises(ValueError):
            a.count_source(self.sources['binarytrees-main'], 'unknown')

    def test_frozen_nine_source_registry_is_unchanged(self):
        spec = importlib.util.spec_from_file_location('original_apl_owners', a.READER)
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        self.assertEqual(len(original.SOURCES), 9)
        self.assertNotIn('binarytrees-main', original.SOURCES)
        self.assertNotEqual(original.POLICY, a.POLICY)


if __name__ == '__main__':
    unittest.main()
