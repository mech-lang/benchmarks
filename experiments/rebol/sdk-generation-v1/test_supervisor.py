"""Pure ownership/retention fixtures; no native process or vendor source load."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


S = load('sdk_supervisor_fixture', ROOT/'tools/qualification/rebol_sdk_supervisor.py')
C = load('sdk_controller_fixture', ROOT/'tools/qualification/rebol_sdk.py')


class Process:
    pid = 4321
    returncode = None

    def __init__(self, events, code=0):
        self.events = events; self.code = code

    def wait(self, timeout):
        self.events.append(('wait', timeout)); self.returncode = self.code
        return self.code


class SupervisorTests(unittest.TestCase):
    def invoke(self, directory, process, identity_status=5, timeout=300):
        identity = dict(pid=process.pid, ppid=os.getpid(), pgid=process.pid, status=identity_status,
                        birth_seconds=1, birth_microseconds=2)
        kernel = SimpleNamespace(identity=lambda pid: dict(identity))
        def spawn(*args, **kwargs):
            self.assertEqual(kwargs['pass_fds'], (19,))
            self.assertTrue(kwargs['start_new_session'])
            self.assertTrue(callable(kwargs['preexec_fn']))
            kwargs['stdout'].write(b'actual partial output\n')
            kwargs['stderr'].write(b'actual partial diagnostic\n')
            return process
        with patch.object(S, 'lock_identity', return_value=SimpleNamespace(st_ino=79859134)), \
             patch.object(S.subprocess, 'Popen', side_effect=spawn):
            return S.owned_command(['retained-runtime'], {'LANG':'C'}, directory, 19,
                                   timeout, 'generation', directory, kernel=kernel)

    def test_normal_exit_keeps_leader_until_empty_then_reaps_without_signal(self):
        events=[]; process=Process(events)
        def scan(pid, timeout):
            self.assertIsNone(process.returncode); events.append(('scan',timeout)); return []
        with tempfile.TemporaryDirectory() as name, patch.object(S, 'members', side_effect=scan), \
             patch.object(S.os, 'killpg') as kill:
            actual=self.invoke(Path(name),process)
            self.assertEqual([e[0] for e in events],['scan','wait'])
            self.assertEqual(actual['detail']['exit_status'],0)
            self.assertTrue(actual['detail']['direct_child_reaped'])
            kill.assert_not_called()

    def test_monitor_timeout_retains_partial_streams_and_cleanup_receipt(self):
        events=[]; process=Process(events,code=-9)
        with tempfile.TemporaryDirectory() as name, \
             patch.object(S,'members',side_effect=[subprocess.TimeoutExpired('ps',5),[]]), \
             patch.object(S.os,'killpg') as kill:
            directory=Path(name)
            with self.assertRaises(subprocess.TimeoutExpired): self.invoke(directory,process)
            actual=json.loads((directory/'generation.json').read_text())
            self.assertEqual(actual['final_exit_status'],-9)
            self.assertTrue(actual['direct_child_reaped'])
            self.assertEqual(actual['cleanup_errors'],[])
            self.assertEqual(actual['stop_signals'],[int(signal.SIGKILL)])
            self.assertTrue(actual['monitor_errors'])
            self.assertEqual((directory/'generation.stdout').read_bytes(),b'actual partial output\n')
            self.assertEqual((directory/'generation.stderr').read_bytes(),b'actual partial diagnostic\n')
            self.assertEqual(json.loads((directory/'generation-started.json').read_text())['pid'],process.pid)
            kill.assert_called_once_with(process.pid,signal.SIGKILL)

    def test_zombie_leader_with_live_descendant_is_killed_before_reap(self):
        events=[]; process=Process(events)
        def scan(pid,timeout):
            self.assertIsNone(process.returncode); events.append(('scan',timeout))
            return [dict(pid=4322,pgid=4321,status='S')] if len(events)==1 else []
        def kill(pid,sig):
            self.assertIsNone(process.returncode); events.append(('kill',sig))
        with tempfile.TemporaryDirectory() as name, patch.object(S,'members',side_effect=scan), \
             patch.object(S.os,'killpg',side_effect=kill):
            with self.assertRaisesRegex(AssertionError,'live descendants'): self.invoke(Path(name),process)
            self.assertEqual([e[0] for e in events],['scan','kill','scan','wait'])

    def test_normal_monitor_receives_only_remaining_execution_budget(self):
        process=Process([])
        with tempfile.TemporaryDirectory() as name, patch.object(S,'members',return_value=[]) as scan, \
             patch.object(S.time,'monotonic',side_effect=[0,299.5,299.5,299.5]):
            self.invoke(Path(name),process)
            self.assertEqual(scan.call_args.kwargs['timeout'],0.5)

    def test_cleanup_uses_one_deadline_for_scan_and_wait(self):
        process=Process([])
        record=dict(stop_signals=[],cleanup_errors=[],monitor_processes=0)
        with patch.object(S.os,'killpg'), patch.object(S,'members',return_value=[]) as scan, \
             patch.object(S.time,'monotonic',side_effect=[0,4,4.5]):
            S.cleanup_owned(process,record)
            self.assertEqual(scan.call_args.kwargs['timeout'],1)
            self.assertEqual(process.events,[('wait',0.5)])
            self.assertEqual(record['cleanup_errors'],[])

    def test_cleanup_timeout_is_retained_without_unbounded_wait(self):
        process=Process([])
        record=dict(stop_signals=[],cleanup_errors=[],monitor_processes=0)
        with patch.object(S.os,'killpg'), \
             patch.object(S,'members',side_effect=subprocess.TimeoutExpired('ps',5)):
            S.cleanup_owned(process,record)
        self.assertIsNone(process.returncode)
        self.assertEqual(process.events,[])
        self.assertTrue(record['cleanup_errors'])

    def test_cleanup_does_not_signal_already_reaped_pid(self):
        process=Process([]); process.returncode=0
        record=dict(stop_signals=[],cleanup_errors=[],monitor_processes=0,remaining_process_group=[])
        with patch.object(S.os,'killpg') as kill, patch.object(S,'members') as scan:
            S.cleanup_owned(process,record)
            kill.assert_not_called(); scan.assert_not_called()

    def test_zombie_is_not_a_live_group_member(self):
        result=SimpleNamespace(stdout='4321 4321 Z\n4322 4321 S\n77 77 R\n')
        with patch.object(S.subprocess,'run',return_value=result) as run:
            self.assertEqual(S.members(4321,timeout=0.25),[dict(pid=4322,pgid=4321,status='S')])
            self.assertEqual(run.call_args.kwargs['timeout'],0.25)

    def test_artifact_failure_keeps_readable_sibling_pins(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); (root/'good').write_bytes(b'good'); (root/'bad').write_bytes(b'bad')
            def digest(path):
                if Path(path).name=='bad': raise PermissionError('fixture unreadable output')
                return 'retained-good-digest'
            with patch.object(C,'sha',side_effect=digest):
                pins,errors=C.artifact_pins([root])
            self.assertEqual(pins,{str(root/'good'):'retained-good-digest'})
            self.assertEqual(errors,[dict(path=str(root/'bad'),error='fixture unreadable output')])

    def test_artifact_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); (root/'link').symlink_to('/unreadable-target')
            with patch.object(C,'sha') as digest:
                pins,errors=C.artifact_pins([root])
                digest.assert_not_called()
            self.assertEqual(pins,{})
            self.assertEqual(errors[0]['path'],str(root/'link'))

    def test_terminal_survives_unreadable_artifact_and_malformed_command_receipt(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); output=root/'output'; copy=root/'copy'; output.mkdir(); copy.mkdir()
            (output/'header-generation.json').write_text('{broken')
            (output/'header-generation-started.json').write_text('{"pid":4321}')
            (copy/'unreadable.h').write_text('actual generated bytes')
            actual_sha=C.sha
            def digest(path):
                if Path(path).name=='unreadable.h': raise PermissionError('fixture unreadable header')
                return actual_sha(path)
            result=dict(status='stopped-unqualified',native_commands_started=0,chart_admission=False)
            with patch.object(C,'sha',side_effect=digest):
                integrity,artifacts=C.retain_terminal(output,copy,result,{})
            report=json.loads((output/'report.json').read_text())
            terminal=json.loads((output/'terminal.json').read_text())
            self.assertEqual(integrity,[])
            self.assertEqual(report['status'],'failed-artifact-integrity')
            self.assertEqual(report['native_commands_started'],1)
            self.assertTrue(report['command_receipt_error'])
            self.assertEqual(terminal['artifact_errors'],artifacts)
            self.assertEqual(terminal['report_sha256'],actual_sha(output/'report.json'))
            self.assertIn(str(output/'header-generation.json'),report['artifact_pins'])
            self.assertFalse(terminal['chart_admission'])

    def test_pending_stop_after_launch_registration_still_cleans_owned_child(self):
        process=Process([],code=-9)
        restores=0
        def mask(how, values):
            nonlocal restores
            if how==signal.SIG_SETMASK:
                restores+=1
                if restores==1: raise KeyboardInterrupt('fixture pending stop after launch')
            return set()
        with tempfile.TemporaryDirectory() as name, patch.object(S.signal,'pthread_sigmask',side_effect=mask), \
             patch.object(S,'members',return_value=[]), patch.object(S.os,'killpg') as kill:
            directory=Path(name)
            with self.assertRaisesRegex(KeyboardInterrupt,'after launch'): self.invoke(directory,process)
            kill.assert_called_once_with(process.pid,signal.SIGKILL)
            receipt=json.loads((directory/'generation.json').read_text())
            self.assertEqual(receipt['pid'],process.pid)
            self.assertTrue(receipt['direct_child_reaped'])
            self.assertEqual(receipt['final_exit_status'],-9)

    def test_pending_stop_after_reap_never_signals_released_pid(self):
        process=Process([])
        restores=0
        def mask(how, values):
            nonlocal restores
            if how==signal.SIG_SETMASK:
                restores+=1
                if restores==2: raise KeyboardInterrupt('fixture pending stop after reap')
            return set()
        with tempfile.TemporaryDirectory() as name, patch.object(S.signal,'pthread_sigmask',side_effect=mask), \
             patch.object(S,'members',return_value=[]), patch.object(S.os,'killpg') as kill:
            directory=Path(name)
            with self.assertRaisesRegex(KeyboardInterrupt,'after reap'): self.invoke(directory,process)
            kill.assert_not_called()
            receipt=json.loads((directory/'generation.json').read_text())
            self.assertEqual(receipt['exit_status'],0)
            self.assertTrue(receipt['direct_child_reaped'])


if __name__=='__main__': unittest.main(verbosity=2)
