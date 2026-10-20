"""Offline evidence/ownership checks; never launch a native language process."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('clojure_source_units', ROOT / 'tools/clojure_logical_source_units.py')
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
PACKET = ROOT / TOOL.PACKET


class SourceSegmentationTests(unittest.TestCase):
    def test_complete_byte_roundtrip_with_comments_and_unicode(self):
        text = '(def β "🌱 ; #= []") ; ignored (fake)\r\n(def c \\))\n'
        tree = TOOL.source_tree(text)
        self.assertEqual(text, ''.join(token['text'] for token in tree['tokens']))
        self.assertEqual(2, len(tree['roots']))
        self.assertTrue(any(token['kind'] == 'comment' for token in tree['tokens']))
        self.assertTrue(any(token['kind'] == 'character' for token in tree['tokens']))

    def test_unsupported_reader_features_fail_in_source_scanner(self):
        for text in ['#=(+ 1 2)', '#custom/tag {}', '`(x ~y)', '#?(:clj 1)', '(def\u00a0x 1)']:
            with self.subTest(text=text), self.assertRaises(TOOL.QualificationError):
                TOOL.source_tree(text)


@unittest.skipUnless((PACKET / 'native-capture.json.gz').exists(), 'Native capture pending an authorized execution window')
class NativeReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = json.loads(gzip.decompress((PACKET / 'native-capture.json.gz').read_bytes()))
        cls.manifest = TOOL.inputs(ROOT)
        cls.report = TOOL.replay(ROOT)

    def test_all_retained_application_and_support_sources_are_bound(self):
        files = {part['job'] for profile in self.manifest['programs'].values() for part in profile['files']}
        supplemental = {row['job'] for row in self.manifest['supplemental_sources']}
        self.assertEqual(files | supplemental, {key for key in self.report['outcomes'] if key.startswith('file:')})
        self.assertTrue(all(self.report['outcomes'][key]['status'] != 'unqualified' for key in files))
        for profile in self.report['programs'].values():
            self.assertEqual(profile['submitted_logical_units'], profile['application_logical_units'] + profile['excluded_support_logical_units'])
            self.assertTrue(any(not part['included_in_application'] for part in profile['files']))

    def test_explicit_fixture_counts_and_packing_equivalences(self):
        self.assertTrue(self.report['summary']['all_fixture_expectations_pass'])
        self.assertTrue(self.report['summary']['all_pairs_pass'])
        self.assertEqual(1, self.report['outcomes']['fixture:pure-definition']['logical_units'])
        self.assertEqual(3, self.report['outcomes']['fixture:block-definition']['logical_units'])
        self.assertEqual(1, self.report['outcomes']['fixture:conditional-definition']['logical_units'])
        self.assertEqual(1, self.report['outcomes']['fixture:conditional-top-level']['logical_units'])
        self.assertEqual(2, self.report['outcomes']['fixture:conditional-loop-body']['logical_units'])
        self.assertEqual(3, self.report['outcomes']['fixture:conditional-block-branch-top-level']['logical_units'])

    def test_actual_source_variants_are_native_bound_and_equal(self):
        self.assertEqual(3, len(self.report['source_variants']))
        for variant in self.report['source_variants']:
            self.assertTrue(variant['passed'])
            self.assertNotEqual(variant['original_source_sha256'], variant['variant_sha256'])

    def test_negative_forms_fail_at_intended_stage(self):
        for name in ['disabled-read-eval', 'disabled-tag-reader', 'disabled-constructor-reader', 'invalid-reader']:
            self.assertFalse(self.native['jobs']['fixture:' + name]['accepted'])
        for name in ['unknown-macro', 'unsupported-core-macro', 'unknown-default-macro']:
            self.assertTrue(self.native['jobs']['fixture:' + name]['accepted'])
            row = self.report['outcomes']['fixture:' + name]
            self.assertEqual('unqualified', row['status'])
            self.assertIn('Unqualified', row['reason'])

    def test_source_drift_and_missing_native_trace_fail_closed(self):
        job = self.manifest['jobs']['fixture:matrix-packed']
        native = self.native['jobs']['fixture:matrix-packed']
        with self.assertRaises(TOOL.QualificationError):
            TOOL.owners(job['text'] + ' ', TOOL.source_tree(job['text'] + ' '), native)
        changed = copy.deepcopy(native); changed['events'] = []
        with self.assertRaises(TOOL.QualificationError):
            TOOL.owners(job['text'], TOOL.source_tree(job['text']), changed)

    def test_draft_scope_is_never_a_canonical_or_language_certificate(self):
        self.assertFalse(self.report['canonical_changed'])
        self.assertFalse(self.report['generic_language_certificate'])
        self.assertEqual('native-qualified-exact-source-subset', self.report['status'])

    def test_reify_method_parameter_destructuring_fails_closed(self):
        # A source-tree mutation uses existing native evidence only. It checks
        # the fail-closed policy guard, not native acceptance of unseen syntax.
        key = 'file:ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446'
        text = self.manifest['jobs'][key]['text']; tree = TOOL.source_tree(text)
        nodes = {node['id']: node for node in tree['nodes']}
        parameter = next(node for node in nodes.values() if node['kind'] == 'vector' and text.encode()[node['start']:node['end']] == b'[_]')
        nodes[parameter['children'][0]]['kind'] = 'map'
        with self.assertRaisesRegex(TOOL.QualificationError, 'Reify method parameter'):
            TOOL.owners(text, tree, self.native['jobs'][key])


if __name__ == '__main__':
    unittest.main()
