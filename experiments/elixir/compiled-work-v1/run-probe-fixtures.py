#!/usr/bin/env python3
"""Run the fifteen diagnostic-only Elixir fixtures once under the timing mutex.

Use the retained Python with -I -S -B, --controller-sha256 REVIEWED_SHA and
--output experiments/elixir/compiled-work-v1/probe-fixtures-v1. No retry or
subject-work qualification is performed. Native execution is a separate step.
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
import stat
import sys

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
READER_PLAN = ROOT/'experiments/elixir/source-counts-v1/plan-v1.json'
READER_PLAN_SHA = 'f65ad1ee110f0dea5c4d20af4166752c2737eb06bccd964c08388896f709bad7'
SUPERVISOR = ROOT/'tools/qualification/kotlin_bounded_v2.py'
SUPERVISOR_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
SOURCE_PINS = {
    'probe.exs': '32a2b9666660e745651abc3fdcba053ce4b134ede7188cd7489a8908932da3c8',
    'probe-review-tests.exs': 'c73a7957d04a4edcc026933db0ef9c8bd5a8cf4e793f85f115ab31bbbe833b06',
}
KIND = 'elixir-diagnostic-fixtures'
COMPLETE = 'diagnostic-fixtures-passed'
REQUEST_FIELDS = ('kind', 'command', 'environment', 'cwd', 'started_at', 'process_timeout_seconds',
    'cleanup_timeout_seconds', 'inherited_common_mutex', 'common_mutex_inode', 'stop_signals', 'cleanup_errors',
    'benchmark_samples', 'stdin_bytes', 'stdin_sha256', 'maximum_process_group_rss_bytes',
    'native_file_limit_bytes', 'stdout_capture_limit_bytes', 'stdout_transport', 'stderr_transport',
    'source_work_qualified', 'chart_admission')


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load_supervisor():
    raw = SUPERVISOR.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SUPERVISOR_SHA, 'Reviewed supervisor changed')
    spec = importlib.util.spec_from_file_location('elixir_probe_fixture_supervisor', SUPERVISOR)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(SUPERVISOR), 'exec'), module.__dict__)
    return module


def inventory(root):
    result, errors = {}, []
    def failed(error):
        errors.append(str(error) or type(error).__name__)
    for directory, children, names in os.walk(root, followlinks=False, onerror=failed):
        retained = []
        for name in children + names:
            path = Path(directory)/name
            try:
                mode = path.lstat().st_mode
                require(not stat.S_ISLNK(mode), 'Unexpected artifact symlink: '+str(path))
                if stat.S_ISREG(mode):
                    result[str(path.relative_to(root))] = dict(bytes=path.stat().st_size, sha256=sha(path))
                else:
                    require(stat.S_ISDIR(mode), 'Nonregular artifact: '+str(path))
                    if name in children:
                        retained.append(name)
            except BaseException as error:
                failed(error)
        children[:] = retained
    return result, errors


def validate_stdout(raw):
    summaries = [tuple(map(int, match.groups())) for line in raw.decode('utf-8').splitlines()
                 if (match := re.fullmatch(r'(\d+) tests?, (\d+) failures?', line))]
    require(summaries == [(15, 0)], 'Expected one ExUnit summary: 15 tests, 0 failures')
    return dict(tests=15, failures=0)


def validate_process(process, report, directory, supervisor):
    require(process['kind'] == KIND and process['status'] == 'native-passed'
            and process['native_process_started'] is True
            and type(process['pid']) is int and process['pid'] > 0
            and type(process['pgid']) is int and process['pgid'] == process['pid']
            and type(process['exit_status']) is int and process['exit_status'] == 0
            and process['direct_child_reaped'] is True and process['remaining_process_group'] == []
            and process['inherited_common_mutex'] is True and process['common_mutex_inode'] == supervisor.LOCK_INODE
            and process['cwd'] == str(directory), 'Fixture process lacks a clean owned exit')
    require(not any(process.get(key) for key in ('error', 'error_type', 'cleanup_errors', 'artifact_errors',
                'stop_signals', 'remaining_after_cleanup', 'timed_out')), 'Fixture process records a failure')
    require(process['command'] == report['command'] and process['environment'] == report['environment']
            and process['source_work_qualified'] is process['chart_admission'] is False
            and process['benchmark_samples'] == 0, 'Fixture command/environment or scope differs')
    for key, expected in (('process_timeout_seconds', supervisor.TIMEOUT),
            ('cleanup_timeout_seconds', supervisor.CLEANUP_TIMEOUT),
            ('maximum_process_group_rss_bytes', supervisor.RSS_LIMIT), ('native_file_limit_bytes', supervisor.FILE_LIMIT),
            ('stdout_capture_limit_bytes', supervisor.FILE_LIMIT + supervisor.PIPE_CHUNK)):
        require(type(process[key]) is int and process[key] == expected, 'Changed resource bound: '+key)
    require(type(process['kernel_monitor_samples']) is int and process['kernel_monitor_samples'] > 0
            and type(process['observed_peak_process_group_rss_bytes']) is int
            and 0 <= process['observed_peak_process_group_rss_bytes'] <= supervisor.RSS_LIMIT,
            'Missing fixture resource observations')
    before, after = process['identity'], process['leader_identity_before_reap']
    require(all(type(before[k]) is int and type(after[k]) is int and before[k] == after[k]
                for k in ('pid', 'ppid', 'pgid', 'birth_seconds', 'birth_microseconds'))
            and before['pid'] == before['pgid'] == process['pid'] and before['ppid'] == report['controller_pid']
            and before['birth_seconds'] > 0 and 0 <= before['birth_microseconds'] < 1000000
            and type(after['status']) is int and after['status'] == 5, 'Fixture ownership identity differs')
    start, active = read(directory/'start.json'), read(directory/'active.json')
    require(start == dict({key: process[key] for key in REQUEST_FIELDS}, status='starting',
        native_process_started=False, kernel_monitor_samples=0, observed_peak_process_group_rss_bytes=0),
        'Fixture start receipt differs')
    require(active == dict(start, status='running', native_process_started=True,
                           pid=process['pid'], pgid=process['pid'], identity=before), 'Fixture active receipt differs')
    for name in ('stdin', 'stdout', 'stderr'):
        path = directory/(name+'.bin')
        require(type(process[name+'_bytes']) is int and process[name+'_bytes'] == path.stat().st_size
                and process[name+'_sha256'] == sha(path), 'Fixture stream receipt differs: '+name)
    require(process['stdin_bytes'] == process['stderr_bytes'] == 0
            and process['stdout_bytes'] <= supervisor.FILE_LIMIT + supervisor.PIPE_CHUNK, 'Unexpected fixture stream size')


def finish(report, pins, output, supervisor, lock):
    errors = []
    process_path = output/'native/process.json'
    observed = []
    if process_path.exists():
        try:
            process = read(process_path)
            require(type(process['native_process_started']) is bool, 'Invalid native-start flag')
            if process['native_process_started']:
                require(type(process['pid']) is int and process['pid'] > 0
                        and type(process['pgid']) is int and process['pgid'] == process['pid']
                        and process['kind'] == KIND, 'Invalid saved native identity')
                observed.append(dict(pid=process['pid'], pgid=process['pgid'], kind=KIND))
                if process.get('direct_child_reaped') is True and not process.get('cleanup_errors') and (
                    process.get('remaining_process_group') == [] or process.get('remaining_after_cleanup') == []):
                    report['active'] = None
            if report['status'] == COMPLETE:
                validate_process(process, report, output/'native', supervisor)
                require(validate_stdout((output/'native/stdout.bin').read_bytes()) == report['fixture_summary'],
                        'Saved ExUnit summary differs')
        except BaseException as error:
            errors.append(str(error) or type(error).__name__)
    if observed != report['native_process_ids'] or len(observed) != report['native_processes_started']:
        errors.append('Actual native receipt and launch ledger differ')
    integrity_errors = []
    for path, expected in pins.items():
        try:
            require(sha(path) == expected, 'Pinned input changed: '+path)
        except BaseException as error:
            integrity_errors.append(str(error) or type(error).__name__)
    artifacts, artifact_errors = inventory(output)
    if report['status'] == COMPLETE:
        native = {name.removeprefix('native/'): item for name, item in artifacts.items() if name.startswith('native/')}
        if native != report.get('validated_native_artifacts'):
            artifact_errors.append('Validated fixture artifacts changed before terminal closure')
        if report['native_processes_started'] != 1 or report['active'] is not None:
            errors.append('Fixture native command did not close exactly once')
    try:
        supervisor.kh.verify_lock(lock)
        lock_held = True
    except BaseException as error:
        lock_held = False
        errors.append(str(error) or type(error).__name__)
    if errors or integrity_errors or artifact_errors:
        report['status'] = 'failed-integrity-or-receipts'
    report.update(process_receipt_errors=errors, integrity_errors=integrity_errors, artifact_errors=artifact_errors,
        observed_native_process_receipts=len(observed), diagnostic_fixtures_passed=report['status'] == COMPLETE,
        finished_at=datetime.now(timezone.utc).isoformat())
    artifacts.pop('report.json', None)
    report_sha = None
    try:
        supervisor.save(output/'report.json', report)
        metadata = dict(bytes=(output/'report.json').stat().st_size, sha256=sha(output/'report.json'))
        report_sha = metadata['sha256']
        artifacts['report.json'] = metadata
    except BaseException as error:
        artifact_errors.append('Report persistence: '+(str(error) or type(error).__name__))
        report.update(status='failed-report-artifact', diagnostic_fixtures_passed=False)
        try:
            supervisor.save(output/'report.json', report)
        except BaseException as save_error:
            artifact_errors.append('Failed report save: '+(str(save_error) or type(save_error).__name__))
    supervisor.save(output/'terminal.json', dict(schema='elixir-probe-fixture-terminal-v1', status=report['status'],
        report_sha256=report_sha, native_processes_started=report['native_processes_started'],
        observed_native_process_receipts=len(observed), native_process_ids=observed,
        diagnostic_fixtures_passed=report['diagnostic_fixtures_passed'], fixture_summary=report.get('fixture_summary'),
        common_mutex_held=lock_held, common_mutex_inode=supervisor.LOCK_INODE,
        process_receipt_errors=errors, integrity_errors=integrity_errors, artifact_errors=artifact_errors,
        available_evidence=artifacts, source_work_qualified=False, chart_admission=False))


def run(args, supervisor, lock):
    output = args.output.resolve()
    require(output.parent == STAGE and not args.output.exists() and not args.output.is_symlink(),
            'Fresh output directly inside compiled-work-v1 required')
    pins = {str(Path(__file__).resolve()): args.controller_sha256, str(READER_PLAN): READER_PLAN_SHA,
            str(SUPERVISOR): SUPERVISOR_SHA, str(supervisor.kh.PYTHON): supervisor.kh.PYTHON_SHA}
    pins.update({str(STAGE/name): digest for name, digest in SOURCE_PINS.items()})
    report = dict(schema='elixir-probe-fixture-results-v1', status='running',
        controller=str(Path(__file__).resolve()), controller_sha256=args.controller_sha256,
        reader_plan=str(READER_PLAN), reader_plan_sha256=READER_PLAN_SHA, pins=pins,
        started_at=datetime.now(timezone.utc).isoformat(), controller_pid=os.getpid(),
        native_processes_started=0, native_process_ids=[], active=None, automatic_retry=False,
        planned_native_processes=1, expected_fixture_tests=15, diagnostic_fixtures_passed=False,
        subject_recompilations=0, subject_main_invocations=0, benchmark_samples=0,
        source_work_qualified=False, canonical_loc=None, formatted_loc=None, chart_admission=False)
    failure = None
    created = False
    try:
        with supervisor.atomic():
            output.mkdir(mode=0o700)
            created = True
            supervisor.save(output/'report.json', report)
        supervisor.kh.verify_lock(lock)
        raw = READER_PLAN.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == READER_PLAN_SHA, 'Retained reader plan changed')
        reader = json.loads(raw)
        require(reader['schema'] == 'elixir-source-reader-plan-v1', 'Wrong retained runtime plan')
        for path, digest in reader['pins'].items():
            require(path not in pins or pins[path] == digest, 'Conflicting retained pin: '+path)
            pins[path] = digest
        for path, digest in pins.items():
            require(sha(path) == digest, 'Pinned input changed: '+path)
        directory = output/'native'; directory.mkdir()
        for name, digest in SOURCE_PINS.items():
            raw = (STAGE/name).read_bytes()
            require(hashlib.sha256(raw).hexdigest() == digest, 'Fixture source changed during copy')
            (directory/name).write_bytes(raw)
            pins[str(directory/name)] = digest
        environment = dict(reader['runtime_environment'])
        for name, folder in (('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'), ('TMPDIR', 'tmp')):
            path = directory/folder; path.mkdir()
            environment[name] = str(path) + (os.sep if name == 'TMPDIR' else '')
        environment['ERL_CRASH_DUMP'] = str(directory/'erl-crash.dump')
        command = [reader['runtime'], str(directory/'probe-review-tests.exs')]
        (directory/'stdin.bin').write_bytes(b'')
        report.update(command=command, environment=environment, runtime_environment=reader['runtime_environment'])
        supervisor.save(output/'report.json', report)
        def launched(pid):
            report['native_processes_started'] += 1
            report['native_process_ids'].append(dict(pid=pid, pgid=pid, kind=KIND))
            report['active'] = dict(pid=pid, pgid=pid, kind=KIND)
            supervisor.save(output/'report.json', report)
        process = supervisor.observe(command, environment, directory, b'', lock, launched, kind=KIND)
        require(read(directory/'process.json') == process, 'Returned and saved fixture receipt differ')
        validate_process(process, report, directory, supervisor)
        report['fixture_summary'] = validate_stdout((directory/'stdout.bin').read_bytes())
        snapshot, errors = inventory(directory)
        required = {'probe.exs', 'probe-review-tests.exs', 'stdin.bin', 'stdout.bin', 'stderr.bin',
                    'start.json', 'active.json', 'process.json'}
        require(not errors and required <= set(snapshot), 'Fixture artifact inventory incomplete')
        report.update(status=COMPLETE, active=None, validated_native_artifacts=snapshot)
    except BaseException as error:
        failure = error
        report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
    finally:
        if created:
            with supervisor.atomic():
                finish(report, pins, output, supervisor, lock)
    if failure is not None:
        raise failure
    require(report['diagnostic_fixtures_passed'] is True, 'Fixture execution or terminal integrity failed')
    print(json.dumps(dict(report=str(output/'report.json'), sha256=sha(output/'report.json'),
                          status=report['status'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--controller-sha256', required=True)
    args = parser.parse_args()
    supervisor = load_supervisor()
    require(Path(sys.executable).resolve() == supervisor.kh.PYTHON.resolve() and sys.flags.isolated
            and sys.flags.no_site and sys.flags.dont_write_bytecode and not sys.flags.optimize,
            'Use pinned Python with -I -S -B and no optimization')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Elixir diagnostic fixtures interrupted: '+str(signum))
    for sig in supervisor.kh.SIGNALS:
        signal.signal(sig, interrupted)
    with supervisor.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        supervisor.kh.verify_lock(lock)
        run(args, supervisor, lock)


if __name__ == '__main__':
    main()
