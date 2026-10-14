"""Synthetic remaining-capture checks; no LLVM, Julia, prepare or runtime hashes."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('julia_native_inspection_remaining.py')
S=importlib.util.spec_from_file_location('julia_remaining_tested',P)
m=importlib.util.module_from_spec(S); S.loader.exec_module(m)


def receipt(directory, slot, zombie=False, peak=1024):
    directory.mkdir(exist_ok=True)
    start=dict(status='starting',kind=m.j.KIND,command=slot['command'],environment=m.j.environment(directory),
        cwd=str(directory),started_at='2026-10-14T00:00:00+00:00',process_timeout_seconds=30,cleanup_timeout_seconds=5,
        inherited_common_mutex=True,common_mutex_inode=79859134,native_process_started=False,stop_signals=[],
        cleanup_errors=[],benchmark_samples=0,stdin_bytes=0,stdin_sha256=m.j.EMPTY_SHA,
        observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0,maximum_process_group_rss_bytes=2*1024**3,
        native_file_limit_bytes=64*1024**2,stdout_capture_limit_bytes=64*1024**2+m.kb.PIPE_CHUNK,
        stdout_transport='OS pipe, retained as received',stderr_transport='exclusive artifact',
        source_work_qualified=False,chart_admission=False)
    identity=dict(pid=42,pgid=42,ppid=os.getpid(),birth_seconds=123,birth_microseconds=456,status=5 if zombie else 2)
    active=dict(start,status='running',pid=42,pgid=42,native_process_started=True,identity=identity)
    final=dict(active,status='native-passed',leader_identity_before_reap=dict(identity,status=5),
        remaining_process_group=[],exit_status=0,direct_child_reaped=True,kernel_monitor_samples=3,
        observed_peak_process_group_rss_bytes=peak,finished_at='2026-10-14T00:00:01+00:00')
    for name,raw in [('stdout',b'arm64 disassembly fixture\n'),('stderr',b'')]:
        (directory/(name+'.bin')).write_bytes(raw)
        final[name+'_bytes']=len(raw); final[name+'_sha256']=hashlib.sha256(raw).hexdigest()
    for name,value in [('start',start),('active',active),('process',final)]:
        (directory/(name+'.json')).write_text(json.dumps(value))
    return final


class Captures(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        self.slot=dict(id='native-archive',directory='09-native-archive',command=['/exact/llvm-objdump','--disassemble'])
        self.directory=self.root/self.slot['directory']

    def check(self):
        return m.checked_capture(self.slot,self.directory,os.getpid())

    def mutate(self, **fields):
        p=self.directory/'process.json'; value=json.loads(p.read_bytes()); value.update(fields)
        p.write_text(json.dumps(value))

    def test_valid_fast_exit_has_null_peak_and_preserved_raw_zero(self):
        receipt(self.directory,self.slot,zombie=True,peak=0)
        original=(self.directory/'process.json').read_bytes()
        result,_=self.check()
        self.assertIsNone(result['observed_peak_process_group_rss_bytes'])
        self.assertEqual(result['raw_observed_peak_process_group_rss_bytes'],0)
        self.assertFalse(result['live_rss_observation_obtained'])
        self.assertFalse(result['rss_observation_complete'])
        self.assertFalse(result['memory_usage_qualified'])
        self.assertEqual((self.directory/'process.json').read_bytes(),original)

    def test_positive_sample_keeps_limit_and_incomplete_memory_scope(self):
        receipt(self.directory,self.slot,peak=1024)
        result,_=self.check()
        self.assertEqual(result['observed_peak_process_group_rss_bytes'],1024)
        self.assertTrue(result['live_rss_observation_obtained'])
        self.assertFalse(result['rss_observation_complete'])
        self.assertFalse(result['memory_usage_qualified'])
        self.assertEqual(m.kb.RSS_LIMIT,2*1024**3)

    def test_ambiguous_zero_after_live_registration_rejected(self):
        receipt(self.directory,self.slot,peak=0)
        with self.assertRaisesRegex(AssertionError,'already-exited'): self.check()

    def test_zero_with_claimed_live_observation_rejected(self):
        receipt(self.directory,self.slot,zombie=True,peak=0)
        self.mutate(live_rss_observation_obtained=True)
        with self.assertRaisesRegex(AssertionError,'conflicts'): self.check()

    def test_missing_or_changed_identity_rejected(self):
        final=receipt(self.directory,self.slot,zombie=True,peak=0)
        for bad in (None,dict(final['identity'],birth_microseconds=789),dict(final['identity'],ppid=1)):
            with self.subTest(identity=bad):
                self.mutate(identity=bad)
                with self.assertRaises((AssertionError,TypeError)): self.check()

    def test_dirty_group_and_unreaped_child_rejected(self):
        for fields in ({'remaining_process_group':[{'pid':43}]},{'remaining_after_cleanup':[{'pid':43}]},
                       {'direct_child_reaped':False},{'cleanup_errors':['error']},{'stop_signals':[9]}):
            with self.subTest(fields=fields):
                receipt(self.directory,self.slot,zombie=True,peak=0); self.mutate(**fields)
                with self.assertRaises(AssertionError): self.check()

    def test_oversized_negative_or_nonnumeric_observed_peak_rejected(self):
        for peak in (2*1024**3+1,-1,None,True,0.0):
            with self.subTest(peak=peak):
                receipt(self.directory,self.slot,zombie=True,peak=peak)
                with self.assertRaises(AssertionError): self.check()

    def test_failed_exit_and_missing_monitor_observation_rejected(self):
        for fields in ({'exit_status':1},{'kernel_monitor_samples':0},{'error':'failed'},
                       {'status':'failed'},{'timed_out':True}):
            with self.subTest(fields=fields):
                receipt(self.directory,self.slot,zombie=True,peak=0); self.mutate(**fields)
                with self.assertRaises(AssertionError): self.check()

    def test_changed_output_or_unexpected_stderr_rejected(self):
        receipt(self.directory,self.slot,zombie=True,peak=0)
        (self.directory/'stdout.bin').write_bytes(b'changed')
        with self.assertRaises(AssertionError): self.check()
        receipt(self.directory,self.slot,zombie=True,peak=0)
        (self.directory/'stderr.bin').write_bytes(b'warning')
        self.mutate(stderr_bytes=7,stderr_sha256=hashlib.sha256(b'warning').hexdigest())
        with self.assertRaisesRegex(AssertionError,'stderr'): self.check()

    def test_new_artifact_rejected(self):
        receipt(self.directory,self.slot,zombie=True,peak=0)
        (self.directory/'unexpected').write_bytes(b'')
        with self.assertRaisesRegex(AssertionError,'Unexpected native files'): self.check()


class PlanAndClosure(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()

    def test_only_original_last_two_commands_are_scheduled(self):
        schedule=[dict(id=f'decode-{n:02}',directory=f'{n:02}-decode-{n:02}',command=['/llvm-dis',str(n)]) for n in range(9)]
        schedule += [dict(id=n,directory=f'{i}-'+n,command=['/llvm-objdump',n])
                     for i,n in [(9,'native-archive'),(10,'final-executable')]]
        old=dict(output='/old',commands=[{'cwd':'/old/'+s['directory']} for s in schedule],
                 pins={},input_resolutions={},schedule=schedule,native_commands=11)
        base=copy.deepcopy(old); base['output']=str(self.root/'new')
        base['commands']=[{'cwd':str(self.root/'new'/s['directory'])} for s in schedule]
        with patch.object(m.j,'build_plan',return_value=base),patch.object(m,'prior_evidence',return_value=(old,{})),\
             patch.object(m.j,'pin'),patch.object(m.j,'sha',return_value='a'*64):
            plan=m.build_plan(self.root/'new')
        self.assertEqual(plan['schedule'],schedule[9:])
        self.assertEqual(plan['native_commands'],2)
        self.assertEqual(plan['remaining_original_slots'],[9,10])
        self.assertFalse(plan['memory_usage_qualified'])

    def test_changed_reconstructed_original_command_rejected(self):
        old=dict(output='/old',commands=[],pins={},input_resolutions={},schedule=['original'])
        base=dict(old,output='/new',schedule=['changed'])
        with patch.object(m.j,'build_plan',return_value=base),patch.object(m,'prior_evidence',return_value=(old,{})):
            with self.assertRaisesRegex(AssertionError,'reconstruction'): m.build_plan(self.root/'new')

    def test_prior_inventory_change_or_new_objdump_directory_rejected(self):
        plan={'tool_closure':{'unavailable_candidates':[]},'preserved_prior_stage':{'artifacts':{'a':1}}}
        with patch.object(m.j,'verify'),patch.object(m.j,'inventory',return_value={'a':2}):
            with self.assertRaisesRegex(AssertionError,'inventory changed'): m.verify({}, {}, plan)
        with patch.object(m.j,'verify'),patch.object(m.j,'inventory',return_value={'a':1}),\
             patch.object(m.os.path,'lexists',return_value=True):
            with self.assertRaisesRegex(AssertionError,'new command'): m.verify({}, {}, plan)

    def failed_report(self):
        return dict(status='failed',registered_commands=[],attempted_commands=[],native_processes_started=0,
                    captures=[],validated_artifacts={})

    def test_final_report_mutation_during_input_replay_rejected(self):
        report=self.failed_report(); calls=0
        def verify(*args):
            nonlocal calls
            calls+=1
            if calls == 2: (self.root/'report.json').write_text('{}\n')
        with patch.object(m,'verify',side_effect=verify),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,{'schedule':[]},self.root,{}, {},object())
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],'failed-integrity')
        self.assertEqual(terminal['available_evidence'],{})

    def test_report_write_mutation_rejected(self):
        report=self.failed_report()
        def save(path,value): path.write_text('{}\n')
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock'),patch.object(m.kb,'save',side_effect=save):
            m.finish(report,{'schedule':[]},self.root,{}, {},object())
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],'failed-integrity')

    def test_last_named_lock_failure_cannot_claim_held(self):
        report=self.failed_report()
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock',side_effect=[None,AssertionError('lock changed')]):
            m.finish(report,{'schedule':[]},self.root,{}, {},object())
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],'failed-integrity')
        self.assertFalse(terminal['common_mutex_held'])


if __name__ == '__main__':
    unittest.main()
