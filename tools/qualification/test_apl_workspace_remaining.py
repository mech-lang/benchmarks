"""Small pure contract and temporary receipt faults; no APL or closure intake."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('apl_workspace_remaining.py')
s=importlib.util.spec_from_file_location('apl_remaining_tested',P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OLD=json.loads((m.ORIGINAL/'plan-v1.json').read_bytes())
PATTERN=OLD['configuration_pattern']


class Policy(unittest.TestCase):
    def test_only_exact_shutdown_bytes_with_exact_stdout(self):
        for slot in OLD['schedule'][1:]:
            stdout=slot['expected_stdout_utf8'].encode()
            self.assertTrue(m.check_output(slot,stdout,m.WARNING,PATTERN)['exact_shutdown_diagnostic'])
            for raw in (b'',m.WARNING+b'WS FULL+\n',b'WS FULL+\n'+m.WARNING,m.WARNING*2,m.WARNING.rstrip(),m.WARNING.replace(b'pipe-to_client',b'/dev/fd/3')):
                with self.subTest(slot=slot['id'],raw=raw),self.assertRaises(AssertionError):m.check_output(slot,stdout,raw,PATTERN)
            with self.assertRaises(AssertionError):m.check_output(slot,stdout+b'x',m.WARNING,PATTERN)

    def test_configuration_still_has_unchanged_complete_contract(self):
        directory=m.OLD_RUN/'00-configuration'
        result=m.check_output(OLD['schedule'][0],b'',(directory/'stderr.bin').read_bytes(),PATTERN)
        self.assertEqual(result['configuration_sizes'],dict(value=464,cell=24,header=176))
        with self.assertRaises(AssertionError):m.check_output(OLD['schedule'][0],b'',(directory/'stderr.bin').read_bytes()+m.WARNING,PATTERN)

    def test_frozen_base_is_not_mutated(self):
        self.assertEqual(hashlib.sha256(m.BASE.read_bytes()).hexdigest(),m.BASE_SHA)
        self.assertEqual(hashlib.sha256(m.DIAGNOSTIC.read_bytes()).hexdigest(),m.DIAGNOSTIC_SHA)
        self.assertEqual(m.b.observe.__code__.co_filename,str(m.BASE))
        self.assertEqual(m.b.check_output,m.check_output)

    def test_remaining_plan_keeps_only_original_last_three(self):
        output=m.PACKET/'unexecuted-test-output'
        base=copy.deepcopy(OLD);base['output']=str(output)
        base['absent_inputs']=[str(output/d/'home/preferences') for d in ('00-configuration','01-workspace-readback','02-allocation-ownership')]
        prefix={'retained_native_observations':2,'original_status':'failed'}
        diagnostic=json.loads(m.DIAGNOSTIC.read_bytes())
        with patch.object(m.b,'build_plan',return_value=base),patch.object(m,'retained_prefix',return_value=prefix),patch.object(m,'document',return_value=diagnostic),patch.object(m,'pin'):
            result=m.build_plan(output)
        self.assertEqual(result['schedule'],OLD['schedule'][2:]);self.assertEqual(result['native_commands'],3)
        self.assertEqual(result['retained_prefix'],prefix);self.assertEqual(len(result['absent_inputs']),1)
        self.assertTrue(all(result[k] is False for k in m.FALSE_GATES))


class Retained(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.slot=OLD['schedule'][1]
        self.directory=self.root/self.slot['directory'];self.directory.mkdir()
        for p in (m.OLD_RUN/self.slot['directory']).iterdir():
            if p.is_file():(self.directory/p.name).write_bytes(p.read_bytes())
        for name in ('start','active','process'):
            path=self.directory/(name+'.json');value=json.loads(path.read_bytes());value['artifact_directory']=str(self.directory);value['environment']=m.b.environment(self.directory);path.write_text(json.dumps(value))
        self.process=json.loads((self.directory/'process.json').read_bytes());self.parent=self.process['identity']['ppid'];self.inherited=self.process['inherited_lock_descriptor']

    def check(self):return m.retained_capture(self.slot,self.directory,self.parent,self.inherited,PATTERN)

    def test_saved_failed_readback_remains_failed_in_disposition(self):
        capture,_=self.check();self.assertEqual(capture['original_producer_status'],'failed')
        self.assertEqual(capture['original_error'],'Unknown APL stderr; complete raw bytes retained')
        self.assertTrue(capture['output_validation']['exact_shutdown_diagnostic'])
        self.assertTrue(all(capture[k] is False for k in m.FALSE_GATES))

    def test_wrong_failure_lifetime_exit_or_promoted_status_rejected(self):
        for fault in ('error','exit','status','group','reap','fd','identity','validation'):
            value=copy.deepcopy(self.process)
            if fault=='error':value['error']='native application failed'
            elif fault=='exit':value['exit_status']=1
            elif fault=='status':value['status']='native-passed'
            elif fault=='group':value['remaining_process_group']=[{'pid':123}]
            elif fault=='reap':value['direct_child_reaped']=False
            elif fault=='fd':value['inherited_lock_descriptor']['fd']=3
            elif fault=='identity':value['identity']['ppid']+=1
            else:value['output_validation']={'exact_output':True}
            (self.directory/'process.json').write_text(json.dumps(value))
            with self.subTest(fault=fault),self.assertRaises(AssertionError):self.check()

    def test_changed_raw_bytes_even_rehashed_are_rejected(self):
        raw=m.WARNING+b'WS FULL+\n';(self.directory/'stderr.bin').write_bytes(raw)
        value=copy.deepcopy(self.process);value['stderr_bytes']=len(raw);value['stderr_sha256']=hashlib.sha256(raw).hexdigest()
        (self.directory/'process.json').write_text(json.dumps(value))
        with self.assertRaises(AssertionError):self.check()


class Closure(unittest.TestCase):
    def test_success_with_missing_captures_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory).resolve();report=dict(status=m.SUCCESS,registered_commands=[],attempted_commands=[],native_processes_started=0,captures=[],validated_artifacts={},inherited_lock_descriptor={'fd':64,'inode':79859134})
            plan=dict(schedule=OLD['schedule'][2:],absent_inputs=[],configuration_pattern=PATTERN)
            with patch.object(m,'verify'),patch.object(m,'lock_identity'):
                m.finish(report,plan,output,{}, {},None)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity');self.assertIn('Incomplete three-command stage',terminal['integrity_errors'])

    def test_original_extra_artifact_detected_after_pin_check(self):
        with patch.object(m.b,'verify'),patch.object(m,'lock_identity'),patch.object(m,'inventory',return_value={}):
            with self.assertRaisesRegex(AssertionError,'Original failed evidence inventory changed'):m.verify({}, {},[],None)


class ThreeCommandClosure(unittest.TestCase):
    def build(self,output):
        template=m.OLD_RUN/'01-workspace-readback'
        inherited=json.loads((template/'process.json').read_bytes())['inherited_lock_descriptor']
        report=dict(status=m.SUCCESS,registered_commands=[],attempted_commands=[],native_processes_started=3,
                    captures=[],validated_artifacts={},inherited_lock_descriptor=inherited)
        schedule=copy.deepcopy(OLD['schedule'][2:])
        for index,slot in enumerate(schedule):
            directory=output/slot['directory'];directory.mkdir();pid=900+index
            begin=f'2026-10-14T22:00:0{index*2}+00:00';end=f'2026-10-14T22:00:0{index*2+1}+00:00'
            raw={'stdout':slot['expected_stdout_utf8'].encode(),'stderr':m.WARNING}
            for name in ('start','active','process'):
                record=json.loads((template/(name+'.json')).read_bytes())
                record.update(command=slot['argv'],environment=m.b.environment(directory),cwd=slot['cwd'],
                              artifact_directory=str(directory),process_timeout_seconds=slot['timeout_seconds'],started_at=begin)
                if name!='start':
                    record.update(pid=pid,pgid=pid)
                    for field in ('identity','leader_identity_before_reap'):
                        if field in record:record[field].update(pid=pid,ppid=os.getpid(),pgid=pid,birth_microseconds=pid)
                if name=='process':
                    record.update(status='native-passed',finished_at=end,output_validation=m.check_output(slot,raw['stdout'],raw['stderr'],PATTERN))
                    for key in ('error','error_type','timed_out'):record.pop(key,None)
                    for stream,data in raw.items():record[stream+'_bytes']=len(data);record[stream+'_sha256']=hashlib.sha256(data).hexdigest()
                (directory/(name+'.json')).write_text(json.dumps(record))
            for name,data in raw.items():(directory/(name+'.bin')).write_bytes(data)
            capture,snapshot=m.checked_capture(slot,directory,os.getpid(),inherited,PATTERN)
            report['attempted_commands'].append(slot['directory']);report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
            report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
        return report,dict(schedule=schedule,absent_inputs=[],configuration_pattern=PATTERN)

    def test_exact_three_close_with_sixteen_artifacts_and_no_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve();report,plan=self.build(output)
            with patch.object(m,'verify'),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],m.SUCCESS);self.assertEqual(terminal['capture_count'],3)
            self.assertEqual(len(terminal['available_evidence']),16);self.assertEqual(terminal['native_processes_started'],3)
            self.assertTrue(all(terminal[k] is False for k in m.FALSE_GATES))

    def test_late_capture_or_report_mutation_cannot_pass(self):
        for target in ('02-allocation-ownership/stderr.bin','report.json'):
            with self.subTest(target=target),tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary).resolve();report,plan=self.build(output);calls=0
                def verify(*args):
                    nonlocal calls
                    calls+=1
                    if calls==2:(output/target).write_bytes(b'changed')
                with patch.object(m,'verify',side_effect=verify),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertTrue(terminal['integrity_errors'])

    def test_changed_prior_lease_rejected_after_physical_pin_replay(self):
        lock=SimpleNamespace(fileno=lambda:64)
        original=SimpleNamespace(st_dev=1,st_ino=82370343)
        changed=SimpleNamespace(st_dev=1,st_ino=82370344)
        with patch.object(m,'_prior_lease',SimpleNamespace(fileno=lambda:65)),patch.object(m.b,'lock_identity',return_value={}),patch.object(m.os,'fstat',return_value=original),patch.object(Path,'stat',side_effect=[original,changed]),patch.object(m.b,'verify'):
            with self.assertRaisesRegex(AssertionError,'Original durable lease changed'):m.verify({}, {},[],lock)


if __name__=='__main__':unittest.main()
