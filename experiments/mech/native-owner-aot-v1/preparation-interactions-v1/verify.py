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


def same_child(left, right):
    # setsid changes the group after the pre-exec gate; birth and parent do not.
    return all(left[key] == right[key] for key in
               ('pid', 'ppid', 'birth_seconds', 'birth_microseconds'))


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
        assert process['maximum_rss_bytes'] == row['maximum_rss_bytes']
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
profile_build = HERE / 'profile-preparation-combined-build-v1'
build = read(profile_build / 'results.json')
assert build['source_commit'] == plan['source_commit'] and build['whole_machine_code_matches_timed']
assert build['candidate_object_sha256'] == prefix['object_sha256']
for index in (1, 2, 3):
    folder = HERE / f'full-profile-preparation-combined-v{index}'
    capture = read(folder / 'analysis.json')
    assert capture['source_commit'] == plan['source_commit']
    assert capture['machine_code_identical'] and capture['completed_output_verified']
    assert capture['timed_binary_sha256'] == prefix['candidate_sha256']
    audit = read(HERE / f'preparation-combined-codegen-audit-v{index}/results.json')
    assert audit['whole_machine_code_matches_timed'] and audit['source_commit'] == plan['source_commit']
    roots.append(folder)
roots.append(profile_build)
hardware_folder = HERE / 'preparation-interactions-hardware-v1'
hardware = read(hardware_folder / 'results.json')
assert hardware['status'] == 'all-five-subject-counter-outputs-and-updates-verified'
assert hardware['driver_sha256'] == sha(STUDY / 'hardware.py')
assert hardware['source']['commit'] == plan['source_commit'] and not hardware['source']['status']
assert hardware['benchmark_samples'] == 0 and len(hardware['observations']) == 15
import re
for row in hardware['observations']:
    folder = hardware_folder / f"{row['order']}-{row['subject']}"
    assert sha(folder / 'process.json') == row['process_sha256']
    assert sha(folder / 'stderr.bin') == row['stderr_sha256']
    assert sha(folder / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    assert not read(folder / 'process.json')['quantitative_benchmark']
    raw = (folder / 'stderr.bin').read_text()
    for key, label in [('instructions', 'instructions retired'), ('cycles', 'cycles elapsed'),
                       ('involuntary_context_switches', 'involuntary context switches')]:
        matches = re.findall(r'^\s*(\d+)\s+' + re.escape(label) + r'\s*$', raw, re.M)
        assert len(matches) == 1 and int(matches[0]) == row[key]
    if row['subject'] != 'rust':
        native = read(hardware_folder / f"{row['order']}-{row['subject']}.native.json")
        assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 874999961
        assert native['native_parallel_tasks'] == native['native_parallel_peak_workers'] == 7
for subject, medians in hardware['medians'].items():
    observations = [row for row in hardware['observations'] if row['subject'] == subject]
    assert len(observations) == 3
    for key, value in medians.items():
        assert statistics.median(row[key] for row in observations) == value
roots.append(hardware_folder)
thread_folder = HERE / 'preparation-combined-thread-lifetimes-v1'
threads = read(thread_folder / 'results.json')
assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified'
assert threads['driver_sha256'] == sha(STUDY / 'thread-driver.py')
assert threads['source']['commit'] == plan['source_commit'] and not threads['source']['status']
assert threads['input_mode'] == 'full' and len(threads['subjects']) == 6
for index, row in enumerate(threads['subjects']):
    folder = thread_folder / f"{index}-{row['subject']}"
    assert sha(folder / 'thread-observations.json') == row['raw_sha256']
    assert sha(folder / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
roots.append(thread_folder)
preparation = read(HERE / 'preparation-combined-checkpoint-v1/preparation.json')
assert preparation['script_sha256'] == sha(STUDY / 'preparation.py')
assert preparation['parser_sha256'] == sha(HERE / 'profile_hotspots.py')
for item in preparation['sources']:
    assert sha(HERE / item['path']) == item['sha256']
for mode, count in [('timeline', 15), ('snapshot', 5)]:
    folder = HERE / f'preparation-interactions-memory-{mode}-v1'
    memory = read(folder / 'results.json')
    assert memory['status'] == 'all-owned-memory-observations-and-outputs-verified'
    assert memory['driver_sha256'] == sha(STUDY / 'memory.py')
    assert memory['mode'] == mode and len(memory['observations']) == count
    assert memory['source'] == memory['source_after'] == report['source']
    assert memory['benchmark_samples'] == 0
    for row in memory['observations']:
        raw_folder = folder / f"{row['order']}-{row['subject']}"
        raw = read(raw_folder / 'memory-observations.json')
        assert sha(raw_folder / 'memory-observations.json') == row['raw_sha256']
        receipt = read(raw_folder / 'process.json')
        assert receipt == row['process'] and not receipt['quantitative_benchmark']
        assert same_child(raw['identity'], receipt['birth_identity'])
        assert raw['identity']['pgid'] == raw['identity']['pid']
        assert sha(Path(receipt['command'][0])) == report['pins'][row['subject']]['binary_sha256']
        assert sha(raw_folder / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        assert len(raw['snapshots']) == row['samples'] >= 2
        assert max(s['resident_bytes'] for s in raw['snapshots']) == row['sampled_peak_rss_bytes']
        assert max(s['lifetime_peak_physical_footprint_bytes'] for s in raw['snapshots']) == row['observed_lifetime_peak_physical_footprint_bytes']
        assert len(raw['captures']) == (2 if mode == 'snapshot' else 0)
        for capture in raw['captures']:
            tool_folder = folder / (raw_folder.name + '-' + capture['tool'])
            assert read(tool_folder / 'process.json') == capture['process']
            assert sha(tool_folder / 'stdout.bin') == capture['stdout_sha256']
            assert sha(tool_folder / 'stderr.bin') == capture['stderr_sha256']
    roots.append(folder)
allocation_folder = HERE / 'preparation-interactions-allocation-callers-v1'
allocation = read(allocation_folder / 'results.json')
assert allocation['status'] == 'all-owned-allocation-diagnostics-and-outputs-verified'
assert allocation['source'] == allocation['source_after'] == report['source']
assert allocation['driver_sha256'] == sha(STUDY / 'allocations.py')
assert allocation['memory_helper_sha256'] == sha(STUDY / 'memory.py')
assert allocation['environment_delta'] == dict(MallocStackLogging='1')
assert allocation['benchmark_samples'] == 0 and len(allocation['observations']) == 2
for row in allocation['observations']:
    folder = allocation_folder / row['subject']
    assert sha(folder / 'allocation-observations.json') == row['raw_sha256']
    raw = read(folder / 'allocation-observations.json')
    assert read(folder / 'process.json') == row['process']
    assert sha(folder / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    assert sha(Path(row['process']['command'][0])) == report['pins'][row['subject']]['binary_sha256']
    assert same_child(raw['identity'], row['process']['birth_identity'])
    assert raw['identity']['pgid'] == raw['identity']['pid']
    assert len(raw['captures']) == 3
    for capture in raw['captures']:
        tool_folder = allocation_folder / (row['subject'] + '-' + capture['tool'])
        assert read(tool_folder / 'process.json') == capture['process']
        assert sha(tool_folder / 'stdout.bin') == capture['stdout_sha256']
        assert sha(tool_folder / 'stderr.bin') == capture['stderr_sha256']
roots.append(allocation_folder)
binary_folder = HERE / 'preparation-interactions-binary-size-v1'
binary = read(binary_folder / 'results.json')
assert binary['status'] == 'exact-binary-file-and-machine-code-sizes-verified'
assert binary['driver_sha256'] == sha(STUDY / 'binary.py')
binary_tools = runpy.run_path(str(STUDY / 'binary.py'))
for subject, item in binary['subjects'].items():
    parsed = binary_tools['macho'](Path(item['path']))[0]
    assert parsed['sha256'] == report['pins'][subject]['binary_sha256']
    for key in parsed:
        assert parsed[key] == item[key]
assert binary_tools['function_ranges'](HERE / '.build/counting-preparation-combined-profile') == binary['combined_function_extents']
assert binary_tools['function_ranges'](Path(binary['subjects']['rust']['path'])) == binary['rust_function_extents']
memory_analysis_path = HERE / 'preparation-interactions-memory-analysis-v1/results.json'
memory_analysis = read(memory_analysis_path)
assert memory_analysis['driver_sha256'] == sha(STUDY / 'memory-analysis.py')
assert memory_analysis['binary_parser_sha256'] == sha(STUDY / 'binary.py')
for item in memory_analysis['sources']:
    assert sha(HERE / item['path']) == item['sha256']
import sys
sys.path.insert(0, str(STUDY))
runpy.run_path(str(STUDY / 'memory-analysis.py'))['main']()
assert read(memory_analysis_path) == memory_analysis
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
