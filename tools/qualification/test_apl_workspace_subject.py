"""Small source/receipt faults for N4/N10; no native or full-pin execution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


m=load('apl_subject_tested',Path(__file__).with_name('apl_workspace_subject.py'))
t=load('apl_scoped_fixture_only',Path(__file__).with_name('test_apl_workspace_scoped.py'))
OLD=json.loads((m.ORIGINAL/'plan-v1.json').read_bytes())
PATTERN=OLD['configuration_pattern']


def slots():return copy.deepcopy(OLD['schedule'][3:])


class Policy(unittest.TestCase):
    def test_only_exact_original_subject_outputs_and_diagnostic(self):
        for slot in slots():
            raw=slot['expected_stdout_utf8'].encode()
            self.assertTrue(m.check_output(slot,raw,m.WARNING,PATTERN)['exact_output'])
            for stdout,stderr in ((raw+b'x',m.WARNING),(raw,b''),(raw,m.WARNING+b'WS FULL+\n')):
                with self.subTest(slot=slot['id']),self.assertRaises(AssertionError):
                    m.check_output(slot,stdout,stderr,PATTERN)
            altered=dict(slot,expected_stdout_utf8='different\n')
            with self.assertRaisesRegex(AssertionError,'Retained subject oracle changed'):
                m.check_output(altered,b'different\n',m.WARNING,PATTERN)

    def test_plan_reuses_only_original_n4_n10(self):
        output=m.PACKET/'unexecuted-test-output';base=copy.deepcopy(OLD);base['output']=str(output)
        base['absent_inputs']=[str(output/name/'home/preferences') for name in
            ('00-configuration','01-workspace-readback','02-allocation-ownership','03-whole-subject-n4','04-whole-subject-n10')]
        with patch.object(m.b,'build_plan',return_value=base),patch.object(m.r,'retained_prefix',return_value={}),\
             patch.object(m.s,'retained_allocation_failure',return_value={}),\
             patch.object(m,'retained_scoped_success',return_value={'exact_bounded_outputs_verified':True}),patch.object(m,'pin'):
            plan=m.build_plan(output)
        self.assertEqual(plan['schedule'],slots())
        self.assertEqual(plan['native_commands'],2)
        self.assertEqual([slot['timeout_seconds'] for slot in plan['schedule']],[30,60])
        self.assertEqual(len(plan['absent_inputs']),2)
        self.assertFalse(plan['full_size_timing_scheduled'])
        self.assertTrue(all(plan[key] is False for key in m.FALSE_GATES))


class Prerequisites(unittest.TestCase):
    def intake(self,report_fault=None,review_fault=None):
        def document(path,digest,pins):
            value=json.loads(path.read_bytes())
            if path==m.SCOPED_RUN/'report.json' and report_fault:value.update(report_fault)
            if path==m.OWNERSHIP_REVIEW and review_fault:value.update(review_fault)
            return value
        with patch.object(m,'document',side_effect=document),patch.object(m,'pin'):
            return m.retained_scoped_success({})

    def test_both_actual_scoped_captures_and_independent_disposition_required(self):
        result=self.intake()
        self.assertEqual([c['id'] for c in result['captures']],list(m.s.IDS))
        self.assertTrue(result['exact_bounded_outputs_verified'])
        self.assertEqual(result['bounded_ownership_review']['sha256'],m.OWNERSHIP_REVIEW_SHA)
        self.assertTrue(all(result[key] is False for key in m.FALSE_GATES))

    def test_failed_incomplete_or_promoted_scoped_report_rejected(self):
        for fault in ({'status':'failed'},{'captures':[]},{'native_processes_started':1},{'full_timing_qualified':True}):
            with self.subTest(fault=fault),self.assertRaises(AssertionError):self.intake(report_fault=fault)

    def test_unqualified_or_changed_bounded_disposition_rejected(self):
        for fault in ({'bounded_allocation_ownership_qualified':False},{'allocation_deltas':[1,2,9,4,2,1]},
                      {'control_deltas':[1,0,0,0,0,0]},{'full_timing_qualified':True}):
            with self.subTest(fault=fault),self.assertRaises(AssertionError):self.intake(review_fault=fault)


class Closure(unittest.TestCase):
    def fixture(self,output):
        # Reuse the previously reviewed synthetic receipt builder, privately.
        with patch.object(t,'m',m),patch.object(t,'slots',side_effect=slots):
            return t.Closure().fixture(output)

    def test_two_subject_captures_close_without_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve();report,plan=self.fixture(output)
            with patch.object(m,'verify'),patch.object(m,'lock_identity'):m.finish(report,plan,output,{}, {},None)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],m.SUCCESS)
            self.assertEqual(terminal['capture_count'],2)
            self.assertEqual(len(terminal['available_evidence']),11)
            self.assertTrue(all(terminal[key] is False for key in m.FALSE_GATES))

    def test_late_output_or_report_change_rejected(self):
        for target in ('03-whole-subject-n4/stdout.bin','report.json'):
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

    def test_first_subject_failure_does_not_launch_n10(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary).resolve()/'new-run'
            plan=dict(output=str(output),pins={},input_resolutions={},absent_inputs=[],retained_prefix={},
                      schedule=slots(),configuration_pattern=PATTERN)
            with patch.object(m,'pin'),patch.object(m,'verify'),patch.object(m,'lock_identity',return_value={'fd':64}),\
                 patch.object(m,'observe',side_effect=AssertionError('N4 failed')) as observer,\
                 patch.object(m,'checked_capture') as capture,patch.object(m,'finish'):
                report=m.run_plan(plan,Path(temporary)/'plan.json','0'*64,None)
            self.assertEqual(observer.call_count,1);capture.assert_not_called()
            self.assertEqual(report['status'],'failed')
            self.assertEqual(report['attempted_commands'],['03-whole-subject-n4'])

    def test_newest_retained_lease_replacement_detected_after_replay(self):
        original=SimpleNamespace(st_dev=1,st_ino=82382998)
        changed=SimpleNamespace(st_dev=1,st_ino=82382999)
        terminal=json.loads((m.SCOPED_RUN/'terminal.json').read_bytes())
        def inventory(path,*args):return terminal['available_evidence'] if path==m.SCOPED_RUN else {}
        with patch.object(m,'_scoped_lease',SimpleNamespace(fileno=lambda:67)),patch.object(m.s,'verify'),\
             patch.object(m,'inventory',side_effect=inventory),patch.object(m,'_prior_lock_identity',return_value={}),\
             patch.object(m.os,'fstat',return_value=original),patch.object(Path,'stat',return_value=changed):
            with self.assertRaisesRegex(AssertionError,'Scoped diagnostic durable lease changed'):
                m.verify({}, {},[],SimpleNamespace(fileno=lambda:64))


if __name__=='__main__':unittest.main()
