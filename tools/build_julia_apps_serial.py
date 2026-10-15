"""Build and check explicit Julia application profiles serially; no timing admission."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def run_command(kind, command, target, output, progress, stop_requested):
    """The child runner owns its mutex and native process-group cleanup."""
    report_path = Path(target[kind + '_output'])/'report.json'
    record = dict(kind=kind, command=command, runner_report=str(report_path),
        started_at=now(), forwarded_signals=[])
    target['commands'].append(record)
    save(output/'progress.json', progress)
    child = None
    try:
        with (output/(target['profile'] + '-' + kind + '.stdout')).open('xb') as stdout, \
                (output/(target['profile'] + '-' + kind + '.stderr')).open('xb') as stderr:
            if stop_requested:
                record['not_launched'] = 'stop requested'
            else:
                child = subprocess.Popen(command, cwd=progress['repository'],
                    stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                    start_new_session=True)
                record['runner_pid'] = child.pid
                save(output/'progress.json', progress)
                forwarded = 0
                while child.poll() is None:
                    for signum in stop_requested[forwarded:]:
                        try:
                            child.send_signal(signum)
                        except ProcessLookupError:
                            pass
                        record['forwarded_signals'].append(signum)
                        forwarded += 1
                        save(output/'progress.json', progress)
                    try:
                        child.wait(timeout=0.2)
                    except subprocess.TimeoutExpired:
                        pass
    except Exception as error:
        record['error'] = dict(type=type(error).__name__, message=str(error))
    finally:
        if child is not None:
            if child.poll() is None:
                child.send_signal(signal.SIGTERM)
            # Never kill the runner before it has cleaned up its native group.
            record['exit_code'] = child.wait()
        record['finished_at'] = now()
        if child is None:
            record['cleanup_confirmed'] = True
        else:
            try:
                runner = json.loads(report_path.read_text())
                record['runner_status'] = runner.get('status')
                record['cleanup_confirmed'] = (
                    bool(runner.get('finished_at'))
                    and runner.get('remaining_process_group') == [])
            except (OSError, ValueError) as error:
                record['cleanup_confirmed'] = False
                record['report_error'] = str(error)
        save(output/'progress.json', progress)
    return record


def main():
    root = Path(__file__).resolve().parents[1]
    base = root/'experiments/julia/packagecompiler-v1'
    profiles = json.loads((base/'training-inputs.json').read_text())['profiles']
    by_id = {profile['profile']: profile for profile in profiles}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', nargs='+', choices=list(by_id), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if len(args.profiles) != len(set(args.profiles)):
        parser.error('--profiles must not contain duplicates')
    output = args.output.absolute()
    # Reuse the recorded current runtime, bundle root and depot pair.
    seed = json.loads((base/'builds/nbody-julia-5-v1/report.json').read_text())
    julia = seed['command'][0]
    bundle_root = Path(seed['command'][7]).parents[1]
    depot, retained_depot = seed['environment']['JULIA_DEPOT_PATH'].split(':')
    targets = []
    occupied = [output] if output.exists() or output.is_symlink() else []
    for profile in args.profiles:
        target = dict(profile=profile, status='pending', commands=[],
            bundle=str(bundle_root/profile/'bundle'),
            build_output=str(base/'builds'/(profile + '-v1')),
            validation_output=str(base/'validation'/(profile + '-v1')))
        targets.append(target)
        for name in ('bundle', 'build_output', 'validation_output'):
            path = Path(target[name])
            if path.exists() or path.is_symlink():
                occupied.append(path)
    if occupied:
        parser.error('refusing existing output or bundle: ' + ', '.join(map(str, occupied)))
    stop_requested = []
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, lambda received, frame: stop_requested.append(received))
    output.mkdir(parents=True)
    progress = dict(schema='julia-packagecompiler-serial-v1', status='running',
        repository=str(root), started_at=now(), profiles=args.profiles,
        targets=targets, stop_signals=stop_requested, benchmark_samples=0,
        timing_admission=False, automatic_retries=0)
    save(output/'progress.json', progress)
    for target in targets:
        if stop_requested:
            break
        profile = target['profile']
        target['status'] = 'building'
        build = [sys.executable, '-I', '-S', '-B', str(root/'tools/build_julia_app.py'),
            '--julia', julia, '--project', str(base/'toolchain'),
            '--package', str(base/'packages'/profile), '--bundle', target['bundle'],
            '--training', str(root/by_id[profile]['training']),
            '--builder', str(base/'build_app.jl'), '--depot', depot,
            '--retained-depot', retained_depot, '--executable', profile,
            '--output', target['build_output']]
        result = run_command('build', build, target, output, progress, stop_requested)
        if stop_requested or not result['cleanup_confirmed']:
            target['status'] = 'interrupted' if stop_requested else 'cleanup-unconfirmed'
            break
        if result.get('exit_code') != 0 or result.get('runner_status') != 'built-awaiting-output-validation':
            target['status'] = 'build-failed'
            save(output/'progress.json', progress)
            continue
        target['status'] = 'validating'
        validation = [sys.executable, '-I', '-S', '-B', str(root/'tools/validate_julia_app.py'),
            '--profile', profile, '--bundle', target['bundle'],
            '--output', target['validation_output']]
        result = run_command('validation', validation, target, output, progress, stop_requested)
        if stop_requested or not result['cleanup_confirmed']:
            target['status'] = 'interrupted' if stop_requested else 'cleanup-unconfirmed'
            break
        target['status'] = ('output-validated' if result.get('exit_code') == 0
            and result.get('runner_status') == 'passed' else 'validation-failed')
        save(output/'progress.json', progress)
    progress['finished_at'] = now()
    progress['status'] = ('interrupted' if stop_requested else
        'cleanup-unconfirmed' if any(t['status'] == 'cleanup-unconfirmed' for t in targets) else
        'completed' if all(t['status'] == 'output-validated' for t in targets) else 'completed-with-failures')
    save(output/'progress.json', progress)
    print(json.dumps(dict(status=progress['status'], progress=str(output/'progress.json'))))
    return 128 + stop_requested[0] if stop_requested else (0 if progress['status'] == 'completed' else 1)


if __name__ == '__main__':
    raise SystemExit(main())
