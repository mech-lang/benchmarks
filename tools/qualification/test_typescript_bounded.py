"""Pure TypeScript bounded-controller tests; no native processes, runtime hashes, or preparation."""
import copy
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH=Path(__file__).with_name('typescript_bounded.py')
SPEC=importlib.util.spec_from_file_location('tested_typescript149',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


def digest(raw):return hashlib.sha256(raw).hexdigest()


class TypeScriptBounded(unittest.TestCase):
    def receipt_fixture(self,directory,code=0):
        command=['/synthetic/node','/synthetic/emitted/main.js']
        env=m.environment(directory);payload=b'input';parent=os.getpid()
        common=dict(kind='typescript-bounded-main',command=command,environment=env,cwd=str(directory),
            started_at='2026-10-14T00:00:00+00:00',stdin_bytes=len(payload),stdin_sha256=digest(payload),
            inherited_common_mutex=True,common_mutex_inode=79859134,process_timeout_seconds=30,cleanup_timeout_seconds=5,
            maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,native_file_limit_bytes=m.kb.FILE_LIMIT,
            stdout_capture_limit_bytes=m.kb.FILE_LIMIT+m.kb.PIPE_CHUNK,stdout_transport='OS pipe, retained as received',
            stderr_transport='exclusive artifact',benchmark_samples=0,source_work_qualified=False,chart_admission=False)
        identity=dict(pid=42,pgid=42,ppid=parent,birth_seconds=100,birth_microseconds=3,status=2)
        start=dict(common,status='starting',native_process_started=False)
        active=dict(common,status='running',native_process_started=True,pid=42,pgid=42,identity=identity)
        final=dict(common,status='failed' if code else 'native-passed',native_process_started=True,pid=42,pgid=42,
            identity=identity,leader_identity_before_reap=dict(identity,status=5),direct_child_reaped=True,
            remaining_process_group=[],cleanup_errors=[],stop_signals=[],exit_status=code,
            kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=100,
            finished_at='2026-10-14T00:00:01+00:00')
        if code:final.update(error_type='AssertionError',error='Native command exited unsuccessfully',timed_out=False)
        for name,raw in (('stdout',b''),('stderr',b'rejection' if code else b'')):
            (directory/(name+'.bin')).write_bytes(raw);final[name+'_bytes']=len(raw);final[name+'_sha256']=digest(raw)
        for name,value in (('start',start),('active',active),('process',final)):(directory/(name+'.json')).write_text(json.dumps(value))
        return command,env,payload,parent,'typescript-bounded-main',code

    def test_native_success_and_exact_expected_exit1_envelopes(self):
        for code in (0,1):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,code)
                receipt,stdout,stderr=m.native_receipt(directory,*args)
                self.assertEqual(receipt['exit_status'],code)
                self.assertEqual(receipt['status'],'failed' if code else 'native-passed')

    def test_exit1_unrelated_failure_timeout_signal_and_cleanup_rejected(self):
        changes=[lambda r:r.update(error='Unexpected stderr; raw bytes retained'),lambda r:r.update(error_type='RuntimeError'),
                 lambda r:r.update(exit_status=-15),lambda r:r.update(timed_out=True),lambda r:r.update(stop_signals=[9]),
                 lambda r:r.update(cleanup_errors=['failed']),lambda r:r.update(artifact_errors=['failed']),
                 lambda r:r.update(direct_child_reaped=False),lambda r:r.update(remaining_process_group=[41]),
                 lambda r:r.update(status='native-passed')]
        for change in changes:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,1);path=directory/'process.json'
                value=json.loads(path.read_bytes());change(value);path.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_missing_unowned_or_changed_birth_and_policy_rejected(self):
        changes=[('active',lambda r:r.update(native_process_started=False)),
                 ('process',lambda r:r['identity'].update(ppid=1)),
                 ('process',lambda r:r['leader_identity_before_reap'].update(birth_seconds=999)),
                 ('start',lambda r:r.update(stdin_sha256='0'*64)),('process',lambda r:r.update(exit_status=True)),
                 ('active',lambda r:r['command'].append('--other')),('process',lambda r:r.update(maximum_process_group_rss_bytes=1))]
        for name,change in changes:
            with self.subTest(name=name,change=change),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,1);path=directory/(name+'.json')
                value=json.loads(path.read_bytes());change(value);path.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_raw_stream_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);args=self.receipt_fixture(directory);(directory/'stdout.bin').write_bytes(b'new')
            with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_actual_corpus149_input_and_expected_pins_without_runtime_hash(self):
        pins={};schedule=m.corpus(pins)
        self.assertEqual(len(schedule),149);self.assertEqual(len({s['directory'] for s in schedule}),149)
        self.assertEqual(sum(s['case']['expected_exit']=='nonzero' for s in schedule),7)
        self.assertEqual(set(s['case']['benchmark'] for s in schedule),set(m.c.BENCHES))
        self.assertTrue(all(str(m.CORPUS.parent/s['case']['stdin']['path']) in pins for s in schedule))
        self.assertEqual(pins[str(m.CORPUS)],m.CORPUS_SHA)

    def test_commands_use_direct_emitted_script_and_original_argument_contract(self):
        plan={'compiled':{'node':'/synthetic/node'}};profile={'javascript':{'path':'/emitted/main.js'}}
        directory=Path('/synthetic/case')
        command,env=m.command_for(plan,profile,{'input_kind':'integer-argument','n':0},directory)
        self.assertEqual(command,['/synthetic/node','/emitted/main.js','0'])
        self.assertNotIn('NODE_OPTIONS',env);self.assertNotIn('NODE_PATH',env);self.assertEqual(env['UV_THREADPOOL_SIZE'],'8')
        command,_=m.command_for(plan,profile,{'input_kind':'stdin','n':0},directory)
        self.assertEqual(command,['/synthetic/node','/emitted/main.js'])
        self.assertNotIn('--eval',command);self.assertNotIn('--require',command)

    def test_rejection_contract_is_strict_and_does_not_promote_work(self):
        case=next(s['case'] for s in m.corpus({}) if s['case']['expected_exit']=='nonzero')
        stderr=b'Invalid IUPAC byte: '+str(case['expected_invalid_byte']).encode()+b'\n'
        value=m.check.validate(case,'typescript',b'>r\n',stderr,1,None)
        self.assertTrue(value['output_contract_satisfied']);self.assertFalse(value['source_work_qualified'])
        for stdout,error,code in ((b'',stderr,1),(b'>r\n',stderr+b'extra\n',1),(b'>r\n',stderr,0),(b'>r\n',stderr,-15)):
            with self.assertRaises(ValueError):m.check.validate(case,'typescript',stdout,error,code,None)

    def test_all142_success_reference_contracts(self):
        checked=0
        for slot in m.corpus({}):
            case=slot['case']
            if case['expected_exit']!=0:continue
            expected=(m.CORPUS.parent/case['expected']['path']).read_bytes()
            self.assertTrue(m.check.validate(case,'typescript',expected,b'',0,expected)['output_contract_satisfied']);checked+=1
        self.assertEqual(checked,142)

    def test_actual_closed_compilation_replay_without_runtime_hash(self):
        original=m.sha
        def small_only(path):
            path=Path(path)
            if path in (m.c.NODE,m.kb.kh.PYTHON) or path.name=='tsc':raise AssertionError('Runtime hash attempted')
            return original(path)
        with patch.object(m,'sha',side_effect=small_only):
            pins={};value=m.compiled_prerequisite(m.c.HERE/'run-v1/report.json',m.COMPILED_REPORT_SHA,m.COMPILED_TERMINAL_SHA,pins)
        self.assertEqual(len(value['profiles']),10);self.assertEqual(len(value['artifacts']),159)
        self.assertEqual(value['node'],str(m.c.NODE));self.assertEqual(pins[str(m.c.NODE)],m.c.NODE_SHA)
        self.assertEqual({r['benchmark'] for r in value['profiles']},set(m.c.BENCHES))
        self.assertTrue(all(r['javascript']['path'].endswith('/'+r['benchmark']+'.js') for r in value['profiles']))

    def test_unreviewed_report_terminal_or_wrong_path_rejected(self):
        path=m.c.HERE/'run-v1/report.json'
        for p,r,t in ((path,'0'*64,m.COMPILED_TERMINAL_SHA),(path,m.COMPILED_REPORT_SHA,'0'*64),
                      (path.parent.parent/'different/report.json',m.COMPILED_REPORT_SHA,m.COMPILED_TERMINAL_SHA)):
            with self.assertRaises(AssertionError):m.compiled_prerequisite(p,r,t,{})

    def test_compiled_pin_omission_bad_qualification_or_terminal_inventory_rejected(self):
        original=m.document
        changes=[('report.json',lambda r:r['pins'].pop(str(m.c.NODE))),
                 ('report.json',lambda r:r.update(required_work_qualified=True)),
                 ('terminal.json',lambda r:r.update(common_mutex_held=False)),
                 ('terminal.json',lambda r:r['available_evidence'].pop('compile/project/emitted/binarytrees.js')),
                 ('report.json',lambda r:r.update(api_child_start_unconfirmed=True))]
        for suffix,change in changes:
            def altered(path,digest,pins):
                value=original(path,digest,pins)
                if Path(path)==m.c.HERE/'run-v1'/suffix:change(value)
                return value
            with self.subTest(suffix=suffix,change=change),patch.object(m,'document',side_effect=altered):
                with self.assertRaises(AssertionError):m.compiled_prerequisite(m.c.HERE/'run-v1/report.json',m.COMPILED_REPORT_SHA,m.COMPILED_TERMINAL_SHA,{})

    def test_bounded_plan_preserves_all149_slots_and_null_unrelated_qualification(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'PACKET',Path(tmp).resolve()):
            packet=Path(tmp).resolve();(packet/'README.md').write_text('fixture')
            plan=m.build_plan(packet/'fresh',m.c.HERE/'run-v1/report.json',m.COMPILED_REPORT_SHA,m.COMPILED_TERMINAL_SHA)
        self.assertEqual(plan['native_processes'],149);self.assertEqual(plan['runtime_flags'],[])
        self.assertEqual(plan['compiler_invocations'],0);self.assertFalse(plan['bounded_outputs_qualified'])
        self.assertFalse(plan['runtime_dependency_closure_qualified']);self.assertFalse(plan['chart_admission'])
        self.assertIsNone(plan['canonical_loc']);self.assertTrue(all(s['id']=='typescript-'+s['case']['benchmark']+'-v1' for s in plan['schedule']))

    def final_fixture(self,directory):
        output=directory/'bounded';output.mkdir();compiled=directory/'compiled';compiled.mkdir()
        prerequisite=directory/'pin';prerequisite.write_text('retained')
        stage=output/'001-one';stage.mkdir()
        receipt=dict(pid=42,pgid=42,native_process_started=True,direct_child_reaped=True,remaining_process_group=[],cleanup_errors=[])
        (stage/'process.json').write_text(json.dumps(receipt));(stage/'terminal.json').write_text('{}')
        report=dict(status='failed',native_processes_started=1,registered_commands=[dict(slot=1,directory=stage.name,pid=42)],
            qualified_cases=1,cases=[],successful_cases=1,rejected_cases=0,bounded_outputs_qualified=False,
            validated_case_artifacts={stage.name:m.inventory(stage)})
        plan=dict(schedule=[dict(slot=1,directory=stage.name)],compiled=dict(report=str(compiled/'report.json'),artifacts={}))
        return report,plan,output,{str(prerequisite):m.sha(prerequisite)}

    def test_final_closure_retains_partial_failure_without_rewriting_receipt(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'),patch.object(m.kb.kh,'verify_lock'):
            report,plan,output,pins=self.final_fixture(Path(tmp));before=(output/'001-one/process.json').read_bytes()
            m.finish(report,plan,output,pins,object());terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed');self.assertFalse(terminal['bounded_outputs_qualified'])
            self.assertEqual(terminal['integrity_errors'],[]);self.assertEqual(before,(output/'001-one/process.json').read_bytes())
            self.assertIn('001-one/terminal.json',terminal['available_evidence'])

    def test_snapshot_late_mutation_and_pin_change_fail_closed(self):
        for fault in ('stage-before','stage-during','pin-after'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'),patch.object(m.kb.kh,'verify_lock'):
                report,plan,output,pins=self.final_fixture(Path(tmp));path=output/'001-one/terminal.json'
                if fault=='stage-before':path.write_text('{"changed":true}')
                original=m.inventory;calls=0
                def inject(directory,exclude=()):
                    nonlocal calls
                    value=original(directory,exclude);calls+=1
                    if fault=='stage-during' and calls==1:path.write_text('{"changed":true}')
                    if fault=='pin-after' and calls==2:Path(next(iter(pins))).write_text('changed')
                    return value
                with patch.object(m,'inventory',side_effect=inject):m.finish(report,plan,output,pins,object())
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertTrue(terminal['integrity_errors'])

    def test_unreaped_native_or_changed_mutex_cannot_claim_success(self):
        for fault in ('unreaped','mutex'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'):
                report,plan,output,pins=self.final_fixture(Path(tmp))
                if fault=='unreaped':
                    path=output/'001-one/process.json';r=json.loads(path.read_bytes());r['direct_child_reaped']=False;path.write_text(json.dumps(r))
                with patch.object(m.kb.kh,'verify_lock',side_effect=AssertionError('wrong mutex') if fault=='mutex' else None):
                    m.finish(report,plan,output,pins,object())
                terminal=json.loads((output/'terminal.json').read_bytes());self.assertEqual(terminal['status'],'failed-integrity')
                if fault=='mutex':self.assertFalse(terminal['common_mutex_held'])

    def test_fifo_and_symlink_artifacts_rejected_without_opening(self):
        for kind in ('fifo','symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp);path=output/'unexpected'
                if kind=='fifo':os.mkfifo(path)
                else:path.symlink_to(output)
                with self.assertRaises(AssertionError):m.inventory(output)

    def test_plan_pin_conflicts_and_nonphysical_paths_rejected(self):
        with self.assertRaises(AssertionError):m.bind({},'relative','0'*64)
        pins={};m.bind(pins,'/synthetic/one','0'*64)
        with self.assertRaises(AssertionError):m.bind(pins,'/synthetic/one','1'*64)
        with self.assertRaises(AssertionError):m.bind(pins,'/synthetic/two','bad')

    def test_signals_enter_owned_supervisor_cleanup(self):
        handlers={}
        def run(args):
            self.assertEqual(set(handlers),m.kb.kh.SIGNALS)
            for sig,handler in handlers.items():
                with self.assertRaises(KeyboardInterrupt):handler(sig,None)
            return 19
        with patch.object(m.sys,'argv',['stage','run','--plan','/synthetic/plan','--plan-sha256','0'*64]),\
             patch.object(m.signal,'signal',side_effect=lambda sig,handler:handlers.__setitem__(sig,handler)),\
             patch.object(m,'run',side_effect=run):self.assertEqual(m.main(),19)


if __name__=='__main__':unittest.main()
