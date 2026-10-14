"""Identity and owner-coverage checks using three small retained source files."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retained_uiua_owners', HERE/'uiua_retained_source_units.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
COHORT = HERE.parents[1]/'archive/comparisons/r-apl-uiua-comparison/20261011'
SOURCES = {
    'nbody-compact': COHORT/'uiua-nbody-v3/sources/compact.ua',
    'nbody-fast': COHORT/'uiua-nbody-v3/sources/fast.ua',
    'binarytrees': COHORT/'sources/uiua/binarytrees/compact.ua',
}


class Owners(unittest.TestCase):
    def test_complete_owner_coverage_and_unavailable_formatting(self):
        for name, path in SOURCES.items():
            with self.subTest(name=name):
                row = u.count_source(path.read_bytes(), name)
                expected = (15,11,1,3) if name == 'binarytrees' else (21,19,0,2)
                self.assertEqual(tuple(row[k] for k in ('canonical_loc','independent_bindings',
                    'record_declarations','output_statements')), expected)
                self.assertEqual([v['line'] for v in row['source_owners']], list(range(1,expected[0]+1)))
                self.assertIsNone(row['formatted_loc'])
                self.assertFalse(row['generic_language_certificate'])
                self.assertFalse(row['chart_admission'])

    def test_tree_alias_has_identical_count_without_inventing_source(self):
        compact = SOURCES['binarytrees'].read_bytes()
        alias = (COHORT/'sources/uiua/binarytrees/fast.ua').read_bytes()
        self.assertEqual(alias, compact)
        self.assertEqual(u.count_source(alias,'binarytrees'),u.count_source(compact,'binarytrees'))

    def test_changed_semantics_and_new_owners_cannot_fall_back_to_line_count(self):
        for identity,path in SOURCES.items():
            raw=path.read_bytes()
            for changed in (raw.replace(b'&args',b'&other'),raw+b'Other \xe2\x86\x90 1\n',raw.replace(b'\n',b'\r\n')):
                with self.subTest(identity=identity),self.assertRaises(ValueError):
                    u.count_source(changed,identity)

    def test_unknown_and_wrongly_relabelled_sources_rejected(self):
        for identity in ('unknown','nbody-fast','binarytrees'):
            with self.assertRaises(ValueError):u.count_source(SOURCES['nbody-compact'].read_bytes(),identity)
        with self.assertRaises(ValueError):u.count_source('not bytes','nbody-compact')


if __name__ == '__main__':
    unittest.main()
