"""Build one ordinary PackageCompiler app while holding the benchmark mutex.

Compilation logs and bundle identities are retained; this produces no timings.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import time


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def group_members(pgid):
    rows = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,stat='],
        capture_output=True, text=True, check=True, timeout=5).stdout.splitlines()
    return [dict(pid=int(x[0]), pgid=int(x[1]), state=x[2])
        for row in rows if len(x := row.split()) == 3 and int(x[1]) == pgid]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['julia', 'project', 'package', 'bundle', 'training', 'builder', 'depot', 'retained-depot', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args()
    for name in ['julia', 'project', 'package', 'training', 'builder', 'retained_depot']:
        path = getattr(args, name)
        assert path.is_absolute() and path.exists(), str(path)
    assert 1 <= args.timeout <= 3600
    assert args.output.is_absolute() and not args.output.exists()
    assert args.bundle.is_absolute() and not args.bundle.exists()
    assert args.depot.is_absolute()
    stop_requested = []
    def interrupted(signum, frame):
        stop_requested.append(signum)
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    lock_path = Path('/tmp/mech-clbg-timing.lock')
    with lock_path.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened, named = os.fstat(lock.fileno()), lock_path.stat()
        assert stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
        args.output.mkdir(parents=True)
        args.bundle.parent.mkdir(parents=True, exist_ok=True)
        args.depot.mkdir(parents=True, exist_ok=True)
        files = [args.builder, args.training, args.project/'Project.toml',
            args.project/'Manifest.toml', args.package/'Project.toml', args.julia]
        files += sorted((args.package/'src').rglob('*.jl'))
        pins = {str(path): sha(path) for path in files}
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C',
            JULIA_DEPOT_PATH=str(args.depot) + ':' + str(args.retained_depot),
            JULIA_PKG_OFFLINE='true', JULIA_PKG_SERVER='',
            JULIA_NUM_THREADS='8', JULIA_IMAGE_THREADS='1', JULIA_NUM_PRECOMPILE_TASKS='1',
            OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
        command = [str(args.julia), '--startup-file=no', '--history-file=no', '--color=no',
            '--project=' + str(args.project), str(args.builder), str(args.package),
            str(args.bundle), str(args.training), args.executable]
        report = dict(schema='julia-packagecompiler-build-v1', status='running',
            started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            command=command, environment=environment, input_sha256=pins,
            benchmark_samples=0, timeout_seconds=args.timeout, automatic_retries=0,
            common_mutex=dict(path=str(lock_path), inode=opened.st_ino), errors=[])
        save(args.output/'report.json', report)
        process = None
        started = time.monotonic()
        try:
            with (args.output/'stdout.txt').open('xb') as stdout, (args.output/'stderr.txt').open('xb') as stderr:
                if stop_requested:
                    raise InterruptedError('Build interrupted before launch')
                process = subprocess.Popen(command, cwd=args.package, env=environment,
                    stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                    start_new_session=True, pass_fds=(lock.fileno(),))
                report['pid'] = process.pid
                report['pgid'] = process.pid
                save(args.output/'report.json', report)
                while process.poll() is None:
                    if stop_requested:
                        raise InterruptedError('Build interrupted')
                    if time.monotonic() - started > args.timeout:
                        raise TimeoutError('PackageCompiler build exceeded deadline')
                    if any(path.stat().st_size > 64 * 1024**2
                        for path in (args.output/'stdout.txt', args.output/'stderr.txt')):
                        raise RuntimeError('Compilation log exceeded 64 MiB')
                    time.sleep(0.25)
                report['exit_code'] = process.wait()
                assert report['exit_code'] == 0, 'PackageCompiler returned nonzero; inspect retained logs'
        except BaseException as error:
            report['errors'].append(dict(type=type(error).__name__, message=str(error)))
        finally:
            if process is not None:
                remaining = group_members(process.pid)
                if process.poll() is None or remaining:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    deadline = time.monotonic() + 5
                    while group_members(process.pid) and time.monotonic() < deadline:
                        if process.poll() is not None:
                            process.wait()
                        time.sleep(0.05)
                    if group_members(process.pid):
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                if process.poll() is None:
                    process.wait(timeout=5)
                report['exit_code'] = process.returncode
                report['remaining_process_group'] = group_members(process.pid)
                if report['remaining_process_group']:
                    report['errors'].append(dict(type='GroupCleanup', message='Owned process group remains'))
            report['input_files_unchanged'] = all(path.exists() and sha(path) == expected
                for name, expected in pins.items() for path in [Path(name)])
            if not report['input_files_unchanged']:
                report['errors'].append(dict(type='InputChanged', message='Build inputs changed'))
            report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report['diagnostic_build_seconds'] = time.monotonic() - started
            executable = args.bundle/'bin'/args.executable
            report['executable'] = dict(path=str(executable), sha256=sha(executable)) if executable.is_file() else None
            report['status'] = 'built-awaiting-output-validation' if not report['errors'] and report['executable'] else 'build-failed'
            save(args.output/'report.json', report)
            save(args.output/'terminal.json', dict(status=report['status'],
                report_sha256=sha(args.output/'report.json'),
                stdout_sha256=sha(args.output/'stdout.txt'), stderr_sha256=sha(args.output/'stderr.txt'),
                common_mutex_inode=opened.st_ino, benchmark_samples=0))
        print(json.dumps({key: report[key] for key in ['status', 'exit_code', 'executable', 'errors']}))
        return 0 if report['status'] == 'built-awaiting-output-validation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
