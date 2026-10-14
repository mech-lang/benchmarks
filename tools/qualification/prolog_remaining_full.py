"""Run only the fifty unfinished slots after the closed 31-attempt continuation.

The first nine regex samples and subsequent 31 completed samples retain their
original reports, receipts, indices and measurement periods. No completed slot
is rerun. Native sampling and process ownership use the frozen full81 helpers.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/prolog/full50-remaining-v1'
PRIOR = ROOT/'experiments/prolog/full81-linear-v1'
JOB = ROOT/'experiments/prolog/full90-v1/owned-jobs/linear-full81-v1'
PRIOR_CONTROLLER_SHA = '27c50f640396d80bea2e505fb985ae7ef6ab354f6e7c0245d8609f68e1fc0e01'
LINEAR_RECONCILER_SHA = '28535a8268f6eba1947bf2e0d520d594684e153259604c136245d45ceb25ee1a'
PLAN_SHA = 'ad39e6e8ccc4b4497b0462014bd1c1d7ee14e4837900adc409634deff0bb5aab'
REPORT_SHA = 'f7ebf54bb651b40a12de6236e6cf36d5910b48267eaff4dda17f563b08dfdb1b'
SCHEMA = 'prolog-linear-remaining50-plus40-v1'
FIXED = {
    PRIOR/'plan-v1.json': PLAN_SHA,
    PRIOR/'run-v1/report.json': REPORT_SHA,
    PRIOR/'run-v1/terminal.json': '0b0f628d14527d94933c72711a0d7138e3944e8e3e8a72bbe556afcd4fe2682c',
    PRIOR/'priority-interpreter-stop-v1/request.json': '211c136c1fd81f16e79a3c503a25ed22a1038c76b06be436f7bf30675356e247',
    PRIOR/'priority-interpreter-stop-v1/closure.json': '1a65e8d7af500a4ee5c01149ab5f35cabaaa0ac7140cb2916e91a1ee8f84ec99',
    JOB/'request.json': 'd398738a3e336ed02609deb2fd3b84222bfed6ca5973e21c46248c6f656a4c6a',
    JOB/'launch.json': '824248330e3b0a70a4d4bad795186bc6d9cb4865d38a3baf8b7800d21029e3ef',
    JOB/'worker-started.json': '229ecb63cac14cf46b0e7bfecf72fe295dfcdd2aa92aca3e927bcea4500b76c3',
    JOB/'command-started.json': 'f13d8422495881f660f0cc388d632b9b17be197e314b9109a6440ad62e80f5da',
    JOB/'terminal.json': 'cc993ca2487922f7ee5fe29023737fb88389f1a5fb765e43bc078c20eb464c51',
}


def load(path, digest, name):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Frozen helper changed: '+str(path))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


# Definition-only imports. No runtime, sampler or process is started here.
l = load(ROOT/'tools/qualification/prolog_linear_full.py', PRIOR_CONTROLLER_SHA, 'remaining50_frozen')
ind = load(ROOT/'tools/qualification/prolog_linear_reconcile.py', LINEAR_RECONCILER_SHA, 'remaining50_independent')
f, r, p = l.f, l.r, ind.p
require, same, sha, merge = p.require, p.same, l.sha, l.merge
bind, file_inventory = l.bind, l.file_inventory
summarize, attempt_paths, fingerprint_pins, check_new_attempt = l.summarize, l.attempt_paths, l.fingerprint_pins, l.check_new_attempt
SUPERVISOR_SHA = l.SUPERVISOR_SHA


def read(pins, path, digest=None):
    path = Path(path)
    digest = FIXED[path] if digest is None else digest
    raw = bind(pins, path, digest).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Evidence changed during read')
    return p.strict_json(raw)


@contextmanager
def owned_locks():
    # Hold the stopped durable lease in addition to the original durable/suite
    # leases and the common timing mutex. Never recreate a missing lease.
    with (JOB/'owner.lock').open('rb') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held, named = os.fstat(lease.fileno()), (JOB/'owner.lock').stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                and held.st_ino == 82039660, 'Stopped owner lease changed')
        with l.owned_locks() as lock:
            yield lock


def stopped_durable(durable, request, closure):
    first, launch, worker, started, ended = [durable[k] for k in
        ('request','launch','worker-started','command-started','terminal')]
    command = [str(f.PYTHON),'-I','-S','-B',str(ROOT/'tools/qualification/prolog_linear_full.py'),
               'run','--plan',str(PRIOR/'plan-v1.json'),'--plan-sha256',PLAN_SHA]
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
         controller_report_sha256=REPORT_SHA, durable_exit_code=-2,
         owned_processes_absent=[66704,66708,81523,81529], common_mutex_inode=79859134), 'Stop closure differs')
    return 66708


def stopped_checks(plan, previous, report, terminal, durable, request, closure, artifacts):
    """Pure replay of all 31 saved receipts; no failed attempt becomes a sample."""
    slots, originals, _ = ind.schedule(plan, previous)
    parent = stopped_durable(durable, request, closure)
    require(report['schema'] == l.SCHEMA and terminal['schema'] == 'prolog-linear-continuation-terminal-v1'
            and report['status'] == terminal['status'] == 'stopped-unqualified' and report['active'] is None,
            'Wrong stopped producer boundary')
    require(report['plan'] == str(PRIOR/'plan-v1.json') and report['plan_sha256'] == PLAN_SHA
            and terminal['report'] == str(PRIOR/'run-v1/report.json') and terminal['report_sha256'] == REPORT_SHA,
            'Stopped report linkage differs')
    require(report['error_type'] == 'KeyboardInterrupt' and report['error'] == 'Benchmark harness received signal 15'
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors'] == []
            and not report.get('terminal_integrity_errors'), 'Stopped report has an unexpected failure')
    same(terminal['prerequisite_pins'],merge(plan['pins'],{str(PRIOR/'plan-v1.json'):PLAN_SHA}),
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
    require(report['no_automatic_retry'] is True and report['shared_timing_lock'] == str(f.LOCK)
            and report['isolated_failed_profiles'] == [] and report['repeated_completed_samples'] == 0
            and all(p.integer(report[k],v) for k,v in (('sample_count',3),('source_work_profiles',20),('canonical_loc_profiles',20))),
            'Stopped policy differs')
    same(report['benchmark_order'],f.BENCHES,'Stopped workload order differs')
    same(report['reused_samples'],plan['retained']['reused_samples'],'Stopped producer changed original nine')
    require(report['supervisor']['pid'] == parent, 'Stopped report controller differs')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+report['supervisor']['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']), 'Stopped report birth/command differs')
    require(len(report['attempts']) == len(report['independent_supervisors']) == 31, 'Stopped receipt count differs')
    rows = l.initial_rows(plan)
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
            original_report=str(PRIOR/'run-v1/report.json'),original_report_sha256=REPORT_SHA,
            raw=str(paths[0]),raw_sha256=snapshots[str(paths[0])],supervised=str(paths[1]),
            supervised_sha256=snapshots[str(paths[1])],outer=str(paths[2]),outer_sha256=snapshots[str(paths[2])],
            seconds=attempt['seconds'],validation=attempt['validation']))
    completed = [bench for bench in f.BENCHES if summarize(rows,plan['manifests'][bench])]
    same(report['programs'],rows,'Stopped profile summary does not replay its 40 samples')
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
    return dict(plan=str(PRIOR/'plan-v1.json'),plan_sha256=PLAN_SHA,report=str(PRIOR/'run-v1/report.json'),
        report_sha256=REPORT_SHA,terminal=str(PRIOR/'run-v1/terminal.json'),terminal_sha256=FIXED[PRIOR/'run-v1/terminal.json'],
        reused_samples=reused, completed_benchmarks=completed, original_regex_samples=9,
        completed_linear_samples=31, interrupted_native_attempts=0, reused_native_processes=40,
        excluded_original_attempt=10, descriptive_provenance=provenance, kernel_identity_observation_gaps=gaps)


def validate_partition(plan):
    slots = l.schedule_for(plan['manifests'])
    same(plan['schedule'],slots,'Combined schedule changed')
    same(plan['retained_slots'],slots[:40],'Retained slots changed')
    same(plan['remaining_slots'],slots[40:],'Remaining fifty slots changed')
    same([s['slot'] for s in plan['retained']['reused_samples']],slots[:40],'Reused sample order changed')
    require(len(plan['remaining_slots']) == 50 and len(plan['retained']['reused_samples']) == 40,
            'Wrong retained/new split')
    require(plan['full_processes'] == 50 and plan['retained_qualified_samples'] == 40
            and plan['new_prolog_processes'] == 33 and plan['new_mech_processes'] == 17,
            'Remaining process counts differ')


def build_plan(output):
    pins = {str(Path(__file__).resolve()):sha(__file__),
        str(ROOT/'tools/qualification/prolog_linear_full.py'):PRIOR_CONTROLLER_SHA,
        str(ROOT/'tools/qualification/prolog_linear_reconcile.py'):LINEAR_RECONCILER_SHA}
    plan = read(pins,PRIOR/'plan-v1.json')
    same(plan,l.build_plan(PRIOR/'run-v1'),'Original concrete prerequisite plan no longer replays')
    pins.update(merge(pins,plan['pins']))
    previous = read(pins,l.OLD/'plan.json',l.FIXED[l.OLD/'plan.json'])
    report = read(pins,PRIOR/'run-v1/report.json'); terminal = read(pins,PRIOR/'run-v1/terminal.json')
    durable = {name:read(pins,JOB/(name+'.json')) for name in
               ('request','launch','worker-started','command-started','terminal')}
    request = read(pins,PRIOR/'priority-interpreter-stop-v1/request.json')
    closure = read(pins,PRIOR/'priority-interpreter-stop-v1/closure.json')
    inventory = file_inventory(PRIOR/'run-v1',exclude=('terminal.json',))
    same(inventory,terminal['available_evidence_pins'],'Stopped artifact bytes or inventory changed')
    pins.update(merge(pins,inventory))
    artifacts = {path:read(pins,path,digest) for path,digest in report['validated_attempt_artifacts'].items()}
    retained = stopped_checks(plan,previous,report,terminal,durable,request,closure,artifacts)
    result = dict(schema=SCHEMA,status='prepared-awaiting-independent-review',repository=str(ROOT),
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),output=str(output),
        pins=pins,historical_pins=plan['historical_pins'],retained=retained,linear_qualification=plan['linear_qualification'],
        manifests=plan['manifests'],schedule=plan['schedule'],retained_slots=plan['schedule'][:40],
        remaining_slots=plan['schedule'][40:],samples=3,full_processes=50,combined_sample_slots=90,
        retained_qualified_samples=40,new_prolog_processes=33,new_mech_processes=17,
        source_work_profiles=20,canonical_loc_profiles=20,shared_timing_lock=str(f.LOCK),
        common_mutex_held_continuously=True,no_automatic_retry=True,compiler_invocations=0,
        fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,
        original_files_mutated=False,full_timings_qualified=False,chart_admission=False,timing_policy=plan['timing_policy'])
    validate_partition(result); f.verify(pins)
    return result


def fresh_paths(plan_path, output):
    require(plan_path.is_relative_to(PACKET) and output.is_relative_to(PACKET)
            and not plan_path.is_relative_to(output) and not output.is_relative_to(plan_path)
            and not plan_path.exists() and not output.exists(), 'Fresh separate plan/output paths required')


def prepare(args):
    plan_path, output = args.plan.resolve(), args.output.resolve()
    fresh_paths(plan_path,output)
    plan = build_plan(output)
    fresh_paths(plan_path,output)
    f.new_json(plan_path,plan)
    print(json.dumps(dict(plan=str(plan_path),sha256=sha(plan_path),full_processes=50,
                         retained_qualified_samples=40,native_executions=0)),flush=True)


def initial_rows(plan):
    validate_partition(plan)
    rows = {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],
                           retained_attempts=[],measurement_status='pending')
            for manifest in plan['manifests'].values() for row in manifest['profiles']}
    require(len(rows) == 30,'Profile inventory changed')
    for sample in plan['retained']['reused_samples']:
        row = rows[sample['slot'][3]]
        row['samples_seconds'].append(sample['seconds'])
        row['sample_validation'].append(copy.deepcopy(sample['validation']))
        row['retained_attempts'].append(dict(cohort=sample['cohort'],attempt=sample['original_attempt'],
            report=sample['original_report'],report_sha256=sample['original_report_sha256']))
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
    completed = [bench for bench in f.BENCHES if summarize(rows,plan['manifests'][bench])]
    same(completed,plan['retained']['completed_benchmarks'],'Retained workload closure changed')
    return rows


def check_success_ledger(plan, report):
    expected = plan['remaining_slots']
    attempts = {tuple([a[k] for k in ('benchmark','round','id','key')]): a for a in report['attempts']}
    skipped = {tuple(s[k] for k in ('benchmark','round','id','key')) for s in report['skipped_failed_profile_slots']}
    require(len(attempts) == len(report['attempts']) and len(skipped) == len(report['skipped_failed_profile_slots'])
            and not set(attempts).intersection(skipped) and set(attempts).union(skipped) == {tuple(s) for s in expected},
            'Missing, duplicate or extra continuation slot')
    require([a['attempt'] for a in report['attempts']] == list(range(1, len(attempts)+1))
            and report['full_performance_runs'] == len(attempts) and report['native_launch_unconfirmed_attempts'] == []
            and report['active'] is None and report['completed_benchmarks'] == f.BENCHES,
            'Incomplete native ledger or workload summaries')
    expected_attempt_slots = [s for s in expected if tuple(s) not in skipped]
    same([[a[k] for k in ('benchmark','round','id','key')] for a in report['attempts']],
         expected_attempt_slots,'Continuation attempts reordered')
    rows = initial_rows(plan)
    failed = []
    for slot in expected:
        key = slot[3]; row = rows[key]
        if tuple(slot) in skipped:
            require(row.get('full_failure'), 'Skipped slot has no earlier isolated profile failure')
            continue
        attempt = attempts[tuple(slot)]
        require(not row.get('full_failure'), 'Retried failed profile')
        row['attempts'].append(attempt['attempt'])
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        else:
            row['full_failure'] = attempt; row['measurement_status'] = 'failed-full-workload'; failed.append(key)
    for manifest in plan['manifests'].values():
        require(summarize(rows, manifest), 'Missing completed workload summary')
    require(rows == report['programs'] and failed == report['isolated_failed_profiles'], 'Summary does not replay ledger')
    require(report['qualified_samples'] == sum(len(row['samples_seconds']) for row in rows.values()),
            'Wrong retained plus new qualified sample count')
    require(report['retained_qualified_samples'] == 40 and report['repeated_completed_samples'] == 0,
            'Retained sample accounting changed')


def finish(plan, report, pins, snapshots, guard, lock):
    errors = []
    for path, digest in merge(pins, snapshots).items():
        try:
            require(sha(path) == digest, 'Pinned or validated bytes changed')
        except BaseException as error:
            errors.append(dict(path=path, error=str(error) or type(error).__name__))
    f.refresh_attempt_accounting(report)
    try:
        require(report['active'] is None, 'Active attempt remains after supervisor cleanup')
        if report['status'] in ('complete', 'complete-with-unqualified-profiles'):
            check_success_ledger(plan, report)
            expected_files = set()
            previous_end = None
            by_slot = {tuple(s):s for s in plan['remaining_slots']}
            for attempt in report['attempts']:
                slot = [attempt[k] for k in ('benchmark','round','id','key')]
                require(tuple(slot) in by_slot, 'Attempt outside new slots')
                manifest = plan['manifests'][attempt['benchmark']]
                row = next(row for row in manifest['profiles'] if row['key'] == attempt['key'])
                new, _, _ = check_new_attempt(guard.OUT, attempt, slot, row, manifest,
                                             fingerprint_pins(plan, pins), os.getpid())
                begin, end = p.timestamp(attempt['started_at']), p.timestamp(attempt['finished_at'])
                require(previous_end is None or previous_end <= begin, 'New native intervals overlap')
                previous_end = end
                expected_files.update(new)
            require(set(snapshots) == expected_files, 'Missing validated attempt snapshot')
            observed = {str(path) for name in ('attempts','outer-supervisor') for path in (guard.OUT/name).rglob('*')
                        if path.is_file()}
            require(observed == expected_files, 'Extra or missing native attempt artifact')
    except BaseException as error:
        errors.append(dict(error=str(error) or type(error).__name__, error_type=type(error).__name__))
    held, named = os.fstat(lock.fileno()), f.LOCK.stat()
    if (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino) or held.st_ino != 79859134:
        errors.append(dict(error='Common timing lock identity changed'))
    report['pins_unchanged_at_end'] = not errors
    report['validated_attempt_artifacts'] = snapshots
    if errors:
        report.update(status_before_terminal_integrity_failure=report['status'], status='failed-terminal-integrity',
                      terminal_integrity_errors=errors)
    guard.save(guard.REPORT, report)
    try:
        artifacts = file_inventory(guard.OUT)
    except BaseException as error:
        errors.append(dict(error='Artifact retention failed: '+str(error), error_type=type(error).__name__))
        artifacts = {str(guard.REPORT):sha(guard.REPORT)}
    # Close the inventory to the earlier validation, rather than allowing an
    # intervening edit to become a newly accepted terminal artifact digest.
    for path, digest in snapshots.items():
        if artifacts.get(path) != digest:
            errors.append(dict(path=path, error='Validated receipt changed during terminal inventory'))
    for path, digest in pins.items():
        try:
            require(sha(path) == digest, 'Prerequisite changed during terminal inventory')
        except BaseException as error:
            errors.append(dict(path=path, error=str(error) or type(error).__name__))
    if artifacts.get(str(guard.REPORT)) != sha(guard.REPORT):
        errors.append(dict(path=str(guard.REPORT), error='Report changed during terminal inventory'))
    if errors:
        report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors, pins_unchanged_at_end=False)
        guard.save(guard.REPORT, report)
        artifacts[str(guard.REPORT)] = sha(guard.REPORT)
    f.new_json(guard.OUT/'terminal.json', dict(schema='prolog-linear-remaining50-terminal-v1', status=report['status'],
        report=str(guard.REPORT), report_sha256=sha(guard.REPORT), prerequisite_pins=pins,
        available_evidence_pins=artifacts, integrity_errors=errors, common_mutex_held=True,
        common_mutex_held_continuously=True, common_mutex_inode=79859134,
        full_performance_runs=report['full_performance_runs'], saved_attempts=len(report['attempts']),
        registered_native_attempts=report['registered_native_attempts'],
        native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
        qualified_samples=report['qualified_samples'], retained_qualified_samples=40,
        new_qualified_samples=report['qualified_samples']-40,
        skipped_failed_profile_slots=report['skipped_failed_profile_slots'], compiler_invocations=0,
        fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0, repeated_completed_samples=0,
        original_files_mutated=False, full_timings_qualified=False, chart_admission=False))
    require(not errors, 'Terminal integrity failed; actual attempts preserved')


def run(args, lock):
    plan_path = args.plan.resolve()
    require(plan_path.is_relative_to(PACKET), 'Continuation plan outside its packet')
    pins = {}
    plan = read(pins, plan_path, args.plan_sha256)
    output = Path(plan['output'])
    require(output.is_absolute() and output.resolve() == output and output.is_relative_to(PACKET)
            and not plan_path.is_relative_to(output) and not output.exists(), 'Fresh continuation output required')
    require(plan == build_plan(output), 'Reviewed continuation plan differs from its exact prerequisites')
    pins = merge(plan['pins'], pins)
    resolver = f.Resolver(); resolver.logical = dict(plan['historical_pins'])
    guard, harness = f.load_measurement(resolver)
    require(all(pins.get(path) == digest for path, digest in resolver.active.items()), 'Frozen sampler loader pins changed')
    supervisor = f.cold(f.SUPERVISOR, SUPERVISOR_SHA, 'linear_full_owned_supervisor')
    manifests = {bench:dict(value, pins=pins) for bench,value in plan['manifests'].items()}
    for bench, manifest in manifests.items():
        require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                and manifest['maximum_rss_mib'] == 10240, 'Workload/resource policy changed')
    output.mkdir(parents=True)
    guard.OUT, guard.REPORT = output, output/'report.json'
    harness.install_interrupt_handlers()
    rows = initial_rows(plan)
    report = dict(schema=SCHEMA, status='running', started_at=guard.now(), supervisor=guard.identity(os.getpid()),
        plan=str(plan_path), plan_sha256=args.plan_sha256, programs=rows, attempts=[], active=None,
        reused_samples=plan['retained']['reused_samples'], retained_qualified_samples=40,
        benchmark_order=f.BENCHES, completed_benchmarks=copy.deepcopy(plan['retained']['completed_benchmarks']), sample_count=3, full_performance_runs=0,
        skipped_failed_profile_slots=[], isolated_failed_profiles=[], shared_timing_lock=str(f.LOCK),
        common_mutex_held_continuously=True, source_work_profiles=20, canonical_loc_profiles=20,
        chart_admission=False, full_timings_qualified=False, no_automatic_retry=True, repeated_completed_samples=0,
        kernel_identity_observation_gaps=[], descriptive_provenance=[])
    snapshots = {}
    f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
    try:
        for slot in plan['remaining_slots']:
            bench, round_index, identifier, key = slot
            row, manifest = rows[key], manifests[bench]
            if row.get('full_failure'):
                report['skipped_failed_profile_slots'].append(dict(benchmark=bench, round=round_index, id=identifier, key=key))
                guard.save(guard.REPORT, report); continue
            f.verify(pins)
            harness.compact.wait_for_environment(harness.REQUIRED)
            print('PROLOG REMAINING FIFTY', bench, round_index, identifier, manifest['size'], flush=True)
            previous_count = len(report['attempts'])
            try:
                attempt = supervisor.one_attempt(guard, harness, row, manifest, report, round_index, lock.fileno())
                with supervisor.lifecycle_atomic():
                    report['attempts'].append(attempt); report['active'] = None
                    row['attempts'].append(attempt['attempt'])
                    f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
            except BaseException as error:
                with supervisor.lifecycle_atomic():
                    if len(report['attempts']) == previous_count:
                        f.preserve_wrapper_failure(guard, report, row, round_index, error)
                raise
            original_row = next(profile for profile in manifest['profiles'] if profile['key'] == key)
            captured, provenance, gaps = check_new_attempt(output, attempt, slot, original_row, manifest,
                                                           fingerprint_pins(plan, pins), os.getpid())
            snapshots.update(merge(snapshots, captured))
            report['descriptive_provenance'].extend(provenance); report['kernel_identity_observation_gaps'].extend(gaps)
            if attempt['qualified']:
                f.qualified_sample(attempt, manifest, row, harness.execution_fingerprint(row))
                row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
            elif f.isolated_failure(guard, attempt):
                row['full_failure'] = dict(attempt); row['measurement_status'] = 'failed-full-workload'
                report['isolated_failed_profiles'].append(key)
            else:
                row['measurement_status'] = 'stopped-unqualified'
            f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
            require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')
            if summarize(rows, manifest) and bench not in report['completed_benchmarks']:
                report['completed_benchmarks'].append(bench)
            guard.save(guard.REPORT, report)
        check_success_ledger(plan, report)
        report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                      finished_at=guard.now())
    except BaseException as error:
        report.update(status='stopped-unqualified', finished_at=guard.now(), error=str(error) or type(error).__name__,
                      error_type=type(error).__name__)
        (output/'error.log').write_text(traceback.format_exc())
        raise
    finally:
        # The same lock still covers all owned cleanup and final evidence.
        with supervisor.lifecycle_atomic():
            finish(plan, report, pins, snapshots, guard, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    prep = modes.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = modes.add_parser('run'); execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == f.PYTHON.resolve(), 'Use the pinned Python with -I -S -B and no -O')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Prolog remaining fifty interrupted: '+str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    with owned_locks() as lock:
        prepare(args) if args.mode == 'prepare' else run(args, lock)


if __name__ == '__main__':
    main()
