"""Synthetic continuation and actual preserved-receipt tests; no native work.

New sample times, identities and closure hashes below are invented fixtures.
They are never written as benchmark evidence or offered for file verification.
"""
import copy
from datetime import datetime,timedelta,timezone
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tested_linear_reconcile',HERE/'prolog_linear_reconcile.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
SHA='1'*64


def read(path):return json.loads(path.read_bytes())


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


def fixture(plan,previous,failure=None,failure_round=1):
    plan=copy.deepcopy(plan);previous=copy.deepcopy(previous)
    old_attempts=previous['report']['attempts'][:9]
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
    report=dict(schema='prolog-linear-continuation81-v1',status='complete',active=None,plan=str(a.PLAN),plan_sha256=a.PLAN_SHA,
        supervisor=dict(pid=parent,process_listing='Fri Jan 1 00:00:00 2027 '+' '.join(command)),
        pins_unchanged_at_end=True,common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],reused_samples=copy.deepcopy(plan['retained']['reused_samples']),
        benchmark_order=list(a.r.BENCHES),completed_benchmarks=list(a.r.BENCHES),shared_timing_lock=str(a.r.LOCK),
        no_automatic_retry=True,sample_count=3,source_work_profiles=20,canonical_loc_profiles=20,retained_qualified_samples=9,
        repeated_completed_samples=0,programs={},attempts=[],independent_supervisors=[],validated_attempt_artifacts={},
        isolated_failed_profiles=[],skipped_failed_profile_slots=[],descriptive_provenance=[],kernel_identity_observation_gaps=[],
        started_at=at(0),finished_at=at(2000))
    terminal=dict(schema='prolog-linear-continuation-terminal-v1',status='complete',report=plan['output']+'/report.json',
        report_sha256=SHA,integrity_errors=[],common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],common_mutex_held=True,common_mutex_inode=79859134,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,
        original_files_mutated=False,retained_qualified_samples=9,prerequisite_pins=dict(plan['pins'],**{str(a.PLAN):a.PLAN_SHA}),
        available_evidence_pins={plan['output']+'/report.json':SHA})
    rows={row['key']:row for manifest in plan['manifests'].values() for row in manifest['profiles']}
    grouped={key:[] for key in rows}
    for x in old_attempts:grouped[x['key']].append(x)
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
        observed=grouped[key];good=[x for x in observed if x['qualified']];retained=row['benchmark']=='regexredux'
        dest=dict(copy.deepcopy(row),samples_seconds=[x['seconds'] for x in good],sample_validation=[x['validation'] for x in good],
            attempts=[] if retained else [x['attempt'] for x in observed],
            retained_attempts=[x['attempt'] for x in observed] if retained else [])
        if key in failed:dest.update(measurement_status='failed-full-workload',full_failure=copy.deepcopy(observed[-1]))
        else:
            median,sd=a.p.three_statistics(dest['samples_seconds'])
            dest.update(measurement_status='measured',median_seconds=median,sample_stdev_seconds=sd)
        report['programs'][key]=dest
    for key,row in report['programs'].items():
        control=report['programs'][row['benchmark']+':prolog-full-study:mech-control']
        row.update(matched_mech_control=control['key'],matched_mech_source_sha256=control['source_sha256'],
            time_x_mech=None if key in failed or control['key'] in failed else row['median_seconds']/control['median_seconds'])
    count=len(report['attempts']);qualified=sum(x['qualified'] for x in report['attempts'])+9
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',saved_attempts=count,
            full_performance_runs=count,qualified_samples=qualified,registered_native_attempts=list(range(1,count+1)))
    terminal.update(new_qualified_samples=qualified-9,skipped_failed_profile_slots=report['skipped_failed_profile_slots'])
    # The source metadata contains retained descriptive provenance that the
    # frozen receipt checks report even though it is not an executed dependency.
    physical=dict(plan['historical_pins']);physical.update(terminal['prerequisite_pins'])
    for x in report['attempts']:report['descriptive_provenance'].extend(a.p.check_fingerprint(x,rows[x['key']],physical))
    return dict(plan=plan,previous=previous,report=report,terminal=terminal,durable=durable,raw=raw,supervised=supervised,
                outer=outer,old_raw=old_raw,old_supervised=old_supervised,old_outer=old_outer)


class Reconcile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(a.PLAN)
        cls.previous={name:read(path) for name,(path,digest) in a.OLD_REFS.items()}

    def case(self,*args,**kwargs):return fixture(self.plan,self.previous,*args,**kwargs)

    def test_combined90_does_not_count_cancelled_attempt(self):
        result=a.reconcile(**self.case())
        self.assertEqual((result['new_full_native_processes'],result['reused_qualified_samples'],result['qualified_samples']),(81,9,90))
        self.assertEqual(result['total_native_processes_including_cancelled'],91)
        self.assertFalse(result['file_integrity_verified']);self.assertFalse(result['chart_admission'])
        self.assertEqual(result['excluded_original_attempt'],10)

    def test_isolated_failure_each_round(self):
        key='revcomp:prolog-revcomp-linear-compact'
        for round_ in (1,2,3):
            result=a.reconcile(**self.case(key,round_))
            self.assertEqual(result['new_full_native_processes'],78+round_)
            self.assertEqual(result['qualified_samples'],86+round_)
            self.assertIsNone(result['profiles'][key]['median_seconds'])

    def test_failed_matched_control_keeps_subject_samples_but_no_ratios(self):
        result=a.reconcile(**self.case('revcomp:prolog-full-study:mech-control'))
        rows=[row for row in result['profiles'].values() if row['benchmark']=='revcomp']
        self.assertEqual(sum(row['full_workload_qualified'] for row in rows),2)
        self.assertTrue(all(row['time_x_mech'] is None for row in rows))

    def test_retained_and_new_attempt_namespaces_are_separate(self):
        result=a.reconcile(**self.case())
        regex=result['profiles']['regexredux:prolog-regexredux-compact']
        revcomp=result['profiles']['revcomp:prolog-revcomp-linear-compact']
        self.assertEqual(regex['attempts'],[1,6,8]);self.assertEqual(revcomp['attempts'],[1,6,8])
        self.assertNotEqual(regex['attempt_cohort'],revcomp['attempt_cohort'])
        self.assertTrue(all('/full90-v1/results/' in e['raw'] for e in regex['sample_evidence']))

    def test_unchanged_profile_and_new_alias_policy(self):
        for modify in (lambda f:f['plan']['manifests']['nbody']['profiles'][0]['command'].append('extra'),
            lambda f:f['plan']['manifests']['revcomp']['profiles'][1].update(optimization_claim='independent algorithm'),
            lambda f:f['plan']['manifests']['revcomp']['profiles'][0].update(canonical_loc=241)):
            f=self.case();modify(f)
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_cancelled_attempt_and_preserved_receipt_changes_rejected(self):
        for modify in (lambda f:f['previous']['report']['attempts'][9].update(qualified=True),
            lambda f:f['previous']['cancellation'].update(cancellation_is_timeout=True),
            lambda f:next(iter(f['old_raw'].values())).update(valid_environment=False),
            lambda f:f['plan']['retained']['reused_samples'][0].update(seconds=0.1)):
            f=self.case();modify(f)
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_no_u_durable_exact_command_and_birth(self):
        for modify in (lambda f:f['durable']['request']['command'].insert(4,'-u'),
            lambda f:f['durable']['terminal'].update(exit_code=1),
            lambda f:f['report']['supervisor'].update(process_listing='Fri Jan 1 00:00:01 2027 wrong')):
            f=self.case();modify(f)
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_unexplained_skips_duplicates_or_extra_artifacts_rejected(self):
        for modify in (lambda f:f['report']['attempts'].pop(),
            lambda f:f['report']['attempts'].append(copy.deepcopy(f['report']['attempts'][0])),
            lambda f:f['terminal']['available_evidence_pins'].update({'/outside.json':SHA}),
            lambda f:f['report']['validated_attempt_artifacts'].pop(next(iter(f['report']['validated_attempt_artifacts'])))):
            f=self.case();modify(f)
            with self.assertRaises((ValueError,KeyError)):a.reconcile(**f)

    def test_raw_output_and_aggregate_disagreement_rejected(self):
        for modify in (lambda f:next(iter(f['raw'].values())).update(stdout_sha256='0'*64),
            lambda f:f['report']['programs']['revcomp:prolog-revcomp-linear-compact'].update(median_seconds=3),
            lambda f:f['report']['programs']['regexredux:prolog-regexredux-compact'].update(retained_attempts=[])):
            f=self.case();modify(f)
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_bad_cleanup_parent_or_environment_rejected(self):
        for modify in (lambda f:next(iter(f['outer'].values()))['cleanup_errors'].append('unreaped'),
            lambda f:next(iter(f['outer'].values()))['owned_groups']['1001'].update(ppid=99),
            lambda f:f['report']['attempts'][0].update(valid_environment=False)):
            f=self.case();modify(f)
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_full_timings_and_chart_flags_remain_false(self):
        for key in ('chart_admission','full_timings_qualified'):
            f=self.case();f['report'][key]=True
            with self.assertRaises(ValueError):a.reconcile(**f)

    def test_actual_plan_and_retained_checks_without_runtime_hashing(self):
        f=self.case();slots,profiles,old_profiles=a.schedule(f['plan'],f['previous']['plan'])
        grouped,_,_,_=a.retained_checks(f['plan'],f['previous'],old_profiles,f['old_raw'],f['old_supervised'],f['old_outer'])
        self.assertEqual(len(slots[9:]),81);self.assertEqual(sum(map(len,grouped.values())),9)


if __name__=='__main__':unittest.main()
