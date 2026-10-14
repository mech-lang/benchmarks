#!/usr/bin/env python3
"""Small synthetic dispatcher tests; no subprocesses, runtime pins or preflight."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).with_name('kotlin_dispatch.py')
spec = importlib.util.spec_from_file_location('dispatch_review', SOURCE)
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        paths = dict(ROOT=self.root, CONTROLLER=self.root/'controller.py',
            PROLOG_PLAN=self.root/'prolog/plan.json', PROLOG_JOB=self.root/'prolog/job',
            COHORT=self.root/'cohort.lock', LOCK=self.root/'timing.lock',
            PLAN=self.root/'bounded/plan-v1.json', OUTPUT=self.root/'bounded/run-v1')
        for key, value in paths.items(): self.stack.enter_context(patch.object(d,key,value))
        d.PROLOG_JOB.mkdir(parents=True)
        for path in (d.PROLOG_JOB/'owner.lock', d.COHORT, d.LOCK): path.write_bytes(b'')
        d.CONTROLLER.write_bytes(b'frozen-controller')
        self.stack.enter_context(patch.object(d,'CONTROLLER_SHA',d.digest(d.CONTROLLER.read_bytes())))
        python=self.root/'python';python.write_bytes(b'pinned-interpreter')
        self.stack.enter_context(patch.object(d,'PYTHON',python))
        self.stack.enter_context(patch.object(d,'PYTHON_SHA',d.digest(python.read_bytes())))
        self.stack.enter_context(patch.object(d,'LOCK_INODE',d.LOCK.stat().st_ino))
        self.receipt = self.root/'experiments/kotlin/dispatch-v1/receipt.json'
        self.args = SimpleNamespace(receipt=self.receipt, dispatcher_sha256=d.digest(SOURCE.read_bytes()))
        self.events = []
        self.flock = self.stack.enter_context(patch.object(d.fcntl,'flock',side_effect=self.locked))
        self.closure = self.stack.enter_context(patch.object(d,'prolog_closed',side_effect=self.closed))
        self.module = SimpleNamespace(kh=SimpleNamespace(verify_lock=Mock()),
            prepare=Mock(side_effect=self.prepare),run=Mock(side_effect=self.stage_run))
        self.loader = self.stack.enter_context(patch.object(d,'load_controller',return_value=self.module))

    def locked(self, fd, flags):
        self.assertEqual(flags,d.fcntl.LOCK_EX)
        self.events.append('lock')

    def closed(self, pins):
        self.assertEqual(self.events,['lock','lock'])
        self.events.append('closure')
        return dict(status='complete',measurement_qualification_inferred=False)

    def prepare(self,args):
        self.assertEqual(self.events,['lock','lock','closure','lock'])
        self.events.append('prepare')
        rows = [dict(id='profile-'+str(i), bounded_cases=[dict(case='case-'+str(j))
                for j in range(8 if i<16 else 7)]) for i in range(20)]
        write(args.plan,dict(controller_sha256=d.CONTROLLER_SHA,output=str(args.output),profiles=rows))

    def stage_run(self,args,lock):
        self.assertEqual(self.events[-1],'prepare')
        self.assertFalse(lock.closed)
        self.assertIs(lock,self.flock.call_args_list[-1].args[0])
        self.assertTrue(all(not call.args[0].closed for call in self.flock.call_args_list))
        self.assertEqual(d.lease_identity(d.LOCK,lock)[1],d.LOCK_INODE)
        self.events.append('run')
        plan=json.loads(args.plan.read_bytes()); rows=plan['profiles']
        counts=dict(native_processes_started=157,diagnostic_compiler_processes_started=1,
            bounded_jvm_processes_started=156,qualified_bounded_cases=156,
            observed_subject_main_invocations=156,observed_subject_main_returns=156)
        common=dict(status=d.COMPLETE,integrity_errors=[],process_receipt_errors=[],artifact_errors=[],
            source_work_qualified=False,chart_admission=False,full_timings_qualified=False,
            canonical_loc=None,formatted_loc=None,**counts)
        report=dict(common,schema='kotlin-retained-classes-bounded-results-v1',bounded_outputs_qualified=True,
            active=None,plan=str(d.PLAN),plan_sha256=args.plan_sha256,profiles=[r['id'] for r in rows],
            cases=[dict(id=r['id'],case=c['case'],status='bounded-output-passed') for r in rows for c in r['bounded_cases']])
        write(d.OUTPUT/'report.json',report)
        write(d.OUTPUT/'terminal.json',dict(common,report_sha256=d.digest((d.OUTPUT/'report.json').read_bytes()),
            common_mutex_held=True,common_mutex_inode=d.LOCK_INODE))

    def receipt_value(self): return json.loads(self.receipt.read_bytes())

    def test_lock_order_and_same_descriptor_cover_prepare_and_run(self):
        d.dispatch(self.args)
        self.assertEqual(self.events,['lock','lock','closure','lock','prepare','run'])
        result=self.receipt_value()
        self.assertTrue(result['bounded_stage_completed'])
        self.assertFalse(result['qualification_granted'])
        self.assertEqual(len(result['held_leases']),3)
        self.assertEqual(result['stage_result'],result['validated_stage_result'])
        self.module.prepare.assert_called_once(); self.module.run.assert_called_once()

    def test_missing_prolog_terminal_never_prepares_or_takes_common_lock(self):
        self.closure.side_effect=FileNotFoundError('terminal.json')
        with self.assertRaises(FileNotFoundError): d.dispatch(self.args)
        self.assertEqual(self.flock.call_count,2)
        self.module.prepare.assert_not_called(); self.module.run.assert_not_called()
        self.assertFalse(self.receipt_value()['run_called'])

    def test_wait_interrupt_is_terminal_without_stage_start(self):
        self.flock.side_effect=KeyboardInterrupt('stop')
        with self.assertRaises(KeyboardInterrupt): d.dispatch(self.args)
        self.module.prepare.assert_not_called()
        self.assertEqual(self.receipt_value()['error_type'],'KeyboardInterrupt')

    def test_replaced_mutex_rejected_after_wait(self):
        original=self.locked
        def replaced(fd,flags):
            original(fd,flags)
            if self.flock.call_count==3:
                d.LOCK.rename(d.LOCK.with_suffix('.old')); d.LOCK.write_bytes(b'')
        self.flock.side_effect=replaced
        with self.assertRaisesRegex(ValueError,'Lease replaced'): d.dispatch(self.args)
        self.module.prepare.assert_not_called()

    def test_source_mutation_while_waiting_blocks_prepare(self):
        original=self.locked
        def changed(fd,flags):
            original(fd,flags)
            if self.flock.call_count==3: d.CONTROLLER.write_bytes(b'changed')
        self.flock.side_effect=changed
        with self.assertRaises(ValueError): d.dispatch(self.args)
        self.module.prepare.assert_not_called()
        self.assertFalse(self.receipt_value()['bounded_stage_completed'])

    def test_wrong_dispatcher_hash_rejected_before_wait(self):
        self.args.dispatcher_sha256='0'*64
        with self.assertRaises(ValueError): d.dispatch(self.args)
        self.flock.assert_not_called()

    def test_wrong_interpreter_bytes_rejected_before_prepare(self):
        d.PYTHON.write_bytes(b'changed-interpreter')
        with self.assertRaises(ValueError):d.dispatch(self.args)
        self.module.prepare.assert_not_called()

    def test_stage_failure_is_preserved_and_never_retried(self):
        def failed(args,lock):
            write(d.OUTPUT/'report.json',dict(status='failed',native_processes_started=3))
            raise RuntimeError('native failure')
        self.module.run.side_effect=failed
        with self.assertRaisesRegex(RuntimeError,'native failure'): d.dispatch(self.args)
        self.module.run.assert_called_once()
        result=self.receipt_value()
        self.assertEqual(result['stage_result']['native_processes_started'],3)
        self.assertFalse(result['bounded_stage_completed'])

    def test_zero_return_with_incomplete_result_fails(self):
        def incomplete(args,lock):
            self.stage_run(args,lock)
            value=json.loads((d.OUTPUT/'report.json').read_bytes()); value['qualified_bounded_cases']=155
            write(d.OUTPUT/'report.json',value)
            terminal=json.loads((d.OUTPUT/'terminal.json').read_bytes())
            terminal.update(qualified_bounded_cases=155,report_sha256=d.digest((d.OUTPUT/'report.json').read_bytes()))
            write(d.OUTPUT/'terminal.json',terminal)
        self.module.run.side_effect=incomplete
        with self.assertRaisesRegex(ValueError,'Incomplete bounded count'): d.dispatch(self.args)
        self.assertFalse(self.receipt_value()['bounded_stage_completed'])

    def test_mutated_completed_terminal_cannot_receive_success_receipt(self):
        complete=d.completed
        def mutation(sha):
            result=complete(sha)
            with (d.OUTPUT/'terminal.json').open('a') as stream: stream.write(' ')
            return result
        with patch.object(d,'completed',side_effect=mutation):
            with self.assertRaisesRegex(ValueError,'finalization integrity'): d.dispatch(self.args)
        self.assertFalse(self.receipt_value()['bounded_stage_completed'])

    def test_existing_output_is_never_reused(self):
        d.OUTPUT.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'Fresh'): d.dispatch(self.args)
        self.flock.assert_not_called()

    def test_preparation_failure_never_runs(self):
        self.module.prepare.side_effect=ValueError('preparation failed')
        with self.assertRaisesRegex(ValueError,'preparation failed'): d.dispatch(self.args)
        self.module.prepare.assert_called_once(); self.module.run.assert_not_called()


class PrologClosureTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack(); self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        for key,path in dict(ROOT=self.root,PROLOG_PLAN=self.root/'plan.json',PROLOG_JOB=self.root/'job').items():
            self.stack.enter_context(patch.object(d,key,path))
        self.output=self.root/'results'
        plan=dict(repository=str(self.root),controller=str(self.root/'prolog_full.py'),output=str(self.output))
        write(d.PROLOG_PLAN,plan)
        self.stack.enter_context(patch.object(d,'PROLOG_PLAN_SHA',d.digest(d.PROLOG_PLAN.read_bytes())))
        command=[str(d.PYTHON),'-I','-S','-B','-u',plan['controller'],'run','--plan',str(d.PROLOG_PLAN),'--plan-sha256',d.PROLOG_PLAN_SHA]
        base=dict(command=command,cwd=str(self.root),automatic_retry=False,qualification_granted=False)
        identity=dict(pid=42,listing='42 original process')
        started=dict(base,command_pid=42,command_identity=identity,command_identity_observation_missing=False)
        docs=dict(request=dict(base,schema_version=1,common_mutex_owned_by_target_command=True),launch=base,
            **{'worker-started':dict(base,inherited_private_lease=True,detached_session=True,common_mutex_owned_by_target_command=True),
               'command-started':started},
            terminal=dict(started,status='command-exited-zero-awaiting-report-review',exit_code=0,
                actual_command_started=True,stop_signals=[]))
        for name,value in docs.items():write(d.PROLOG_JOB/(name+'.json'),value)
        report=dict(status='complete',active=None,plan=str(d.PROLOG_PLAN),plan_sha256=d.PROLOG_PLAN_SHA,
            pins_unchanged_at_end=True,native_launch_unconfirmed_attempts=[],attempts=[{}]*90,
            skipped_failed_profile_slots=[],completed_benchmarks=list(range(10)),benchmark_order=list(range(10)),
            full_performance_runs=90,supervisor=dict(pid=42))
        write(self.output/'report.json',report)
        write(self.output/'terminal.json',dict(status='complete',report=str(self.output/'report.json'),
            report_sha256=d.digest((self.output/'report.json').read_bytes()),common_mutex_held=True,
            integrity_errors=[],native_launch_unconfirmed_attempts=[],full_performance_runs=90,saved_attempts=90))

    def test_closed_metadata_is_bound_without_claiming_measurement_qualification(self):
        pins={}; result=d.prolog_closed(pins)
        self.assertEqual(len(pins),8)
        self.assertFalse(result['measurement_qualification_inferred'])

    def test_missing_terminal_fails_closed(self):
        (d.PROLOG_JOB/'terminal.json').unlink()
        with self.assertRaises(FileNotFoundError): d.prolog_closed({})

    def test_running_or_unbound_report_fails_closed(self):
        report=json.loads((self.output/'report.json').read_bytes());report['status']='running'
        write(self.output/'report.json',report)
        with self.assertRaises(ValueError): d.prolog_closed({})

    def test_failed_durable_command_fails_closed(self):
        terminal=json.loads((d.PROLOG_JOB/'terminal.json').read_bytes());terminal['exit_code']=1
        write(d.PROLOG_JOB/'terminal.json',terminal)
        with self.assertRaises(ValueError):d.prolog_closed({})


if __name__=='__main__':unittest.main()
