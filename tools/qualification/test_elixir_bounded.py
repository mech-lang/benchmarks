"""Pure output/ownership failure fixtures; no Elixir, compiler, ps, or signal runs."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

PATH = Path(__file__).with_name('elixir_bounded.py')
SPEC = importlib.util.spec_from_file_location('tested_elixir_bounded', PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class OutputContracts(unittest.TestCase):
    def test_full_size_cannot_replace_an_approved_bounded_slot(self):
        rows = [dict(id='elixir-'+bench+'-'+variant, benchmark=bench, variant=variant,
            bounded_cases=[dict(case=case, n=int(case[2:]) if bench in M.NUMERIC else 0,
                stdin=None if bench in M.NUMERIC else {'path': 'fixture'}) for case in cases])
            for bench, cases in M.CASE_NAMES.items() for variant in ('compact', 'optimized')]
        M.bounded_schedule(rows)
        rows[0]['bounded_cases'][0]['n'] = 50000000
        with self.assertRaises(ValueError):
            M.bounded_schedule(rows)

    def test_exact_output_keeps_empty_cases_and_rejects_missing_bytes(self):
        self.assertTrue(M.output_validation('pidigits', b'', b'')['reference_match'])
        self.assertTrue(M.output_validation('revcomp', b'>one\nT\n', b'>one\nT\n')['reference_match'])
        for actual in (b'>one\nT', b'>one\nT\nextra', b'>one\nA\n'):
            with self.assertRaises(ValueError):
                M.output_validation('revcomp', actual, b'>one\nT\n')

    def test_nbody_tolerance_cannot_hide_bad_format_nonfinite_or_extra_lines(self):
        reference = b'-0.169075164\n-0.169075164\n'
        self.assertTrue(M.output_validation('nbody', b'-0.169075160\n-0.169075160\n', reference)['reference_match'])
        for actual in (b'nan\n-0.169075164\n', b'-0.169075164\n', reference+b'0\n',
                       b'-0.169074000\n-0.169075164\n', b'-0.169075164\n-0.169075164'):
            with self.assertRaises(ValueError):
                M.output_validation('nbody', actual, reference)


class NativeFailureAccounting(unittest.TestCase):
    def kernel(self, status=5):
        return SimpleNamespace(identity=lambda pid: dict(pid=pid, ppid=M.os.getpid(), pgid=pid,
            status=status, birth_seconds=123, birth_microseconds=456))

    def fixture(self, root):
        expected = root/'reference'; expected.write_bytes(b'expected\n')
        row = dict(id='elixir-pidigits-compact', benchmark='pidigits', ebin='/fixture/ebin',
            command=['/fixture/elixir', '-pa', '/fixture/ebin', '/fixture/runner.exs', '{n}'],
            runtime_environment={}, physical_inputs=[dict(role='application', path='/fixture/main.ex'),
                dict(role='application-helper', path='/fixture/support.ex')],
            beams=[dict(path='/fixture/ebin/Elixir.Clbg.Main.beam', sha256='1'*64),
                dict(path='/fixture/ebin/Elixir.Clbg.Support.beam', sha256='2'*64)])
        case = dict(case='n-1', n=1, stdin=None, expected=dict(path=str(expected), sha256=M.sha(expected)))
        return row, case, dict(observer='/fixture/observer.exs')

    def test_spawn_failure_is_not_a_native_execution_and_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); row, case, plan = self.fixture(root)
            started = mock.Mock()
            with mock.patch.object(M.subprocess, 'Popen', side_effect=OSError('fixture spawn failure')):
                with self.assertRaises(OSError):
                    M.observe(row, case, root/'case', plan, SimpleNamespace(fileno=lambda: 9), started,
                              kernel=self.kernel())
            record = json.loads((root/'case/process.json').read_text())
            self.assertEqual(record['status'], 'failed')
            self.assertFalse(record['native_process_started'])
            self.assertIsNone(record['pid'])
            started.assert_not_called()
            self.assertEqual(record['artifacts']['stdout.bin']['bytes'], 0)

    def test_wrapper_failure_after_spawn_keeps_actual_pid_and_partial_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); row, case, plan = self.fixture(root)
            def spawn(command, **kwargs):
                kwargs['stdout'].write(b'partial actual output')
                child = SimpleNamespace(pid=12345, returncode=None)
                def wait(timeout):
                    child.returncode = 0
                    return 0
                child.wait = wait
                return child
            with mock.patch.object(M.subprocess, 'Popen', side_effect=spawn), \
                    mock.patch.object(M, 'members', return_value=[]), \
                    mock.patch.object(M.os, 'killpg') as kill:
                with self.assertRaisesRegex(RuntimeError, 'fixture callback failure'):
                    M.observe(row, case, root/'case', plan, SimpleNamespace(fileno=lambda: 9),
                        mock.Mock(side_effect=RuntimeError('fixture callback failure')), kernel=self.kernel())
                kill.assert_called_once_with(12345, M.signal.SIGKILL)
            record = json.loads((root/'case/process.json').read_text())
            self.assertEqual(record['status'], 'failed')
            self.assertTrue(record['native_process_started'])
            self.assertEqual(record['pid'], 12345)
            self.assertEqual((root/'case/stdout.bin').read_bytes(), b'partial actual output')
            self.assertEqual(record['artifacts']['stdout.bin']['sha256'], M.sha(root/'case/stdout.bin'))
            self.assertEqual(record['remaining_after_cleanup'], [])

    def test_post_reap_validation_failure_never_signals_reusable_group_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); row, case, plan = self.fixture(root)
            def spawn(command, **kwargs):
                kwargs['stdout'].write(b'partial output')
                kwargs['stderr'].write(b'validation failure after successful reap')
                child = SimpleNamespace(pid=12345, returncode=None)
                def wait(timeout):
                    child.returncode = 0
                    return 0
                child.wait = wait
                return child
            with mock.patch.object(M.subprocess, 'Popen', side_effect=spawn), \
                    mock.patch.object(M, 'members', return_value=[]) as members, \
                    mock.patch.object(M.os, 'killpg') as kill:
                with self.assertRaisesRegex(ValueError, 'Native stderr'):
                    M.observe(row, case, root/'case', plan, SimpleNamespace(fileno=lambda: 9), mock.Mock(),
                              kernel=self.kernel())
                kill.assert_not_called()
                members.assert_called_once_with(12345, timeout=5)
            record = json.loads((root/'case/process.json').read_text())
            self.assertEqual(record['status'], 'failed')
            self.assertEqual(record['exit_status'], 0)
            self.assertEqual(record['stop_signals'], [])
            self.assertEqual(record['cleanup_signal_skipped_reason'],
                             'direct-child-already-reaped-no-active-owned-identity')
            self.assertEqual(record['artifacts']['stderr.txt']['bytes'],
                             len(b'validation failure after successful reap'))

    def test_cleanup_process_scan_and_reap_share_one_deadline(self):
        clock = [100.0]
        child = SimpleNamespace(pid=12345, returncode=None)
        record = dict(stop_signals=[], cleanup_errors=[], monitor_processes=0)
        def wait(timeout):
            self.assertEqual(timeout, 1)
            clock[0] += timeout
            raise M.subprocess.TimeoutExpired('/fixture/elixir', timeout)
        def scan(pgid, *, timeout):
            self.assertEqual(pgid, child.pid)
            self.assertEqual(timeout, 5)
            self.assertIsNone(child.returncode)
            clock[0] += 4
            return []
        child.wait = wait
        with mock.patch.object(M.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(M.time, 'sleep') as sleep, \
                mock.patch.object(M, 'members', side_effect=scan), \
                mock.patch.object(M.os, 'killpg') as kill:
            M.cleanup_owned(child, record)
            kill.assert_called_once_with(12345, M.signal.SIGKILL)
            sleep.assert_not_called()
        self.assertEqual(clock[0], 105)
        self.assertEqual(len(record['cleanup_errors']), 1)
        self.assertIn('timed out after 1.0 seconds', record['cleanup_errors'][0])

    def test_exited_leader_keeps_group_owned_until_descendants_are_stopped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); row, case, plan = self.fixture(root)
            events = []
            child = SimpleNamespace(pid=12345, returncode=None)
            descendant = dict(pid=12346, pgid=12345, rss_kib=12, status='S')
            def spawn(command, **kwargs):
                kwargs['stdout'].write(b'partial output before descendant cleanup')
                return child
            def scan(pgid, *, timeout):
                self.assertIsNone(child.returncode, 'Leader was reaped while group still owned')
                events.append('scan')
                return [descendant] if len(events) == 1 else []
            def kill(pgid, sig):
                self.assertIsNone(child.returncode)
                self.assertEqual((pgid, sig), (12345, M.signal.SIGKILL))
                events.append('kill')
            def wait(timeout):
                events.append('reap')
                child.returncode = 0
                return 0
            child.wait = wait
            with mock.patch.object(M.subprocess, 'Popen', side_effect=spawn), \
                    mock.patch.object(M, 'members', side_effect=scan), \
                    mock.patch.object(M.os, 'killpg', side_effect=kill):
                with self.assertRaisesRegex(ValueError, 'exited with live descendants'):
                    M.observe(row, case, root/'case', plan, SimpleNamespace(fileno=lambda: 9), mock.Mock(),
                              kernel=self.kernel(status=5))
            self.assertEqual(events, ['scan', 'kill', 'scan', 'reap'])
            record = json.loads((root/'case/process.json').read_text())
            self.assertEqual(record['remaining_process_group'], [descendant])
            self.assertEqual(record['remaining_after_cleanup'], [])
            self.assertTrue(record['direct_child_reaped'])
            self.assertEqual(record['cleanup_errors'], [])
            self.assertEqual(record['status'], 'failed')

    def test_normal_scan_cannot_spend_more_than_remaining_execution_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); row, case, plan = self.fixture(root)
            clock = [100.0]; scan_timeouts = []
            child = SimpleNamespace(pid=12345, returncode=None)
            def spawn(command, **kwargs):
                clock[0] += 59.5
                return child
            def scan(pgid, *, timeout):
                scan_timeouts.append(timeout)
                if len(scan_timeouts) == 1:
                    self.assertEqual(timeout, 0.5)
                    clock[0] += timeout
                    raise M.subprocess.TimeoutExpired('/fixture/ps', timeout)
                return []
            def wait(timeout):
                child.returncode = -M.signal.SIGKILL
                return child.returncode
            child.wait = wait
            with mock.patch.object(M.time, 'monotonic', side_effect=lambda: clock[0]), \
                    mock.patch.object(M.subprocess, 'Popen', side_effect=spawn), \
                    mock.patch.object(M, 'members', side_effect=scan), \
                    mock.patch.object(M.os, 'killpg') as kill:
                with self.assertRaises(M.subprocess.TimeoutExpired):
                    M.observe(row, case, root/'case', plan, SimpleNamespace(fileno=lambda: 9), mock.Mock(),
                              kernel=self.kernel(status=2))
                kill.assert_called_once_with(12345, M.signal.SIGKILL)
            self.assertEqual(scan_timeouts, [0.5, 5])
            self.assertEqual(clock[0], 160)
            record = json.loads((root/'case/process.json').read_text())
            self.assertTrue(record['direct_child_reaped'])
            self.assertEqual(record['status'], 'failed')

    def test_live_group_scan_excludes_reserved_zombie_leader(self):
        with mock.patch.object(M.subprocess, 'run', return_value=SimpleNamespace(
                stdout='12345 12345 0 Z\n12346 12345 12 S\n22222 22222 100 R+\n')) as scan:
            self.assertEqual(M.members(12345, timeout=0.25),
                             [dict(pid=12346, pgid=12345, rss_kib=12, status='S')])
            self.assertEqual(scan.call_args.kwargs['timeout'], 0.25)


if __name__ == '__main__':
    unittest.main()
