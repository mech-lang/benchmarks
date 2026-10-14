"""Actual preserved40 receipts and synthetic remaining50 ledgers; no native work.

No future native observations or successful file-closure receipts are invented
outside these test fixtures. The runtime images and full pin closure are not read.
"""
import copy
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tested_remaining_reconcile',HERE/'prolog_remaining_reconcile.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
SHA='1'*64

def read(path):return json.loads(path.read_bytes())

def saved():
    prior={key:read(path) for key,path in [('plan',a.PRIOR_PLAN),('report',a.PRIOR/'run-v1/report.json'),
        ('terminal',a.PRIOR/'run-v1/terminal.json'),('request',a.PRIOR/'priority-interpreter-stop-v1/request.json'),
        ('closure',a.PRIOR/'priority-interpreter-stop-v1/closure.json')]}
    prior['durable']={key:read(a.PRIOR_JOB/(key+'.json')) for key in
        ('request','launch','worker-started','command-started','terminal')}
    return read(a.PLAN),prior,{key:read(path) for key,(path,digest) in a.OLD_REFS.items()}


def support(row):
    found={}
    def visit(value):
        if isinstance(value,dict):
            if value.get('path') and a.p.digest(value.get('sha256')):found[value['path']]=value['sha256']
            for key,child in value.items():
                if key in ('pins','libraries','pin_files','support_pins') and isinstance(child,dict):
                    found.update({name:digest for name,digest in child.items() if a.p.digest(digest)})
                visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    visit(row);return found

def fixture(plan,prior,original,failure=None,failure_round=1):
    plan=copy.deepcopy(plan);prior=copy.deepcopy(prior);original=copy.deepcopy(original)
    old_attempts=original['report']['attempts'][:9]
    old_raw={x['result_path']:read(Path(x['result_path'])) for x in old_attempts}
    old_supervised={x['supervisor_result_path']:read(Path(x['supervisor_result_path'])) for x in old_attempts}
    old_outer={str(a.OLD/'results/outer-supervisor'/f'{x["attempt"]:03d}-{x["id"]}.json'):
        read(a.OLD/'results/outer-supervisor'/f'{x["attempt"]:03d}-{x["id"]}.json') for x in old_attempts}
    start=datetime(2027,1,1,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    parent=66708;worker_pid=66704
    command=[a.p.PYTHON,'-I','-S','-B',str(a.CONTROLLER),'run','--plan',str(a.PLAN),'--plan-sha256',a.PLAN_SHA]
    parent_listing='66708 66704 Fri Jan 1 00:00:00 2027 '+' '.join(command)
    parent_identity=dict(pid=parent,listing=parent_listing)
    worker_identity=dict(pid=worker_pid,listing='66704 1 Fri Jan 1 00:00:00 2027 /synthetic/worker.py')
    durable=dict(request=dict(command=command,cwd=str(a.ROOT),schema_version=1,common_mutex_owned_by_target_command=True,
            automatic_retry=False,qualification_granted=False,created_at=at(-3)),
        launch=dict(command=command,cwd=str(a.ROOT),automatic_retry=False,qualification_granted=False,worker_identity=worker_identity),
        terminal=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
            command_identity_observation_missing=False,stop_signals=[],command_identity=parent_identity,
            worker_identity=worker_identity,command_pid=parent,finished_at=at(2001),automatic_retry=False,qualification_granted=False))
    durable['worker-started']=dict(command=command,cwd=str(a.ROOT),qualification_granted=False,inherited_private_lease=True,
        detached_session=True,common_mutex_owned_by_target_command=True,worker_identity=worker_identity,started_at=at(-2))
    durable['command-started']=dict(command=command,cwd=str(a.ROOT),command_identity_observation_missing=False,
        command_identity=parent_identity,command_pid=parent,started_at=at(-1))
    report=dict(schema=a.PRODUCER_SCHEMA,status='complete',active=None,plan=str(a.PLAN),plan_sha256=a.PLAN_SHA,
        supervisor=dict(pid=parent,process_listing='Fri Jan 1 00:00:00 2027 '+' '.join(command)),
        pins_unchanged_at_end=True,common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],reused_samples=copy.deepcopy(plan['retained']['reused_samples']),
        benchmark_order=list(a.r.BENCHES),completed_benchmarks=list(a.r.BENCHES),shared_timing_lock=str(a.r.LOCK),
        no_automatic_retry=True,sample_count=3,source_work_profiles=20,canonical_loc_profiles=20,retained_qualified_samples=40,
        repeated_completed_samples=0,programs={},attempts=[],independent_supervisors=[],validated_attempt_artifacts={},
        isolated_failed_profiles=[],skipped_failed_profile_slots=[],descriptive_provenance=[],kernel_identity_observation_gaps=[],
        started_at=at(0),finished_at=at(2000))
    terminal=dict(schema='prolog-linear-remaining50-terminal-v1',status='complete',report=plan['output']+'/report.json',
        report_sha256=SHA,integrity_errors=[],common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],common_mutex_held=True,common_mutex_inode=79859134,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,
        original_files_mutated=False,retained_qualified_samples=40,prerequisite_pins=dict(plan['pins'],**{str(a.PLAN):a.PLAN_SHA}),
        available_evidence_pins={plan['output']+'/report.json':SHA})
    rows={row['key']:row for manifest in plan['manifests'].values() for row in manifest['profiles']}
    grouped={key:[] for key in rows}
    for x in old_attempts+prior['report']['attempts']:grouped[x['key']].append(x)
    failed=set();raw={};supervised={};outer={}
    for bench,round_,identity,key in plan['remaining_slots']:
        if key in failed:
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_,id=identity,key=key));continue
        index=len(report['attempts'])+1;row=rows[key];manifest=plan['manifests'][bench]
        command=[part.replace('{n}',str(manifest['size'])) for part in row['command']]
        reference=manifest['full_output_reference'] or dict(bytes=26,sha256=SHA)
        validation=dict(reference,reference_match=True)
        if bench=='nbody':validation.update(tolerance=1e-8,energies=[-0.169075164,-0.169059907])
        path=plan['output']+'/attempts/'+f'{index:03d}-{identity}'
        native=dict(type='native-group-started',pid=1000+index,pgid=1000+index,command=command,inherited_common_mutex=True)
        x=dict(key=key,id=identity,benchmark=bench,language=row['language'],source_sha256=row['source_sha256'],command=command,
            cwd=row['cwd'],runtime_environment=row['runtime_environment'],
            execution_fingerprint=json.dumps(dict(source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
                command=[part.replace(row['source'],'{source}') for part in row['command']],cwd=row['cwd'],
                environment=row['runtime_environment'],support=support(row))),
            started_at=at(index*20),finished_at=at(index*20+round_),seconds=float(round_),exit_status=0,
            workload_n=manifest['size'],full_workload=True,timeout_seconds=21600,maximum_rss_mib=10240,
            power_at_start=a.r.POWER,power_at_end=a.r.POWER,valid_environment=True,pins_unchanged_at_end=True,
            peak_process_group_rss_kib=100,resource_violation=None,stderr='',stdout_bytes=reference['bytes'],
            stdout_sha256=reference['sha256'],validation=validation,round=round_,attempt=index,sampler_wait_status=0,
            result_path=path+'.json',supervisor_result_path=path+'.supervisor.json',qualified=True,
            supervised_native_group=native,qualification_checks={key:True for key in a.p.CHECKS},
            **{name:[] for name in a.p.EMPTY_LIST_FIELDS})
        if key==failure and round_==failure_round:
            x.update(qualified=False,error='synthetic wrong output',error_type='OutputValidationError')
            for gate in ('no_execution_error','complete_output_reference_match','complete_output_bytes_and_hash'):
                x['qualification_checks'][gate]=False
            x['validation']['reference_match']=False;failed.add(key);report['isolated_failed_profiles'].append(key)
        report['attempts'].append(x);grouped[key].append(x)
        raw[x['result_path']]={k:copy.deepcopy(v) for k,v in x.items() if k not in a.p.SUPERVISOR_FIELDS}
        supervised[x['supervisor_result_path']]=copy.deepcopy(x)
        out=plan['output']+'/outer-supervisor/'+f'{index:03d}-{identity}.json';child=2000+index
        child_identity=dict(pid=child,ppid=parent,pgid=parent,status=2,birth_seconds=100,birth_microseconds=123)
        outer[out]=dict(status='returned',deadline_seconds=22200,native_timeout_seconds=21600,common_mutex_fd=5,
            common_mutex_held_through_cleanup=True,native_execute_unchanged=True,native_validation_unchanged=True,
            deadline_expired=False,cleanup_errors=[],signals=[],native_registrations=[copy.deepcopy(native)],
            owned_sampler_children={str(child):dict(identity=child_identity,reaped=True)},
            owned_groups={str(child):child_identity,str(native['pid']):dict(pid=native['pid'],ppid=child,pgid=native['pid'],
                status=2,birth_seconds=101,birth_microseconds=456)})
        report['independent_supervisors'].append(dict(path=out,sha256=SHA,status='returned'))
        for name in (x['result_path'],x['supervisor_result_path'],out):
            report['validated_attempt_artifacts'][name]=terminal['available_evidence_pins'][name]=SHA
    for key,row in rows.items():
        observed=grouped[key];good=[x for x in observed if x['qualified']]
        retained=[s for s in plan['retained']['reused_samples'] if s['slot'][3]==key]
        dest=dict(copy.deepcopy(row),samples_seconds=[x['seconds'] for x in good],sample_validation=[x['validation'] for x in good],
            attempts=[x['attempt'] for x in report['attempts'] if x['key']==key],
            retained_attempts=[dict(cohort=s['cohort'],attempt=s['original_attempt'],report=s['original_report'],
                report_sha256=s['original_report_sha256']) for s in retained])
        if key in failed:dest.update(measurement_status='failed-full-workload',full_failure=copy.deepcopy(observed[-1]))
        else:
            median,sd=a.p.three_statistics(dest['samples_seconds'])
            dest.update(measurement_status='measured',median_seconds=median,sample_stdev_seconds=sd)
        report['programs'][key]=dest
    for key,row in report['programs'].items():
        control=report['programs'][row['benchmark']+':prolog-full-study:mech-control']
        row.update(matched_mech_control=control['key'],matched_mech_source_sha256=control['source_sha256'],
            time_x_mech=None if key in failed or control['key'] in failed else row['median_seconds']/control['median_seconds'])
    count=len(report['attempts']);qualified=sum(x['qualified'] for x in report['attempts'])+40
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',saved_attempts=count,
            full_performance_runs=count,qualified_samples=qualified,registered_native_attempts=list(range(1,count+1)))
    terminal.update(new_qualified_samples=qualified-40,skipped_failed_profile_slots=report['skipped_failed_profile_slots'])
    # The source metadata contains retained descriptive provenance that the
    # frozen receipt checks report even though it is not an executed dependency.
    physical=dict(plan['historical_pins']);physical.update(terminal['prerequisite_pins'])
    for x in report['attempts']:report['descriptive_provenance'].extend(a.p.check_fingerprint(x,rows[x['key']],physical))
    prior_artifacts={path:read(Path(path)) for path in prior['report']['validated_attempt_artifacts']}
    return dict(plan=plan,prior=prior,original=original,prior_artifacts=prior_artifacts,report=report,terminal=terminal,durable=durable,raw=raw,supervised=supervised,
                outer=outer,old_raw=old_raw,old_supervised=old_supervised,old_outer=old_outer)


class Reconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.inputs=saved()
    def case(self,*args,**kwargs):return fixture(*self.inputs,*args,**kwargs)

    def test_three_real_cohorts_combine_without_completing_stopped_producers(self):
        value=self.case();result=a.reconcile(**value)
        self.assertEqual((result['new_full_native_processes'],result['reused_qualified_samples'],result['qualified_samples']),(50,40,90))
        self.assertEqual(result['total_native_processes_including_cancelled'],91)
        self.assertEqual(result['prior_producer_statuses'],{'original-full90':'stopped-unqualified','linear-full81':'stopped-unqualified'})
        self.assertFalse(result['file_integrity_verified']);self.assertFalse(result['chart_admission'])
        origins=[s for row in result['profiles'].values() for s in row['sample_evidence']]
        self.assertEqual({c:sum(s['cohort']==c for s in origins) for c in ('original-full90','linear-full81','linear-remaining50')},
                         {'original-full90':9,'linear-full81':31,'linear-remaining50':50})
        self.assertEqual(len({s['raw'] for s in origins}),90)
        self.assertEqual(value['prior']['report']['status'],'stopped-unqualified')

    def test_mandelbrot_control_has_one_retained_and_two_new_samples(self):
        result=a.reconcile(**self.case());row=result['profiles']['mandelbrot:prolog-full-study:mech-control']
        self.assertEqual([s['cohort'] for s in row['sample_evidence']],['linear-full81','linear-remaining50','linear-remaining50'])
        self.assertEqual([s['round'] for s in row['sample_evidence']],[1,2,3])
        self.assertEqual(len(row['retained_attempts']),1);self.assertEqual(len(row['attempts']),2)

    def test_isolated_failure_each_round_preserves_partials_without_summary(self):
        for round_ in (1,2,3):
            result=a.reconcile(**self.case('nbody:prolog-nbody-compact',round_))
            row=result['profiles']['nbody:prolog-nbody-compact']
            self.assertEqual(result['new_full_native_processes'],47+round_)
            self.assertEqual(len(row['samples_seconds']),round_-1)
            self.assertIsNone(row['median_seconds']);self.assertEqual(row['failed_cohort'],'linear-remaining50')
            self.assertEqual(sum(not s['qualified'] for s in row['sample_evidence']),1)

    def test_failed_mixed_control_preserves_old_sample_but_excludes_all_ratios(self):
        result=a.reconcile(**self.case('mandelbrot:prolog-full-study:mech-control',2))
        rows=[row for row in result['profiles'].values() if row['benchmark']=='mandelbrot']
        self.assertTrue(all(row['time_x_mech'] is None for row in rows))
        control=next(row for row in rows if row['language']=='mech')
        self.assertEqual(len(control['samples_seconds']),1);self.assertEqual(len(control['retained_attempts']),1)
        self.assertEqual(result['qualified_samples'],88);self.assertEqual(len(result['skipped_slots']),1)

    def test_retained_status_or_stop_boundary_cannot_be_normalized(self):
        mutations=[lambda v:v['prior']['report'].update(status='complete'),
            lambda v:v['original']['report'].update(status='complete'),
            lambda v:v['prior']['closure'].update(interrupted_native_attempts=1),
            lambda v:v['prior']['request'].update(active_before_signal={'pid':123}),
            lambda v:v['prior']['report']['attempts'][-1].update(qualified=False),
            lambda v:v['original']['report']['attempts'][9].update(qualified=True)]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises(ValueError):a.reconcile(**value)

    def test_preserved_values_roles_and_snapshot_digests_are_not_reassigned(self):
        mutations=[lambda v:v['plan']['retained']['reused_samples'][9].update(cohort='original-full90'),
            lambda v:v['plan']['retained']['reused_samples'][0].update(seconds=1),
            lambda v:v['prior']['report']['validated_attempt_artifacts'].pop(next(iter(v['prior']['report']['validated_attempt_artifacts']))),
            lambda v:next(iter(v['old_raw'].values())).update(valid_environment=False),
            lambda v:v['prior_artifacts'].update({'/extra/receipt.json':{}})]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises((ValueError,KeyError)):a.reconcile(**value)

    def test_plan_keeps_exact_remaining_partition_and_runtime(self):
        mutations=[lambda v:v['plan']['remaining_slots'].append(v['plan']['retained_slots'][0]),
            lambda v:v['plan']['retained_slots'].reverse(),
            lambda v:v['plan']['manifests']['nbody']['profiles'][0]['command'].append('extra'),
            lambda v:v['plan']['pins'].pop(str(a.CONTROLLER)),
            lambda v:v['plan'].update(full_processes=True)]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises(ValueError):a.reconcile(**value)

    def test_missing_extra_repeated_skipped_or_old_slot_in_new_ledger_rejects(self):
        mutations=[lambda v:v['report']['attempts'].pop(),
            lambda v:v['report']['attempts'].append(copy.deepcopy(v['report']['attempts'][0])),
            lambda v:v['report']['attempts'][0].update(zip(('benchmark','round','id','key'),v['plan']['retained_slots'][-1])),
            lambda v:v['terminal']['available_evidence_pins'].update({'/unregistered.json':SHA}),
            lambda v:v['report']['skipped_failed_profile_slots'].append(dict(benchmark='nbody',round=3,id='missing',key='missing'))]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises((ValueError,KeyError)):a.reconcile(**value)

    def test_no_u_command_parent_birth_and_cleanup_remain_exact(self):
        mutations=[lambda v:v['durable']['request']['command'].insert(4,'-u'),
            lambda v:v['durable']['terminal'].update(exit_code=1),
            lambda v:v['durable']['terminal']['command_identity'].update(listing=v['durable']['terminal']['command_identity']['listing'].replace('66708 66704','66708 1')),
            lambda v:v['report']['supervisor'].update(process_listing='Fri Jan 1 00:00:01 2027 changed'),
            lambda v:next(iter(v['outer'].values()))['cleanup_errors'].append('unreaped'),
            lambda v:next(iter(v['outer'].values()))['owned_groups']['1001'].update(ppid=1)]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises(ValueError):a.reconcile(**value)

    def test_output_or_timing_fault_rejects_even_consistent_receipt_copies(self):
        for kind in ('output','overlap','stderr','nonfinite'):
            value=self.case();attempt=value['report']['attempts'][1]
            if kind=='output':attempt['stdout_sha256']=attempt['validation']['sha256']='0'*64
            if kind=='overlap':attempt['started_at']=value['report']['attempts'][0]['started_at']
            if kind=='stderr':attempt['stderr']='warning'
            if kind=='nonfinite':attempt['seconds']=float('nan')
            value['raw'][attempt['result_path']]={k:copy.deepcopy(v) for k,v in attempt.items() if k not in a.p.SUPERVISOR_FIELDS}
            value['supervised'][attempt['supervisor_result_path']]=copy.deepcopy(attempt)
            with self.assertRaises(ValueError):a.reconcile(**value)

    def test_statistics_and_retained_attempt_provenance_reject_tampering(self):
        mutations=[lambda v:v['report']['programs']['nbody:prolog-nbody-compact'].update(median_seconds=99),
            lambda v:v['report']['programs']['mandelbrot:prolog-full-study:mech-control'].update(retained_attempts=[]),
            lambda v:v['report']['programs']['regexredux:prolog-regexredux-compact'].update(sample_stdev_seconds=-1),
            lambda v:v['report']['programs']['fasta:prolog-fasta-compact'].update(time_x_mech=True)]
        for mutate in mutations:
            value=self.case();mutate(value)
            with self.assertRaises(ValueError):a.reconcile(**value)

    def test_cohort_refs_keep_exact_prior_reports_and_distinct_indices(self):
        value=self.case();cohorts=a.cohort_refs(value['report'],value['terminal'],SHA)
        self.assertEqual(cohorts['original-full90']['report']['sha256'],a.OLD_REFS['report'][1])
        self.assertEqual(cohorts['linear-full81']['report']['sha256'],a.PRIOR_REPORT_SHA)
        self.assertEqual(cohorts['linear-remaining50']['plan']['sha256'],a.PLAN_SHA)
        self.assertEqual(cohorts['linear-full81']['status'],'stopped-unqualified')
        self.assertEqual(cohorts['linear-remaining50']['status'],'complete')


class Closure(unittest.TestCase):
    def test_consumer_pin_check_and_restoration_remain_inside_leases(self):
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try:yield
            finally:events.append('released')
        def check():self.assertNotIn('released',events);events.append('check')
        def consumer():events.append('consumer');raise ValueError('changed publication input')
        def restore():self.assertNotIn('released',events);events.append('restored')
        with self.assertRaisesRegex(ValueError,'publication input'),lease():
            with a._yield_verified({},check,restore,consumer):events.append('body')
        self.assertEqual(events,['held','check','body','check','consumer','restored','released'])

    def test_failing_body_still_rechecks_and_dual_exit_failures_survive(self):
        calls=[]
        with self.assertRaises(RuntimeError):
            with a._yield_verified({},lambda:calls.append('check'),None,None):raise RuntimeError('body')
        self.assertEqual(calls,['check','check'])
        def check():
            calls.append('check')
            if len(calls)==4:raise ValueError('closure')
        def restore():raise OSError('restoration')
        with self.assertRaises(BaseExceptionGroup) as caught:
            with a._yield_verified({},check,restore,None):pass
        self.assertEqual([str(e) for e in caught.exception.exceptions],['closure','restoration'])

    def test_writer_removes_owned_receipt_on_final_check_failure(self):
        events=[]
        @contextmanager
        def context(on_exit_failure):
            events.append('held')
            try:
                yield {'status':'synthetic-success'}
                self.assertTrue(path.exists());on_exit_failure();events.append('removed')
                raise ValueError('late change')
            finally:events.append('released')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'review.json'
            with patch.object(a,'review_context',context),self.assertRaises(ValueError):a.write_review(path)
            self.assertFalse(path.exists())
        self.assertEqual(events,['held','removed','released'])

    def test_closed_inventory_rejects_symlinks_and_includes_nested_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'nested').mkdir();(path/'nested/terminal.json').write_text('{}')
            self.assertEqual(a.r.inventory(path),{str(path/'nested/terminal.json')})
            (path/'alias').symlink_to(path/'nested')
            with self.assertRaises(ValueError):a.r.inventory(path)


if __name__=='__main__':unittest.main()
