"""Synthetic artifact/receipt faults; no BEAM process or runtime preflight."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('elixir_work_test_subject', Path(__file__).with_name('elixir_work.py'))
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
SHA = '1'*64


def write(path, value):
    path.write_text(json.dumps(value))


def output_validation(benchmark, actual, expected):
    if actual != expected: raise ValueError('Synthetic output mismatch')
    return dict(reference_match=True, bytes=len(actual), sha256=hashlib.sha256(actual).hexdigest())


SUPERVISOR = SimpleNamespace(TIMEOUT=30, CLEANUP_TIMEOUT=5, RSS_LIMIT=2*1024**3,
    FILE_LIMIT=8*1024**2, PIPE_CHUNK=65536, eb=SimpleNamespace(output_validation=output_validation),
    kh=SimpleNamespace(verify_lock=lambda lock: None))


def fixture(root):
    output=root/'results';output.mkdir();references=root/'references';references.mkdir()
    plan=dict(profiles=[])
    report=dict(status=work.COMPLETE,profiles=[],native_process_ids=[],native_processes_started=20,
        diagnostic_mains_observed=20,native_launch_requests=20,controller_pid=500,active=None,
        validated_profile_artifacts={},integrity_errors=[],**work.UNQUALIFIED)
    for index,(benchmark,variant) in enumerate((b,v) for b in work.CASE for v in ('compact','optimized')):
        identity='elixir-'+benchmark+'-'+variant;directory=output/identity;directory.mkdir()
        for name in ('home','config','tmp'):(directory/name).mkdir()
        expected=references/(identity+'.stdout');expected.write_bytes(('synthetic '+benchmark+'\n').encode())
        row=dict(id=identity,benchmark=benchmark,retained_command=['/fixture/elixir'],runtime_environment={'ERL_FLAGS':'+S 8:8'},
            reference_case=dict(n=1,stdin=None,expected=dict(path=str(expected),sha256=work.sha(expected))),
            witness_spec=dict(artifact_dir='{fresh-profile-artifact-dir}',lock_fd='{inherited-common-lock-fd}',lock_inode=79859134,
                ebin='/fixture/'+identity,arguments=['1'],main_beam_sha256=SHA,support_beam_sha256=SHA))
        plan['profiles'].append(row)
        for name,value in (('stdin.bin',b''),('stdout.bin',expected.read_bytes()),('stderr.bin',b''),
                           ('expected.stdout',expected.read_bytes()),('trace-framed.etf',b'trace')):
            (directory/name).write_bytes(value)
        for stem in work.ARTIFACT_STEMS:
            for suffix in ('.etf','.txt'):(directory/(stem+suffix)).write_bytes(b'synthetic evidence')
        summary=dict(schema='elixir-compiled-work-draft-observation-v1',
            status='dynamic-observations-recorded-awaiting-instruction-review',benchmark=benchmark,arguments=['1'],
            subject_main_executions=1,subject_modules_recompiled=0,dynamic_assertions_passed=True,common_mutex_inherited=True,
            common_mutex_fd=5,common_mutex_inode=79859134,
            main_beam_sha256=SHA,support_beam_sha256=SHA,trace_events=1,trace_artifact_bytes=5,
            source_work_qualified=False,compiled_work_qualified=False,chart_admission=False,
            direct_instruction_review_complete=False,tree_normal_gc_lifetime_proven=False,pidigits_two_division_dominance_proven=False)
        write(directory/'summary.json',summary)
        write(directory/'spec.json',dict(row['witness_spec'],artifact_dir=str(directory),lock_fd=5))
        pid=1000+index;birth=dict(pid=pid,ppid=500,pgid=pid,birth_seconds=1791950000+index,birth_microseconds=123,status=2)
        process=dict(kind='elixir-compiled-work-witness',status='native-passed',native_process_started=True,
            pid=pid,pgid=pid,exit_status=0,direct_child_reaped=True,remaining_process_group=[],cleanup_errors=[],
            inherited_common_mutex=True,common_mutex_inode=79859134,cwd=str(directory),
            command=['/fixture/elixir','-pa',row['witness_spec']['ebin'],str(work.STAGE/'probe-v2.exs'),str(directory/'spec.json')],
            environment=dict(row['runtime_environment'],HOME=str(directory/'home'),XDG_CONFIG_HOME=str(directory/'config'),
                TMPDIR=str(directory/'tmp')+os.sep,ERL_CRASH_DUMP=str(directory/'erl-crash.dump')),
            process_timeout_seconds=30,cleanup_timeout_seconds=5,maximum_process_group_rss_bytes=SUPERVISOR.RSS_LIMIT,
            native_file_limit_bytes=SUPERVISOR.FILE_LIMIT,stdout_capture_limit_bytes=SUPERVISOR.FILE_LIMIT+SUPERVISOR.PIPE_CHUNK,
            kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=10000,identity=birth,
            stop_signals=[],benchmark_samples=0,source_work_qualified=False,chart_admission=False,
            stdout_transport='OS pipe, retained as received',stderr_transport='exclusive artifact',
            leader_identity_before_reap=dict(birth,status=5),started_at='2026-10-14T00:00:00+00:00',
            finished_at='2026-10-14T00:00:01+00:00')
        for name in ('stdin','stdout','stderr'):
            path=directory/(name+'.bin');process.update({name+'_bytes':path.stat().st_size,name+'_sha256':work.sha(path)})
        write(directory/'process.json',process)
        start=dict({key:process[key] for key in work.IMMUTABLE_RECEIPT_FIELDS},status='starting',
            native_process_started=False,observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0)
        write(directory/'start.json',start)
        write(directory/'active.json',dict(start,status='running',native_process_started=True,pid=pid,pgid=pid,identity=birth))
        report['native_process_ids'].append(dict(id=identity,pid=pid,pgid=pid,kind=process['kind']))
        report['profiles'].append(dict(id=identity,benchmark=benchmark,process=str(directory/'process.json'),
            process_sha256=work.sha(directory/'process.json'),observation=work.validate_observation(row,directory,SUPERVISOR)))
        report['validated_profile_artifacts'][identity]=work.snapshot_observation(directory)
    return output,plan,report


class Integrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.original_stage=work.STAGE;work.STAGE=self.root
        self.output,self.plan,self.report=fixture(self.root)
        self.first=self.plan['profiles'][0];self.directory=self.output/self.first['id']

    def tearDown(self):
        work.STAGE=self.original_stage;self.tmp.cleanup()

    def reconcile(self):return work.reconcile_native(self.report,self.plan,self.output,SUPERVISOR)

    def test_complete_synthetic_observations_are_unqualified(self):
        self.assertEqual(self.reconcile(),[])
        self.assertEqual(self.report['observed_native_process_receipts'],20)
        self.assertFalse(self.report['source_work_qualified']);self.assertFalse(self.report['chart_admission'])

    def test_actual_start_pid_must_match_saved_receipt(self):
        self.report['native_process_ids'][0]['pid']+=1
        self.assertTrue(self.reconcile())

    def test_profile_cannot_select_another_workload_contract(self):
        self.report['profiles'][0]['benchmark']='pidigits'
        self.assertTrue(self.reconcile())

    def test_missing_profile_or_summary_cannot_pass(self):
        self.report['profiles'].pop()
        self.assertTrue(self.reconcile())
        self.report['profiles'].append(dict(id='invalid',observation={}))
        (self.directory/'summary.json').unlink()
        self.assertTrue(self.reconcile())

    def test_changed_disassembly_is_not_rebound_at_terminal(self):
        (self.directory/'main-disassembly.txt').write_bytes(b'changed after validation')
        with self.assertRaises(ValueError):work.finish_run(self.report,{},self.output,SUPERVISOR,None,self.plan)
        report=work.read(self.output/'report.json');terminal=work.read(self.output/'terminal.json')
        self.assertNotEqual(report['status'],work.COMPLETE)
        self.assertEqual(report['status'],terminal['status']);self.assertFalse(terminal['source_work_qualified'])

    def test_deleted_trace_is_detected(self):
        (self.directory/'trace-framed.etf').unlink()
        self.assertTrue(self.reconcile())

    def test_changed_stream_rejected_even_without_snapshot_comparison(self):
        process=work.read(self.directory/'process.json');(self.directory/'stdout.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'stream receipt'):
            work.validate_native_receipt(process,self.first,self.directory,SUPERVISOR,500)

    def test_resource_identity_and_boolean_faults_rejected(self):
        original=work.read(self.directory/'process.json')
        changes=[dict(exit_status=False),dict(native_process_started=1),dict(kernel_monitor_samples=0),
                 dict(observed_peak_process_group_rss_bytes=SUPERVISOR.RSS_LIMIT+1),dict(stop_signals=[9]),
                 dict(leader_identity_before_reap=dict(original['leader_identity_before_reap'],birth_seconds=999)),
                 dict(environment={}),dict(command=['wrong'])]
        for changeset in changes:
            with self.subTest(changes=changeset),self.assertRaises(ValueError):
                work.validate_native_receipt(dict(original,**changeset),self.first,self.directory,SUPERVISOR,500)

    def test_changed_start_or_active_record_is_rejected(self):
        process=work.read(self.directory/'process.json')
        start=work.read(self.directory/'start.json');write(self.directory/'start.json',dict(start,native_process_started=True))
        with self.assertRaisesRegex(ValueError,'request and final'):
            work.validate_native_receipt(process,self.first,self.directory,SUPERVISOR,500)
        write(self.directory/'start.json',start)
        active=work.read(self.directory/'active.json');active['identity']['birth_seconds']+=1
        write(self.directory/'active.json',active)
        with self.assertRaisesRegex(ValueError,'launch observation'):
            work.validate_native_receipt(process,self.first,self.directory,SUPERVISOR,500)

    def test_native_receipt_never_grants_work_or_chart_qualification(self):
        original=work.read(self.directory/'process.json')
        for field,value in (('source_work_qualified',True),('chart_admission',True),('benchmark_samples',False)):
            with self.subTest(field=field),self.assertRaises(ValueError):
                work.validate_native_receipt(dict(original,**{field:value}),self.first,self.directory,SUPERVISOR,500)

    def test_unreported_extra_native_receipt_rejected(self):
        directory=self.output/'elixir-unregistered';directory.mkdir()
        write(directory/'process.json',work.read(self.directory/'process.json'))
        self.assertTrue(self.reconcile())

    def test_artifact_symlink_rejected(self):
        (self.directory/'outside').symlink_to(self.root/'references')
        artifacts,errors=work.collect_artifacts(self.output)
        self.assertTrue(errors);self.assertNotIn(self.first['id']+'/outside',artifacts)

    def test_traversal_error_is_retained(self):
        def broken(*args,**kwargs):
            kwargs['onerror'](OSError('synthetic traversal denial'))
            return iter(())
        with mock.patch.object(work.os,'walk',broken):
            artifacts,errors=work.collect_artifacts(self.output)
        self.assertEqual(artifacts,{});self.assertTrue(errors)

    def test_summary_bool_cannot_be_one_execution(self):
        summary=work.read(self.directory/'summary.json');summary['subject_main_executions']=True
        write(self.directory/'summary.json',summary)
        with self.assertRaises(ValueError):work.validate_observation(self.first,self.directory,SUPERVISOR)

    def test_prepared_spec_and_reference_are_required(self):
        original_spec=work.read(self.directory/'spec.json')
        write(self.directory/'spec.json',dict(original_spec,ebin='/wrong/classes'))
        with self.assertRaisesRegex(ValueError,'specification differs'):
            work.validate_observation(self.first,self.directory,SUPERVISOR)
        write(self.directory/'spec.json',original_spec)
        (self.directory/'stdin.bin').write_bytes(b'unexpected input')
        with self.assertRaisesRegex(ValueError,'stdin differs'):
            work.validate_observation(self.first,self.directory,SUPERVISOR)
        (self.directory/'stdin.bin').write_bytes(b'')
        (self.directory/'expected.stdout').write_bytes(b'wrong reference')
        with self.assertRaisesRegex(ValueError,'expected output differs'):
            work.validate_observation(self.first,self.directory,SUPERVISOR)

    def test_prepared_argument_must_match_bounded_size(self):
        changed=copy.deepcopy(self.first);changed['reference_case']['n']=2
        with self.assertRaisesRegex(ValueError,'bounded case size'):
            work.validate_observation(changed,self.directory,SUPERVISOR)

    def qualification_fixture(self):
        contracts=self.root/'contracts.json'
        write(contracts,dict(benchmarks={benchmark:dict(compiled_review=['synthetic obligation']) for benchmark in work.CASE}))
        controller=Path(work.__file__).resolve()
        self.plan.update(schema='elixir-retained-beam-compiled-work-plan-v1',controller=str(controller),
            controller_sha256=work.sha(controller),pins={str(controller):work.sha(controller),str(contracts):work.sha(contracts)})
        plan_path=self.root/'plan.json';write(plan_path,self.plan)
        self.report.update(plan=str(plan_path),plan_sha256=work.sha(plan_path),pins=dict(self.plan['pins'],**{str(plan_path):work.sha(plan_path)}))
        work.finish_run(self.report,self.report['pins'],self.output,SUPERVISOR,None,self.plan)
        report_path=self.output/'report.json'
        decisions=dict(schema='elixir-direct-compiled-work-review-v1',report_sha256=work.sha(report_path),profiles={})
        for row in self.plan['profiles']:
            path=self.output/row['id']/'main-disassembly.txt'
            decisions['profiles'][row['id']]=dict(compiled_review=[dict(obligation=1,passed=True,
                finding='Synthetic review only',citations=[dict(artifact=row['id']+'/main-disassembly.txt',
                    sha256=work.sha(path),location='synthetic:function/1')])])
        decisions_path=self.root/'decisions.json';write(decisions_path,decisions)
        return SimpleNamespace(report=report_path,report_sha256=work.sha(report_path),decisions=decisions_path,
            decisions_sha256=work.sha(decisions_path),output=self.root/'qualified.json')

    def test_explicit_synthetic_review_qualifies_only_work(self):
        args=self.qualification_fixture()
        with mock.patch.object(work,'load_supervisor',return_value=SUPERVISOR),mock.patch('builtins.print'):work.qualify(args)
        result=work.read(args.output)
        self.assertTrue(result['source_work_qualified']);self.assertFalse(result['full_timings_qualified'])
        self.assertFalse(result['chart_admission'])

    def test_qualify_rejects_extra_file_and_terminal_omission(self):
        args=self.qualification_fixture()
        (self.output/'unregistered.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'inventory differs'):work.qualify(args)
        (self.output/'unregistered.json').unlink()
        terminal=work.read(self.output/'terminal.json');terminal['available_evidence'].pop(self.first['id']+'/main-disassembly.txt')
        write(self.output/'terminal.json',terminal)
        with self.assertRaisesRegex(ValueError,'inventory differs'):work.qualify(args)

    def test_qualify_rejects_rehashed_changed_observation(self):
        args=self.qualification_fixture()
        (self.directory/'main-disassembly.txt').write_bytes(b'changed since validation')
        terminal=work.read(self.output/'terminal.json')
        terminal['available_evidence'][self.first['id']+'/main-disassembly.txt']=dict(
            bytes=(self.directory/'main-disassembly.txt').stat().st_size,sha256=work.sha(self.directory/'main-disassembly.txt'))
        write(self.output/'terminal.json',terminal)
        with mock.patch.object(work,'load_supervisor',return_value=SUPERVISOR),self.assertRaisesRegex(ValueError,'final reconciliation'):
            work.qualify(args)

    def test_qualification_cannot_be_written_into_closed_evidence(self):
        args=self.qualification_fixture();args.output=self.output/'new-qualification.json'
        with mock.patch.object(work,'load_supervisor',return_value=SUPERVISOR),self.assertRaisesRegex(ValueError,'closed native evidence'):
            work.qualify(args)

    def test_disassembly_citation_must_name_generated_evidence(self):
        fake=self.directory/'fake-disassembly.txt';fake.write_text('not a decoded instruction artifact')
        self.report['validated_profile_artifacts'][self.first['id']]=work.snapshot_observation(self.directory)
        args=self.qualification_fixture();decisions=work.read(args.decisions)
        decisions['profiles'][self.first['id']]['compiled_review'][0]['citations']=[dict(
            artifact=self.first['id']+'/fake-disassembly.txt',sha256=work.sha(fake),location='invented')]
        write(args.decisions,decisions);args.decisions_sha256=work.sha(args.decisions)
        with mock.patch.object(work,'load_supervisor',return_value=SUPERVISOR),self.assertRaisesRegex(ValueError,'decoded instruction'):
            work.qualify(args)


if __name__=='__main__':unittest.main()
