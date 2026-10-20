"""Pinned, serial spectral-norm comparison; --prepare starts no native process."""
import argparse
import difflib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'experiments/bqn/spectral-sum-v1'
PLAN = HERE / 'plan.json'
PARENT = ROOT / 'archive/comparisons/array-comparison/all-20261009/sources/spectralnorm-faithful.bqn'
PARENT_SHA = '5e6955104b07d3c2fdda9b5ee29c80ced059c064bd386db33d941f6c2b29d380'
RUNTIME = ROOT / 'experiments/bqn/optimization-v1/.build/CBQN/BQN'
RUNTIME_SHA = '0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5'
BUILD = ROOT / 'experiments/bqn/optimization-v1/release-build.json'
COMMIT = 'c893d3e7828899a50150df03ad33c9052fa51d3c'
HELPER = ROOT / 'tools/qualification/lean_run.py'
HELPER_SHA = '313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases'
NS = [1, 2, 3, 5, 9, 10, 100]
IDENTITIES = ['parent-faithful', 'row-sum', 'row-and-dots-sum']
FULL = dict(n=5500, bytes=12, sha256='f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb')
SEED = 20261020


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), sha256=sha(path))


def atom(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def load(path):
    return json.loads(Path(path).read_text())


def derived_sources():
    require(sha(PARENT) == PARENT_SHA, 'Retained faithful parent changed')
    parent = PARENT.read_bytes()
    require(parent.count('+´'.encode()) == 4, 'Unexpected parent reduction inventory')
    require(parent.count('{+´v×'.encode()) == 2, 'Unexpected matrix-row reduction inventory')
    rows = parent.replace('{+´v×'.encode(), '{•math.Sum v×'.encode())
    return dict(zip(IDENTITIES, [parent, rows, rows.replace('+´'.encode(), '•math.Sum '.encode())]))


def make_plan():
    expected_sources = derived_sources()
    for name, expected in expected_sources.items():
        require((HERE/'sources'/(name+'.bqn')).read_bytes() == expected, 'Source is not the exact reviewed derivation: '+name)
    require(sha(RUNTIME) == RUNTIME_SHA, 'Use the exact rebuilt release runtime')
    require(sha(HELPER) == HELPER_SHA, 'Saved process controller changed')
    build = load(BUILD)
    require(build['schema'] == 'bqn-runtime-build.v1' and build['runtime_use'] == 'release-timing'
            and build['commit'] == COMMIT and build['release_source_status'] == ''
            and build['witness_patch_sha256'] is None, 'Wrong release build receipt')
    require(any(row['sha256'] == RUNTIME_SHA and row['path'].endswith('/.build/CBQN/BQN')
                for row in build['artifacts']), 'Runtime not bound to build receipt')
    ffi = next(row for row in build['artifacts'] if row['path'] == '/opt/homebrew/opt/libffi/lib/libffi.8.dylib')
    require(sha(ffi['path']) == ffi['sha256'], 'Linked libffi changed')
    corpus = load(CORPUS/'manifest.json')
    cases = sorted((row for row in corpus['cases'] if row['benchmark'] == 'spectralnorm'), key=lambda row: row['n'])
    require([row['n'] for row in cases] == NS, 'Need exactly all seven shared spectral cases')
    references = []
    for row in cases:
        require(row['expected_exit'] == 0 and row['validation'] == 'exact-complete-bytes', 'Unexpected spectral validation policy')
        for key in ['stdin', 'expected']:
            path = CORPUS/row[key]['path']
            require(sha(path) == row[key]['sha256'] and path.stat().st_size == row[key]['bytes'], 'Changed shared '+key)
            references.append(ref(path))
    parent_text = expected_sources['parent-faithful'].decode()
    return dict(schema='bqn-spectral-sum-plan.v1', status='PREPARED-NO-EXECUTION', benchmark='spectralnorm',
        parent=ref(PARENT), runtime=ref(RUNTIME), runtime_build=ref(BUILD), runtime_commit=COMMIT,
        controller=ref(__file__), process_controller=ref(HELPER), review=ref(HERE/'REVIEW.md'),
        corpus=ref(CORPUS/'manifest.json'), bounded_cases=cases, reference_files=references,
        runtime_dependencies=[dict(path=ffi['path'], resolved_path=ffi['resolved_path'], sha256=ffi['sha256'])],
        sources={name: ref(HERE/'sources'/(name+'.bqn')) for name in IDENTITIES},
        source_deltas={name: ''.join(difflib.unified_diff(parent_text.splitlines(True), expected_sources[name].decode().splitlines(True),
            fromfile=str(PARENT.relative_to(ROOT)), tofile=str((HERE/'sources'/(name+'.bqn')).relative_to(ROOT)))) for name in IDENTITIES},
        full=FULL, samples=3, order_seed=SEED, common_mutex='/tmp/mech-clbg-timing.lock',
        required_work=dict(status='source-reviewed-awaiting-native-output', separate_functions=['A', 'Av', 'Atv', 'AtAv'],
            atav_applications=20, matrix_vector_products=40, coefficient_evaluations='40*n*n',
            single_thread_application=True, new_ffi_or_native_helper=False, precomputed_matrix=False),
        timing_boundary='Fresh BQN process through exit, including startup, parsing argv, all forty matrix-vector products and output; excludes hashing, reference validation and power checks.',
        runtime_support='Only the existing CBQN executable and its linked runtime dependencies; no application imports or new standard-library source.',
        parent_origin='Retained suite-derived faithful adaptation; predecessor origin uncertainty is inherited. Original upstream alternative is unchanged.',
        chart_admission=False, canonical_data_changed=False)


def pins_from(plan):
    pins = [plan[key] for key in ['parent', 'runtime', 'runtime_build', 'controller', 'process_controller', 'review', 'corpus']]
    pins += [ref(PLAN)] + list(plan['sources'].values()) + plan['reference_files'] + plan['runtime_dependencies']
    return {row['path']: row['sha256'] for row in pins}


def check_pins(pins):
    require(all(sha(ROOT/path) == digest for path, digest in pins.items()), 'A source/runtime/support/reference pin changed')


def power():
    battery = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
    settings = subprocess.check_output(['/usr/bin/pmset', '-g', 'custom'], text=True)
    low_power = [line.split()[-1] for line in settings.splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in battery and low_power and all(value == '0' for value in low_power), 'AC power with low-power mode disabled is required')
    return dict(battery=battery, settings=settings)


def check_bounded(path, plan):
    report = load(path)
    require(report['schema'] == 'bqn-spectral-sum-execution.v1' and report['mode'] == 'bounded'
            and report['status'] == 'PASSED' and report['active'] is None and report['plan'] == ref(PLAN)
            and report['pins'] == pins_from(plan), 'Full runs require the matching bounded report')
    require(len(report['cases']) == len(NS)*len(IDENTITIES)
            and sorted((row['source'], row['n']) for row in report['cases']) == sorted((name, n) for name in IDENTITIES for n in NS), 'Incomplete bounded coverage')
    for row in report['cases']:
        require(row['output_valid'] and row['exit_code'] == 0 and row['timed_out'] is False and row['stderr']['bytes'] == 0,
                'Bounded prerequisite contains a failed execution')
        require(row['source_sha256'] == plan['sources'][row['source']]['sha256'] and row['runtime_sha256'] == RUNTIME_SHA,
                'Bounded source/runtime identity differs')
        raw = load(Path(row['stdout']['path']).with_name('process.json'))
        require(all(row[key] == value for key, value in raw.items()), 'Bounded raw process receipt differs')
        for stream in ['stdout', 'stderr']:
            require(sha(row[stream]['path']) == row[stream]['sha256'] and Path(row[stream]['path']).stat().st_size == row[stream]['bytes'], 'Bounded stream changed')
        expected = next(case['expected'] for case in plan['bounded_cases'] if case['n'] == row['n'])
        require(row['stdout']['sha256'] == expected['sha256'] and row['stdout']['bytes'] == expected['bytes'], 'Bounded reference differs')
        require(row['command'] == [str(RUNTIME), str(ROOT/plan['sources'][row['source']]['path']), str(row['n'])], 'Bounded command differs')
    return ref(path)


def execute(args, plan):
    require(args.output is not None, 'Execution needs --output')
    output = args.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(), 'Use a new output directory inside this experiment')
    require(args.timeout > 0, 'Timeout must be positive')
    # Import the retained helper without invoking its command-line entry point.
    spec = importlib.util.spec_from_file_location('spectral_saved_process', HELPER)
    process = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = process
    spec.loader.exec_module(process)
    pins = pins_from(plan)
    prerequisite = check_bounded(args.bounded_report.resolve(), plan) if args.mode == 'full' else None
    with open(plan['common_mutex'], 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_pins(pins)
        output.mkdir(parents=True)
        snapshot = output/'sources'; snapshot.mkdir()
        for name, source in plan['sources'].items():
            shutil.copyfile(ROOT/source['path'], snapshot/(name+'.bqn'))
        support = output/'controllers'; support.mkdir()
        shutil.copyfile(__file__, support/'run_serial.py')
        shutil.copyfile(HELPER, support/'lean_run.py')
        shutil.copyfile(PLAN, output/'plan.json')
        report = dict(schema='bqn-spectral-sum-execution.v1', mode=args.mode, status='RUNNING', started_utc=process.now(),
            plan=ref(PLAN), pins=pins, source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            controller_sha256=sha(__file__), process_controller_sha256=sha(HELPER), runtime_sha256=RUNTIME_SHA,
            common_mutex_inode=os.fstat(lock.fileno()).st_ino, bounded_prerequisite=prerequisite,
            full_workload=args.mode == 'full', chart_admission=False, diagnostic_profile=False,
            timing_boundary=plan['timing_boundary'], required_work=plan['required_work'], cases=[], orders=[], active=None,
            host=dict(cpu=subprocess.check_output(['/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip(),
                os=subprocess.check_output(['/usr/bin/sw_vers'], text=True)))
        rng = random.Random(SEED)
        schedule = [(case['n'], 1, case['case'], case['stdin'], case['expected']) for case in plan['bounded_cases']] if args.mode == 'bounded' else [
            (FULL['n'], sample, 'full-'+str(sample), None, FULL) for sample in range(1, 4)]
        for n, sample, case_name, stdin_ref, expected in schedule:
            order = IDENTITIES.copy(); rng.shuffle(order)
            report['orders'].append(dict(n=n, sample=sample, sources=order))
            for name in order:
                check_pins(pins)
                before = power()
                report['active'] = dict(source=name, n=n, sample=sample, case=case_name)
                atom(output/'report.json', report)
                command = [str(RUNTIME), str(ROOT/plan['sources'][name]['path']), str(n)]
                directory = output/(case_name+'-'+name)
                record = process.one(command, CORPUS/stdin_ref['path'] if stdin_ref else Path('/dev/null'), directory, args.timeout)
                after = power()
                valid = (record['exit_code'] == 0 and not record['timed_out'] and record['stderr']['bytes'] == 0
                    and record['stdout']['bytes'] == expected['bytes'] and record['stdout']['sha256'] == expected['sha256']
                    and math.isfinite(record['elapsed_seconds']) and record['elapsed_seconds'] > 0)
                record.update(source=name, n=n, sample=sample, case=case_name, output_valid=valid,
                    source_sha256=plan['sources'][name]['sha256'], runtime_sha256=RUNTIME_SHA,
                    power_before=before, power_after=after)
                report['cases'].append(record); report['active'] = None
                if not valid:
                    report['status'] = 'FAILED'
                atom(output/'report.json', report)
                print(json.dumps(dict(source=name, n=n, sample=sample, seconds=record['elapsed_seconds'], valid=valid)), flush=True)
                require(valid, 'Native output failed; retain this attempt and do not retry automatically')
                check_pins(pins)
        report.update(status='PASSED', finished_utc=process.now(), pins_unchanged=True)
        if args.mode == 'full':
            samples = {name: [row['elapsed_seconds'] for row in report['cases'] if row['source'] == name] for name in IDENTITIES}
            report['samples'] = samples
            report['medians'] = {name: statistics.median(values) for name, values in samples.items()}
            report['sample_sd_seconds'] = {name: statistics.stdev(values) for name, values in samples.items()}
        atom(output/'report.json', report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Write the pinned plan only; starts no native process')
    parser.add_argument('--mode', choices=['bounded', 'full'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bounded-report', type=Path)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    require(args.prepare != (args.mode is not None), 'Choose --prepare or --mode')
    plan = make_plan()
    if args.prepare:
        require(args.output is None and args.bounded_report is None, 'Preparation takes no execution paths')
        atom(PLAN, plan)
        print(json.dumps(dict(status=plan['status'], plan=ref(PLAN), native_processes_started=0)))
        return
    require(load(PLAN) == plan, 'Plan is absent/stale; review a freshly prepared plan first')
    require((args.bounded_report is not None) == (args.mode == 'full'), 'Full runs alone need --bounded-report')
    execute(args, plan)


if __name__ == '__main__':
    main()
