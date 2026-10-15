"""Synthetic full6 ledgers and local ownership faults; no native or pin replay.

These tests are source drafts until the serial timing lane is released. Fixtures
never become native evidence and import no timing producer or sampler.
"""
import copy
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import importlib.util
import json
import os
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('apl_independent_test',HERE/'apl_workspace_reconcile.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
SHA='a'*64


def support(value):
    result={}
    def visit(item):
        if isinstance(item,dict):
            if item.get('path') and a.p.digest(item.get('sha256')):result[item['path']]=item['sha256']
            for name,child in item.items():
                if name in ('pins','libraries','pin_files','support_pins') and isinstance(child,dict):
                    result.update({key:digest for key,digest in child.items() if a.p.digest(digest)})
                visit(child)
        elif isinstance(item,list):
            for child in item:visit(child)
    visit(value);return result


def fixture():
    """Six invented observations with genuine independent receipt schema."""
    counts=dict(path=str(a.PACKET/'synthetic-counts.json'),sha256=SHA)
    work=dict(path=str(a.PACKET/'synthetic-work.json'),sha256=SHA)
    subject=dict(id=a.SUBJECT_ID,key=a.SUBJECT_KEY,language='apl',benchmark='binarytrees',variant='compact',
        source=str(a.SOURCE),source_sha256=a.SOURCE_SHA,binary='/synthetic/apl-launcher',binary_sha256=SHA,
        cwd='/synthetic',runtime_environment=dict(LANG='C'),runtime_binary=dict(path='/synthetic/apl',sha256=SHA),
        source_bundle=[dict(path=str(a.SOURCE),sha256=a.SOURCE_SHA,canonical_loc=40,physical_loc=40),
                       dict(path=str(a.SETUP),sha256=a.SETUP_SHA,canonical_loc=1,physical_loc=1)],
        canonical_loc=41,physical_loc=41,loc=41,formatted_loc=None,formatted_loc_qualified=False,
        setup_inside_timer=True,maximum_workers=1,source_work_qualified=True,canonical_source_count_qualified=True,
        source_count_review=counts,required_work_review=work,support_pins={str(a.SETUP):a.SETUP_SHA,'/synthetic/apl':SHA})
    subject['command']=[subject['binary'],'--cc','1','-f',str(a.SETUP),'-f',subject['source'],'--','{n}']
    control=dict(id='mech-aot-control',key=a.CONTROL_KEY,language='mech',benchmark='binarytrees',source='/synthetic/tree.mec',
        source_sha256=SHA,binary='/synthetic/tree',binary_sha256=SHA,command=['/synthetic/tree','{n}'],
        maximum_workers=8,chart_admission=False,cwd='/synthetic',runtime_environment={})
    rows=[subject,control];ids=[row['id'] for row in rows]
    orders=[dict(round=i+1,profiles=ids[i%2:]+ids[:i%2]) for i in range(3)]
    slots=[['binarytrees',order['round'],identity,next(row['key'] for row in rows if row['id']==identity)]
           for order in orders for identity in order['profiles']]
    pins={str(a.PRODUCER):SHA,str(a.BOUND_REVIEW):a.BOUND_REVIEW_SHA,str(a.OWNER_REVIEW):a.OWNER_REVIEW_SHA,
          **{str(key):value for key,value in a.FAILED_REPORTS.items()}}
    for row in rows:pins.update({row['source']:row['source_sha256'],row['binary']:row['binary_sha256']},**support(row))
    plan=dict(schema='apl-workspace-qualified-full6-plan-v1',repository=str(a.ROOT),controller=str(a.PRODUCER),
        controller_sha256=SHA,pins=pins,output=str(a.PACKET/'synthetic-run'),samples=3,apl_samples=3,
        matched_mech_samples=3,full_processes=6,maximum_live_native_groups=1,minimum_inherited_lock_fd=64,
        continuous_common_mutex=True,common_mutex_inode=79859134,original_files_mutated=False,no_automatic_retry=True,
        stop_on_first_unqualified_attempt=True,compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,
        native_count_reexecutions=0,new_native_probes=0,full_size_work_qualified=False,full_timings_qualified=False,
        chart_admission=False,source_aliases=[a.alias()],qualification=dict(counts=counts,work=work),schedule=slots,
        manifests=dict(binarytrees=dict(benchmark='binarytrees',size=21,samples=3,timeout_seconds=14400,
            supervisor_timeout_seconds=15000,maximum_rss_mib=10240,canonical_full_workload=True,
            runtime_startup_parsing_setup_output_shutdown_inside_timer=True,no_automatic_retry=True,chart_admission=False,
            shared_timing_lock=str(a.LOCK),full_output_reference=a.REFERENCE.copy(),orders=orders,profiles=rows)))
    refs={name:dict(path=str(a.PACKET/'synthetic-plan.json') if name=='plan' else
        str(a.JOB/'terminal.json') if name=='durable' else plan['output']+'/'+name+'.json',sha256=SHA)
        for name in ('plan','report','terminal','durable')}
    start=datetime(2027,1,1,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    argv=[str(a.PYTHON),'-I','-S','-B',str(a.PRODUCER),'run','--plan',refs['plan']['path'],'--plan-sha256',SHA]
    parent=dict(pid=100,listing='100 99 Fri Jan 1 00:00:00 2027 '+' '.join(argv))
    worker=dict(pid=99,listing='99 1 Fri Jan 1 00:00:00 2027 /synthetic/durable')
    durable=dict(request=dict(command=argv,cwd=str(a.ROOT),schema_version=1,common_mutex_owned_by_target_command=True,
        automatic_retry=False,qualification_granted=False,created_at=at(-3)),
        launch=dict(command=argv,cwd=str(a.ROOT),automatic_retry=False,qualification_granted=False,worker_identity=worker),
        terminal=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
            command_identity_observation_missing=False,stop_signals=[],command_identity=parent,worker_identity=worker,
            command_pid=100,finished_at=at(1001),automatic_retry=False,qualification_granted=False),
        **{'worker-started':dict(command=argv,cwd=str(a.ROOT),qualification_granted=False,inherited_private_lease=True,
            detached_session=True,common_mutex_owned_by_target_command=True,worker_identity=worker,started_at=at(-2)),
           'command-started':dict(command=argv,cwd=str(a.ROOT),command_identity_observation_missing=False,
            command_identity=parent,command_pid=100,started_at=at(-1))})
    common=dict(status='complete',full_performance_runs=6,qualified_samples=6,registered_native_attempts=list(range(1,7)),
        native_launch_unconfirmed_attempts=[],full_size_work_qualified=False,full_timings_qualified=False,chart_admission=False,
        source_aliases=[a.alias()],validated_attempt_artifacts={})
    report=dict(copy.deepcopy(common),schema='apl-workspace-full6-results-v1',active=None,pins_unchanged_at_end=True,
        supervisor=dict(pid=100,process_listing='Fri Jan 1 00:00:00 2027 '+' '.join(argv)),
        plan=refs['plan']['path'],plan_sha256=SHA,sample_count=3,planned_apl_samples=3,planned_matched_mech_samples=3,
        benchmark_order=['binarytrees'],completed_benchmarks=['binarytrees'],source_work_profiles=1,canonical_loc_profiles=1,
        formatted_loc_profiles=0,attempts=[],programs={},independent_supervisors=[],started_at=at(0),finished_at=at(1000),
        shared_timing_lock=str(a.LOCK),no_automatic_retry=True,stop_on_first_unqualified_attempt=True)
    terminal=dict(copy.deepcopy(common),schema='apl-workspace-full6-terminal-v1',integrity_errors=[],saved_attempts=6,
        common_mutex_held=True,common_mutex_held_continuously=True,common_mutex_inode=79859134,common_mutex_fd=64,
        report=refs['report']['path'],report_sha256=SHA,prerequisite_pins=dict(pins,**{refs['plan']['path']:SHA}),
        available_evidence_pins={refs['report']['path']:SHA},compiler_invocations=0,fixture_reexecutions=0,
        bounded_reexecutions=0,new_native_probes=0,repeated_completed_samples=0,original_files_mutated=False)
    raw={};supervised={};outer={};grouped={row['key']:[] for row in rows}
    for index,slot in enumerate(slots,1):
        row=next(row for row in rows if row['key']==slot[3]);stem=f'{index:03d}-{row["id"]}'
        paths=[plan['output']+'/attempts/'+stem+'.json',plan['output']+'/attempts/'+stem+'.supervisor.json',
               plan['output']+'/outer-supervisor/'+stem+'.json']
        command=[part.replace('{n}','21') for part in row['command']];pid=200+index;sampler=300+index
        native=dict(type='native-group-started',pid=pid,pgid=pid,inherited_common_mutex=True,command=command)
        fp=dict(source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
            command=[part.replace(row['source'],'{source}') for part in row['command']],cwd=row['cwd'],
            environment=row['runtime_environment'],support=support(row))
        attempt=dict(zip(('benchmark','round','id','key'),slot),attempt=index,qualified=True,seconds=float(index),
            qualification_checks={key:True for key in a.p.CHECKS},sampler_wait_status=0,full_workload=True,workload_n=21,
            timeout_seconds=14400,maximum_rss_mib=10240,valid_environment=True,pins_unchanged_at_end=True,
            power_at_start=a.POWER.copy(),power_at_end=a.POWER.copy(),supervised_native_group=native,command=command,
            cwd=row['cwd'],runtime_environment=row['runtime_environment'],source_sha256=row['source_sha256'],language=row['language'],
            execution_fingerprint=json.dumps(fp),started_at=at(index*20),finished_at=at(index*20+index),exit_status=0,
            stderr=a.WARNING if row['language']=='apl' else '',peak_process_group_rss_kib=1024,
            stdout_bytes=a.REFERENCE['bytes'],stdout_sha256=a.REFERENCE['sha256'],
            validation=dict(reference_match=True,**a.REFERENCE),result_path=paths[0],supervisor_result_path=paths[1])
        attempt.update({key:[] for key in a.p.EMPTY_LIST_FIELDS});report['attempts'].append(attempt);grouped[row['key']].append(attempt)
        supervised[paths[1]]=copy.deepcopy(attempt);raw[paths[0]]={key:copy.deepcopy(value) for key,value in attempt.items() if key not in a.p.SUPERVISOR_FIELDS}
        def kernel(pid,parent):return dict(pid=pid,ppid=parent,pgid=pid,status=2,birth_seconds=1700000000,birth_microseconds=0)
        child=kernel(sampler,100);native_kernel=kernel(pid,sampler)
        outer[paths[2]]=dict(status='returned',deadline_seconds=15000,native_timeout_seconds=14400,common_mutex_fd=64,
            common_mutex_held_through_cleanup=True,native_execute_unchanged=True,native_validation_unchanged=True,
            deadline_expired=False,cleanup_errors=[],native_registrations=[native],
            owned_sampler_children={str(sampler):dict(reaped=True,identity=child)},
            owned_groups={str(sampler):child,str(pid):native_kernel},signals=[])
        for path in paths:
            report['validated_attempt_artifacts'][path]=terminal['validated_attempt_artifacts'][path]=terminal['available_evidence_pins'][path]=SHA
        report['independent_supervisors'].append(dict(path=paths[2],sha256=SHA,status='returned'))
    control_values=[v['seconds'] for v in grouped[a.CONTROL_KEY]];control_median=statistics.median(control_values)
    for row in rows:
        attempts=grouped[row['key']];values=[v['seconds'] for v in attempts]
        report['programs'][row['key']]=dict(copy.deepcopy(row),attempts=[v['attempt'] for v in attempts],samples_seconds=values,
            sample_validation=[v['validation'] for v in attempts],measurement_status='measured',median_seconds=statistics.median(values),
            sample_stdev_seconds=statistics.stdev(values),time_x_mech=statistics.median(values)/control_median,
            matched_mech_control=a.CONTROL_KEY,matched_mech_source_sha256=control['source_sha256'])
    return dict(plan=plan,report=report,terminal=terminal,raw=raw,supervised=supervised,outer=outer,durable=durable,refs=refs,producer_sha=SHA)


class Ledger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):a.load_primitives(a.Files())

    def test_complete_ledger_preserves_raw_data_and_counts_alias_once(self):
        data=fixture();before=copy.deepcopy(data);result=a.reconcile(**data)
        self.assertEqual(data,before);self.assertEqual(result['actual_full_native_processes'],6)
        self.assertEqual(result['profiles'][a.SUBJECT_KEY]['samples_seconds'],[1.0,4.0,5.0])
        self.assertEqual(result['profiles'][a.CONTROL_KEY]['samples_seconds'],[2.0,3.0,6.0])
        self.assertEqual(result['references'],data['refs']);self.assertEqual(len(result['preserved_failed_reports']),2)
        self.assertNotIn(a.ALIAS_KEY,result['profiles']);self.assertFalse(result['file_integrity_verified'])
        self.assertEqual(a.encoded(result),a.encoded(a.reconcile(**data)))

    def test_partial_failed_or_repeated_cohort_rejected(self):
        for alter in (lambda d:d['report']['attempts'].pop(),lambda d:d['report']['attempts'][0].update(qualified=False),
                      lambda d:d['report']['attempts'][1].update(attempt=1),lambda d:d['terminal'].update(status='stopped-unqualified')):
            data=fixture();alter(data)
            with self.assertRaises((ValueError,KeyError)):a.reconcile(**data)

    def test_work_setup_alias_and_limits_cannot_change(self):
        for alter in (lambda d:d['plan']['manifests']['binarytrees'].update(size=20),
                      lambda d:d['plan']['manifests']['binarytrees']['profiles'][0]['source_bundle'].pop(),
                      lambda d:d['plan']['source_aliases'][0].update(additional_native_processes=3),
                      lambda d:d['plan']['manifests']['binarytrees'].update(timeout_seconds=21600)):
            data=fixture();alter(data)
            with self.assertRaises(ValueError):a.reconcile(**data)

    def test_unknown_stderr_bad_output_nonfinite_timing_and_overlap(self):
        for field,value in [('stderr',a.WARNING+'other\n'),('stdout_sha256','b'*64),('seconds',float('nan')),
                            ('started_at','2027-01-01T00:00:00+00:00')]:
            data=fixture();attempt=data['report']['attempts'][1];attempt[field]=value
            data['supervised'][attempt['supervisor_result_path']]=copy.deepcopy(attempt)
            data['raw'][attempt['result_path']]={k:copy.deepcopy(v) for k,v in attempt.items() if k not in a.p.SUPERVISOR_FIELDS}
            with self.assertRaises(ValueError):a.reconcile(**data)

    def test_wrong_birth_reap_fd_or_extra_receipt_rejected(self):
        for alter in (lambda d:next(iter(d['outer'].values())).update(common_mutex_fd=3),
                      lambda d:next(iter(next(iter(d['outer'].values()))['owned_sampler_children'].values())).update(reaped=False),
                      lambda d:d['raw'].update({'/unexpected':{}}),
                      lambda d:d['durable']['terminal']['command_identity'].update(listing='100 99 Sat Jan 2 00:00:00 2027 /other')):
            data=fixture();alter(data)
            with self.assertRaises(ValueError):a.reconcile(**data)

    def test_derived_statistics_and_original_runtime_are_not_trusted(self):
        for change in (dict(median_seconds=99),dict(time_x_mech=1),dict(runtime_environment={'LANG':'changed'})):
            data=fixture();data['report']['programs'][a.SUBJECT_KEY].update(change)
            with self.assertRaises(ValueError):a.reconcile(**data)

    def test_durable_target_has_no_unbuffered_flag(self):
        data=fixture()
        for key in ('request','launch','worker-started','command-started'):data['durable'][key]['command'].insert(4,'-u')
        with self.assertRaises(ValueError):a.reconcile(**data)

    def test_report_controller_pid_birth_and_argv_must_match_durable_owner(self):
        for field in ('pid','birth','argv'):
            data=fixture();supervisor=data['report']['supervisor']
            if field=='pid':supervisor['pid']=101
            elif field=='birth':supervisor['process_listing']=supervisor['process_listing'].replace('Fri Jan 1','Sat Jan 2')
            else:supervisor['process_listing']='Fri Jan 1 00:00:00 2027 /other'
            with self.assertRaises(ValueError):a.reconcile(**data)


class Ownership(unittest.TestCase):
    def test_body_failure_restores_before_release_even_when_checks_pass(self):
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try:yield
            finally:events.append('released')
        with self.assertRaisesRegex(RuntimeError,'body'):
            with lease(),a.yielded_review({},None,lambda:events.append('rechecked'),lambda:events.append('restored')):
                raise RuntimeError('body')
        self.assertEqual(events,['held','rechecked','restored','released'])

    def test_body_closure_cleanup_failures_are_all_retained(self):
        def fail(text):raise RuntimeError(text)
        with self.assertRaises(BaseExceptionGroup) as caught:
            with a.yielded_review({},None,lambda:fail('closure'),lambda:fail('cleanup')):raise KeyboardInterrupt('body')
        self.assertEqual([str(e) for e in caught.exception.exceptions],['body','closure','cleanup'])

    def test_final_consumer_runs_after_input_replay_and_before_last_lock_check(self):
        events=[]
        with a.yielded_review({},None,lambda:events.append('pins'),final_consumer_check=lambda:events.append('consumer'),
                              final_lock_check=lambda:events.append('locks')):events.append('body')
        self.assertEqual(events,['body','pins','consumer','locks'])

    def test_named_alias_keeps_original_pin_and_rejects_retarget_even_for_equal_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();one=root/'one';two=root/'two';name=root/'alias'
            one.write_bytes(b'unchanged');two.write_bytes(b'unchanged');name.symlink_to(one)
            files=a.Files();files.resolutions={str(name):str(one)};digest=a.sha(b'unchanged')
            files.verify(name,digest);self.assertEqual(files.pins,{str(name):digest})
            name.unlink();name.symlink_to(two)
            with self.assertRaises(ValueError):files.verify(name,digest)

    def test_fifo_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'fifo';os.mkfifo(path)
            with patch.object(a.os,'open',side_effect=AssertionError('must not open')):
                with self.assertRaisesRegex(ValueError,'Regular file'):a.file_sha(path)

    def test_main_late_output_edit_is_preserved_and_success_not_printed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();output=root/'reconciliation/result.json'
            @contextmanager
            def context(*args,**kwargs):
                with a.yielded_review({'synthetic':True},None,lambda:output.write_bytes(b'changed'),
                                      kwargs['on_exit_failure'],kwargs['final_consumer_check']) as result:yield result
            argv=['reconcile','--producer-sha256',SHA,'--tool-sha256',SHA,'--output',str(output)]
            for name in ('plan','report','terminal','durable-terminal'):argv+=['--'+name,str(root/(name+'.json')),'--'+name+'-sha256',SHA]
            with patch.object(a,'PACKET',root),patch.object(a,'review_context',context),patch.object(a.sys,'argv',argv),\
                 patch.object(a.signal,'signal'),patch('builtins.print') as printed:
                with self.assertRaises(BaseExceptionGroup):a.main()
                printed.assert_not_called()
            self.assertEqual(output.read_bytes(),b'changed')


if __name__=='__main__':unittest.main()
