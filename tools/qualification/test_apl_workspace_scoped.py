"""Pure contract/receipt faults; no APL launches or runtime closure replay."""
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

P=Path(__file__).with_name('apl_workspace_scoped.py')
s=importlib.util.spec_from_file_location('apl_scoped_tested',P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OLD=json.loads((m.ORIGINAL/'plan-v1.json').read_bytes())
PATTERN=OLD['configuration_pattern']


def slots():
    result=[]
    for index,(identity,name,stdout) in enumerate(zip(m.IDS,m.FILES,m.EXPECTED)):
        slot=dict(OLD['schedule'][2],id=identity,directory=f'{index:02}-'+identity,
                  expected_stdout_utf8=stdout)
        slot['argv']=slot['argv'][:-1]+[str(m.PACKET/name)]
        result.append(slot)
    return result


class Policy(unittest.TestCase):
    def test_exact_warning_stdout_and_independent_oracles_only(self):
        for slot in slots():
            stdout=slot['expected_stdout_utf8'].encode()
            self.assertTrue(m.check_output(slot,stdout,m.WARNING,PATTERN)['exact_output'])
            for bad in (b'',m.WARNING+b'WS FULL+\n',m.WARNING*2,m.WARNING.rstrip()):
                with self.subTest(bad=bad),self.assertRaises(AssertionError):
                    m.check_output(slot,stdout,bad,PATTERN)
            with self.assertRaises(AssertionError):m.check_output(slot,stdout+b'x',m.WARNING,PATTERN)
            altered=dict(slot,expected_stdout_utf8='live_deltas=1,2,9,4,2,1\n')
            with self.assertRaisesRegex(AssertionError,'Diagnostic oracle changed'):
                m.check_output(altered,altered['expected_stdout_utf8'].encode(),m.WARNING,PATTERN)

    def test_old_subject_and_configuration_commands_not_registered(self):
        for slot in OLD['schedule']:
            with self.assertRaisesRegex(AssertionError,'Only the two'):
                m.check_output(slot,b'',m.WARNING,PATTERN)

    def test_reuses_frozen_native_supervision_without_source_mutation(self):
        self.assertEqual(hashlib.sha256(m.PRIOR.read_bytes()).hexdigest(),m.PRIOR_SHA)
        self.assertEqual(hashlib.sha256(m.r.BASE.read_bytes()).hexdigest(),m.r.BASE_SHA)
        self.assertEqual(m.observe.__code__.co_filename,str(m.r.BASE))
        self.assertEqual(m.b.check_output,m.check_output)
        self.assertEqual(m.b.lock_identity,m.lock_identity)

    def test_plan_contains_only_control_then_witness_with_same_limits(self):
        output=m.PACKET/'unexecuted-test-output'
        base=copy.deepcopy(OLD);base['output']=str(output)
        base['absent_inputs']=['/synthetic/missing-library',str(output/'02-allocation-ownership/home/preferences')]
        prefix={'original_status':'failed','retained_native_observations':2}
        failure={'original_producer_status':'failed','qualified':False}
        def doc(path,digest,pins):return json.loads(path.read_bytes())
        with patch.object(m.b,'build_plan',return_value=base),patch.object(m.r,'retained_prefix',return_value=prefix),\
             patch.object(m,'retained_allocation_failure',return_value=failure),patch.object(m,'document',side_effect=doc),\
             patch.object(m,'pin'),patch.object(m.b,'preference_paths',return_value=[]):
            result=m.build_plan(output)
        self.assertEqual(result['schedule'],slots())
        self.assertEqual(result['native_commands'],2)
        self.assertEqual(result['retained_prefix'],dict(configuration_and_readback=prefix,failed_allocation=failure))
        self.assertEqual(result['absent_inputs'],['/synthetic/missing-library'])
        self.assertFalse(result['whole_subject_n4_n10_scheduled'])
        self.assertTrue(all(result[k] is False for k in m.FALSE_GATES))
        for slot in result['schedule']:
            self.assertEqual(slot['timeout_seconds'],30)
            self.assertEqual(slot['maximum_process_group_rss_mib'],10240)
            self.assertEqual(slot['argv'][:-1],OLD['schedule'][2]['argv'][:-1])


class PreservedFailure(unittest.TestCase):
    def review(self,fault=None):
        def doc(path,digest,pins):
            value=json.loads(path.read_bytes())
            if path==m.FAILED_RUN/'report.json' and fault:value.update(fault)
            return value
        with patch.object(m,'document',side_effect=doc),patch.object(m,'pin'):
            return m.retained_allocation_failure({})

    def test_saved_allocation_failure_stays_failed_and_unqualified(self):
        result=self.review()
        self.assertEqual(result['original_producer_status'],'failed')
        self.assertEqual(result['original_error'],'Exact bounded APL output mismatch')
        self.assertFalse(result['qualified'])
        self.assertTrue(result['whole_subject_n4_n10_unstarted'])

    def test_failed_record_promotion_or_added_attempt_rejected(self):
        for fault in ({'status':'passed'},{'native_processes_started':2},{'captures':[{}]},
                      {'attempted_commands':['02-allocation-ownership','03-whole-subject-n4']}):
            with self.subTest(fault=fault),self.assertRaises(AssertionError):self.review(fault)


class Closure(unittest.TestCase):
    def fixture(self,output):
        template=m.r.OLD_RUN/'01-workspace-readback'
        inherited=json.loads((template/'process.json').read_bytes())['inherited_lock_descriptor']
        report=dict(status=m.SUCCESS,registered_commands=[],attempted_commands=[],native_processes_started=2,
                    captures=[],validated_artifacts={},inherited_lock_descriptor=inherited)
        schedule=slots()
        for index,slot in enumerate(schedule):
            directory=output/slot['directory'];directory.mkdir();pid=990+index
            begin=f'2026-10-14T23:00:0{index*2}+00:00';end=f'2026-10-14T23:00:0{index*2+1}+00:00'
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
                    record.update(status='native-passed',finished_at=end,
                                  output_validation=m.check_output(slot,raw['stdout'],raw['stderr'],PATTERN))
                    for key in ('error','error_type','timed_out'):record.pop(key,None)
                    for stream,data in raw.items():
                        record[stream+'_bytes']=len(data);record[stream+'_sha256']=hashlib.sha256(data).hexdigest()
                (directory/(name+'.json')).write_text(json.dumps(record))
            for name,data in raw.items():(directory/(name+'.bin')).write_bytes(data)
            capture,snapshot=m.checked_capture(slot,directory,os.getpid(),inherited,PATTERN)
            report['attempted_commands'].append(slot['directory'])
            report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
            report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
        return report,dict(schedule=schedule,absent_inputs=[],configuration_pattern=PATTERN)

    def test_exact_two_captures_close_with_eleven_artifacts_no_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve();report,plan=self.fixture(output)
            with patch.object(m,'verify'),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],m.SUCCESS)
            self.assertEqual(terminal['capture_count'],2)
            self.assertEqual(len(terminal['available_evidence']),11)
            self.assertTrue(all(terminal[k] is False for k in m.FALSE_GATES))

    def test_missing_second_capture_cannot_close_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve();report,plan=self.fixture(output)
            report['captures'].pop();report['validated_artifacts'].pop(plan['schedule'][1]['directory'])
            with patch.object(m,'verify'),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity')
            self.assertIn('Incomplete two-command stage',terminal['integrity_errors'])

    def test_reordered_or_extra_attempt_rejected(self):
        for fault in ('reverse','extra'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary).resolve();report,plan=self.fixture(output)
                if fault=='reverse':report['attempted_commands'].reverse()
                else:report['attempted_commands'].append('02-whole-subject-n4')
                with patch.object(m,'verify'),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')

    def test_late_capture_or_report_mutation_rejected(self):
        for target in ('00-zero-allocation-control/stderr.bin','report.json'):
            with self.subTest(target=target),tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary).resolve();report,plan=self.fixture(output);calls=0
                def verify(*args):
                    nonlocal calls
                    calls+=1
                    if calls==2:(output/target).write_bytes(b'changed')
                with patch.object(m,'verify',side_effect=verify),patch.object(m,'lock_identity'):
                    m.finish(report,plan,output,{}, {},None)
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')
                self.assertTrue(terminal['integrity_errors'])

    def test_first_failure_stops_before_witness_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve()/'new-run'
            plan=dict(output=str(output),pins={},input_resolutions={},absent_inputs=[],retained_prefix={},
                      schedule=slots(),configuration_pattern=PATTERN)
            with patch.object(m,'pin'),patch.object(m,'verify'),patch.object(m,'lock_identity',return_value={'fd':64}),\
                 patch.object(m,'observe',side_effect=AssertionError('zero control failed')) as observer,\
                 patch.object(m,'checked_capture') as capture,patch.object(m,'finish'):
                report=m.run_plan(plan,Path(temporary)/'plan.json','0'*64,None)
            self.assertEqual(observer.call_count,1);capture.assert_not_called()
            self.assertEqual(report['status'],'failed')
            self.assertEqual(report['attempted_commands'],['00-zero-allocation-control'])
            self.assertTrue(all(report[k] is False for k in m.FALSE_GATES))

    def test_second_retained_lease_replacement_detected_after_replay(self):
        first=SimpleNamespace(st_dev=1,st_ino=82370343)
        second=SimpleNamespace(st_dev=1,st_ino=82374025)
        changed=SimpleNamespace(st_dev=1,st_ino=82374026)
        first_lease=SimpleNamespace(fileno=lambda:65);second_lease=SimpleNamespace(fileno=lambda:66)
        old_terminal=json.loads((m.FAILED_RUN/'terminal.json').read_bytes())
        def inventory(path,*args):return old_terminal['available_evidence'] if path==m.FAILED_RUN else {}
        with patch.object(m.r,'_prior_lease',first_lease),patch.object(m,'_failure_lease',second_lease),\
             patch.object(m.r,'verify'),patch.object(m,'inventory',side_effect=inventory),\
             patch.object(m,'_base_lock_identity',return_value={}),\
             patch.object(m.os,'fstat',side_effect=[first,second]),patch.object(Path,'stat',side_effect=[first,changed]):
            with self.assertRaisesRegex(AssertionError,'Retained durable lease changed'):
                m.verify({}, {},[],SimpleNamespace(fileno=lambda:64))


if __name__=='__main__':unittest.main()
