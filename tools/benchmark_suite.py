"""Campaign contracts, process supervision, validation and comparisons (stdlib only)."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'mech.benchmark-campaign.v1'
PROGRESS = ('planned', 'implemented', 'verified', 'measured')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)


def load_catalog(path=ROOT / 'suite/catalog.json'):
    catalog = json.loads(Path(path).read_text())
    if catalog.get('schema') != 'mech.benchmark-suite.v1':
        raise ValueError('unsupported catalog schema')
    identifiers = set()
    for case in catalog['cases']:
        identifier = case['id']
        if not identifier or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in identifier) or identifier in identifiers:
            raise ValueError(f'invalid or duplicate case id: {identifier}')
        identifiers.add(identifier)
        if case['progress'] not in PROGRESS:
            raise ValueError(f'invalid progress: {identifier}')
        if case['progress'] == 'planned':
            continue
        source = (ROOT / case['source']).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f'invalid source: {identifier}')
        if case['task']['outputs'] != ['result']:
            raise ValueError('v1 adapter requires an explicitly named result output')
        schedule = case['measurement']['schedule']
        if not schedule or not all(isinstance(frame, list) and all(
                isinstance(n, (int, float)) and math.isfinite(n) for n in frame) for frame in schedule):
            raise ValueError(f'invalid schedule: {identifier}')
        if not set(case['backends']) <= {'source', 'bytecode', 'native'}:
            raise ValueError(f'invalid backend: {identifier}')
    return catalog


def environment():
    cpu = platform.processor() or platform.machine()
    if sys.platform == 'darwin':
        cpu = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
    return {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine(),
            'cpu': cpu, 'logical_cpus': os.cpu_count(), 'python': platform.python_version(),
            'thread_environment': {key: os.environ[key] for key in
                ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'RAYON_NUM_THREADS') if key in os.environ}}


def worker_provenance(path):
    path = Path(path).resolve()
    worker = json.loads(path.read_text())
    if worker.get('protocol') != 1:
        raise ValueError('unsupported worker protocol')
    binary = Path(worker['binary'])
    if not binary.is_absolute():
        binary = (path.parent / binary).resolve()
    if not binary.is_file() or file_digest(binary) != worker['binary_sha256']:
        raise ValueError(f'worker binary missing or hash mismatch: {binary}')
    if not worker.get('revision') or not worker.get('adapter_sha256') or not worker.get('lock_sha256'):
        raise ValueError('incomplete worker provenance')
    worker['binary'] = str(binary)
    worker['manifest_path'] = str(path)
    return worker


@contextmanager
def campaign_lock(directory):
    """Prevent overlapping suites on this machine/check-out; stale locks require explicit review."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / 'campaign.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError(f'another campaign owns {lock}; check its PID before removing a stale lock') from error
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump({'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat()}, stream)
        yield
    finally:
        lock.unlink(missing_ok=True)


def stop_group(process):
    # Every owned worker starts a new session. Reap the leader and stop lingering
    # compiler/linker descendants even when the leader has already exited.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def invoke(command, request, directory, timeout):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / 'request.json', request)
    save(directory / 'command.json', command)
    outcome = {'outcome': 'error'}
    with (directory / 'stdout.json').open('wb') as stdout, (directory / 'stderr.txt').open('wb') as stderr:
        started = time.perf_counter()
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        try:
            process.communicate(json.dumps(request, allow_nan=False).encode(), timeout=timeout)
            wall = time.perf_counter() - started
            if process.returncode != 0:
                outcome = {'outcome': 'crash', 'error': f'worker exited {process.returncode}'}
            elif (directory / 'stdout.json').stat().st_size > 16 * 1024 * 1024:
                outcome = {'outcome': 'error', 'error': 'worker response exceeds protocol limit'}
            else:
                try:
                    outcome = json.loads((directory / 'stdout.json').read_text())
                    if not isinstance(outcome, dict) or outcome.get('protocol') != 1:
                        raise ValueError('invalid protocol response')
                except (ValueError, UnicodeError) as error:
                    outcome = {'outcome': 'error', 'error': f'malformed worker response: {error}'}
        except subprocess.TimeoutExpired:
            wall = time.perf_counter() - started
            outcome = {'outcome': 'timeout', 'error': f'worker exceeded {timeout:g}s'}
        finally:
            stop_group(process)
    outcome['worker_protocol_process_seconds'] = wall
    save(directory / 'supervised.json', outcome)
    return outcome


def execute(command, directory, timeout, env=None):
    """File-backed non-protocol command, used for build/link and complete program lifecycles."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / 'command.json', command)
    with (directory / 'stdout.txt').open('wb') as stdout, (directory / 'stderr.txt').open('wb') as stderr:
        started = time.perf_counter()
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                   start_new_session=True, env=env)
        try:
            process.wait(timeout=timeout)
            result = {'outcome': 'ok' if process.returncode == 0 else 'error', 'returncode': process.returncode}
        except subprocess.TimeoutExpired:
            result = {'outcome': 'timeout', 'error': f'command exceeded {timeout:g}s'}
        finally:
            duration = time.perf_counter() - started
            stop_group(process)
    result['seconds'] = duration
    save(directory / 'supervised.json', result)
    return result


def equal(actual, expected, task):
    if isinstance(expected, bool) or isinstance(expected, str) or expected is None:
        return actual == expected
    if isinstance(expected, (int, float)):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(
            actual, expected, abs_tol=task['absolute_tolerance'], rel_tol=task['relative_tolerance'])
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(equal(a, b, task) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            return False
        # Shapes and kinds are exact semantic requirements; never tolerate different dimensions.
        return all(actual[k] == expected[k] if k in ('kind', 'shape') else equal(actual[k], expected[k], task) for k in expected)
    return False


def verify_response(response, expected, case):
    if response.get('outcome') != 'ok':
        return response.get('outcome', 'error'), response.get('error', 'worker failed')
    if response.get('output_name') != case['task']['outputs'][0]:
        return 'incorrect', 'worker observed the wrong named output'
    if not equal(response.get('outputs'), expected, case['task']):
        return 'incorrect', 'trajectory differs from independent oracle'
    if not equal(response.get('before_execution'), expected[:-1], case['task']):
        return 'incorrect', 'no-execution control changed the published output'
    if case['measurement']['retain_snapshots'] and not equal(response.get('retained_outputs'), expected, case['task']):
        return 'incorrect', 'retained snapshots changed after later turns'
    if response.get('metrics', {}).get('managed_after_drop_bytes') != 0:
        return 'incorrect', 'managed budget remains charged after teardown'
    return 'ok', None


def measurement_response(response, endpoint, case, iterations):
    if response.get('outcome') != 'ok':
        return response.get('outcome', 'error'), response.get('error', 'worker failed')
    if response.get('iterations') != iterations or response.get('output_name') != case['task']['outputs'][0]:
        return 'incorrect', 'worker measured a different iteration count or output'
    if not equal(response.get('final_output'), endpoint, case['task']):
        return 'incorrect', 'measured endpoint differs from independent oracle'
    metrics = response.get('metrics', {})
    required = ('resident_turn_seconds', 'source_to_artifact_seconds', 'artifact_bytes', 'managed_after_drop_bytes')
    if any(key not in metrics for key in required) or any(
            not isinstance(n, (int, float)) or not math.isfinite(n) or n < 0 for n in metrics.values()):
        return 'error', 'invalid or missing numeric metrics'
    if metrics['resident_turn_seconds'] <= 0 or metrics['managed_after_drop_bytes'] != 0:
        return 'incorrect', 'invalid timed duration or unreclaimed managed ownership'
    return 'ok', None


def summarize(samples):
    keys = sorted(set.intersection(*(set(sample['metrics']) for sample in samples))) if samples else []
    return {key: {'median': statistics.median(values), 'min': min(values), 'max': max(values),
                  'stdev': statistics.stdev(values) if len(values) > 1 else None, 'samples': values}
            for key in keys for values in [[sample['metrics'][key] for sample in samples]]}


def comparison(baseline, candidate, metric='resident_turn_seconds', seed=0, threshold=0.05):
    for key in ('task_hash', 'measurement_hash', 'source_sha256', 'backend', 'environment_hash'):
        if baseline.get(key) != candidate.get(key):
            return {'status': 'incompatible', 'reason': f'{key} differs'}
    if baseline['outcome'] != 'ok' or candidate['outcome'] != 'ok':
        return {'status': 'inconclusive', 'reason': 'one or both runs did not qualify'}
    left = {s['fork']: s['metrics'][metric] for s in baseline['samples'] if metric in s['metrics']}
    right = {s['fork']: s['metrics'][metric] for s in candidate['samples'] if metric in s['metrics']}
    shared = sorted(left.keys() & right.keys())
    if not shared or any(left[i] <= 0 or right[i] <= 0 for i in shared):
        return {'status': 'inconclusive', 'reason': 'no positive matched fork observations'}
    logs = [math.log(right[i] / left[i]) for i in shared]
    ratio = math.exp(statistics.mean(logs))
    result = {'ratio': ratio, 'percent_change': (ratio - 1) * 100, 'forks': len(logs),
              'status': 'informational', 'method': 'paired fork log ratios; deterministic percentile bootstrap',
              'practical_threshold': threshold, 'performance_gate': False}
    if len(logs) < 5:
        result['reason'] = 'at least five independent fork pairs required for a screening decision'
        return result
    rng = random.Random(seed)
    estimates = sorted(math.exp(statistics.mean(rng.choices(logs, k=len(logs)))) for _ in range(4000))
    low, high = estimates[100], estimates[3899]
    result['interval_95'] = [low, high]
    result['status'] = 'suspected_regression' if low > 1 + threshold else 'improvement' if high < 1 - threshold else 'inconclusive'
    result['reason'] = 'independent confirmation campaign required before a regression decision'
    return result


def report(campaign):
    lines = ['# Mech benchmark campaign', '', f"Started: {campaign['started_at']}", '',
             'Timings are informational. Resident turns include captured-input submission, managed execution and publication. '
             'Source-to-artifact compilation, activation, observation and teardown are separate diagnostics. '
             'These observations do not replace the historical fresh-process cross-language chart.', '',
             '| Case | Backend | Worker | Outcome | Turn median | Compile median | Artifact | Managed retained |',
             '| --- | --- | --- | --- | ---: | ---: | ---: | ---: |']
    for result in campaign['results']:
        summary = result.get('summary', {})
        def metric(key, suffix='', scale=1):
            row = summary.get(key)
            return f"{row['median'] * scale:.6g}{suffix}" if row else '—'
        lines.append(f"| {result['case_id']} | {result['backend']} | {result['lane']} | {result['outcome']} | "
                     f"{metric('resident_turn_seconds', ' µs', 1e6)} | {metric('source_to_artifact_seconds', ' ms', 1e3)} | "
                     f"{metric('artifact_bytes', ' B')} | {metric('managed_retained_bytes', ' B')} |")
    lines += ['', 'Managed counters report admitted backing, separately from whole-worker peak RSS. '
              'The worker high-water mark includes compilation and preparation, and is not an execution-interval RSS measurement. '
              'Allocation counters include the counting-allocator overhead. Object/linked sections are absent until a native recipe is qualified.', '',
              'Exact source, contracts, worker hashes, toolchains, comparison order, verification outputs, requests and raw observations accompany this report.', '']
    return '\n'.join(lines)
