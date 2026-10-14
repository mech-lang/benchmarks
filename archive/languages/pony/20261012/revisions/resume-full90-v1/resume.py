"""Retain the stopped Pony run's 22 completed samples and execute its remaining slots."""
import argparse
from contextlib import ExitStack
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
COHORT = HERE.parents[1]
CLBG = COHORT.parents[1]
LOCK = Path('/tmp/mech-clbg-timing.lock')
OLD_WORKER = COHORT/'revisions/full90-retained-v1/full_study.py'
OLD_WORKER_SHA = 'ec044db2f618830ef9b445bc4a2ac063d96b77cbd4a1614acc4264f540d6fcc2'
OLD_REVIEW_SHA = '29cb21d8c728de8fbf1f89d258bc4a18221888df95b4b8315b185c65fe605abc'
OLD = COHORT/'full-studies/pony-retained20-full-v1'
OWNER = CLBG/'continuation/owned-jobs/pony-retained20-full90-v1'
OUTPUT = COHORT/'full-studies/pony-retained20-resumed-v1'
WORK_OWNER = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/continuation/owned-jobs/pony-reviewed-work-metadata-v1')
SUITE_SHA = '0bb51cf4b706d6bb7fa4e36447dd3e641665f513c9608d04217ae377126cb5e1'
BODY_SHA = 'd8fffef67cf6039f41f64770c415d3e9ee7bdd657df67df5ecf67fa8d6d1e025'
REPORT_SHA = 'b1536d6ba6e336eb61f06d1fcc6dd3e7437a8e29ad9d047808215f9e8d6b6588'
DURABLE_SHA = '866a9d6cc32a1064fe5a110b50414a3f0c65135ecd4fe695da9bbe37661e93d3'
REQUEST_SHA = '3cae47dbd2e099e21bcf8312cad1fdf52e31084497e9204ff6078670e2c6c044'
APPROVED = CLBG/'continuation/jobs/pony-retained-full-manifest-review-v1/review.json'
APPROVED_SHA = 'ad48d5381906dca4a1b14b7a92333b8c12812da1fb739639e20d9af8af00fee7'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def original():
    raw = OLD_WORKER.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == OLD_WORKER_SHA
    module = types.ModuleType('pony_retained_original_full_controller')
    module.__file__ = str(OLD_WORKER)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(OLD_WORKER), 'exec'), module.__dict__)
    return module


def prerequisite_args():
    return argparse.Namespace(worker_sha256=OLD_WORKER_SHA, review_sha256=OLD_REVIEW_SHA,
        source_audit_sha256='d76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3',
        mandelbrot_manifest_sha256='fbffba7b5674e889ac9e5088bbb2e2d8499df41f5d9b4c677be38d831091680f')


def retained(full, guard, harness, pins):
    """Validate actual saved samples against the original deterministic schedule."""
    body = full.read(OLD/'terminal.json', BODY_SHA, pins)
    before = full.read(OLD/'report.json', REPORT_SHA, pins)
    durable = full.read(OWNER/'terminal.json', DURABLE_SHA, pins)
    request = full.read(OWNER/'request.json', REQUEST_SHA, pins)
    assert body['status'] == before['status'] == 'stopped'
    assert body['report'] == str(OLD/'report.json') and body['report_sha256'] == REPORT_SHA
    assert body['full_performance_runs'] == before['full_performance_runs'] == len(before['attempts']) == 22
    assert body['integrity_errors'] == [] and body['common_mutex_held'] is True
    assert before['error'] == 'Benchmark harness received signal 15' and before['error_type'] == 'KeyboardInterrupt'
    assert durable['status'] == 'command-failed' and durable['exit_code'] == -2 and durable['stop_signals'] == [15]
    assert durable['actual_command_started'] is True and durable['automatic_retry'] is False
    assert durable['worker_identity']['pid'] == 24782 and durable['command_pid'] == 24786
    assert durable['command_identity_observation_missing'] is False
    expected = [str(full.PYTHON), '-I', '-S', '-B', '-u', str(OLD_WORKER), '--run', '--revision',
        'pony-retained20-full-v1', '--worker-sha256', OLD_WORKER_SHA, '--review-sha256', OLD_REVIEW_SHA,
        '--source-audit-sha256', prerequisite_args().source_audit_sha256,
        '--mandelbrot-manifest-sha256', prerequisite_args().mandelbrot_manifest_sha256,
        '--manifest-sha256', SUITE_SHA, '--approved-manifest-review', str(APPROVED),
        '--approved-manifest-review-sha256', APPROVED_SHA]
    assert request['command'] == expected
    started = full.read(OWNER/'command-started.json', '5fda5a87aa0ce71781b7865d6d2b79efd2708a1099defbdbaf12e4e162313f5e', pins)
    worker = full.read(OWNER/'worker-started.json', 'a1f94ac0b4dedcf09f4de0a0ad30638af3286ed4956085c91d58f4c0bb27d1b7', pins)
    assert started['command'] == worker['command'] == expected
    assert started['command_identity'] == durable['command_identity']
    assert worker['worker_identity'] == durable['worker_identity']
    full.absorb(body['prerequisite_pins'], pins)
    full.absorb(body['available_evidence_pins'], pins)
    suite = full.read(OLD/'manifest.json', SUITE_SHA, pins)
    approved = full.read(APPROVED, APPROVED_SHA, pins)
    assert approved['status'] == 'root-reviewed-exact-Pony20-Mech10-full90-manifests'
    assert approved['manifest_sha256'] == before['manifest_sha256'] == SUITE_SHA
    assert approved['benchmark_manifests'] == suite['benchmarks']
    assert approved['worker_sha256'] == OLD_WORKER_SHA and approved['review_sha256'] == OLD_REVIEW_SHA
    assert suite['samples'] == 3 and suite['full_performance_runs_required'] == 90
    assert suite['chart_admission'] is False and len(suite['profiles']) == 30
    full.absorb(suite['pins'], pins)
    manifests, schedule = {}, []
    for benchmark in suite['benchmark_order']:
        ref = suite['benchmarks'][benchmark]
        manifest = full.read(ref['path'], ref['sha256'], pins)
        manifests[benchmark] = manifest
        keys = {row['id']: row['key'] for row in manifest['profiles']}
        for order in manifest['orders']:
            for identifier in order['profiles']:
                schedule.append((benchmark, order['round'], identifier, keys[identifier]))
    assert len(schedule) == len(set(schedule)) == 90
    initial = {row['key']: row for row in suite['profiles']}
    assert set(before['programs']) == set(initial)
    for index, (attempt, slot) in enumerate(zip(before['attempts'], schedule), 1):
        benchmark, round_index, identifier, key = slot
        row = initial[key]
        assert (attempt['benchmark'], attempt['round'], attempt['id'], attempt['key']) == slot
        assert attempt['attempt'] == index and attempt['qualified'] is True
        result_path = OLD/'attempts'/f'{index:03d}-{identifier}.json'
        supervisor_path = result_path.with_suffix('.supervisor.json')
        assert attempt['result_path'] == str(result_path) and attempt['supervisor_result_path'] == str(supervisor_path)
        assert full.read(supervisor_path, pins[str(supervisor_path)], pins) == attempt
        raw = full.read(result_path, pins[str(result_path)], pins)
        assert all(attempt.get(field) == value for field, value in raw.items())
        checks = guard.qualification_checks(attempt, attempt['supervised_native_group'], manifests[benchmark], row, attempt['sampler_wait_status'])
        assert checks == attempt['qualification_checks'] and all(value is True for value in checks.values())
        assert attempt['execution_fingerprint'] == harness.execution_fingerprint(row)
        assert not harness.group_members(attempt['supervised_native_group']['pgid'])
    for key, row in before['programs'].items():
        actual = [attempt for attempt in before['attempts'] if attempt['key'] == key]
        assert harness.execution_fingerprint(row) == harness.execution_fingerprint(initial[key])
        for field in ('loc', 'physical_loc', 'source_bundle'):
            assert row.get(field) == initial[key].get(field)
        assert row['attempts'] == [a['attempt'] for a in actual]
        assert row['samples_seconds'] == [a['seconds'] for a in actual]
        assert row['sample_validation'] == [a['validation'] for a in actual]
        assert not row.get('full_failure')
        if len(actual) == 3:
            assert row['median_seconds'] == statistics.median(row['samples_seconds'])
            assert row['sample_stdev_seconds'] == statistics.stdev(row['samples_seconds'])
    assert before['completed_benchmarks'] == suite['benchmark_order'][:2] == ['regexredux', 'revcomp']
    assert schedule[22] == ('pidigits', 2, 'mech-pidigits-control', 'pidigits:pony-full:mech-control')
    active = before['active']
    assert (active['attempt'], active['round'], active['id'], active['key']) == (23, *schedule[22][1:])
    interrupted = full.read(active['result_path'], pins[active['result_path']], pins)
    assert interrupted == dict(error='Benchmark harness received signal 15', error_type='KeyboardInterrupt', sampler_failure=True)
    assert guard.identity(active['sampler_pid']) is None
    for identity in (durable['worker_identity'], durable['command_identity']):
        assert guard.identity(identity['pid']) is None
    # Reject any still-running measured image; never signal an unrelated process.
    listing = subprocess.run(['ps', '-axo', 'command='], capture_output=True, text=True, check=True).stdout.splitlines()
    assert not any(line.startswith(row['command'][0]+' ') or line == row['command'][0]
                   for row in initial.values() for line in listing)
    return suite, manifests, schedule, before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-sha256', required=True)
    parser.add_argument('--review-sha256', required=True)
    args = parser.parse_args()
    assert sys.dont_write_bytecode
    with ExitStack() as leases:
        for path in (OWNER/'owner.lock', OLD/'owner.lock', WORK_OWNER/'owner.lock', CLBG/'continuation/owned-jobs/pony-reviewed-loc-seal-v1/owner.lock'):
            lock = leases.enter_context(path.open('rb')); fcntl.flock(lock, fcntl.LOCK_SH|fcntl.LOCK_NB)
            assert (os.fstat(lock.fileno()).st_dev, os.fstat(lock.fileno()).st_ino) == (path.stat().st_dev, path.stat().st_ino)
        lease_path = HERE/'owner.lock'
        lease = leases.enter_context(lease_path.open('a+')); fcntl.flock(lease, fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert (os.fstat(lease.fileno()).st_dev, os.fstat(lease.fileno()).st_ino) == (lease_path.stat().st_dev, lease_path.stat().st_ino)
        with LOCK.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            opened, named = os.fstat(lock.fileno()), LOCK.stat()
            assert (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino) and opened.st_ino == 79859134
            for name, digest in (('resume.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
                assert not (HERE/name).stat().st_mode & 0o222 and sha(HERE/name) == digest
            full = original(); full.common_identity(lock)
            assert Path(sys.executable).resolve() == full.PYTHON.resolve()
            _, _, _, guard, harness, pins, _ = full.prerequisites(prerequisite_args())
            for name, digest in (('resume.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
                assert not (HERE/name).stat().st_mode & 0o222
                full.bind(HERE/name, digest, pins)
            suite, manifests, schedule, before = retained(full, guard, harness, pins)
            assert not OUTPUT.exists(); OUTPUT.mkdir()
            report = copy.deepcopy(before)
            report.update(status='running', active=None, resumed_from=dict(report=str(OLD/'report.json'), report_sha256=REPORT_SHA,
                terminal=str(OLD/'terminal.json'), terminal_sha256=BODY_SHA, interrupted_attempt=before['active'],
                reused_completed_processes=22, new_process_slots=68), new_completed_processes=0)
            report.pop('error'); report.pop('error_type')
            guard.OUT, guard.REPORT = OUTPUT, OUTPUT/'report.json'
            harness.install_interrupt_handlers()
            guard.save(OUTPUT/'resume-evidence.json', dict(status='verified-exact-22-completed-samples-before-explicit-resumption',
                original_report=str(OLD/'report.json'), original_report_sha256=REPORT_SHA, prior_pins=pins,
                completed_slots=schedule[:22], remaining_slots=schedule[22:], repeated_completed_samples=0,
                original_files_mutated=False, chart_admission=False))
            guard.save(guard.REPORT, report)
        try:
            for benchmark, round_index, identifier, key in schedule[22:]:
                row, manifest = report['programs'][key], manifests[benchmark]
                if row.get('full_failure'):
                    continue
                with LOCK.open('r+') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX); full.common_identity(lock)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    guard.verify(manifest['pins'])
                    print('RESUME PONY', benchmark, round_index, identifier, manifest['size'], flush=True)
                    attempt = guard.one_attempt(harness, row, manifest, report, round_index, lock.fileno())
                    report['attempts'].append(attempt); report['active'] = None
                    row['attempts'].append(attempt['attempt']); report['full_performance_runs'] += 1
                    report['new_completed_processes'] += 1
                    if attempt['qualified']:
                        row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                        row.setdefault('full_validation', attempt['validation'])
                        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
                    elif full.isolated_profile_failure(guard, attempt):
                        row['measurement_status'] = 'failed'; row['full_failure'] = dict(attempt)
                    else:
                        row['measurement_status'] = 'failed-qualification'
                    guard.save(guard.REPORT, report)
                    if not attempt['qualified'] and not row.get('full_failure'):
                        raise AssertionError(('Full integrity/environment/ownership failure retained; resumption stops', identifier, attempt.get('error')))
                    rows = [report['programs'][r['key']] for r in manifest['profiles']]
                    if all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in rows):
                        for r in rows:
                            if not r.get('full_failure'):
                                r.update(median_seconds=statistics.median(r['samples_seconds']),
                                    sample_stdev_seconds=statistics.stdev(r['samples_seconds']),
                                    qualification_status='three-canonical-processes-qualified-awaiting-independent-suite-and-runtime-publication-review')
                        if benchmark not in report['completed_benchmarks']:
                            report['completed_benchmarks'].append(benchmark)
                        guard.save(guard.REPORT, report)
            with LOCK.open('r+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); full.common_identity(lock); guard.verify(pins)
                assert report['attempts'][:22] == before['attempts']
                assert report['full_performance_runs'] == len(report['attempts']) == report['new_completed_processes']+22
                assert len(report['attempts']) == sum(len(r['samples_seconds'])+bool(r.get('full_failure')) for r in report['programs'].values())
                assert len(report['completed_benchmarks']) == 10
                assert all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in report['programs'].values())
                failed = [r['id'] for r in report['programs'].values() if r.get('full_failure')]
                if not failed:
                    assert len(report['attempts']) == 90 and report['new_completed_processes'] == 68
                report.update(status='complete-with-failures' if failed else 'complete', pins_unchanged_at_end=True,
                    correctable_source_failures=failed, chart_admission=False)
        except BaseException as error:
            report.update(status='stopped', error=str(error) or type(error).__name__, error_type=type(error).__name__)
            raise
        finally:
            with LOCK.open('r+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); full.common_identity(lock)
                guard.save(guard.REPORT, report)
                errors, available = [], {}
                for path, digest in pins.items():
                    try:
                        assert sha(path) == digest
                    except BaseException as error:
                        errors.append(dict(path=path, error=str(error) or type(error).__name__))
                for path in OUTPUT.rglob('*'):
                    if path.is_file():
                        available[str(path)] = sha(path)
                full.preparation.new_json(OUTPUT/'terminal.json', dict(status='failed-terminal-integrity' if errors else report['status'],
                    report=str(guard.REPORT), report_sha256=sha(guard.REPORT), prerequisite_pins=pins,
                    available_evidence_pins=available, integrity_errors=errors, common_mutex_held=True,
                    reused_completed_processes=22, new_completed_processes=report['new_completed_processes'],
                    full_performance_runs=report['full_performance_runs'], repeated_completed_samples=0,
                    compiler_invocations=0, fixture_reexecutions=0, original_files_mutated=False, chart_admission=False))
                if errors:
                    raise RuntimeError('Pony resumption terminal integrity failed; partial evidence retained')


if __name__ == '__main__':
    main()
