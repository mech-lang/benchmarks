"""Pure RSS teardown-race fixtures plus the unchanged original 14-test suite.

No native commands, host kernel calls, sleeps, full pins or failed-run rewrites.
"""
import ast
import ctypes
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name,HERE/filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


kb = load('kotlin_bounded_v2_review','kotlin_bounded_v2.py')
original_tests = load('kotlin_bounded_original_tests','test_kotlin_bounded.py')
original_tests.kb = kb  # Reuse every original fixture against the new revision.


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.identity = dict(pid=424242,ppid=123,pgid=424242,status=2,birth_seconds=1,birth_microseconds=2)

    def kernel(self, sizes, identities, resident=43210):
        kernel = kb.Kernel.__new__(kb.Kernel)
        results = iter(sizes)
        def task_info(pid,flavor,arg,buffer,size):
            self.assertEqual((pid,flavor,arg,size),(424242,4,0,96))
            ctypes.cast(buffer,ctypes.POINTER(kb.TaskInfo)).contents.resident_size=resident
            return next(results)
        kernel.library=Mock(); kernel.library.proc_pidinfo.side_effect=task_info
        kernel.identity=Mock(side_effect=identities)
        return kernel

    def read(self,kernel):
        with patch.object(kb.time,'sleep') as sleep, patch.object(kb.os,'kill') as kill:
            value=kernel.resident_bytes(self.identity)
        return value,sleep,kill

    def test_transient_teardown_becomes_same_identity_zombie(self):
        kernel=self.kernel([0,0],[dict(self.identity),dict(self.identity,status=5)])
        value,sleep,kill=self.read(kernel)
        self.assertEqual(value,0); sleep.assert_called_once_with(0.005);kill.assert_not_called()
        self.assertEqual(kernel.library.proc_pidinfo.call_count,2)

    def test_transient_failure_recovers_actual_resident_value(self):
        kernel=self.kernel([0,24,96],[dict(self.identity)]*3)
        value,sleep,kill=self.read(kernel)
        self.assertEqual(value,43210);self.assertEqual(sleep.call_count,2);kill.assert_not_called()
        self.assertTrue(all(c.args==(0.005,) for c in sleep.call_args_list))

    def test_persistent_live_failure_stops_after_five_attempts(self):
        kernel=self.kernel([0]*5,[dict(self.identity)]*5)
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill') as kill:
            with self.assertRaisesRegex(AssertionError,'after 5 attempts'):kernel.resident_bytes(self.identity)
        self.assertEqual(kernel.library.proc_pidinfo.call_count,5)
        self.assertEqual(sleep.call_count,4);kill.assert_not_called()

    def test_reused_live_identity_rejected_on_retry(self):
        kernel=self.kernel([0,96],[dict(self.identity),dict(self.identity,birth_microseconds=3)])
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill') as kill:
            with self.assertRaisesRegex(AssertionError,'identity changed'):kernel.resident_bytes(self.identity)
        sleep.assert_called_once_with(0.005);kill.assert_not_called()

    def test_reused_zombie_identity_is_not_zero_rss(self):
        kernel=self.kernel([0],[dict(self.identity,status=5,birth_seconds=99)])
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill') as kill:
            with self.assertRaisesRegex(AssertionError,'identity changed'):kernel.resident_bytes(self.identity)
        sleep.assert_not_called();kill.assert_not_called()

    def test_missing_identity_requires_confirmed_esrch(self):
        kernel=self.kernel([0],[None])
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill',side_effect=ProcessLookupError) as kill:
            self.assertEqual(kernel.resident_bytes(self.identity),0)
        kill.assert_called_once_with(424242,0);sleep.assert_not_called()

    def test_missing_identity_with_existing_pid_fails_closed(self):
        kernel=self.kernel([0],[None])
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill') as kill:
            with self.assertRaisesRegex(AssertionError,'identity unavailable'):kernel.resident_bytes(self.identity)
        kill.assert_called_once_with(424242,0);sleep.assert_not_called()

    def test_permission_error_is_not_confirmed_exit(self):
        kernel=self.kernel([0],[None])
        with patch.object(kb.time,'sleep') as sleep,patch.object(kb.os,'kill',side_effect=PermissionError):
            with self.assertRaises(PermissionError):kernel.resident_bytes(self.identity)
        sleep.assert_not_called()

    def test_valid_first_read_never_retries(self):
        kernel=self.kernel([96],[dict(self.identity)])
        value,sleep,kill=self.read(kernel)
        self.assertEqual(value,43210);sleep.assert_not_called();kill.assert_not_called()

    def test_revision_changes_only_resident_bytes_and_preserves_original(self):
        old=(HERE/'kotlin_bounded.py').read_bytes();new=(HERE/'kotlin_bounded_v2.py').read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(),'916a94f68e191cce8d074121859121351517c8ab2132bb5953ebc62621ba710e')
        trees=[ast.parse(raw) for raw in (old,new)]
        for tree in trees:
            kernel=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Kernel')
            method=next(n for n in kernel.body if isinstance(n,ast.FunctionDef) and n.name=='resident_bytes')
            method.body=[ast.Pass()]
        self.assertEqual(ast.dump(trees[0]),ast.dump(trees[1]))
        self.assertEqual((kb.TIMEOUT,kb.CLEANUP_TIMEOUT,kb.RSS_LIMIT,kb.FILE_LIMIT),(30,5,2147483648,8388608))


if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(original_tests),
                            unittest.defaultTestLoader.loadTestsFromTestCase(RetryTests)])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())
