"""Verify one actual closed Prolog gate; save new-repository evidence copies."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
CLBG = HOST / 'benchmarks/clbg'
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
WORK = CLBG / 'prolog-comparison/20261013/revisions/prepared-work-v2'
READER = NEW / 'loc-normalization/20261013/prolog-proposal-v4'
CAPTURE = NEW / 'continuation/jobs/prolog-next-gates-source-capture-v1'
READER_CAPTURE = NEW / 'continuation/jobs/prolog-reader31-v4-source-capture-v1'
PY = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
WORK_SHA = '379a3d6e2f5e5aad5af89b78c436db79bb3b5c01067266de40583b25f1ee67c9'
READER_SHA = '027a652b2c535f1343c3c76a8eca3ff543bcd9b051409c21f9f2c708ccaca6bc'
CAPTURE_SHA = '36827f87daba0ca932baf586348480d4d482ae40c706906cfb9ad8f881ba1f9d'
GATES = {
    'six': ('prolog-prepared-work-six-v2', WORK.parents[1] / 'work-qualification/prepared-work-v2-fixtures-v1',
        'six-work-fixtures-passed-awaiting-thirty-probes'),
    'reader': ('prolog-original-reader31-v4', READER / 'jobs/reader31-v1', 'passed-awaiting-original-source-review'),
    'work': ('prolog-prepared-work-thirty-v2', WORK.parents[1] / 'work-qualification/prepared-work-v2-probes-v1',
        'thirty-instrumented-work-probes-passed-awaiting-scored-source-and-WAM-review'),
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path, expected=None):
    if expected is not None:
        assert sha(path) == expected, path
    return json.loads(Path(path).read_bytes())


def cold(path, pins):
    path = Path(path)
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pins[str(path.resolve())], path
    result = dict(__name__='prolog_closed_gate_constants', __file__=str(path))
    exec(compile(raw, str(path), 'exec'), result)
    return result


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def expected_command(gate):
    if gate == 'reader':
        return [PY, '-I', '-S', '-B', '-u', str(READER / 'run_fixtures.py'),
            '--packet', str(READER_CAPTURE / 'reader-source-packet.json'), '--packet-sha256', READER_SHA,
            '--output', str(READER / 'jobs/reader31-v1')]
    command = [PY, '-I', '-S', '-B', '-u', str(WORK / 'run.py'),
        '--fixtures' if gate == 'six' else '--work-probes',
        '--packet', str(CAPTURE / 'work-source-packet.json'), '--packet-sha256', WORK_SHA]
    if gate == 'work':
        previous = read(NEW / 'continuation/jobs/prolog-prepared-work-six-v2-closed-review/receipt.json')
        assert previous['status'] == 'passed-closed-six-Prolog-work-fixtures'
        command += ['--fixture-owner', str(CLBG / 'continuation/owned-jobs/prolog-prepared-work-six-v2'),
            '--fixture-terminal-sha256', previous['durable_terminal_sha256'],
            '--fixture-report-sha256', previous['report_sha256'],
            '--fixture-body-sha256', previous['body_terminal_sha256']]
    return command


parser = argparse.ArgumentParser()
parser.add_argument('--gate', choices=GATES, required=True)
args = parser.parse_args()
name, output, wanted = GATES[args.gate]
owner = (NEW if args.gate == 'reader' else CLBG) / 'continuation/owned-jobs' / name
destination = NEW / 'continuation/jobs' / (name + '-closed-review')
print('WAIT private lease then common: close Prolog ' + args.gate, flush=True)
with (owner / 'owner.lock').open('rb') as lease:
    fcntl.flock(lease, fcntl.LOCK_SH)
    actual, named = os.fstat(lease.fileno()), (owner / 'owner.lock').stat()
    assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino)
    with Path('/tmp/mech-clbg-timing.lock').open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        actual, named = os.fstat(lock.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
        assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
        destination.mkdir(parents=True, exist_ok=False)
        records = {filename: read(owner / filename) for filename in
            ('request.json', 'launch.json', 'command-started.json', 'worker-started.json', 'terminal.json')}
        report_file = output / ('fixture-receipt.json' if args.gate == 'reader' else 'report.json')
        report, body = read(report_file), read(output / 'terminal-pin.json')
        pins = dict(report.get('pins', {}))
        if args.gate == 'reader':
            pins = dict(report['input_pins'])
            for path, digest in report['artifact_pins'].items():
                assert path not in pins or pins[path] == digest
                pins[path] = digest
        mismatches = []
        for path, digest in pins.items():
            try:
                assert sha(path) == digest
            except BaseException as error:
                mismatches.append(dict(path=path, expected_sha256=digest, error=str(error)))
        copies = {}
        for label, source in (('evidence', output), ('durable', owner)):
            for path in sorted(source.rglob('*')):
                if not path.is_file() or path.name == 'owner.lock':
                    continue
                assert not path.is_symlink(), path
                target = destination / label / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                digest = sha(path)
                assert sha(target) == digest
                target.chmod(0o444)
                copies[str(path)] = dict(path=str(target), sha256=digest)
        error = None
        metrics = {}
        try:
            capture = read(CAPTURE / 'receipt.json', CAPTURE_SHA)
            work_packet = read(CAPTURE / 'work-source-packet.json', WORK_SHA)
            reader_capture = read(READER_CAPTURE / 'receipt.json',
                'f2878f94ca8af1ae0ddb04ae347ea3a4f78fe3d0d70b7ccd99fc0647d9020596')
            assert reader_capture['packet_sha256'] == READER_SHA and reader_capture['pin_count'] == 8
            reader_packet = read(READER_CAPTURE / 'reader-source-packet.json', READER_SHA)
            assert capture['work_pin_count'] == 9 and capture['reader_pin_count'] == 8 and capture['authored_file_count'] == 13
            for packet in (work_packet, reader_packet):
                for path, digest in packet['pins'].items():
                    assert sha(path) == digest, path
            request, launch, start, worker, done = [records[key] for key in
                ('request.json', 'launch.json', 'command-started.json', 'worker-started.json', 'terminal.json')]
            expected = expected_command(args.gate)
            assert request['command'] == launch['command'] == start['command'] == worker['command'] == expected
            assert request['cwd'] == launch['cwd'] == start['cwd'] == worker['cwd'] == str(NEW.parents[1] if args.gate == 'reader' else HOST)
            assert request['common_mutex_owned_by_target_command'] is True
            assert request['qualification_granted'] is request['automatic_retry'] is False
            assert done['status'] == 'command-exited-zero-awaiting-report-review'
            assert type(done['exit_code']) is int and done['exit_code'] == 0 and done['stop_signals'] == []
            assert done['actual_command_started'] is True and done['command_identity_observation_missing'] is False
            assert done['qualification_granted'] is done['automatic_retry'] is False
            assert not any(done.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
            assert start['command_identity'] == done['command_identity'] and start['command_pid'] == done['command_pid']
            assert worker['worker_identity'] == done['worker_identity']
            first, final = launch['worker_identity']['listing'].split(None, 7), worker['worker_identity']['listing'].split(None, 7)
            assert first[:1] == final[:1] and first[2:7] == final[2:7] and first[7] == final[7]
            listing = done['command_identity']['listing'].split(None, 7)
            assert listing[:2] == [str(done['command_pid']), str(done['worker_identity']['pid'])]
            assert listing[7].split() == expected
            assert not mismatches
            assert report['status'] == body['status'] == wanted
            assert not any(report.get(key) for key in ('error', 'error_type', 'terminal_artifact_errors'))
            assert report['chart_admission'] is False
            if args.gate == 'reader':
                assert body['receipt'] == str(report_file) and body['receipt_sha256'] == sha(report_file)
                assert body['input_pins'] == report['input_pins'] and body['artifact_pins'] == report['artifact_pins']
                assert body['integrity_errors'] == [] and body['shared_timing_mutex_held'] is True
                assert body['available_bytes_not_fully_pinned'] is False
                assert report['pin_reconciliation_passed'] is report['exact_test_execution'] is True
                assert report['benchmark_processes_started'] == 0 and report['source_counting_started'] is False
                assert report['successful_bounded_cases_reexecuted'] == report['source_profiles_recompiled'] == 0
                ids = list(cold(READER / 'run_fixtures.py', reader_packet['pins'])['EXPECTED'])
                assert report['expected_ids'] == ids
                assert type(report['tests_run']) is int and report['tests_run'] == 31
                for key in ('discovered_ids', 'started_ids'):
                    assert len(report[key]) == len(set(report[key])) == 31 and set(report[key]) == set(ids)
                assert all(report[key] == 0 for key in
                    ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes'))
                metrics = dict(tests=31, scanner_processes=len(report['scanner_attempts']),
                    projections=len(report['projections']), source_counting_started=False)
            else:
                assert body['report'] == str(report_file) and body['report_sha256'] == sha(report_file)
                assert body['partial_evidence_pins'] == report['pins']
                assert report['terminal_evidence_complete'] is body['inherited_common_mutex'] is True
                assert report['source_work_qualified'] is False and report['canonical_loc'] is None
                assert report['full_processes_authorized'] == report['successful_preparation_cases_reexecuted'] == 0
                assert report['original_scored_profiles_recompiled'] == 0
                assert report['old_contract_fixture_reexecutions'] == report['old_ownership_fixture_reexecutions'] == 0
                if args.gate == 'six':
                    fixture = read(output / 'fixture-receipt.json')
                    ids = cold(WORK / 'fixture_runner.py', work_packet['pins'])['IDS']
                    assert fixture == report['work_fixture_receipt'] and fixture['status'] == 'passed'
                    assert fixture['expected_test_ids'] == ids
                    assert fixture['execution_completed'] is fixture['inherited_common_mutex'] is True
                    assert type(fixture['tests_run']) is type(fixture['discovered_tests']) is int
                    assert fixture['tests_run'] == fixture['discovered_tests'] == 6
                    for key in ('actual_test_ids', 'discovered_test_ids'):
                        assert len(fixture[key]) == len(set(fixture[key])) == 6 and set(fixture[key]) == set(ids)
                    assert all(fixture[key] == [] for key in
                        ('failures', 'errors', 'skips', 'expected_failures', 'unexpected_successes'))
                    assert report['new_native_commands'] == report['work_probe_processes'] == 0
                    metrics = dict(tests=6, new_native_commands=0)
                else:
                    assert report['actual_tree_map_pi_observations_reconciled'] is True
                    assert report['original_scored_work_receipt_qualified'] is False
                    assert report['new_work_fixture_reexecutions'] == 0
                    assert report['work_probe_processes'] == len(report['attempts']) == len(report['case_results']) == 30
                    assert len(report['instrumented_profiles']) == 6 and report['new_native_commands'] == 56
                    unique = {(row['id'], row['case']) for row in report['case_results']}
                    expected_cases = set()
                    for form in ('compact', 'optimized'):
                        expected_cases.update(('prolog-binarytrees-' + form, 'n-' + str(n)) for n in (0, 4, 7, 9))
                        expected_cases.update(('prolog-pidigits-' + form, 'n-' + str(n)) for n in (0, 1, 9, 10, 11, 27, 97))
                        expected_cases.update(('prolog-knucleotide-' + form, case) for case in
                            ('missing-three', 'one-base', 'overlap-and-tail', 'arbitrary-width18-keys'))
                    assert len(unique) == 30 and unique == expected_cases
                    metrics = dict(work_probe_processes=30, new_native_commands=56, instrumented_profiles=6)
        except BaseException as failure:
            error = dict(type=type(failure).__name__, detail=str(failure))
        receipt = dict(status=('passed-closed-six-Prolog-work-fixtures' if args.gate == 'six' else
            'passed-closed-Prolog-reader31' if args.gate == 'reader' else 'passed-closed-thirty-Prolog-work-probes')
            if error is None else 'failed-Prolog-gate-preserved', gate=args.gate,
            reviewed_at=datetime.now(timezone.utc).isoformat(), owner=str(owner), original_output=str(output),
            command=records['request.json']['command'], durable_terminal_sha256=sha(owner / 'terminal.json'),
            report_sha256=sha(report_file), body_terminal_sha256=sha(output / 'terminal-pin.json'),
            actual_durable_exit_status=records['terminal.json']['exit_code'], verified_pins=len(pins),
            input_pin_mismatches=mismatches, metrics=metrics, copies=copies,
            reviewer_source=str(Path(__file__).resolve()), reviewer_source_sha256=sha(__file__),
            error=error, source_work_qualified=False, canonical_loc=None, chart_admission=False,
            original_preparation_reexecutions=0, automatic_retry=False)
        save(destination / 'receipt.json', receipt)
        print(json.dumps(dict(receipt=str(destination / 'receipt.json'), receipt_sha256=sha(destination / 'receipt.json'),
            status=receipt['status'], durable_terminal_sha256=receipt['durable_terminal_sha256'],
            report_sha256=receipt['report_sha256'], body_terminal_sha256=receipt['body_terminal_sha256'],
            verified_pins=len(pins), metrics=metrics, error=error)), flush=True)
        assert error is None, 'Preserved actual failed gate; no retry or dependent launch'
