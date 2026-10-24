"""Recompute the exact two-factor matrix, complete outputs and paired estimates."""
from collections import Counter
import hashlib
import json
import runpy
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STUDY = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True).strip()


plan = read(STUDY / 'plan.json')
versions = {pin['label']: pin['source_commit'] for pin in plan['existing_binary_pins']}
versions['combined'] = plan['source_commit']
assert len(plan['factor_source_blobs']) == 11
for path, expected in plan['factor_source_blobs'].items():
    actual = {}
    for label, commit in versions.items():
        row = git('ls-tree', commit, '--', path)
        actual[label] = row.split()[2] if row else None
    assert actual == expected
    if path.startswith('src/engine/'):
        assert actual['baseline'] == actual['alias'] and actual['scan'] == actual['combined']
    else:
        assert actual['baseline'] == actual['scan'] and actual['alias'] == actual['combined']
predeclared = subprocess.check_output(['git', '-C', str(HERE.parents[2]), 'show',
    'a3c44503bec0b358181808528b93ae672474b3fe:experiments/mech/native-owner-aot-v1/preparation-interactions-v1/plan.json'])
assert hashlib.sha256(predeclared).hexdigest() == sha(STUDY / 'plan.json')
assert plan['independent_batches'] == 2 and plan['observations_per_subject'] == 20
assert plan['excluded_warmups'] == plan['excluded_outliers'] == 0
roots, evidence = [], {}
for batch in (1, 2):
    folder = HERE / f'full-preparation-interactions-v{batch}'
    report = read(folder / 'results.json')
    assert report['status'] == 'all-factorial-outputs-updates-and-source-pins-verified'
    assert report['plan_sha256'] == sha(STUDY / 'plan.json')
    assert report['driver_sha256'] == sha(STUDY / 'measure.py')
    assert report['source'] == report['source_after']
    assert report['source']['commit'] == plan['source_commit'] and not report['source']['status']
    assert len(report['orders']) == 20 and len(report['samples']) == 100
    assert report['selected_bases'] == 125000000 and report['expected_source_table_updates'] == 874999961
    assert report['source_sha256'] == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
    assert report['bytecode_sha256'] == '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
    assert report['policy_sha256'] == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
    assert report['input_sha256'] == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    for start in (0, 10):
        block = report['orders'][start:start + 10]
        for position in range(5):
            assert Counter(row[position] for row in block) == {s: 2 for s in plan['subjects']}
        pairs = Counter((a, b) for row in block for a, b in zip(row, row[1:]))
        assert len(pairs) == 20 and set(pairs.values()) == {2}
    values = {s: [] for s in plan['subjects']}
    for index, row in enumerate(report['samples']):
        order, position = divmod(index, 5)
        subject = report['orders'][order][position]
        assert (row['order'], row['position'], row['subject']) == (order, position, subject)
        path = HERE / row['process']
        assert sha(path) == row['process_sha256']
        process = read(path)
        assert process['quantitative_benchmark'] and process['exit_status'] == 0
        assert process['elapsed_seconds'] == row['seconds']
        assert sha(path.parent / 'stdout.bin') == row['stdout_sha256'] == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        assert sha(Path(process['command'][0])) == report['pins'][subject]['binary_sha256']
        if subject != 'rust':
            policy, native_path = map(Path, process['command'][1:3])
            assert sha(policy) == report['policy_sha256'] and sha(native_path) == row['native_sha256']
            native = read(native_path)
            assert native['native_aot'] and not native['jit'] and native['policy'] == 'secured'
            assert native['shutdown'] == 'completed'
            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 874999961
            assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
            assert native['native_parallel_tasks'] == native['native_parallel_peak_workers'] == 7
            assert native['native_direct_lookup_regions'] == 5
            assert row['native'] == {k: v for k, v in native.items() if k.startswith('native_')}
        else:
            assert row['native'] is None and row['native_sha256'] is None
        values[subject].append(row['seconds'])
    for subject, samples in values.items():
        assert len(samples) == 20 and samples == report['samples_seconds'][subject]
        assert statistics.median(samples) == report['median_seconds'][subject]
        assert statistics.stdev(samples) == report['standard_deviation_seconds'][subject]
        assert statistics.median(samples) / statistics.median(values['rust']) == report['x_rust'][subject]
    roots.append(folder)
    evidence[folder.name] = dict(median_seconds=report['median_seconds'], x_rust=report['x_rust'])
analysis = read(STUDY / 'analysis.json')
assert analysis['analysis_driver_sha256'] == sha(STUDY / 'analyze.py')
assert analysis['plan_sha256'] == sha(STUDY / 'plan.json')
assert analysis['complete_process_observations'] == 200 and not analysis['pooled']
analyze = runpy.run_path(str(STUDY / 'analyze.py'))['analyze']
assert analysis['batches'] == [analyze(HERE / f'full-preparation-interactions-v{i}', plan) for i in (1, 2)]
validation = {}
for name, count in [('lines', 45), ('workers', 26), ('native', 379), ('catalog', 1)]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / f'preparation-interactions-{name}-v1'
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['source_commit'] == plan['source_commit'] and summary['clean_revision_qualified']
    assert summary['all_owned_processes_reaped_and_groups_closed']
    validation[name] = count
    roots.append(folder)
prefix_folder = HERE / plan['combined_receipt']
prefix = read(prefix_folder / 'results.json')
assert prefix['source_commit'] == plan['source_commit'] and prefix['status'] == 'all-outputs-and-update-counts-verified'
assert prefix['candidate_sha256'] == report['pins']['combined']['binary_sha256']
assert prefix['bytecode_sha256'] == report['bytecode_sha256']
assert prefix['object_sha256'] == report['pins']['alias']['object_sha256']
assert sha(prefix_folder / 'measure-stage-driver.py') == prefix['study_driver_sha256']
assert report['pins']['baseline']['object_sha256'] == report['pins']['scan']['object_sha256']
assert report['pins']['baseline']['object_sha256'] != prefix['object_sha256']
roots.extend([prefix_folder, HERE / plan['compiler']])
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes:
            continue
        processes.add(path)
        process = read(path)
        assert process['exit_status'] == 0 and process['reaped'] and process['group_closed']
        assert process['inherited_common_mutex'] and not process['cleanup_errors']
canonical = HERE.parents[2] / 'data/benchmarks.json'
assert sha(canonical) == report['canonical_data_sha256']
assert Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
result = dict(status='preparation-factorial-study-verified', evidence=evidence, validation=validation,
              primary_complete_process_observations=200, canonical_benchmark_samples=0,
              terminal_owned_processes=len(processes), canonical_data_sha256=sha(canonical),
              verifier_sha256=sha(Path(__file__)), plan_sha256=sha(STUDY / 'plan.json'),
              source_commit=plan['source_commit'], scope='Exact predeclared source-factor matrix, both independent balanced cohorts, all complete outputs and physical updates, unchanged source and secured policy, exact-revision validation and deterministic paired bootstrap recomputation. All configurations remain retained; no per-factor speed threshold removes a combination from this analysis.')
(STUDY / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'primary_complete_process_observations', 'terminal_owned_processes']}))
