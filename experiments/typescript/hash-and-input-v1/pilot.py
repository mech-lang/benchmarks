#!/usr/bin/env python3
"""Isolated, randomized reduced-input comparison of four qualified TS variants."""
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
PROCESS = ROOT / 'experiments/elixir/rolling-v1/pilot-1m-v1/process.py'
LOCK = Path('/private/tmp/mech-clbg-timing.lock')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


qualified = load('typescript_input_map_qualification', HERE / 'qualify.py')
sha, write = qualified.sha, qualified.write


def prepare():
    native = HERE / 'native-v1/results.json'
    result = json.loads(native.read_bytes())
    assert result['status'] == 'passed' and result['output_checks'] == 280
    assert result['complete_work_checks'] == 140 and result['rejection_checks'] == 12
    directory = HERE / 'pilot-v1'
    directory.mkdir(exist_ok=False)
    input_path = ROOT / 'experiments/implementation-audit/remaining-v1/pilot-v1/three-1m.fasta'
    raw = input_path.read_bytes()
    assert len(qualified.bases(raw)) == 1000000
    expected = directory / 'expected.stdout'
    expected.write_bytes(qualified.shared.nucleotide_reference(raw))
    commands = {label: [str(qualified.NODE), str(HERE / '.build/native-v1' / label / 'emitted/knucleotide.js')]
                for label in qualified.SOURCES}
    pins = {str(path): sha(path) for path in [Path(__file__), HERE / 'qualify.py',
            HERE / 'native-plan-v1.json', native, PROCESS, input_path, expected, qualified.NODE,
            *qualified.SOURCES.values(), *[Path(command[1]) for command in commands.values()]]}
    order = []
    rng = random.Random(193763)
    for round_number in range(1, 4):
        labels = list(commands)
        rng.shuffle(labels)
        order.extend(dict(round=round_number, label=label) for label in labels)
    write(directory / 'plan.json', dict(schema='typescript-input-map-reduced-pilot.v1',
        pins=pins, commands=commands, order=order, input=str(input_path), expected=str(expected),
        common_mutex_inode=LOCK.stat().st_ino, input_bytes=len(raw), selected_bases=1000000,
        sample_scope='First one million retained THREE bases only; preceding records omitted. Fresh whole processes.',
        full_size_results=False, chart_admission=False,
        mech_aot_denominator=None,
        mech_aot_denominator_status='No qualified Mech AOT sample exists on this exact reduced input; full-size timings must not be substituted.',
        preselection='Use this fixed three-round pilot to select at most one new full-size candidate; no full timing starts here.'))
    print(sha(directory / 'plan.json'), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.prepare:
        prepare()
        return
    plan_path = HERE / 'pilot-v1/plan.json'
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
    output = HERE / 'pilot-v1/run-v1'
    output.mkdir(exist_ok=False)
    process = load('typescript_pilot_process', PROCESS)
    report = dict(schema=plan['schema'], status='running', plan_sha256=sha(plan_path),
                  full_size_results=False, chart_admission=False, observations=[])
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['common_mutex_inode']
        environment = dict(PATH='/opt/homebrew/bin:/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC',
            UV_THREADPOOL_SIZE='8', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')

        def one(command, name, stdin=None):
            row = process.one(command, output / name, environment, output, lock.fileno(), timeout=120, stdin=stdin)
            process.success(row)
            assert not (output / name / 'stderr.bin').read_bytes()
            return row

        try:
            one(['/usr/bin/pmset', '-g', 'batt'], 'power-source')
            assert b'AC Power' in (output / 'power-source/stdout.bin').read_bytes()
            one(['/usr/bin/pmset', '-g', 'custom'], 'power-settings')
            assert not any('lowpowermode' in line and line.split()[-1] != '0'
                           for line in (output / 'power-settings/stdout.bin').read_text().splitlines())
            one(['/bin/ps', '-axo', 'pid,ppid,pgid,pcpu,comm'], 'processes-before')
            for index, job in enumerate(plan['order']):
                name = f'{index:02d}-' + job['label']
                row = one(plan['commands'][job['label']], name, stdin=plan['input'])
                assert sha(output / name / 'stdout.bin') == sha(Path(plan['expected']))
                observation = dict(job, directory=name, seconds=row['elapsed_seconds'],
                    maximum_rss_bytes=row['maximum_rss_bytes'], mech_aot_multiple=None,
                    mech_aot_comparison_status=plan['mech_aot_denominator_status'])
                report['observations'].append(observation)
                print(json.dumps(observation), flush=True)
            one(['/bin/ps', '-axo', 'pid,ppid,pgid,pcpu,comm'], 'processes-after')
            summary = {}
            for label in plan['commands']:
                observations = [row for row in report['observations'] if row['label'] == label]
                values = [row['seconds'] for row in observations]
                summary[label] = dict(samples_seconds=values, median_seconds=statistics.median(values),
                    stdev_seconds=statistics.stdev(values), peak_rss_bytes=max(row['maximum_rss_bytes'] for row in observations),
                    mech_aot_multiple=None, mech_aot_comparison_status=plan['mech_aot_denominator_status'])
            assert all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
            report.update(status='passed', summary=summary, pins_unchanged=True)
        except BaseException as error:
            report.update(status='failed', error=repr(error))
            raise
        finally:
            write(output / 'results.json', report)
    print(json.dumps(dict(status=report['status'], summary=summary)), flush=True)


if __name__ == '__main__':
    main()
