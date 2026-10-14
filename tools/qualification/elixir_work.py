#!/usr/bin/env python3
"""Prepare/run compiled-work witnesses of the twenty retained Elixir BEAM forms.

``draft`` reads JSON metadata, copies the exact twenty retained identities and records proposed
bounded witness commands. It does not hash the toolchain, load BEAMs, execute
subjects, compile, parse, format, count LOC, or claim verification of inputs.
``prepare`` freezes/verifies those inputs; ``run`` performs the small witnesses
under the shared timing mutex. Native supervision reuses the reviewed atomic
Kotlin bounded observer, including real stdin, pipe capture, RSS bounds and
owned-child cleanup. No existing qualification file or subject is modified.
Direct review of the resulting instruction/dataflow evidence is recorded with
``qualify``; correct output or dynamic call totals alone cannot close that gate.
"""
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'experiments/elixir/compiled-work-v1'
BOUNDED = ROOT / 'experiments/elixir/bounded-work-v1'
LOCK = Path('/tmp/mech-clbg-timing.lock')
SUPERVISOR = ROOT / 'tools/qualification/kotlin_bounded_v2.py'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
PRIOR_REPORT_SHA = 'a7f2700bebd56df569478721fc254e93a2982e230d27862026dc88a38cfe06f2'
PRIOR_TERMINAL_SHA = 'b4e85ac05e86d25c2dc2b25a3243da2b43344f58e25ba50c95577c9d3f71f672'
SUPERVISOR_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
FIXTURE_REVIEW_SHA = 'ea4d1bea1f4863c65609247f62a72154d122166bf7f9fecf83735237f46ddfae'
COMPLETE = 'all20-compiled-work-observed-awaiting-direct-instruction-review'
IMMUTABLE_RECEIPT_FIELDS = ('kind', 'command', 'environment', 'cwd', 'started_at',
    'process_timeout_seconds', 'cleanup_timeout_seconds', 'inherited_common_mutex',
    'common_mutex_inode', 'stop_signals', 'cleanup_errors', 'benchmark_samples',
    'stdin_bytes', 'stdin_sha256', 'maximum_process_group_rss_bytes', 'native_file_limit_bytes',
    'stdout_capture_limit_bytes', 'stdout_transport', 'stderr_transport',
    'source_work_qualified', 'chart_admission')
CASE = {
    'nbody': 'n-2', 'mandelbrot': 'n-9', 'spectralnorm': 'n-3',
    'binarytrees': 'n-4', 'fannkuchredux': 'n-5', 'fasta': 'n-31',
    'knucleotide': 'arbitrary-widths', 'pidigits': 'n-27',
    'regexredux': 'all-replacements', 'revcomp': 'iupac',
}
UNQUALIFIED = dict(source_work_qualified=False, canonical_loc=None,
                   formatted_loc=None, full_timings_qualified=False,
                   chart_admission=False)


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def inventory():
    """Copy already recorded identities; this is not a pin-verification pass."""
    plan = read(BOUNDED / 'plan.json')
    report = read(BOUNDED / 'results-v1/report.json')
    terminal = read(BOUNDED / 'results-v1/terminal.json')
    review = read(BOUNDED / 'source-review.json')
    require(plan['schema'] == 'elixir-retained-beam-bounded-plan-v1', 'Wrong retained cohort schema')
    require(report['status'] == terminal['status'] ==
            'all20-bounded-output-passed-awaiting-compiled-work-and-LOC', 'Bounded report is not complete')
    require(terminal['report_sha256'] == PRIOR_REPORT_SHA
            and report['bounded_outputs_qualified'] is True and report['active'] is None
            and report['qualified_bounded_cases'] == 156
            and report['integrity_errors'] == terminal['integrity_errors'] == terminal['artifact_errors'] == [],
            'Bounded terminal metadata is incomplete')
    expected = {'elixir-' + benchmark + '-' + variant
                for benchmark in CASE for variant in ('compact', 'optimized')}
    require(len(plan['profiles']) == 20 and {p['id'] for p in plan['profiles']} == expected
            and set(report['profiles']) == expected, 'Twenty separate retained forms required')
    cases = {(r['id'], r['case']): r for r in report['cases']}
    rows = []
    for profile in plan['profiles']:
        benchmark = profile['benchmark']
        wanted = CASE[benchmark]
        case = next(c for c in profile['bounded_cases'] if c['case'] == wanted)
        passed = cases[(profile['id'], wanted)]
        require(passed['status'] == 'bounded-output-passed', 'Selected bounded reference did not pass')
        sources = profile['physical_inputs']
        require(len(sources) == 3 and all(s['counted'] is True for s in sources)
                and {s['role'] for s in sources} ==
                {'application', 'application-helper', 'application-launcher'}, 'Authored closure differs')
        roles = {s['role']: s for s in sources}
        require(roles['application']['sha256'] == review['benchmarks'][benchmark]['main_sha256'],
                'Main source metadata differs from source review')
        beams = {Path(b['path']).name: b for b in profile['beams']}
        require(set(beams) == {'Elixir.Clbg.Main.beam', 'Elixir.Clbg.Support.beam'},
                'Unexpected retained module inventory')
        spec = dict(artifact_dir='{fresh-profile-artifact-dir}', ebin=profile['ebin'],
                    main_source=roles['application']['path'],
                    support_source=roles['application-helper']['path'],
                    main_beam_sha256=beams['Elixir.Clbg.Main.beam']['sha256'],
                    support_beam_sha256=beams['Elixir.Clbg.Support.beam']['sha256'],
                    benchmark=benchmark, arguments=[str(case['n'])],
                    lock_fd='{inherited-common-lock-fd}', lock_inode=79859134)
        rows.append(dict(id=profile['id'], benchmark=benchmark, variant=profile['variant'],
                         physical_inputs=sources, beams=profile['beams'], owners=profile['owners'],
                         runtime_environment=profile['runtime_environment'], retained_command=profile['command'],
                         witness_command=[profile['command'][0], '-pa', profile['ebin'],
                                          str(STAGE / 'probe-v2.exs'), '{fresh-spec.json}'],
                         witness_spec=spec, reference_case=case, bounded_process_receipt=passed,
                         separate_loc_stage='experiments/elixir/source-counts-v1/',
                         alias_policy='Inspect and witness each compiled form separately; no optimization claim.',
                         **UNQUALIFIED))
    return dict(schema='elixir-compiled-work-draft-v1', status='draft-source-only-unexecuted',
                  metadata_only=True, pins_verified=False,
                  bounded_plan=str(BOUNDED / 'plan.json'),
                  bounded_plan_sha256_recorded=report['plan_sha256'],
                  bounded_report=str(BOUNDED / 'results-v1/report.json'),
                  bounded_report_sha256_recorded=terminal['report_sha256'],
                  source_review=str(BOUNDED / 'source-review.json'),
                  inherited_pin_inventory=plan['pins'], profiles=rows,
                  proposed_diagnostic_main_processes=20,
                  proposed_full_workload_runs=0, proposed_subject_recompilations=0,
                  native_executions_performed=0, tests_performed=0,
                  qualification_contract=str(STAGE / 'contracts.json'),
                  source_review_before_execution=[
                      'Review this new controller/probe source and the concrete frozen plan.',
                      'Acquire the existing nonblocking common timing lock; an active benchmark blocks all native work.',
                      'Freeze and verify this controller, probes, exact sources/BEAMs, bounded receipts and retained runtime pins.',
                      'Use timeout/RSS/output bounds, inherited lock FD, owned process identity, and complete raw terminal artifacts.',
                      'Inspect real decoded instructions; debug metadata or opcode totals alone cannot pass required work.',
                      'Close tree normal-GC/liveness, pi two-div control-flow and seven complete-map obligations.',
                      'Close the separate source-counts-v1 stage before granting canonical counts.',
                  ], **UNQUALIFIED)


def new_json(output, result):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def save(output, result):
    output = Path(output)
    temporary = output.with_suffix(output.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(output)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fresh_stage_path(path):
    path = Path(path).resolve()
    require(path.is_relative_to(STAGE.resolve()) and not path.exists(),
            'Fresh destination inside this new stage required: ' + str(path))
    return path


def load_supervisor():
    # This imports definitions only. Its own pinned dependencies are the
    # unchanged Kotlin helper and Elixir bounded output/reference utilities.
    raw = SUPERVISOR.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SUPERVISOR_SHA, 'Reviewed native supervisor changed')
    spec = importlib.util.spec_from_file_location('elixir_work_owned_supervisor', SUPERVISOR)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(SUPERVISOR), 'exec'), module.__dict__)
    return module


def prepare(args, lock):
    destination, output = fresh_stage_path(args.plan), fresh_stage_path(args.output)
    require(not destination.is_relative_to(output), 'Plan must be outside execution output')
    result = inventory()
    bounded_plan = read(BOUNDED / 'plan.json')
    require(sha(BOUNDED / 'results-v1/report.json') == PRIOR_REPORT_SHA
            and sha(BOUNDED / 'results-v1/terminal.json') == PRIOR_TERMINAL_SHA
            and sha(BOUNDED / 'plan.json') == result['bounded_plan_sha256_recorded'],
            'Recorded bounded report or plan changed')
    pins = dict(result.pop('inherited_pin_inventory'))
    fixture_review_path = STAGE / 'probe-fixtures-v2-review.json'
    require(sha(fixture_review_path) == FIXTURE_REVIEW_SHA, 'Native probe fixture review changed')
    fixture_review = read(fixture_review_path)
    require(fixture_review['status'] == 'fifteen-native-diagnostic-fixtures-qualified'
            and fixture_review['diagnostic_fixtures_passed'] is True
            and fixture_review['tests'] == 15 and fixture_review['failures'] == 0
            and fixture_review['native_exit_status'] == 0
            and fixture_review['owned_process_reaped'] is True,
            'Native diagnostic fixtures are not qualified')
    pins[str(fixture_review_path)] = FIXTURE_REVIEW_SHA
    for relative, digest in fixture_review['pins'].items():
        path = ROOT / relative
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                'Unsafe fixture review path')
        require(str(path) not in pins or pins[str(path)] == digest, 'Conflicting fixture input identity')
        pins[str(path)] = digest
    result['native_probe_fixture_qualification'] = dict(path=str(fixture_review_path),
        sha256=FIXTURE_REVIEW_SHA, tests=15, failures=0, source_work_qualified=False)
    # Reuse the existing proven provenance closure. This is a byte-integrity
    # check, not a new recursive semantic/toolchain audit.
    for path, digest in pins.items():
        require(sha(path) == digest, 'Retained input changed: ' + path)
    for path in (Path(__file__).resolve(), SUPERVISOR,
                 ROOT / 'tools/qualification/kotlin_helpers.py',
                 ROOT / 'tools/qualification/elixir_bounded.py',
                 STAGE / 'probe-v2.exs', STAGE / 'contracts.json',
                 BOUNDED / 'plan.json', BOUNDED / 'results-v1/report.json',
                 BOUNDED / 'results-v1/terminal.json', BOUNDED / 'source-review.json',
                 PYTHON):
        digest = sha(path)
        require(str(path) not in pins or pins[str(path)] == digest, 'Conflicting input identity')
        pins[str(path)] = digest
    require(pins[str(PYTHON)] == PYTHON_SHA, 'Retained controller Python changed')
    for row in result['profiles']:
        for item in row['physical_inputs'] + row['beams']:
            require(sha(item['path']) == item['sha256'], 'Exact retained form changed')
            pins[item['path']] = item['sha256']
        receipt = row['bounded_process_receipt']
        require(sha(receipt['process']) == receipt['process_sha256'], 'Selected bounded receipt changed')
        pins[receipt['process']] = receipt['process_sha256']
        for key in ('expected', 'stdin'):
            item = row['reference_case'][key]
            if item:
                require(sha(item['path']) == item['sha256'], 'Selected bounded reference changed')
                pins[item['path']] = item['sha256']
        # Preserve the exact same normal runtime options used by the closed
        # 156-case run, including its default collector policy.
        source = next(p for p in bounded_plan['profiles'] if p['id'] == row['id'])
        require(row['runtime_environment'] == source['runtime_environment'], 'Runtime options differ')
    supervisor = load_supervisor()
    supervisor.kh.verify_lock(lock)
    result.update(schema='elixir-retained-beam-compiled-work-plan-v1',
                  status='prepared-awaiting-reviewed-native-execution', metadata_only=False,
                  pins_verified=True, pins=pins, output=str(output),
                  controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
                  python=str(PYTHON), python_sha256=PYTHON_SHA,
                  probe=str(STAGE / 'probe-v2.exs'), supervisor=str(SUPERVISOR),
                  native_timeout_seconds=supervisor.TIMEOUT,
                  maximum_process_group_rss_bytes=supervisor.RSS_LIMIT,
                  per_file_limit_bytes=supervisor.FILE_LIMIT,
                  retained_source_recompilations=0, benchmark_samples=0)
    new_json(destination, result)
    print(json.dumps(dict(status=result['status'], plan=str(destination), sha256=sha(destination),
                          proposed_diagnostic_main_processes=20, native_executions=0)))


ARTIFACT_STEMS = ('main-chunks', 'support-chunks', 'main-disassembly', 'support-disassembly',
                  'main-function-inventory', 'support-function-inventory', 'call-counts',
                  'subject-outcome', 'dynamic-observations')


def validate_observation(row, directory, supervisor):
    summary = read(directory / 'summary.json')
    require(type(summary['common_mutex_fd']) is int and summary['common_mutex_fd'] > 2
            and type(summary['common_mutex_inode']) is int and summary['common_mutex_inode'] == 79859134,
            'Native probe did not record the inherited mutex descriptor')
    expected_spec = dict(row['witness_spec'], artifact_dir=str(directory), lock_fd=summary['common_mutex_fd'])
    equal(read(directory / 'spec.json'), expected_spec, 'Executed witness specification differs from prepared profile')
    require(type(row['reference_case']['n']) is int
            and row['witness_spec']['arguments'] == [str(row['reference_case']['n'])],
            'Witness arguments differ from bounded case size')
    stdin = row['reference_case']['stdin']
    expected_stdin = Path(stdin['path']).read_bytes() if stdin else b''
    require((directory / 'stdin.bin').read_bytes() == expected_stdin, 'Witness stdin differs from bounded reference')
    expected = Path(row['reference_case']['expected']['path']).read_bytes()
    require((directory / 'expected.stdout').read_bytes() == expected, 'Witness expected output differs from reference')
    require(summary['schema'] == 'elixir-compiled-work-draft-observation-v1'
            and summary['status'] == 'dynamic-observations-recorded-awaiting-instruction-review',
            'Missing completed probe observation')
    require(summary['benchmark'] == row['benchmark']
            and summary['arguments'] == row['witness_spec']['arguments']
            and type(summary['subject_main_executions']) is int and summary['subject_main_executions'] == 1
            and type(summary['subject_modules_recompiled']) is int and summary['subject_modules_recompiled'] == 0
            and summary['dynamic_assertions_passed'] is True
            and summary['common_mutex_inherited'] is True, 'Wrong subject invocation')
    for stem in ('main', 'support'):
        require(summary[stem + '_beam_sha256'] == row['witness_spec'][stem + '_beam_sha256'],
                'Observed retained BEAM identity differs')
    require(all(summary[name] is False for name in ('source_work_qualified', 'compiled_work_qualified',
            'chart_admission', 'direct_instruction_review_complete', 'tree_normal_gc_lifetime_proven',
            'pidigits_two_division_dominance_proven')),
            'Probe must not grant unreviewed source-work admission')
    for stem in ARTIFACT_STEMS:
        for suffix in ('.etf', '.txt'):
            path = directory / (stem + suffix)
            require(path.is_file() and 0 < path.stat().st_size <= supervisor.FILE_LIMIT,
                    'Incomplete direct observation artifact: ' + str(path))
    trace = directory / 'trace-framed.etf'
    require(type(summary['trace_events']) is int and summary['trace_events'] > 0 and trace.is_file()
            and type(summary['trace_artifact_bytes']) is int
            and 0 < summary['trace_artifact_bytes'] == trace.stat().st_size <= supervisor.FILE_LIMIT,
            'Trace evidence missing or oversized')
    validation = supervisor.eb.output_validation(row['benchmark'], (directory / 'stdout.bin').read_bytes(), expected)
    require((directory / 'stderr.bin').read_bytes() == b'', 'Unexpected native stderr')
    return dict(summary=summary, validation=validation)


def collect_artifacts(output):
    artifacts, errors = {}, []
    def failed(error, path=None):
        errors.append(dict(path=str(path if path is not None else getattr(error, 'filename', output)),
                           error=str(error) or type(error).__name__))
    try:
        require(stat.S_ISDIR(output.lstat().st_mode), 'Nonregular artifact root')
        for directory, children, names in os.walk(output, onerror=failed, followlinks=False):
            retained = []
            for name in children + names:
                path = Path(directory) / name
                try:
                    mode = path.lstat().st_mode
                    require(not stat.S_ISLNK(mode), 'Artifact symlink')
                    if stat.S_ISREG(mode):
                        artifacts[str(path.relative_to(output))] = dict(bytes=path.stat().st_size, sha256=sha(path))
                    else:
                        require(stat.S_ISDIR(mode), 'Nonregular artifact')
                        if name in children: retained.append(name)
                except BaseException as error: failed(error, path)
            children[:] = retained
    except BaseException as error: failed(error, output)
    return artifacts, errors


def equal(left, right, message):
    require(json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False), message)


def validate_native_receipt(process, row, directory, supervisor, controller_pid):
    require(type(controller_pid) is int and controller_pid > 0, 'Invalid controller PID')
    require(process['kind'] == 'elixir-compiled-work-witness' and process['status'] == 'native-passed'
            and process['native_process_started'] is True and type(process['pid']) is int and process['pid'] > 0
            and type(process['pgid']) is int and process['pgid'] == process['pid']
            and type(process['exit_status']) is int and process['exit_status'] == 0
            and process['direct_child_reaped'] is True and process['remaining_process_group'] == []
            and process['inherited_common_mutex'] is True and type(process['common_mutex_inode']) is int
            and process['common_mutex_inode'] == 79859134
            and process['cwd'] == str(directory), 'Native observation lacks a clean owned exit')
    require(not any(process.get(k) for k in ('error', 'error_type', 'cleanup_errors', 'artifact_errors',
            'stop_signals', 'remaining_after_cleanup', 'timed_out')), 'Native observation records failure')
    require(process['source_work_qualified'] is False and process['chart_admission'] is False
            and type(process['benchmark_samples']) is int and process['benchmark_samples'] == 0,
            'Native diagnostic receipt grants qualification or timing')
    expected_start = dict({key: process[key] for key in IMMUTABLE_RECEIPT_FIELDS},
        status='starting', native_process_started=False, observed_peak_process_group_rss_bytes=0, kernel_monitor_samples=0)
    equal(read(directory / 'start.json'), expected_start, 'Native request and final receipt differ')
    expected_active = dict(expected_start, status='running', native_process_started=True,
                           pid=process['pid'], pgid=process['pgid'], identity=process['identity'])
    equal(read(directory / 'active.json'), expected_active, 'Native launch observation and final receipt differ')
    expected_command = [row['retained_command'][0], '-pa', row['witness_spec']['ebin'],
                        str(STAGE / 'probe-v2.exs'), str(directory / 'spec.json')]
    expected_environment = dict(row['runtime_environment'], HOME=str(directory / 'home'),
        XDG_CONFIG_HOME=str(directory / 'config'), TMPDIR=str(directory / 'tmp') + os.sep,
        ERL_CRASH_DUMP=str(directory / 'erl-crash.dump'))
    equal(process['command'], expected_command, 'Native witness command differs')
    equal(process['environment'], expected_environment, 'Native witness environment differs')
    for field, expected in (('process_timeout_seconds', supervisor.TIMEOUT),
            ('cleanup_timeout_seconds', supervisor.CLEANUP_TIMEOUT),
            ('maximum_process_group_rss_bytes', supervisor.RSS_LIMIT),
            ('native_file_limit_bytes', supervisor.FILE_LIMIT),
            ('stdout_capture_limit_bytes', supervisor.FILE_LIMIT + supervisor.PIPE_CHUNK)):
        equal(process[field], expected, 'Changed native resource policy: ' + field)
    require(type(process['kernel_monitor_samples']) is int and process['kernel_monitor_samples'] > 0
            and type(process['observed_peak_process_group_rss_bytes']) is int
            and 0 <= process['observed_peak_process_group_rss_bytes'] <= supervisor.RSS_LIMIT,
            'Missing or invalid native resource observation')
    before, after = process['identity'], process['leader_identity_before_reap']
    require(all(type(before[k]) is int and type(after[k]) is int and before[k] == after[k]
                for k in ('pid', 'ppid', 'pgid', 'birth_seconds', 'birth_microseconds'))
            and before['pid'] == before['pgid'] == process['pid'] and before['ppid'] == controller_pid
            and before['birth_seconds'] > 0 and 0 <= before['birth_microseconds'] < 1000000
            and type(after['status']) is int and after['status'] == 5, 'Native birth/ownership identity differs')
    for name in ('stdin', 'stdout', 'stderr'):
        path = directory / (name + '.bin')
        require(type(process[name + '_bytes']) is int and process[name + '_bytes'] == path.stat().st_size
                and process[name + '_sha256'] == sha(path), 'Native stream receipt differs: ' + name)
    require(process['stderr_bytes'] == 0, 'Native witness stderr is not empty')
    started = datetime.fromisoformat(process['started_at']); finished = datetime.fromisoformat(process['finished_at'])
    require(started.utcoffset() is not None and finished.utcoffset() is not None and started <= finished,
            'Invalid native observation interval')


def snapshot_observation(directory):
    artifacts, errors = collect_artifacts(directory)
    required = {'start.json', 'active.json', 'process.json', 'spec.json', 'summary.json',
                'stdin.bin', 'stdout.bin', 'stderr.bin', 'expected.stdout', 'trace-framed.etf'}
    required.update(stem + suffix for stem in ARTIFACT_STEMS for suffix in ('.etf', '.txt'))
    require(not errors and required <= set(artifacts), 'Required validated observation artifact missing')
    return artifacts


def reconcile_native(report, plan, output, supervisor):
    """Recheck actual starts, validated observations and their retained bytes."""
    native_receipts, receipt_errors, registered = [], [], []
    passed = report['status'] == COMPLETE
    rows = {row['id']: row for row in plan['profiles']}
    observations = {row['id']: row for row in report['profiles']}
    all_artifacts, errors = collect_artifacts(output)
    receipt_errors.extend(errors)
    for name in sorted(all_artifacts):
        if Path(name).name != 'process.json': continue
        receipt = output / name; directory = receipt.parent
        try:
            require(directory.parent == output and directory.name in rows, 'Unexpected native process receipt')
            process = read(receipt)
            require(type(process['native_process_started']) is bool, 'Invalid native-start flag')
            if process['native_process_started'] is True:
                require(type(process['pid']) is int and process['pid'] > 0 and type(process['pgid']) is int
                        and process['pgid'] == process['pid'], 'Invalid native PID/PGID')
                registered.append(dict(id=directory.name, pid=process['pid'], pgid=process['pgid'], kind=process['kind']))
                native_receipts.append(dict(id=directory.name, pid=process['pid'], pgid=process['pgid'],
                                            process=str(receipt), process_sha256=sha(receipt),
                                            status=process['status']))
                require(process['direct_child_reaped'] is True and process['cleanup_errors'] == []
                        and process.get('artifact_errors', []) == [], 'Owned observation cleanup incomplete')
                if passed:
                    require(observations[directory.name]['benchmark'] == rows[directory.name]['benchmark'],
                            'Observed profile benchmark differs from prepared source')
                    validate_native_receipt(process, rows[directory.name], directory, supervisor, report['controller_pid'])
                    observation = validate_observation(rows[directory.name], directory, supervisor)
                    equal(observation, observations[directory.name]['observation'], 'Retained observation differs from report')
                    require(observations[directory.name]['process'] == str(receipt)
                            and observations[directory.name]['process_sha256'] == sha(receipt), 'Validated process binding differs')
            else:
                require(process['direct_child_reaped'] is False,
                        'Receipt reaped a child without registering its native launch')
        except BaseException as error:
            receipt_errors.append(dict(path=str(receipt), error=str(error) or type(error).__name__))
    try:
        key = lambda row: (row['id'], row['pid'], row['pgid'], row['kind'])
        equal(sorted(registered, key=key), sorted(report['native_process_ids'], key=key), 'Native launch and receipt identities differ')
        require(type(report['native_processes_started']) is int and len(registered) == report['native_processes_started'],
                'Native launch and receipt counts differ')
        if passed:
            require(len(rows) == len(observations) == len(report['profiles']) == len(registered) == 20
                    and set(observations) == {r['id'] for r in registered} == set(rows)
                    and type(report['diagnostic_mains_observed']) is int and report['diagnostic_mains_observed'] == 20
                    and type(report['native_launch_requests']) is int and report['native_launch_requests'] == 20
                    and report['active'] is None, 'Successful observation inventory is incomplete')
            require(set(report['validated_profile_artifacts']) == set(rows), 'Validated artifact snapshots incomplete')
        for identity, expected in report['validated_profile_artifacts'].items():
            require(identity in rows, 'Unknown validated artifact profile')
            equal(snapshot_observation(output / identity), expected, 'Validated observation artifact changed or disappeared')
    except BaseException as error:
        receipt_errors.append(dict(error=str(error) or type(error).__name__))
    report['native_process_receipts'] = native_receipts
    report['observed_native_process_receipts'] = len(native_receipts)
    report['process_receipt_errors'] = receipt_errors
    return receipt_errors


def finish_run(report, pins, output, supervisor, lock, plan):
    """Called with stop signals blocked, after the owned observer cleaned up."""
    receipt_errors = reconcile_native(report, plan, output, supervisor)
    if receipt_errors:
        report['status'] = 'failed-process-receipt-reconciliation'
    for path, digest in pins.items():
        try:
            require(sha(path) == digest, 'Pinned input changed')
        except BaseException as error:
            report['integrity_errors'].append(dict(path=path, error=str(error) or type(error).__name__))
    if report['integrity_errors']:
        report['status'] = 'failed-input-integrity'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    save(output / 'report.json', report)
    artifacts, artifact_errors = {}, []
    try:
        artifacts, artifact_errors = collect_artifacts(output)
        for identity, expected in report['validated_profile_artifacts'].items():
            for name, binding in expected.items():
                equal(artifacts.get(identity + '/' + name), binding, 'Terminal bytes differ from validated observation')
    except BaseException as error:
        artifact_errors.append(dict(path=str(output), error=str(error) or type(error).__name__))
    if artifact_errors:
        report.update(status='failed-artifact-integrity', artifact_errors=artifact_errors)
        save(output / 'report.json', report)
        artifacts['report.json'] = dict(bytes=(output / 'report.json').stat().st_size,
                                        sha256=sha(output / 'report.json'))
    supervisor.kh.verify_lock(lock)
    new_json(output / 'terminal.json', dict(status=report['status'], report_sha256=sha(output / 'report.json'),
             available_evidence=artifacts, integrity_errors=report['integrity_errors'],
             artifact_errors=artifact_errors, native_processes_started=report['native_processes_started'],
             observed_native_process_receipts=report['observed_native_process_receipts'],
             native_process_receipts=report['native_process_receipts'],
             process_receipt_errors=receipt_errors,
             diagnostic_mains_observed=report['diagnostic_mains_observed'], common_mutex_held=True,
             subject_recompilations=0, benchmark_samples=0, **UNQUALIFIED))
    require(not report['integrity_errors'] and not artifact_errors and not receipt_errors,
            'Input, observation artifact, or native receipt integrity failed')


def run(args, lock):
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan hash differs')
    plan = read(args.plan)
    require(plan['schema'] == 'elixir-retained-beam-compiled-work-plan-v1'
            and plan['controller_sha256'] == sha(__file__), 'Wrong plan/controller identity')
    require(plan['proposed_diagnostic_main_processes'] == 20
            and len(plan['profiles']) == 20
            and {r['id'] for r in plan['profiles']} ==
            {'elixir-' + b + '-' + v for b in CASE for v in ('compact', 'optimized')},
            'Twenty separate retained form witnesses required')
    for path, digest in plan['pins'].items():
        require(sha(path) == digest, 'Pinned input changed: ' + path)
    supervisor = load_supervisor()
    supervisor.kh.verify_lock(lock)
    require((plan['native_timeout_seconds'], plan['maximum_process_group_rss_bytes'], plan['per_file_limit_bytes'])
            == (supervisor.TIMEOUT, supervisor.RSS_LIMIT, supervisor.FILE_LIMIT), 'Native supervision limits changed')
    output = fresh_stage_path(plan['output']); output.mkdir(parents=True)
    pins = dict(plan['pins'], **{str(args.plan.resolve()): args.plan_sha256})
    report = dict(schema='elixir-retained-beam-compiled-work-results-v1', status='running',
                  plan=str(args.plan.resolve()), plan_sha256=args.plan_sha256, pins=pins,
                  profiles=[], native_processes_started=0, diagnostic_mains_observed=0,
                  active=None, subject_recompilations=0, benchmark_samples=0,
                  controller_pid=os.getpid(), native_process_ids=[], native_launch_requests=0,
                  validated_profile_artifacts={},
                  integrity_errors=[], **UNQUALIFIED)
    save(output / 'report.json', report)
    try:
        for row in plan['profiles']:
            require(row['reference_case']['case'] == CASE[row['benchmark']], 'Unexpected bounded case')
            supervisor.kh.verify_lock(lock)
            hot = row['physical_inputs'] + row['beams'] + [row['reference_case']['expected']]
            if row['reference_case']['stdin']:
                hot.append(row['reference_case']['stdin'])
            for item in hot:
                require(sha(item['path']) == item['sha256'], 'Active retained form/reference changed')
            directory = output / row['id']; directory.mkdir()
            for name in ('home', 'config', 'tmp'):
                (directory / name).mkdir()
            spec = dict(row['witness_spec'], artifact_dir=str(directory), lock_fd=lock.fileno())
            new_json(directory / 'spec.json', spec)
            case = row['reference_case']
            payload = Path(case['stdin']['path']).read_bytes() if case['stdin'] else b''
            (directory / 'stdin.bin').write_bytes(payload)
            (directory / 'expected.stdout').write_bytes(Path(case['expected']['path']).read_bytes())
            command = [row['retained_command'][0], '-pa', spec['ebin'], plan['probe'], str(directory / 'spec.json')]
            environment = dict(row['runtime_environment'], HOME=str(directory / 'home'),
                               XDG_CONFIG_HOME=str(directory / 'config'), TMPDIR=str(directory / 'tmp') + os.sep,
                               ERL_CRASH_DUMP=str(directory / 'erl-crash.dump'))
            report['active'] = dict(id=row['id'], pid=None, process=str(directory / 'process.json'))
            report['native_launch_requests'] += 1
            save(output / 'report.json', report)

            def launched(pid):
                report['native_processes_started'] += 1
                report['native_process_ids'].append(dict(id=row['id'], pid=pid, pgid=pid, kind='elixir-compiled-work-witness'))
                report['active']['pid'] = pid
                save(output / 'report.json', report)

            receipt = supervisor.observe(command, environment, directory, payload, lock, launched,
                                         kind='elixir-compiled-work-witness')
            validate_native_receipt(receipt, row, directory, supervisor, report['controller_pid'])
            observation = validate_observation(row, directory, supervisor)
            report['validated_profile_artifacts'][row['id']] = snapshot_observation(directory)
            report['profiles'].append(dict(id=row['id'], benchmark=row['benchmark'],
                                           process=str(directory / 'process.json'),
                                           process_sha256=sha(directory / 'process.json'),
                                           observation=observation))
            report['diagnostic_mains_observed'] += 1; report['active'] = None
            save(output / 'report.json', report)
            print('Collected retained Elixir compiled work: ' + row['id'], flush=True)
        require(report['native_processes_started'] == report['diagnostic_mains_observed'] == 20,
                'Incomplete compiled-work observations')
        report['status'] = COMPLETE
    except BaseException as error:
        report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        raise
    finally:
        with supervisor.atomic():
            finish_run(report, pins, output, supervisor, lock, plan)


def qualify(args):
    """Close the existing work contract from a concrete review of actual artifacts.

    decisions.profiles maps each exact ID to compiled_review (one evidence
    record per numbered contract obligation, in order). Each record contains
    passed=true, a nonempty finding, and citations with artifact SHA-256 and
    function/label location. This is an explicit review record, never an
    automated inference that a positive flag alone proves machine semantics.
    """
    require(sha(args.report) == args.report_sha256 and sha(args.decisions) == args.decisions_sha256,
            'Reviewed observation or decision hash differs')
    report, decisions = read(args.report), read(args.decisions)
    require(report['status'] == COMPLETE
            and report['diagnostic_mains_observed'] == 20 and report['active'] is None
            and len(report['profiles']) == 20 and {p['id'] for p in report['profiles']} ==
            {'elixir-' + b + '-' + v for b in CASE for v in ('compact', 'optimized')}
            and report['native_processes_started'] == report['observed_native_process_receipts'] == 20
            and report['process_receipt_errors'] == []
            and report['integrity_errors'] == []
            and not report.get('error') and not report.get('error_type'), 'Compiled observations are incomplete')
    terminal_path = args.report.parent / 'terminal.json'
    terminal_sha = sha(terminal_path)
    terminal = read(terminal_path)
    require(terminal['report_sha256'] == args.report_sha256
            and terminal['status'] == report['status']
            and terminal['integrity_errors'] == terminal['artifact_errors'] == []
            and terminal['common_mutex_held'] is True,
            'Observation terminal differs')
    require(terminal['process_receipt_errors'] == []
            and terminal['observed_native_process_receipts'] == terminal['native_processes_started'] == 20,
            'Observation terminal native ledger differs')
    equal(terminal['native_process_receipts'], report['native_process_receipts'], 'Report/terminal process receipts differ')
    for item in (report, terminal):
        for key, value in UNQUALIFIED.items(): equal(item[key], value, 'Unreviewed observation granted qualification')
    plan_path = Path(report['plan'])
    require(sha(plan_path) == report['plan_sha256'] and report['pins'][str(plan_path)] == report['plan_sha256'],
            'Observation plan binding differs')
    plan = read(plan_path)
    require(plan['schema'] == 'elixir-retained-beam-compiled-work-plan-v1'
            and plan['controller_sha256'] == sha(__file__)
            and plan['controller'] == str(Path(__file__).resolve()), 'Observation used another controller/plan')
    equal(report['pins'], dict(plan['pins'], **{str(plan_path): report['plan_sha256']}),
          'Observation input closure differs from prepared plan')
    require(report['pins'].get(str(STAGE / 'contracts.json')) == sha(STAGE / 'contracts.json'),
            'Compiled-work contract is not bound by the observation')
    inventory, inventory_errors = collect_artifacts(args.report.parent)
    require(not inventory_errors, 'Observation inventory is unreadable')
    equal({k: v for k, v in inventory.items() if k != 'terminal.json'}, terminal['available_evidence'],
          'Closed observation artifact inventory differs')
    for name, item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe evidence path')
        require(sha(args.report.parent / name) == item['sha256'], 'Direct observation artifact changed')
    for path, digest in report['pins'].items():
        require(sha(path) == digest, 'Reviewed input changed')
    reproduced = copy.deepcopy(report)
    require(not reconcile_native(reproduced, plan, args.report.parent, load_supervisor()),
            'Saved native observations fail independent final reconciliation')
    for name in ('native_process_receipts', 'observed_native_process_receipts', 'process_receipt_errors'):
        equal(reproduced[name], report[name], 'Saved native accounting differs: ' + name)
    contracts = read(STAGE / 'contracts.json')
    require(decisions['schema'] == 'elixir-direct-compiled-work-review-v1'
            and decisions['report_sha256'] == args.report_sha256
            and set(decisions['profiles']) == {p['id'] for p in report['profiles']},
            'Review must cover each of the twenty actual compiled forms')
    for profile in report['profiles']:
        require(profile['observation']['validation']['reference_match'] is True
                and profile['observation']['summary']['dynamic_assertions_passed'] is True,
                'Missing successful dynamic/output observation')
        entries = decisions['profiles'][profile['id']]['compiled_review']
        require(len(entries) == len(contracts['benchmarks'][profile['benchmark']]['compiled_review']),
                'Review does not cover every required compiled-work obligation')
        for index, entry in enumerate(entries, 1):
            require(type(entry['obligation']) is int and entry['obligation'] == index
                    and entry['passed'] is True and entry['finding'].strip()
                    and entry['citations'], 'Missing actual compiled-work finding')
            for citation in entry['citations']:
                name = citation['artifact']
                require(name.startswith(profile['id'] + '/')
                        and terminal['available_evidence'][name]['sha256'] == citation['sha256']
                        and citation['location'].strip(), 'Review citation is not tied to this compiled form')
            disassembly = {profile['id'] + '/' + name + '-disassembly.txt' for name in ('main', 'support')}
            require(any(c['artifact'] in disassembly for c in entry['citations']),
                    'Every obligation requires direct decoded instruction evidence')
    destination = fresh_stage_path(args.output)
    require(not destination.is_relative_to(args.report.parent.resolve()), 'Qualification cannot alter closed native evidence')
    final_inventory, errors = collect_artifacts(args.report.parent)
    require(not errors, 'Observation inventory became unreadable')
    equal(final_inventory, inventory, 'Observation artifacts changed during review')
    require(sha(terminal_path) == terminal_sha and sha(args.decisions) == args.decisions_sha256,
            'Review/terminal changed during qualification')
    for path, digest in report['pins'].items(): require(sha(path) == digest, 'Reviewed input changed during qualification')
    result = dict(schema='elixir-retained-compiled-work-qualified-v1', status='all20-compiled-required-work-qualified',
                  source_work_qualified=True, compiled_work_profiles=20,
                  report=str(args.report.resolve()), report_sha256=args.report_sha256,
                  decisions=str(args.decisions.resolve()), decisions_sha256=args.decisions_sha256,
                  terminal=str(terminal_path.resolve()), terminal_sha256=terminal_sha,
                  bounded_cases_reused=156, subject_recompilations=0, benchmark_samples=0,
                  canonical_loc=None, formatted_loc=None, full_timings_qualified=False, chart_admission=False)
    new_json(destination, result)
    print(json.dumps(dict(status=result['status'], receipt=str(destination), sha256=sha(destination))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    draft_parser = sub.add_parser('draft', help='Read metadata and write an unverified, unexecuted draft inventory')
    draft_parser.add_argument('--output', type=Path, required=True)
    frozen = sub.add_parser('prepare', help='Freeze a concrete plan under the free common timing mutex')
    frozen.add_argument('--plan', type=Path, required=True)
    frozen.add_argument('--output', type=Path, required=True)
    native = sub.add_parser('run', help='Run twenty serial small witnesses; never recompile subjects')
    native.add_argument('--plan', type=Path, required=True)
    native.add_argument('--plan-sha256', required=True)
    reviewed = sub.add_parser('qualify', help='Record direct instruction/dataflow review of actual evidence')
    reviewed.add_argument('--report', type=Path, required=True)
    reviewed.add_argument('--report-sha256', required=True)
    reviewed.add_argument('--decisions', type=Path, required=True)
    reviewed.add_argument('--decisions-sha256', required=True)
    reviewed.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve()
            and sys.flags.isolated == 1 and sys.flags.no_site == 1
            and sys.dont_write_bytecode and sys.flags.optimize == 0,
            'Use the exact retained Python with -I -S -B and no optimization')
    if args.action == 'draft':
        result = inventory()
        new_json(fresh_stage_path(args.output), result)
        print(json.dumps(dict(status=result['status'], profiles=len(result['profiles']),
                              native_executions=0, pins_verified=False, **UNQUALIFIED)))
        return
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Elixir compiled-work qualification interrupted: ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held, named = os.fstat(lock.fileno()), LOCK.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                and held.st_ino == 79859134, 'Common timing lock changed')
        require(sha(PYTHON) == PYTHON_SHA, 'Retained controller Python changed')
        if args.action == 'prepare':
            prepare(args, lock)
        elif args.action == 'run':
            run(args, lock)
        else:
            qualify(args)


if __name__ == '__main__':
    main()
