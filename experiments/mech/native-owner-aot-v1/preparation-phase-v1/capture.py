"""Collect balanced diagnostic captures, separate from all primary timing data."""
import fcntl
import importlib.util
from pathlib import Path
import statistics
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA, DATA_SHA
from parse import parse

worker_spec = importlib.util.spec_from_file_location('worker_parse', HERE / 'worker-completion-v1/parse.py')
worker_parse = importlib.util.module_from_spec(worker_spec)
worker_spec.loader.exec_module(worker_parse)
plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
assert read(STUDY / 'smoke-v1/qualification.json')['status'] == 'prefix-output-rows-phases-and-original-updates-verified'
builds = {
    'mech': read(STUDY / 'build-offsets-v2/results.json'),
    'rust': read(HERE / 'worker-completion-v1/build-rust-v1/results.json'),
}
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
policy = HERE / 'full-disjoint-state-v1/launch.json'
data = HERE.parents[2] / 'data/benchmarks.json'
assert process.sha(inp) == INPUT_SHA and process.sha(policy) == POLICY_SHA and process.sha(data) == DATA_SHA
out = STUDY / 'full-capture-v1'
out.mkdir(exist_ok=False)
report = dict(status='running', source_before=before, plan_sha256=process.sha(STUDY / 'plan.json'),
    driver_sha256=process.sha(Path(__file__)), parser_sha256=process.sha(STUDY / 'parse.py'),
    worker_parser_sha256=process.sha(HERE / 'worker-completion-v1/parse.py'),
    input_sha256=INPUT_SHA, policy_sha256=POLICY_SHA, canonical_data_sha256=DATA_SHA,
    primary_benchmark_samples=0, excluded_warmups=0, excluded_outliers=0, samples=[])
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino == plan['lock_inode']
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index, order in enumerate(plan['orders']):
        for position, subject in enumerate(order):
            build = builds[subject]
            binary = Path(build['binary'])
            assert process.sha(binary) == build['binary_sha256']
            folder = out / f'{index:02d}-{position}-{subject}'
            native = out / (folder.name + '.native.json')
            command = [str(binary)] + ([str(policy), str(native), '--'] if subject == 'mech' else [])
            receipt = process.execute(command, folder, builds['mech']['environment'], lock,
                stdin=inp, deadline=30, quantitative=True)
            assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
            checked = check_native(native) if subject == 'mech' else None
            records = parse(folder / 'stderr.bin') if subject == 'mech' else worker_parse.parse(folder / 'stderr.bin', 'rust')
            process.save(folder / 'phases.json', records)
            report['samples'].append(dict(order=index, position=position, subject=subject,
                diagnostic_seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                binary_sha256=build['binary_sha256'], process_sha256=process.sha(folder / 'process.json'),
                stdout_sha256=OUTPUT_SHA, native=checked, records=records))
            process.save(out / 'results.json', report)
        print('Diagnostic order', index + 1, 'of', len(plan['orders']), 'verified', flush=True)
assert source_state() == before and process.sha(data) == DATA_SHA
mech = [s['records'] for s in report['samples'] if s['subject'] == 'mech']
rust = [s['records'] for s in report['samples'] if s['subject'] == 'rust']
assert len(mech) == len(rust) == 6
report['median_phase_cpu_seconds'] = {
    k: statistics.median(r['phases'][k]['cpu_ns'] / 1e9 for r in mech) for k in mech[0]['phases']
}
report['median_mark_cpu_seconds'] = {
    m['name']: statistics.median(next(n['cpu_ns'] for n in r['marks'] if n['name'] == m['name']) / 1e9 for r in mech)
    for m in mech[0]['marks']
}
def rust_delta(records):
    rows = records['main']
    return (next(r['cpu_ns'] for r in rows if r['label'] == 'input_ready') - rows[0]['cpu_ns']) / 1e9
report['rust_input_ready_cpu_seconds'] = [rust_delta(r) for r in rust]
report['rust_median_input_ready_cpu_seconds'] = statistics.median(report['rust_input_ready_cpu_seconds'])
report.update(status='all-diagnostic-outputs-updates-and-phase-boundaries-verified', source_after=source_state())
process.save(out / 'results.json', report)
print(report['median_phase_cpu_seconds'], flush=True)
print('Rust input-ready CPU seconds:', report['rust_median_input_ready_cpu_seconds'], flush=True)
