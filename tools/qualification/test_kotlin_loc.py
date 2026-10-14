"""Pure saved-PSI/receipt validation tests; no JDK launch or runtime hashing."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('kotlin_loc', Path(__file__).with_name('kotlin_loc.py'))
loc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loc)


def fixture(source='val x = "😀"\n', parsed=None, error=False):
    parsed = source if parsed is None else parsed
    digest = hashlib.sha256(source.encode()).hexdigest()
    expected = dict(id='fixture', sha256=digest, expected_parse='error' if error else 'ok', reader_path='/fixture.kt')
    length = len(loc.utf16(parsed))//2
    def node(index, parent, a, b, children, **fields):
        return dict(id=index, parent=parent, start_utf16=a, end_utf16=b, children=children,
                    psi_class='NativePsiFixture', element_type='ERROR_ELEMENT' if error and index == 1 else 'TOKEN',
                    comment=False, whitespace=False, **fields)
    nodes = [node(0, -1, 0, length, [1]), node(1, 0, 0, length, [], text=parsed)]
    errors = [dict(node=1, start_utf16=0, end_utf16=length, message='Expected expression')] if error else []
    evidence = dict(schema='kotlin-native-psi-source-v1', id='fixture', source_path='/fixture.kt',
                    source_sha256=digest, psi_source_sha256=hashlib.sha256(parsed.encode()).hexdigest(),
                    offset_units='UTF-16 code units', source_utf16_length=length,
                    newline_normalization_observed=source != parsed, leaf_coverage_complete=True,
                    nodes=nodes, parse_errors=errors)
    return expected, evidence, source, parsed


class PsiTests(unittest.TestCase):
    def test_utf16_non_bmp_and_crlf_are_not_python_character_offsets(self):
        expected, evidence, source, parsed = fixture('val x = "😀"\r\n', 'val x = "😀"\n')
        loc.validate_psi(evidence, source, parsed, expected)
        evidence['source_utf16_length'] = len(parsed)
        with self.assertRaisesRegex(AssertionError, 'offset metadata'):
            loc.validate_psi(evidence, source, parsed, expected)

    def test_no_parser_rewriting_beyond_newline_normalization(self):
        expected, evidence, source, parsed = fixture('val x = 1\n', 'val x = 2\n')
        with self.assertRaisesRegex(AssertionError, 'beyond newline'):
            loc.validate_psi(evidence, source, parsed, expected)

    def test_zero_width_nodes_cover_no_extra_source(self):
        expected, evidence, source, parsed = fixture('x')
        root, leaf = evidence['nodes']
        root['children'] = [1, 2]
        empty = dict(leaf, start_utf16=0, end_utf16=0, text='')
        evidence['nodes'] = [root, empty, dict(leaf, id=2)]
        loc.validate_psi(evidence, source, parsed, expected)
        evidence['nodes'][2]['start_utf16'] = 1
        evidence['nodes'][2]['text'] = ''
        with self.assertRaisesRegex(AssertionError, 'partition parent'):
            loc.validate_psi(evidence, source, parsed, expected)

    def test_duplicate_child_missing_node_and_parent_substitution_fail(self):
        expected, original, source, parsed = fixture()
        for change in ('duplicate', 'unreferenced', 'wrong-parent'):
            evidence = copy.deepcopy(original)
            if change == 'duplicate':
                evidence['nodes'][0]['children'] = [1, 1]
            elif change == 'unreferenced':
                evidence['nodes'].append(dict(evidence['nodes'][1], id=2))
            else:
                evidence['nodes'][1]['parent'] = -1
            with self.subTest(change=change), self.assertRaises(AssertionError):
                loc.validate_psi(evidence, source, parsed, expected)

    def test_native_errors_must_match_nodes_and_expected_outcome(self):
        expected, evidence, source, parsed = fixture('fun f(', error=True)
        loc.validate_psi(evidence, source, parsed, expected)
        with self.assertRaisesRegex(AssertionError, 'Unexpected native parse outcome'):
            loc.validate_psi(evidence, source, parsed, dict(expected, expected_parse='ok'))
        evidence['parse_errors'] = []
        with self.assertRaisesRegex(AssertionError, 'error-node inventory'):
            loc.validate_psi(evidence, source, parsed, expected)

    def test_changed_leaf_text_is_not_accepted_on_range_alone(self):
        expected, evidence, source, parsed = fixture()
        evidence['nodes'][1]['text'] = parsed.replace('x', 'y')
        with self.assertRaisesRegex(AssertionError, 'leaf text differs'):
            loc.validate_psi(evidence, source, parsed, expected)

    def test_manifest_continuations_and_per_entry_attributes(self):
        raw = b'Manifest-Version: 1.0\r\nClass-Path: a.jar \r\n b.jar\r\n\r\nName: file\r\nClass-Path: ignored.jar\r\n'
        self.assertEqual(loc.manifest_fields(raw), {'manifest-version': '1.0', 'class-path': 'a.jar b.jar'})
        with self.assertRaisesRegex(AssertionError, 'duplicate'):
            loc.manifest_fields(b'Class-Path: a.jar\nclass-path: b.jar\n')


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name)
        expected, evidence, source, parsed = fixture()
        self.plan = dict(inputs=[expected])
        self.directory = self.output/'fixture'; self.directory.mkdir()
        (self.directory/'source.kt').write_bytes(source.encode())
        (self.directory/'psi-source.kt').write_bytes(parsed.encode())
        (self.directory/'psi.json').write_text(json.dumps(evidence))
        actual = dict(id=expected['id'], source_sha256=expected['sha256'], psi_sha256=loc.sha(self.directory/'psi.json'),
                      psi_source_sha256=loc.sha(self.directory/'psi-source.kt'), canonical_loc=None, formatted_loc=None,
                      nodes=2, parse_errors=0, status='parsed')
        self.report = dict(items=[actual])
        (self.output/'report.json').write_text(json.dumps(self.report))
        (self.output/'started.json').write_text('{}')

    def tearDown(self):
        self.temporary.cleanup()

    def test_complete_artifacts_and_missing_psi(self):
        loc.validate_artifacts(self.report, self.plan, self.output)
        (self.directory/'psi.json').unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing or unexpected'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_preserved_original_crlf_bytes_are_required(self):
        (self.directory/'source.kt').write_bytes(b'val x = "other"\n')
        with self.assertRaisesRegex(AssertionError, 'artifact hash differs'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_no_premature_loc_and_no_unreported_inputs(self):
        self.report['items'][0]['canonical_loc'] = 1
        with self.assertRaisesRegex(AssertionError, 'identity/count'):
            loc.validate_artifacts(self.report, self.plan, self.output)
        self.report['items'][0]['canonical_loc'] = None
        (self.output/'unreported.kt').write_text('x')
        with self.assertRaisesRegex(AssertionError, 'inventory differs'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_wrong_parser_input_path_fails_even_with_current_artifact_hash(self):
        path = self.directory/'psi.json'
        evidence = json.loads(path.read_bytes()); evidence['source_path'] = '/another.kt'
        path.write_text(json.dumps(evidence)); self.report['items'][0]['psi_sha256'] = loc.sha(path)
        with self.assertRaisesRegex(AssertionError, 'different input path'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_native_failure_or_unreaped_process_is_not_a_completed_reader(self):
        valid = dict(kind='native-source-reader', status='native-passed', native_process_started=True,
                     pid=123, pgid=123, exit_status=0, direct_child_reaped=True, inherited_common_mutex=True,
                     common_mutex_inode=loc.LOCK_INODE, remaining_process_group=[], cleanup_errors=[],
                     artifact_errors=[], stop_signals=[])
        loc.validate_receipt(valid, 'native-source-reader')
        for change in [dict(pid=0), dict(exit_status=1), dict(direct_child_reaped=False), dict(stop_signals=[9]),
                       dict(remaining_process_group=[124]), dict(artifact_errors=['missing'])]:
            with self.subTest(change=change), self.assertRaisesRegex(AssertionError, 'clean owned exit'):
                loc.validate_receipt(dict(valid, **change), 'native-source-reader')

    def test_artifact_walk_preserves_partial_inventory_and_records_denial(self):
        def denied(root, onerror, followlinks):
            yield str(root), [], ['report.json']
            onerror(PermissionError(13, 'Cannot read directory', str(root/'unreadable')))
        errors = []
        with patch.object(loc.os, 'walk', side_effect=denied):
            files = loc.inventory_files(self.output, errors)
        self.assertEqual(files, [self.output/'report.json'])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['path'], str(self.output/'unreadable'))

    def test_dangling_symlink_is_an_artifact_error(self):
        link = self.output/'missing'; link.symlink_to(self.output/'absent-target')
        errors = []; files = loc.inventory_files(self.output, errors)
        self.assertNotIn(link, files)
        self.assertTrue(any(error['path'] == str(link) and 'symlink' in error['error'] for error in errors))


if __name__ == '__main__':
    unittest.main()
