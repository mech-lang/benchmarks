#!/usr/bin/env python3
"""Pure runner tests; every process, monitor, signal timer and mutex is mocked."""
from contextlib import ExitStack, nullcontext
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('rerun', ROOT / 'tools/rerun_mech_interpreted.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class FakeMonitor:
    def __init__(self):
        self.errors = []
        self.observations = [{'power': m.POWER, 'competing_compilers': []}]
        self.stop = Mock()
        self.stop.is_set.return_value = False

    def start(self):
        pass

    def finish(self):
        self.stop.is_set.return_value = True

    def validate(self):
        if self.errors:
            raise ValueError('monitor failure')


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m.boundary.load_retained_report(ROOT)
        cls.plan = m.make_plan(cls.report, '/private/tmp/test-mech-interpreted-output')

    def test_exact_15_forms_45_serial_schedule(self):
        plan = self.plan
        self.assertEqual(len(plan['programs']), 15)
        self.assertEqual([s['ordinal'] for s in plan['schedule']], list(range(1, 46)))
        for number in range(1, 4):
            cases = [s['key'] for s in plan['schedule'] if s['round'] == number]
            self.assertEqual(len(cases), 15)
            self.assertEqual(set(cases), set(plan['programs']))
        self.assertEqual(plan, m.make_plan(self.report, '/private/tmp/test-mech-interpreted-output'))

    def test_exact_commands_sources_oracles_and_inputs(self):
        for key, row in self.plan['programs'].items():
            old = self.report['programs'][key.removesuffix(':resident') + ':after']
            expected = [arg.replace('{n}', str(m.boundary.WORKLOADS[row['benchmark']][1])) for arg in old['command']]
            self.assertEqual(row['command'], expected)
            for field in ('source', 'source_sha256', 'binary', 'binary_sha256', 'loc', 'physical_loc'):
                self.assertEqual(row[field], old[field])
            self.assertEqual(row['expected_output'], old['full_validation'])
            self.assertEqual(row['command'][2], 'resident')
            if row['benchmark'] in ('revcomp', 'knucleotide'):
                self.assertEqual(row['stdin'], m.INPUTS['sequence'])
            elif row['benchmark'] == 'regexredux':
                self.assertEqual(row['stdin'], m.INPUTS['regex'])
            else:
                self.assertIsNone(row['stdin'])

    def test_environment_is_explicit_and_phase_diagnostics_are_not_ranked(self):
        with patch.dict(m.os.environ, {'PRIVATE_TOKEN': 'must-not-be-copied'}):
            plan = m.make_plan(self.report, '/private/tmp/output')
        for row in plan['programs'].values():
            self.assertNotIn('PRIVATE_TOKEN', row['runtime_environment'])
            self.assertEqual(row['runtime_environment']['MECH_TIMINGS'], '1')
            for key, value in row['original_runtime_overrides'].items():
                self.assertEqual(row['runtime_environment'][key], value)
        self.assertFalse(plan['historical_phase_diagnostics_ranked'])
        self.assertFalse(plan['automatic_retry'])

    def test_mutated_retained_form_rejected_even_when_not_selected(self):
        report = deepcopy(self.report)
        report['programs']['fannkuchredux:mech-fannkuch-even:after']['command'][3] = '7'
        with self.assertRaises(ValueError):
            m.make_plan(report, '/private/tmp/output')

    def fixture(self, stack, directory, wait_error=None, exit_code=0):
        content = b'OK\n'
        row = {'command': ['/exact/binary', '/exact/source', 'resident', '12'], 'cwd': '/exact/cwd',
               'runtime_environment': {'MECH_TIMINGS': '1'}, 'stdin': None,
               'expected_output': {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}}
        events = []
        proc = Mock(pid=123456, returncode=exit_code)

        def wait(*args, **kwargs):
            events.append('wait')
            if wait_error and not kwargs:
                raise wait_error
            return exit_code

        proc.wait.side_effect = wait

        def popen(*args, **kwargs):
            events.append('launch')
            self.assertEqual(args[0], row['command'])
            self.assertEqual(kwargs['pass_fds'], (77,))
            self.assertTrue(kwargs['start_new_session'])
            self.assertEqual(kwargs['env'], row['runtime_environment'])
            kwargs['stdout'].write(content)
            kwargs['stderr'].write(b'TIMING {"prepare_seconds":0.1,"kernel_seconds":0.2}\n')
            return proc

        times = iter((1_000_000_000, 1_500_000_000))

        def clock():
            events.append('clock')
            return next(times)

        stack.enter_context(patch.object(m, 'Monitor', FakeMonitor))
        stack.enter_context(patch.object(m, 'verify_lock'))
        stack.enter_context(patch.object(m, 'atomic_signals', nullcontext))
        stack.enter_context(patch.object(m.signal, 'signal'))
        stack.enter_context(patch.object(m.signal, 'setitimer'))
        stack.enter_context(patch.object(m, 'group_alive', return_value=False))
        stack.enter_context(patch.object(m.subprocess, 'Popen', side_effect=popen))
        stack.enter_context(patch.object(m.time, 'perf_counter_ns', side_effect=clock))
        return row, proc, events

    def test_single_external_timer_is_not_phase_sum_and_output_hash_is_outside(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            directory = Path(temporary) / 'sample'
            row, proc, events = self.fixture(stack, directory)
            validate = m.validate_output

            def checked(*args):
                events.append('validate')
                return validate(*args)

            stack.enter_context(patch.object(m, 'validate_output', side_effect=checked))
            receipt = m.run_one(row, directory, 77, 600)
            self.assertEqual(events, ['clock', 'launch', 'wait', 'clock', 'validate'])
            self.assertEqual(receipt['seconds'], 0.5)
            self.assertEqual(receipt['sample_details'], {'seconds': 0.5, 'wall_seconds': 0.5,
                                                        'prepare_seconds': 0.1, 'kernel_seconds': 0.2})
            self.assertTrue(receipt['qualified'])
            proc.wait.assert_called_once_with()
            self.assertEqual(json.loads((directory / 'process.json').read_text()), receipt)

    def test_interruption_reaps_owned_process_and_preserves_failed_receipt(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            directory = Path(temporary) / 'sample'
            row, proc, _ = self.fixture(stack, directory, wait_error=KeyboardInterrupt('stop'))
            with self.assertRaises(KeyboardInterrupt):
                m.run_one(row, directory, 77, 600)
            self.assertEqual(proc.wait.call_count, 2)
            self.assertEqual(proc.wait.call_args.kwargs, {'timeout': 10})
            receipt = json.loads((directory / 'process.json').read_text())
            self.assertEqual(receipt['status'], 'failed')
            self.assertFalse(receipt['qualified'])
            self.assertTrue(receipt['native_process_started'])

    def test_nonzero_exit_never_qualifies_and_no_redundant_group_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            directory = Path(temporary) / 'sample'
            row, proc, _ = self.fixture(stack, directory, exit_code=1)
            with self.assertRaisesRegex(ValueError, 'exited with status'):
                m.run_one(row, directory, 77, 600)
            proc.wait.assert_called_once_with()
            self.assertFalse(json.loads((directory / 'process.json').read_text())['qualified'])

    def test_changed_output_fails_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            directory = Path(temporary) / 'sample'
            row, proc, _ = self.fixture(stack, directory)
            row['expected_output']['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'Full output'):
                m.run_one(row, directory, 77, 600)
            proc.wait.assert_called_once_with()
            receipt = json.loads((directory / 'process.json').read_text())
            self.assertFalse(receipt['qualified'])
            self.assertEqual(receipt['wall_seconds'], 0.5)

    def test_atomic_mask_covers_cancellation_and_popen_deadline(self):
        with patch.object(m.signal, 'pthread_sigmask', return_value=set()) as blocked:
            with m.atomic_signals():
                pass
        self.assertEqual(set(blocked.call_args_list[0].args[1]), {*m.SIGNALS, m.signal.SIGALRM})
        self.assertEqual(blocked.call_args_list[1].args, (m.signal.SIG_SETMASK, set()))

    def test_pin_cache_rehashes_changes_and_final_force(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'source'
            path.write_bytes(b'original')
            pins = {str(path): hashlib.sha256(b'original').hexdigest()}
            cache = {}
            m.verify_pins(pins, cache)
            with patch.object(m, 'sha', wraps=m.sha) as check:
                m.verify_pins(pins, cache)
                check.assert_not_called()
                m.verify_pins(pins, cache, force=True)
                check.assert_called_once()
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                m.verify_pins(pins, cache)

    def test_existing_output_refused_before_lock_or_hash(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(m, 'common_lock') as lock:
            with self.assertRaisesRegex(ValueError, 'Fresh output'):
                m.run(SimpleNamespace(output=str(Path(temporary).resolve()), timeout=600))
            lock.assert_not_called()

    def test_monitor_error_or_competing_compiler_fails(self):
        monitor = m.Monitor()
        monitor.observations = [{'power': m.POWER, 'competing_compilers': [{'executable': 'rustc'}]}]
        with self.assertRaises(ValueError):
            monitor.validate()
        monitor.observations = [{'power': {'source': 'Battery Power', 'low_power_mode': 0}, 'competing_compilers': []}]
        with self.assertRaises(ValueError):
            monitor.validate()
        monitor.errors = ['could not inspect']
        with self.assertRaises(ValueError):
            monitor.validate()

    def test_complete_controller_closes_exact_45_sample_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary).resolve() / 'fresh'
            plan = m.make_plan(self.report, str(output))
            contents = b'OK\n'
            output_hash = hashlib.sha256(contents).hexdigest()
            stderr = b'TIMING {"prepare_seconds":0.1,"kernel_seconds":0.2}\n'

            def fake_sample(row, directory, lock_fd, timeout):
                directory.mkdir()
                (directory / 'stdout.bin').write_bytes(contents)
                (directory / 'stderr.txt').write_bytes(stderr)
                receipt = {'qualified': True, 'status': 'passed', 'native_process_started': True,
                           'wall_seconds': 0.5, 'sample_details': {'seconds': 0.5, 'wall_seconds': 0.5,
                           'kernel_seconds': 0.2, 'prepare_seconds': 0.1},
                           'validation': {'bytes': 3, 'sha256': output_hash, 'reference_match': True},
                           'stderr_sha256': hashlib.sha256(stderr).hexdigest()}
                m.save(directory / 'process.json', receipt)
                return receipt

            stack.enter_context(patch.object(m, 'make_plan', return_value=plan))
            stack.enter_context(patch.object(m, 'pin_inventory', return_value={str(Path(m.__file__).resolve()): m.CONTROLLER_SHA256}))
            pins = stack.enter_context(patch.object(m, 'verify_pins'))
            stack.enter_context(patch.object(m, 'verify_lock'))
            stack.enter_context(patch.object(m, 'common_lock', lambda: nullcontext(77)))
            stack.enter_context(patch.object(m, 'atomic_signals', nullcontext))
            execute = stack.enter_context(patch.object(m, 'run_one', side_effect=fake_sample))
            stack.enter_context(patch('builtins.print'))
            report = m.run(SimpleNamespace(output=str(output), timeout=600))
            self.assertEqual(report['status'], 'complete')
            self.assertEqual(report['completed_samples'], 45)
            self.assertEqual(report['native_processes'], 45)
            self.assertEqual(execute.call_count, 45)
            self.assertEqual(len(report['artifacts']), 136)
            self.assertEqual(pins.call_args.kwargs, {'force': True})
            terminal = json.loads((output / 'terminal.json').read_text())
            self.assertEqual(terminal['report_sha256'], hashlib.sha256((output / 'report.json').read_bytes()).hexdigest())
            self.assertEqual(terminal['artifacts'], report['artifacts'])
            self.assertTrue(terminal['common_mutex_held'])


if __name__ == '__main__':
    unittest.main()
