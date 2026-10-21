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
    qualification = ROOT/'experiments/crystal/regex-byte-offsets-v1/utf8-once-v1/native-v1/report.json'
    report = json.loads(qualification.read_bytes())
    assert report['status'] == 'passed-bounded-outputs-and-invalid-utf8-rejection' and report['pins_unchanged']
    previous_path = HERE/'pilot-v2/plan.json'
    previous = json.loads(previous_path.read_bytes())
    case = next(case for case in previous['cases'] if case['language'] == 'crystal')
    case = dict(case, labels=['cr-parent', 'cr-bytes', 'cr-utf8'])
    pins = dict(previous['pins'])
    candidate = next(row for row in report['compilations'] if row['variant'] == 'parallel')
    binary = Path(candidate['binary'])
    assert sha(binary) == candidate['binary_sha256']
    for path in [Path(__file__), previous_path, qualification, binary,
                 ROOT/'experiments/crystal/regex-byte-offsets-v1/utf8-once-v1/source/parallel.cr',
                 ROOT/'experiments/crystal/regex-byte-offsets-v1/utf8-once-v1/source-counts-v1/receipt.json']:
        pins[str(path)] = sha(path)
    commands = {label: previous['commands'][label] for label in ['cr-parent','cr-bytes']}
    commands['cr-utf8'] = [str(binary)]
    rng = random.Random(53719)
    order = []
    for round_number in range(3):
        labels = list(case['labels'])
        rng.shuffle(labels)
        order.extend({'language':'crystal','round':round_number+1,'label':label} for label in labels)
    directory = HERE/'utf8-pilot-v1'
    directory.mkdir(exist_ok=False)
    plan = {'schema':'crystal-validation-once-reduced-pilot.v1','status':'prepared','full_mode_available':False,
            'chart_admission':False,'pins':pins,'cases':[case],'commands':commands,'order':order,
            'common_mutex_inode':LOCK.stat().st_ino,
            'sample_scope':'Same preselected TWO/THREE reduced-input mix as pilot-v2; isolate byte-offset and UTF-validation hypotheses.',
            'known_remaining_gates':'Independent source/ownership review, complete runtime/work qualification and separately preselected full-size observations.'}
    write(directory/'plan.json',plan)
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
    plan_path = HERE/'utf8-pilot-v1/plan.json'
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
    process = load('quantitative_pilot_process', PROCESS)
    output = HERE/'utf8-pilot-v1/run-v1'
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
