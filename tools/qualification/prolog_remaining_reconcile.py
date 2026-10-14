"""Independently reconcile fifty new Prolog slots and forty retained samples.

The original nine regex observations and the closed31 continuation keep their
actual stopped producer statuses, report identities and receipt indices. No
producer, sampler, runtime or compiler is imported or executed. Completed-job
leases remain held through consumer verification and final artifact closure.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/prolog/full50-remaining-v1'
PRIOR=ROOT/'experiments/prolog/full81-linear-v1'
OLD=ROOT/'experiments/prolog/full90-v1'
PLAN=PACKET/'plan-v1.json'
PLAN_SHA='fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195'
CONTROLLER=ROOT/'tools/qualification/prolog_remaining_full.py'
CONTROLLER_SHA='d5921e9807413dbd720bd38fd42b3f0ff2984553216e8ab6ca2b558092e09147'
JOB=OLD/'owned-jobs/linear-remaining50-v1'
PRIOR_JOB=OLD/'owned-jobs/linear-full81-v1'
PRIOR_PLAN_SHA='ad39e6e8ccc4b4497b0462014bd1c1d7ee14e4837900adc409634deff0bb5aab'
PRIOR_REPORT_SHA='f7ebf54bb651b40a12de6236e6cf36d5910b48267eaff4dda17f563b08dfdb1b'
PRIOR_PLAN=PRIOR/'plan-v1.json'
HELPER=Path(__file__).with_name('prolog_linear_reconcile.py')
HELPER_SHA='28535a8268f6eba1947bf2e0d520d594684e153259604c136245d45ceb25ee1a'
raw=HELPER.read_bytes()
if hashlib.sha256(raw).hexdigest()!=HELPER_SHA:raise ValueError('Frozen independent linear reconciler changed')
spec=importlib.util.spec_from_file_location('remaining50_independent_receipts',HELPER)
l=importlib.util.module_from_spec(spec);exec(compile(raw,str(HELPER),'exec'),l.__dict__)
r,p,require,same=l.r,l.p,l.require,l.same
OLD_REFS=l.OLD_REFS
SCHEMA='prolog-linear-independent50-plus40-reconciliation-v1'
PRODUCER_SCHEMA='prolog-linear-remaining50-plus40-v1'
AGGREGATE=l.AGGREGATE


FIXED = {
    PRIOR/'plan-v1.json': PRIOR_PLAN_SHA,
    PRIOR/'run-v1/report.json': PRIOR_REPORT_SHA,
    PRIOR/'run-v1/terminal.json': '0b0f628d14527d94933c72711a0d7138e3944e8e3e8a72bbe556afcd4fe2682c',
    PRIOR/'priority-interpreter-stop-v1/request.json': '211c136c1fd81f16e79a3c503a25ed22a1038c76b06be436f7bf30675356e247',
    PRIOR/'priority-interpreter-stop-v1/closure.json': '1a65e8d7af500a4ee5c01149ab5f35cabaaa0ac7140cb2916e91a1ee8f84ec99',
    PRIOR_JOB/'request.json': 'd398738a3e336ed02609deb2fd3b84222bfed6ca5973e21c46248c6f656a4c6a',
    PRIOR_JOB/'launch.json': '824248330e3b0a70a4d4bad795186bc6d9cb4865d38a3baf8b7800d21029e3ef',
    PRIOR_JOB/'worker-started.json': '229ecb63cac14cf46b0e7bfecf72fe295dfcdd2aa92aca3e927bcea4500b76c3',
    PRIOR_JOB/'command-started.json': 'f13d8422495881f660f0cc388d632b9b17be197e314b9109a6440ad62e80f5da',
    PRIOR_JOB/'terminal.json': 'cc993ca2487922f7ee5fe29023737fb88389f1a5fb765e43bc078c20eb464c51',
}



def merge(*maps):
    result={}
    for values in maps:
        for name,digest in values.items():
            require(name not in result or result[name]==digest,'Conflicting input pin')
            result[name]=digest
    return result


def attempt_paths(output, attempt):
    stem=f'{attempt["attempt"]:03d}-{attempt["id"]}'
    return (output/'attempts'/(stem+'.json'),output/'attempts'/(stem+'.supervisor.json'),
            output/'outer-supervisor'/(stem+'.json'))


def fingerprint_pins(plan, physical):
    result=dict(plan['historical_pins']);result.update(physical);return result


def summarize(rows, manifest):
    group=[rows[row['key']] for row in manifest['profiles']]
    if not all(len(row['samples_seconds'])==3 or row.get('full_failure') for row in group):return False
    control=next(row for row in group if row['language']=='mech')
    for row in group:
        if not row.get('full_failure'):
            median,sd=p.three_statistics(row['samples_seconds'])
            row.update(median_seconds=median,sample_stdev_seconds=sd)
    for row in group:
        row['time_x_mech']=(row['median_seconds']/control['median_seconds']
            if not row.get('full_failure') and not control.get('full_failure') else None)
        row['matched_mech_control']=control['key'];row['matched_mech_source_sha256']=control['source_sha256']
    return True


def seed_original_rows(plan):
    rows={row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],
            retained_attempts=[],measurement_status='pending')
          for manifest in plan['manifests'].values() for row in manifest['profiles']}
    for sample in plan['retained']['reused_samples']:
        row=rows[sample['slot'][3]];row['samples_seconds'].append(sample['seconds'])
        row['sample_validation'].append(copy.deepcopy(sample['validation']))
        row['retained_attempts'].append(sample['original_attempt'])
        row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
    require(summarize(rows,plan['manifests']['regexredux']),'Retained regex observations incomplete')
    return rows


def same_summary(actual, expected):
    require(set(actual)==set(expected),'Profile summary inventory differs')
    for key,row in expected.items():
        other=actual[key]
        same({k:v for k,v in other.items() if k!='sample_stdev_seconds'},
             {k:v for k,v in row.items() if k!='sample_stdev_seconds'},'Stopped profile summary differs')
        if 'sample_stdev_seconds' in row:
            value=other.get('sample_stdev_seconds')
            require(p.finite(value) and value>=0 and math.isclose(value,row['sample_stdev_seconds'],
                rel_tol=1e-12,abs_tol=1e-12),'Stopped sample SD differs from independent formula')
        else:require('sample_stdev_seconds' not in other,'Partial stopped summary has a standard deviation')


def stopped_durable(durable, request, closure):
    first, launch, worker, started, ended = [durable[k] for k in
        ('request','launch','worker-started','command-started','terminal')]
    command = [p.PYTHON,'-I','-S','-B',str(ROOT/'tools/qualification/prolog_linear_full.py'),
               'run','--plan',str(PRIOR/'plan-v1.json'),'--plan-sha256',PRIOR_PLAN_SHA]
    for item in (first, launch, worker, started):
        same(item['command'], command, 'Stopped durable argv differs')
        require(item['cwd'] == str(ROOT), 'Stopped durable cwd differs')
    require(p.integer(first['schema_version'],1) and first['common_mutex_owned_by_target_command'] is True,
            'Stopped durable request ownership differs')
    for item in (first, launch, ended):
        require(item['automatic_retry'] is item['qualification_granted'] is False, 'Stopped durable scope changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Stopped durable worker ownership differs')
    require(ended['status'] == 'command-failed' and p.integer(ended['exit_code'],-2)
            and ended['actual_command_started'] is True and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False and ended['stop_signals'] == [15],
            'Stopped durable outcome differs')
    require(not any(ended.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure')),
            'Stopped durable cleanup failure')
    same(p.process_identity(started['command_identity']), p.process_identity(ended['command_identity']),
         'Stopped controller birth or command differs')
    for identity in (launch['worker_identity'], ended['worker_identity']):
        same(p.process_identity(identity),p.process_identity(worker['worker_identity']), 'Stopped worker identity differs')
    require(started['command_pid'] == ended['command_pid'] == started['command_identity']['pid'] == 66708
            and worker['worker_identity']['pid'] == 66704
            and p.process_identity(started['command_identity'])[2] == ' '.join(command)
            and started['command_identity']['listing'].split(None,2)[1] == '66704', 'Stopped PID/parent differs')
    require(p.timestamp(first['created_at']) <= p.timestamp(worker['started_at']) <= p.timestamp(started['started_at'])
            <= p.timestamp(ended['finished_at']), 'Stopped durable chronology differs')
    require(request['completed_attempt'] == 31 and request['qualified_samples'] == 40
            and request['active_before_signal'] is None and request['signal'] == 15
            and request['signal_target'] == 66704 and request['preserved_completed_attempts'] == list(range(1,32)),
            'Stop request boundary differs')
    require(request['worker'] == ended['worker_identity']['listing']
            and request['controller'] == ended['command_identity']['listing'], 'Stop request identity differs')
    same(closure, dict(status='closed-after-completed-sample', completed_attempts=31,
         qualified_samples_preserved=40, interrupted_native_attempts=0, active=None, integrity_errors=[],
         controller_report_sha256=PRIOR_REPORT_SHA, durable_exit_code=-2,
         owned_processes_absent=[66704,66708,81523,81529], common_mutex_inode=79859134), 'Stop closure differs')
    return 66708


def stopped_checks(plan, previous, report, terminal, durable, request, closure, artifacts):
    """Pure replay of all 31 saved receipts; no failed attempt becomes a sample."""
    slots, originals, _ = l.schedule(plan, previous)
    parent = stopped_durable(durable, request, closure)
    require(report['schema'] == 'prolog-linear-continuation81-v1' and terminal['schema'] == 'prolog-linear-continuation-terminal-v1'
            and report['status'] == terminal['status'] == 'stopped-unqualified' and report['active'] is None,
            'Wrong stopped producer boundary')
    require(report['plan'] == str(PRIOR/'plan-v1.json') and report['plan_sha256'] == PRIOR_PLAN_SHA
            and terminal['report'] == str(PRIOR/'run-v1/report.json') and terminal['report_sha256'] == PRIOR_REPORT_SHA,
            'Stopped report linkage differs')
    require(report['error_type'] == 'KeyboardInterrupt' and report['error'] == 'Benchmark harness received signal 15'
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors'] == []
            and not report.get('terminal_integrity_errors'), 'Stopped report has an unexpected failure')
    same(terminal['prerequisite_pins'],merge(plan['pins'],{str(PRIOR/'plan-v1.json'):PRIOR_PLAN_SHA}),
         'Stopped prerequisite closure differs')
    for value in (report,terminal):
        require(value['common_mutex_held_continuously'] is True
                and value['full_timings_qualified'] is value['chart_admission'] is False,
                'Stopped producer scope differs')
        for name, expected in (('saved_attempts',31),('full_performance_runs',31),('qualified_samples',40),
                               ('retained_qualified_samples',9)):
            require(p.integer(value[name],expected), 'Stopped accounting differs: '+name)
        same(value['registered_native_attempts'], list(range(1,32)), 'Stopped native registration differs')
        require(value['native_launch_unconfirmed_attempts'] == [] and value['skipped_failed_profile_slots'] == [],
                'Unconfirmed or skipped stopped attempt')
    require(terminal['common_mutex_held'] is True and p.integer(terminal['common_mutex_inode'],79859134)
            and p.integer(terminal['new_qualified_samples'],31) and terminal['original_files_mutated'] is False,
            'Stopped lock or retained accounting differs')
    for name in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','count_replays','repeated_completed_samples'):
        require(p.integer(terminal[name],0), 'Unexpected repeated work')
    require(report['no_automatic_retry'] is True and report['shared_timing_lock'] == str(r.LOCK)
            and report['isolated_failed_profiles'] == [] and report['repeated_completed_samples'] == 0
            and all(p.integer(report[k],v) for k,v in (('sample_count',3),('source_work_profiles',20),('canonical_loc_profiles',20))),
            'Stopped policy differs')
    same(report['benchmark_order'],list(r.BENCHES),'Stopped workload order differs')
    same(report['reused_samples'],plan['retained']['reused_samples'],'Stopped producer changed original nine')
    require(report['supervisor']['pid'] == parent, 'Stopped report controller differs')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+report['supervisor']['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']), 'Stopped report birth/command differs')
    require(len(report['attempts']) == len(report['independent_supervisors']) == 31, 'Stopped receipt count differs')
    rows = seed_original_rows(plan)
    reused = [dict(copy.deepcopy(sample), cohort='original-full90', original_report=plan['retained']['report'],
                   original_report_sha256=plan['retained']['report_sha256']) for sample in plan['retained']['reused_samples']]
    snapshots, provenance, gaps = {}, [], []
    last = None
    pins = fingerprint_pins(plan,terminal['prerequisite_pins'])
    for index, (slot, attempt) in enumerate(zip(slots[9:40],report['attempts']),1):
        require(p.integer(attempt['attempt'],index) and attempt['qualified'] is True, 'Nonqualified or reordered stopped sample')
        paths = attempt_paths(PRIOR/'run-v1',attempt)
        require(attempt['result_path'] == str(paths[0]) and attempt['supervisor_result_path'] == str(paths[1]),
                'Stopped receipt path differs')
        raw, supervised, outer = [artifacts[str(path)] for path in paths]
        begin, end = r.check_attempt(attempt,raw,supervised,slot,originals[slot[3]],plan['manifests'][slot[0]],pins,provenance)
        require(last is None or last <= begin, 'Stopped native intervals overlap')
        last = end
        gaps.extend(r.check_outer(outer,attempt,parent))
        ref = report['independent_supervisors'][index-1]
        same(ref,dict(path=str(paths[2]),sha256=terminal['available_evidence_pins'][str(paths[2])],status='returned'),
             'Stopped outer receipt binding differs')
        for path in paths:
            snapshots[str(path)] = terminal['available_evidence_pins'][str(path)]
        row = rows[slot[3]]
        row['attempts'].append(index); row['samples_seconds'].append(attempt['seconds'])
        row['sample_validation'].append(attempt['validation'])
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        reused.append(dict(slot=slot, original_attempt=index, cohort='linear-full81',
            original_report=str(PRIOR/'run-v1/report.json'),original_report_sha256=PRIOR_REPORT_SHA,
            raw=str(paths[0]),raw_sha256=snapshots[str(paths[0])],supervised=str(paths[1]),
            supervised_sha256=snapshots[str(paths[1])],outer=str(paths[2]),outer_sha256=snapshots[str(paths[2])],
            seconds=attempt['seconds'],validation=attempt['validation']))
    completed = [bench for bench in list(r.BENCHES) if summarize(rows,plan['manifests'][bench])]
    same_summary(report['programs'],rows)
    same(report['completed_benchmarks'],completed,'Stopped completed workload summary differs')
    same(report['validated_attempt_artifacts'],snapshots,'Stopped validation snapshots differ')
    same(report['descriptive_provenance'],provenance,'Stopped provenance differs')
    same(report['kernel_identity_observation_gaps'],gaps,'Stopped kernel observation gaps differ')
    require(set(artifacts) == set(snapshots), 'Unregistered or missing stopped receipt')
    require(set(terminal['available_evidence_pins']) == set(snapshots) |
            {str(PRIOR/'run-v1/report.json'),str(PRIOR/'run-v1/error.log')}, 'Stopped artifact inventory differs')
    require(p.timestamp(durable['command-started']['started_at']) <= p.timestamp(report['started_at'])
            <= p.timestamp(report['attempts'][0]['started_at']) and last <= p.timestamp(report['finished_at'])
            <= p.timestamp(durable['terminal']['finished_at']), 'Stopped sample interval exceeds controller lifetime')
    return dict(plan=str(PRIOR/'plan-v1.json'),plan_sha256=PRIOR_PLAN_SHA,report=str(PRIOR/'run-v1/report.json'),
        report_sha256=PRIOR_REPORT_SHA,terminal=str(PRIOR/'run-v1/terminal.json'),terminal_sha256=FIXED[PRIOR/'run-v1/terminal.json'],
        reused_samples=reused, completed_benchmarks=completed, original_regex_samples=9,
        completed_linear_samples=31, interrupted_native_attempts=0, reused_native_processes=40,
        excluded_original_attempt=10, descriptive_provenance=provenance, kernel_identity_observation_gaps=gaps)


def durable_checks(durable, plan):
    request,launch,worker,started,ended = [durable[k] for k in ('request','launch','worker-started','command-started','terminal')]
    command = [p.PYTHON,'-I','-S','-B',str(CONTROLLER),'run','--plan',str(PLAN),'--plan-sha256',PLAN_SHA]
    for item in (request,launch,worker,started):
        same(item['command'],command,'Durable command must have exact reviewed argv, without -u')
        require(item['cwd']==str(ROOT),'Durable working directory differs')
    require(p.integer(request['schema_version'],1) and request['common_mutex_owned_by_target_command'] is True,
            'Durable ownership request differs')
    for item in (request,launch,ended):
        require(item['automatic_retry'] is item['qualification_granted'] is False,'Durable scope changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Durable worker ownership incomplete')
    require(ended['status']=='command-exited-zero-awaiting-report-review' and p.integer(ended['exit_code'],0)
            and ended['actual_command_started'] is True and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False and ended['stop_signals']==[],
            'Durable controller is not closed successfully')
    require(not any(ended.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure')),
            'Durable owner has failure evidence')
    same(p.process_identity(ended['command_identity']),p.process_identity(started['command_identity']),
         'Controller identity changed')
    same(p.process_identity(ended['worker_identity']),p.process_identity(worker['worker_identity']),'Worker identity changed')
    same(p.process_identity(launch['worker_identity']),p.process_identity(worker['worker_identity']),'Launch worker changed')
    pid = started['command_pid']
    require(p.integer(pid) and pid>0 and p.integer(ended['command_pid'],pid)
            and started['command_identity']['pid']==pid
            and p.process_identity(started['command_identity'])[2]==' '.join(command), 'Unbound observed controller')
    require(p.timestamp(request['created_at']) <= p.timestamp(worker['started_at']) <= p.timestamp(started['started_at'])
            <= p.timestamp(ended['finished_at']),'Durable timestamps inverted')
    return pid


def schedule(plan, prior, original):
    slots,profiles,old_profiles=l.schedule(prior,original)
    require(plan['schema']==PRODUCER_SCHEMA and plan['status']=='prepared-awaiting-independent-review'
            and plan['controller']==str(CONTROLLER) and plan['controller_sha256']==CONTROLLER_SHA
            and plan['repository']==str(ROOT) and plan['output']==str(PACKET/'run-v1'),
            'Wrong remaining50 cohort identity')
    for field,value in (('samples',3),('full_processes',50),('combined_sample_slots',90),
            ('retained_qualified_samples',40),('new_prolog_processes',33),('new_mech_processes',17),
            ('source_work_profiles',20),('canonical_loc_profiles',20),('compiler_invocations',0),
            ('fixture_reexecutions',0),('bounded_reexecutions',0),('count_replays',0),('repeated_completed_samples',0)):
        require(p.integer(plan[field],value),'Remaining50 plan count differs: '+field)
    require(plan['common_mutex_held_continuously'] is True and plan['no_automatic_retry'] is True
            and plan['original_files_mutated'] is False and plan['full_timings_qualified'] is False
            and plan['chart_admission'] is False and plan['shared_timing_lock']==str(r.LOCK),
            'Remaining50 execution policy differs')
    for field in ('manifests','historical_pins','linear_qualification','timing_policy'):
        same(plan[field],prior[field],'Previously qualified source/runtime policy changed: '+field)
    same(plan['schedule'],slots,'Combined rotation differs')
    same(plan['retained_slots'],slots[:40],'Preserved40 rotation differs')
    same(plan['remaining_slots'],slots[40:],'Remaining50 rotation differs')
    same([s['slot'] for s in plan['retained']['reused_samples']],slots[:40],'Retained sample provenance reordered')
    required=merge(prior['pins'],{str(k):v for k,v in FIXED.items()},
                   {str(CONTROLLER):CONTROLLER_SHA,str(HELPER):HELPER_SHA})
    require(all(plan['pins'].get(path)==digest for path,digest in required.items()),
            'Inherited or remaining50 source/evidence pin omitted')
    return slots,profiles,old_profiles


def retained_context(plan, prior, original, old_raw, old_supervised, old_outer, prior_artifacts):
    slots,profiles,old_profiles=schedule(plan,prior['plan'],original['plan'])
    grouped,provenance,gaps,last_original=l.retained_checks(prior['plan'],original,old_profiles,
        old_raw,old_supervised,old_outer)
    retained=stopped_checks(prior['plan'],original['plan'],prior['report'],prior['terminal'],
        prior['durable'],prior['request'],prior['closure'],prior_artifacts)
    same(plan['retained'],retained,'Remaining50 changed the independently preserved forty samples')
    require(last_original<=p.timestamp(prior['report']['started_at']),
            'Stopped continuation overlaps original retained cohort')
    for attempt in prior['report']['attempts']:
        grouped.setdefault(attempt['key'],[]).append(attempt)
    provenance+=retained['descriptive_provenance'];gaps+=retained['kernel_identity_observation_gaps']
    return slots,profiles,grouped,provenance,gaps,p.timestamp(prior['report']['finished_at'])


def sample_origin(attempt, cohort, output):
    paths=attempt_paths(Path(output),attempt)
    return dict(cohort=cohort,attempt=attempt['attempt'],round=attempt['round'],
        raw=str(paths[0]),supervisor=str(paths[1]),outer=str(paths[2]),qualified=attempt['qualified'],
        seconds=attempt.get('seconds'),stdout_bytes=attempt.get('stdout_bytes'),
        stdout_sha256=attempt.get('stdout_sha256'),validation=attempt.get('validation'))


def reconcile(plan,prior,original,report,terminal,durable,raw,supervised,outer,
              old_raw,old_supervised,old_outer,prior_artifacts):
    """Pure three-cohort accounting; file/inventory verification is a separate gate."""
    slots,profiles,grouped,provenance,gaps,last_prior=retained_context(plan,prior,original,
        old_raw,old_supervised,old_outer,prior_artifacts)
    parent=durable_checks(durable,plan)
    worker=p.process_identity(durable['worker-started']['worker_identity'])[0]
    require(all(durable[k]['command_identity']['listing'].split(None,7)[1]==str(worker)
                for k in ('command-started','terminal')),'New controller parent differs from durable worker')
    require(report['schema']==PRODUCER_SCHEMA and terminal['schema']=='prolog-linear-remaining50-terminal-v1'
            and report['status'] in ('complete','complete-with-unqualified-profiles')
            and report['status']==terminal['status'] and report['active'] is None,
            'Remaining50 producer has not completed')
    require(report['plan']==str(PLAN) and report['plan_sha256']==PLAN_SHA
            and terminal['report']==plan['output']+'/report.json','New plan/report binding differs')
    require(not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors'))
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors']==[],
            'Remaining50 integrity failure')
    require(terminal['common_mutex_held'] is True and p.integer(terminal['common_mutex_inode'],79859134),
            'Terminal common mutex differs')
    for value in (report,terminal):
        require(value['common_mutex_held_continuously'] is True and value['full_timings_qualified'] is False
                and value['chart_admission'] is False and value['native_launch_unconfirmed_attempts']==[],
                'New producer scope or ownership differs')
    require(report['shared_timing_lock']==str(r.LOCK) and report['no_automatic_retry'] is True
            and all(p.integer(report[k],v) for k,v in (('sample_count',3),('source_work_profiles',20),
                ('canonical_loc_profiles',20),('retained_qualified_samples',40),('repeated_completed_samples',0))),
            'Remaining50 report policy differs')
    for field in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','count_replays','repeated_completed_samples'):
        require(p.integer(terminal[field],0),'Unexpected repeated or preparatory execution')
    require(terminal['original_files_mutated'] is False and p.integer(terminal['retained_qualified_samples'],40),
            'Changed original evidence or retained count')
    expected_pins=merge(plan['pins'],{str(PLAN):PLAN_SHA})
    same(terminal['prerequisite_pins'],expected_pins,'New terminal prerequisite closure differs')
    same(report['reused_samples'],plan['retained']['reused_samples'],'New report changed preserved observations')
    same(report['benchmark_order'],list(r.BENCHES),'Benchmark order changed')
    same(report['completed_benchmarks'],list(r.BENCHES),'Incomplete combined workload accounting')
    require(report['supervisor']['pid']==parent,'Report names another controller')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+report['supervisor']['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']),'New controller birth/command differs')
    require(set(report['programs'])==set(profiles),'Profile inventory differs')
    all_pins=fingerprint_pins(plan,expected_pins)
    attempts=report['attempts'];failed={};skipped=[];index=0;previous_end=None;used=set();new_provenance=[];new_gaps=[]
    require(len(report['independent_supervisors'])==len(attempts),'New outer receipt count differs')
    for slot in slots[40:]:
        bench,round_,identifier,key=slot
        if key in failed:
            skipped.append(dict(benchmark=bench,round=round_,id=identifier,key=key));continue
        require(index<len(attempts),'Missing remaining50 attempt');attempt=attempts[index];index+=1
        require(p.integer(attempt['attempt'],index),'Repeated or missing new attempt index')
        paths=attempt_paths(Path(plan['output']),attempt);out=str(paths[2])
        require(attempt['result_path']==str(paths[0]) and attempt['supervisor_result_path']==str(paths[1]),
                'New sample artifact path differs')
        ref=report['independent_supervisors'][index-1]
        require(ref['path']==out and ref['status']=='returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'][out]==ref['sha256'],'New outer receipt binding differs')
        begin,end=r.check_attempt(attempt,raw[str(paths[0])],supervised[str(paths[1])],slot,
            profiles[key],plan['manifests'][bench],all_pins,new_provenance)
        require(previous_end is None or previous_end<=begin,'Remaining50 native intervals overlap');previous_end=end
        new_gaps.extend(r.check_outer(outer[out],attempt,parent));used.update(map(str,paths))
        grouped.setdefault(key,[]).append(attempt)
        if not attempt['qualified']:failed[key]=attempt
    require(index==len(attempts) and index+len(skipped)==50,'Unaccounted new attempts or schedule slots')
    require(set(raw)|set(supervised)|set(outer)==used and len(raw)==len(supervised)==len(outer)==index,
            'Unexpected, duplicate or missing new receipt')
    require(set(terminal['available_evidence_pins'])==used|{plan['output']+'/report.json'},
            'Unregistered terminal artifact')
    same(report['validated_attempt_artifacts'],{path:terminal['available_evidence_pins'][path] for path in used},
         'Terminal digests differ from validated receipt snapshots')
    same(report['descriptive_provenance'],new_provenance,'New provenance observations differ')
    same(report['kernel_identity_observation_gaps'],new_gaps,'New kernel observations differ')
    same(report['isolated_failed_profiles'],list(failed),'Failed-profile inventory differs')
    same(report['skipped_failed_profile_slots'],skipped,'Unexplained skipped new slots')
    same(terminal['skipped_failed_profile_slots'],skipped,'Terminal skipped slots differ')
    require(report['status']==('complete-with-unqualified-profiles' if failed else 'complete'),'Final status hides failure')
    good_new=sum(a['qualified'] for a in attempts)
    for value in (report,terminal):
        for field,count in (('saved_attempts',index),('full_performance_runs',index),('qualified_samples',40+good_new)):
            require(p.integer(value[field],count),'Wrong new/retained process count: '+field)
        same(value['registered_native_attempts'],list(range(1,index+1)),'New native registration ledger differs')
    require(p.integer(terminal['new_qualified_samples'],good_new),'Wrong new qualified sample count')
    origins={}
    for cohort,output,observations in (
        ('original-full90',str(OLD/'results'),original['report']['attempts'][:9]),
        ('linear-full81',str(PRIOR/'run-v1'),prior['report']['attempts']),
        ('linear-remaining50',plan['output'],attempts)):
        for attempt in observations:
            origins[attempt['result_path']]=sample_origin(attempt,cohort,output)
    summaries={}
    for key,original_row in profiles.items():
        row=report['programs'][key];observations=grouped.get(key,[])
        same({k:v for k,v in row.items() if k not in AGGREGATE},original_row,'Measured profile/source metadata changed')
        new=[a for a in attempts if a['key']==key]
        retained=[s for s in plan['retained']['reused_samples'] if s['slot'][3]==key]
        same(row['attempts'],[a['attempt'] for a in new],'New profile membership differs')
        expected_retained=[dict(cohort=s['cohort'],attempt=s['original_attempt'],report=s['original_report'],
            report_sha256=s['original_report_sha256']) for s in retained]
        same(row['retained_attempts'],expected_retained,'Retained profile provenance differs')
        good=[a for a in observations if a['qualified']];values=[a['seconds'] for a in good]
        same(row['samples_seconds'],values,'Profile samples differ across the three actual cohorts')
        same(row['sample_validation'],[a['validation'] for a in good],'Profile validation membership differs')
        if key in failed:
            require(row['measurement_status']=='failed-full-workload' and len(values)<3
                    and row.get('median_seconds') is None and row.get('sample_stdev_seconds') is None
                    and row['time_x_mech'] is None,'Partial failed profile promoted to a summary')
            same(row['full_failure'],failed[key],'Failure differs from actual new attempt');median=sd=None
        else:
            require(row['measurement_status']=='measured' and not row.get('full_failure'),'Incomplete measured profile')
            median,sd=p.three_statistics(values)
            require(p.finite(row['median_seconds'],True) and row['median_seconds']==median
                    and p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds']>=0
                    and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Profile statistics differ')
        summaries[key]=dict(key=key,id=row['id'],language=row['language'],benchmark=row['benchmark'],source=row['source'],
            source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],attempts=[a['attempt'] for a in new],
            retained_attempts=expected_retained,samples_seconds=values,median_seconds=median,sample_stdev_seconds=sd,
            full_workload_qualified=key not in failed,failed_attempt=failed.get(key,{}).get('attempt'),
            failed_cohort='linear-remaining50' if key in failed else None,
            sample_evidence=[origins[a['result_path']] for a in observations])
    for key,row in report['programs'].items():
        control_key=row['benchmark']+':prolog-full-study:mech-control';control=summaries[control_key]
        require(row['matched_mech_control']==control_key and row['matched_mech_source_sha256']==profiles[control_key]['source_sha256'],
                'Matched control identity differs')
        ratio=summaries[key]['median_seconds']/control['median_seconds'] if key not in failed and control_key not in failed else None
        same(row['time_x_mech'],ratio,'Matched-control ratio differs');summaries[key]['time_x_mech']=ratio
    require(last_prior<=p.timestamp(report['started_at'])<=p.timestamp(attempts[0]['started_at'])
            and previous_end<=p.timestamp(report['finished_at']),'Remaining50 overlaps preserved cohort or excludes a sample')
    require(p.timestamp(durable['command-started']['started_at'])<=p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at'])<=p.timestamp(durable['terminal']['finished_at']),
            'Remaining50 exceeds durable lifetime')
    return dict(schema=SCHEMA,status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        new_full_native_processes=index,reused_qualified_samples=40,original_regex_samples=9,retained_linear_samples=31,
        actual_full_native_processes=index+40,total_native_processes_including_cancelled=index+41,
        excluded_original_attempt=10,qualified_samples=40+good_new,new_qualified_samples=good_new,
        skipped_slots=skipped,failed_profiles=list(failed),profiles=summaries,repeated_completed_samples=0,
        original_files_mutated=False,prior_producer_statuses={'original-full90':'stopped-unqualified','linear-full81':'stopped-unqualified'},
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance+new_provenance})],
        kernel_identity_observation_gaps=gaps+new_gaps,file_integrity_verified=False,chart_admission=False,
        runtime_publication_metadata_qualified=False,full_timings_qualified=False,complete_stdout_retained=False,
        full_output_evidence='sampler byte counts/hashes and frozen complete-output validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        cohort_policy='Nine original regex observations,31 preserved linear-continuation observations and50 remaining slots; all retain original reports and attempt indices.',
        source_evidence=dict(original_plan=dict(path=str(l.OLD_REFS['plan'][0]),sha256=l.OLD_REFS['plan'][1]),
            original_source_outcome=original['plan']['sealed_source_outcome'],linear_qualification=plan['linear_qualification']),
        admission_requirements=['recorded runtime metadata for all20 forms including linear QLF',
            'publication preserving all three actual cohort identities and excluding failed forms','catalog and website validation'])


def cohort_refs(report, terminal, terminal_sha):
    def binding(path,digest):
        require(p.digest(digest),'Missing cohort artifact digest')
        return dict(path=str(path),sha256=digest)
    return {
        'original-full90':dict(plan=binding(*l.OLD_REFS['plan']),report=binding(*l.OLD_REFS['report']),
            terminal=binding(*l.OLD_REFS['terminal']),status='stopped-unqualified',preserved_qualified_samples=9,
            excluded_attempts=[10]),
        'linear-full81':dict(plan=binding(PRIOR/'plan-v1.json',PRIOR_PLAN_SHA),
            report=binding(PRIOR/'run-v1/report.json',PRIOR_REPORT_SHA),
            terminal=binding(PRIOR/'run-v1/terminal.json',FIXED[PRIOR/'run-v1/terminal.json']),
            status='stopped-unqualified',preserved_qualified_samples=31,interrupted_native_attempts=0),
        'linear-remaining50':dict(plan=binding(PLAN,PLAN_SHA),report=binding(terminal['report'],terminal['report_sha256']),
            terminal=binding(PACKET/'run-v1/terminal.json',terminal_sha),status=report['status'],
            actual_native_processes=len(report['attempts']),qualified_samples=terminal['new_qualified_samples'])}


def verify_leases(leases):
    for path,handle,device,inode in leases:
        held,named=os.fstat(handle.fileno()),path.stat()
        require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==(device,inode),
                'Completed-job lease identity changed')


@contextmanager
def _yield_verified(result,recheck,on_exit_failure,final_consumer_check):
    recheck()
    try:yield result
    finally:
        try:
            recheck()
            if final_consumer_check is not None:final_consumer_check()
        except BaseException as closure_error:
            if on_exit_failure is not None:
                try:on_exit_failure()
                except BaseException as restoration_error:
                    raise BaseExceptionGroup('Evidence closure and publication restoration failed',
                                             [closure_error,restoration_error])
            raise


@contextmanager
def review_context(*,on_exit_failure=None,final_consumer_check=None):
    """Reproduce the actual completed three-cohort ledger while holding five leases."""
    with ExitStack() as stack:
        leases=[]
        for path,expected_inode in ((JOB/'owner.lock',None),(PRIOR_JOB/'owner.lock',82039660),
                (OLD/'owned-jobs/full90/owner.lock',81764070),
                (ROOT/'experiments/prolog/prolog-full90.owner.lock',81764078),(r.LOCK,79859134)):
            handle=stack.enter_context(path.open('rb'));fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held,named=os.fstat(handle.fileno()),path.stat()
            require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)
                    and (expected_inode is None or held.st_ino==expected_inode),'Completed-job lease replaced')
            leases.append((path,handle,held.st_dev,held.st_ino))
        files=r.Files();files.verify(p.PYTHON,l.PYTHON_SHA)
        plan=files.document(str(PLAN),PLAN_SHA)
        for path,digest in plan['pins'].items():files.verify(path,digest)
        for path,digest in ((Path(__file__).resolve(),hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                (HELPER,HELPER_SHA),(l.RECONCILER,l.RECONCILER_SHA),(r.HELPER,r.HELPER_SHA)):
            files.verify(str(path),digest)
        original={key:files.document(str(path),digest) for key,(path,digest) in l.OLD_REFS.items()}
        prior=dict(plan=files.document(str(PRIOR/'plan-v1.json'),PRIOR_PLAN_SHA),
            report=files.document(str(PRIOR/'run-v1/report.json'),PRIOR_REPORT_SHA),
            terminal=files.document(str(PRIOR/'run-v1/terminal.json'),FIXED[PRIOR/'run-v1/terminal.json']),
            request=files.document(str(PRIOR/'priority-interpreter-stop-v1/request.json'),FIXED[PRIOR/'priority-interpreter-stop-v1/request.json']),
            closure=files.document(str(PRIOR/'priority-interpreter-stop-v1/closure.json'),FIXED[PRIOR/'priority-interpreter-stop-v1/closure.json']),
            durable={name:files.document(str(PRIOR_JOB/(name+'.json')),FIXED[PRIOR_JOB/(name+'.json')])
                for name in ('request','launch','worker-started','command-started','terminal')})
        durable={name:files.document(str(JOB/(name+'.json')),hashlib.sha256((JOB/(name+'.json')).read_bytes()).hexdigest())
            for name in ('request','launch','worker-started','command-started','terminal')}
        require((JOB/'command.stderr').read_bytes()==b'','New durable controller emitted errors')
        inventories=[]
        for directory in (JOB,PRIOR_JOB,OLD/'owned-jobs/full90'):
            expected={str(directory/name) for name in ('request.json','launch.json','worker-started.json',
                'command-started.json','terminal.json','command.stdout','command.stderr','worker.log','owner.lock')}
            same(sorted(r.inventory(directory)),sorted(expected),'Durable artifact inventory differs')
            for path in expected:
                if path in files.verified:continue
                with Path(path).open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
                files.verify(path,digest)
            inventories.append((directory,expected))
        output=Path(plan['output']);terminal_path=output/'terminal.json'
        terminal_sha=hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal=files.document(str(terminal_path),terminal_sha)
        require(terminal['report']==str(output/'report.json'),'New terminal report path escaped run')
        report=files.document(terminal['report'],terminal['report_sha256'])
        for directory,closed in ((output,terminal),(PRIOR/'run-v1',prior['terminal']),(OLD/'results',original['terminal'])):
            expected=set(closed['available_evidence_pins'])|{str(directory/'terminal.json')}
            same(sorted(r.inventory(directory)),sorted(expected),'Closed native artifact inventory differs')
            for name,digest in closed['available_evidence_pins'].items():
                require(Path(name).is_relative_to(directory),'Native artifact escapes closed run');files.verify(name,digest)
            inventories.append((directory,expected))
        def documents(paths):return {path:files.document(path,files.verified[path]) for path in paths}
        old=original['report']['attempts'][:9]
        result=reconcile(plan,prior,original,report,terminal,durable,
            documents(a['result_path'] for a in report['attempts']),
            documents(a['supervisor_result_path'] for a in report['attempts']),
            documents(a['path'] for a in report['independent_supervisors']),
            documents(a['result_path'] for a in old),documents(a['supervisor_result_path'] for a in old),
            documents(str(attempt_paths(OLD/'results',a)[2]) for a in old),
            documents(prior['report']['validated_attempt_artifacts']))
        verified=tuple(files.verified.items())
        def recheck():
            for path,digest in verified:files.verify(path,digest)
            for directory,expected in inventories:
                same(sorted(r.inventory(directory)),sorted(expected),'Closed artifact inventory changed during review')
            verify_leases(leases)
        result.update(status='full50-plus-retained40-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=dict(path=str(PLAN),sha256=PLAN_SHA),report=dict(path=terminal['report'],sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path),sha256=terminal_sha),durable_directory=str(JOB),
            cohorts=cohort_refs(report,terminal,terminal_sha),verified_file_pins=dict(verified))
        with _yield_verified(result,recheck,on_exit_failure,final_consumer_check) as reviewed:yield reviewed


def review_files():
    with review_context() as result:return result


def write_review(path):
    owned={}
    def remove_owned():
        if not owned:return
        stat=path.lstat()
        require(not path.is_symlink() and (stat.st_dev,stat.st_ino)==owned['identity']
                and owned['bytes'].startswith(path.read_bytes()),'Result path changed; preserving unowned bytes')
        path.unlink();owned.clear()
    with review_context(on_exit_failure=remove_owned) as result:
        raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode()
        try:
            with path.open('xb') as stream:
                stat=os.fstat(stream.fileno());owned.update(identity=(stat.st_dev,stat.st_ino),bytes=raw)
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
        except BaseException as error:
            try:remove_owned()
            except BaseException as cleanup:
                raise BaseExceptionGroup('Result write and restoration failed',[error,cleanup])
            raise
    return result,hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B')
    path=args.output.resolve()
    require(path.is_relative_to(PACKET) and not path.is_relative_to(PACKET/'run-v1')
            and not path.exists() and path.parent.is_dir(),'Fresh additive review outside native output required')
    result,digest=write_review(path)
    print(json.dumps(dict(output=str(path),sha256=digest,new_native_processes=result['new_full_native_processes'],
        retained_samples=40,qualified_samples=result['qualified_samples'],failed_profiles=result['failed_profiles'],
        chart_admission=False)),flush=True)


if __name__=='__main__':main()
