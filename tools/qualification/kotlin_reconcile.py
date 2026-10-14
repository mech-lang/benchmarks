"""Independently reconcile completed retained Kotlin full90 evidence.

No producer, sampler, runtime or benchmark is imported or executed. The pure
ledger validates every planned slot, receipt, outer supervisor and matched
control; the file phase requires completed durable/private/common leases and
rechecks the complete physical closure. Failed forms keep their real evidence
and never receive a median or ratio from partial samples. This is not a dataset
importer and grants no chart admission or runtime-publication approval.
"""
import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).with_name('prolog_reconcile.py')
HELPER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
raw_helper = HELPER.read_bytes()
if hashlib.sha256(raw_helper).hexdigest() != HELPER_SHA:
    raise ValueError('Independent receipt reconciliation helper changed')
spec = importlib.util.spec_from_file_location('kotlin_independent_receipt_primitives', HELPER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw_helper, str(HELPER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
BENCHES, SIZES, LOCK, POWER = r.BENCHES, r.SIZES, r.LOCK, r.POWER
AGGREGATE, check_attempt, check_outer = r.AGGREGATE, r.check_attempt, r.check_outer
Files, inventory = r.Files, r.inventory
PLAN_SHA = 'fa50e8f327ac960623be79f99730aa94ba1c8588c9008854830a3b74495550f5'
CONTROLLER_SHA = '1c7e97cc2f5556e91338a73ce2cdfba32dfc5f961c4f101078e92366f4c01c41'
WORK_SHA = '8df64fe0309de9331a8ef9645d0c8541bb03baed5d936bb14cb482a3b9b51cee'
LOC_SHA = '0f956d1dffcdcf688637b092004e32c1ce8818be16819871725a58ec7bd78e69'
FROZEN_CONTROLLER_SHA = '06f52fac0287b64ae0c231df8f8eb4a4793112a91efb01c5dde9b107c743c6e7'
SCHEMA = 'kotlin-independent-full90-reconciliation-v1'
JVM_FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
ENVIRONMENT_FIELDS = frozenset(('PATH', 'JAVA_HOME', 'JAVACMD', 'JAVA_OPTS', 'CLASSPATH',
    'KOTLIN_RUNNER', 'KOTLIN_COMPILER', 'KOTLIN_TOOL', 'LC_ALL', 'LANG', 'HOME',
    'XDG_CONFIG_HOME', 'TMPDIR', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'))


def validate_kotlin_row(row, pins):
    """Validate authored roles, retained classes and the direct JVM timing boundary."""
    sources, artifacts, env = row['physical_inputs'], row['class_artifacts'], row['runtime_environment']
    same([s['role'] for s in sources], ['application', 'application-helper'],
         'Both authored Kotlin roles must be counted')
    require(all(s['counted'] is True and p.digest(s['sha256']) and pins.get(s['path']) == s['sha256']
                for s in sources), 'Uncounted or unpinned authored source')
    require(sources[0]['path'] == row['source'] and sources[0]['sha256'] == row['source_sha256'],
            'Main source binding differs')
    require(set(env) == ENVIRONMENT_FIELDS, 'JVM environment contains omitted or injected fields')
    options = JVM_FLAGS + ['-Duser.home='+env['HOME'], '-Djava.io.tmpdir='+env['TMPDIR'].rstrip('/')]
    same(row['command'], [row['binary']]+options+['-cp', row['classes']+':'+row['stdlib'],
                            'clbg.'+row['benchmark']+'.MainKt', '{n}'],
         'Changed direct-main command or JVM policy')
    require(env['JAVACMD'] == row['binary'] and env['JAVA_OPTS'] == ' '.join(options)
            and env['JAVA_HOME'] == str(Path(row['binary']).parent.parent)
            and env['PATH'] == str(Path(row['binary']).parent)+':/usr/bin:/bin:/usr/sbin:/sbin'
            and env['LC_ALL'] == env['LANG'] == 'C'
            and all(env[k] == '' for k in ('CLASSPATH', 'KOTLIN_RUNNER', 'KOTLIN_COMPILER', 'KOTLIN_TOOL'))
            and all(env[k] == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')),
            'Retained JVM environment differs')
    require(all(Path(env[k]).is_absolute() for k in ('HOME', 'TMPDIR', 'XDG_CONFIG_HOME'))
            and Path(row['classes']).is_absolute() and p.digest(pins.get(row['stdlib'])),
            'Unpinned classpath or invalid working-directory policy')
    require(artifacts and len({a['relative_path'] for a in artifacts}) == len(artifacts),
            'Duplicate or missing retained class artifacts')
    owners = []
    for artifact in artifacts:
        part = Path(artifact['relative_path'])
        require(not part.is_absolute() and '..' not in part.parts
                and str(Path(row['classes'])/part) == artifact['path']
                and p.digest(artifact['sha256']) and pins.get(artifact['path']) == artifact['sha256']
                and p.integer(artifact['bytes']) and artifact['bytes'] > 0,
                'Retained class escaped classpath or lacks an exact byte pin')
        if part.suffix == '.class':
            owners.append(str(part.with_suffix('')).replace('/', '.'))
    same(sorted(owners), sorted(row['class_owner_names']), 'Class-owner inventory differs')
    require('clbg.'+row['benchmark']+'.MainKt' in owners and 'clbg.Support' in owners,
            'Main or authored helper class missing')
    require(row['variant'] in ('compact', 'optimized')
            and row['id'] == 'kotlin-'+row['benchmark']+'-'+row['variant']
            and row['alias_of'] == 'kotlin-'+row['benchmark']+'-baseline-v1'
            and row['optimization_claim'] is False and row['cwd'] == str(Path(row['source']).parent)
            and row['runtime_policy_changes'] == row['diagnostic_flags'] == [], 'Retained form identity differs')
    require(row['source_work_qualified'] is row['canonical_loc_qualified'] is True
            and row['formatted_loc_qualified'] is False and row['formatted_loc'] is None
            and row['loc'] == row['canonical_loc']
            and all(p.integer(row[k]) and row[k] > 0 for k in ('canonical_loc', 'physical_loc')),
            'Canonical-only count qualification differs')
    require(row['memory_policy'] == 'Retained -Xms64m -Xmx8g G1; ActiveProcessorCount=8; default tiered compilation',
            'Changed memory or JIT policy')


def prerequisite_inventory(plan, verify_files=False):
    """Bind original failed captures additively without rewriting their statuses."""
    closures = plan['prerequisite_artifact_closures']
    require(len(closures) == len({c['directory'] for c in closures}) == 8,
            'Required-work/count artifact closure incomplete')
    for closure in closures:
        directory, terminal = Path(closure['directory']), closure['terminal']
        require(directory.is_absolute() and terminal['path'] == str(directory/'terminal.json')
                and p.digest(terminal['sha256'])
                and plan['pins'].get(terminal['path']) == terminal['sha256'], 'Unpinned prerequisite terminal')
        expected = {terminal['path']}
        for name, item in closure['artifacts'].items():
            relative = Path(name)
            path = str(directory/relative)
            require(not relative.is_absolute() and '..' not in relative.parts and name != 'terminal.json'
                    and p.integer(item['bytes']) and item['bytes'] >= 0
                    and p.digest(item['sha256']) and plan['pins'].get(path) == item['sha256'],
                    'Unsafe or unpinned prerequisite artifact')
            expected.add(path)
            if verify_files:
                require(Path(path).stat().st_size == item['bytes'], 'Prerequisite artifact size changed')
        if verify_files:
            same(sorted(inventory(directory)), sorted(expected), 'Prerequisite artifact inventory changed')
    if verify_files:
        for manifest in plan['manifests'].values():
            for row in manifest['profiles'][:2]:
                same(sorted(inventory(row['classes'])), sorted(a['path'] for a in row['class_artifacts']),
                     'Retained classpath inventory changed')


def check_durable(durable, plan_path, plan_sha, plan):
    """Validate the exact retained Python -I -S -B -u durable launch."""
    request, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    command = [p.PYTHON, '-I', '-S', '-B', '-u', plan['controller'], 'run',
               '--plan', plan_path, '--plan-sha256', plan_sha]
    same(request['command'], command, 'Durable command is not the exact prepared Kotlin run')
    require(p.digest(plan['pins'].get(p.PYTHON)), 'Unpinned Kotlin interpreter')
    for item in (launch, worker, started):
        same(item['command'], command, 'Durable argv disagreement')
        require(item['cwd'] == request['cwd'] == plan['repository'], 'Durable cwd disagreement')
    require(p.integer(request['schema_version'], 1) and request['common_mutex_owned_by_target_command'] is True,
            'Wrong durable ownership request')
    for item in (request, launch, ended):
        require(item['automatic_retry'] is False and item['qualification_granted'] is False, 'Durable policy changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Worker ownership incomplete')
    require(ended['status'] == 'command-exited-zero-awaiting-report-review'
            and p.integer(ended['exit_code'], 0) and ended['actual_command_started'] is True
            and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False, 'Durable process did not finish normally')
    same(ended['stop_signals'], [], 'Durable stop signal recorded')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Durable terminal contains a failure')
    first_identity, final_identity = [p.process_identity(item['command_identity']) for item in (started, ended)]
    same(final_identity, first_identity, 'Command identity differs at terminal')
    same(first_identity[2], ' '.join(command), 'Observed controller command differs from durable argv')
    worker_identity = p.process_identity(worker['worker_identity'])
    same(p.process_identity(ended['worker_identity']), worker_identity, 'Worker identity differs at terminal')
    same(p.process_identity(launch['worker_identity']), worker_identity, 'Launch worker identity differs')
    require(p.integer(started['command_pid']) and started['command_pid'] > 0
            and p.integer(ended['command_pid'], started['command_pid'])
            and p.integer(first_identity[0], started['command_pid']), 'Missing command PID/identity')
    require(all(item['command_identity']['listing'].split(None, 7)[1] == str(worker_identity[0])
                for item in (started, ended)), 'Controller parent differs from durable worker')
    require(p.timestamp(request['created_at']) <= p.timestamp(worker['started_at'])
            <= p.timestamp(started['started_at']) <= p.timestamp(ended['finished_at']),
            'Durable times are inconsistent')


def schedule(plan):
    require(plan['schema'] == 'kotlin-qualified-retained-full90-v1'
            and plan['status'] == 'prepared-awaiting-independent-review'
            and plan['pins_verified'] is True, 'Unprepared or wrong Kotlin plan')
    require(plan['controller_sha256'] == CONTROLLER_SHA
            and plan['pins'][plan['controller']] == CONTROLLER_SHA, 'Changed frozen controller')
    require(plan['pins'].get(str(Path(plan['controller']).with_name('kotlin_full.py'))) == FROZEN_CONTROLLER_SHA
            and plan['formatted_loc_qualified'] is False, 'Changed frozen full90 timing implementation')
    for name, expected in (('source_work_profiles', 20), ('canonical_loc_profiles', 20),
            ('formatted_loc_profiles', 0), ('retained_bounded_cases', 186), ('samples', 3),
            ('full_processes', 90), ('kotlin_samples', 60), ('matched_mech_samples', 30),
            ('new_native_probes', 0), ('compiler_invocations', 0), ('fixture_reexecutions', 0),
            ('bounded_reexecutions', 0), ('count_replays', 0)):
        require(p.integer(plan[name], expected), 'Changed plan count: '+name)
    require(plan['original_files_mutated'] is False and plan['chart_admission'] is False
            and plan['full_timings_qualified'] is False and plan['no_automatic_retry'] is True
            and plan['continuous_common_mutex'] is True and plan['shared_timing_lock'] == str(LOCK)
            and p.integer(plan['common_mutex_inode'], p.LOCK_INODE), 'Changed plan policy')
    for name, expected in (('qualified_work', WORK_SHA), ('qualified_source_counts', LOC_SHA)):
        binding = plan[name]
        require(binding['sha256'] == expected and plan['pins'][binding['path']] == expected,
                'Changed qualification prerequisite')
    prerequisite_inventory(plan)
    require(set(plan['manifests']) == set(BENCHES), 'Ten manifests required')
    slots, profiles = [], {}
    for bench in BENCHES:
        manifest = plan['manifests'][bench]
        require(manifest['benchmark'] == bench and p.integer(manifest['size'], SIZES[bench])
                and p.integer(manifest['samples'], 3) and p.integer(manifest['timeout_seconds'], 21600)
                and p.integer(manifest['supervisor_timeout_seconds'], 22200)
                and p.integer(manifest['maximum_rss_mib'], 10240), 'Changed workload or bounds')
        require(manifest['canonical_full_workload'] is True and manifest['chart_admission'] is False
                and manifest['no_automatic_retry'] is True and manifest['shared_timing_lock'] == str(LOCK)
                and manifest['retained_subject_compilation_outside_timer'] is True
                and manifest['runtime_and_class_loading_inside_timer'] is True
                and manifest['runtime_JIT_inside_timer'] is True
                and p.integer(manifest['direct_main_invocations_per_sample'], 1), 'Changed timing policy')
        ids = [f'kotlin-{bench}-compact', f'kotlin-{bench}-optimized', 'mech-aot-control']
        rows = manifest['profiles']
        same([row['id'] for row in rows], ids, 'Changed retained cohort')
        same([row['language'] for row in rows], ['kotlin', 'kotlin', 'mech'], 'Changed language cohort')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        same(manifest['orders'], orders, 'Changed rotation')
        for row in rows:
            key = row['id'] if row['language'] == 'kotlin' else bench+':kotlin-full-study:mech-control'
            require(row['key'] == key and row['benchmark'] == bench and key not in profiles,
                    'Duplicate or changed profile identity')
            for field in ('source', 'binary'):
                require(p.digest(row[field+'_sha256']) and plan['pins'].get(row[field]) == row[field+'_sha256'],
                        'Unpinned measured source/runtime')
            require(row['chart_admission'] is False and p.integer(row['maximum_workers'], 8), 'Changed row policy')
            if row['language'] == 'kotlin':
                validate_kotlin_row(row, plan['pins'])
            profiles[key] = row
        keys = {row['id']: row['key'] for row in rows}
        slots.extend([bench, order['round'], identity, keys[identity]] for order in orders for identity in order['profiles'])
    require(len(slots) == len({tuple(s) for s in slots}) == 90 and len(profiles) == 30, 'Incomplete rotation')
    same(plan['schedule'], slots, 'Changed complete schedule')
    return slots, profiles


def execution_support_pins(plan):
    """Kotlin fingerprint paths already name the measured physical files."""
    return dict(plan['pins'])


def reconcile(plan, report, terminal, raw, supervised, outer, durable, plan_path, plan_sha):
    """Pure validation; file hashes and completed leases must be bound separately."""
    require(plan_sha == PLAN_SHA, 'Wrong independently retained plan digest')
    slots, originals = schedule(plan)
    check_durable(durable, plan_path, plan_sha, plan)
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
            and p.integer(report['source_work_profiles'], 20) and p.integer(report['canonical_loc_profiles'], 20)
            and p.integer(report['formatted_loc_profiles'], 0) and p.integer(report['planned_kotlin_samples'], 60)
            and p.integer(report['planned_matched_mech_samples'], 30) and report['full_timings_qualified'] is False
            and terminal['full_timings_qualified'] is False,
            'Changed report policy')
    same(report['benchmark_order'], list(BENCHES), 'Changed benchmark order')
    same(report['completed_benchmarks'], list(BENCHES), 'Incomplete workload accounting')
    require(set(report['programs']) == set(originals), 'Changed profile inventory')
    attempts, failed, skipped, provenance, gaps = report['attempts'], {}, [], [], []
    grouped = {key: [] for key in originals}
    all_pins = execution_support_pins(plan); all_pins.update(expected_pins)
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
        control_key = row['benchmark']+':kotlin-full-study:mech-control'
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
        runtime_publication_metadata_qualified=False, full_timings_qualified=False, complete_stdout_retained=False,
        planned_kotlin_samples=60, planned_matched_mech_samples=30,
        actual_kotlin_processes=sum(a['language']=='kotlin' for a in attempts),
        actual_matched_mech_processes=sum(a['language']=='mech' for a in attempts),
        full_output_evidence='sampler byte counts/hashes and frozen validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        admission_requirements=['source-work and canonical LOC semantic review', 'runtime metadata review',
            'explicit publication excluding failed profiles', 'catalog and website validation'])


def verify_leases(leases):
    for path, handle, device, inode in leases:
        held, named = os.fstat(handle.fileno()), path.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == (device, inode),
                'Lease identity changed during result review')


@contextmanager
def _yield_verified(result, recheck, on_exit_failure):
    """Keep a final closure check and optional restoration inside outer leases."""
    recheck()
    try:
        yield result
    finally:
        try:
            recheck()
        except BaseException as closure_error:
            if on_exit_failure is not None:
                try:
                    on_exit_failure()
                except BaseException as restoration_error:
                    raise BaseExceptionGroup('Closure validation and publication restoration failed',
                        [closure_error, restoration_error])
            raise


@contextmanager
def review_files(plan_path, expected_sha, durable_directory, on_exit_failure=None):
    """Yield only after completed-job and physical-file verification.

    All three live descriptors remain held through the caller's exclusive
    output write and a final closure check, including on a failing body. A
    guarded publication consumer may supply restoration on exit-check failure;
    restoration runs before releasing any lease. Never call during a live run.
    """
    plan_path, job = Path(plan_path).resolve(), Path(durable_directory).resolve()
    plan_bytes = plan_path.read_bytes()
    require(expected_sha == PLAN_SHA and hashlib.sha256(plan_bytes).hexdigest() == expected_sha,
            'Wrong independently retained Kotlin plan')
    plan = p.strict_json(plan_bytes)
    cohort = Path(plan['repository'])/'experiments/kotlin/kotlin-full90.owner.lock'
    files = Files()
    with ExitStack() as stack:
        leases = []
        for path in (job/'owner.lock', cohort, LOCK):
            handle = stack.enter_context(path.open('rb'))
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino), 'Lease replaced')
            if path == LOCK:
                require(held.st_ino == p.LOCK_INODE, 'Original common mutex replaced')
            leases.append((path, handle, held.st_dev, held.st_ino))
        files.verify(str(plan_path), expected_sha)
        for path, digest in ((Path(__file__).resolve(), hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                             (HELPER.resolve(), HELPER_SHA), (r.HELPER.resolve(), r.HELPER_SHA)):
            files.verify(str(path), digest)
        durable = {}
        for name in ('request', 'launch', 'worker-started', 'command-started', 'terminal'):
            path = job/(name+'.json')
            durable[name] = files.document(str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        check_durable(durable, str(plan_path), expected_sha, plan)
        require((job/'command.stderr').read_bytes() == b'', 'Durable controller emitted errors')
        for name in ('command.stdout', 'command.stderr', 'worker.log'):
            path = job/name
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            files.verify(str(path), digest)
        output = Path(plan['output'])
        terminal_path = output/'terminal.json'
        terminal_sha = hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal = files.document(str(terminal_path), terminal_sha)
        require(terminal['report'] == str(output/'report.json'), 'Terminal report path changed')
        report = files.document(terminal['report'], terminal['report_sha256'])
        available = terminal['available_evidence_pins']
        expected_inventory = set(available) | {str(terminal_path)}
        require(inventory(output) == expected_inventory, 'Closed full90 artifact inventory differs')
        for path, digest in available.items():
            require(Path(path).is_relative_to(output), 'Output artifact escapes retained run')
            files.verify(path, digest)
        for path, digest in plan['pins'].items():
            files.verify(path, digest)
        prerequisite_inventory(plan, verify_files=True)
        def documents(paths):
            return {path: files.document(path, available[path]) for path in paths}
        raw = documents(a['result_path'] for a in report['attempts'])
        supervised = documents(a['supervisor_result_path'] for a in report['attempts'])
        outer = documents(a['path'] for a in report['independent_supervisors'])
        result = reconcile(plan, report, terminal, raw, supervised, outer, durable, str(plan_path), expected_sha)
        verified_pins = tuple(files.verified.items())
        def recheck():
            for path, digest in verified_pins:
                files.verify(path, digest)
            require(inventory(output) == expected_inventory, 'Closed artifact inventory changed during review')
            prerequisite_inventory(plan, verify_files=True)
            verify_leases(leases)
        result.update(status='full90-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=p.LOCK_INODE,
            plan=dict(path=str(plan_path), sha256=expected_sha),
            report=dict(path=terminal['report'], sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path), sha256=terminal_sha), verified_file_pins=dict(verified_pins),
            source_evidence=dict(work=plan['qualified_work'], counts=plan['qualified_source_counts']),
            compiler_owner_fingerprint_policy='Exact physical source, class and retained provenance paths; no alias substitution')
        with _yield_verified(result, recheck, on_exit_failure) as verified:
            yield verified


def save_review_result(path, plan_path, plan_sha, durable_directory):
    """Keep only a receipt whose surrounding closure check completed successfully."""
    path, owned = Path(path), {}
    def remove_owned():
        if not owned:
            return
        identity = path.lstat()
        require((identity.st_dev, identity.st_ino) == owned['identity'] and not path.is_symlink(),
                'Refusing to remove a replaced result path')
        actual = path.read_bytes()
        require(owned['bytes'].startswith(actual), 'Refusing to remove altered result bytes')
        path.unlink()
        owned.clear()
    with review_files(plan_path, plan_sha, durable_directory, on_exit_failure=remove_owned) as result:
        raw = (json.dumps(result, indent=2, allow_nan=False)+'\n').encode('utf-8')
        try:
            with path.open('xb') as stream:
                identity = os.fstat(stream.fileno())
                owned.update(identity=(identity.st_dev, identity.st_ino), bytes=raw)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as write_error:
            try:
                remove_owned()
            except BaseException as restoration_error:
                raise BaseExceptionGroup('Result write and restoration failed', [write_error, restoration_error])
            raise
    return result, hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    require(not args.output.exists() and args.output.parent.is_dir(), 'Result review requires a new file')
    plan = p.strict_json(args.plan.read_bytes())
    require(not args.output.resolve().is_relative_to(Path(plan['output']).resolve()),
            'Result review cannot alter original measurement artifacts')
    result, digest = save_review_result(args.output, args.plan, args.plan_sha256, args.durable_directory)
    print(json.dumps(dict(output=str(args.output), sha256=digest,
                          actual_native_processes=result['actual_full_native_processes'],
                          failed_profiles=result['failed_profiles'], chart_admission=False)), flush=True)


if __name__ == '__main__':
    main()
