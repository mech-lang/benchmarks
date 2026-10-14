#!/usr/bin/env python3
"""Compile and check the new linear Prolog candidate, under the common mutex.

This is bounded conformance evidence only. It does not qualify source work,
source counts, a full workload, or chart admission. The original implementation
and its cancelled study are immutable prerequisites, not replacement results.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/prolog/revcomp-linear-v1'
RETAINED_PLAN = ROOT/'experiments/prolog/full90-v1/plan.json'
RETAINED_PLAN_SHA = '55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a'
CANDIDATE_SHA = 'bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322'
FIXTURES_SHA = '0e761400188ce52ec987135fca94975cea41cef8eaac7af5fcc89c4c92f79e4a'
PREPARER = ROOT/'archive/languages/prolog/20261013/revisions/prepare-success-halt-v1/tools/prepare_qlf.pl'
PREPARER_SHA = '1969d7d1cdb6ac33ffb0135ac9c5335c9b5aaf18b16f75f345e449a495ec147e'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
STARTUP_REVIEW_SHA = '41cba7bd637d0c11c15c86dac884c81d27c6b87dfaa2a00929e8676757c8a9c8'
CAPACITIES = (None, 1, 2, 3, 7, 59, 60, 61, 64, 127)
FLAGS = ['-q', '-O', '-f', 'none', '--stack-limit=8g']
COMPILE_WARNING = (b'Warning: [Thread main] Local definition of clbg_prepare:main/0 '
                   b'overrides weak import from clbg_revcomp_linear\n')


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def module(path, expected, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Executable source changed: '+str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


# Definition-only imports: no process launch, prerequisite replay, or large hash.
kb = module(ROOT/'tools/qualification/kotlin_bounded_v2.py', OBSERVER_SHA, 'revcomp_bounded_observer')
save = kb.save


def bind(pins, path, digest=None):
    path = Path(path).resolve()
    actual = sha(path)
    require(digest is None or actual == digest, 'Changed input: '+str(path))
    require(str(path) not in pins or pins[str(path)] == actual, 'Conflicting pin: '+str(path))
    pins[str(path)] = actual
    return str(path)


def verify_pins(pins):
    errors = []
    for path, expected in pins.items():
        try:
            require(sha(path) == expected, 'Pinned bytes changed')
        except BaseException as error:
            errors.append(dict(path=path, error=str(error) or type(error).__name__))
    return errors


def schedule(manifest):
    cases = manifest['cases']
    require(manifest['schema'] == 'prolog-revcomp-linear-fixtures-v1' and
            manifest['generator_sha256'] == FIXTURES_SHA and
            manifest['diagnostic_chunk_sizes'] == list(CAPACITIES[1:]), 'Wrong fixture protocol')
    require(len(cases) == len({r['id'] for r in cases}) == 54 and
            sum(r['expected_status'] == 'success' for r in cases) == 47 and
            sum(r['expected_status'] == 'invalid-iupac' for r in cases) == 7,
            'Expected 47 success and seven rejection fixtures')
    result = []
    for capacity in CAPACITIES:
        for case in cases:
            require(re.fullmatch(r'[a-z0-9-]+', case['id']), 'Unsafe fixture ID')
            mode = 'production' if capacity is None else 'capacity-'+str(capacity)
            result.append(dict(id=mode+'-'+case['id'], capacity=capacity, case=case))
    require(len(result) == 540, 'Incomplete bounded schedule')
    return result


def candidate_command(binary, compiled, capacity):
    require(capacity in CAPACITIES and (capacity is None or type(capacity) is int), 'Unplanned capacity')
    goal = 'clbg_revcomp_linear:run' if capacity is None else 'clbg_revcomp_linear:diagnostic('+str(capacity)+')'
    # Both selected entries halt themselves. The later initialization(main)
    # hook cannot execute a second application entry after this explicit goal.
    return [binary]+FLAGS+['-s', str(compiled), '-g', goal]


def required_pins():
    return {str(path.resolve()):digest for path, digest in [
        (RETAINED_PLAN, RETAINED_PLAN_SHA), (PACKET/'candidate.pl', CANDIDATE_SHA),
        (PACKET/'fixtures.py', FIXTURES_SHA), (PREPARER, PREPARER_SHA),
        (PACKET/'startup-protocol-review.md', STARTUP_REVIEW_SHA),
        (ROOT/'tools/qualification/kotlin_bounded_v2.py', OBSERVER_SHA),
        (ROOT/'tools/qualification/kotlin_helpers.py', kb.HELPER_CONTROLLER_SHA),
        (ROOT/'tools/qualification/elixir_bounded.py', kb.REFERENCE_CONTROLLER_SHA),
        (kb.kh.PYTHON, kb.kh.PYTHON_SHA), (Path(__file__), sha(__file__))]}


def validate_plan(plan):
    expected = dict(schema='prolog-revcomp-linear-bounded-plan-v1',
        status='prepared-awaiting-native-execution', controller=str(Path(__file__).resolve()),
        controller_sha256=sha(__file__), candidate_source=str(PACKET/'candidate.pl'),
        candidate_sha256=CANDIDATE_SHA, retained_plan_sha256=RETAINED_PLAN_SHA,
        planned_compiler_processes=1, planned_inspection_processes=1, planned_candidate_processes=540,
        expected_success_cases=470, expected_rejection_cases=70, process_timeout_seconds=kb.TIMEOUT,
        cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT, maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        native_file_limit_bytes=kb.FILE_LIMIT, maximum_live_subject_processes=1, automatic_retries=0,
        benchmark_samples=0, source_work_qualified=False, canonical_loc=None, formatted_loc=None,
        full_timings_qualified=False, chart_admission=False)
    for key, value in expected.items():
        require(type(plan.get(key)) is type(value) and plan.get(key) == value, 'Plan policy differs: '+key)
    for key in ('output','fixtures'):
        path = Path(plan[key])
        require(path.is_absolute() and path.resolve() == path and path.is_relative_to(PACKET),
                'Candidate path escapes its packet: '+key)
    raw = RETAINED_PLAN.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == RETAINED_PLAN_SHA, 'Retained study plan changed')
    retained = json.loads(raw)
    profile = retained['manifests']['revcomp']['profiles'][0]
    require(plan['binary'] == profile['binary'] and plan['environment'] == profile['runtime_environment'],
            'Prepared runtime identity/environment differs')
    require(all(plan['pins'].get(path) == digest for path, digest in retained['pins'].items()),
            'Retained input pin omitted or substituted')
    require(all(plan['pins'].get(path) == digest for path, digest in required_pins().items()),
            'Candidate, oracle, controller or protocol pin omitted or substituted')
    fixtures = Path(plan['fixtures'])
    manifest_path = fixtures/'manifest.json'
    raw = manifest_path.read_bytes()
    require(plan['pins'].get(str(manifest_path)) == hashlib.sha256(raw).hexdigest(), 'Fixture manifest is not pinned')
    manifest = json.loads(raw)
    require(plan['schedule'] == schedule(manifest), 'Schedule changed')
    for case in manifest['cases']:
        for field, hashfield in [('stdin','input_sha256'), ('stdout','output_sha256')]:
            if field in case:
                relative = Path(case[field])
                require(not relative.is_absolute() and '..' not in relative.parts and
                        plan['pins'].get(str(fixtures/relative)) == case[hashfield],
                        'Fixture byte pin omitted or substituted')


def preparation_command(binary, mode, source, directory, authored):
    require(mode in ('compile', 'inspect'), 'Unknown preparation mode')
    return [binary]+FLAGS+['-l', str(PREPARER), '-g', 'clbg_prepare:main', '--', mode,
            str(source), str(directory/'loaded-inputs.json'), str(directory/'candidate.wam'), str(authored)]


def prepare(args):
    require(not args.plan.exists() and not args.output.exists() and not args.fixtures.exists(),
            'Plan, fixture directory and run output must be fresh')
    plan_path, output, fixtures = args.plan.resolve(), args.output.resolve(), args.fixtures.resolve()
    require(plan_path.is_relative_to(PACKET) and output.is_relative_to(PACKET) and fixtures.is_relative_to(PACKET),
            'Candidate artifacts must remain inside their own packet')
    require(not plan_path.is_relative_to(output) and not fixtures.is_relative_to(output), 'Inputs overlap run output')
    require(sha(RETAINED_PLAN) == RETAINED_PLAN_SHA, 'Retained study plan changed')
    retained = json.loads(RETAINED_PLAN.read_bytes())
    # Preserve the complete previously prepared physical runtime/dependency
    # closure. Verification happens only with the common mutex held.
    pins = dict(retained['pins'])
    require(not verify_pins(pins), 'Retained physical prerequisite closure changed')
    profile = retained['manifests']['revcomp']['profiles'][0]
    require(profile['id'] == 'prolog-revcomp-compact' and
            pins[profile['binary']] == profile['binary_sha256'], 'Wrong retained runtime')
    for path, digest in [(RETAINED_PLAN, RETAINED_PLAN_SHA), (PACKET/'candidate.pl', CANDIDATE_SHA),
                         (PACKET/'fixtures.py', FIXTURES_SHA), (PREPARER, PREPARER_SHA),
                         (ROOT/'tools/qualification/kotlin_bounded_v2.py', OBSERVER_SHA),
                         (PACKET/'startup-protocol-review.md', STARTUP_REVIEW_SHA),
                         (kb.kh.PYTHON, kb.kh.PYTHON_SHA), (Path(__file__), None)]:
        bind(pins, path, digest)
    for dependency in ('kotlin_helpers.py', 'elixir_bounded.py'):
        bind(pins, ROOT/'tools/qualification'/dependency)
    generator = module(PACKET/'fixtures.py', FIXTURES_SHA, 'revcomp_independent_fixture_oracle')
    generator.self_check()
    manifest = generator.write_fixtures(fixtures)
    rows = schedule(manifest)
    bind(pins, fixtures/'manifest.json')
    for row in manifest['cases']:
        for field, hashfield in [('stdin', 'input_sha256'), ('stdout', 'output_sha256')]:
            if field in row:
                relative = Path(row[field])
                require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe fixture path')
                bind(pins, fixtures/relative, row[hashfield])
    plan = dict(schema='prolog-revcomp-linear-bounded-plan-v1',
        status='prepared-awaiting-native-execution', controller=str(Path(__file__).resolve()),
        controller_sha256=sha(__file__), output=str(output), fixtures=str(fixtures),
        binary=profile['binary'], environment=profile['runtime_environment'], pins=pins,
        candidate_source=str(PACKET/'candidate.pl'), candidate_sha256=CANDIDATE_SHA,
        retained_plan_sha256=RETAINED_PLAN_SHA, schedule=rows,
        planned_compiler_processes=1, planned_inspection_processes=1, planned_candidate_processes=540,
        expected_success_cases=470, expected_rejection_cases=70,
        process_timeout_seconds=kb.TIMEOUT, cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT, native_file_limit_bytes=kb.FILE_LIMIT,
        maximum_live_subject_processes=1, automatic_retries=0, benchmark_samples=0,
        source_work_qualified=False, canonical_loc=None, formatted_loc=None,
        full_timings_qualified=False, chart_admission=False)
    require(not plan_path.exists(), 'Plan appeared during preparation')
    save(plan_path, plan)
    print(json.dumps(dict(plan=str(plan_path), sha256=sha(plan_path),
                         planned_candidate_processes=540, native_executions=0)))


def check_receipt(directory, command, environment, payload, pid, expected_failure=False, compiler_warning=False):
    directory = Path(directory)
    records = {name:json.loads((directory/(name+'.json')).read_bytes()) for name in ('start','active','process')}
    final, active = records['process'], records['active']
    for name, record in records.items():
        require(record['command'] == command and record['environment'] == environment and
                record['cwd'] == str(directory) and record['stdin_bytes'] == len(payload) and
                record['stdin_sha256'] == hashlib.sha256(payload).hexdigest() and
                record['kind'] == 'prolog-revcomp-bounded', 'Native input receipt differs: '+name)
        require(record['inherited_common_mutex'] is True and record['common_mutex_inode'] == kb.LOCK_INODE and
                record['process_timeout_seconds'] == kb.TIMEOUT and
                record['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT and
                record['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and
                record['native_file_limit_bytes'] == kb.FILE_LIMIT and
                record['stdout_capture_limit_bytes'] == kb.FILE_LIMIT+kb.PIPE_CHUNK,
                'Native supervision policy differs')
    require(records['start']['status'] == 'starting' and records['start']['native_process_started'] is False and
            active['status'] == 'running' and active['native_process_started'] is True, 'Native launch states differ')
    identity = active['identity']
    require(active['pid'] == active['pgid'] == final['pid'] == final['pgid'] == pid and
            final['identity'] == identity and identity['pid'] == identity['pgid'] == pid and
            identity['ppid'] == os.getpid() and
            final['native_process_started'] is True and final['direct_child_reaped'] is True and
            final['remaining_process_group'] == [] and not final['stop_signals'] and
            not final['cleanup_errors'] and not final.get('artifact_errors') and
            not final.get('timed_out') and final['kernel_monitor_samples'] > 0 and
            final['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT,
            'Unclean or unowned native lifetime')
    leader = final['leader_identity_before_reap']
    require(leader['status'] == 5 and all(leader[k] == identity[k] for k in
            ('pid','pgid','ppid','birth_seconds','birth_microseconds')), 'Native identity changed before reap')
    require(not (expected_failure and compiler_warning), 'Conflicting expected native outcomes')
    expected = ('failed', 1) if expected_failure else ('failed', 0) if compiler_warning else ('native-passed', 0)
    require((final['status'], final['exit_status']) == expected, 'Unexpected native status')
    if expected_failure:
        require(final['error_type'] == 'AssertionError' and final['error'] == 'Native command exited unsuccessfully',
                'Invalid-input case failed for an unrelated observer reason')
    elif compiler_warning:
        require(final['error_type'] == 'AssertionError' and final['error'] == 'Unexpected stderr; raw bytes retained',
                'Compiler failed for an unrelated observer reason')
    for name in ('stdout','stderr'):
        raw = (directory/(name+'.bin')).read_bytes()
        require(len(raw) == final[name+'_bytes'] and hashlib.sha256(raw).hexdigest() == final[name+'_sha256'],
                'Native output artifact changed')
    return final


def check_case(case, stdout, stderr):
    if case['expected_status'] == 'success':
        require(not stderr and len(stdout) == case['output_bytes'] and
                hashlib.sha256(stdout).hexdigest() == case['output_sha256'], 'Complete output differs')
        return 'exact-output'
    require(case['expected_status'] == 'invalid-iupac', 'Unknown expected result')
    # SWI's retained English domain-error formatter; no arbitrary stderr suffix
    # or generic nonzero-exit acceptance is permitted.
    code = str(case['expected_invalid_code']).encode()
    expected = b"ERROR: [Thread main] Domain error: `iupac_nucleotide' expected, found `"+code+b"'\n"
    require(stderr == expected, 'Expected invalid IUPAC code not reported exactly')
    # All seven pinned rejection fixtures contain one >r header and fewer
    # than sixty bases. The error printer flushes the header already written;
    # the unfinished sequence line has not been emitted.
    require(stdout == b'>r\n', 'Invalid-input output prefix differs')
    return 'expected-invalid-iupac'


def check_compiler_metadata(directory, mode, target, authored, plan):
    data = json.loads((directory/'loaded-inputs.json').read_bytes())
    runtime = data['runtime']
    require(data['mode'] == mode and data['target'] == str(target) and data['wam'] == str(directory/'candidate.wam'),
            'Compile/inspection target differs')
    require(runtime['version_components'] == [10,0,2] and runtime['version_data'] == 'swi(10,0,2,[])' and
            runtime['architecture'] == 'arm64-darwin' and runtime['bounded'] is False and runtime['gc'] is True and
            runtime['stack_limit'] == 8*1024**3 and runtime['home'] == plan['environment']['SWI_HOME_DIR'],
            'Retained SWI runtime policy differs')
    require(str(authored/'candidate.pl') in data['loaded_sources'], 'Compiled authored source absent')
    for path in data['loaded_sources']:
        require(path == str(authored/'candidate.pl') or path in plan['pins'], 'Unpinned compiler source: '+path)
    for library in data['foreign_libraries']:
        require(library['resolved_path'] in plan['pins'], 'Unpinned foreign compiler dependency')
    wam = (directory/'candidate.wam').read_text()
    require('clbg_revcomp_linear:read_blocks/2' in wam and 'clbg_revcomp_linear:emit_codes/5' in wam,
            'Candidate VM listing missing required parser/emitter predicates')
    return data


def inventory(output):
    artifacts = {}
    for path in sorted(output.rglob('*')):
        require(not path.is_symlink(), 'Symlink in native artifacts')
        if path.is_file():
            artifacts[str(path.relative_to(output))] = dict(bytes=path.stat().st_size, sha256=sha(path))
    return artifacts


def run(args, lock):
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan)
    pins = dict(plan['pins'])
    bind(pins, args.plan, args.plan_sha256)
    require(not verify_pins(pins), 'Prepared physical inputs changed')
    manifest = json.loads((Path(plan['fixtures'])/'manifest.json').read_bytes())
    require(plan['schedule'] == schedule(manifest), 'Schedule changed')
    output = Path(plan['output'])
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema='prolog-revcomp-linear-bounded-report-v1', status='running',
        started_at=datetime.now(timezone.utc).isoformat(), plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256, pins=pins, commands=[], active=None, native_processes_started=0,
        qualified_cases=0, successful_cases=0, rejected_cases=0, bounded_conformance_qualified=False,
        source_work_qualified=False, canonical_loc=None, formatted_loc=None,
        full_timings_qualified=False, benchmark_samples=0, chart_admission=False)
    save(output/'report.json', report)
    snapshots = {}

    def execute(name, command, payload=b'', expected_failure=False, compiler_warning=False):
        directory = output/name
        directory.mkdir()
        entry = dict(id=name, command=command, environment=plan['environment'], cwd=str(directory), pid=None,
                     expected_failure=expected_failure, compiler_warning=compiler_warning, stdin_bytes=len(payload),
                     stdin_sha256=hashlib.sha256(payload).hexdigest(), status='starting')
        report['commands'].append(entry)
        report['active'] = name
        save(output/'report.json', report)
        def launched(pid):
            entry['pid'] = pid
            report['native_processes_started'] += 1
            save(output/'report.json', report)
        try:
            kb.observe(command, plan['environment'], directory, payload, lock, launched,
                       kind='prolog-revcomp-bounded')
        except AssertionError as error:
            expected_error = ('Native command exited unsuccessfully' if expected_failure else
                              'Unexpected stderr; raw bytes retained' if compiler_warning else None)
            if str(error) != expected_error:
                raise
        receipt = check_receipt(directory, command, plan['environment'], payload, entry['pid'],
                                expected_failure, compiler_warning)
        if compiler_warning:
            require((directory/'stderr.bin').read_bytes() == COMPILE_WARNING, 'Unfamiliar compiler diagnostic')
        entry.update(status='native-lifetime-verified', process_sha256=sha(directory/'process.json'),
                     stdout_sha256=receipt['stdout_sha256'], stderr_sha256=receipt['stderr_sha256'])
        snapshots[name] = inventory(directory)
        report['active'] = None
        save(output/'report.json', report)
        return directory

    try:
        authored = output/'authored'
        authored.mkdir()
        source = authored/'candidate.pl'
        source.write_bytes(Path(plan['candidate_source']).read_bytes())
        require(sha(source) == CANDIDATE_SHA, 'Compiler input copy differs')
        compiled = source.with_suffix('.qlf')
        for mode, target in [('compile', source), ('inspect', compiled)]:
            directory = output/mode
            command = preparation_command(plan['binary'], mode, target, directory, authored)
            execute(mode, command, compiler_warning=True)
            require(not (directory/'stdout.bin').read_bytes() and (directory/'stderr.bin').read_bytes() == COMPILE_WARNING,
                    'Unexpected compiler/inspection output')
            check_compiler_metadata(directory, mode, target, authored, plan)
            require(compiled.is_file() and compiled.stat().st_size > 0, 'Compiled QLF absent')
        report['compiler_bound_source'] = dict(path=str(source), sha256=sha(source), counted=True)
        report['compiled_artifact'] = dict(path=str(compiled), sha256=sha(compiled), bytes=compiled.stat().st_size)
        for row in plan['schedule']:
            require(sha(source) == CANDIDATE_SHA and sha(compiled) == report['compiled_artifact']['sha256'],
                    'Candidate input/QLF changed between cases')
            case = row['case']
            payload = (Path(plan['fixtures'])/case['stdin']).read_bytes()
            command = candidate_command(plan['binary'], compiled, row['capacity'])
            directory = execute(row['id'], command, payload, case['expected_status'] == 'invalid-iupac')
            result = check_case(case, (directory/'stdout.bin').read_bytes(), (directory/'stderr.bin').read_bytes())
            report['commands'][-1].update(status='qualified-case', result=result, fixture=case['id'], capacity=row['capacity'])
            report['qualified_cases'] += 1
            report['successful_cases' if result == 'exact-output' else 'rejected_cases'] += 1
            save(output/'report.json', report)
        require((report['native_processes_started'], report['qualified_cases'], report['successful_cases'],
                 report['rejected_cases']) == (542,540,470,70), 'Incomplete native cohort')
        report.update(status='bounded-conformance-passed-awaiting-work-and-source-count-review',
                      bounded_conformance_qualified=True)
    except BaseException as error:
        report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():
            integrity = verify_pins(pins)
            artifact_errors = []
            for key in ('compiler_bound_source', 'compiled_artifact'):
                if key in report:
                    item = report[key]
                    try:
                        require(sha(item['path']) == item['sha256'], 'Authored source or compiled QLF changed')
                    except BaseException as error:
                        artifact_errors.append(dict(path=item['path'], error=str(error) or type(error).__name__))
            for name, expected in snapshots.items():
                try:
                    require(inventory(output/name) == expected, 'Validated command artifacts changed')
                except BaseException as error:
                    artifact_errors.append(dict(path=name, error=str(error) or type(error).__name__))
            if integrity or artifact_errors:
                report.update(status='failed-integrity', bounded_conformance_qualified=False)
            report.update(integrity_errors=integrity, artifact_errors=artifact_errors,
                          finished_at=datetime.now(timezone.utc).isoformat())
            save(output/'report.json', report)
            artifacts = inventory(output)
            kb.kh.verify_lock(lock)
            require(not (output/'terminal.json').exists(), 'Terminal receipt appeared before finalization')
            save(output/'terminal.json', dict(status=report['status'], report_sha256=sha(output/'report.json'),
                available_evidence=artifacts, integrity_errors=integrity, artifact_errors=artifact_errors,
                native_processes_started=report['native_processes_started'], qualified_cases=report['qualified_cases'],
                bounded_conformance_qualified=report['bounded_conformance_qualified'],
                common_mutex_held=True, common_mutex_inode=kb.LOCK_INODE,
                source_work_qualified=False, full_timings_qualified=False, chart_admission=False))
            require(not integrity and not artifact_errors, 'Closure integrity failed')
    print(json.dumps({k:report[k] for k in ('status','native_processes_started','qualified_cases')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--plan', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--fixtures', required=True, type=Path)
    p = sub.add_parser('run')
    p.add_argument('--plan', required=True, type=Path)
    p.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve(), 'Wrong controller interpreter')
    require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1 and
            sys.flags.optimize == 0, 'Controller requires -I -S -B without optimization')
    with kb.LOCK.open('r+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        kb.kh.verify_lock(lock)
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
        prepare(args) if args.mode == 'prepare' else run(args, lock)


if __name__ == '__main__':
    main()
