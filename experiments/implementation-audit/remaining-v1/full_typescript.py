#!/usr/bin/env python3
"""Preselected full-process TypeScript comparison; canonical admission remains separate."""
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
    previous_path = HERE/'pilot-v1/plan.json'
    previous = json.loads(previous_path.read_bytes())
    pilot_path = HERE/'pilot-v1/run-v1/report.json'
    pilot = json.loads(pilot_path.read_bytes())
    assert pilot['status'] == 'passed-reduced-input-pilots' and pilot['pins_unchanged']
    native_path = HERE/'native-v1/report.json'
    native = json.loads(native_path.read_bytes())
    assert native['status'] == 'passed-bounded-output-checks' and native['pins_unchanged']
    selected = ['ts-parent','ts-rolling']
    commands = {label:previous['commands'][label] for label in selected}
    directory = HERE/'typescript-full-v1'
    directory.mkdir(exist_ok=False)
    inp = ROOT/'experiments/lean4/.build/inputs/n25000000.fasta'
    expected = ROOT/'archive/workloads/knucleotide/inputs/knucleotide-output-25000000.txt'
    assert sha(inp) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    catalog_path = ROOT/'data/benchmarks.json'
    catalog = json.loads(catalog_path.read_bytes())
    key = 'knucleotide:mech-compact-final-std1-simd0-p4'
    baseline = catalog['programs'][key]
    assert baseline['language'] == 'mech' and baseline['execution_mode'] == 'aot'
    assert baseline['measurement_status'] == 'measured' and statistics.median(baseline['samples']) == baseline['seconds']
    assert baseline['seconds'] == min(r['seconds'] for r in catalog['programs'].values()
        if r['benchmark'] == 'knucleotide' and r['language'] == 'mech' and r.get('measurement_status') == 'measured')
    old_path = ROOT/catalog['archive_paths'][baseline['report']]
    old = json.loads(old_path.read_bytes())
    retained = old['programs']['knucleotide:mech-control']
    assert old['workloads']['knucleotide'][1] == 25000000 and retained['samples_seconds'] == baseline['samples']
    assert retained['full_validation']['sha256'] == sha(expected)
    baseline_record = dict(profile=key, seconds=baseline['seconds'], samples_seconds=baseline['samples'],
        original_report=str(old_path.relative_to(ROOT)), original_report_sha256=sha(old_path),
        original_selector='/programs/knucleotide:mech-control', workload_size=25000000,
        source_sha256=baseline['files'], binary_sha256=baseline['binary_sha256'],
        comparison_scope='Retained historical Mech AOT denominator on the same canonical full-size workload; not a fresh cohort member.')
    pins = dict(previous['pins'])
    for path in [Path(__file__), previous_path, pilot_path, native_path, inp, expected, catalog_path, old_path]:
        pins[str(path)] = sha(path)
    capture_path = ROOT/'experiments/elixir/rolling-v1/qualification-v1/native_process.py'
    capture = load('untimed_library_capture',capture_path)
    pins[str(capture_path)] = sha(capture_path)
    runtime = directory/'runtime-discovery'
    runtime.mkdir()
    system_names, inspected = set(), set()
    pending = [Path(command[0]) for command in commands.values()]
    env = {'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','TZ':'UTC'}
    with LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        inode = os.fstat(lock.fileno()).st_ino
        assert inode == LOCK.stat().st_ino == previous['common_mutex_inode']
        while pending:
            binary = pending.pop()
            if str(binary) in inspected: continue
            inspected.add(str(binary)); assert len(inspected) <= 64
            name = 'image-'+str(len(inspected))
            result = capture.one(['/usr/bin/otool','-L',str(binary)],runtime/name,env,runtime,lock.fileno(),timeout=30)
            capture.success(result); assert not (runtime/name/'stderr.bin').read_bytes()
            pins[str(binary)] = sha(binary)
            for line in (runtime/name/'stdout.bin').read_text().splitlines()[1:]:
                install = line.strip().split(' (',1)[0]
                if not install.startswith('/'): raise ValueError('Unresolved install name: '+install)
                path = Path(install)
                if path.is_file():
                    path = path.resolve(); pins[str(path)] = sha(path); pending.append(path)
                else:
                    assert install.startswith(('/usr/lib/','/System/Library/'))
                    system_names.add(install)
        result = capture.one(['/usr/bin/sw_vers'],runtime/'os-build',env,runtime,lock.fileno(),timeout=30)
        capture.success(result)
        assert inode == LOCK.stat().st_ino == os.fstat(lock.fileno()).st_ino
    for path in runtime.rglob('*'):
        if path.is_file(): pins[str(path)] = sha(path)
    rng = random.Random(710291)
    order = []
    for round_number in range(3):
        labels = list(selected); rng.shuffle(labels)
        order.extend({'language':'typescript','round':round_number+1,'label':label} for label in labels)
    case = {'language':'typescript','labels':selected,'input':str(inp),'expected':str(expected),
            'limit':'Complete canonical N25m FASTA; parse input, count every overlapping occurrence in all seven full maps, sort frequency tables, all output.'}
    plan = {'schema':'typescript-rolling-full-process-comparison.v1','status':'prepared','full_mode_available':True,
            'chart_admission':False,'pins':pins,'cases':[case],'commands':commands,'order':order,
            'common_mutex_inode':LOCK.stat().st_ino,'input_bytes':inp.stat().st_size,'workload_size':25000000,
            'selection':'Retained parent and the one rolling candidate whose bounded full outputs passed and 1m pilot improved. No variants selected after full timing.',
            'sample_scope':'Three shuffled sequential fresh-process observations per source; startup, V8 JIT, input, all work, complete output and shutdown included. Preparation/hashing excluded.',
            'system_runtime_install_names':sorted(system_names),'mech_aot_baseline':baseline_record,
            'known_remaining_gates':'Independent source/count/work review and guarded canonical admission. No source is claimed globally optimal.'}
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
    plan_path = HERE/'typescript-full-v1/plan.json'
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert all(sha(Path(path)) == expected for path, expected in plan['pins'].items())
    process = load('quantitative_pilot_process', PROCESS)
    output = HERE/'typescript-full-v1/run-v1'
    output.mkdir(exist_ok=False)
    report = {'schema': plan['schema'], 'status': 'running', 'plan_sha256': sha(plan_path),
              'full_size_results': True, 'chart_admission': False, 'observations': [], 'mech_aot_baseline': plan['mech_aot_baseline']}
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
                assert sha(output/directory/'stdout.bin') == sha(Path(case['expected'])), 'Full complete output differs'
                report['observations'].append(dict(job, seconds=result['elapsed_seconds'],
                                                  maximum_rss_bytes=result['maximum_rss_bytes'], directory=directory,
                                                  x_mech_aot=result['elapsed_seconds']/plan['mech_aot_baseline']['seconds']))
                print(json.dumps({'completed': index + 1, 'total': len(plan['order']),
                                  'label': job['label'], 'seconds': result['elapsed_seconds'],
                                  'x_mech_aot': result['elapsed_seconds']/plan['mech_aot_baseline']['seconds']}), flush=True)
            summary = {}
            for label in plan['commands']:
                observations = [r for r in report['observations'] if r['label'] == label]
                values = [r['seconds'] for r in observations]
                summary[label] = {'samples': values, 'median_seconds': statistics.median(values),
                                  'stdev_seconds': statistics.stdev(values),
                                  'peak_rss_bytes': max(r['maximum_rss_bytes'] for r in observations),
                                  'samples_x_mech_aot': [v/plan['mech_aot_baseline']['seconds'] for v in values],
                                  'median_x_mech_aot': statistics.median(values)/plan['mech_aot_baseline']['seconds']}
            report.update(status='passed-full-process-comparison', summary=summary)
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
