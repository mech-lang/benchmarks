"""Preserve 54 observations and run only 36 slots after knucleotide replacement.

Preparation requires a separately reviewed, actually qualified replacement.
The cancelled process remains excluded; no original producer is rewritten.
"""
import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/prolog/full36-knucleotide-v1'
SOURCE = ROOT/'experiments/prolog/knucleotide-linear-v1'
STOP = SOURCE/'stop-v1'
PREVIOUS = ROOT/'experiments/prolog/full50-remaining-v1'
JOB = ROOT/'experiments/prolog/full90-v1/owned-jobs/linear-remaining50-v1'
PREVIOUS_PLAN_SHA = 'fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195'
PREVIOUS_CONTROLLER_SHA = 'd5921e9807413dbd720bd38fd42b3f0ff2984553216e8ab6ca2b558092e09147'
SCHEMA = 'prolog-knucleotide-remaining36-plus54-v1'
CLOSURE_SHA = '0649952532e5a1c8a1bd27d805e087f950ea0c50bb82e6246c1ecd1c230536b6'
SOURCE_SHA = 'b3f524485ccfc29204efecc2f0da47b91b7a63041f4591512ecb2af844ade1e6'
SOURCES = {
    str(SOURCE/'sources/knucleotide/compact.pl'): SOURCE_SHA,
    str(SOURCE/'sources/knucleotide/optimized.pl'): SOURCE_SHA,
    str(SOURCE/'support/clbg_io.pl'): 'bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3',
    str(SOURCE/'support/clbg_records.pl'): 'efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19',
}


def load(path, digest, name):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Frozen definition changed: '+str(path))
    module = types.ModuleType(name); module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


# Definition-only imports; runtime and historical pin replay occur under leases.
c = load(ROOT/'tools/qualification/prolog_remaining_full.py', PREVIOUS_CONTROLLER_SHA, 'knucleotide_retained50')
f, l, r, p = c.f, c.l, c.r, c.p
require, same, sha, merge = p.require, p.same, c.sha, c.merge
attempt_paths, summarize, fingerprint_pins = c.attempt_paths, c.summarize, c.fingerprint_pins


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path
            and stat.S_ISREG(path.lstat().st_mode), 'Physical regular file required: '+str(path))
    return path


def read(pins, path, digest):
    path = regular(path)
    require(p.digest(digest), 'Invalid evidence digest')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Evidence changed: '+str(path))
    pins.update(merge(pins, {str(path): digest}))
    return p.strict_json(raw)


@contextmanager
def owned_locks():
    with regular(JOB/'owner.lock').open('rb') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = os.fstat(lease.fileno())
        require(before.st_ino == 82087540, 'Stopped remaining50 lease changed')
        with c.owned_locks() as lock:
            verify_lease(lease, JOB/'owner.lock', 82087540)
            try:
                yield lock
            finally:
                verify_lease(lease, JOB/'owner.lock', 82087540)


def verify_lease(lease, path, inode):
    held, named = os.fstat(lease.fileno()), Path(path).lstat()
    require(stat.S_ISREG(named.st_mode) and (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
            and held.st_ino == inode, 'Owned lease path changed')


def stopped_durable(durable, request, closure):
    command = [str(f.PYTHON), '-I', '-S', '-B', str(ROOT/'tools/qualification/prolog_remaining_full.py'),
               'run', '--plan', str(PREVIOUS/'plan-v1.json'), '--plan-sha256', PREVIOUS_PLAN_SHA]
    for name in ('request', 'launch', 'worker-started', 'command-started'):
        same(durable[name]['command'], command, 'Stopped durable command changed')
        require(durable[name]['cwd'] == str(ROOT), 'Stopped durable cwd changed')
    first, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    require(p.integer(first['schema_version'], 1) and first['common_mutex_owned_by_target_command'] is True,
            'Stopped durable request changed')
    for value in (first, launch, ended):
        require(value['automatic_retry'] is value['qualification_granted'] is False, 'Stopped scope changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Stopped worker lost ownership')
    require(ended['status'] == 'command-failed' and p.integer(ended['exit_code'], -2)
            and ended['stop_signals'] == [15] and ended['actual_command_started'] is True
            and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False,
            'Deliberate interruption was normalized')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Durable cleanup failed')
    same(p.process_identity(started['command_identity']), p.process_identity(ended['command_identity']),
         'Controller identity changed')
    for value in (launch, ended):
        same(p.process_identity(value['worker_identity']), p.process_identity(worker['worker_identity']),
             'Worker identity changed')
    require(started['command_pid'] == ended['command_pid'] == 2953 and worker['worker_identity']['pid'] == 2948
            and p.process_identity(started['command_identity'])[2] == ' '.join(command)
            and started['command_identity']['listing'].split(None, 2)[1] == '2948', 'Stopped owner differs')
    same(request['worker'], ended['worker_identity']['listing'], 'Stop worker differs')
    same(request['controller'], ended['command_identity']['listing'], 'Stop controller differs')
    require(p.timestamp(first['created_at']) <= p.timestamp(worker['started_at']) <= p.timestamp(started['started_at'])
            <= p.timestamp(request['created_at']) <= p.timestamp(ended['finished_at'])
            <= p.timestamp(closure['verified_at']), 'Stop chronology changed')


def cancelled_attempt(attempt, raw, wrapper, outer, request, closure):
    """Cancellation is preserved as an ownership event, never a timing sample."""
    same(attempt, wrapper, 'Report interrupted attempt differs from wrapper')
    fields = {'wrapper_native_registration', 'attempt', 'round', 'qualified', 'wrapper_supervisor_failure',
              'wrapper_error', 'wrapper_error_type', 'chart_admission'}
    same({k: v for k, v in wrapper.items() if k not in fields}, raw, 'Wrapper changed interrupted raw result')
    require(attempt['attempt'] == 15 and attempt['round'] == 1 and attempt['id'] == 'prolog-knucleotide-compact'
            and attempt['key'] == 'knucleotide:prolog-knucleotide-compact' and attempt['benchmark'] == 'knucleotide'
            and attempt['qualified'] is attempt['chart_admission'] is False
            and attempt['wrapper_supervisor_failure'] is True, 'Interrupted attempt was admitted')
    for prefix in ('', 'wrapper_'):
        require(attempt[prefix+'error_type'] == 'KeyboardInterrupt'
                and attempt[prefix+'error'] == 'Benchmark harness received signal 15', 'Stop is not a deadline')
    require(attempt['pins_unchanged_at_end'] is True and attempt['valid_environment'] is True
            and p.integer(attempt['exit_status'], -9) and not attempt.get('resource_violation'),
            'Interrupted environment or cleanup changed')
    for field in ('monitor_errors', 'resource_monitor_errors', 'competing_compilers', 'power_changes'):
        same(attempt[field], [], 'Interrupted monitor failure')
    require(not any(attempt.get(k) for k in ('cleanup_error', 'remaining_group_members', 'monitor_finish_error')),
            'Interrupted native group was not cleaned')
    active = request['active_before_signal']
    same(attempt['wrapper_native_registration'], active['native'], 'Cancelled native registration differs')
    native = {k: v for k, v in active['native'].items() if k != 'identity'}
    same(outer['native_registrations'], [native], 'Outer native registration differs')
    require(outer['status'] == 'failed' and outer['error_type'] == 'KeyboardInterrupt'
            and outer['error'] == attempt['error'] and outer['deadline_expired'] is False
            and outer['common_mutex_held_through_cleanup'] is True
            and outer['native_execute_unchanged'] is outer['native_validation_unchanged'] is True
            and p.integer(outer['deadline_seconds'], 22200) and p.integer(outer['native_timeout_seconds'], 21600)
            and p.integer(outer['common_mutex_fd']) and outer['common_mutex_fd'] >= 0,
            'Outer cancellation policy changed')
    same(outer['cleanup_errors'], [], 'Outer cleanup failure')
    same(outer['owned_sampler_children'], {'15240': dict(identity=active['sampler_identity'], reaped=True)},
         'Owned sampler was not reaped')
    same(outer['owned_groups'], {'15240': active['sampler_identity'], '15261': active['native']['identity']},
         'Recorded owned groups changed')
    same(outer['signals'], [dict(kind='direct-child', pid=15240, signal=15)], 'Unexpected cancellation signals')
    for pid, parent in ((15240, 2953), (15261, 15240)):
        identity = outer['owned_groups'][str(pid)]
        r.kernel_identity(identity, pid)
        require(identity['ppid'] == parent, 'Unowned cancellation child')
        recorded = request['identities'][str(pid)]
        same({k: identity[k] for k in ('pid', 'ppid', 'birth_seconds', 'birth_microseconds')},
             {k: recorded[k] for k in ('pid', 'ppid', 'birth_seconds', 'birth_microseconds')},
             'Process birth differs from the stop observation')
    same(closure['owned_processes_absent'], [2948, 2953, 15240, 15261], 'Closed process inventory differs')
    same(closure['owned_groups_empty'], [2948, 15240, 15261], 'Closed group inventory differs')


def stopped_prefix(plan, before, report, terminal, durable, request, closure, artifacts):
    """Pure boundary/receipt replay; the original forty remain separately sealed."""
    c.validate_partition(plan)
    stopped_durable(durable, request, closure)
    require(closure['schema'] == 'prolog-knucleotide-quadratic-stop-closure-v1'
            and closure['status'] == 'closed-deliberately-stopped-unqualified'
            and closure['deadline_expired'] is closure['interrupted_attempt_qualified'] is False
            and closure['automatic_retry'] is closure['chart_admission'] is False
            and closure['remaining_cohort_reconciliation_performed'] is False
            and closure['integrity_errors'] == [], 'Wrong deliberately closed boundary')
    for field, value in (('qualified_samples_preserved', 54), ('original_retained_samples', 40),
                         ('new_completed_samples_preserved', 14), ('interrupted_attempt', 15),
                         ('repeated_completed_samples', 0), ('signal_target', 2948)):
        require(p.integer(closure[field], value), 'Changed stop count: '+field)
    require(request['signal'] == 15 and request['signal_target'] == 2948
            and request['native_signal_sent_directly'] is request['timeout_claim'] is False
            and request['automatic_retry'] is request['qualification_granted'] is False
            and request['qualified_samples_before_signal'] == 54 and request['retained_qualified_samples'] == 40
            and request['new_qualified_samples'] == 14 and request['preserved_completed_attempts'] == list(range(1, 15)),
            'Wrong stop request')
    same(before['active'], request['active_before_signal'], 'Saved active checkpoint differs')
    require(before['status'] == 'running' and before['qualified_samples'] == 54, 'Wrong pre-stop checkpoint')
    same(before['attempts'], report['attempts'][:14], 'Completed attempts changed after stop')
    require(report['schema'] == c.SCHEMA and terminal['schema'] == 'prolog-linear-remaining50-terminal-v1'
            and report['status'] == terminal['status'] == 'stopped-unqualified' and report['active'] is None
            and report['error_type'] == 'KeyboardInterrupt' and report['error'] == 'Benchmark harness received signal 15'
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors'] == []
            and not report.get('terminal_integrity_errors'), 'Stopped producer closure failed')
    require(report['plan'] == str(PREVIOUS/'plan-v1.json') and report['plan_sha256'] == PREVIOUS_PLAN_SHA
            and terminal['report'] == str(PREVIOUS/'run-v1/report.json')
            and terminal['report_sha256'] == closure['controller_report_sha256'], 'Stopped report binding differs')
    same(terminal['prerequisite_pins'], merge(plan['pins'], {str(PREVIOUS/'plan-v1.json'): PREVIOUS_PLAN_SHA}),
         'Stopped prerequisite closure differs')
    require(closure['prerequisite_pins_verified'] == len(terminal['prerequisite_pins'])
            and closure['terminal_artifacts_verified'] == len(terminal['available_evidence_pins']),
            'Closed inventory count differs')
    require(terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134
            and terminal['original_files_mutated'] is False and terminal['new_qualified_samples'] == 14,
            'Stopped mutex/new-sample policy differs')
    for value in (report, terminal):
        for field, expected in (('qualified_samples', 54), ('retained_qualified_samples', 40),
                                ('saved_attempts', 15), ('full_performance_runs', 15)):
            require(p.integer(value[field], expected), 'Stopped native ledger differs')
        require(value['common_mutex_held_continuously'] is True
                and value['full_timings_qualified'] is value['chart_admission'] is False,
                'Stopped measurement scope differs')
        same(value['registered_native_attempts'], list(range(1, 16)), 'Missing registered native attempt')
        same(value['native_launch_unconfirmed_attempts'], [], 'Unconfirmed native launch')
        same(value['skipped_failed_profile_slots'], [], 'Unexplained skipped slot')
    require(report['isolated_failed_profiles'] == [] and report['no_automatic_retry'] is True
            and report['repeated_completed_samples'] == 0, 'Cancellation was an isolated benchmark failure')
    same(report['completed_benchmarks'], f.BENCHES[:6], 'Stopped workload boundary differs')
    same(report['reused_samples'], plan['retained']['reused_samples'], 'Original forty observations changed')
    require(len(report['attempts']) == len(report['independent_supervisors']) == 15, 'Stopped receipt count differs')
    rows = c.initial_rows(plan)
    reused = copy.deepcopy(plan['retained']['reused_samples'])
    provenance, gaps, snapshots, last = [], [], {}, None
    pins = fingerprint_pins(plan, terminal['prerequisite_pins'])
    for index, (slot, attempt) in enumerate(zip(plan['remaining_slots'][:14], report['attempts'][:14]), 1):
        require(attempt['attempt'] == index and attempt['qualified'] is True, 'Stopped prefix contains a failed sample')
        paths = attempt_paths(PREVIOUS/'run-v1', attempt)
        require(attempt['result_path'] == str(paths[0]) and attempt['supervisor_result_path'] == str(paths[1]),
                'Stopped receipt path changed')
        row = rows[slot[3]]; manifest = plan['manifests'][slot[0]]
        begin, end = r.check_attempt(attempt, artifacts[str(paths[0])], artifacts[str(paths[1])],
                                    slot, row, manifest, pins, provenance)
        require(last is None or last <= begin, 'Stopped samples overlap'); last = end
        gaps.extend(r.check_outer(artifacts[str(paths[2])], attempt, 2953))
        for path in paths:
            snapshots[str(path)] = terminal['available_evidence_pins'][str(path)]
        same(report['independent_supervisors'][index-1],
             dict(path=str(paths[2]), sha256=snapshots[str(paths[2])], status='returned'), 'Outer receipt reference differs')
        row['attempts'].append(index); row['samples_seconds'].append(attempt['seconds'])
        row['sample_validation'].append(attempt['validation'])
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        reused.append(dict(slot=slot, original_attempt=index, cohort='linear-remaining50',
            original_report=str(PREVIOUS/'run-v1/report.json'), original_report_sha256=closure['controller_report_sha256'],
            raw=str(paths[0]), raw_sha256=snapshots[str(paths[0])], supervised=str(paths[1]),
            supervised_sha256=snapshots[str(paths[1])], outer=str(paths[2]), outer_sha256=snapshots[str(paths[2])],
            seconds=attempt['seconds'], validation=attempt['validation']))
    for manifest in plan['manifests'].values(): summarize(rows, manifest)
    cancelled = report['attempts'][14]; key = cancelled['key']
    rows[key]['attempts'].append(15); rows[key]['measurement_status'] = 'stopped-unqualified'
    same(report['programs'], rows, 'Stopped summaries do not replay actual observations')
    same(snapshots, closure['completed_artifacts_unchanged'], 'Completed checkpoint hashes differ')
    same(snapshots, report['validated_attempt_artifacts'], 'Stopped validated snapshots differ')
    same(provenance, report['descriptive_provenance'], 'Stopped descriptive evidence differs')
    same(gaps, report['kernel_identity_observation_gaps'], 'Stopped identity observations differ')
    raw, _, outer = attempt_paths(PREVIOUS/'run-v1', cancelled)
    wrapper = raw.with_suffix('.wrapper.json')
    cancelled_attempt(cancelled, artifacts[str(raw)], artifacts[str(wrapper)], artifacts[str(outer)], request, closure)
    same(report['independent_supervisors'][-1], dict(path=str(outer),
         sha256=terminal['available_evidence_pins'][str(outer)], status='failed'), 'Interrupted outer binding differs')
    expected = set(snapshots) | {str(raw), str(wrapper), str(outer)}
    require(set(artifacts) == expected, 'Extra/missing stopped process receipt')
    require(set(terminal['available_evidence_pins']) == expected | {str(PREVIOUS/'run-v1/report.json'),
         str(PREVIOUS/'run-v1/error.log')}, 'Unregistered stopped artifact')
    require(p.timestamp(report['started_at']) <= p.timestamp(report['attempts'][0]['started_at'])
            <= last <= p.timestamp(cancelled['started_at']) <= p.timestamp(request['created_at'])
            <= p.timestamp(cancelled['finished_at']) <= p.timestamp(report['finished_at'])
            <= p.timestamp(durable['terminal']['finished_at']), 'Stopped process chronology differs')
    return dict(reused_samples=reused, completed_benchmarks=f.BENCHES[:6], reused_native_processes=54,
        excluded_attempts=[dict(report=str(PREVIOUS/'run-v1/report.json'), attempt=15,
                               disposition='deliberately-stopped-unqualified')],
        stopped_report=dict(path=str(PREVIOUS/'run-v1/report.json'), sha256=closure['controller_report_sha256']),
        stop_review=dict(path=str(STOP/'closure.json'), sha256=CLOSURE_SHA),
        descriptive_provenance=provenance, kernel_identity_observation_gaps=gaps)


def retained_prerequisite(pins):
    plan = read(pins, PREVIOUS/'plan-v1.json', PREVIOUS_PLAN_SHA)
    same(plan, c.build_plan(PREVIOUS/'run-v1'), 'Original fifty-slot plan no longer replays')
    pins.update(merge(pins, plan['pins']))
    closure = read(pins, STOP/'closure.json', CLOSURE_SHA)
    report = read(pins, PREVIOUS/'run-v1/report.json', closure['controller_report_sha256'])
    terminal = read(pins, PREVIOUS/'run-v1/terminal.json', closure['controller_terminal_sha256'])
    request = read(pins, STOP/'request.json', closure['request_sha256'])
    before = read(pins, STOP/'before-report.json', closure['before_report_sha256'])
    sent = read(pins, STOP/'signal-sent.json', closure['signal_sent_sha256'])
    require(sent['signal'] == 15 and sent['target'] == 2948 and sent['automatic_retry'] is False
            and sent['request_sha256'] == closure['request_sha256'], 'Actual signal receipt differs')
    durable = {name: read(pins, JOB/(name+'.json'), closure['durable_terminal_sha256'] if name == 'terminal'
                         else sha(regular(JOB/(name+'.json')))) for name in
               ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
    inventory = l.file_inventory(PREVIOUS/'run-v1', exclude=('terminal.json',))
    same(inventory, terminal['available_evidence_pins'], 'Stopped artifact inventory changed')
    pins.update(merge(pins, inventory))
    artifacts = {path: read(pins, path, digest) for path, digest in inventory.items()
                 if '/attempts/' in path or '/outer-supervisor/' in path}
    retained = stopped_prefix(plan, before, report, terminal, durable, request, closure, artifacts)
    inventories = {}
    for directory, terminal_sha in (
            (l.OLD/'results', l.FIXED[l.OLD/'results/terminal.json']),
            (c.PRIOR/'run-v1', c.FIXED[c.PRIOR/'run-v1/terminal.json']),
            (PREVIOUS/'run-v1', closure['controller_terminal_sha256'])):
        closed = read(pins, directory/'terminal.json', terminal_sha)
        expected = dict(closed['available_evidence_pins'])
        expected[str(directory/'terminal.json')] = terminal_sha
        same(l.file_inventory(directory), expected, 'Retained directory inventory differs')
        inventories[str(directory)] = expected
    return plan, retained, inventories


REPLACED = frozenset(('source', 'source_sha256', 'measured_source', 'source_bundle', 'command', 'cwd',
    'compiled_artifact', 'compiler_bound_input_inventory', 'required_work_review', 'source_count_review',
    'canonical_source_projection', 'loc', 'canonical_loc', 'physical_loc', 'formatted_loc',
    'source_alias_of', 'optimization_claim'))


def packet_path(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(SOURCE),
            'Replacement evidence outside its packet')
    return path


def qualification_checks(value, old_profiles):
    require(value['schema'] == 'prolog-knucleotide-linear-qualified-v1'
            and value['status'] == 'qualified-source-work-and-canonical-counts-awaiting-full-timing',
            'Actual independently qualified replacement is required')
    for flag in ('bounded_outputs_qualified', 'compiled_inputs_qualified', 'source_work_qualified', 'canonical_LOC_admitted'):
        require(value[flag] is True, 'Pending replacement qualification: '+flag)
    require(value['full_timings_qualified'] is value['chart_admission'] is False, 'Replacement claims unmeasured timings')
    pins = value['pins']
    require(type(pins) is dict and all(Path(k).is_absolute() and p.digest(v) for k, v in pins.items()),
            'Replacement pins are malformed')
    require(all(pins.get(path) == digest for path, digest in SOURCES.items()), 'Missing exact authored source pins')
    require(set(value['evidence']) == {'compilation', 'bounded', 'source_counts', 'required_work'},
            'Missing independent replacement evidence')
    for ref in value['evidence'].values():
        packet_path(ref['path']); require(pins.get(ref['path']) == ref['sha256'], 'Unpinned qualification evidence')
    require(type(value['artifact_inventories']) is dict and bool(value['artifact_inventories']),
            'Closed native artifact inventories required')
    for directory, inventory in value['artifact_inventories'].items():
        packet_path(directory)
        require(type(inventory) is dict and bool(inventory), 'Empty artifact closure')
        for relative, digest in inventory.items():
            path = Path(relative)
            require(not path.is_absolute() and '..' not in path.parts and path.parts and p.digest(digest)
                    and pins.get(str(Path(directory)/path)) == digest, 'Unpinned/escaped native artifact')
    profiles = value['profiles']
    require(type(profiles) is list and len(profiles) == 2, 'Exactly two existing source aliases required')
    for index, (row, old) in enumerate(zip(profiles, old_profiles)):
        same({k: v for k, v in row.items() if k not in REPLACED},
             {k: v for k, v in old.items() if k not in REPLACED}, 'Replacement changed unrelated profile policy')
        require(row['source_sha256'] == SOURCE_SHA and row['source'] in SOURCES
                and SOURCES[row['source']] == SOURCE_SHA and row.get('formatted_loc') is None,
                'Replacement main identity/formatted count differs')
        require(pins.get(row['binary']) == row['binary_sha256'], 'Replacement runtime unpinned')
        bundle = row['source_bundle']
        require(len(bundle) == 3 and len({v['path'] for v in bundle}) == 3
                and {v['origin'] for v in bundle} == {row['source'], str(SOURCE/'support/clbg_io.pl'),
                                                       str(SOURCE/'support/clbg_records.pl')}, 'Incomplete three-file bundle')
        for entry in bundle:
            packet_path(entry['path'])
            require(pins.get(entry['path']) == SOURCES[entry['origin']] == entry['sha256']
                    and p.integer(entry['normalized_loc']) and entry['normalized_loc'] > 0
                    and p.integer(entry['physical_loc']) and entry['physical_loc'] > 0, 'Unqualified source/count binding')
        primary = next(e for e in bundle if e['origin'] == row['source'])
        require(row['measured_source'] == primary['path'] and row['loc'] == row['canonical_loc']
                == sum(e['normalized_loc'] for e in bundle)
                and row['physical_loc'] == sum(e['physical_loc'] for e in bundle), 'Bundle count/primary mismatch')
        by_name = {Path(e['origin']).name: Path(e['path']).with_suffix('.qlf') for e in bundle}
        qlf = Path(primary['path']).with_suffix('.qlf')
        require(row['compiled_artifact']['path'] == str(qlf)
                and row['compiled_artifact']['sha256'] == pins.get(str(qlf))
                and p.integer(row['compiled_artifact']['bytes']) and row['compiled_artifact']['bytes'] > 0,
                'Unbound compiled main')
        require(all(p.digest(pins.get(str(path))) for path in by_name.values()), 'Unpinned helper QLF')
        same(row['command'], [old['binary'], '-q', '-O', '-f', 'none', '--stack-limit=8g', '-l',
             str(by_name['clbg_io.pl']), '-l', str(by_name['clbg_records.pl']), '-s', str(qlf),
             '-g', 'clbg_io:run(clbg_knucleotide:main)'], 'Changed direct runtime invocation')
        packet_path(row['cwd'])
        require(row['cwd'] == str(Path(primary['path']).parents[2])
                and by_name['clbg_io.pl'] == Path(row['cwd'])/'support/clbg_io.qlf'
                and by_name['clbg_records.pl'] == Path(row['cwd'])/'support/clbg_records.qlf',
                'Compiled input root/helper layout differs')
        for name in ('compiler_bound_input_inventory', 'required_work_review', 'source_count_review', 'canonical_source_projection'):
            ref = row[name]; packet_path(ref['path'])
            require(pins.get(ref['path']) == ref['sha256'], 'Unpinned profile proof: '+name)
        for profile_field, evidence_field in (('required_work_review', 'required_work'), ('source_count_review', 'source_counts')):
            same({k: row[profile_field][k] for k in ('path', 'sha256')}, value['evidence'][evidence_field],
                 'Independent profile qualification differs')
        require(row['required_work_review']['status'] == 'passed'
                and row['compiler_bound_input_inventory']['status'] == 'qualified-exact-authored-compiler-inputs',
                'Compiled input/work disposition missing')
        require(row['source_alias_of'] == (old_profiles[0]['id'] if index else None), 'Alias identity differs')
    require(profiles[1]['optimization_claim'] == 'explicit equivalent-source alias; no distinct optimization admitted',
            'Identical sources presented as distinct optimization')
    for field in ('binary', 'binary_sha256', 'runtime_environment', 'canonical_loc', 'physical_loc'):
        same(profiles[0][field], profiles[1][field], 'Alias execution differs: '+field)


def qualification_prerequisite(path, digest, old_profiles, pins):
    packet_path(path)
    value = read(pins, path, digest)
    qualification_checks(value, old_profiles)
    for name, expected in value['pins'].items():
        regular(name); c.bind(pins, name, expected)
    for directory, expected in value['artifact_inventories'].items():
        actual = {str(Path(path).relative_to(directory)): digest for path, digest in l.file_inventory(Path(directory)).items()}
        same(actual, expected, 'Qualified native artifact closure changed')
    for row in value['profiles']:
        require(regular(row['compiled_artifact']['path']).stat().st_size == row['compiled_artifact']['bytes'],
                'Compiled artifact size changed')
    return value


def validate_partition(plan):
    slots = l.schedule_for(plan['manifests'])
    same(plan['schedule'], slots, 'Combined rotation changed')
    same(plan['retained_slots'], slots[:54], 'Retained54 slots changed')
    same(plan['remaining_slots'], slots[54:], 'Remaining36 slots changed')
    same([s['slot'] for s in plan['retained']['reused_samples']], slots[:54], 'Retained observation order changed')
    for key, value in (('samples', 3), ('full_processes', 36), ('retained_qualified_samples', 54),
                       ('new_prolog_processes', 24), ('new_mech_processes', 12), ('combined_sample_slots', 90)):
        require(p.integer(plan[key], value), 'Continuation count differs: '+key)


def build_plan(output, qualification, qualification_sha256):
    pins = {str(Path(__file__).resolve()): sha(__file__),
            str(ROOT/'tools/qualification/prolog_remaining_full.py'): PREVIOUS_CONTROLLER_SHA}
    # Reject an absent or pending replacement before the expensive old closure.
    packet_path(qualification)
    preliminary = read(pins, qualification, qualification_sha256)
    require(preliminary['status'] == 'qualified-source-work-and-canonical-counts-awaiting-full-timing'
            and all(preliminary.get(flag) is True for flag in ('bounded_outputs_qualified',
                'compiled_inputs_qualified', 'source_work_qualified', 'canonical_LOC_admitted')),
            'Replacement is not actually qualified')
    old, retained, inventories = retained_prerequisite(pins)
    q = qualification_prerequisite(qualification, qualification_sha256,
                                  old['manifests']['knucleotide']['profiles'][:2], pins)
    manifests = copy.deepcopy(old['manifests'])
    manifests['knucleotide']['profiles'][:2] = copy.deepcopy(q['profiles'])
    slots = l.schedule_for(manifests)
    same(slots, old['schedule'], 'Replacement changed original slot identities')
    result = dict(schema=SCHEMA, status='prepared-awaiting-independent-review', repository=str(ROOT),
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), output=str(output),
        qualification=dict(path=str(qualification), sha256=qualification_sha256),
        pins=pins, historical_pins=old['historical_pins'], retained=retained,
        retained_artifact_inventories=inventories,
        linear_qualification=old['linear_qualification'], knucleotide_qualification=q,
        manifests=manifests, schedule=slots, retained_slots=slots[:54], remaining_slots=slots[54:],
        samples=3, full_processes=36, combined_sample_slots=90, retained_qualified_samples=54,
        new_prolog_processes=24, new_mech_processes=12, source_work_profiles=20, canonical_loc_profiles=20,
        shared_timing_lock=str(f.LOCK), common_mutex_held_continuously=True, no_automatic_retry=True,
        compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0,
        repeated_completed_samples=0, original_files_mutated=False, full_timings_qualified=False,
        chart_admission=False, timing_policy=old['timing_policy'])
    validate_partition(result); f.verify(pins); verify_input_inventories(result)
    return result


def verify_input_inventories(plan):
    for directory, expected in plan['retained_artifact_inventories'].items():
        same(l.file_inventory(Path(directory)), expected, 'Retained artifact inventory changed')
    for directory, expected in plan['knucleotide_qualification']['artifact_inventories'].items():
        actual = {str(Path(path).relative_to(directory)): digest
                  for path, digest in l.file_inventory(Path(directory)).items()}
        same(actual, expected, 'Replacement artifact inventory changed')


def initial_rows(plan):
    validate_partition(plan)
    rows = {row['key']: dict(copy.deepcopy(row), samples_seconds=[], sample_validation=[], attempts=[],
                            retained_attempts=[], measurement_status='pending')
            for manifest in plan['manifests'].values() for row in manifest['profiles']}
    require(len(rows) == 30, 'Wrong profile inventory')
    for sample in plan['retained']['reused_samples']:
        row = rows[sample['slot'][3]]
        row['samples_seconds'].append(sample['seconds']); row['sample_validation'].append(copy.deepcopy(sample['validation']))
        row['retained_attempts'].append(dict(cohort=sample['cohort'], attempt=sample['original_attempt'],
            report=sample['original_report'], report_sha256=sample['original_report_sha256']))
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
    same([bench for bench in f.BENCHES if summarize(rows, plan['manifests'][bench])],
         plan['retained']['completed_benchmarks'], 'Retained group completeness differs')
    return rows


def check_success_ledger(plan, report):
    rows = initial_rows(plan); failed = []; skipped = []; index = 0
    for slot in plan['remaining_slots']:
        bench, round_, identifier, key = slot; row = rows[key]
        if row.get('full_failure'):
            skipped.append(dict(benchmark=bench, round=round_, id=identifier, key=key)); continue
        require(index < len(report['attempts']), 'Missing unfinished slot')
        attempt = report['attempts'][index]; index += 1
        require(p.integer(attempt['attempt'], index), 'Repeated/out-of-order attempt')
        same([attempt[k] for k in ('benchmark', 'round', 'id', 'key')], slot, 'Repeated/reordered native slot')
        row['attempts'].append(index)
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        else:
            row['full_failure'] = attempt; row['measurement_status'] = 'failed-full-workload'; failed.append(key)
    require(index == len(report['attempts']) and index+len(skipped) == 36, 'Unaccounted remaining slot')
    for manifest in plan['manifests'].values(): require(summarize(rows, manifest), 'Missing workload summary')
    same(report['programs'], rows, 'Summary does not replay preserved/new observations')
    same(report['isolated_failed_profiles'], failed, 'Failed profile ledger differs')
    same(report['skipped_failed_profile_slots'], skipped, 'Skipped slot lacks earlier failure')
    require(report['active'] is None and report['completed_benchmarks'] == f.BENCHES
            and report['native_launch_unconfirmed_attempts'] == [] and report['full_performance_runs'] == index
            and report['qualified_samples'] == sum(len(row['samples_seconds']) for row in rows.values())
            and report['retained_qualified_samples'] == 54 and report['repeated_completed_samples'] == 0,
            'Incomplete native/accounting closure')
    same(report['registered_native_attempts'], list(range(1, index+1)), 'Native registration changed')


def finish(plan, report, pins, snapshots, guard, lock):
    errors = []
    held = False
    f.refresh_attempt_accounting(report)
    try:
        f.verify(merge(pins, snapshots))
        require(report['active'] is None, 'Active native attempt after cleanup')
        if report['status'] in ('complete', 'complete-with-unqualified-profiles'):
            check_success_ledger(plan, report)
            expected = {}; previous = None
            for attempt in report['attempts']:
                slot = [attempt[k] for k in ('benchmark', 'round', 'id', 'key')]
                manifest = plan['manifests'][slot[0]]
                row = next(row for row in manifest['profiles'] if row['key'] == slot[3])
                new, _, _ = c.check_new_attempt(guard.OUT, attempt, slot, row, manifest,
                                               fingerprint_pins(plan, pins), os.getpid())
                expected.update(merge(expected, new))
                begin, end = p.timestamp(attempt['started_at']), p.timestamp(attempt['finished_at'])
                require(previous is None or previous <= begin, 'Overlapping native attempts'); previous = end
            same(snapshots, expected, 'Validated receipt closure differs')
            observed = {str(path) for name in ('attempts', 'outer-supervisor')
                        for path in (guard.OUT/name).rglob('*') if path.is_file()}
            require(observed == set(expected), 'Missing or unregistered native receipt')
        verify_lease(lock, f.LOCK, 79859134)
        held = True
    except BaseException as error:
        errors.append(dict(error=str(error) or type(error).__name__, error_type=type(error).__name__))
    report.update(pins_unchanged_at_end=not errors, validated_attempt_artifacts=snapshots)
    if errors: report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors)
    guard.save(guard.REPORT, report)
    expected_report = hashlib.sha256((json.dumps(report, indent=2)+'\n').encode()).hexdigest()
    artifacts = {}
    try:
        artifacts = l.file_inventory(guard.OUT)
        require(artifacts.get(str(guard.REPORT)) == expected_report, 'Serialized report changed during snapshot')
        require(all(artifacts.get(path) == digest for path, digest in snapshots.items()), 'Validated artifact changed')
        f.verify(pins)
        verify_input_inventories(plan)
        same(l.file_inventory(guard.OUT), artifacts, 'Output changed during final pin replay')
        held = False
        verify_lease(lock, f.LOCK, 79859134)
        held = True
    except BaseException as error:
        errors.append(dict(error=str(error) or type(error).__name__, error_type=type(error).__name__))
        report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors, pins_unchanged_at_end=False)
        guard.save(guard.REPORT, report); artifacts[str(guard.REPORT)] = sha(guard.REPORT)
    f.new_json(guard.OUT/'terminal.json', dict(schema='prolog-knucleotide-remaining36-terminal-v1', status=report['status'],
        report=str(guard.REPORT), report_sha256=sha(guard.REPORT), prerequisite_pins=pins, available_evidence_pins=artifacts,
        integrity_errors=errors, common_mutex_held=held, common_mutex_held_continuously=held, common_mutex_inode=79859134,
        full_performance_runs=report['full_performance_runs'], saved_attempts=len(report['attempts']),
        registered_native_attempts=report['registered_native_attempts'],
        native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
        qualified_samples=report['qualified_samples'], retained_qualified_samples=54,
        new_qualified_samples=report['qualified_samples']-54, skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
        compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0,
        repeated_completed_samples=0, original_files_mutated=False, full_timings_qualified=False, chart_admission=False))
    require(not errors, 'Terminal integrity failed; actual observations retained')


def fresh_paths(plan, output):
    require(plan.is_relative_to(PACKET) and output.is_relative_to(PACKET) and not plan.is_relative_to(output)
            and not output.is_relative_to(plan) and not plan.exists() and not output.exists(),
            'Fresh separate plan/output paths required')


def prepare(args):
    plan_path, output = args.plan.resolve(), args.output.resolve()
    fresh_paths(plan_path, output)
    plan = build_plan(output, args.qualification.resolve(), args.qualification_sha256)
    fresh_paths(plan_path, output); f.new_json(plan_path, plan)
    print(json.dumps(dict(plan=str(plan_path), sha256=sha(plan_path), full_processes=36,
                         retained_qualified_samples=54, native_executions=0)), flush=True)


def run(args, lock):
    plan_path = args.plan.resolve(); require(plan_path.is_relative_to(PACKET), 'Plan outside continuation packet')
    pins = {}; plan = read(pins, plan_path, args.plan_sha256); output = Path(plan['output'])
    require(output.is_absolute() and output.resolve() == output and output.is_relative_to(PACKET)
            and not plan_path.is_relative_to(output) and not output.exists(), 'Fresh output required')
    q = plan['qualification']
    same(plan, build_plan(output, Path(q['path']), q['sha256']), 'Plan no longer replays its exact qualified inputs')
    pins = merge(plan['pins'], pins)
    resolver = f.Resolver(); resolver.logical = dict(plan['historical_pins'])
    guard, harness = f.load_measurement(resolver)
    require(all(pins.get(path) == digest for path, digest in resolver.active.items()), 'Frozen sampler pins changed')
    supervisor = f.cold(f.SUPERVISOR, c.SUPERVISOR_SHA, 'knucleotide36_owned_supervisor')
    manifests = {bench: dict(value, pins=pins) for bench, value in plan['manifests'].items()}
    for bench, manifest in manifests.items():
        require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                and manifest['maximum_rss_mib'] == 10240, 'Native workload/resource policy changed')
    output.mkdir(parents=True); guard.OUT, guard.REPORT = output, output/'report.json'
    harness.install_interrupt_handlers(); rows = initial_rows(plan)
    report = dict(schema=SCHEMA, status='running', started_at=guard.now(), supervisor=guard.identity(os.getpid()),
        plan=str(plan_path), plan_sha256=args.plan_sha256, programs=rows, attempts=[], active=None,
        reused_samples=plan['retained']['reused_samples'], retained_qualified_samples=54,
        benchmark_order=f.BENCHES, completed_benchmarks=copy.deepcopy(plan['retained']['completed_benchmarks']),
        sample_count=3, full_performance_runs=0, skipped_failed_profile_slots=[], isolated_failed_profiles=[],
        shared_timing_lock=str(f.LOCK), common_mutex_held_continuously=True, source_work_profiles=20,
        canonical_loc_profiles=20, chart_admission=False, full_timings_qualified=False, no_automatic_retry=True,
        repeated_completed_samples=0, kernel_identity_observation_gaps=[], descriptive_provenance=[])
    snapshots = {}; f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
    try:
        for slot in plan['remaining_slots']:
            bench, round_, identifier, key = slot; row, manifest = rows[key], manifests[bench]
            if row.get('full_failure'):
                report['skipped_failed_profile_slots'].append(dict(benchmark=bench, round=round_, id=identifier, key=key))
                guard.save(guard.REPORT, report); continue
            f.verify(pins); verify_input_inventories(plan)
            harness.compact.wait_for_environment(harness.REQUIRED)
            print('PROLOG REMAINING36', bench, round_, identifier, manifest['size'], flush=True)
            previous = len(report['attempts'])
            try:
                attempt = supervisor.one_attempt(guard, harness, row, manifest, report, round_, lock.fileno())
                with supervisor.lifecycle_atomic():
                    report['attempts'].append(attempt); report['active'] = None; row['attempts'].append(attempt['attempt'])
                    f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
            except BaseException as error:
                with supervisor.lifecycle_atomic():
                    if len(report['attempts']) == previous: f.preserve_wrapper_failure(guard, report, row, round_, error)
                raise
            original = next(profile for profile in manifest['profiles'] if profile['key'] == key)
            captured, provenance, gaps = c.check_new_attempt(output, attempt, slot, original, manifest,
                                                            fingerprint_pins(plan, pins), os.getpid())
            with supervisor.lifecycle_atomic():
                snapshots.update(merge(snapshots, captured)); report['descriptive_provenance'].extend(provenance)
                report['kernel_identity_observation_gaps'].extend(gaps)
                if attempt['qualified']:
                    f.qualified_sample(attempt, manifest, row, harness.execution_fingerprint(row))
                    row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                    row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
                elif f.isolated_failure(guard, attempt):
                    row['full_failure'] = dict(attempt); row['measurement_status'] = 'failed-full-workload'
                    report['isolated_failed_profiles'].append(key)
                else: row['measurement_status'] = 'stopped-unqualified'
                f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
                require(attempt['qualified'] or row.get('full_failure'), 'Integrity/ownership failure; no retry')
                if summarize(rows, manifest) and bench not in report['completed_benchmarks']:
                    report['completed_benchmarks'].append(bench)
                guard.save(guard.REPORT, report)
        check_success_ledger(plan, report)
        report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                      finished_at=guard.now())
    except BaseException as error:
        report.update(status='stopped-unqualified', finished_at=guard.now(), error=str(error) or type(error).__name__,
                      error_type=type(error).__name__)
        (output/'error.log').write_text(traceback.format_exc()); raise
    finally:
        with supervisor.lifecycle_atomic(): finish(plan, report, pins, snapshots, guard, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__); modes = parser.add_subparsers(dest='mode', required=True)
    prep = modes.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True); prep.add_argument('--qualification', type=Path, required=True)
    prep.add_argument('--qualification-sha256', required=True)
    execute = modes.add_parser('run'); execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True); args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == f.PYTHON.resolve(), 'Use pinned Python -I -S -B without -O')
    def interrupted(signum, frame): raise KeyboardInterrupt('Prolog remaining36 interrupted: '+str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP): signal.signal(signum, interrupted)
    with owned_locks() as lock:
        prepare(args) if args.mode == 'prepare' else run(args, lock)


if __name__ == '__main__': main()
