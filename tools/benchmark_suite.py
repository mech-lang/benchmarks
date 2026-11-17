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
import threading
import gzip
import tarfile

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


def load_catalog(path=ROOT / 'suite/catalog.json', root=ROOT):
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
        source = (Path(root) / case['source']).resolve()
        if not source.is_relative_to(Path(root)) or not source.is_file():
            raise ValueError(f'invalid source: {identifier}')
        if len(case['task']['outputs']) != 1 or not isinstance(case['task']['outputs'][0], str):
            raise ValueError('adapter requires one explicitly named output')
        measurement = case['measurement']
        if 'schedule_file' in measurement:
            import struct
            trace = (Path(root) / measurement['schedule_file']).resolve()
            if not trace.is_relative_to(Path(root)) or measurement.get('schedule_encoding') != 'f64le-rows-4':
                raise ValueError('invalid schedule file or encoding')
            raw = trace.read_bytes()
            if len(raw) % 32:
                raise ValueError('truncated four-element f64 trace')
            measurement['schedule'] = [list(row) for row in struct.iter_unpack('<4d', raw)]
        schedule = measurement['schedule']
        if not schedule or not all(isinstance(frame, list) and all(
                (isinstance(n, str) if measurement.get('input_kind') == 'string' else isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)) for n in frame) for frame in schedule):
            raise ValueError(f'invalid schedule: {identifier}')
        if not set(case['backends']) <= {'source', 'bytecode', 'native', 'jit', 'process', 'process-workers', 'source-native', 'fused-native', 'program-jit', 'program-jit-bytecode', 'program-linked', 'roc', 'libdeflate', 'related-managed', 'related-compact'}:
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
    for name, field in (('src/main.rs','adapter_sha256'),('Cargo.toml','manifest_sha256'),('Cargo.lock','lock_sha256')):
        if not (path.parent/name).is_file() or file_digest(path.parent/name)!=worker.get(field):
            raise ValueError(f'worker reproduction input changed: {name}')
    for name, checksum in worker.get('auxiliary_adapter_sha256', {}).items():
        if file_digest(path.parent/'src'/name) != checksum:
            raise ValueError('worker auxiliary adapter changed: '+name)
    worker['binary'] = str(binary)
    worker['manifest_path'] = str(path)
    return worker


def preserve_worker(worker, destination):
    import shutil
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    source = Path(worker['manifest_path']).parent
    for name in ('worker.json', 'Cargo.toml', 'Cargo.lock', 'src/main.rs', *('src/'+name for name in worker.get('auxiliary_adapter_sha256', {}))):
        file = source / name
        if not file.is_file():
            raise ValueError(f'worker reproduction input missing: {file}')
        target = destination / Path(name).name
        shutil.copyfile(file, target)


def seal_evidence(directory):
    directory = Path(directory)
    files = {str(file.relative_to(directory)): file_digest(file) for file in sorted(directory.rglob('*'))
             if file.is_file() and file.name not in ('campaign.json', 'report.md', 'evidence.json')}
    save(directory / 'evidence.json', {'schema':'mech.benchmark-evidence.v1','files':files})


class EvidenceReader:
    """Read the same pinned bytes from a checkout or its lossless raw archive."""
    def __init__(self, directory):
        self.directory=Path(directory).resolve()
        self.manifest=json.loads((self.directory/'evidence.json').read_text())
        self.archive=None
        self.members={}

    def __enter__(self):
        archives=self.manifest.get('archives',{})
        if archives:
            if set(archives)!={'raw.tar.gz'}:raise ValueError('unsupported evidence archive')
            path=self.directory/'raw.tar.gz'
            if file_digest(path)!=archives['raw.tar.gz']:raise ValueError('raw archive hash mismatch')
            self.archive=tarfile.open(path,'r:gz')
            for member in self.archive.getmembers():
                name=member.name
                if (not member.isfile() or not name.startswith('raw/') or Path(name).is_absolute()
                        or '..' in Path(name).parts or name in self.members):
                    self.archive.close()
                    raise ValueError('unsafe or duplicate raw archive member')
                self.members[name]=member
        return self

    def __exit__(self, *_):
        if self.archive:self.archive.close()

    def read(self, name):
        path=(self.directory/name).resolve()
        if not path.is_relative_to(self.directory):raise ValueError('unsafe evidence path')
        if self.archive and name.startswith('raw/'):
            member=self.members.get(name)
            if member is None:raise ValueError(f'missing archived observation: {name}')
            return self.archive.extractfile(member).read()
        return path.read_bytes()


def archive_evidence(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'evidence.json').read_text())
    if manifest.get('archives'):
        with EvidenceReader(directory) as reader:
            for name,checksum in manifest['files'].items():
                if hashlib.sha256(reader.read(name)).hexdigest()!=checksum:raise ValueError('evidence hash mismatch')
        return
    temporary=directory/'raw.tar.gz.tmp'
    with temporary.open('wb') as file:
        with gzip.GzipFile(filename='',fileobj=file,mode='wb',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as archive:
                for name in sorted(manifest['files']):
                    if not name.startswith('raw/'):continue
                    path=directory/name
                    if path.is_symlink() or file_digest(path)!=manifest['files'][name]:raise ValueError('raw evidence changed before archiving')
                    member=tarfile.TarInfo(name)
                    member.size=path.stat().st_size
                    member.mode=0o644
                    with path.open('rb') as source:archive.addfile(member,source)
    temporary.replace(directory/'raw.tar.gz')
    manifest['archives']={'raw.tar.gz':file_digest(directory/'raw.tar.gz')}
    save(directory/'evidence.json',manifest)
    # Verify every archived byte before treating it as the portable evidence.
    with EvidenceReader(directory) as reader:
        for name,checksum in manifest['files'].items():
            if hashlib.sha256(reader.read(name)).hexdigest()!=checksum:raise ValueError('archived evidence hash mismatch')


def validate_campaign(directory, campaign):
    directory = Path(directory).resolve()
    if campaign.get('schema')!=SCHEMA or not campaign.get('complete'):
        raise ValueError(f'incomplete or unsupported campaign: {directory}')
    evidence = json.loads((directory/'evidence.json').read_text())
    if evidence.get('schema')!='mech.benchmark-evidence.v1':
        raise ValueError('unsupported evidence schema')
    wanted={sample['raw']+'/supervised.json' for result in campaign['results'] for sample in result['samples']}
    observations={}
    retained_reports={}
    with EvidenceReader(directory) as reader:
        for name, checksum in evidence['files'].items():
            content=reader.read(name)
            if hashlib.sha256(content).hexdigest()!=checksum:
                raise ValueError(f'campaign evidence changed: {name}')
            if name in wanted:
                observation=json.loads(content)
                retained=observation.get('retained_observation')
                if retained:
                    from import_related_posts import retained_metrics
                    import gzip
                    retained_name=retained['path']
                    if retained_name not in evidence['files'] or evidence['files'][retained_name]!=retained['sha256']:
                        raise ValueError('retained observation report is not pinned')
                    if retained_name not in retained_reports:retained_reports[retained_name]=json.loads(gzip.decompress(reader.read(retained_name)))
                    cohort=retained['cohort']
                    if cohort not in ('primary','confirmation'):raise ValueError('unknown retained cohort')
                    index='sample' if cohort=='primary' else 'round'
                    matches=[x for x in retained_reports[retained_name]['samples'] if x['variant']==retained['variant'] and x[index]==retained['round']]
                    if len(matches)!=1:raise ValueError('retained observation identity changed')
                    source=matches[0]
                    exact='exact_rust_output' if cohort=='primary' else 'exact_output'
                    if source['exit']!=0 or not source[exact] or observation['metrics']!=retained_metrics(source,cohort,retained['variant']=='rust-preinitialized'):
                        raise ValueError('retained receipt differs from original measurement')
                parent=observation.get('parent_observation')
                if parent:
                    parent_name=parent['path']
                    if parent_name not in evidence['files'] or evidence['files'][parent_name]!=parent['sha256']:
                        raise ValueError('case receipt parent observation is not pinned')
                    source=json.loads(reader.read(parent_name))
                    matches=[entry for entry in source.get('application_results',[]) if entry.get('name')==parent['case']]
                    if source.get('outcome')!='ok' or len(matches)!=1 or observation.get('metrics')!={**matches[0]['metrics'],**source['metrics']}:
                        raise ValueError('case receipt differs from its actual program worker observation')
                    if hashlib.sha256(bytes.fromhex(matches[0]['raw_hex'])).hexdigest()!=observation.get('final_output',{}).get('sha256'):
                        raise ValueError('case receipt output differs from its actual program output')
                observations[name]=observation
    host_hash=digest(campaign['environment'])
    if campaign['environment_hash']!=host_hash:
        raise ValueError('campaign environment hash mismatch')
    identities=set()
    for result in campaign['results']:
        identity=result['case_id'],result['backend'],result['lane']
        if identity in identities:raise ValueError('duplicate campaign result')
        identities.add(identity)
        if (digest(result['task'])!=result['task_hash'] or digest(result['measurement'])!=result['measurement_hash']
                or hashlib.sha256(result['source'].encode()).hexdigest()!=result['source_sha256']
                or result['environment_hash']!=host_hash):
            raise ValueError('campaign contract or source hash mismatch')
        if result.get('progress')=='measured' and result['outcome']!='ok':
            raise ValueError('failed result marked measured')
        if result['outcome']!='ok':
            if result.get('summary'):raise ValueError('failed result has accepted summary')
            continue
        samples=result['samples']
        if result['progress']=='measured' and (not samples or result.get('summary')!=summarize(samples)):
            raise ValueError('campaign summary differs from retained samples')
        forks=set()
        for sample in samples:
            if sample['fork'] in forks:raise ValueError('duplicate fork')
            forks.add(sample['fork'])
            raw=sample['raw']+'/supervised.json'
            if raw not in observations:raise ValueError('missing raw sample')
            recorded=observations[raw]
            if recorded['outcome']!='ok' or sample['metrics']!=recorded['metrics']:
                raise ValueError('sample differs from raw worker observation')
    return True


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


def signal_group(identifier, sig):
    try:
        os.killpg(identifier,sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        # On macOS an exiting orphaned group can briefly contain only zombies
        # and reject SIGKILL. Ignore that race only after proving no live member
        # remains; a real permission failure must still stop the campaign.
        rows=subprocess.check_output(['ps','-axo','pgid=,stat='],text=True)
        for row in rows.splitlines():
            fields=row.split()
            if len(fields)>=2 and fields[0]==str(identifier) and not fields[1].startswith(('Z','X')):
                raise


def stop_group(process):
    # Every owned worker starts a new session. Reap the leader and stop lingering
    # compiler/linker descendants even when the leader has already exited.
    signal_group(process.pid,signal.SIGTERM)
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        pass
    signal_group(process.pid,signal.SIGKILL)
    process.wait()


def deadline(process, timeout):
    expired = threading.Event()
    def terminate():
        expired.set()
        signal_group(process.pid,signal.SIGKILL)
    timer = threading.Timer(timeout, terminate)
    timer.daemon = True
    timer.start()
    return timer, expired


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
        timer, expired = deadline(process, timeout)
        try:
            process.communicate(json.dumps(request, allow_nan=False).encode())
            wall = time.perf_counter() - started
            if expired.is_set():
                outcome = {'outcome': 'timeout', 'error': f'worker exceeded {timeout:g}s'}
            elif process.returncode != 0:
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
        finally:
            timer.cancel()
            stop_group(process)
    outcome['worker_protocol_process_seconds'] = wall
    save(directory / 'supervised.json', outcome)
    return outcome


def execute(command, directory, timeout, env=None, stdin_path=None):
    """File-backed non-protocol command, used for build/link and complete program lifecycles."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / 'command.json', command)
    if stdin_path is not None:
        save(directory / 'stdin.json', {'path':str(Path(stdin_path).resolve()),'sha256':file_digest(stdin_path),'bytes':Path(stdin_path).stat().st_size})
    with (Path(stdin_path).open('rb') if stdin_path is not None else open(os.devnull,'rb')) as stdin, (directory / 'stdout.txt').open('wb') as stdout, (directory / 'stderr.txt').open('wb') as stderr:
        started = time.perf_counter()
        process = subprocess.Popen(command, stdin=stdin, stdout=stdout, stderr=stderr,
                                   start_new_session=True, env=env)
        timer, expired = deadline(process, timeout)
        try:
            # Blocking wait observes actual process completion, avoiding the
            # exponential polling delay of Popen.wait(timeout=...) in timings.
            process.wait()
            result = {'outcome': 'timeout', 'error': f'command exceeded {timeout:g}s'} if expired.is_set() else {
                'outcome': 'ok' if process.returncode == 0 else 'error', 'returncode': process.returncode}
        finally:
            duration = time.perf_counter() - started
            timer.cancel()
            stop_group(process)
    result['seconds'] = duration
    save(directory / 'supervised.json', result)
    return result


def equal(actual, expected, task):
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected
    if isinstance(expected, str) or expected is None:
        return actual == expected
    if type(expected) is int and type(actual) is int and task['absolute_tolerance'] == task['relative_tolerance'] == 0:
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
    primary = case['measurement'].get('primary_metric', 'resident_turn_seconds')
    required = (primary, 'source_to_artifact_seconds', 'artifact_bytes', 'managed_after_drop_bytes')
    if any(key not in metrics for key in required) or any(
            not isinstance(n, (int, float)) or not math.isfinite(n) or n < 0 for n in metrics.values()):
        return 'error', 'invalid or missing numeric metrics'
    if metrics[primary] <= 0 or metrics['managed_after_drop_bytes'] != 0:
        return 'incorrect', 'invalid timed duration or unreclaimed managed ownership'
    return 'ok', None


def summarize(samples):
    keys = sorted(set.intersection(*(set(sample['metrics']) for sample in samples))) if samples else []
    return {key: {'median': statistics.median(values), 'min': min(values), 'max': max(values),
                  'stdev': statistics.stdev(values) if len(values) > 1 else None, 'samples': values}
            for key in keys for values in [[sample['metrics'][key] for sample in samples]]}


def comparison(baseline, candidate, metric='resident_turn_seconds', seed=0, threshold=0.05):
    for key in ('task_hash', 'measurement_hash', 'source_sha256', 'backend', 'environment_hash', 'feature_profile'):
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
