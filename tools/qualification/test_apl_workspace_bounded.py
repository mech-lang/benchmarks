"""Pure small-source, fake-child and tempfile faults; no APL or tool intake."""
import copy
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('apl_workspace_bounded.py')
S=importlib.util.spec_from_file_location('apl_workspace_tested',P)
m=importlib.util.module_from_spec(S);S.loader.exec_module(m)
SPEC=json.loads(m.SPEC.read_bytes())
SCOPE=json.loads(m.RUNTIME_SCOPE.read_bytes())
CONFIG=Path(SPEC['runtime_source_evidence']['config.h']['path']).read_text()
PATTERN=m.configuration_pattern(CONFIG,SCOPE['runtime']['version'])


def configuration_output():
    # Fixture independent of the parser: native sizes remain synthetic here.
    configure=json.loads(re.search(r'^#define cfg_CONFIGURE_ARGS (".*")$',CONFIG,re.M)[1])
    return ('\nconfigurable options:\n---------------------\n'
        '    ASSERT_LEVEL_WANTED=1 (default)\n    SECURITY_LEVEL_WANTED=0 (default)\n'
        '    APSERVER_PATH=/tmp/GNU-APL/APserver (default)\n    APSERVER_PORT=16366 (default)\n'
        '    APSERVER_TRANSPORT=0 (default)\n    CORE_COUNT_WANTED=-2  (= argv (--cc))\n'
        '    DYNAMIC_LOG_WANTED=no (default)\n    MAX_RANK_WANTED=8 (default)\n'
        '    RATIONAL_NUMBERS_WANTED=no (default)\n    SHORT_VALUE_LENGTH_WANTED=12, therefore:\n'
        '        sizeof(Value)       : 320 bytes\n        sizeof(Cell)        :  16 bytes\n'
        '        sizeof(Value header): 128 bytes\n\n'
        '    VALUE_CHECK_WANTED=no (default)\n    VALUE_HISTORY_WANTED=no (default)\n'
        '    VF_TRACING_WANTED=no (default)\n    VISIBLE_MARKERS_WANTED=no (default)\n\n'
        'how ./configure was (probably) called:\n--------------------------------------\n    '+configure+'\n\n'+SCOPE['runtime']['version']+'\n').encode()


class SourcePolicy(unittest.TestCase):
    def test_exact_saved_spec_five_commands_and_only_bounded_scope(self):
        self.assertEqual(hashlib.sha256(m.SPEC.read_bytes()).hexdigest(),m.SPEC_SHA)
        self.assertEqual(tuple(r['id'] for r in m.validate_spec(SPEC)),m.IDS)
        self.assertEqual([r['timeout_seconds'] for r in SPEC['commands']],[30,30,30,30,60])
        self.assertTrue(all(SPEC['qualification'][k] is False for k in m.FALSE_GATES))

    def test_spec_order_size_retries_and_fd_collision_fail(self):
        for fault in ('order','size','retry','fd','deadline','stdin'):
            spec=copy.deepcopy(SPEC)
            if fault=='order':spec['commands'].reverse()
            elif fault=='size':spec['commands'][-1]['argv'][-1]='21'
            elif fault=='retry':spec['supervision']['no_retries']=False
            elif fault=='fd':spec['supervision']['minimum_inherited_lock_fd']=3
            elif fault=='deadline':spec['commands'][0]['timeout_seconds']=3600
            else:spec['commands'][0]['stdin']='pipe'
            with self.subTest(fault=fault),self.assertRaises(AssertionError):m.validate_spec(spec)

    def test_all_exact_oracles_and_unknown_stderr(self):
        for slot in SPEC['commands']:
            stdout=b'' if slot['id']=='configuration' else slot['expected_stdout_utf8'].encode()
            stderr=configuration_output() if slot['id']=='configuration' else b''
            result=m.check_output(slot,stdout,stderr,PATTERN)
            self.assertTrue(result['exact_output'])
            with self.assertRaises(AssertionError):m.check_output(slot,stdout,stderr+b'warning\n',PATTERN)
            with self.assertRaises(AssertionError):m.check_output(slot,stdout+b'x',stderr,PATTERN)
        bad=configuration_output().replace(b'320 bytes',b'321 bytes')
        with self.assertRaises(AssertionError):m.check_output(SPEC['commands'][0],b'',bad,PATTERN)

    def test_stream_bound_and_failed_workspace_are_not_valid_outputs(self):
        with self.assertRaises(AssertionError):m.check_output(SPEC['commands'][1],b'x'*(m.FILE_LIMIT+1),b'',PATTERN)
        with self.assertRaises(AssertionError):m.check_output(SPEC['commands'][2],b'',b'WS FULL+\n',PATTERN)


class FakeKernel:
    def __init__(self,pid):self.pid=pid;self.status=2
    def identity(self,pid):
        return dict(pid=pid,ppid=os.getpid(),pgid=pid,birth_seconds=123,birth_microseconds=pid,status=self.status)
    def group(self,pid):return [] if self.status==5 else [self.identity(pid)]
    def resident_bytes(self,identity):return 4096


class OwnedStage(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.inherited=dict(fd=64,device=1,inode=m.kb.LOCK_INODE)
        self.lock=SimpleNamespace(fileno=lambda:64);self.pid=900;self.launches=[];self.waits=[]

    def fake_observe(self,slot,directory,lock,launched,pattern,*,failure=None,stderr=None,early_exit=False):
        self.pid+=1;kernel=FakeKernel(self.pid)
        process=SimpleNamespace(pid=self.pid,args=slot['argv'],stdin=None,stdout=io.BytesIO())
        def wait(timeout):
            self.assertEqual(kernel.group(process.pid),[])
            self.waits.append(process.pid);return 0
        process.wait=wait
        def launch(command,**kwargs):
            self.assertEqual(kwargs['pass_fds'],(64,));self.assertTrue(kwargs['start_new_session'])
            self.assertEqual(kwargs['cwd'],slot['cwd']);self.assertNotEqual(kwargs['cwd'],str(directory))
            self.assertEqual(kwargs['stdin'],m.subprocess.DEVNULL)
            self.launches.append(command)
            raw=configuration_output() if slot['id']=='configuration' else b''
            kwargs['stderr'].write(raw if stderr is None else stderr);kwargs['stderr'].flush()
            return process
        def transfer(child,payload,output,deadline,tick):
            if early_exit:kernel.status=5
            tick()
            if failure:raise failure
            if slot['id']!='configuration':output.write(slot['expected_stdout_utf8'].encode());output.flush()
            kernel.status=5
        def kill(pgid,sig):
            self.assertEqual(pgid,process.pid);kernel.status=5
        with patch.object(m,'lock_identity',return_value=self.inherited),patch.object(m.os,'killpg',side_effect=kill):
            return m.observe(slot,directory,lock,launched,pattern,kernel=kernel,launch=launch,
                             transfer=transfer,drainer=lambda *_:None)

    def slot(self,index=1):return dict(SPEC['commands'][index],directory=f'{index:02}-'+m.IDS[index])

    def capture(self,index=1):
        slot=self.slot(index);directory=self.root/slot['directory'];directory.mkdir()
        result=self.fake_observe(slot,directory,self.lock,lambda pid:None,PATTERN)
        capture,snapshot=m.checked_capture(slot,directory,os.getpid(),self.inherited,PATTERN)
        return slot,directory,result,capture,snapshot

    def test_owned_launch_uses_high_fd_actual_cwd_devnull_and_reaps(self):
        slot,directory,result,_,_=self.capture()
        self.assertEqual(result['status'],'native-passed');self.assertEqual(len(self.waits),1)
        self.assertEqual(result['cwd'],slot['cwd']);self.assertEqual(result['sampler_processes'],0)

    def test_fd3_rejected_before_start_or_launch(self):
        directory=self.root/'bad';directory.mkdir()
        with self.assertRaisesRegex(AssertionError,'FD >=64'):
            m.observe(self.slot(),directory,SimpleNamespace(fileno=lambda:3),lambda _:None,PATTERN,
                      launch=lambda *_:self.fail('FD3 reached launch'))
        self.assertEqual(list(directory.iterdir()),[])

    def test_fast_exit_without_live_rss_uses_null_and_no_memory_claim(self):
        slot=self.slot(0);directory=self.root/slot['directory'];directory.mkdir()
        result=self.fake_observe(slot,directory,self.lock,lambda _:None,PATTERN,early_exit=True)
        capture,_=m.checked_capture(slot,directory,os.getpid(),self.inherited,PATTERN)
        self.assertIsNone(result['observed_peak_process_group_rss_bytes'])
        self.assertIsNone(capture['observed_peak_process_group_rss_bytes'])
        self.assertFalse(capture['live_rss_observation_obtained'])
        self.assertFalse(capture['rss_observation_complete']);self.assertFalse(capture['memory_usage_qualified'])
        result['observed_peak_process_group_rss_bytes']=0
        (directory/'process.json').write_text(json.dumps(result))
        with self.assertRaises(AssertionError):m.checked_capture(slot,directory,os.getpid(),self.inherited,PATTERN)

    def test_high_fd_acquisition_holds_original_inode_until_context_exit(self):
        path=self.root/'mutex';path.write_bytes(b'')
        inode=path.stat().st_ino
        with patch.object(m.kb,'LOCK',path),patch.object(m.kb,'LOCK_INODE',inode),patch.object(m.kb.kh,'LOCK',path),patch.object(m.kb.kh,'LOCK_INODE',inode):
            with m.held_mutex() as lock:
                fd=lock.fileno();self.assertGreaterEqual(fd,64)
                self.assertEqual(os.fstat(fd).st_ino,inode)
                with path.open('rb') as competing:
                    with self.assertRaises(BlockingIOError):fcntl.flock(competing,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(OSError):os.fstat(fd)

    def test_timeout_reaps_and_keeps_failure_without_retry(self):
        slot=self.slot();directory=self.root/slot['directory'];directory.mkdir()
        error=m.subprocess.TimeoutExpired(slot['argv'],slot['timeout_seconds'])
        with self.assertRaises(m.subprocess.TimeoutExpired):
            self.fake_observe(slot,directory,self.lock,lambda _:None,PATTERN,failure=error)
        receipt=json.loads((directory/'process.json').read_bytes())
        self.assertTrue(receipt['timed_out']);self.assertTrue(receipt['direct_child_reaped'])
        self.assertEqual(receipt['remaining_after_cleanup'],[]);self.assertEqual(len(self.launches),1)
        self.assertEqual(receipt['stop_signals'],[int(m.signal.SIGKILL)])

    def test_unknown_stderr_normal_exit_does_not_pass(self):
        slot=self.slot();directory=self.root/slot['directory'];directory.mkdir()
        with self.assertRaisesRegex(AssertionError,'Unknown APL stderr'):
            self.fake_observe(slot,directory,self.lock,lambda _:None,PATTERN,stderr=b'unknown warning\n')
        receipt=json.loads((directory/'process.json').read_bytes())
        self.assertEqual(receipt['exit_status'],0);self.assertEqual(receipt['status'],'failed')
        self.assertEqual((directory/'stderr.bin').read_bytes(),b'unknown warning\n')

    def test_receipt_identity_cleanup_stream_and_descriptor_faults_rejected(self):
        slot,directory,receipt,_,_=self.capture()
        for fault in ('reap','group','identity','fd','cwd','boolean_exit','stream'):
            broken=copy.deepcopy(receipt)
            if fault=='reap':broken['direct_child_reaped']=False
            elif fault=='group':broken['remaining_process_group']=[{'pid':1}]
            elif fault=='identity':broken['identity']['ppid']+=1
            elif fault=='fd':broken['inherited_lock_descriptor']['fd']=3
            elif fault=='cwd':broken['cwd']=str(directory)
            elif fault=='boolean_exit':broken['exit_status']=False
            else:broken['stdout_sha256']='0'*64
            (directory/'process.json').write_text(json.dumps(broken))
            with self.subTest(fault=fault),self.assertRaises(AssertionError):
                m.checked_capture(slot,directory,os.getpid(),self.inherited,PATTERN)

    def completed(self):
        report=dict(status=m.SUCCESS,attempted_commands=[],registered_commands=[],native_processes_started=5,
            captures=[],validated_artifacts={},active=None,inherited_lock_descriptor=self.inherited)
        schedule=[]
        for index in range(5):
            slot,directory,receipt,capture,snapshot=self.capture(index)
            schedule.append(slot);report['attempted_commands'].append(slot['directory'])
            report['registered_commands'].append(dict(directory=slot['directory'],pid=receipt['pid']))
            report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
        return report,dict(schedule=schedule,absent_inputs=[],configuration_pattern=PATTERN)

    def test_five_closed_captures_and_terminal_keep_all_26_artifacts(self):
        report,plan=self.completed()
        with patch.object(m,'verify'),patch.object(m,'lock_identity',return_value=self.inherited):
            m.finish(report,plan,self.root,{}, {},self.lock)
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],m.SUCCESS);self.assertEqual(len(terminal['available_evidence']),26)
        self.assertEqual(terminal['sampler_processes'],0);self.assertFalse(terminal['full_timing_qualified'])

    def test_late_capture_or_report_change_during_final_pin_replay_fails(self):
        for filename in ('00-configuration/stderr.bin','report.json'):
            with self.subTest(filename=filename):
                child=self.root/filename.replace('/','-');child.mkdir()
                original_root=self.root;self.root=child
                report,plan=self.completed();calls=0
                def verify(*args):
                    nonlocal calls
                    calls+=1
                    if calls==2:(self.root/filename).write_bytes(b'changed')
                with patch.object(m,'verify',side_effect=verify),patch.object(m,'lock_identity',return_value=self.inherited):
                    m.finish(report,plan,self.root,{}, {},self.lock)
                self.assertEqual(report['status'],'failed-integrity');self.root=original_root

    def test_initial_report_snapshot_cannot_adopt_external_edit(self):
        report,plan=self.completed();original=m.inventory
        def inventory(path,exclude=()):
            if path == self.root and exclude == ('terminal.json',):
                (self.root/'report.json').write_bytes(b'{}\n')
            return original(path,exclude)
        with patch.object(m,'verify'),patch.object(m,'lock_identity',return_value=self.inherited),patch.object(m,'inventory',side_effect=inventory):
            m.finish(report,plan,self.root,{}, {},self.lock)
        self.assertEqual(report['status'],'failed-integrity')
        self.assertTrue(any('validated ledger bytes' in e for e in report['integrity_errors']))

    def test_failed_first_native_stops_whole_stage_without_retry(self):
        plan_path=self.root/'plan.json';plan_path.write_text('{}')
        plan=dict(output=str(self.root/'output'),pins={},input_resolutions={},absent_inputs=[],
                  schedule=[self.slot(i) for i in range(5)],configuration_pattern=PATTERN)
        def observer(*args):return self.fake_observe(*args,stderr=b'unknown diagnostic\n')
        # Exercise the real local lifecycle with a synthetic child, not APL.
        real_observer=m.observe
        def first(*args):
            with patch.object(m,'observe',real_observer):return observer(*args)
        with patch.object(m,'verify'),patch.object(m,'lock_identity',return_value=self.inherited),patch.object(m,'observe',side_effect=first):
            report=m.run_plan(plan,plan_path,m.sha(plan_path),self.lock)
        self.assertEqual(report['status'],'failed');self.assertEqual(len(self.launches),1)
        self.assertEqual(report['native_processes_started'],1);self.assertEqual(len(report['attempted_commands']),1)
        self.assertEqual(len(self.waits),1);self.assertEqual(report['captures'],[])

    def test_schedule_retry_or_incomplete_success_fails_terminal(self):
        report,plan=self.completed();report['attempted_commands'].append(report['attempted_commands'][-1])
        with patch.object(m,'verify'),patch.object(m,'lock_identity',return_value=self.inherited):
            m.finish(report,plan,self.root,{}, {},self.lock)
        self.assertEqual(report['status'],'failed-integrity')

    def test_pin_drift_and_new_preference_candidate_fail(self):
        source=self.root/'source';source.write_bytes(b'original');absent=self.root/'preferences'
        pins={str(source):m.sha(source)};resolutions={str(source):str(source)}
        with patch.object(m,'lock_identity',return_value=self.inherited):
            m.verify(pins,resolutions,[str(absent)],self.lock)
            source.write_bytes(b'changed')
            with self.assertRaises(AssertionError):m.verify(pins,resolutions,[str(absent)],self.lock)
            source.write_bytes(b'original');absent.write_bytes(b'new setting')
            with self.assertRaises(AssertionError):m.verify(pins,resolutions,[str(absent)],self.lock)


if __name__=='__main__':unittest.main()
