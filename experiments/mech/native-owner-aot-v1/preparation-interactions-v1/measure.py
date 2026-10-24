"""Measure all four optimization combinations and Rust in predeclared orders."""
import fcntl
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STUDY = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
INPUT_SHA = '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'


def read(path):
    return json.loads(path.read_text())


def source_state():
    def git(*args):
        return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True).strip()
    return dict(commit=git('rev-parse', 'HEAD'), tree=git('rev-parse', 'HEAD^{tree}'),
                status=git('status', '--porcelain'))


def check_native(path):
    native = read(path)
    assert native['native_aot'] and not native['jit']
    assert native['policy'] == 'secured' and native['shutdown'] == 'completed'
    for key in ['native_hash_table_regions', 'native_packed_map_regions',
                'native_packed_ssa_regions', 'native_parallel_tasks',
                'native_parallel_peak_workers', 'native_guarded_loop_regions',
                'native_guarded_call_regions']:
        assert native[key] == 7, (key, native[key])
    assert native['native_parallel_batches'] == 1 and native['native_parallel_regions'] == 2
    assert native['native_frozen_map_regions'] == native['native_direct_lookup_regions'] == 5
    assert native['native_frozen_map_reads'] == 10
    assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 874999961
    return {k: v for k, v in native.items() if k.startswith('native_')}


def main():
    assert len(sys.argv) == 3 and sys.argv[2] in ('1', '2')
    batch = int(sys.argv[2])
    plan_path = STUDY / 'plan.json'
    plan = read(plan_path)
    subjects = plan['subjects']
    assert subjects == ['baseline', 'scan', 'alias', 'combined', 'rust']
    orders = plan['orders']
    if batch == 2:
        # A second deterministic shuffle uses the same balanced ten-order
        # design; no timings select its ordering or membership.
        import random
        rng = random.Random(plan['seed'] + 1)
        orders = [row.copy() for row in orders]
        for start in (0, 10):
            block = orders[start:start + 10]
            rng.shuffle(block)
            orders[start:start + 10] = block
    assert len(orders) == 20
    from collections import Counter
    for start in (0, 10):
        block = orders[start:start + 10]
        assert all(sorted(row) == sorted(subjects) for row in block)
        assert all(Counter(row[pos] for row in block) == {s: 2 for s in subjects}
                   for pos in range(5))
        adjacent = Counter((a, b) for row in block for a, b in zip(row, row[1:]))
        assert len(adjacent) == 20 and set(adjacent.values()) == {2}
    targets, pins = {}, {}
    for pin in plan['existing_binary_pins']:
        timing_path = HERE / pin['receipt'] / 'results.json'
        assert process.sha(timing_path) == pin['receipt_sha256']
        timing = read(timing_path)
        assert timing['source_commit'] == pin['source_commit']
        assert timing['candidate_sha256'] == pin['binary_sha256']
        targets[pin['label']] = HERE / '.build' / pin['binary']
        pins[pin['label']] = dict(pin, object_sha256=timing['object_sha256'])
    timing_path = HERE / plan['combined_receipt'] / 'results.json'
    timing = read(timing_path)
    assert timing['status'] == 'all-outputs-and-update-counts-verified'
    assert timing['source_commit'] == plan['source_commit']
    assert timing['source_sha256'] == SOURCE_SHA and timing['bytecode_sha256'] == BYTECODE_SHA
    targets['combined'] = HERE / '.build' / plan['combined_binary']
    pins['combined'] = dict(receipt=plan['combined_receipt'], receipt_sha256=process.sha(timing_path),
                            source_commit=plan['source_commit'], binary=plan['combined_binary'],
                            binary_sha256=timing['candidate_sha256'], object_sha256=timing['object_sha256'])
    targets['rust'] = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
    pins['rust'] = dict(binary_sha256='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763')
    for subject in subjects:
        assert process.sha(targets[subject]) == pins[subject]['binary_sha256']
    assert pins['baseline']['object_sha256'] == pins['scan']['object_sha256']
    assert pins['alias']['object_sha256'] == pins['combined']['object_sha256']
    assert pins['baseline']['object_sha256'] != pins['alias']['object_sha256']
    assert process.sha(HERE / 'knucleotide-source-map.mec') == SOURCE_SHA
    canonical = HERE.parents[2] / 'data/benchmarks.json'
    assert process.sha(canonical) == DATA_SHA
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    policy = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == INPUT_SHA and process.sha(policy) == POLICY_SHA
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    compiler = read(HERE / plan['compiler'] / 'results.json')
    assert compiler['source_commit'] == before['commit']
    out = HERE / sys.argv[1]
    out.mkdir(exist_ok=False)
    report = dict(status='running', source=before, batch=batch, plan_sha256=process.sha(plan_path),
                  driver_sha256=process.sha(Path(__file__)), orders=orders, pins=pins,
                  input_sha256=INPUT_SHA, policy_sha256=POLICY_SHA, source_sha256=SOURCE_SHA,
                  bytecode_sha256=BYTECODE_SHA, canonical_data_sha256=DATA_SHA,
                  selected_bases=125000000, expected_source_table_updates=874999961,
                  excluded_warmups=0, excluded_outliers=0, samples=[],
                  scope='Twenty balanced orders of five serial complete-process executions; four fixed compiler/runtime configurations plus exact upstream Rust. Includes startup and secured shutdown. No observations excluded or pooled with earlier experiments.')
    process.save(out / 'results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, order in enumerate(orders):
            for position, subject in enumerate(order):
                assert process.sha(targets[subject]) == pins[subject]['binary_sha256']
                folder = out / f'{index:02d}-{position}-{subject}'
                native_path = out / (folder.name + '.native.json')
                command = [str(targets[subject])]
                if subject != 'rust':
                    command += [str(policy), str(native_path), '--']
                receipt = process.execute(command, folder, compiler['environment'], lock,
                                          stdin=inp, deadline=30, quantitative=True)
                assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                native = check_native(native_path) if subject != 'rust' else None
                report['samples'].append(dict(order=index, position=position, subject=subject,
                    seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                    process=str((folder / 'process.json').relative_to(HERE)),
                    process_sha256=process.sha(folder / 'process.json'),
                    stdout_sha256=OUTPUT_SHA, native=native,
                    native_sha256=process.sha(native_path) if native else None))
                process.save(out / 'results.json', report)
            print('order', index + 1, 'of', len(orders), 'verified', flush=True)
    assert source_state() == before and process.sha(canonical) == DATA_SHA
    values = {s: [r['seconds'] for r in report['samples'] if r['subject'] == s] for s in subjects}
    assert all(len(v) == 20 for v in values.values())
    report['samples_seconds'] = values
    report['median_seconds'] = {s: statistics.median(v) for s, v in values.items()}
    report['x_rust'] = {s: report['median_seconds'][s] / report['median_seconds']['rust'] for s in subjects}
    report['standard_deviation_seconds'] = {s: statistics.stdev(v) for s, v in values.items()}
    report['status'] = 'all-factorial-outputs-updates-and-source-pins-verified'
    process.save(out / 'results.json', report)
    print(json.dumps(dict(median_seconds=report['median_seconds'], x_rust=report['x_rust'])), flush=True)


if __name__ == '__main__':
    main()
