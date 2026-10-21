#!/usr/bin/env python3
"""Fixed reduced-input diagnostic pilots; full-size/chart admission unavailable."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCK = Path('/private/tmp/mech-clbg-timing.lock')
PROCESS = ROOT/'experiments/elixir/rolling-v1/pilot-1m-v1/process.py'


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


def prepare():
    native = json.loads((HERE/'native-v1/report.json').read_bytes())
    assert native['status'] == 'passed-bounded-output-checks' and native['pins_unchanged']
    bounded = load('bounded_references', HERE/'native_bounded.py')
    directory = HERE/'pilot-v1'
    directory.mkdir(exist_ok=False)
    original = ROOT/'experiments/lean4/.build/inputs/n5000000.fasta'
    assert sha(original) == '97197f5957a12f8a859ba7edff6d97994daa18afacd77db21fa68c6f2e447e38'
    prefix = directory/'prefix-8m.fasta'
    with original.open('rb') as stream:
        prefix.write_bytes(stream.read(8*1024*1024))
    target = bytearray()
    started = False
    with original.open('rb') as stream:
        for line in stream:
            if line.startswith(b'>THREE '):
                started = True
            elif started and len(target) < 1000000:
                target.extend(line.rstrip(b'\r\n')[:1000000-len(target)])
            if len(target) == 1000000:
                break
    assert len(target) == 1000000
    dna = directory/'three-1m.fasta'
    dna.write_bytes(b'>THREE pilot\n'+b'\n'.join(target[i:i+60] for i in range(0,len(target),60))+b'\n')
    cases = [
        {'language': 'typescript', 'labels': ['ts-parent', 'ts-rolling'], 'input': dna,
         'expected': bounded.nucleotide_reference(dna.read_bytes()),
         'limit': 'First1m THREE bases only; preceding records omitted. Does not measure full input parsing.'},
        {'language': 'crystal', 'labels': ['cr-parent', 'cr-bytes'], 'input': prefix,
         'expected': bounded.regex_reference(prefix.read_bytes()),
         'limit': 'First8MiB of the canonical regex FASTA; EOF truncation is intentional. Reduced input only.'},
        {'language': 'd', 'labels': ['d-parent', 'd-inplace'], 'input': prefix,
         'expected': bounded.reverse_reference(prefix.read_bytes()),
         'limit': 'First8MiB of the canonical FASTA, ending within a record. Reduced input only.'},
    ]
    pins = dict(json.loads((HERE/'native-plan-v1.json').read_bytes())['pins'])
    pins.update({str(p): sha(p) for p in [Path(__file__), PROCESS, HERE/'native-plan-v1.json', HERE/'native_bounded.py', HERE/'native-v1/report.json',
                                            ROOT/'experiments/crystal/regex-byte-offsets-v1/source-counts-v3/receipt.json']}
                )
    build = HERE/'.build/bounded-v1'
    node = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    commands = {}
    for case in cases:
        expected = directory/(case['language']+'.expected')
        expected.write_bytes(case.pop('expected'))
        case.update(input=str(case['input']), expected=str(expected))
        pins[str(expected)] = sha(expected)
        pins[case['input']] = sha(Path(case['input']))
        for label in case['labels']:
            command = [node, build/label/'emitted/knucleotide.js'] if label.startswith('ts-') else [build/label]
            commands[label] = list(map(str, command))
            for path in command:
                pins[str(path)] = sha(path)
    order = []
    rng = random.Random(826719)
    for case in cases:
        for round_number in range(3):
            labels = list(case['labels'])
            rng.shuffle(labels)
            order.extend({'language': case['language'], 'round': round_number+1, 'label': label} for label in labels)
    plan = {'schema': 'reduced-input-language-pilots.v1', 'status': 'prepared', 'full_mode_available': False,
            'chart_admission': False, 'sample_scope': 'Reduced-input diagnostics; no full-size speedup claim.',
            'pins': pins, 'cases': cases, 'commands': commands, 'order': order,
            'common_mutex_inode': LOCK.stat().st_ino, 'known_remaining_gates':
                'Independent ownership review, detailed runtime closure/work qualification and separate full-size preselection remain pending.'}
    write(directory/'plan.json', plan)
    print(sha(directory/'plan.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.prepare:
        prepare()
        return
    plan_path = HERE/'pilot-v1/plan.json'
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
    process = load('quantitative_pilot_process', PROCESS)
    output = HERE/'pilot-v1/run-v1'
    output.mkdir(exist_ok=False)
    report = {'schema': plan['schema'], 'status': 'running', 'plan_sha256': sha(plan_path),
              'full_size_results': False, 'chart_admission': False, 'observations': []}
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['common_mutex_inode']
        environment = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C', 'TZ': 'UTC',
                       'UV_THREADPOOL_SIZE': '8', 'CRYSTAL_WORKERS': '8', 'OMP_NUM_THREADS': '1',
                       'OPENBLAS_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '1'}
        def one(command, directory, stdin=None):
            result = process.one(command, output/directory, environment, output, lock.fileno(), timeout=120, stdin=stdin)
            process.success(result)
            assert not (output/directory/'stderr.bin').read_bytes()
            return result
        try:
            one(['/usr/bin/pmset', '-g', 'batt'], 'power-source')
            assert b'AC Power' in (output/'power-source/stdout.bin').read_bytes()
            one(['/usr/bin/pmset', '-g', 'custom'], 'power-settings')
            settings = (output/'power-settings/stdout.bin').read_text()
            assert not any('lowpowermode' in line and line.split()[-1] != '0' for line in settings.splitlines())
            one(['/bin/ps', '-axo', 'pid,ppid,pgid,pcpu,comm'], 'processes-before')
            cases = {case['language']: case for case in plan['cases']}
            for index, job in enumerate(plan['order']):
                case = cases[job['language']]
                directory = f'{index:02d}-'+job['label']
                result = one(plan['commands'][job['label']], directory, stdin=case['input'])
                assert sha(output/directory/'stdout.bin') == sha(Path(case['expected'])), 'Pilot complete output differs'
                report['observations'].append(dict(job, seconds=result['elapsed_seconds'],
                                                  maximum_rss_bytes=result['maximum_rss_bytes'], directory=directory))
            summary = {}
            for label in plan['commands']:
                observations = [r for r in report['observations'] if r['label'] == label]
                values = [r['seconds'] for r in observations]
                summary[label] = {'samples': values, 'median_seconds': statistics.median(values),
                                  'stdev_seconds': statistics.stdev(values),
                                  'peak_rss_bytes': max(r['maximum_rss_bytes'] for r in observations)}
            report.update(status='passed-reduced-input-pilots', summary=summary)
        except Exception as error:
            report.update(status='failed', error=repr(error))
            raise
        finally:
            report['pins_unchanged'] = all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
            report['lock_identity_unchanged'] = os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['common_mutex_inode']
            write(output/'report.json', report)
            print(json.dumps({k:v for k,v in report.items() if k != 'observations'}), flush=True)
            assert report['pins_unchanged'] and report['lock_identity_unchanged']


if __name__ == '__main__':
    main()
