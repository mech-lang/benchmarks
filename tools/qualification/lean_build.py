"""Compile pinned Lean source to native executables, one compiler at a time."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/lean4/source-v1'
DEFAULT_TOOLCHAIN = Path('/private/tmp/mech-lean4-toolchain/lean-4.35.0-darwin_aarch64')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--toolchain', type=Path, default=DEFAULT_TOOLCHAIN)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('benchmarks', nargs='+')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    build = ROOT / 'experiments/lean4/.build/native-v1'
    build.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LEAN_PATH=str(build))
    sdk = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip()
    report = dict(schema='lean-native-build.v1', status='RUNNING',
                  toolchain=str(args.toolchain), commands=[], artifacts={},
                  sources={str(p.relative_to(ROOT)): sha(p) for p in SOURCE.iterdir() if p.is_file()},
                  benchmark_measurements=0)

    def save():
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    def run(command, name):
        record = dict(command=[str(x) for x in command], cwd=str(SOURCE))
        report['commands'].append(record)
        save()
        with (args.output / (name + '.stdout')).open('wb') as out, (args.output / (name + '.stderr')).open('wb') as err:
            result = subprocess.run(command, cwd=SOURCE, env=env, stdout=out, stderr=err, timeout=300)
        record['exit_code'] = result.returncode
        save()
        if result.returncode:
            report['status'] = 'BUILD_FAILED'
            save()
            print(name, 'FAILED', flush=True)
            print((args.output / (name + '.stdout')).read_text(), flush=True)
            print((args.output / (name + '.stderr')).read_text(), flush=True)
            raise SystemExit(result.returncode)
        print(name, 'PASS', flush=True)

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['common_mutex_inode'] = os.fstat(lock.fileno()).st_ino
        save()
        run([args.toolchain / 'bin/lean', '-j1', '-o', build / 'Common.olean', '-c', build / 'Common.c', 'Common.lean'], 'common')
        for bench in args.benchmarks:
            run([args.toolchain / 'bin/lean', '-j1', '-o', build / (bench + '.olean'), '-c', build / (bench + '.c'), bench + '.lean'], bench + '-lean')
            extra = [SOURCE / 'Regex.c', '/opt/homebrew/opt/pcre2/lib/libpcre2-8.a'] if bench == 'regexredux' else []
            command = [args.toolchain / 'bin/leanc', '-O3', '-DNDEBUG', '-fno-fast-math', '-ffp-contract=off',
                       '-mmacosx-version-min=14.4', '-isysroot', sdk, '-isystem', str(Path(sdk) / 'usr/include'), '-I/opt/homebrew/opt/pcre2/include',
                       '-o', build / bench, build / 'Common.c', build / (bench + '.c'), SOURCE / 'Format.c', *extra]
            run(command, bench + '-native')
            report['artifacts'][bench] = dict(binary=str(build / bench), binary_sha256=sha(build / bench),
                                              generated_c=str(build / (bench + '.c')), generated_c_sha256=sha(build / (bench + '.c')))
        report['status'] = 'COMPILED_AWAITING_CONFORMANCE'
        report['sources_unchanged'] = all(sha(ROOT / name) == digest for name, digest in report['sources'].items())
        save()


if __name__ == '__main__':
    main()
