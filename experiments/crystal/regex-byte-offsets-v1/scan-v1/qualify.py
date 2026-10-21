#!/usr/bin/env python3
"""Compile validation-once candidates and check complete bounded outputs."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BATCH = ROOT/'experiments/implementation-audit/remaining-v1'
LOCK = Path('/private/tmp/mech-clbg-timing.lock')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    plan_path = HERE/'native-plan-v1.json'
    if args.prepare:
        pins = dict(json.loads((BATCH/'native-plan-v1.json').read_bytes())['pins'])
        for path in [Path(__file__), *[HERE/f'source/{v}.cr' for v in ['block-compact','block-parallel','inline-compact','inline-parallel']], HERE/'source-counts-v1/receipt.json']:
            pins[str(path)] = sha(path)
        write(plan_path, {'schema': 'crystal-standard-scan-bounded.v1', 'pins': pins,
                         'mutex_inode': LOCK.stat().st_ino, 'quantitative_benchmark': False,
                         'full_timing_available': False, 'chart_admission': False})
        print(sha(plan_path))
        return
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert all(sha(Path(path)) == value for path,value in plan['pins'].items())
    output = HERE/'native-v1'
    output.mkdir(exist_ok=False)
    build = HERE/'.build/native-v1'
    build.mkdir(parents=True, exist_ok=False)
    bounded = load('bounded_references', BATCH/'native_bounded.py')
    capture = load('native_capture', bounded.PROCESS)
    report = {'schema': plan['schema'], 'plan_sha256': sha(plan_path), 'status': 'running', 'cases': [],
              'compilations': [], 'quantitative_benchmark': False, 'chart_admission': False}
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
        env = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C', 'TZ': 'UTC',
               'TMPDIR': str(build)+'/', 'CRYSTAL_PATH': str(bounded.CRYSTAL/'src'),
               'CRYSTAL_CACHE_DIR': str(build/'cache'), 'CRYSTAL_WORKERS': '8'}
        def one(command, name, stdin=None, invalid=False):
            result = capture.one(list(map(str,command)), output/name, env, build, lock.fileno(), timeout=120, stdin=stdin)
            if invalid:
                assert result['exit_code'] != 0 and not result['timed_out'] and not result['remaining_process_group']
                assert b'UTF' in (output/name/'stderr.bin').read_bytes()
            else:
                capture.success(result)
                assert not (output/name/'stderr.bin').read_bytes()
            return result
        try:
            cases = bounded.regex_cases()
            cases['utf8-near-matches'] = ('>h\nクリスタルagggtaaaéagggtaaaλtttaccct\n'*4).encode()
            cases['match-at-eof'] = b'>h\nagggtaaatttaccct'
            link = ('-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX14.4.sdk -mmacosx-version-min=14.4 '
                    '-L /opt/homebrew/Cellar/gmp/6.3.0/lib -L /opt/homebrew/Cellar/pcre2/10.49/lib -L '+str(bounded.CRYSTAL/'embedded/lib'))
            for variant in ['block-compact', 'block-parallel', 'inline-compact', 'inline-parallel']:
                source = HERE/f'source/{variant}.cr'
                binary = build/variant
                one([bounded.CRYSTAL/'embedded/bin/crystal', 'build', '--release', '--no-debug', '--no-color',
                     '--error-trace', '--mcpu', 'native', '--threads', '1', '--link-flags', link,
                     '-o', binary, source], 'compile-'+variant)
                report['compilations'].append({'variant': variant, 'source_sha256': sha(source),
                                               'binary': str(binary), 'binary_sha256': sha(binary)})
                for name, raw in cases.items():
                    inp = output/(name+'.stdin')
                    expected = output/(name+'.expected')
                    if not inp.exists():
                        inp.write_bytes(raw)
                        expected.write_bytes(bounded.regex_reference(raw))
                    one([binary], variant+'-'+name, stdin=inp)
                    actual = output/(variant+'-'+name)/'stdout.bin'
                    assert actual.read_bytes() == expected.read_bytes()
                    report['cases'].append({'variant': variant, 'case': name, 'passed': True, 'output_sha256': sha(actual)})
                invalid = output/'invalid-utf8.stdin'
                if not invalid.exists():
                    invalid.write_bytes(b'>h\nagggtaaa\xfftttaccct\n')
                one([binary], variant+'-invalid-utf8', stdin=invalid, invalid=True)
            report['status'] = 'passed-bounded-outputs-and-invalid-utf8-rejection'
        except Exception as error:
            report.update(status='failed', error=repr(error))
            raise
        finally:
            report['pins_unchanged'] = all(sha(Path(path)) == value for path,value in plan['pins'].items())
            report['lock_identity_unchanged'] = os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
            write(output/'report.json', report)
            print(json.dumps({k:v for k,v in report.items() if k not in ['cases','compilations']}), flush=True)
            assert report['pins_unchanged'] and report['lock_identity_unchanged']


if __name__ == '__main__':
    main()
