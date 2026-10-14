"""Small pure fixtures: no subprocesses, JVMs, corpus rehash or host kernel calls."""
from contextlib import contextmanager
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('kotlin_bounded',ROOT/'tools/qualification/kotlin_bounded.py')
kb = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(kb)


class FakeProcess:
    pid = 424242
    args = ['retained-java','boundedqualification.BoundedProbe']
    def __init__(self):
        self.stdin = io.BytesIO(); self.stdout = io.BytesIO(); self.returncode = None
    def wait(self,timeout):
        self.returncode = 0
        return 0


class FakeKernel:
    def identity(self,pid):
        return dict(pid=pid,ppid=os.getpid(),pgid=pid,status=5,birth_seconds=1,birth_microseconds=2)
    def group(self,pgid): return []


class FakeLock:
    def fileno(self): return 99


class BoundedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.directory = Path(self.temp.name).resolve()
    def tearDown(self): self.temp.cleanup()
    def receipt(self): return json.loads((self.directory/'process.json').read_text())
    def observe(self,transfer=None,kernel=None,launch=None,launched=None):
        self.launches = []; self.signals = []
        def create(command,**kwargs):
            self.assertEqual(kwargs['pass_fds'],(99,)); self.assertTrue(kwargs['start_new_session'])
            self.assertIs(kwargs['stdin'],subprocess.PIPE); self.assertIs(kwargs['stdout'],subprocess.PIPE)
            return FakeProcess()
        if transfer is None: transfer = lambda p,b,o,d,t:o.write(b'actual')
        with patch.object(kb.kh,'verify_lock'),patch.object(kb.os,'killpg') as kill:
            try:
                return kb.observe(['retained-java'],{},self.directory,b'input',FakeLock(),
                    launched or self.launches.append,kernel=kernel or FakeKernel(),launch=launch or create,
                    transfer=transfer,drainer=lambda s,p,d:None)
            finally: self.signals = kill.call_args_list

    def test_closed_schedule_requires_all_156_original_case_identities(self):
        rows = []
        for bench,labels in kb.CASE_NAMES.items():
            for variant in ('compact','optimized'):
                rows.append(dict(id='kotlin-'+bench+'-'+variant,benchmark=bench,variant=variant,
                    bounded_cases=[dict(case=label,n=int(label[2:]) if bench in kb.NUMERIC else 0,
                        stdin=dict(path='retained-input') if bench in kb.STREAMS else None) for label in labels]))
        kb.bounded_schedule(rows)
        self.assertEqual(sum(len(r['bounded_cases']) for r in rows),156)
        rows[0]['bounded_cases'][0]['n'] = 50000000
        with self.assertRaisesRegex(AssertionError,'Unexpected size/input'): kb.bounded_schedule(rows)

    def test_success_counts_native_start_without_claiming_output_qualification(self):
        record = self.observe()
        self.assertEqual(self.launches,[424242]); self.assertEqual(record['status'],'native-passed')
        self.assertTrue(record['native_process_started']); self.assertTrue(record['direct_child_reaped'])
        self.assertNotIn('qualified_bounded_cases',record)
        self.assertEqual((self.directory/'stdout.bin').read_bytes(),b'actual')
        self.assertEqual(record['kernel_monitor_samples'],1)
        self.assertEqual(self.signals,[])

    def test_launch_failure_records_no_native_start(self):
        def fail(*a,**k): raise OSError('missing native executable')
        with self.assertRaisesRegex(OSError,'missing native'): self.observe(launch=fail)
        self.assertEqual(self.launches,[]); self.assertFalse(self.receipt()['native_process_started'])
        self.assertFalse(self.receipt()['direct_child_reaped']); self.assertEqual(self.signals,[])

    def test_launch_registration_failure_still_retains_and_reaps_owned_child(self):
        def fail(pid): raise RuntimeError('ledger write failure after launch')
        with self.assertRaisesRegex(RuntimeError,'ledger write'): self.observe(launched=fail)
        record = self.receipt()
        self.assertTrue(record['native_process_started']); self.assertTrue(record['direct_child_reaped'])
        self.assertEqual(record['pid'],424242); self.assertEqual(self.signals,[])

    def test_identity_read_failure_after_launch_counts_native_start_and_cleans_owned_group(self):
        class IdentityFailure(FakeKernel):
            scans = 0
            def identity(self,pid): raise RuntimeError('identity read failed after Popen')
            def group(self,pid):
                self.scans += 1
                return [dict(pid=pid)] if self.scans == 1 else []
        with self.assertRaisesRegex(RuntimeError,'identity read failed after Popen'):
            self.observe(kernel=IdentityFailure())
        record = self.receipt()
        self.assertEqual(self.launches,[424242])
        self.assertTrue(record['native_process_started']); self.assertEqual(record['pid'],424242)
        self.assertEqual(record['pgid'],424242); self.assertEqual(record['status'],'failed')
        self.assertTrue(record['direct_child_reaped']); self.assertEqual(record['remaining_after_cleanup'],[])
        self.assertEqual(record['stop_signals'],[9]); self.assertEqual(self.signals[0].args,(424242,9))
        self.assertEqual(record['cleanup_errors'],[])

    def test_timeout_retains_partial_stdout_and_signals_only_unreaped_group(self):
        class LiveUntilKilled(FakeKernel):
            scans = 0
            def group(self,pid):
                self.scans += 1
                return [dict(pid=pid)] if self.scans == 1 else []
        def transfer(p,b,o,d,t):
            o.write(b'partial'); o.flush(); raise subprocess.TimeoutExpired(p.args,30)
        with self.assertRaises(subprocess.TimeoutExpired): self.observe(transfer,kernel=LiveUntilKilled())
        record = self.receipt()
        self.assertTrue(record['direct_child_reaped']); self.assertTrue(record['timed_out'])
        self.assertEqual(record['remaining_after_cleanup'],[]); self.assertEqual(record['stop_signals'],[9])
        self.assertEqual((self.directory/'stdout.bin').read_bytes(),b'partial')
        self.assertEqual(self.signals[0].args,(424242,9))

    def test_pending_interrupt_after_atomic_reap_never_signals_reused_group(self):
        exits = 0
        @contextmanager
        def interrupted_boundary():
            nonlocal exits
            try: yield set()
            finally:
                exits += 1
                if exits == 2: raise KeyboardInterrupt('pending after reap')
        with patch.object(kb,'atomic',interrupted_boundary):
            with self.assertRaisesRegex(KeyboardInterrupt,'pending after reap'): self.observe()
        record = self.receipt()
        self.assertTrue(record['direct_child_reaped']); self.assertEqual(self.signals,[])
        self.assertEqual(record['error_type'],'KeyboardInterrupt')

    def test_pending_interrupt_after_atomic_launch_preserves_registered_child(self):
        exits = 0
        @contextmanager
        def interrupted_boundary():
            nonlocal exits
            try: yield set()
            finally:
                exits += 1
                if exits == 1: raise KeyboardInterrupt('pending after launch')
        with patch.object(kb,'atomic',interrupted_boundary):
            with self.assertRaisesRegex(KeyboardInterrupt,'pending after launch'): self.observe()
        self.assertEqual(self.launches,[424242]); self.assertTrue(self.receipt()['direct_child_reaped'])
        self.assertEqual(self.signals,[])

    def test_cleanup_inventory_failure_is_terminal_and_preserves_original_error(self):
        class BrokenKernel(FakeKernel):
            def group(self,pid): raise RuntimeError('kernel inventory unavailable')
        def transfer(p,b,o,d,t): raise subprocess.TimeoutExpired(p.args,30)
        with self.assertRaisesRegex(AssertionError,'Cleanup or output retention'):
            self.observe(transfer,kernel=BrokenKernel())
        record = self.receipt()
        self.assertFalse(record['direct_child_reaped']); self.assertEqual(record['status'],'failed-cleanup-or-artifacts')
        self.assertEqual(record['error_type'],'TimeoutExpired')
        self.assertEqual(record['cleanup_signal_fallback'],'unreaped-owned-direct-child-kernel-query-failed')
        self.assertEqual(self.signals[0].args,(424242,9))

    def test_artifact_hash_failure_still_writes_final_process_receipt(self):
        original = kb.sha
        def failing_hash(path):
            if Path(path).name == 'stdout.bin': raise OSError('artifact hash failed')
            return original(path)
        with patch.object(kb,'sha',failing_hash):
            with self.assertRaisesRegex(AssertionError,'Cleanup or output retention'): self.observe()
        record = self.receipt()
        self.assertTrue(record['direct_child_reaped']); self.assertEqual(self.signals,[])
        self.assertEqual(record['status'],'failed-cleanup-or-artifacts')
        self.assertEqual(record['artifact_errors'][0]['error'],'artifact hash failed')

    def test_rss_layout_and_live_identity_recheck(self):
        test = self
        class Library:
            def proc_pidinfo(self,pid,flavor,arg,buffer,size):
                test.assertEqual((flavor,arg,size),(4,0,96))
                ctypes.cast(buffer,ctypes.POINTER(kb.TaskInfo)).contents.resident_size = 123456
                return size
        kernel = kb.Kernel.__new__(kb.Kernel); kernel.library = Library()
        identity = FakeKernel().identity(424242); identity['status'] = 2
        kernel.identity = lambda pid:dict(identity)
        self.assertEqual(kernel.resident_bytes(identity),123456)
        kernel.identity = lambda pid:dict(identity,birth_seconds=3)
        with self.assertRaisesRegex(AssertionError,'identity changed'): kernel.resident_bytes(identity)
        kernel.identity = lambda pid:dict(identity,status=5)
        self.assertEqual(kernel.resident_bytes(identity),0)

    def test_rss_bound_fails_closed(self):
        class LargeKernel(FakeKernel):
            def group(self,pid): return [self.identity(pid)]
            def resident_bytes(self,identity): return kb.RSS_LIMIT+1
        process = FakeProcess(); record = dict(identity=FakeKernel().identity(process.pid),
            observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0)
        with self.assertRaisesRegex(AssertionError,'RSS limit'):
            kb.monitor(LargeKernel(),process,record,self.directory)
        self.assertEqual(record['observed_peak_process_group_rss_bytes'],kb.RSS_LIMIT+1)

    def test_class_log_rejects_foreign_subject_stdlib_and_hidden_lambda(self):
        classes = self.directory/'classes'; stdlib = self.directory/'stdlib.jar'; probe = self.directory/'probe'
        owners = {'clbg.Support','clbg.nbody.MainKt'}
        valid = '\n'.join([
            '[0.01s][class,load] boundedqualification.BoundedProbe source: '+probe.as_uri(),
            '[0.02s][class,load] clbg.Support source: '+classes.as_uri(),
            '[0.03s][class,load] clbg.nbody.MainKt source: '+classes.as_uri(),
            '[0.04s][class,load] kotlin.jvm.internal.Intrinsics source: '+stdlib.as_uri(),
            '[0.05s][class,load] java.lang.management.ManagementFactory source: jrt:/java.management',
            '[0.06s][class,load] java.lang.management.ManagementFactory$PlatformMBeanFinder source: jrt:/java.management',
            '[0.07s][class,load] java.lang.management.ManagementFactory$PlatformMBeanFinder$$Lambda/0x123 source: java.lang.management.ManagementFactory'])
        self.assertIn('clbg.nbody.MainKt',kb.validate_log(valid,classes,stdlib,probe,owners))
        with self.assertRaisesRegex(AssertionError,'Unretained benchmark'):
            kb.validate_log(valid.replace('clbg.nbody.MainKt','clbg.other.MainKt'),classes,stdlib,probe,owners)
        with self.assertRaisesRegex(AssertionError,'Unexpected non-platform'):
            kb.validate_log(valid.replace(stdlib.as_uri(),(self.directory/'other.jar').as_uri()),classes,stdlib,probe,owners)
        with self.assertRaisesRegex(AssertionError,'Unknown class origin'):
            kb.validate_log(valid.replace('source: java.lang.management.ManagementFactory','source: java.unloaded.Host'),classes,stdlib,probe,owners)

    def test_output_tolerance_and_complete_bytes(self):
        result = kb.eb.output_validation('nbody',b'-0.169075164\n-0.169075164\n',b'-0.169075163\n-0.169075163\n')
        self.assertTrue(result['reference_match']); self.assertEqual(result['tolerance'],1e-8)
        with self.assertRaisesRegex(ValueError,'Malformed N-body'):
            kb.eb.output_validation('nbody',b'nan\nnan\n',b'-0.169075163\n-0.169075163\n')
        with self.assertRaisesRegex(ValueError,'Complete bounded output differs'):
            kb.eb.output_validation('fasta',b'>wrong\n',b'>correct\n')


if __name__ == '__main__': unittest.main()
