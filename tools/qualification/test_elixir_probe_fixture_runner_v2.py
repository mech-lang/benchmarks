"""Tiny mocked one-shot fixture-launcher regressions; no native execution."""
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2]/'experiments/elixir/compiled-work-v1/run-probe-fixtures-v2.py'
SPEC = importlib.util.spec_from_file_location('elixir_fixture_runner', PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def save(path, value):
    Path(path).write_text(json.dumps(value))


def observe(command, environment, directory, payload, lock, launched, *, kind):
    pid = 1234
    empty = hashlib.sha256(b'').hexdigest()
    identity = dict(pid=pid, ppid=os.getpid(), pgid=pid, birth_seconds=100, birth_microseconds=25, status=2)
    start = dict(kind=kind, status='starting', native_process_started=False, command=command,
        environment=environment, cwd=str(directory), started_at='2026-10-14T07:00:00+00:00',
        process_timeout_seconds=30, cleanup_timeout_seconds=5, inherited_common_mutex=True,
        common_mutex_inode=79859134, stop_signals=[], cleanup_errors=[], benchmark_samples=0,
        stdin_bytes=0, stdin_sha256=empty, maximum_process_group_rss_bytes=2*1024**3,
        native_file_limit_bytes=8*1024**2, stdout_capture_limit_bytes=8*1024**2+65536,
        stdout_transport='OS pipe, retained as received', stderr_transport='exclusive artifact',
        source_work_qualified=False, chart_admission=False, kernel_monitor_samples=0,
        observed_peak_process_group_rss_bytes=0)
    save(directory/'start.json', start)
    launched(pid)
    save(directory/'active.json', dict(start, status='running', native_process_started=True,
                                      pid=pid, pgid=pid, identity=identity))
    (directory/'stdout.bin').write_bytes(b'Running ExUnit with seed: 123\n...............\n15 tests, 0 failures\n')
    (directory/'stderr.bin').write_bytes(b'')
    process = dict(start, status='native-passed', native_process_started=True, pid=pid, pgid=pid,
        identity=identity, leader_identity_before_reap=dict(identity, status=5), direct_child_reaped=True,
        remaining_process_group=[], exit_status=0, kernel_monitor_samples=2,
        observed_peak_process_group_rss_bytes=1024, finished_at='2026-10-14T07:00:01+00:00')
    for name in ('stdout', 'stderr'):
        path = directory/(name+'.bin')
        process[name+'_bytes'] = path.stat().st_size
        process[name+'_sha256'] = runner.sha(path)
    save(directory/'process.json', process)
    return process


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.plan = self.root/'reader-plan.json'
        self.observer_source = self.root/'observer.py'; self.observer_source.write_bytes(b'observer fixture')
        self.python = self.root/'python'; self.python.write_bytes(b'python fixture')
        self.sources = {}
        for name in ('probe.exs', 'probe-review-tests.exs'):
            path = self.root/('probe-v2.exs' if name == 'probe.exs' else name); path.write_bytes(name.encode())
            self.sources[name] = runner.sha(path)
        save(self.plan, dict(schema='elixir-source-reader-plan-v1', pins={}, runtime='/retained/elixir',
            runtime_environment={'PATH':'/retained/bin:/bin', 'ELIXIR_ERL_OPTIONS':'+S 8:8 +A 1 +SDcpu 1:1 +SDio 1'}))
        self.supervisor = SimpleNamespace(TIMEOUT=30, CLEANUP_TIMEOUT=5, RSS_LIMIT=2*1024**3,
            FILE_LIMIT=8*1024**2, PIPE_CHUNK=65536, LOCK_INODE=79859134, save=save,
            atomic=nullcontext, observe=observe,
            kh=SimpleNamespace(PYTHON=self.python, PYTHON_SHA=runner.sha(self.python), verify_lock=lambda lock: None))
        self.args = SimpleNamespace(output=self.root/'probe-fixtures-v1', controller_sha256=runner.sha(PATH))
        for name, value in {'STAGE':self.root, 'READER_PLAN':self.plan, 'READER_PLAN_SHA':runner.sha(self.plan),
                            'SUPERVISOR':self.observer_source, 'SUPERVISOR_SHA':runner.sha(self.observer_source),
                            'SOURCE_PINS':self.sources}.items():
            context = patch.object(runner, name, value); context.start(); self.addCleanup(context.stop)

    def execute(self):
        with patch('subprocess.Popen', side_effect=AssertionError('Native launch forbidden')), patch('builtins.print'):
            runner.run(self.args, self.supervisor, object())

    def terminal(self):
        return runner.read(self.args.output/'terminal.json')

    def test_one_clean_command_closes_with_all_artifacts_and_never_reuses_output(self):
        self.execute()
        terminal = self.terminal()
        self.assertEqual(terminal['status'], runner.COMPLETE)
        self.assertTrue(terminal['diagnostic_fixtures_passed'])
        self.assertEqual(terminal['native_processes_started'], 1)
        self.assertEqual(terminal['fixture_summary'], {'tests':15, 'failures':0})
        artifacts, errors = runner.inventory(self.args.output)
        self.assertEqual(errors, [])
        artifacts.pop('terminal.json')
        self.assertEqual(artifacts, terminal['available_evidence'])
        with self.assertRaisesRegex(AssertionError, 'Fresh output'):
            self.execute()

    def test_changed_input_stops_before_native_and_keeps_failed_terminal(self):
        (self.root/'probe-v2.exs').write_bytes(b'changed source')
        with patch.object(self.supervisor, 'observe') as observer:
            with self.assertRaisesRegex(AssertionError, 'Pinned input changed'):
                self.execute()
            observer.assert_not_called()
        self.assertEqual(self.terminal()['native_processes_started'], 0)
        self.assertFalse(self.terminal()['diagnostic_fixtures_passed'])

    def test_post_launch_failure_counts_saved_native_once_and_does_not_retry(self):
        def fail(*args, **kwargs):
            process = observe(*args, **kwargs)
            process.update(status='failed', exit_status=2, error='native fixture failed')
            save(args[2]/'process.json', process)
            raise AssertionError('native fixture failed')
        with patch.object(self.supervisor, 'observe', side_effect=fail) as observer:
            with self.assertRaisesRegex(AssertionError, 'native fixture failed'):
                self.execute()
            self.assertEqual(observer.call_count, 1)
        terminal = self.terminal()
        self.assertEqual(terminal['native_processes_started'], 1)
        self.assertEqual(terminal['observed_native_process_receipts'], 1)
        self.assertFalse(terminal['diagnostic_fixtures_passed'])

    def test_incomplete_or_ambiguous_exunit_summary_is_not_success(self):
        for raw in (b'14 tests, 0 failures\n', b'15 tests, 1 failure\n',
                    b'15 tests, 0 failures, 1 skipped\n', b'15 tests, 0 failures\n15 tests, 0 failures\n'):
            with self.subTest(raw=raw), self.assertRaisesRegex(AssertionError, 'ExUnit summary'):
                runner.validate_stdout(raw)

    def test_post_validation_output_mutation_clears_success(self):
        original = runner.inventory
        def mutate(root):
            if root == self.args.output:
                (root/'native/stdout.bin').write_bytes(b'changed after validation')
            return original(root)
        with patch.object(runner, 'inventory', side_effect=mutate):
            with self.assertRaisesRegex(AssertionError, 'terminal integrity'):
                self.execute()
        self.assertFalse(self.terminal()['diagnostic_fixtures_passed'])
        self.assertIn('Validated fixture artifacts changed before terminal closure', self.terminal()['artifact_errors'])

    def test_copied_executed_fixture_source_stays_bound_to_original_pin(self):
        def mutate_copy(*args, **kwargs):
            process = observe(*args, **kwargs)
            (args[2]/'probe-review-tests.exs').write_bytes(b'changed executed fixture copy')
            return process
        with patch.object(self.supervisor, 'observe', side_effect=mutate_copy):
            with self.assertRaisesRegex(AssertionError, 'terminal integrity'):
                self.execute()
        self.assertFalse(self.terminal()['diagnostic_fixtures_passed'])
        self.assertTrue(any('probe-review-tests.exs' in error for error in self.terminal()['integrity_errors']))

    def test_report_hash_failure_still_writes_disqualified_terminal(self):
        original = runner.sha
        def fail_report(path):
            if Path(path).name == 'report.json':
                raise OSError('unreadable report artifact')
            return original(path)
        with patch.object(runner, 'sha', side_effect=fail_report):
            with self.assertRaisesRegex(AssertionError, 'terminal integrity'):
                self.execute()
        self.assertIsNone(self.terminal()['report_sha256'])
        self.assertFalse(self.terminal()['diagnostic_fixtures_passed'])
        self.assertTrue(self.terminal()['artifact_errors'])


if __name__ == '__main__':
    unittest.main()
