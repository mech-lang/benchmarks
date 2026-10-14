"""Independently reconcile a completed Pony full90 study, without native execution.

The pure checks below import neither the sampler nor the continuation controller.
``review_files`` additionally checks pinned bytes under the common mutex. Call it
only after the durable job has ended, with the independently retained plan hash.
It returns metadata for review; it never publishes, changes an old receipt, runs
a benchmark, or grants runtime/chart admission.

Limits: successful stdout was validated and hashed by the frozen sampler, then
discarded. Raw JSON is preserved, not complete stdout. N-body energies can be
rechecked numerically but its output byte stream cannot be reconstructed here.
RSS is the sampler's observed process-group peak, not an unsampled maximum.
Source-work/LOC proofs and runtime publication still require their own reviewed
closures; verifying their pinned bytes does not replace semantic review.
"""
from datetime import datetime
import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import posixpath
from pathlib import Path
import sys


BENCHES = ('regexredux', 'revcomp', 'pidigits', 'spectralnorm', 'mandelbrot',
           'fasta', 'knucleotide', 'binarytrees', 'nbody', 'fannkuchredux')
SIZES = dict(zip(BENCHES, (5000000, 25000000, 10000, 5500, 16000,
                         25000000, 25000000, 21, 50000000, 12)))
PONY_IDS = {
    'regexredux': ('pony-regexredux-compact', 'pony-regexredux-optimized'),
    'revcomp': ('pony-revcomp-compact', 'pony-revcomp-optimized'),
    'pidigits': ('pony-pidigits-compact', 'pony-pidigits-optimized'),
    'spectralnorm': ('pony-spectralnorm-compact', 'pony-spectralnorm-optimized'),
    'mandelbrot': ('pony-mandelbrot-compact', 'pony-mandelbrot-optimized'),
    'fasta': ('pony-fasta-compact', 'pony-fasta-optimized'),
    'knucleotide': ('pony-knucleotide-compact-precedence-v4', 'pony-knucleotide-optimized-shift-types-v5'),
    'binarytrees': ('pony-binarytrees-compact-precedence-v4', 'pony-binarytrees-optimized-precedence-v4'),
    'nbody': ('pony-nbody-compact', 'pony-nbody-optimized'),
    'fannkuchredux': ('pony-fannkuchredux-compact', 'pony-fannkuchredux-optimized'),
}
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
RETAINED_SHA = '24eec56b10bead949ffa7c182500a8b930829c322c4ee612bf88ad756ac85ef4'
RETAINED_TERMINAL_SHA = 'ec1b22744664932c287693ff0bf030d158adeb0423e83374631356b63fc26842'
OLD_STUDY = ('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg/pony-comparison/'
             '20261012/full-studies/pony-retained20-full-v1')
OLD_RESUMED = OLD_STUDY.replace('pony-retained20-full-v1', 'pony-retained20-resumed-v1')
HOST_CLBG = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
# Direct algorithm.evidence entries describe optimization history. They are
# preserved exactly by the frozen fingerprint, but are not execution inputs.
# Any alias of an actual source/binary/helper/runtime dependency stays strict.
UPSTREAM_RUST_SHA = 'fb6b33b1bf74612f8ce78d19e70f10f41650b02b72e4c73d2cb0480508fbef65'
SUPERVISOR_FIELDS = frozenset(('round', 'attempt', 'sampler_wait_status', 'result_path',
    'supervised_native_group', 'supervisor_remaining_members', 'qualification_checks',
    'qualified', 'supervisor_result_path'))
CHECKS = frozenset(('sampler_exited_normally', 'authoritative_native_group_received',
    'native_inherited_common_mutex', 'native_exited_normally', 'no_execution_error',
    'no_wrapper_integrity_error', 'no_resource_violation', 'no_resource_monitor_errors',
    'no_compiler_power_monitor_errors', 'no_monitor_finish_error', 'no_execute_cleanup_error',
    'no_remaining_execute_group', 'no_supervisor_cleanup', 'no_supervisor_remaining_group',
    'valid_environment', 'actual_full_workload', 'exact_command_and_group',
    'complete_output_reference_match', 'complete_output_bytes_and_hash', 'pins_unchanged'))
ERROR_FIELDS = ('error', 'error_type', 'sampler_failure', 'sampler_error',
    'registration_error', 'supervisor_error', 'supervisor_pin_failure', 'resource_violation',
    'monitor_finish_error', 'cleanup_error', 'supervisor_cleanup',
    'execution_failure_before_sampler_error', 'execution_failure_before_supervisor_error')
EMPTY_LIST_FIELDS = ('remaining_group_members', 'supervisor_remaining_members',
    'competing_compilers', 'power_changes', 'monitor_errors', 'resource_monitor_errors')
AGGREGATE_FIELDS = frozenset(('attempts', 'samples_seconds', 'sample_validation',
    'full_validation', 'measurement_status', 'qualification_status', 'median_seconds',
    'sample_stdev_seconds'))


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    """Type-sensitive equality: JSON true must never equal the integer one."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def same(left, right, message):
    require(canonical(left) == canonical(right), message)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: '+key)
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError('Nonfinite JSON number: '+value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def integer(value, expected=None):
    return type(value) is int and (expected is None or value == expected)


def finite(value, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def timestamp(value):
    require(type(value) is str, 'Timestamp missing')
    parsed = datetime.fromisoformat(value)
    require(parsed.utcoffset() is not None, 'Timestamp lacks timezone')
    return parsed


def schedule(plan):
    require(plan['schema'] == 'pony-retained54-migration-plan-v1', 'Wrong plan schema')
    require(set(plan['manifests']) == set(BENCHES), 'Ten canonical manifests required')
    slots, profiles = [], {}
    for benchmark in BENCHES:
        m = plan['manifests'][benchmark]
        require(m['benchmark'] == benchmark and integer(m['size'], SIZES[benchmark])
                and integer(m['samples'], 3) and integer(m['required_processes'], 9), 'Changed workload')
        require(m['canonical_full_workload'] is True and integer(m['timeout_seconds'], 14400)
                and integer(m['maximum_rss_mib'], 10240) and integer(m['maximum_compute_workers'], 8),
                'Changed measurement limits')
        same(m['required_power_profile'], {'source': 'AC Power', 'low_power_mode': 0}, 'Changed power policy')
        require(m['chart_admission'] is False and m['runtime_publication_metadata_qualified'] is False,
                'Measurement manifest cannot grant publication')
        rows = m['profiles']
        ids = [*PONY_IDS[benchmark], 'mech-'+benchmark+'-control']
        require(len(rows) == 3 and [r['id'] for r in rows] == ids
                and [r['language'] for r in rows] == ['pony', 'pony', 'mech'], 'Wrong measured cohort')
        same(m['orders'], [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)], 'Changed rotation')
        for r in rows:
            require(r['key'] not in profiles and r['benchmark'] == benchmark, 'Duplicate profile key')
            require(digest(r['source_sha256']) and digest(r['binary_sha256']), 'Missing source/binary binding')
            if r['language'] == 'pony':
                require(r['command'][1:] == ['{n}', '--ponymaxthreads', '8']
                        and integer(r['maximum_compute_actors']) and 1 <= r['maximum_compute_actors'] <= 8,
                        'Pony worker command changed')
            profiles[r['key']] = r
        by_id = {r['id']: r['key'] for r in rows}
        for order in m['orders']:
            slots.extend([benchmark, order['round'], name, by_id[name]] for name in order['profiles'])
    require(len(slots) == 90 and len({tuple(s) for s in slots}) == 90, 'Duplicate schedule slot')
    same(plan['retained_slots'], slots[:54], 'Retained rotation changed')
    same(plan['remaining_slots'], slots[54:], 'Remaining rotation changed')
    return slots, profiles


def check_fingerprint(attempt, row, all_pins):
    fp = strict_json(attempt['execution_fingerprint'])
    require(set(fp) == {'source_sha256', 'binary_sha256', 'command', 'cwd', 'environment', 'support'},
            'Unexpected execution fingerprint fields')
    expected = dict(source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
                    command=[part.replace(row['source'], '{source}') for part in row['command']],
                    cwd=row['cwd'], environment=row.get('runtime_environment', {}))
    same({k: v for k, v in fp.items() if k != 'support'}, expected, 'Execution fingerprint changed')
    require(type(fp['support']) is dict, 'Missing fingerprint source closure')
    require(all_pins.get(row['source']) == row['source_sha256']
            and all_pins.get(row['command'][0]) == row['binary_sha256'], 'Scored source/binary pin mismatch')
    def collect(value, result):
        if isinstance(value, dict):
            if value.get('path') and digest(value.get('sha256')):
                result[value['path']] = value['sha256']
            for name, child in value.items():
                if name in ('pins', 'libraries', 'pin_files', 'support_pins') and isinstance(child, dict):
                    for filename, pin in child.items():
                        if digest(pin):
                            require(Path(filename).is_absolute(), 'Unexpected relative producer pin map')
                            result[filename] = pin
                            result[posixpath.normpath(filename)] = pin
                collect(child, result)
        elif isinstance(value, list):
            for child in value:
                collect(child, result)
    def logical(path):
        p = Path(path)
        return posixpath.normpath(str(p if p.is_absolute() else HOST_CLBG/p))
    expected_support = {}
    collect(row, expected_support)
    same(fp['support'], expected_support, 'Frozen fingerprint support differs from immutable profile metadata')
    # Remove only the direct evidence list, leaving every other row field in the
    # measured closure. In particular, nested support maps never inherit this
    # descriptive treatment just because they contain the same path/hash shape.
    active_row = dict(row)
    active_row['algorithm'] = {k: v for k, v in row.get('algorithm', {}).items() if k != 'evidence'}
    active_support = {}
    collect(active_row, active_support)
    active_paths = {logical(path) for path in active_support}
    active_paths.update((logical(row['source']), logical(row['command'][0])))
    refs = row.get('algorithm', {}).get('evidence', []) if row['language'] == 'mech' else []
    require(type(refs) is list, 'Algorithm evidence must be a direct list')
    differences = []
    for path, sha256 in fp['support'].items():
        resolved = logical(path)
        current = all_pins.get(resolved)
        descriptive = any(type(ref) is dict and ref.get('path') == path
                          and ref.get('sha256') == sha256 for ref in refs)
        if not descriptive or resolved in active_paths:
            require(current == sha256, 'Unpinned measured support or changed active input: '+path)
        if descriptive:
            differences.append(dict(profile=row['key'], field='algorithm.evidence', path=path,
                resolved_path=resolved, recorded_sha256=sha256, current_plan_sha256=current,
                also_measured_dependency=resolved in active_paths,
                descriptive_provenance_only=resolved not in active_paths,
                claimed_source_of_scored_binary=False,
                status='awaiting-file-review'))

    return differences


def check_attempt(attempt, raw, supervised, slot, row, manifest, all_pins, provenance=None):
    same(supervised, attempt, 'Report differs from supervisor receipt')
    same({k: v for k, v in supervised.items() if k not in SUPERVISOR_FIELDS}, raw,
         'Supervisor changed or omitted raw sampler fields')
    same([attempt[k] for k in ('benchmark', 'round', 'id', 'key')], slot, 'Attempt is outside canonical rotation')
    require(integer(attempt['sampler_wait_status'], 0) and integer(attempt['exit_status'], 0), 'Abnormal native/sampler exit')
    require(attempt['qualified'] is True and set(attempt['qualification_checks']) == CHECKS
            and all(v is True for v in attempt['qualification_checks'].values()), 'Qualification check omitted or not true')
    require(all(not attempt.get(k) for k in ERROR_FIELDS), 'Attempt contains failure or cleanup evidence')
    for key in EMPTY_LIST_FIELDS:
        same(attempt[key], [], 'Nonempty or missing monitor/group field: '+key)
    require(attempt['stderr'] == '', 'Successful sample contains stderr diagnostics')
    require(attempt['full_workload'] is True and integer(attempt['workload_n'], manifest['size'])
            and integer(attempt['timeout_seconds'], 14400) and integer(attempt['maximum_rss_mib'], 10240),
            'Sample used changed workload or limits')
    require(attempt['valid_environment'] is True and attempt['pins_unchanged_at_end'] is True,
            'Sample lacks clean environment/pin gate')
    for field in ('power_at_start', 'power_at_end'):
        same(attempt[field], manifest['required_power_profile'], 'Wrong measured power profile')
    native = attempt['supervised_native_group']
    require(native['type'] == 'native-group-started' and integer(native['pid']) and native['pid'] > 0
            and integer(native['pgid'], native['pid']) and native['inherited_common_mutex'] is True,
            'Missing authoritative owned native process group')
    command = [part.replace('{n}', str(manifest['size'])) for part in row['command']]
    same(native['command'], command, 'Registered native command differs')
    same(attempt['command'], command, 'Sample command differs')
    for field in ('cwd', 'runtime_environment', 'source_sha256', 'language'):
        same(attempt[field], row[field], 'Measured identity differs: '+field)
    differences = check_fingerprint(attempt, row, all_pins)
    if provenance is not None:
        provenance.extend(differences)
    seconds = attempt['seconds']
    require(finite(seconds, True) and seconds <= manifest['timeout_seconds'], 'Invalid sample duration')
    begin, end = timestamp(attempt['started_at']), timestamp(attempt['finished_at'])
    require(begin <= end and seconds <= (end-begin).total_seconds()+0.01, 'Impossible timing interval')
    peak = attempt['peak_process_group_rss_kib']
    require(integer(peak) and 0 <= peak <= manifest['maximum_rss_mib']*1024, 'Recorded RSS exceeds ceiling')
    require(integer(attempt['stdout_bytes']) and attempt['stdout_bytes'] > 0 and digest(attempt['stdout_sha256']),
            'Missing complete output digest')
    validation = attempt['validation']
    require(validation['reference_match'] is True, 'Output validation failed')
    same([validation['bytes'], validation['sha256']], [attempt['stdout_bytes'], attempt['stdout_sha256']],
         'Validator and sampler output differ')
    reference = manifest['full_output_reference']
    if reference is not None:
        same(reference, {'bytes': attempt['stdout_bytes'], 'sha256': attempt['stdout_sha256']},
             'Output bytes/hash do not match the full reference')
    else:
        require(slot[0] == 'nbody' and validation['tolerance'] == 1e-8, 'Unexpected tolerance-only workload')
        energies = validation['energies']
        require(type(energies) is list and len(energies) == 2
                and all(finite(x) for x in energies), 'Invalid N-body energies')
        require(all(abs(a-b) <= 1e-8 for a, b in zip(energies, (-0.169075164, -0.169059907))),
                'N-body energies exceed the frozen tolerance')
    return begin, end


def three_statistics(samples):
    require(type(samples) is list and len(samples) == 3 and all(finite(x, True) for x in samples),
            'Exactly three finite positive samples required')
    a, b, c = samples
    # Independent three-sample formula, rather than the producer's statistics.stdev.
    sd = math.sqrt(((a-b)**2+(a-c)**2+(b-c)**2)/6.0)
    return sorted(samples)[1], sd


def process_identity(value):
    """Ignore only the PPID that changes when the detached launcher exits."""
    require(type(value) is dict and integer(value['pid']) and value['pid'] > 0, 'Invalid process identity')
    fields = value['listing'].split(None, 7)
    require(len(fields) == 8 and fields[0] == str(value['pid']) and fields[1].isdigit(),
            'Incomplete process listing')
    return value['pid'], fields[2:7], fields[7]


def check_durable(durable, plan_path, plan_sha, plan):
    request, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    command = request['command']
    expected = [command[0], '-I', '-S', '-B', '-u', plan['controller'], 'run',
                '--plan', plan_path, '--plan-sha256', plan_sha]
    same(command, expected, 'Durable command is not the exact prepared continuation')
    require(command[0] == PYTHON and digest(plan['pins'].get(PYTHON)), 'Unpinned continuation interpreter')
    for item in (launch, worker, started):
        same(item['command'], command, 'Durable argv disagreement')
        require(item['cwd'] == request['cwd'] == plan['repository'], 'Durable cwd disagreement')
    require(integer(request['schema_version'], 1) and request['common_mutex_owned_by_target_command'] is True,
            'Wrong durable ownership request')
    for item in (request, launch, ended):
        require(item['automatic_retry'] is False and item['qualification_granted'] is False, 'Durable policy changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Worker ownership incomplete')
    require(ended['status'] == 'command-exited-zero-awaiting-report-review'
            and integer(ended['exit_code'], 0) and ended['actual_command_started'] is True
            and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False, 'Durable process did not finish normally')
    same(ended['stop_signals'], [], 'Durable stop signal recorded')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Durable terminal contains a failure')
    same(process_identity(ended['command_identity']), process_identity(started['command_identity']),
         'Command identity differs at terminal')
    same(process_identity(ended['worker_identity']), process_identity(worker['worker_identity']),
         'Worker identity differs at terminal')
    same(process_identity(launch['worker_identity']), process_identity(worker['worker_identity']),
         'Launch worker identity differs')
    require(integer(started['command_pid']) and started['command_pid'] > 0
            and integer(ended['command_pid'], started['command_pid'])
            and integer(started['command_identity']['pid'], started['command_pid'])
            and started['command_identity']['listing'], 'Missing command PID/identity')
    require(timestamp(request['created_at']) <= timestamp(worker['started_at'])
            <= timestamp(started['started_at']) <= timestamp(ended['finished_at']), 'Durable times are inconsistent')


def reconcile(plan, retained, report, terminal, raw, supervised, durable, plan_path, plan_sha):
    """Pure ledger checks. Inputs must separately be bound to verified file hashes."""
    slots, originals = schedule(plan)
    check_durable(durable, plan_path, plan_sha, plan)
    require(plan['retained_report_sha256'] == RETAINED_SHA
            and plan['retained_terminal_sha256'] == RETAINED_TERMINAL_SHA, 'Wrong retained study')
    require(report['status'] == terminal['status'] == 'complete' and report['active'] is None,
            'Only a completed, successful full90 ledger may reconcile')
    require(not any(report.get(k) for k in ('error', 'error_type', 'correctable_source_failures')),
            'Study records failed profiles')
    require(report['chart_admission'] is terminal['chart_admission'] is plan['chart_admission'] is False,
            'Producer unexpectedly granted chart admission')
    require(plan['runtime_publication_metadata_qualified'] is False, 'Plan cannot grant runtime publication')
    for item in (report, terminal):
        require(integer(item['full_performance_runs'], 90) and integer(item['new_completed_processes'], 36),
                'Wrong full/new sample totals')
    for item in (plan, terminal):
        require(integer(item['reused_completed_processes'], 54) and integer(item['repeated_completed_samples'], 0)
                and integer(item['compiler_invocations'], 0) and integer(item['fixture_reexecutions'], 0)
                and item['original_files_mutated'] is False, 'Unexpected continuation scope')
    require(integer(report['retained_completed_processes'], 54) and report['pins_unchanged_at_end'] is True,
            'Retained/end integrity accounting failed')
    require(terminal['common_mutex_held'] is True, 'Terminal lacked common mutex')
    same(terminal['integrity_errors'], [], 'Terminal integrity failure')
    expected_pins = dict(plan['pins']); expected_pins[plan_path] = plan_sha
    same(report['pins'], expected_pins, 'Report pin closure differs from the plan')
    same(terminal['prerequisite_pins'], expected_pins, 'Terminal pin closure differs')
    require(report['migration_plan'] == plan_path and report['migration_plan_sha256'] == plan_sha,
            'Report references another plan')
    same(report['resumed_from'], dict(report=plan['original_report'], report_sha256=RETAINED_SHA,
        terminal=plan['original_terminal'], terminal_sha256=RETAINED_TERMINAL_SHA,
        reused_completed_processes=54, new_process_slots=36), 'Retained provenance differs')
    same(report['benchmark_order'], list(BENCHES), 'Workload order differs')
    same(report['completed_benchmarks'], list(BENCHES), 'Missing completed workload')
    require(integer(report['sample_count'], 3) and integer(report['maximum_rss_mib'], 10240)
            and report['shared_timing_lock'] == str(LOCK), 'Report policy differs')
    require(len(retained['attempts']) == 54 and len(report['attempts']) == 90, 'Full90 evidence is incomplete')
    same(report['attempts'][:54], retained['attempts'], 'Preserved 54 attempts changed')
    require(set(report['programs']) == set(originals), 'Profile inventory changed')
    all_pins = dict(plan['historical_pins']); all_pins.update(expected_pins)
    grouped = {k: [] for k in originals}
    previous_end = None
    provenance = []
    paths = set()
    for index, (attempt, slot) in enumerate(zip(report['attempts'], slots), 1):
        require(integer(attempt['attempt'], index), 'Attempt sequence has omission or repeat')
        directory = OLD_STUDY if index <= 22 else OLD_RESUMED if index <= 54 else plan['output']
        result_path = directory+'/attempts/'+f'{index:03d}-{slot[2]}.json'
        require(attempt['result_path'] == result_path
                and attempt['supervisor_result_path'] == result_path[:-5]+'.supervisor.json', 'Attempt path changed')
        for path in (attempt['result_path'], attempt['supervisor_result_path']):
            require(path not in paths, 'Attempt evidence reused'); paths.add(path)
        key = slot[3]
        begin, end = check_attempt(attempt, raw[result_path], supervised[attempt['supervisor_result_path']],
            slot, originals[key], plan['manifests'][slot[0]], all_pins, provenance)
        require(previous_end is None or previous_end <= begin, 'Native sample intervals overlap')
        previous_end = end
        grouped[key].append(attempt)
    summaries = {}
    for key, original in originals.items():
        row, attempts = report['programs'][key], grouped[key]
        same({k: v for k, v in row.items() if k not in AGGREGATE_FIELDS},
             {k: v for k, v in original.items() if k not in AGGREGATE_FIELDS}, 'Program metadata/source binding changed')
        require(not row.get('full_failure') and row['measurement_status'] == 'measured', 'Profile failed or incomplete')
        same(row['attempts'], [a['attempt'] for a in attempts], 'Program attempt indices differ')
        values = [a['seconds'] for a in attempts]
        same(row['samples_seconds'], values, 'Aggregate sample values differ')
        same(row['sample_validation'], [a['validation'] for a in attempts], 'Aggregate output validations differ')
        same(row['full_validation'], attempts[0]['validation'], 'First full validation differs')
        median, sd = three_statistics(values)
        require(finite(row['median_seconds'], True) and row['median_seconds'] == median, 'Median differs')
        require(finite(row['sample_stdev_seconds']) and math.isclose(row['sample_stdev_seconds'], sd,
                rel_tol=1e-12, abs_tol=1e-12), 'Sample SD differs from independent n-1 calculation')
        summaries[key] = dict(key=key, id=row['id'], language=row['language'], benchmark=row['benchmark'],
            source=row['source'], source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
            loc=row['loc'], physical_loc=row.get('physical_loc'), source_bundle=row.get('source_bundle'),
            compiler_bound_input_inventory=row.get('compiler_bound_input_inventory'),
            command=row['command'], cwd=row['cwd'], runtime_environment=row['runtime_environment'],
            attempts=row['attempts'], samples_seconds=values, median_seconds=median,
            sample_stdev_seconds=row['sample_stdev_seconds'], independently_calculated_sample_stdev_seconds=sd,
            sample_evidence=[dict(attempt=a['attempt'], round=a['round'], raw=a['result_path'],
                supervisor=a['supervisor_result_path'], stdout_bytes=a['stdout_bytes'],
                stdout_sha256=a['stdout_sha256'], validation=a['validation']) for a in attempts])
    controls = {}
    for bench in BENCHES:
        candidates = [p for p in summaries.values() if p['benchmark'] == bench]
        control = [p for p in candidates if p['language'] == 'mech']
        require(len(control) == 1 and len(candidates) == 3, 'Missing matched Mech control')
        controls[bench] = control[0]
        for p in candidates:
            if p['language'] == 'pony':
                p['matched_mech_control_key'] = control[0]['key']
    return dict(schema='pony-independent-full90-reconciliation-v1',
        status='ledger-reconciled-awaiting-pin-seal-runtime-and-publication-review',
        source_forms=20, pony_samples=60, matched_mech_samples=30, actual_full_native_processes=90,
        retained_samples=54, added_samples=36, repeated_completed_samples=0,
        profiles=summaries, matched_mech_controls=controls, file_integrity_verified=False,
        historical_algorithm_provenance=[strict_json(value) for value in sorted({canonical(p) for p in provenance})],
        runtime_publication_metadata_qualified=False, chart_admission=False,
        complete_stdout_retained=False, full_output_evidence='sampler byte counts/hashes and frozen validation receipts',
        nbody_validation='two retained finite energies independently checked within 1e-8; full stdout not retained',
        sample_sd_comparison_tolerance=dict(relative=1e-12, absolute=1e-12),
        admission_requirements=['independent source-work/LOC closure review', 'runtime publication metadata review',
            'explicit publication record preserving producer flags and historical fixed baselines',
            'Pony-specific catalog/import/export verification'])


class Files:
    """Read-only digest binding. No caches that can conceal changed bytes."""
    def __init__(self, plan):
        self.relocations = plan['path_reconciliation']
        self.verified = {}

    def path(self, logical):
        p = Path(logical)
        require(p.is_absolute() and '..' not in p.parts, 'Unsafe evidence path')
        if logical in self.relocations:
            p = Path(self.relocations[logical]['path'])
            require(p.is_absolute() and '..' not in p.parts, 'Unsafe relocated evidence path')
        return p

    def verify(self, logical, expected):
        require(digest(expected), 'Invalid expected SHA-256')
        path = self.path(logical)
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        require(actual == expected, 'Pinned bytes differ: '+str(path))
        require(str(path) not in self.verified or self.verified[str(path)] == expected, 'Conflicting file pins')
        self.verified[str(path)] = expected

    def document(self, logical, expected):
        self.verify(logical, expected)
        raw = self.path(logical).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'Document changed while reading')
        return strict_json(raw)


def review_files(plan_path, expected_plan_sha256, durable_directory):
    """Read/hash only after full completion; caller writes a new review artifact.

    The common lock is nonblocking. A still-running durable worker also causes
    the private lease acquisition to fail, including gaps between sample locks.
    No file is created or mutated, and no imported benchmark code executes.
    """
    plan_path, job = Path(plan_path).resolve(), Path(durable_directory).resolve()
    with LOCK.open('rb') as lock, (job/'owner.lock').open('rb') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held, named = os.fstat(lock.fileno()), LOCK.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == LOCK_INODE,
                'Original shared mutex changed')
        plan_raw = plan_path.read_bytes()
        require(hashlib.sha256(plan_raw).hexdigest() == expected_plan_sha256, 'Wrong independently pinned plan')
        plan = strict_json(plan_raw)
        files = Files(plan)
        files.verify(str(plan_path), expected_plan_sha256)
        checker_path = Path(__file__).resolve()
        checker_sha = hashlib.sha256(checker_path.read_bytes()).hexdigest()
        files.verify(str(checker_path), checker_sha)
        durable, durable_pins = {}, {}
        for name in ('request', 'launch', 'worker-started', 'command-started', 'terminal'):
            path = job/(name+'.json'); raw_bytes = path.read_bytes()
            pin = hashlib.sha256(raw_bytes).hexdigest()
            durable[name] = files.document(str(path), pin); durable_pins[str(path)] = pin
        check_durable(durable, str(plan_path), expected_plan_sha256, plan)
        require((job/'command.stderr').read_bytes() == b'', 'Durable command emitted stderr')
        for name in ('command.stdout', 'command.stderr', 'worker.log'):
            path = job/name
            with path.open('rb') as stream:
                pin = hashlib.file_digest(stream, 'sha256').hexdigest()
            files.verify(str(path), pin); durable_pins[str(path)] = pin
        output = Path(plan['output'])
        terminal_path = output/'terminal.json'
        terminal_bytes = terminal_path.read_bytes(); terminal_sha = hashlib.sha256(terminal_bytes).hexdigest()
        terminal = files.document(str(terminal_path), terminal_sha)
        require(terminal['report'] == str(output/'report.json'), 'Terminal points to another report')
        report = files.document(terminal['report'], terminal['report_sha256'])
        # Check the exact output directory inventory. No unattached attempt or
        # temporary/error file may disappear from the reconciliation.
        available = terminal['available_evidence_pins']
        actual = set()
        for path in output.rglob('*'):
            require(not path.is_symlink(), 'Symlink in final output evidence')
            if path.is_file() and path != terminal_path:
                actual.add(str(path))
        require(actual == set(available), 'Terminal artifact inventory differs from actual files')
        for path, pin in available.items():
            require(Path(path).is_relative_to(output), 'Terminal evidence escapes study output')
            files.verify(path, pin)
        for path, pin in plan['pins'].items():
            files.verify(path, pin)
        # The optional upstream Rust example is a descriptive comparison source,
        # not the executable output oracle. Bind preserved bytes when available.
        upstream = Path(plan['repository'])/'archive/workloads/pidigits/upstream/pidigits-rust-4.rs'
        upstream_sha = UPSTREAM_RUST_SHA
        if upstream.is_file():
            files.verify(str(upstream), upstream_sha)
        retained = files.document(plan['original_report'], RETAINED_SHA)
        old_terminal = files.document(plan['original_terminal'], RETAINED_TERMINAL_SHA)
        require(old_terminal['report_sha256'] == RETAINED_SHA, 'Retained terminal linkage differs')
        raw, supervisors = {}, {}
        for index, a in enumerate(report['attempts'], 1):
            for field, target in (('result_path', raw), ('supervisor_result_path', supervisors)):
                path = a[field]
                pins = plan['historical_pins'] if index <= 54 else available
                require(path in pins, 'Attempt is outside the pinned evidence inventory')
                target[path] = files.document(path, pins[path])
        review = reconcile(plan, retained, report, terminal, raw, supervisors, durable, str(plan_path), expected_plan_sha256)
        allowed = {str(output/'report.json'), str(output/'recovery.json')}
        allowed.update(a[field] for a in report['attempts'][54:] for field in ('result_path', 'supervisor_result_path'))
        require(set(available) == allowed, 'Unreconciled extra output artifacts')
        recovery_path = str(output/'recovery.json')
        recovery = files.document(recovery_path, available[recovery_path])
        require(recovery['plan'] == str(plan_path) and recovery['plan_sha256'] == expected_plan_sha256
                and recovery['original_files_mutated'] is False and recovery['chart_admission'] is False
                and integer(recovery['retained_processes'], 54) and integer(recovery['new_process_slots'], 36)
                and integer(recovery['repeated_completed_samples'], 0), 'Recovery receipt differs')
        same(recovery['retained_slots'], plan['retained_slots'], 'Recovery retained slots differ')
        same(recovery['remaining_slots'], plan['remaining_slots'], 'Recovery remaining slots differ')
        # Historical references are informative rather than prerequisites for
        # unchanged measured controls. Preserve their recorded values and bind
        # available current bytes, without claiming they built the scored binary.
        mapping_path = Path(plan['repository'])/'migration/reorganization-paths.tsv'
        require(str(mapping_path) in files.verified, 'Migration aliases are outside the pinned closure')
        with mapping_path.open(newline='') as stream:
            aliases = {r['original_path']: r['current_path'] for r in csv.DictReader(stream, delimiter='\t')}
        for ref in review['historical_algorithm_provenance']:
            current_path = files.path(ref['resolved_path'])
            archived = aliases.get('benchmarks/clbg/'+ref['path'])
            if archived and not ref['also_measured_dependency']:
                current_path = Path(plan['repository'])/archived
                require(current_path.resolve().is_relative_to(Path(plan['repository']).resolve()),
                        'Historical alias escapes the repository')
            ref['current_path'] = str(current_path)
            if current_path.is_file():
                with current_path.open('rb') as stream:
                    current_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
                files.verify(str(current_path), current_sha)
                ref.update(current_sha256=current_sha,
                    status='recorded-bytes-verified' if current_sha == ref['recorded_sha256'] else 'current-bytes-differ')
            else:
                ref.update(current_sha256=None, status='historical-reference-unavailable')
        # Rehash after all pure validation. Never trust only a preflight digest.
        for path, pin in list(files.verified.items()):
            files.verify(path, pin)
        held_after, named_after = os.fstat(lock.fileno()), LOCK.stat()
        require((held_after.st_dev, held_after.st_ino) == (named_after.st_dev, named_after.st_ino)
                == (held.st_dev, held.st_ino), 'Shared mutex changed during review')
        review.update(status='full90-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=LOCK_INODE,
            plan=dict(path=str(plan_path), sha256=expected_plan_sha256),
            report=dict(path=terminal['report'], sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path), sha256=terminal_sha),
            retained_report=dict(path=plan['original_report'], sha256=RETAINED_SHA),
            retained_terminal=dict(path=plan['original_terminal'], sha256=RETAINED_TERMINAL_SHA),
            durable_evidence_pins=durable_pins, verified_file_pins=files.verified,
            reconciler=dict(path=str(checker_path), sha256=checker_sha),
            optional_upstream_provenance=dict(path=str(upstream), sha256=upstream_sha, verified=upstream.is_file(),
                measured_dependency=False),
            source_evidence=plan['source_evidence'])
        return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New independent review JSON outside the study output')
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site
            and not sys.flags.optimize and Path(sys.executable).resolve() == Path(PYTHON).resolve(),
            'Use the retained Python with -I -S -B, without optimization')
    require(not args.output.exists() and args.output.parent.is_dir(), 'Review output must be a new file in an existing directory')
    # Refuse to place a new review inside the producer's closed artifact set.
    plan = strict_json(args.plan.read_bytes())
    require(not args.output.resolve().is_relative_to(Path(plan['output']).resolve()),
            'Independent review cannot modify the study artifact inventory')
    result = None
    try:
        result = review_files(args.plan, args.plan_sha256, args.durable_directory)
    except BaseException as error:
        result = dict(schema='pony-independent-full90-reconciliation-v1', status='reconciliation-failed',
            error_type=type(error).__name__, error=str(error), file_integrity_verified=False,
            runtime_publication_metadata_qualified=False, chart_admission=False)
        raise
    finally:
        if result is not None:
            with args.output.open('x') as stream:
                json.dump(result, stream, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


if __name__ == '__main__':
    main()
