"""Pure synthetic ledger fault tests; no native execution or closure hashing."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('prolog_reconcile_test_subject', Path(__file__).with_name('prolog_reconcile.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
SHA = '1'*64
PLAN = '/fixture/plan.json'


def fixture(failure=None, failure_round=1):
    """Generate a synthetic closed study, with optional isolated workload failure.

    These invented times/identities are test inputs, never measured results.
    Each completed profile has [1,2,3] seconds, median 2, sample SD 1.
    """
    plan = dict(schema='prolog-qualified-original22-full90-v1', controller='/fixture/controller.py',
        controller_sha256=audit.CONTROLLER_SHA, repository='/fixture', output='/fixture/results',
        sealed_source_outcome=dict(path='/fixture/source-outcome.json',sha256=audit.OUTCOME_SHA),
        storage_manifest=dict(path='/fixture/storage.json',sha256=audit.STORAGE_SHA),
        original_authored_sources=22, compiled_copy_reconciliations=44, retained_bounded_cases=156,
        samples=3, full_processes=90, source_work_profiles=20, canonical_loc_profiles=20,
        new_native_probes=0,compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,
        original_files_mutated=False,chart_admission=False,no_automatic_retry=True,shared_timing_lock=str(audit.LOCK),
        pins={'/fixture/controller.py':audit.CONTROLLER_SHA,'/fixture/source-outcome.json':audit.OUTCOME_SHA,
              '/fixture/storage.json':audit.STORAGE_SHA,audit.p.PYTHON:SHA},historical_pins={},manifests={},schedule=[])
    profiles = {}
    for bench in audit.BENCHES:
        ids=[f'prolog-{bench}-compact',f'prolog-{bench}-optimized','mech-aot-control']
        rows=[]
        for identifier,language in zip(ids,('prolog','prolog','mech')):
            key = f'{bench}:{identifier}' if language=='prolog' else f'{bench}:prolog-full-study:mech-control'
            source='/fixture/'+bench+'-'+identifier+'.src'; binary='/fixture/'+language
            row=dict(id=identifier,key=key,benchmark=bench,language=language,source=source,source_sha256=SHA,
                binary=binary,binary_sha256=SHA,command=[binary,'{n}'],cwd='/fixture',runtime_environment={},
                maximum_workers=1 if language=='prolog' else 8,eligible_for_chart=False,chart_admission=False)
            plan['pins'].update({source:SHA,binary:SHA});rows.append(row);profiles[key]=row
        orders=[dict(round=i+1,profiles=ids[i:]+ids[:i]) for i in range(3)]
        plan['manifests'][bench]=dict(benchmark=bench,size=audit.SIZES[bench],samples=3,timeout_seconds=21600,
            supervisor_timeout_seconds=22200,maximum_rss_mib=10240,canonical_full_workload=True,
            chart_admission=False,no_automatic_retry=True,shared_timing_lock=str(audit.LOCK),
            compilation_outside_timer=True,runtime_and_QLF_loading_inside_timer=True,orders=orders,profiles=rows,
            full_output_reference=None if bench=='nbody' else dict(bytes=99,sha256=SHA))
        keys={r['id']:r['key'] for r in rows}
        plan['schedule'].extend([bench,o['round'],name,keys[name]] for o in orders for name in o['profiles'])
    start=datetime(2026,10,14,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    report=dict(status='complete',active=None,plan=PLAN,plan_sha256=audit.PLAN_SHA,pins_unchanged_at_end=True,
        supervisor=dict(pid=99,process_listing='Wed Oct 14 00:00:01 2026 /fixture/controller.py'),
        chart_admission=False,no_automatic_retry=True,shared_timing_lock=str(audit.LOCK),sample_count=3,
        source_work_profiles=20,canonical_loc_profiles=20,benchmark_order=list(audit.BENCHES),
        completed_benchmarks=list(audit.BENCHES),attempts=[],independent_supervisors=[],skipped_failed_profile_slots=[],
        isolated_failed_profiles=[],native_launch_unconfirmed_attempts=[],programs={},started_at=at(0),finished_at=at(2000))
    terminal=dict(status='complete',common_mutex_held=True,integrity_errors=[],chart_admission=False,
        native_launch_unconfirmed_attempts=[],prerequisite_pins=dict(plan['pins'],**{PLAN:audit.PLAN_SHA}),
        available_evidence_pins={'/fixture/results/report.json':SHA},original_files_mutated=False,compiler_invocations=0,fixture_reexecutions=0,
        bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0)
    raw,supervised,outer={}, {}, {}
    for key,row in profiles.items():report['programs'][key]=dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[])
    failed=set()
    for bench,round_number,identifier,key in plan['schedule']:
        if key in failed:
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_number,id=identifier,key=key));continue
        i=len(report['attempts'])+1;pid=1000+i;child=2000+i;row=profiles[key]
        command=[row['binary'],str(audit.SIZES[bench])]
        path=f'/fixture/results/attempts/{i:03d}-{identifier}'
        validation=dict(bytes=99,sha256=SHA,reference_match=True)
        if bench=='nbody':validation.update(tolerance=1e-8,energies=[-0.169075164,-0.169059907])
        a=dict(key=key,id=identifier,benchmark=bench,language=row['language'],source_sha256=SHA,
            command=command,cwd='/fixture',runtime_environment={},
            execution_fingerprint=json.dumps(dict(source_sha256=SHA,binary_sha256=SHA,command=row['command'],
                cwd='/fixture',environment={},support={})),
            started_at=at(i*20),finished_at=at(i*20+round_number),seconds=float(round_number),exit_status=0,
            workload_n=audit.SIZES[bench],full_workload=True,timeout_seconds=21600,maximum_rss_mib=10240,
            power_at_start=audit.POWER,power_at_end=audit.POWER,valid_environment=True,pins_unchanged_at_end=True,
            peak_process_group_rss_kib=100,resource_violation=None,stderr='',stdout_bytes=99,stdout_sha256=SHA,
            validation=validation,round=round_number,attempt=i,sampler_wait_status=0,result_path=path+'.json',
            supervisor_result_path=path+'.supervisor.json',qualified=True,
            supervised_native_group=dict(type='native-group-started',pid=pid,pgid=pid,command=command,inherited_common_mutex=True),
            qualification_checks={name:True for name in audit.p.CHECKS},**{name:[] for name in audit.p.EMPTY_LIST_FIELDS})
        profile=report['programs'][key];profile['attempts'].append(i)
        if key==failure and round_number==failure_round:
            a.update(qualified=False,error='synthetic wrong output',error_type='OutputValidationError')
            a['qualification_checks']['no_execution_error']=False
            a['qualification_checks']['complete_output_reference_match']=False
            a['qualification_checks']['complete_output_bytes_and_hash']=False
            a['validation']['reference_match']=False
            failed.add(key);report['isolated_failed_profiles'].append(key)
            profile.update(measurement_status='failed-full-workload',full_failure=copy.deepcopy(a))
        else:
            profile['samples_seconds'].append(a['seconds']);profile['sample_validation'].append(copy.deepcopy(validation))
        report['attempts'].append(a)
        raw[path+'.json']={k:copy.deepcopy(v) for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        supervised[path+'.supervisor.json']=copy.deepcopy(a)
        terminal['available_evidence_pins'].update({path+'.json':SHA,path+'.supervisor.json':SHA})
        outer_path=f'/fixture/results/outer-supervisor/{i:03d}-{identifier}.json'
        identity=dict(pid=child,ppid=99,pgid=98,status=2,birth_seconds=100,birth_microseconds=123)
        outer[outer_path]=dict(status='returned',deadline_seconds=22200,native_timeout_seconds=21600,common_mutex_fd=5,
            common_mutex_held_through_cleanup=True,native_execute_unchanged=True,native_validation_unchanged=True,
            deadline_expired=False,cleanup_errors=[],signals=[],native_registrations=[copy.deepcopy(a['supervised_native_group'])],
            owned_sampler_children={str(child):dict(identity=identity,reaped=True)},
            owned_groups={str(child):identity,str(pid):dict(pid=pid,ppid=child,pgid=pid,status=2,birth_seconds=101,birth_microseconds=456)})
        report['independent_supervisors'].append(dict(path=outer_path,sha256=SHA,status='returned'))
        terminal['available_evidence_pins'][outer_path]=SHA
    for key,row in report['programs'].items():
        control=row['benchmark']+':prolog-full-study:mech-control'
        row.update(time_x_mech=None if key in failed or control in failed else 1.0,
            matched_mech_control=control,matched_mech_source_sha256=SHA)
        if key not in failed:row.update(measurement_status='measured',median_seconds=2.0,sample_stdev_seconds=1.0)
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',
            saved_attempts=len(report['attempts']),full_performance_runs=len(report['attempts']),
            qualified_samples=sum(a['qualified'] for a in report['attempts']),
            registered_native_attempts=list(range(1,len(report['attempts'])+1)))
    terminal['skipped_failed_profile_slots']=copy.deepcopy(report['skipped_failed_profile_slots'])
    command=[audit.p.PYTHON,'-I','-S','-B','-u',plan['controller'],'run','--plan',PLAN,'--plan-sha256',audit.PLAN_SHA]
    worker=dict(pid=98,listing='98 1 Wed Oct 14 00:00:00 2026 /fixture/worker.py')
    child=dict(pid=99,listing='99 98 Wed Oct 14 00:00:01 2026 /fixture/controller.py')
    durable=dict(request=dict(command=command,cwd='/fixture',schema_version=1,common_mutex_owned_by_target_command=True,
        automatic_retry=False,qualification_granted=False,created_at=at(-3)),
        launch=dict(command=command,cwd='/fixture',automatic_retry=False,qualification_granted=False,worker_identity=worker),
        terminal=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
            command_identity_observation_missing=False,stop_signals=[],command_identity=child,worker_identity=worker,
            command_pid=99,finished_at=at(2001),automatic_retry=False,qualification_granted=False))
    durable['worker-started']=dict(command=command,cwd='/fixture',qualification_granted=False,inherited_private_lease=True,
        detached_session=True,common_mutex_owned_by_target_command=True,worker_identity=worker,started_at=at(-2))
    durable['command-started']=dict(command=command,cwd='/fixture',command_identity_observation_missing=False,
        command_identity=child,command_pid=99,started_at=at(-1))
    return dict(plan=plan,report=report,terminal=terminal,raw=raw,supervised=supervised,outer=outer,durable=durable,
        plan_path=PLAN,plan_sha=audit.PLAN_SHA)


class Reconciliation(unittest.TestCase):
    def test_full90_has_no_admission(self):
        result=audit.reconcile(**fixture())
        self.assertEqual((result['actual_full_native_processes'],result['qualified_samples']),(90,90))
        self.assertFalse(result['chart_admission']);self.assertFalse(result['file_integrity_verified'])
        self.assertTrue(all(r['time_x_mech']==1.0 for r in result['profiles'].values()))

    def test_isolated_failure_each_round_preserves_prior_samples(self):
        key='revcomp:prolog-revcomp-compact'
        for round_number in (1,2,3):
            with self.subTest(round_number=round_number):
                result=audit.reconcile(**fixture(key,round_number))
                self.assertEqual(result['actual_full_native_processes'],87+round_number)
                self.assertEqual(result['qualified_samples'],86+round_number)
                self.assertIsNone(result['profiles'][key]['median_seconds'])
                self.assertEqual(len(result['profiles'][key]['samples_seconds']),round_number-1)

    def test_failed_control_disables_ratios_not_other_valid_samples(self):
        result=audit.reconcile(**fixture('revcomp:prolog-full-study:mech-control'))
        rows=[r for r in result['profiles'].values() if r['benchmark']=='revcomp']
        self.assertEqual(sum(r['full_workload_qualified'] for r in rows),2)
        self.assertTrue(all(r['time_x_mech'] is None for r in rows))

    def test_unexplained_skip_cannot_hide_sample(self):
        f=fixture();f['report']['attempts'].pop()
        with self.assertRaises(ValueError):audit.reconcile(**f)

    def test_orphaned_terminal_artifact_rejected(self):
        f=fixture();f['terminal']['available_evidence_pins']['/fixture/results/attempts/unregistered.json']=SHA
        with self.assertRaisesRegex(ValueError,'unregistered'):audit.reconcile(**f)

    def test_sampler_must_belong_to_durable_controller(self):
        f=fixture();o=next(iter(f['outer'].values()))
        o['owned_sampler_children']['2001']['identity']['ppid']=999
        with self.assertRaisesRegex(ValueError,'durable controller'):audit.reconcile(**f)

    def test_report_controller_birth_must_match_durable(self):
        f=fixture();f['report']['supervisor']['process_listing']=f['report']['supervisor']['process_listing'].replace('00:00:01','00:00:02')
        with self.assertRaisesRegex(ValueError,'birth/command'):audit.reconcile(**f)

    def test_wrong_aggregate_or_control_is_rejected(self):
        for key,value in (('median_seconds',2.1),('sample_stdev_seconds',0.0),('time_x_mech',True),
                          ('matched_mech_source_sha256','0'*64),('source_sha256','0'*64)):
            with self.subTest(key=key):
                f=fixture();next(iter(f['report']['programs'].values()))[key]=value
                with self.assertRaises(ValueError):audit.reconcile(**f)

    def test_partial_failure_median_is_not_published(self):
        key='revcomp:prolog-revcomp-compact';f=fixture(key,2)
        f['report']['programs'][key]['median_seconds']=1.0
        with self.assertRaisesRegex(ValueError,'partial timings'):audit.reconcile(**f)

    def test_negative_sd_is_rejected_even_inside_zero_tolerance(self):
        f=fixture();key='regexredux:prolog-regexredux-compact';row=f['report']['programs'][key]
        row.update(samples_seconds=[1.0,1.0,1.0],median_seconds=1.0,sample_stdev_seconds=-1e-13,time_x_mech=0.5)
        for a in f['report']['attempts']:
            if a['key'] != key:continue
            a['seconds']=1.0
            f['raw'][a['result_path']]={k:v for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
            f['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        with self.assertRaisesRegex(ValueError,'Sample SD differs'):audit.reconcile(**f)

    def test_terminal_counts_require_integers(self):
        f=fixture();f['terminal']['compiler_invocations']=False
        with self.assertRaises(ValueError):audit.reconcile(**f)

    def test_outer_cleanup_failure_rejects_stale_success(self):
        f=fixture();next(iter(f['outer'].values()))['cleanup_errors']=['owned child remains']
        with self.assertRaisesRegex(ValueError,'cleanup error'):audit.reconcile(**f)

    def test_native_identity_must_belong_to_sampler(self):
        f=fixture();o=next(iter(f['outer'].values()));o['owned_groups']['1001']['ppid']=99999
        with self.assertRaisesRegex(ValueError,'child-owned'):audit.reconcile(**f)

    def test_missing_kernel_observation_is_explicit_not_invented(self):
        f=fixture();o=next(iter(f['outer'].values()));o['owned_groups']['1001']=None
        result=audit.reconcile(**f)
        self.assertEqual(len(result['kernel_identity_observation_gaps']),1)
        self.assertFalse(result['runtime_publication_metadata_qualified'])

    def test_live_or_unowned_durable_job_rejected(self):
        f=fixture();f['durable']['terminal']['actual_command_started']=False
        with self.assertRaises(ValueError):audit.reconcile(**f)
        f=fixture();f['report']['active']=dict(pid=123)
        with self.assertRaises(ValueError):audit.reconcile(**f)

    def test_changed_full_output_even_with_consistent_receipts_rejected(self):
        f=fixture();a=f['report']['attempts'][0]
        a['stdout_sha256']='0'*64;a['validation']['sha256']='0'*64
        f['raw'][a['result_path']]={k:v for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        f['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        with self.assertRaisesRegex(ValueError,'full reference'):audit.reconcile(**f)

    def test_overlapping_intervals_rejected(self):
        f=fixture();a=f['report']['attempts'][1]
        a['started_at']=f['report']['attempts'][0]['started_at']
        f['raw'][a['result_path']]={k:v for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        f['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        with self.assertRaisesRegex(ValueError,'intervals overlap'):audit.reconcile(**f)

    def test_nbody_tolerance_checked_from_values(self):
        f=fixture();a=next(a for a in f['report']['attempts'] if a['benchmark']=='nbody')
        a['validation']['energies'][1]=0.0
        f['raw'][a['result_path']]={k:v for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        f['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        with self.assertRaisesRegex(ValueError,'N-body'):audit.reconcile(**f)


if __name__=='__main__':unittest.main()
