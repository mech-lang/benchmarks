"""Pure reader-receipt checks; no Elixir, subprocess, or retained runtime reads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('elixir_loc', Path(__file__).with_name('elixir_loc.py'))
loc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loc)


class ReaderEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name)
        for name in ('started.json', 'report.json'):
            (self.output/name).write_text('{}')
        self.source = b'x = 1\n'
        source_hash = hashlib.sha256(self.source).hexdigest()
        self.plan = {'inputs': [{'id': 'sample', 'sha256': source_hash, 'expected_parse': 'ok'}]}
        self.report = {'items': [{'id': 'sample', 'formatted_sha256': source_hash}]}
        self.case = self.output/'sample'
        self.case.mkdir()
        (self.case/'source.exs').write_bytes(self.source)
        (self.case/'formatted.exs').write_bytes(self.source)
        (self.case/'ast.etf').write_bytes(b'\x83fixture')
        for name in ('ast.json', 'formatted-ast.json'):
            (self.case/name).write_text(json.dumps({'ast': ['tuple', []], 'comments': ['list', []]}))

    def tearDown(self):
        self.temporary.cleanup()

    def test_complete_inventory_and_changed_formatted_bytes(self):
        loc.validate_artifacts(self.report, self.plan, self.output)
        (self.case/'formatted.exs').write_bytes(b'x = 2\n')
        with self.assertRaisesRegex(AssertionError, 'Formatted artifact hash'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_missing_ast_is_not_a_successful_directory_walk(self):
        (self.case/'ast.json').unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing or unexpected reader artifacts'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_changed_source_and_unexpected_artifacts_are_rejected(self):
        (self.case/'source.exs').write_bytes(b'x = 2\n')
        with self.assertRaisesRegex(AssertionError, 'Retained source artifact changed'):
            loc.validate_artifacts(self.report, self.plan, self.output)
        (self.case/'source.exs').write_bytes(self.source)
        (self.output/'unplanned').write_text('extra')
        with self.assertRaisesRegex(AssertionError, 'Reader output inventory differs'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_malformed_native_term_is_rejected(self):
        (self.case/'ast.etf').write_bytes(b'')
        with self.assertRaisesRegex(AssertionError, 'Missing native ETF term'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_expected_rejection_requires_raw_parser_evidence(self):
        self.plan['inputs'][0]['expected_parse'] = 'error'
        for name in ('ast.etf', 'ast.json', 'formatted.exs', 'formatted-ast.json'):
            (self.case/name).unlink()
        (self.case/'parse-error.json').write_text(json.dumps({'error': ['tuple', []]}))
        loc.validate_artifacts(self.report, self.plan, self.output)
        (self.case/'parse-error.json').unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing or unexpected reader artifacts'):
            loc.validate_artifacts(self.report, self.plan, self.output)

    def test_only_clean_owned_normal_exit_can_complete_reader(self):
        valid = dict(pid=123, pgid=123, exit_status=0, final_exit_status=0, direct_child_reaped=True,
                     inherited_common_mutex=True, common_mutex_inode=79859134, remaining_process_group=[],
                     cleanup_errors=[], monitor_errors=[], stop_signals=[])
        loc.validate_receipt(valid)
        for changed in [dict(pid=0), dict(pgid=456), dict(exit_status=1), dict(final_exit_status=None),
                        dict(direct_child_reaped=False), dict(remaining_process_group=[456]),
                        dict(cleanup_errors=['failed']), dict(stop_signals=[9])]:
            with self.subTest(changed=changed), self.assertRaisesRegex(AssertionError, 'clean owned exit'):
                loc.validate_receipt(dict(valid, **changed))


if __name__ == '__main__':
    unittest.main()
