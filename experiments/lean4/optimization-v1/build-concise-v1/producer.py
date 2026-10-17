"""Build immutable, explicitly bundled Lean optimization candidates serially."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / 'experiments/lean4/optimization-v1'
TOOLCHAIN = Path('/private/tmp/mech-lean4-toolchain/lean-4.35.0-darwin_aarch64')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=['fast', 'concise'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--benchmarks', nargs='*')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(STUDY) and not output.exists()
    manifest_path = STUDY / 'plan.json'
    manifest = json.loads(manifest_path.read_text())
    variant = manifest['variants'][args.variant]
    source = ROOT / variant['source']
    selected = args.benchmarks or list(variant['profiles'])
    assert selected and len(set(selected)) == len(selected)
    assert set(selected) <= set(variant['profiles'])
    output.mkdir(parents=True)
    snapshot = output / 'source'
    shutil.copytree(source, snapshot)
    build = ROOT / 'experiments/lean4/.build/optimization-v1' / output.name
    build.mkdir(parents=True, exist_ok=False)
    sdk = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip()
    report = dict(schema='lean-variant-native-build.v1', status='BUILDING',
                  variant=args.variant, toolchain=str(TOOLCHAIN), build_directory=str(build),
                  source_directory=str(snapshot), plan_sha256=sha(manifest_path),
                  controller_sha256=sha(__file__), commands=[], profiles={}, benchmark_samples=0,
                  sources={str(p.relative_to(ROOT)): sha(p) for p in snapshot.iterdir() if p.is_file()})
    shutil.copyfile(__file__, output / 'producer.py')
    shutil.copyfile(manifest_path, output / 'plan.json')
    env = dict(os.environ, LEAN_PATH=str(build))

    def save():
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    def run(command, name):
        command = [str(arg) for arg in command]
        entry = dict(command=command, cwd=str(snapshot))
        report['commands'].append(entry)
        save()
        with (output / (name + '.stdout')).open('wb') as out, (output / (name + '.stderr')).open('wb') as err:
            result = subprocess.run(command, cwd=snapshot, env=env, stdout=out, stderr=err, timeout=300)
        entry['exit_code'] = result.returncode
        save()
        if result.returncode:
            report['status'] = 'BUILD_FAILED'
            save()
            print((output / (name + '.stdout')).read_text(), flush=True)
            print((output / (name + '.stderr')).read_text(), flush=True)
            raise SystemExit(result.returncode)
        print(name, 'PASS', flush=True)

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['common_mutex_inode'] = os.fstat(lock.fileno()).st_ino
        for benchmark in selected:
            units = variant['profiles'][benchmark]['files']
            assert units[0] == benchmark + '.lean'
            assert all((snapshot / name).is_file() for name in units)
            assert [name for name in units if name.endswith('.lean')] == [benchmark + '.lean']
            run([TOOLCHAIN / 'bin/lean', '-j1', '-o', build / (benchmark + '.olean'),
                 '-c', build / (benchmark + '.c'), benchmark + '.lean'], benchmark + '-lean')
            extra = [snapshot / name for name in units if name.endswith('.c')]
            libraries = ['/opt/homebrew/opt/pcre2/lib/libpcre2-8.a'] if benchmark == 'regexredux' else []
            command = [TOOLCHAIN / 'bin/leanc', '-O3', '-DNDEBUG', '-fno-fast-math', '-ffp-contract=off',
                       '-mmacosx-version-min=14.4', '-isysroot', sdk, '-isystem', sdk + '/usr/include',
                       '-I/opt/homebrew/opt/pcre2/include', '-o', build / benchmark,
                       build / (benchmark + '.c'), *extra, *libraries]
            run(command, benchmark + '-native')
            report['profiles'][benchmark] = dict(
                files=units, binary=str(build / benchmark), binary_sha256=sha(build / benchmark),
                generated_c=str(build / (benchmark + '.c')),
                generated_c_sha256=sha(build / (benchmark + '.c')),
                linked_native_helpers=[str(p) for p in extra],
                libraries={p: sha(p) for p in libraries})
            save()
        assert all(sha(ROOT / name) == digest for name, digest in report['sources'].items())
        report['status'] = 'COMPILED_AWAITING_CONFORMANCE'
        save()


if __name__ == '__main__':
    main()
