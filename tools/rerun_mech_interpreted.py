#!/usr/bin/env python3
"""Run 15 retained Mech interpreted forms three times using full-process time.

Fresh output only, 45 serial processes, no retries or automatic continuation.
The common benchmark mutex is held from preflight through terminal recording.
Raw stdout, stderr, process receipts and every measured sample are retained.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import stat
import statistics
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
HELPER = ROOT / 'tools/mech_timing_boundary.py'
HELPER_SHA256 = '27e42b3f54b5cef9c17b8fea65b789b370b7eda714fdd27f575c7850c553001c'
raw = HELPER.read_bytes()
if hashlib.sha256(raw).hexdigest() != HELPER_SHA256:
    raise ValueError('Timing evidence helper changed')
spec = importlib.util.spec_from_file_location('mech_timing_boundary', HELPER)
boundary = importlib.util.module_from_spec(spec)
exec(compile(raw, str(HELPER), 'exec'), boundary.__dict__)

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
CLBG = HOST / 'benchmarks/clbg'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA256 = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
POWER = {'source': 'AC Power', 'low_power_mode': 0}
INPUTS = {
    'sequence': {'path': str(CLBG / 'knucleotide/.build/knucleotide-input25000000.txt'),
                 'bytes': 254166745,
                 'sha256': '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'},
    'regex': {'path': str(CLBG / 'regexredux/.build/input5000000.txt'), 'bytes': 50833411,
              'sha256': '97197f5957a12f8a859ba7edff6d97994daa18afacd77db21fa68c6f2e447e38'},
}
ENVIRONMENT = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C', 'LC_ALL': 'C',
               'RAYON_NUM_THREADS': '8', 'JULIA_NUM_THREADS': '8', 'OMP_NUM_THREADS': '8',
               'OMP_DYNAMIC': 'FALSE', 'CHPL_RT_NUM_THREADS_PER_LOCALE': '8', 'GOMAXPROCS': '8',
               'OPENBLAS_NUM_THREADS': '1', 'PYTHONHASHSEED': '0', 'MECH_TIMINGS': '1'}
COMPILERS = {'rustc', 'clang', 'clang++', 'cc1', 'cc1plus', 'lto1', 'gcc', 'g++', 'swift-frontend'}


def require(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextmanager
def atomic_signals():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, (*SIGNALS, signal.SIGALRM))
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def verify_lock(fd):
    held, named = os.fstat(fd), LOCK.lstat()
    require(stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
            and (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
            and held.st_ino == LOCK_INODE, 'Common timing mutex identity changed')


@contextmanager
def common_lock():
    fd = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_lock(fd)
        yield fd
    finally:
        os.close(fd)


def make_plan(retained_report, output):
    """Pure plan construction; no binaries, inputs, locks or processes touched."""
    rows = boundary._validate_report(retained_report)
    output = Path(output)
    require(output.is_absolute(), 'Output must be absolute')
    programs = {}
    for key, entry in sorted(rows.items()):
        original = entry['row']
        benchmark = original['benchmark']
        stdin = INPUTS['sequence'] if benchmark in ('knucleotide', 'revcomp') else (
            INPUTS['regex'] if benchmark == 'regexredux' else None)
        command = [arg.replace('{n}', str(boundary.WORKLOADS[benchmark][1])) for arg in original['command']]
        require(all('{' not in arg and '}' not in arg for arg in command), 'Unexpanded command placeholder')
        row = {field: deepcopy(original[field]) for field in (
            'source_key', 'benchmark', 'mode', 'language', 'source', 'source_sha256', 'loc',
            'physical_loc', 'loc_expansions', 'binary', 'binary_sha256')}
        row.update(key=key, id=key.split(':', 1)[1], phase='fresh-full-process', command=command,
                   original_command_template=deepcopy(original['command']), cwd=str(HOST),
                   retained_report_selector='/programs/' + original['key'],
                   stdin=deepcopy(stdin), expected_output=deepcopy(original['full_validation']),
                   runtime_environment={**ENVIRONMENT, 'HOME': str(output / 'home'),
                                        'TMPDIR': str(output / 'tmp'), **original['runtime_environment']},
                   original_runtime_overrides=deepcopy(original['runtime_environment']))
        programs[key] = row
    schedule = []
    rng = random.Random(20261014)
    for round_number in range(1, 4):
        order = sorted(programs)
        rng.shuffle(order)
        offset = len(schedule)
        schedule.extend({'ordinal': offset + index + 1, 'round': round_number, 'key': key}
                        for index, key in enumerate(order))
    require(len(schedule) == 45 and all(sum(item['key'] == key for item in schedule) == 3 for key in programs),
            'Expected 45 processes and three samples per retained form')
    return {'schema': 'mech-interpreted-whole-process-v1', 'output': str(output),
            'sample_count': 3, 'planned_native_processes': 45, 'programs': programs, 'schedule': schedule,
            'retained_report': boundary.REPORT, 'retained_report_sha256': boundary.REPORT_SHA256,
            'inputs': deepcopy(INPUTS), 'power_profile': POWER,
            'timing_measurement': 'full-process-wall', 'timing_boundary': boundary.TIMING_BOUNDARY,
            'clock': 'time.perf_counter_ns', 'timer_start': 'Immediately before subprocess.Popen',
            'timer_stop': 'Immediately after blocking child wait returns',
            'historical_phase_diagnostics_ranked': False, 'automatic_retry': False,
            'common_mutex': str(LOCK), 'common_mutex_inode': LOCK_INODE,
            'environment_policy': 'Explicit recorded environment; no ambient variables inherited.'}


def pin_inventory(plan):
    pins = {str(HELPER): HELPER_SHA256,
            str(ROOT / boundary.ARCHIVE_REPORT): boundary.REPORT_SHA256}
    for row in plan['programs'].values():
        for kind in ('source', 'binary'):
            path, digest = row[kind], row[kind + '_sha256']
            require(path not in pins or pins[path] == digest, 'Conflicting prerequisite pin')
            pins[path] = digest
        if row['stdin']:
            pins[row['stdin']['path']] = row['stdin']['sha256']
    pins[str(Path(__file__).resolve())] = CONTROLLER_SHA256
    pins[str(PYTHON.resolve())] = PYTHON_SHA256
    return pins


def state(path):
    info = Path(path).stat()
    require(stat.S_ISREG(info.st_mode), 'Nonregular evidence file: ' + str(path))
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def verify_pins(pins, cache, force=False):
    for path, digest in pins.items():
        before = state(path)
        if force or cache.get(path) != before:
            require(sha(path) == digest and state(path) == before, 'Prerequisite bytes changed: ' + path)
            cache[path] = before


def environment_observation():
    # Same executable-name threshold and power conditions as the retained
    # guard. Full arguments and unrelated environment values are never logged.
    listing = subprocess.check_output(['/bin/ps', '-eo', 'pid,pcpu,comm'], text=True, timeout=10)
    active = []
    for line in listing.splitlines()[1:]:
        fields = line.split(None, 2)
        if len(fields) == 3:
            pid, cpu, command = fields
            name = Path(command).name
            if (name in COMPILERS or re.fullmatch(r'(?:clang|gcc|g\+\+)-\d+', name)) and float(cpu) >= 5:
                active.append({'pid': int(pid), 'cpu_percent': float(cpu), 'executable': name})
    battery = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True, timeout=10).splitlines()[0]
    source = 'AC Power' if "'AC Power'" in battery else 'Battery Power' if "'Battery Power'" in battery else None
    settings = subprocess.check_output(['/usr/bin/pmset', '-g', 'custom'], text=True, timeout=10)
    section, low_power = None, None
    for line in settings.splitlines():
        if not line.startswith(' '):
            section = line.rstrip(':')
        fields = line.split()
        if section == source and len(fields) == 2 and fields[0] == 'lowpowermode':
            low_power = int(fields[1])
    require(source is not None and low_power is not None, 'Could not inspect active power profile')
    return {'at': now(), 'power': {'source': source, 'low_power_mode': low_power}, 'competing_compilers': active}


class Monitor:
    def __init__(self):
        self.observations, self.errors = [], []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.poll, daemon=True)

    def check(self):
        try:
            self.observations.append(environment_observation())
        except Exception as error:
            self.errors.append(str(error))

    def poll(self):
        while not self.stop.wait(10):
            self.check()

    def start(self):
        self.check()
        self.validate()
        self.thread.start()

    def finish(self):
        self.stop.set()
        if self.thread.ident is not None:
            self.thread.join()
        self.check()

    def validate(self):
        require(not self.errors and self.observations, 'Power/compiler monitor failed: ' + repr(self.errors))
        require(all(x['power'] == POWER and not x['competing_compilers'] for x in self.observations),
                'Power changed or a competing compiler was observed; sample is not qualified')


def group_alive(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def cleanup(proc):
    if proc is None:
        return
    if group_alive(proc.pid):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait(timeout=10)
    require(not group_alive(proc.pid), 'Owned process group remains after cleanup')


def validate_output(path, expected):
    size = Path(path).stat().st_size
    digest = sha(path)
    require(size == expected['bytes'] and digest == expected['sha256'], 'Full output byte/hash mismatch')
    return {'bytes': size, 'sha256': digest, 'reference_match': True,
            'validation': 'Exact complete-output match to the retained independently validated full-work oracle'}


def diagnostics(path):
    require(Path(path).stat().st_size < 1024 * 1024, 'Unexpectedly large runtime diagnostic output')
    text = Path(path).read_text(encoding='utf-8')
    records = [json.loads(line.removeprefix('TIMING ')) for line in text.splitlines() if line.startswith('TIMING ')]
    require(len(records) == 1, 'Expected one retained runtime phase diagnostic')
    result = records[0]
    require(set(result) == {'prepare_seconds', 'kernel_seconds'}, 'Unexpected phase diagnostic fields')
    require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in result.values()),
            'Invalid phase diagnostic')
    return result


def run_one(row, directory, lock_fd, timeout):
    directory.mkdir()
    stdout, stderr = directory / 'stdout.bin', directory / 'stderr.txt'
    receipt = {'status': 'running', 'command': row['command'], 'cwd': row['cwd'],
               'environment': row['runtime_environment'], 'stdin': row['stdin'],
               'stdout': str(stdout), 'stderr': str(stderr), 'started_at': now(),
               'timing_measurement': 'full-process-wall', 'common_mutex_inode': LOCK_INODE,
               'native_inherits_common_mutex': True, 'qualified': False}
    save(directory / 'process.json', receipt)
    proc, monitor, measured = None, Monitor(), None
    reaped_empty_group = False
    input_stream = None
    previous_alarm = signal.getsignal(signal.SIGALRM)

    def expired(signum, frame):
        raise TimeoutError('Native process deadline exceeded')

    try:
        monitor.start()
        verify_lock(lock_fd)
        input_stream = Path(row['stdin']['path']).open('rb') if row['stdin'] else None
        with stdout.open('xb') as out, stderr.open('xb') as err:
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            # Block cancellation only until the Popen ownership record is in
            # memory. No disk recording/validation is inserted into the timer.
            with atomic_signals():
                started = time.perf_counter_ns()
                proc = subprocess.Popen(row['command'], stdin=input_stream or subprocess.DEVNULL,
                    stdout=out, stderr=err, cwd=row['cwd'], env=row['runtime_environment'],
                    start_new_session=True, pass_fds=(lock_fd,))
            status = proc.wait()  # blocking wait: no timeout polling added to elapsed time
            stopped = time.perf_counter_ns()
            measured = (stopped - started) / 1e9
            signal.setitimer(signal.ITIMER_REAL, 0)
        receipt.update(pid=proc.pid, process_group_id=proc.pid, exit_code=status,
                       seconds=measured, wall_seconds=measured, clock_start_ns=started, clock_stop_ns=stopped)
        require(not group_alive(proc.pid), 'Native descendants remain after main exit')
        reaped_empty_group = True
        require(status == 0, 'Native process exited with status ' + str(status))
        monitor.finish()
        monitor.validate()
        verify_lock(lock_fd)
        validation = validate_output(stdout, row['expected_output'])
        phases = diagnostics(stderr)
        receipt.update(status='passed', qualified=True, sample_details={'seconds': measured,
                       'wall_seconds': measured, **phases}, validation=validation,
                       stderr_sha256=sha(stderr), stderr_bytes=stderr.stat().st_size)
    except BaseException as error:
        receipt.update(status='failed', qualified=False, error=type(error).__name__ + ': ' + str(error))
        raise
    finally:
        with atomic_signals():
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_alarm)
            if input_stream is not None:
                input_stream.close()
            cleanup_error = None
            try:
                if not reaped_empty_group:
                    cleanup(proc)
            except BaseException as error:
                cleanup_error = str(error)
                receipt.update(status='failed', qualified=False, cleanup_error=cleanup_error)
            if not monitor.stop.is_set():
                monitor.finish()
            receipt.update(finished_at=now(), monitor_observations=monitor.observations,
                           monitor_errors=monitor.errors, native_process_started=proc is not None)
            if proc is not None:
                receipt.update(pid=proc.pid, process_group_id=proc.pid, exit_code=proc.returncode)
            save(directory / 'process.json', receipt)
            if cleanup_error:
                raise RuntimeError('Owned process cleanup failed: ' + cleanup_error)
    return receipt


def run(args):
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated == 1
            and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1 and sys.flags.optimize == 0,
            'Use the retained Python interpreter with -I -S -B and without -O')
    output = Path(args.output)
    require(output.is_absolute() and str(output.resolve()) == str(output), 'Output must be a physical absolute path')
    require(not output.exists() and not output.is_symlink(), 'Fresh output directory required; no resume or retry')
    retained = boundary.load_retained_report(ROOT)
    plan = make_plan(retained, output)
    with common_lock() as lock_fd:
        pins = pin_inventory(plan)
        cache = {}
        verify_pins(pins, cache, force=True)
        for item in INPUTS.values():
            require(Path(item['path']).stat().st_size == item['bytes'], 'Full input size mismatch')
        output.mkdir(parents=True, exist_ok=False)
        (output / 'home').mkdir()
        (output / 'tmp').mkdir()
        (output / 'samples').mkdir()
        plan['pins'] = pins
        save(output / 'plan.json', plan)
        plan_sha256 = sha(output / 'plan.json')
        pins[str(output / 'plan.json')] = plan_sha256
        report = deepcopy(plan)
        report.update(status='running', created_at=now(), completed_samples=0, native_processes=0,
                      attempts=[], pins=pins, controller=str(Path(__file__).resolve()),
                      controller_sha256=pins[str(Path(__file__).resolve())], integrity_errors=[],
                      plan_sha256=plan_sha256, artifacts={
                          'plan.json': {'sha256': plan_sha256, 'bytes': (output / 'plan.json').stat().st_size}})
        for row in report['programs'].values():
            row.update(samples_seconds=[], sample_details=[], sample_validation=[], sample_receipts=[])
        save(output / 'report.json', report)
        error = None
        artifact_states = {str(output / 'plan.json'): state(output / 'plan.json')}
        try:
            for item in plan['schedule']:
                verify_lock(lock_fd)
                verify_pins(pins, cache)
                row = report['programs'][item['key']]
                directory = output / 'samples' / f"{item['ordinal']:03d}"
                report['active_run'] = {**item, 'directory': str(directory), 'started_at': now()}
                save(output / 'report.json', report)
                print('RUN', item['ordinal'], '/45', item['key'], 'round', item['round'], flush=True)
                try:
                    receipt = run_one(row, directory, lock_fd, args.timeout)
                    with atomic_signals():
                        require(receipt['qualified'] is True, 'Unqualified receipt')
                        report['native_processes'] += 1
                        report['completed_samples'] += 1
                        report['attempts'].append({**item, 'receipt': str(directory / 'process.json'), 'qualified': True})
                        row['samples_seconds'].append(receipt['wall_seconds'])
                        row['sample_details'].append(receipt['sample_details'])
                        row['sample_validation'].append(receipt['validation'])
                        row['sample_receipts'].append(str(directory / 'process.json'))
                        row['median_seconds'] = statistics.median(row['samples_seconds'])
                        row['sample_stdev_seconds'] = statistics.stdev(row['samples_seconds']) if len(row['samples_seconds']) > 1 else None
                        row['full_validation'] = receipt['validation']
                        for name, digest in (('stdout.bin', receipt['validation']['sha256']),
                                             ('stderr.txt', receipt['stderr_sha256']),
                                             ('process.json', sha(directory / 'process.json'))):
                            path = directory / name
                            artifact_states[str(path)] = state(path)
                            report['artifacts'][str(path.relative_to(output))] = {'sha256': digest, 'bytes': path.stat().st_size}
                        report.pop('active_run', None)
                        save(output / 'report.json', report)
                except BaseException:
                    if (directory / 'process.json').exists() and not any(x['ordinal'] == item['ordinal'] for x in report['attempts']):
                        failed = json.loads((directory / 'process.json').read_text())
                        report['native_processes'] += int(failed.get('native_process_started', False))
                        report['attempts'].append({**item, 'receipt': str(directory / 'process.json'), 'qualified': False})
                    raise
                print('SAMPLE', item['ordinal'], f"{receipt['wall_seconds']:.9f}s", flush=True)
            require(report['completed_samples'] == report['native_processes'] == 45
                    and all(len(row['samples_seconds']) == 3 for row in report['programs'].values()),
                    'Incomplete 45-process cohort')
            report['status'] = 'complete'
        except BaseException as caught:
            error = caught
            report.update(status='failed', error=type(caught).__name__ + ': ' + str(caught))
        finally:
            with atomic_signals():
                mutex_held = False
                try:
                    verify_pins(pins, cache, force=True)
                    verify_lock(lock_fd)
                    mutex_held = True
                    require(all(state(path) == prior for path, prior in artifact_states.items()),
                            'Previously validated raw sample artifact changed')
                    if report['status'] == 'complete':
                        actual = set()
                        for path in output.rglob('*'):
                            require(not path.is_symlink() and (path.is_file() or path.is_dir()),
                                    'Unexpected nonregular output artifact')
                            if path.is_file() and path != output / 'report.json':
                                actual.add(str(path.relative_to(output)))
                        require(actual == set(report['artifacts']) and len(actual) == 136,
                                'Final sample artifact inventory differs from 45 complete receipts')
                except BaseException as caught:
                    report['integrity_errors'].append(type(caught).__name__ + ': ' + str(caught))
                    report['status'] = 'failed'
                    error = error or caught
                report['finished_at'] = now()
                save(output / 'report.json', report)
                terminal = {'status': report['status'], 'report_sha256': sha(output / 'report.json'),
                            'completed_samples': report['completed_samples'], 'native_processes': report['native_processes'],
                            'integrity_errors': report['integrity_errors'], 'finished_at': now(),
                            'common_mutex_inode': LOCK_INODE, 'common_mutex_held': mutex_held,
                            'artifacts': deepcopy(report['artifacts'])}
                require(not (output / 'terminal.json').exists(), 'Unexpected early terminal')
                save(output / 'terminal.json', terminal)
                print('REPORT', report['status'], str(output / 'report.json'), flush=True)
        if error:
            raise error
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=float, default=600)
    args = parser.parse_args()
    require(math.isfinite(args.timeout) and args.timeout > 0, 'Positive finite timeout required')

    def interrupted(signum, frame):
        raise KeyboardInterrupt('Controller interrupted by signal ' + str(signum))

    for signum in SIGNALS:
        signal.signal(signum, interrupted)
    run(args)


if __name__ == '__main__':
    main()
