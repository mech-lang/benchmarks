"""Draft pure fault cases; not executed during the active timing cohort."""
import contextlib
import importlib.util
import os
from pathlib import Path
import time
import unittest

SOURCE = Path(__file__).with_name('owned_processes.py')
SPEC = importlib.util.spec_from_file_location('julia_owned_processes_draft', SOURCE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def session(kernel=None):
    events = []
    owner = m.OwnedProcesses(kernel, contextlib.nullcontext, None,
        lambda: None, lambda: None, events.append, time.monotonic()+10)
    return owner, events


class OwnershipFaults(unittest.TestCase):
    def test_failed_normal_closure_always_forces_cleanup(self):
        owner, _ = session()
        calls = []
        def close(terminate):
            calls.append(terminate)
            if not terminate:
                raise ValueError('owned group remained')
        owner._cleanup_once = close
        with self.assertRaisesRegex(ValueError, 'owned group remained'):
            owner.cleanup(False)
        self.assertEqual(calls, [False, True])

    def test_forced_cleanup_error_preserves_initial_failure(self):
        owner, _ = session()
        def close(terminate):
            raise ValueError('forced' if terminate else 'normal')
        owner._cleanup_once = close
        with self.assertRaises(BaseExceptionGroup) as caught:
            owner.cleanup(False)
        self.assertEqual([str(error) for error in caught.exception.exceptions], ['normal', 'forced'])

    def target_and_server(self, kernel):
        owner, events = session(kernel)
        target, server = m.Child('subject'), m.Child('debugserver')
        target.pid_slot.value, server.pid_slot.value = 123, 456
        target.spawned = server.spawned = True
        target.identity = dict(pid=123, ppid=os.getpid(), pgid=123, status=4,
                               birth_seconds=100, birth_microseconds=200)
        owner.children = [target, server]
        return owner, events, target

    def test_only_verified_parent_transition_retries(self):
        class Kernel:
            calls = 0
            def resident_bytes(self, identity):
                self.calls += 1
                if self.calls == 1:
                    raise AssertionError('Process identity changed during RSS read')
                return 99
            def identity(self, pid):
                return dict(pid=123, ppid=456, pgid=123, status=4,
                            birth_seconds=100, birth_microseconds=200)
        kernel = Kernel()
        owner, events, target = self.target_and_server(kernel)
        self.assertEqual(owner.resident_bytes(target, target.identity), 99)
        self.assertEqual(kernel.calls, 2)
        self.assertEqual(len([e for e in events if e['kind'] == 'rss-parent-transition-retry']), 1)

    def test_changed_birth_is_not_retryable(self):
        class Kernel:
            calls = 0
            def resident_bytes(self, identity):
                self.calls += 1
                raise AssertionError('Process identity changed during RSS read')
            def identity(self, pid):
                return dict(pid=123, ppid=456, pgid=123, status=4,
                            birth_seconds=101, birth_microseconds=200)
        kernel = Kernel()
        owner, _, target = self.target_and_server(kernel)
        with self.assertRaisesRegex(ValueError, 'birth/group identity changed'):
            owner.resident_bytes(target, target.identity)
        self.assertEqual(kernel.calls, 1)

    def test_other_kernel_failure_is_not_retryable(self):
        class Kernel:
            calls = 0
            def resident_bytes(self, identity):
                self.calls += 1
                raise AssertionError('Kernel RSS read failed for live owned process after 5 attempts')
        kernel = Kernel()
        owner, _, target = self.target_and_server(kernel)
        with self.assertRaisesRegex(AssertionError, 'Kernel RSS read failed'):
            owner.resident_bytes(target, target.identity)
        self.assertEqual(kernel.calls, 1)


if __name__ == '__main__':
    unittest.main()
