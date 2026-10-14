"""Reuse the exact actual Prolog preparation, reader31 and work6/30 closures."""
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OLD = HOST / 'benchmarks/clbg'
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
WORK = OLD / 'prolog-comparison/20261013/revisions/prepared-work-v2'
READER = NEW / 'loc-normalization/20261013/prolog-proposal-v5'
SCORING = OLD / 'prolog-comparison/20261013/revisions/scored-work-review-v1/REVIEW.md'
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
ROOTS = {
    'six': ('prolog-prepared-work-six-v2', OLD,
        '1257cb69626a1f1fd4fbfa051329c80b2023875800a51a01dc5696144b92e43f',
        'passed-closed-six-Prolog-work-fixtures', 14652,
        dict(tests=6, new_native_commands=0)),
    'reader': ('prolog-original-reader31-v5', NEW,
        '61aa28c91bb0504b9daa9d752943e79e223d0f8f0838ad9a17459f8de9d8c617',
        'passed-closed-Prolog-reader31', 15888,
        dict(tests=31, scanner_processes=46, projections=46, source_counting_started=False)),
    'work': ('prolog-prepared-work-thirty-v2', OLD,
        '621ffebf2fadc30dcb0251f6183ca990603c61f5e8b8b5bfe3a0280c12301c4d',
        'passed-closed-thirty-Prolog-work-probes', 15048,
        dict(work_probe_processes=30, new_native_commands=56, instrumented_profiles=6,
             independent_raw_trace_reconciliations=30, independent_complete_output_comparisons=30)),
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path, digest, pins):
    path = Path(path).absolute()
    assert sha(path) == digest and (str(path) not in pins or pins[str(path)] == digest), path
    pins[str(path)] = digest
    return path


def read(path, digest, pins):
    return json.loads(bind(path, digest, pins).read_bytes())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def verify(pins):
    for path, digest in pins.items():
        assert sha(path) == digest, ('Changed retained input', path)


def cold(path, digest, name, pins):
    path = bind(path, digest, pins).resolve(strict=True)
    assert name not in sys.modules
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


@contextmanager
def raw_old_loaders(pins):
    original = importlib.machinery.SourceFileLoader.get_code
    def code(loader, name):
        path = Path(loader.path).resolve(strict=True)
        if path.is_relative_to(OLD):
            assert path.suffix == '.py' and str(path) in pins, ('Unpinned original loader', path)
            raw = bind(path, pins[str(path)], pins).read_bytes()
            return compile(raw, str(path), 'exec')
        return original(loader, name)
    importlib.machinery.SourceFileLoader.get_code = code
    try:
        yield
    finally:
        importlib.machinery.SourceFileLoader.get_code = original


def lease(path, stack):
    path = Path(path)
    handle = stack.enter_context(path.open('rb'))
    fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
    actual, named = os.fstat(handle.fileno()), path.stat()
    assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino)


def closed(key, pins, stack):
    name, location, digest, status, count, metrics = ROOTS[key]
    root_path = NEW / 'continuation/jobs' / (name + '-closed-review') / 'receipt.json'
    root = read(root_path, digest, pins)
    assert root['status'] == status and root['verified_pins'] == count and root['metrics'] == metrics
    assert root['error'] is None and root['input_pin_mismatches'] == []
    assert root['original_preparation_reexecutions'] == 0 and root['automatic_retry'] is False
    owner = location / 'continuation/owned-jobs' / name
    assert root['owner'] == str(owner)
    lease(owner / 'owner.lock', stack)
    done = read(owner / 'terminal.json', root['durable_terminal_sha256'], pins)
    request, start, worker = [read(owner / filename, root['copies'][str(owner / filename)]['sha256'], pins)
        for filename in ('request.json', 'command-started.json', 'worker-started.json')]
    assert request['command'] == start['command'] == worker['command'] == root['command']
    assert request['cwd'] == start['cwd'] == worker['cwd'] == str(NEW.parents[1] if key == 'reader' else HOST)
    assert request['common_mutex_owned_by_target_command'] is True
    assert request['qualification_granted'] is request['automatic_retry'] is False
    assert done['status'] == 'command-exited-zero-awaiting-report-review'
    assert type(done['exit_code']) is int and done['exit_code'] == 0 and done['stop_signals'] == []
    assert done['actual_command_started'] is True and done['command_identity_observation_missing'] is False
    assert done['qualification_granted'] is done['automatic_retry'] is False
    assert not any(done.get(field) for field in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
    assert start['command_identity'] == done['command_identity'] and start['command_pid'] == done['command_pid']
    assert worker['worker_identity'] == done['worker_identity']
    listing = done['command_identity']['listing'].split(None, 7)
    assert listing[:2] == [str(done['command_pid']), str(done['worker_identity']['pid'])]
    assert listing[7].split() == root['command']
    output = Path(root['original_output'])
    report_path = output / ('fixture-receipt.json' if key == 'reader' else 'report.json')
    report = read(report_path, root['report_sha256'], pins)
    body = read(output / 'terminal-pin.json', root['body_terminal_sha256'], pins)
    assert report['status'] == body['status']
    if key == 'reader':
        assert report['status'] == 'passed-awaiting-original-source-review'
        assert report['tests_run'] == len(set(report['started_ids'])) == len(set(report['discovered_ids'])) == 31
        assert set(report['started_ids']) == set(report['discovered_ids']) == set(report['expected_ids'])
        assert all(report[field] == 0 for field in ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes'))
        assert report['source_counting_started'] is False and report['benchmark_processes_started'] == 0
        assert report['pin_reconciliation_passed'] is report['exact_test_execution'] is True
        assert body['receipt'] == str(report_path) and body['receipt_sha256'] == root['report_sha256']
        assert body['input_pins'] == report['input_pins'] and body['artifact_pins'] == report['artifact_pins']
        assert body['integrity_errors'] == [] and body['available_bytes_not_fully_pinned'] is False
        mappings = (report['input_pins'], report['artifact_pins'])
    else:
        assert body['report'] == str(report_path) and body['report_sha256'] == root['report_sha256']
        assert body['partial_evidence_pins'] == report['pins']
        assert report['terminal_evidence_complete'] is body['inherited_common_mutex'] is True
        assert report['source_work_qualified'] is False and report['canonical_loc'] is None
        assert report['successful_preparation_cases_reexecuted'] == report['original_scored_profiles_recompiled'] == 0
        if key == 'six':
            fixture_path = output / 'fixture-receipt.json'
            fixture = read(fixture_path, report['pins'][str(fixture_path)], pins)
            assert fixture == report['work_fixture_receipt'] and fixture['status'] == 'passed'
            assert fixture['tests_run'] == fixture['discovered_tests'] == 6
            assert set(fixture['actual_test_ids']) == set(fixture['discovered_test_ids']) == set(fixture['expected_test_ids'])
            assert len(fixture['actual_test_ids']) == len(set(fixture['actual_test_ids'])) == 6
            assert all(fixture[field] == [] for field in ('failures', 'errors', 'skips', 'expected_failures', 'unexpected_successes'))
        else:
            assert report['status'] == 'thirty-instrumented-work-probes-passed-awaiting-scored-source-and-WAM-review'
            assert report['work_probe_processes'] == len(report['case_results']) == len(report['attempts']) == 30
            assert report['new_native_commands'] == 56 and len(report['instrumented_profiles']) == 6
            assert report['actual_tree_map_pi_observations_reconciled'] is True
        mappings = (report['pins'],)
    assert not any(report.get(field) for field in ('error', 'error_type', 'terminal_artifact_errors'))
    for mapping in mappings:
        for path, actual_digest in mapping.items(): bind(path, actual_digest, pins)
    for original, copy in root['copies'].items():
        bind(original, copy['sha256'], pins)
        bind(copy['path'], copy['sha256'], pins)
    bind(root['reviewer_source'], root['reviewer_source_sha256'], pins)
    return dict(root_path=str(root_path), root_sha256=digest, root=root, report=report,
        report_path=str(report_path), report_sha256=root['report_sha256'], body=body)


def load(pins, stack, scored_review_sha256):
    bind(Path(PYTHON).resolve(), PYTHON_SHA, pins)
    work_packet_path = NEW / 'continuation/jobs/prolog-next-gates-source-capture-v1/work-source-packet.json'
    packet = read(work_packet_path, '379a3d6e2f5e5aad5af89b78c436db79bb3b5c01067266de40583b25f1ee67c9', pins)
    assert packet['schema'] == 'frozen-prolog-prepared-work-v2' and len(packet['pins']) == 9
    for path, digest in packet['pins'].items(): bind(path, digest, pins)
    authority_path = WORK / 'qualified_preparation.py'
    authority = cold(authority_path, packet['pins'][str(authority_path)], 'prolog_original22_actual_authority', pins)
    for owner in authority.leases(): lease(owner / 'owner.lock', stack)
    with raw_old_loaders(pins):
        modules = authority.load(pins)
    gates = {key: closed(key, pins, stack) for key in ('six', 'reader', 'work')}
    assert gates['reader']['report']['input_pins'][str(READER / 'scan_source.pl')] == sha(READER / 'scan_source.pl')
    bind(SCORING, scored_review_sha256, pins)
    counterpart = NEW / SCORING.relative_to(OLD)
    bind(counterpart, scored_review_sha256, pins)
    assert SCORING.read_bytes() == counterpart.read_bytes()
    verify(pins)
    return authority, modules, gates
