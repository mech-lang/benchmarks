"""Compare copy-phase CPU in independent hosts using identical diagnostics."""
import fcntl
import importlib.util
from pathlib import Path
import statistics
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
PHASE = HERE / 'preparation-phase-v1'
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA, DATA_SHA
spec = importlib.util.spec_from_file_location('phase_parse', PHASE / 'parse.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
plan = read(STUDY / 'phase-plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
builds = {s: read(PHASE / path / 'results.json') for s, path in plan['subjects'].items()}
assert builds['candidate']['source_before'] == builds['candidate']['source_after'] == before
assert builds['parent']['probe_sha256'] == builds['candidate']['probe_sha256'] == process.sha(PHASE / 'phase_probe.rs')
assert builds['parent']['guest_object_sha256'] == builds['candidate']['guest_object_sha256']
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
policy = HERE / 'full-disjoint-state-v1/launch.json'
data = HERE.parents[2] / 'data/benchmarks.json'
assert process.sha(inp) == INPUT_SHA and process.sha(policy) == POLICY_SHA and process.sha(data) == DATA_SHA
out = STUDY / 'phase-comparison-v1'
out.mkdir(exist_ok=False)
report = dict(status='running', source_before=before, production_source=plan['production_source'],
    plan_sha256=process.sha(STUDY / 'phase-plan.json'), driver_sha256=process.sha(Path(__file__)),
    parser_sha256=process.sha(PHASE / 'parse.py'), probe_sha256=process.sha(PHASE / 'phase_probe.rs'),
    input_sha256=INPUT_SHA, policy_sha256=POLICY_SHA, primary_benchmark_samples=0,
    excluded_warmups=0, excluded_outliers=0, samples=[])
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino == plan['lock_inode']
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    build = builds['candidate']
    binary = Path(build['binary'])
    assert process.sha(binary) == build['binary_sha256']
    prefix = HERE / 'rust-span-diagnostic-v2/input.fasta'
    prefix_policy = HERE / 'full-timing-v1/launch.json'
    assert process.sha(prefix) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
    smoke = out / 'prefix-qualification'
    native = out / 'prefix-qualification.native.json'
    r = process.execute([str(binary), str(prefix_policy), str(native), '--'], smoke,
        build['environment'], lock, stdin=prefix, deadline=30, quantitative=False)
    assert r['exit_status'] == 0 and process.sha(smoke / 'stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
    n = read(native)
    assert n['native_hash_table_updates'] == n['native_packed_map_updates'] == 6999961
    assert n['native_parallel_tasks'] == 7 and n['policy'] == 'secured' and n['shutdown'] == 'completed'
    process.save(smoke / 'phases.json', parser.parse(smoke / 'stderr.bin'))
    for index, order in enumerate(plan['orders']):
        for position, subject in enumerate(order):
            build = builds[subject]
            binary = Path(build['binary'])
            assert process.sha(binary) == build['binary_sha256']
            folder = out / f'{index:02d}-{position}-{subject}'
            native = out / (folder.name + '.native.json')
            r = process.execute([str(binary), str(policy), str(native), '--'], folder,
                builds['candidate']['environment'], lock, stdin=inp, deadline=30, quantitative=False)
            assert r['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
            checked = check_native(native)
            records = parser.parse(folder / 'stderr.bin')
            process.save(folder / 'phases.json', records)
            report['samples'].append(dict(order=index, position=position, subject=subject,
                binary_sha256=build['binary_sha256'], process_sha256=process.sha(folder / 'process.json'),
                native_sha256=process.sha(native), native=checked, stdout_sha256=OUTPUT_SHA, records=records))
            process.save(out / 'results.json', report)
        print('Phase comparison order', index + 1, 'of', len(plan['orders']), 'verified', flush=True)
assert source_state() == before and process.sha(data) == DATA_SHA
values = {s: [r['records'] for r in report['samples'] if r['subject'] == s] for s in builds}
assert all(len(v) == 6 for v in values.values())
report['median_phase_cpu_seconds'] = {
    s: {p: statistics.median(r['phases'][p]['cpu_ns'] / 1e9 for r in rows) for p in rows[0]['phases']}
    for s, rows in values.items()
}
report['median_milestone_cpu_seconds'] = {
    s: {m['name']: statistics.median(next(n['cpu_ns'] for n in r['marks'] if n['name'] == m['name']) / 1e9 for r in rows)
        for m in rows[0]['marks']}
    for s, rows in values.items()
}
report.update(status='copy-phase-outputs-original-updates-and-boundaries-verified', source_after=source_state())
process.save(out / 'results.json', report)
print('CPU seconds:', report['median_phase_cpu_seconds'], flush=True)
print('Launch milestones:', {s: m['spawn_begin'] for s, m in report['median_milestone_cpu_seconds'].items()}, flush=True)
