"""Independent case/spec-binding regressions using synthetic native artifacts."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location('elixir_receipt_review_fixtures',
    Path(__file__).with_name('test_elixir_work.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
work = fixtures.work


class PreparedCaseIdentity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_stage = work.STAGE
        work.STAGE = self.root
        self.output, self.plan, self.report = fixtures.fixture(self.root)
        self.row = self.plan['profiles'][0]
        self.directory = self.output/self.row['id']

    def tearDown(self):
        work.STAGE = self.old_stage
        self.tmp.cleanup()

    def refresh_snapshot(self):
        """Model inconsistent bytes that were already present at validation."""
        observation = next(row for row in self.report['profiles'] if row['id'] == self.row['id'])
        observation['process_sha256'] = work.sha(self.directory/'process.json')
        self.report['validated_profile_artifacts'][self.row['id']] = work.snapshot_observation(self.directory)

    def require_rejected(self):
        self.assertTrue(work.reconcile_native(self.report, self.plan, self.output, fixtures.SUPERVISOR))

    def test_changed_spec_cannot_become_a_validated_snapshot(self):
        specification = work.read(self.directory/'spec.json')
        specification['ebin'] = '/unrelated/retained-subject'
        fixtures.write(self.directory/'spec.json', specification)
        self.refresh_snapshot()
        self.require_rejected()

    def test_changed_stdin_cannot_be_hidden_by_consistent_stream_receipt(self):
        path = self.directory/'stdin.bin'
        path.write_bytes(b'different prepared case')
        for name in ('start.json', 'active.json', 'process.json'):
            process = work.read(self.directory/name)
            process.update(stdin_bytes=path.stat().st_size, stdin_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            fixtures.write(self.directory/name, process)
        self.refresh_snapshot()
        self.require_rejected()

    def test_changed_expected_copy_cannot_become_a_validated_snapshot(self):
        (self.directory/'expected.stdout').write_bytes(b'not the frozen reference')
        self.refresh_snapshot()
        self.require_rejected()

    def test_report_workload_cannot_select_a_different_contract(self):
        observation = next(row for row in self.report['profiles'] if row['id'] == self.row['id'])
        observation['benchmark'] = 'regexredux'
        self.require_rejected()

    def test_start_record_cannot_describe_another_command(self):
        record = work.read(self.directory/'start.json')
        record['command'] = ['/unrelated/program']
        fixtures.write(self.directory/'start.json', record)
        self.refresh_snapshot()
        self.require_rejected()

    def test_active_pid_must_match_the_final_owned_process(self):
        record = work.read(self.directory/'active.json')
        record['pid'] += 1
        fixtures.write(self.directory/'active.json', record)
        self.refresh_snapshot()
        self.require_rejected()

    def test_direct_child_already_zombie_at_initial_identity_is_valid(self):
        for name in ('active.json', 'process.json'):
            record = work.read(self.directory/name)
            record['identity']['status'] = 5
            fixtures.write(self.directory/name, record)
        self.refresh_snapshot()
        self.assertEqual(work.reconcile_native(self.report, self.plan, self.output, fixtures.SUPERVISOR), [])


if __name__ == '__main__':
    unittest.main()
