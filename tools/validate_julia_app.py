"""Check a PackageCompiler executable against an existing bounded oracle, without JIT."""
import argparse
import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_julia_app import group_members, save, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    training = json.loads((root/'experiments/julia/packagecompiler-v1/training-inputs.json').read_text())
    profile = next(p for p in training['profiles'] if p['profile'] == args.profile)
    corpus = root/'experiments/shared/bounded-corpus-v1/cases'
    manifest = json.loads((corpus/'manifest.json').read_text())
    case = next(c for c in manifest['cases'] if c['benchmark'] == profile['workload']
        and c['case'] == (args.case or profile['case']))
    assert case['expected_exit'] == 0
    executable = args.bundle/'bin'/args.profile
    image = args.bundle/'lib/julia/sys.dylib'
    assert executable.is_file() and image.is_file() and not args.output.exists()
    stop_requested = []
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, lambda signum, frame: stop_requested.append(signum))
    with Path('/tmp/mech-clbg-timing.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        args.output.mkdir(parents=True)
        stdin = corpus/case['stdin']['path']
        expected = corpus/case['expected']['path']
        assert sha(stdin) == case['stdin']['sha256']
        assert sha(expected) == case['expected']['sha256']
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C',
            JULIA_NUM_THREADS='8', JULIA_LOAD_CODEGEN_LIB='0', OPENBLAS_NUM_THREADS='1',
            OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
        command = [str(executable)]
        if case['input_kind'] == 'integer-argument':
            command.append(str(case['n']))
        command += ['--julia-args', '--startup-file=no', '--history-file=no', '--compile=no']
        report = dict(schema='julia-packagecompiler-native-output-v1', profile=args.profile,
            case=case['case'], command=command, environment=environment,
            executable_sha256=sha(executable), stdin_sha256=sha(stdin), expected_sha256=sha(expected),
            sysimage=dict(path=str(image), sha256=sha(image)),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,
            started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            benchmark_samples=0, errors=[])
        process = None
        try:
            with stdin.open('rb') as input_file, (args.output/'actual.stdout').open('xb') as stdout, \
                    (args.output/'actual.stderr').open('xb') as stderr:
                process = subprocess.Popen(command, env=environment, cwd=args.bundle,
                    stdin=input_file, stdout=stdout, stderr=stderr, start_new_session=True,
                    pass_fds=(lock.fileno(),))
                report['pid'] = process.pid
                deadline = time.monotonic() + 120
                while process.poll() is None:
                    if stop_requested or time.monotonic() > deadline:
                        raise TimeoutError('Native output validation interrupted or exceeded 120 seconds')
                    if (args.output/'actual.stdout').stat().st_size > 16*1024**2:
                        raise RuntimeError('Bounded output exceeded 16 MiB')
                    time.sleep(0.05)
                report['exit_code'] = process.wait()
            actual = (args.output/'actual.stdout').read_bytes()
            wanted = expected.read_bytes()
            report['exact_complete_bytes'] = actual == wanted
            valid = actual == wanted
            if case['benchmark'] in ('nbody', 'spectralnorm'):
                try:
                    values, references = [list(map(float, b.split())) for b in (actual, wanted)]
                    tolerance = 1e-8 if case['benchmark'] == 'nbody' else 1e-9
                    valid = len(values) == len(references) and all(math.isfinite(a)
                        and abs(a-b) <= tolerance for a, b in zip(values, references))
                    report['absolute_tolerance'] = tolerance
                except ValueError:
                    valid = False
            report['complete_output_matches'] = valid
            assert report['exit_code'] == 0 and valid, 'Native executable failed complete-output validation'
        except BaseException as error:
            report['errors'].append(dict(type=type(error).__name__, message=str(error)))
        finally:
            if process is not None:
                if process.poll() is None or group_members(process.pid):
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
                    process.wait(timeout=5)
                report['remaining_process_group'] = group_members(process.pid)
                if report['remaining_process_group']:
                    report['errors'].append(dict(type='GroupCleanup', message='Owned group remains'))
            report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report['stdout_sha256'] = sha(args.output/'actual.stdout')
            report['stderr_sha256'] = sha(args.output/'actual.stderr')
            report['executable_unchanged'] = sha(executable) == report['executable_sha256']
            report['sysimage_unchanged'] = sha(image) == report['sysimage']['sha256']
            report['status'] = 'passed' if not report['errors'] and report['executable_unchanged'] and report['sysimage_unchanged'] else 'failed'
            save(args.output/'report.json', report)
        print(json.dumps(report))
        return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
