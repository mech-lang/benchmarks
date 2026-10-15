"""Focused owner/provenance checks; authored while native timing is active.

Execution is deferred. Fixtures exercise exact reviewed spans, not a generic
Rebol parser or a native runtime. The current fifteen sources remain unqualified.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rebol_source_units_under_test', HERE / 'rebol_source_units.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
ledger = c.load_ledger()
FIXTURES = c.ROOT / 'experiments/rebol/source-counts-v1/fixtures'


def rebol_fixture():
    return ledger.source('fixtures/owners.reb', 12,
        rows={'D': '1 3-4', 'C': '11-12'}, headers=(2, 8), packed={
            5: ledger.block('f: func [x [integer!] /local y]', 'y: x + 1', 'y'),
            6: ledger.block('while [chunk: read-chunk not none? chunk]', 'append values chunk'),
            7: ledger.parts(('H', 'sort/compare values func [a b]'), ('O', '['),
                            ('V', 'either a = b [false] [a < b]'), ('C', ']')),
            9: ledger.block('empty? values'),
            10: ledger.block('true', 'append values 5', 'clear values'),
        })


def c_fixture():
    return ledger.source('fixtures/owners.c', 13,
        rows={'M': '1', 'P': '2', 'S': '3 12', 'D': '4-5', 'C': '13'},
        headers=(8,), packed={
            6: ledger.parts(('H', 'enum'), ('O', '{'), ('E', 'A,'), ('E', 'B,')),
            7: ledger.parts(('E', 'C'), ('C', '};')),
            9: ledger.parts(('S', 'int a,'), ('S', 'b;')),
            10: ledger.parts(('S', 'a ='), ('S', 'b = 0;')),
            11: ledger.parts(('H', 'for (int i = 0; i < WIDTH; ++i)'), ('O', '{'),
                             ('S', 'a += i;'), ('S', 'b += i;'), ('C', '}')),
        })


class OwnerBoundaryTests(unittest.TestCase):
    def test_rebol_function_callback_case_and_data_owners(self):
        result = c.project((FIXTURES / 'owners.reb').read_bytes(), rebol_fixture(), ledger.KINDS)
        self.assertEqual((result['canonical_loc'], result['physical_loc']), (23, 12))
        rows = {entry['line']: entry['canonical_units'] for entry in result['row_totals']}
        self.assertEqual({n: rows[n] for n in (3, 4, 5, 6, 7, 9, 10)},
                         {3: 1, 4: 1, 5: 4, 6: 3, 7: 3, 9: 2, 10: 4})
        loop = [o for o in result['source_owners'] if o['line'] == 6 and o['tag'] == 'H']
        self.assertEqual(loop[0]['text'], 'while [chunk: read-chunk not none? chunk]')
        self.assertFalse(result['canonical_LOC_admitted'])
        self.assertFalse(result['generic_language_certificate'])

    def test_c_bindings_enum_and_embedded_source_data(self):
        result = c.project((FIXTURES / 'owners.c').read_bytes(), c_fixture(), ledger.KINDS)
        self.assertEqual((result['canonical_loc'], result['physical_loc']), (20, 12))
        rows = {entry['line']: entry['canonical_units'] for entry in result['row_totals']}
        self.assertEqual({n: rows[n] for n in (1, 4, 5, 6, 7, 9, 10, 11)},
                         {1: 0, 4: 1, 5: 1, 6: 3, 7: 2, 9: 2, 10: 2, 11: 4})
        for owner in result['source_owners']:
            raw = (FIXTURES / 'owners.c').read_bytes()
            self.assertEqual(raw[owner['start']:owner['end']].decode('ascii'), owner['text'])

    def test_packed_operation_cannot_be_added_or_reordered(self):
        raw = (FIXTURES / 'owners.reb').read_bytes()
        for changed in (raw.replace(b'append values 5 clear values', b'append values 5 clear values print 1'),
                        raw.replace(b'append values 5 clear values', b'clear values append values 5')):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                c.project(changed, rebol_fixture(), ledger.KINDS)

    def test_missing_or_overlapping_owner_is_rejected(self):
        raw = (FIXTURES / 'owners.reb').read_bytes()
        missing = rebol_fixture()
        missing['packed'].pop(5)
        with self.assertRaisesRegex(ValueError, 'Unowned significant'):
            c.project(raw, missing, ledger.KINDS)
        duplicate = rebol_fixture()
        duplicate['rows']['S'] = '5'
        with self.assertRaisesRegex(ValueError, 'Duplicate row'):
            c.project(raw, duplicate, ledger.KINDS)

    def test_repeated_fragments_keep_distinct_spans(self):
        spec = ledger.source('fixture.reb', 1, rows={}, packed={
            1: ledger.block('loop 2', 'append x 1', 'append x 1'),
        })
        raw = b'loop 2 [append x 1 append x 1]\n'
        result = c.project(raw, spec, ledger.KINDS)
        statements = [owner for owner in result['source_owners'] if owner['tag'] == 'S']
        self.assertEqual(result['canonical_loc'], 4)
        self.assertLess(statements[0]['end'], statements[1]['start'])

    def test_multiline_header_has_one_header_and_retains_physical_rows(self):
        raw = b'f: func [x [integer!]\n    /local y] [\n    x\n]\n'
        spec = ledger.source('fixture.reb', 4, rows={'S': '3', 'C': '4'}, headers=((1, 2),))
        result = c.project(raw, spec, ledger.KINDS)
        self.assertEqual((result['canonical_loc'], result['physical_loc']), (3, 4))
        header = result['source_owners'][0]
        self.assertEqual((header['line'], header['last_line']), (1, 2))
        self.assertIn('/local y]', header['text'])

    def test_unlisted_nonblank_row_has_no_physical_fallback(self):
        raw = b'f: func [] [\nprint 1\n]\n'
        spec = ledger.source('fixture.reb', 3, rows={'C': '3'}, headers=(1,))
        with self.assertRaisesRegex(ValueError, 'Unowned significant'):
            c.project(raw, spec, ledger.KINDS)

    def test_unprepared_identity_is_not_counted_even_if_layout_matches(self):
        raw = (FIXTURES / 'owners.reb').read_bytes()
        temporary = SimpleNamespace(SOURCES={'fixture': rebol_fixture()}, KINDS=ledger.KINDS, RULE=ledger.RULE)
        with self.assertRaisesRegex(ValueError, 'freeze.*pending'):
            c.count_source(raw, 'fixture', temporary)
        temporary.SOURCES['fixture']['reviewed_source_sha256'] = hashlib.sha256(raw).hexdigest()
        result = c.count_source(raw, 'fixture', temporary)
        self.assertTrue(result['source_identity_reviewed'])
        self.assertFalse(result['canonical_LOC_admitted'])
        with self.assertRaisesRegex(ValueError, 'Source bytes differ'):
            c.count_source(raw.replace(b'3 4]', b'3 5]'), 'fixture', temporary)

    def test_fifteen_exact_layouts_and_unprepared_gates(self):
        self.assertEqual(len(ledger.SOURCES), 15)
        for identity, specification in ledger.SOURCES.items():
            with self.subTest(identity=identity):
                self.assertIsNone(specification['reviewed_source_sha256'])
                raw = (c.ROOT / specification['path']).read_bytes()
                result = c.project(raw, specification, ledger.KINDS)
                self.assertFalse(result['canonical_LOC_admitted'])
                self.assertFalse(result['source_identity_reviewed'])
                self.assertEqual(result['unowned_significant_characters'], [])
                with self.assertRaisesRegex(ValueError, 'freeze.*pending'):
                    c.count_source(raw, identity, ledger)

    def test_exact_bundle_membership_and_corrected_c_substitution(self):
        result = c.propose(c.ROOT, ledger)
        sizes = [len(bundle['files']) for bundle in result['bundles'].values()]
        self.assertEqual((sizes.count(4), sizes.count(5)), (8, 2))
        paths = {source['source_path'] for source in result['sources'].values()}
        self.assertIn(ledger.CORRECTED_C, paths)
        self.assertNotIn(ledger.ORIGINAL_C, paths)
        self.assertIn(ledger.CORRECTED_FANN, paths)
        self.assertNotIn(ledger.ORIGINAL_FANN, paths)
        self.assertEqual(result['corrected_fannkuch_substitution']['counted'], ledger.CORRECTED_FANN)
        for name, bundle in result['bundles'].items():
            self.assertEqual(sum(item['identity'] == 'extension' for item in bundle['files']), 1)
            self.assertEqual(bundle['source_forms'], 1)
            self.assertEqual(bundle['native_samples'], 0)
            self.assertFalse(bundle['canonical_LOC_admitted'])
        broken = SimpleNamespace(**{name: getattr(ledger, name) for name in
            ('SOURCES', 'BUNDLES', 'KINDS', 'RULE', 'ORIGINAL_C', 'CORRECTED_C',
             'ORIGINAL_FANN', 'CORRECTED_FANN', 'DECISIONS')})
        broken.BUNDLES = copy.deepcopy(ledger.BUNDLES)
        broken.BUNDLES['pidigits'] = broken.BUNDLES['pidigits'] + ('extension',)
        with self.assertRaisesRegex(ValueError, 'counted twice'):
            c.propose(c.ROOT, broken)

    def test_actual_c_nine_command_rows_and_enum_are_retained(self):
        raw = (c.ROOT / ledger.CORRECTED_C).read_bytes()
        result = c.project(raw, ledger.SOURCES['extension'], ledger.KINDS)
        enums = [owner for owner in result['source_owners'] if owner['tag'] == 'E']
        self.assertEqual(len(enums), 9)
        commands = [owner for owner in result['source_owners'] if 27 <= owner['line'] <= 35]
        self.assertEqual(len(commands), 9)
        self.assertTrue(all(owner['tag'] == 'D' and owner['canonical_units'] == 1 for owner in commands))
        chain = [owner for owner in result['source_owners'] if owner['line'] == 222]
        self.assertEqual([owner['canonical_units'] for owner in chain], [1, 1])

    def test_regular_source_rejects_alias_or_special_path_before_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'real').write_bytes(b'x\n')
            (root / 'alias').symlink_to(root / 'real')
            with self.assertRaisesRegex(ValueError, 'nonsymlink'):
                c.regular_source(root, 'alias')
            (root / 'folder').mkdir()
            with self.assertRaisesRegex(ValueError, 'regular'):
                c.regular_source(root, 'folder')


if __name__ == '__main__':
    unittest.main()
