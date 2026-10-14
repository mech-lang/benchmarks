"""Pure fixtures for helper supervision, retained artifacts, and observation gates."""
import importlib.util
import ctypes
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('kotlin_helpers',ROOT/'tools/qualification/kotlin_helpers.py')
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


class FakeProcess:
    pid = 424242
    args = ['retained-java','helperqualification.HelperProbe']
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


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.directory = Path(self.temporary.name).resolve()
    def tearDown(self): self.temporary.cleanup()
    def observe(self,transfer,expected=b'answer',kernel=None,launch=None):
        def create(*args,**kwargs):
            self.assertEqual(kwargs['pass_fds'],(99,))
            self.assertTrue(kwargs['start_new_session'])
            self.assertIs(kwargs['stdout'],subprocess.PIPE)
            return FakeProcess()
        with patch.object(helper,'verify_lock'), patch.object(helper.os,'killpg') as kill:
            try:
                return helper.observe(['retained-java'],{},self.directory,b'input',expected,FakeLock(),
                    kernel=kernel or FakeKernel(),launch=launch or create,transfer=transfer,
                    drain=lambda stream,path,deadline:None)
            finally:
                self.signals = kill.call_args_list
    def receipt(self): return json.loads((self.directory/'process.json').read_text())

    def test_success_retains_real_command_accounting_and_streams(self):
        def transfer(process,payload,out,deadline):
            self.assertEqual(payload,b'input'); out.write(b'answer')
        receipt = self.observe(transfer)
        self.assertEqual(receipt['status'],'passed')
        self.assertTrue(receipt['direct_child_reaped'])
        self.assertTrue(receipt['complete_output_matches'])
        self.assertEqual(receipt['stop_signals'],[])
        self.assertTrue((self.directory/'start.json').is_file())
        self.assertTrue((self.directory/'active.json').is_file())

    def test_bad_output_retained_after_normal_exit(self):
        with self.assertRaisesRegex(AssertionError,'Complete stdout differs'):
            self.observe(lambda p,b,o,d:o.write(b'wrong'))
        self.assertEqual((self.directory/'stdout.bin').read_bytes(),b'wrong')
        self.assertTrue(self.receipt()['direct_child_reaped'])
        self.assertEqual(self.signals,[])

    def test_timeout_preserves_partial_pipe_output_and_owned_cleanup(self):
        class LiveUntilKilled(FakeKernel):
            calls = 0
            def group(self,pgid):
                self.calls += 1
                return [dict(pid=pgid,pgid=pgid,status=2)] if self.calls == 1 else []
        def transfer(process,payload,out,deadline):
            out.write(b'partial'); out.flush()
            raise subprocess.TimeoutExpired(process.args,30)
        with self.assertRaises(subprocess.TimeoutExpired): self.observe(transfer,kernel=LiveUntilKilled())
        receipt = self.receipt()
        self.assertTrue(receipt['timed_out']); self.assertTrue(receipt['direct_child_reaped'])
        self.assertEqual(receipt['remaining_after_cleanup'],[])
        self.assertEqual(receipt['stop_signals'],[9])
        self.assertEqual((self.directory/'stdout.bin').read_bytes(),b'partial')
        self.assertEqual(self.signals[0].args,(424242,9))

    def test_kernel_identity_includes_unreaped_zombie(self):
        test = self
        class FakeLibrary:
            def proc_pidinfo(self,pid,flavor,arg,buffer,size):
                test.assertEqual((pid,flavor,arg),(424242,3,1))
                info = ctypes.cast(buffer,ctypes.POINTER(helper.BSDInfo)).contents
                info.pid = pid; info.ppid = os.getpid(); info.pgid = pid
                info.status = 5; info.birth_seconds = 1; info.birth_microseconds = 2
                return size
        kernel = helper.Kernel.__new__(helper.Kernel); kernel.library = FakeLibrary()
        self.assertEqual(kernel.identity(424242)['status'],5)

    def test_failed_observation_of_already_empty_group_sends_no_signal(self):
        def transfer(process,payload,out,deadline): raise RuntimeError('observation failed')
        with self.assertRaisesRegex(RuntimeError,'observation failed'): self.observe(transfer)
        self.assertTrue(self.receipt()['direct_child_reaped'])
        self.assertEqual(self.receipt()['cleanup_errors'],[])
        self.assertEqual(self.signals,[])

    def test_cleanup_failure_is_terminal_and_retains_failure(self):
        class BrokenKernel(FakeKernel):
            def group(self,pgid): raise RuntimeError('kernel inventory unavailable')
        def transfer(process,payload,out,deadline):
            out.write(b'partial'); raise subprocess.TimeoutExpired(process.args,30)
        with self.assertRaisesRegex(AssertionError,'Cleanup or output retention failed'):
            self.observe(transfer,kernel=BrokenKernel())
        receipt = self.receipt()
        self.assertEqual(receipt['status'],'failed-cleanup-or-artifacts')
        self.assertIn('kernel inventory unavailable',receipt['cleanup_errors'])
        self.assertFalse(receipt['direct_child_reaped'])
        self.assertEqual(receipt['error_type'],'TimeoutExpired')

    def test_failed_launch_never_registers_native_execution(self):
        def launch(*args,**kwargs): raise OSError('executable unavailable')
        with self.assertRaisesRegex(OSError,'executable unavailable'):
            self.observe(None,launch=launch)
        receipt = self.receipt()
        self.assertNotIn('pid',receipt)
        self.assertFalse(receipt['direct_child_reaped'])
        self.assertEqual(self.signals,[])
        self.assertTrue((self.directory/'stdout.bin').is_file())

    def test_cleanup_drains_bytes_still_buffered_in_real_pipe(self):
        path = self.directory/'stdout.bin'; path.write_bytes(b'already retained;')
        read_fd,write_fd = os.pipe()
        try:
            os.write(write_fd,b'buffered at failure'); os.close(write_fd); write_fd = None
            with os.fdopen(read_fd,'rb',buffering=0) as stream:
                read_fd = None
                helper.retain_pipe(stream,path,time.monotonic()+2)
            self.assertEqual(path.read_bytes(),b'already retained;buffered at failure')
        finally:
            if read_fd is not None: os.close(read_fd)
            if write_fd is not None: os.close(write_fd)

    def test_main_and_foreign_class_origins_fail(self):
        classes = self.directory/'classes'; probe = self.directory/'probe'; stdlib = self.directory/'stdlib.jar'
        valid = '\n'.join([
            '[0.01s][class,load] java.lang.Object source: shared objects file',
            '[0.02s][class,load] helperqualification.HelperProbe source: '+probe.as_uri(),
            '[0.03s][class,load] clbg.Support source: '+classes.as_uri(),
            '[0.04s][class,load] kotlin.jvm.internal.Intrinsics source: '+stdlib.as_uri(),
            '[0.05s][class,load] java.lang.management.ManagementFactory source: jrt:/java.management',
            '[0.06s][class,load] java.lang.management.ManagementFactory$$Lambda/0x123 source: java.lang.management.ManagementFactory'])
        self.assertIn('clbg.Support',helper.validate_log(valid,classes,stdlib,probe))
        with self.assertRaisesRegex(AssertionError,'Prohibited benchmark owner'):
            helper.validate_log(valid+'\n[1.0s][class,load] clbg.nbody.MainKt source: '+classes.as_uri(),classes,stdlib,probe)
        with self.assertRaisesRegex(AssertionError,'Unexpected non-platform class origin'):
            helper.validate_log(valid.replace(stdlib.as_uri(),(self.directory/'unapproved.jar').as_uri()),classes,stdlib,probe)
        with self.assertRaisesRegex(AssertionError,'Unknown class origin'):
            helper.validate_log(valid.replace('source: java.lang.management.ManagementFactory','source: java.unobserved.Host'),classes,stdlib,probe)

    def test_retained_directory_copy_must_match_exact_complete_inventory(self):
        original = self.directory/'missing'/'classes'
        retained = self.directory/'retained'/'classes'; (retained/'clbg').mkdir(parents=True)
        path = retained/'clbg/Support.class'; path.write_bytes(b'exact retained class')
        digest = helper.sha(path)
        item = dict(path=str(original/'clbg/Support.class'),sha256=digest,bytes=path.stat().st_size)
        row = dict(compile_command=dict(command=['compiler',str(original)]),generated_artifacts=[item])
        mapping = {item['path']:dict(stored_path='retained/classes/clbg/Support.class',sha256=digest,bytes=item['bytes'])}
        def bind(path,expected): self.assertEqual(helper.sha(path),expected)
        with patch.object(helper,'ROOT',self.directory),patch.object(helper,'SUPPORT_CLASS_SHA',digest):
            self.assertEqual(helper.class_directory(row,mapping,bind),(original,retained))
            (retained/'Unexpected.class').write_bytes(b'extra')
            with self.assertRaisesRegex(AssertionError,'Class directory changed'):
                helper.class_directory(row,mapping,bind)

    def test_nested_platform_lambda_requires_loaded_matching_host_and_enclosing_class(self):
        classes = self.directory/'classes'; probe = self.directory/'probe'; stdlib = self.directory/'stdlib.jar'
        prefix = '\n'.join([
            '[0.01s][class,load] helperqualification.HelperProbe source: '+probe.as_uri(),
            '[0.02s][class,load] clbg.Support source: '+classes.as_uri()])+'\n'
        host = 'java.lang.management.ManagementFactory'
        enclosing = host+'$PlatformMBeanFinder'
        host_line = '[0.03s][class,load] '+host+' source: jrt:/java.management\n'
        enclosing_line = '[0.04s][class,load] '+enclosing+' source: jrt:/java.management\n'
        lambda_line = '[0.05s][class,load] '+enclosing+'$$Lambda/0x00007ff801008e90 source: '+host
        self.assertIn(enclosing+'$$Lambda/0x00007ff801008e90',
            helper.validate_log(prefix+host_line+enclosing_line+lambda_line,classes,stdlib,probe))
        failures = [
            prefix+enclosing_line+lambda_line,
            prefix+host_line+lambda_line,
            prefix+host_line+enclosing_line.replace('jrt:/java.management','jrt:/java.base')+lambda_line,
            prefix+host_line+enclosing_line.replace(host+'$',host+'Other$')+lambda_line.replace(host+'$',host+'Other$'),
            prefix+host_line+enclosing_line+lambda_line.replace('$$Lambda/0x00007ff801008e90','$$LambdaUnexpected'),
        ]
        for text in failures:
            with self.subTest(log=text),self.assertRaisesRegex(AssertionError,'Unknown class origin'):
                helper.validate_log(text,classes,stdlib,probe)

    def test_complete_saved_first_helper_class_log(self):
        case = ROOT/'experiments/kotlin/helper-semantics/run-v2/kotlin-binarytrees-compact'
        summary = json.loads((case/'summary.json').read_text())
        def path(uri): return Path(helper.unquote(helper.urlparse(uri).path)).resolve()
        classes = path(summary['support_code_source'])
        stdlib = path(summary['non_platform_class_origins']['kotlin.jvm.internal.Intrinsics'])
        probe = Path(summary['runtime']['CLASS_PATH']).resolve()
        observed = helper.validate_log((case/'classes.log').read_text(),classes,stdlib,probe)
        self.assertEqual([name for name in observed if name.startswith('clbg.')],['clbg.Support'])

    def test_shared_independent_format_vector_bytes(self):
        pins = {}
        path = ROOT/'experiments/elixir/helper-semantics/generate_vectors.py'
        generator = helper.load_module(path,pins)
        vectors = list(generator.vectors())
        self.assertEqual(len(vectors),1536)
        self.assertEqual(''.join('\t'.join(row)+'\n' for row in vectors).encode(),path.with_name('format-vectors.tsv').read_bytes())


if __name__ == '__main__': unittest.main()
