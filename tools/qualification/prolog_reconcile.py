"""Independent reconciliation of the original22 Prolog full90 measurement ledger.

This reads evidence without importing the producer, sampler, or runtime. File
review requires the completed durable worker and exclusive existing locks. It
can reconcile isolated workload failures without admitting their partial times.
Successful stdout was validated and discarded by the sampler; the retained
evidence consists of byte counts, hashes, and validation receipts, not stdout.
This stage grants neither runtime qualification nor chart admission.
"""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import stat
import sys

HELPER = Path(__file__).with_name('pony_reconcile.py')
HELPER_SHA = 'a15b07f8e6eec9b268c0a8b02c0f2a5b1ad39bcc037abfa408021bf2793bb84a'
helper_raw = HELPER.read_bytes()
if hashlib.sha256(helper_raw).hexdigest() != HELPER_SHA:
    raise ValueError('Independent reconciliation helper changed')
_spec = importlib.util.spec_from_file_location('prolog_independent_primitives', HELPER)
p = importlib.util.module_from_spec(_spec)
exec(compile(helper_raw, str(HELPER), 'exec'), p.__dict__)
require, same = p.require, p.same
BENCHES, SIZES, LOCK = p.BENCHES, p.SIZES, p.LOCK
PLAN_SHA = '55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a'
CONTROLLER_SHA = '0d75d33bb77d3715ca7adcd8c07fcf3b659be472c2ef84c063dec57ee4b8eb94'
OUTCOME_SHA = 'c6ff85042d9cc72f590b730825a4bba60bd85f0dd764d67ab64bffb4a5d6b69e'
STORAGE_SHA = '3538de1dfd61b923970c81db881342cf8ff15cb45c691817ce73433a7c9c1340'
POWER = dict(source='AC Power', low_power_mode=0)
FAILURE_GATES = frozenset(('native_exited_normally', 'no_execution_error',
    'no_resource_violation', 'complete_output_reference_match', 'complete_output_bytes_and_hash'))
AGGREGATE = frozenset(('samples_seconds', 'sample_validation', 'attempts', 'measurement_status',
    'median_seconds', 'sample_stdev_seconds', 'time_x_mech', 'matched_mech_control',
    'matched_mech_source_sha256', 'full_failure'))
SCHEMA = 'prolog-independent-full90-reconciliation-v1'


def schedule(plan):
    require(plan['schema'] == 'prolog-qualified-original22-full90-v1', 'Wrong plan schema')
    require(plan['controller_sha256'] == CONTROLLER_SHA
            and plan['pins'][plan['controller']] == CONTROLLER_SHA, 'Changed frozen controller')
    for name, expected in (('source_work_profiles', 20), ('canonical_loc_profiles', 20),
            ('original_authored_sources', 22), ('compiled_copy_reconciliations', 44),
            ('retained_bounded_cases', 156), ('samples', 3), ('full_processes', 90),
            ('new_native_probes', 0), ('compiler_invocations', 0), ('fixture_reexecutions', 0),
            ('bounded_reexecutions', 0), ('count_replays', 0)):
        require(p.integer(plan[name], expected), 'Changed plan count: '+name)
    require(plan['original_files_mutated'] is False and plan['chart_admission'] is False
            and plan['no_automatic_retry'] is True and plan['shared_timing_lock'] == str(LOCK),
            'Changed plan policy')
    for name, expected in (('sealed_source_outcome', OUTCOME_SHA), ('storage_manifest', STORAGE_SHA)):
        binding = plan[name]
        require(binding['sha256'] == expected and plan['pins'][binding['path']] == expected,
                'Changed source qualification seal')
    require(set(plan['manifests']) == set(BENCHES), 'Ten manifests required')
    slots, profiles = [], {}
    for bench in BENCHES:
        m = plan['manifests'][bench]
        require(m['benchmark'] == bench and p.integer(m['size'], SIZES[bench])
                and p.integer(m['samples'], 3) and p.integer(m['timeout_seconds'], 21600)
                and p.integer(m['supervisor_timeout_seconds'], 22200)
                and p.integer(m['maximum_rss_mib'], 10240), 'Changed workload or limits')
        require(m['canonical_full_workload'] is True and m['chart_admission'] is False
                and m['no_automatic_retry'] is True and m['shared_timing_lock'] == str(LOCK)
                and m['compilation_outside_timer'] is True
                and m['runtime_and_QLF_loading_inside_timer'] is True, 'Changed timing policy')
        ids = [f'prolog-{bench}-compact', f'prolog-{bench}-optimized', 'mech-aot-control']
        rows = m['profiles']
        same([r['id'] for r in rows], ids, 'Changed profile cohort')
        same([r['language'] for r in rows], ['prolog', 'prolog', 'mech'], 'Changed languages')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        same(m['orders'], orders, 'Changed rotation')
        for row in rows:
            key = (f'{bench}:{row["id"]}' if row['language'] == 'prolog'
                   else f'{bench}:prolog-full-study:mech-control')
            require(row['key'] == key and row['benchmark'] == bench and key not in profiles,
                    'Changed or duplicate profile key')
            require(p.digest(row['source_sha256']) and p.digest(row['binary_sha256']), 'Unbound executable')
            if row['language'] == 'prolog':
                require(p.integer(row['maximum_workers'], 1) and row['eligible_for_chart'] is False
                        and row['chart_admission'] is False, 'Prolog policy changed')
            profiles[key] = row
        keys = {r['id']: r['key'] for r in rows}
        slots.extend([bench, order['round'], name, keys[name]] for order in orders for name in order['profiles'])
    same(plan['schedule'], slots, 'Changed complete schedule')
    return slots, profiles


def check_attempt(attempt, raw, supervised, slot, row, manifest, pins, provenance):
    same(supervised, attempt, 'Report differs from supervisor receipt')
    same({k: v for k, v in attempt.items() if k not in p.SUPERVISOR_FIELDS}, raw,
         'Supervisor changed raw sampler evidence')
    same([attempt[k] for k in ('benchmark', 'round', 'id', 'key')], slot, 'Attempt outside rotation')
    checks = attempt['qualification_checks']
    require(set(checks) == p.CHECKS and all(type(v) is bool for v in checks.values()),
            'Missing or nonboolean qualification gate')
    require(type(attempt['qualified']) is bool and p.integer(attempt['sampler_wait_status'], 0),
            'Invalid qualification or sampler exit')
    require(attempt['full_workload'] is True and p.integer(attempt['workload_n'], manifest['size'])
            and p.integer(attempt['timeout_seconds'], 21600)
            and p.integer(attempt['maximum_rss_mib'], 10240), 'Changed measured workload')
    require(attempt['valid_environment'] is True and attempt['pins_unchanged_at_end'] is True,
            'Environment or integrity failure')
    for field in p.EMPTY_LIST_FIELDS:
        # The frozen execute exception path cleans and waits for its child but
        # does not create this normal-exit-only field. Other monitor receipts
        # remain mandatory; a present nonempty group always rejects the run.
        value = (attempt.get(field, []) if not attempt['qualified'] and field == 'remaining_group_members'
                 else attempt[field])
        same(value, [], 'Monitor or process cleanup failure: '+field)
    for field in ('power_at_start', 'power_at_end'):
        same(attempt[field], POWER, 'Changed measured power policy')
    command = [part.replace('{n}', str(manifest['size'])) for part in row['command']]
    native = attempt['supervised_native_group']
    require(native['type'] == 'native-group-started' and p.integer(native['pid']) and native['pid'] > 0
            and p.integer(native['pgid'], native['pid']) and native['inherited_common_mutex'] is True,
            'Missing authoritative native group')
    same(native['command'], command, 'Registered command differs')
    same(attempt['command'], command, 'Executed command differs')
    for field in ('cwd', 'runtime_environment', 'source_sha256', 'language'):
        same(attempt[field], row[field], 'Measured profile differs: '+field)
    provenance.extend(p.check_fingerprint(attempt, row, pins))
    begin, end = p.timestamp(attempt['started_at']), p.timestamp(attempt['finished_at'])
    require(begin <= end, 'Inverted timing interval')
    if not attempt['qualified']:
        require(all(checks[k] for k in p.CHECKS-FAILURE_GATES), 'Failure compromised measurement integrity')
        require(attempt.get('error') and attempt.get('error_type') in
                ('TimeoutError', 'OutputValidationError', 'RuntimeError'), 'Not an isolated workload failure')
        require(not all(checks.values()), 'Unqualified attempt claims every gate passed')
        require(not any(attempt.get(k) for k in p.ERROR_FIELDS
                if k not in ('error', 'error_type', 'resource_violation')), 'Failure contains wrapper/cleanup error')
        return begin, end
    require(all(checks.values()) and p.integer(attempt['exit_status'], 0), 'Failed successful-sample gate')
    require(not any(attempt.get(k) for k in p.ERROR_FIELDS) and attempt['stderr'] == '',
            'Successful sample contains error evidence')
    seconds = attempt['seconds']
    require(p.finite(seconds, True) and seconds <= 21600
            and seconds <= (end-begin).total_seconds()+0.01, 'Impossible sample duration')
    peak = attempt['peak_process_group_rss_kib']
    require(p.integer(peak) and 0 <= peak <= 10240*1024, 'Exceeded measured RSS ceiling')
    require(p.integer(attempt['stdout_bytes']) and attempt['stdout_bytes'] > 0
            and p.digest(attempt['stdout_sha256']), 'Incomplete output binding')
    validation = attempt['validation']
    require(validation['reference_match'] is True, 'Output validation failed')
    same([validation['bytes'], validation['sha256']], [attempt['stdout_bytes'], attempt['stdout_sha256']],
         'Sampler/validator output disagreement')
    if manifest['full_output_reference'] is not None:
        same(manifest['full_output_reference'], dict(bytes=attempt['stdout_bytes'], sha256=attempt['stdout_sha256']),
             'Output differs from full reference')
    else:
        require(slot[0] == 'nbody' and validation['tolerance'] == 1e-8, 'Unexpected tolerance-only validation')
        energies = validation['energies']
        require(type(energies) is list and len(energies) == 2 and all(p.finite(x) for x in energies)
                and all(abs(a-b) <= 1e-8 for a,b in zip(energies, (-0.169075164, -0.169059907))),
                'Invalid N-body energies')
    return begin, end


def kernel_identity(value, pid):
    require(type(value) is dict and p.integer(value['pid'], pid), 'Wrong kernel process identity')
    for field in ('ppid', 'pgid', 'status', 'birth_seconds', 'birth_microseconds'):
        require(p.integer(value[field]) and value[field] >= 0, 'Invalid kernel identity field')
    require(value['birth_seconds'] > 0 and value['birth_microseconds'] < 1000000, 'Invalid process birth time')


def check_outer(record, attempt, controller_pid=None):
    require(record['status'] == 'returned' and p.integer(record['deadline_seconds'], 22200)
            and p.integer(record['native_timeout_seconds'], 21600)
            and p.integer(record['common_mutex_fd']) and record['common_mutex_fd'] >= 0,
            'Outer supervisor did not return within the unchanged policy')
    require(record['common_mutex_held_through_cleanup'] is True and record['native_execute_unchanged'] is True
            and record['native_validation_unchanged'] is True and record['deadline_expired'] is False,
            'Outer supervisor changed measurement or lost ownership')
    same(record['cleanup_errors'], [], 'Outer supervisor cleanup error')
    require(not record.get('error') and not record.get('error_type'), 'Outer supervisor error')
    native = attempt['supervised_native_group']; pid = native['pid']
    same(record['native_registrations'], [native], 'Outer native registration differs')
    children, groups = record['owned_sampler_children'], record['owned_groups']
    require(len(children) == 1, 'Expected exactly one sampler child')
    child_key = next(iter(children)); child = children[child_key]
    require(child_key.isdecimal() and str(int(child_key)) == child_key and int(child_key) > 0
            and int(child_key) != pid and child['reaped'] is True, 'Sampler not normally owned/reaped')
    require(set(groups) == {child_key, str(pid)}, 'Extra or missing owned process group')
    same(groups[child_key], child['identity'], 'Sampler identity differs across receipts')
    gaps = []
    for key in (child_key, str(pid)):
        identity = groups[key]
        if identity is None:
            gaps.append(dict(attempt=attempt['attempt'], pid=int(key), observation='kernel identity unavailable'))
        else:
            kernel_identity(identity, int(key))
            if key == str(pid):
                require(identity['pgid'] == pid and identity['ppid'] == int(child_key), 'Native group not child-owned')
            elif controller_pid is not None:
                require(p.integer(identity['ppid'], controller_pid), 'Sampler not owned by durable controller')
    # Sampler identity can precede setsid(): its observed PGID may still be the
    # controller group. Do not replace that real observation with its later PID.
    if attempt['qualified']:
        same(record['signals'], [], 'Successful outer supervisor used cleanup signals')
    else:
        for event in record['signals']:
            require(p.integer(event['signal'], int(signal.SIGKILL)), 'Unexpected outer cleanup signal')
            require((event['kind'] == 'direct-child' and p.integer(event.get('pid'), int(child_key)))
                    or (event['kind'] == 'owned-group' and p.integer(event.get('pgid'))
                        and str(event['pgid']) in groups), 'Signal targets unowned process')
    return gaps


def reconcile(plan, report, terminal, raw, supervised, outer, durable, plan_path, plan_sha):
    """Pure validation; file hashes and completed leases must be bound separately."""
    require(plan_sha == PLAN_SHA, 'Wrong independently retained plan digest')
    slots, originals = schedule(plan)
    p.check_durable(durable, plan_path, plan_sha, plan)
    controller_pid = durable['command-started']['command_pid']
    supervisor = report['supervisor']
    require(p.integer(supervisor['pid'], controller_pid), 'Report names another controller process')
    same(p.process_identity(dict(pid=supervisor['pid'],
         listing=str(supervisor['pid'])+' 0 '+supervisor['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']), 'Controller birth/command identity differs')
    require(report['status'] in ('complete', 'complete-with-unqualified-profiles')
            and terminal['status'] == report['status'] and report['active'] is None, 'Study is not terminal')
    require(not any(report.get(k) for k in ('error', 'error_type', 'terminal_integrity_errors')),
            'Study has integrity or execution error')
    require(report['plan'] == plan_path and report['plan_sha256'] == plan_sha, 'Report belongs to another plan')
    require(report['pins_unchanged_at_end'] is True and terminal['common_mutex_held'] is True,
            'Unverified final pin/lock state')
    same(terminal['integrity_errors'], [], 'Final integrity failure')
    expected_pins = dict(plan['pins']); expected_pins[plan_path] = plan_sha
    same(terminal['prerequisite_pins'], expected_pins, 'Terminal closure differs')
    for item in (report, terminal):
        require(item['chart_admission'] is False, 'Measurement cannot grant chart admission')
        same(item['native_launch_unconfirmed_attempts'], [], 'Unconfirmed native launch')
    for name in ('compiler_invocations', 'fixture_reexecutions', 'bounded_reexecutions',
                 'count_replays', 'repeated_completed_samples'):
        require(p.integer(terminal[name], 0), 'Unexpected repeated/preparation work')
    require(terminal['original_files_mutated'] is False and report['no_automatic_retry'] is True
            and report['shared_timing_lock'] == str(LOCK) and p.integer(report['sample_count'], 3)
            and p.integer(report['source_work_profiles'], 20) and p.integer(report['canonical_loc_profiles'], 20),
            'Changed report policy')
    same(report['benchmark_order'], list(BENCHES), 'Changed benchmark order')
    same(report['completed_benchmarks'], list(BENCHES), 'Incomplete workload accounting')
    require(set(report['programs']) == set(originals), 'Changed profile inventory')
    attempts, failed, skipped, provenance, gaps = report['attempts'], {}, [], [], []
    grouped = {key: [] for key in originals}
    all_pins = dict(plan['historical_pins']); all_pins.update(expected_pins)
    index = 0; previous_end = None
    require(len(report['independent_supervisors']) == len(attempts), 'Outer receipt count differs')
    used_raw, used_supervised, used_outer = set(), set(), set()
    for slot in slots:
        bench, round_number, identifier, key = slot
        if key in failed:
            skipped.append(dict(benchmark=bench, round=round_number, id=identifier, key=key))
            continue
        require(index < len(attempts), 'Missing scheduled attempt')
        a = attempts[index]; index += 1
        require(p.integer(a['attempt'], index), 'Repeated or missing attempt index')
        base = plan['output']+'/attempts/'+f'{index:03d}-{identifier}'
        require(a['result_path'] == base+'.json' and a['supervisor_result_path'] == base+'.supervisor.json',
                'Attempt artifact path differs')
        outer_path = plan['output']+'/outer-supervisor/'+f'{index:03d}-{identifier}.json'
        ref = report['independent_supervisors'][index-1]
        require(ref['path'] == outer_path and ref['status'] == 'returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'][outer_path] == ref['sha256'], 'Outer receipt binding differs')
        begin, end = check_attempt(a, raw[a['result_path']], supervised[a['supervisor_result_path']], slot,
            originals[key], plan['manifests'][bench], all_pins, provenance)
        require(previous_end is None or previous_end <= begin, 'Native timing intervals overlap')
        previous_end = end
        gaps.extend(check_outer(outer[outer_path], a, controller_pid))
        used_raw.add(a['result_path']); used_supervised.add(a['supervisor_result_path']); used_outer.add(outer_path)
        grouped[key].append(a)
        if not a['qualified']:
            failed[key] = a
    require(index == len(attempts) and index+len(skipped) == 90, 'Unaccounted attempts or schedule slots')
    require(set(raw) == used_raw, 'Raw receipt inventory differs')
    require(set(supervised) == used_supervised and set(outer) == used_outer, 'Supervisor receipt inventory differs')
    require(set(terminal['available_evidence_pins']) ==
            used_raw | used_supervised | used_outer | {plan['output']+'/report.json'},
            'Closed inventory contains unregistered or missing evidence')
    same(report['isolated_failed_profiles'], list(failed), 'Failed profile inventory differs')
    same(report['skipped_failed_profile_slots'], skipped, 'Skipped slots are not explained by prior failure')
    same(terminal['skipped_failed_profile_slots'], skipped, 'Terminal skipped slots differ')
    require(report['status'] == ('complete-with-unqualified-profiles' if failed else 'complete'), 'Status hides failures')
    qualified = sum(a['qualified'] for a in attempts)
    for item in (report, terminal):
        for name, value in (('saved_attempts', index), ('full_performance_runs', index), ('qualified_samples', qualified)):
            require(p.integer(item[name], value), 'Wrong actual execution accounting: '+name)
        same(item['registered_native_attempts'], list(range(1,index+1)), 'Registration ledger differs')
    summaries = {}
    for key, original in originals.items():
        row, observations = report['programs'][key], grouped[key]
        same({k:v for k,v in row.items() if k not in AGGREGATE}, original, 'Measured source/profile metadata changed')
        same(row['attempts'], [a['attempt'] for a in observations], 'Profile attempt membership differs')
        good = [a for a in observations if a['qualified']]
        values = [a['seconds'] for a in good]
        same(row['samples_seconds'], values, 'Profile sample values differ')
        same(row['sample_validation'], [a['validation'] for a in good], 'Profile validations differ')
        if key in failed:
            require(row['measurement_status'] == 'failed-full-workload'
                    and len(values) < 3 and row.get('median_seconds') is None
                    and row.get('sample_stdev_seconds') is None and row['time_x_mech'] is None,
                    'Failed profile promoted partial timings')
            same(row['full_failure'], failed[key], 'Profile failure differs from attempt')
            median = sd = None
        else:
            require(row['measurement_status'] == 'measured' and not row.get('full_failure'), 'Incomplete measured profile')
            median, sd = p.three_statistics(values)
            require(p.finite(row['median_seconds'], True) and row['median_seconds'] == median, 'Median differs')
            require(p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds'] >= 0
                    and math.isclose(row['sample_stdev_seconds'], sd,
                    rel_tol=1e-12, abs_tol=1e-12), 'Sample SD differs from independent calculation')
        summaries[key] = dict(key=key, id=row['id'], language=row['language'], benchmark=row['benchmark'],
            source=row['source'], source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
            attempts=row['attempts'], samples_seconds=values, median_seconds=median, sample_stdev_seconds=sd,
            full_workload_qualified=key not in failed, failed_attempt=failed.get(key, {}).get('attempt'))
    for key, row in report['programs'].items():
        control_key = row['benchmark']+':prolog-full-study:mech-control'
        control = summaries[control_key]
        require(row['matched_mech_control'] == control_key
                and row['matched_mech_source_sha256'] == originals[control_key]['source_sha256'], 'Wrong matched control')
        ratio = (summaries[key]['median_seconds']/control['median_seconds']
                 if key not in failed and control_key not in failed else None)
        same(row['time_x_mech'], ratio, 'Matched Mech ratio differs')
        summaries[key]['time_x_mech'] = ratio
    require(p.timestamp(report['started_at']) <= p.timestamp(attempts[0]['started_at'])
            and previous_end <= p.timestamp(report['finished_at']), 'Study times exclude native intervals')
    require(p.timestamp(durable['command-started']['started_at']) <= p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at']) <= p.timestamp(durable['terminal']['finished_at']),
            'Study extends outside durable controller lifetime')
    return dict(schema=SCHEMA, status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        actual_full_native_processes=index, qualified_samples=qualified, skipped_slots=skipped,
        failed_profiles=list(failed), profiles=summaries, repeated_completed_samples=0,
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance})],
        kernel_identity_observation_gaps=gaps, file_integrity_verified=False, chart_admission=False,
        runtime_publication_metadata_qualified=False, complete_stdout_retained=False,
        full_output_evidence='sampler byte counts/hashes and frozen validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        admission_requirements=['source-work and canonical LOC semantic review', 'runtime metadata review',
            'explicit publication excluding failed profiles', 'catalog and website validation'])


class Files:
    """Plan pins already name physical files; historical aliases are not substituted."""
    def __init__(self):
        self.verified = {}

    def verify(self, filename, expected):
        path = Path(filename)
        require(path.is_absolute() and '..' not in path.parts and p.digest(expected), 'Unsafe file pin')
        with path.open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == expected, 'Pinned file changed: '+filename)
        require(filename not in self.verified or self.verified[filename] == expected, 'Conflicting physical pins')
        self.verified[filename] = expected

    def document(self, filename, expected):
        self.verify(filename, expected)
        raw = Path(filename).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'JSON changed during read')
        return p.strict_json(raw)


def inventory(directory):
    """Fail on traversal errors, symlinks, and nonregular evidence files."""
    result = set()
    require(stat.S_ISDIR(Path(directory).lstat().st_mode), 'Evidence root is not a regular directory')
    def failed(error): raise error
    for base, dirs, files in os.walk(directory, onerror=failed, followlinks=False):
        for name in dirs+files:
            path = Path(base)/name; mode = path.lstat().st_mode
            require(stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode), 'Nonregular evidence path')
            if name in files: result.add(str(path))
    return result


def review_files(plan_path, expected_sha, durable_directory):
    plan_path, job = Path(plan_path).resolve(), Path(durable_directory).resolve()
    # These small metadata reads establish lease paths, not completed execution.
    raw_plan = plan_path.read_bytes()
    require(expected_sha == PLAN_SHA and hashlib.sha256(raw_plan).hexdigest() == expected_sha, 'Wrong retained plan')
    plan = p.strict_json(raw_plan)
    cohort = Path(plan['repository'])/'experiments/prolog/prolog-full90.owner.lock'
    files = Files()
    with ExitStack() as stack:
        leases = []
        for path in (job/'owner.lock', cohort, LOCK):
            handle = stack.enter_context(path.open('rb'))
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino), 'Lease replaced')
            if path == LOCK: require(held.st_ino == p.LOCK_INODE, 'Original common mutex replaced')
            leases.append((path, handle, held.st_dev, held.st_ino))
        files.verify(str(plan_path), expected_sha)
        for path in (Path(__file__).resolve(), HELPER.resolve()):
            files.verify(str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        durable = {}
        for name in ('request', 'launch', 'worker-started', 'command-started', 'terminal'):
            path = job/(name+'.json')
            durable[name] = files.document(str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        p.check_durable(durable, str(plan_path), expected_sha, plan)
        require((job/'command.stderr').read_bytes() == b'', 'Durable command emitted errors')
        for name in ('command.stdout', 'command.stderr', 'worker.log'):
            path = job/name
            with path.open('rb') as stream: sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            files.verify(str(path), sha)
        output = Path(plan['output']); terminal_path = output/'terminal.json'
        terminal_sha = hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal = files.document(str(terminal_path), terminal_sha)
        require(terminal['report'] == str(output/'report.json'), 'Terminal report path changed')
        report = files.document(terminal['report'], terminal['report_sha256'])
        available = terminal['available_evidence_pins']
        expected_inventory = set(available) | {str(terminal_path)}
        require(inventory(output) == expected_inventory, 'Closed evidence inventory differs')
        for path, pin in available.items():
            require(Path(path).is_relative_to(output), 'Output evidence escapes study directory')
            files.verify(path, pin)
        for path, pin in plan['pins'].items(): files.verify(path, pin)
        def documents(paths):
            return {path: files.document(path, available[path]) for path in paths}
        raw = documents(a['result_path'] for a in report['attempts'])
        supervised = documents(a['supervisor_result_path'] for a in report['attempts'])
        outer = documents(ref['path'] for ref in report['independent_supervisors'])
        review = reconcile(plan, report, terminal, raw, supervised, outer, durable, str(plan_path), expected_sha)
        for path, pin in list(files.verified.items()): files.verify(path, pin)
        require(inventory(output) == expected_inventory, 'Evidence inventory changed during review')
        for path, handle, device, inode in leases:
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == (device, inode),
                    'Lease identity changed during review')
        review.update(status='full90-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=p.LOCK_INODE,
            plan=dict(path=str(plan_path), sha256=expected_sha),
            report=dict(path=terminal['report'], sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path), sha256=terminal_sha), verified_file_pins=files.verified,
            source_evidence=dict(outcome=plan['sealed_source_outcome'], storage=plan['storage_manifest'],
                preparation=plan['original_preparation']),
            path_reconciliation=plan['path_reconciliation'])
        return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    require(not args.output.exists() and args.output.parent.is_dir(), 'Review requires a new file')
    plan = p.strict_json(args.plan.read_bytes())
    require(not args.output.resolve().is_relative_to(Path(plan['output']).resolve()), 'Review cannot alter producer evidence')
    result = None
    try:
        result = review_files(args.plan, args.plan_sha256, args.durable_directory)
    except BaseException as error:
        result = dict(schema=SCHEMA, status='reconciliation-failed', error_type=type(error).__name__, error=str(error),
            file_integrity_verified=False, chart_admission=False, runtime_publication_metadata_qualified=False)
        raise
    finally:
        if result is not None:
            with args.output.open('x') as stream:
                json.dump(result, stream, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


if __name__ == '__main__':
    main()
