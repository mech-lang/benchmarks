"""Mocked process-failure fixtures; no Elixir or other native child is started."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('elixir_helpers_under_test', HERE/'elixir_helpers.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


class HelperSupervisor(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name)
        self.lock = (self.output/'lock').open('w+')
        self.addCleanup(self.lock.close)
        self.payload = b'\x00\xffpartial\r\n'
        self.command = ['retained-elixir', 'probe.exs']
        self.calls = []

    def fake_process(self, *, content=None, stderr=b'', timeout=False, cleanup_timeout=False, spawn_error=False):
        parent = self

        class Process:
            pid = 123456
            returncode = None

            def __init__(self, command, **kwargs):
                parent.assertEqual(command, parent.command)
                parent.assertEqual(kwargs['pass_fds'], (parent.lock.fileno(),))
                parent.assertTrue(kwargs['start_new_session'])
                if spawn_error:
                    raise OSError('spawn fixture failure')
                # Duplicate the supplied descriptors just as a child would, so
                # they remain usable after the supervisor closes its handles.
                self.stdout = os.fdopen(os.dup(kwargs['stdout'].fileno()), 'wb', buffering=0)
                self.stderr = os.fdopen(os.dup(kwargs['stderr'].fileno()), 'wb', buffering=0)
                parent.addCleanup(self.stdout.close)
                parent.addCleanup(self.stderr.close)
                self.count = 0

            def communicate(self, payload=None, timeout=None):
                parent.calls.append((payload, timeout))
                self.count += 1
                if self.count == 1:
                    self.stdout.write(parent.payload if content is None else content)
                    self.stderr.write(stderr)
                    if timeout_error:
                        raise subprocess.TimeoutExpired(parent.command, timeout)
                    self.returncode = 0
                else:
                    if cleanup_timeout:
                        raise subprocess.TimeoutExpired(parent.command, timeout)
                    self.returncode = -9
                return None, None

        timeout_error = timeout
        return Process

    def invoke(self, process, groups=None, kill_error=None):
        with patch.object(helpers.subprocess, 'Popen', process), \
             patch.object(helpers, 'group', side_effect=groups or (lambda pid: [])), \
             patch.object(helpers.os, 'killpg', side_effect=kill_error):
            helpers.observe(self.command, {}, self.output, self.payload, self.lock)

    def receipt(self):
        return json.loads((self.output/'process.json').read_text())

    def test_success_preserves_exact_bytes_hashes_and_inherited_mutex(self):
        self.invoke(self.fake_process())
        receipt = self.receipt()
        self.assertEqual(receipt['status'], 'passed')
        self.assertTrue(receipt['complete_output_matches'])
        self.assertEqual(receipt['stdout_sha256'], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(receipt['stderr_bytes'], 0)

    def test_timeout_preserves_partial_output_and_records_bounded_cleanup(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.invoke(self.fake_process(content=b'partial-before-timeout', timeout=True))
        receipt = self.receipt()
        self.assertTrue(receipt['timed_out'])
        self.assertEqual(receipt['status'], 'failed')
        self.assertEqual((self.output/'stdout.bin').read_bytes(), b'partial-before-timeout')
        self.assertEqual(receipt['remaining_after_cleanup'], [])
        self.assertEqual(len(self.calls), 2)
        self.assertGreater(self.calls[1][1], 0)
        self.assertLessEqual(self.calls[1][1], 5)

    def test_cleanup_timeout_retains_original_error_and_marks_cleanup_failure(self):
        with self.assertRaisesRegex(AssertionError, 'cleanup/artifact'):
            self.invoke(self.fake_process(timeout=True, cleanup_timeout=True))
        receipt = self.receipt()
        self.assertEqual(receipt['error_type'], 'TimeoutExpired')
        self.assertEqual(len(receipt['cleanup_errors']), 1)
        self.assertTrue((self.output/'stdout.bin').is_file())

    def test_bad_stderr_is_preserved_without_overwriting_evidence(self):
        with self.assertRaisesRegex(AssertionError, 'output differs'):
            self.invoke(self.fake_process(stderr=b'diagnostic fixture\n'))
        receipt = self.receipt()
        self.assertEqual(receipt['stderr_bytes'], len(b'diagnostic fixture\n'))
        self.assertEqual((self.output/'stderr.txt').read_bytes(), b'diagnostic fixture\n')
        self.assertEqual(receipt['status'], 'failed')

    def test_spawn_error_has_a_terminal_process_receipt(self):
        with self.assertRaisesRegex(OSError, 'spawn fixture'):
            self.invoke(self.fake_process(spawn_error=True))
        receipt = self.receipt()
        self.assertEqual(receipt['error_type'], 'OSError')
        self.assertEqual(receipt['stdout_bytes'], 0)
        self.assertEqual(receipt['status'], 'failed')

    def test_remaining_descendants_cannot_pass(self):
        with self.assertRaisesRegex(AssertionError, 'running descendants'):
            self.invoke(self.fake_process(), groups=[[123457], []])
        receipt = self.receipt()
        self.assertEqual(receipt['status'], 'failed')
        self.assertEqual(receipt['remaining_process_group'], [123457])
        self.assertEqual(receipt['remaining_after_cleanup'], [])

    def test_cleanup_error_does_not_replace_original_recorded_failure(self):
        with self.assertRaisesRegex(AssertionError, 'cleanup/artifact'):
            self.invoke(self.fake_process(content=b'wrong'), kill_error=PermissionError('kill fixture failure'))
        receipt = self.receipt()
        self.assertEqual(receipt['error'], 'Helper output differs; raw output retained')
        self.assertEqual(receipt['cleanup_errors'], ['kill fixture failure'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
