"""Verify the bounded lookup-cache trial, exact-code profiles and production-equivalent validation."""
import ast
import copy
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
OUT = HERE / 'direct-lookup-cache-checkpoint-v1'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
TRIALS = [('direct-lookup-cache', 'c7cda2018917a75bd014c07ee2777305d88832e7', 61)]
VALIDATED = '49bdf267dfdab441c69007b4f04b4088be0a0337'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
assert sha(HERE / 'knucleotide-source-map.mec') == SOURCE_SHA
assert Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
roots, evidence, negative = [], {}, 0
for name, commit, compiler in TRIALS:
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', commit], text=True).strip() == commit
    timing_folder = HERE / (name + '-timing-v1')
    timing = read(timing_folder / 'results.json')
    assert timing['status'] == 'all-outputs-and-update-counts-verified'
    assert timing['source_commit'] == commit
    assert timing['source_sha256'] == SOURCE_SHA and timing['bytecode_sha256'] == BYTECODE_SHA
    assert sha(timing_folder / 'measure-stage-driver.py') == timing['study_driver_sha256']
    assert sha(HERE / '.build' / ('counting-' + name)) == timing['candidate_sha256']
    descriptor = read(HERE / '.build' / ('counting-' + name + '.project/native-descriptor.json'))['descriptor']
    tree = ast.parse((timing_folder / 'measure-stage-driver.py').read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'require_steady_loops')
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), name, 'exec'), namespace)
    qualify = namespace['require_steady_loops']
    args = dict(descriptor=descriptor, loops=timing['compiled_outlined_loops'],
                guarded=timing['compiled_guarded_loops'], invariants=timing['compiled_loop_invariants'],
                lookups=timing['compiled_lookup_facts'], pre_data_passes=1,
                specialize_widths=True, fuel_edge_checks=True, productive_entry=True,
                separate_header_snapshots=True, peeled_entry_probes=True,
                prepaid_extent=True, caller_prepaid_extent=True, affine_cursor=True,
                cold_recipes=True)
    args['cold_frame_reloads'] = True
    records = timing['compiled_steady_loops']
    assert qualify(records, **args) == timing['qualified_steady_regions']
    mutations = [
        lambda r: r[0].update(cold_snapshot_recipes=[]),
        lambda r: r[0]['cold_snapshot_recipes'].append(copy.deepcopy(r[0]['cold_snapshot_recipes'][0])),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(node=-1),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(header=1),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(incoming=1),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(updates=True),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(previous=True),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(words=[[-1, 0]]),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(words=[[r[0]['cold_snapshot_recipes'][0]['words'][0][0], -1]]),
        lambda r: r[0]['cold_snapshot_recipes'][0].update(words=[[r[0]['cold_snapshot_recipes'][0]['words'][0][0], True]]),
    ]
    if name == 'direct-lookup-cache':
        mutations += [lambda r: r[0]['cold_snapshot_recipes'][0].update(reload_words=[9, 12])]
    for mutate in mutations:
        bad = copy.deepcopy(records)
        mutate(bad)
        try:
            qualify(bad, **args)
        except (AssertionError, KeyError):
            negative += 1
        else:
            raise AssertionError('Malformed cold snapshot accepted')
    cohort = read(HERE / ('full-' + name + '-cohort-v1/results.json'))
    assert cohort['status'] == 'all-cohorts-and-outputs-verified'
    assert cohort['source_commit'] == commit and cohort['launch_sha256'] == POLICY_SHA
    assert cohort['selected_bases'] == 125000000 and cohort['expected_table_updates'] == 874999961
    values = {subject: [] for subject in ['rust', 'mech', 'baseline']}
    for index in range(1, 7):
        folder = HERE / f'full-{name}-v{index}'
        raw = read(folder / 'results.json')
        assert raw['status'] == 'full-output-and-update-counts-verified'
        assert raw['candidate_sha256'] == timing['candidate_sha256']
        assert raw['source_sha256'] == SOURCE_SHA and raw['bytecode_sha256'] == BYTECODE_SHA
        assert sha(folder / 'launch.json') == raw['launch_sha256'] == POLICY_SHA
        for subject in values:
            process = read(folder / subject / 'process.json')
            assert process['quantitative_benchmark'] and process['exit_status'] == 0
            assert sha(folder / subject / 'stdout.bin') == OUTPUT_SHA
            values[subject].append(process['elapsed_seconds'])
        for filename in ['native.report.json', 'baseline.native.report.json']:
            native = read(folder / filename)
            assert native['native_aot'] and not native['jit'] and native['policy'] == 'secured'
            assert native['shutdown'] == 'completed'
            assert native['native_parallel_tasks'] == native['native_parallel_peak_workers'] == 7
            assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 874999961
            if filename == 'native.report.json': assert native['native_direct_lookup_regions'] == 5
        roots.append(folder)
    for subject, samples in values.items():
        assert samples == cohort['samples_seconds'][subject]
        assert statistics.median(samples) == cohort['median_seconds'][subject]
        assert statistics.median(samples) / statistics.median(values['rust']) == cohort['x_rust'][subject]
    build_folder = HERE / ('profile-' + name + '-build-v1')
    build = read(build_folder / 'results.json')
    assert build['source_commit'] == commit and build['whole_machine_code_matches_timed']
    for index in range(1, 4):
        folder = HERE / f'full-profile-{name}-v{index}'
        analysis = read(folder / 'analysis.json')
        assert analysis['source_commit'] == commit and analysis['machine_code_identical']
        assert analysis['completed_output_verified'] and analysis['timed_binary_sha256'] == timing['candidate_sha256']
        audit = read(HERE / f'{name}-codegen-audit-v{index}/results.json')
        assert audit['source_commit'] == commit and audit['whole_machine_code_matches_timed']
        roots.append(folder)
    paths = read(HERE / f'{name}-codegen-audit-v1/steady-paths-cache-on.json')
    assert paths['source_commit'] == commit and len(paths['paths']) == 38
    assert paths['script_sha256'] == sha(HERE / 'audit_lookup_cache_paths.py')
    hardware = read(HERE / (name + '-hardware-v1/results.json'))
    assert hardware['status'] == 'all-complete-outputs-updates-and-hardware-counters-verified'
    assert hardware['source_commit'] == commit and len(hardware['observations']) == 9
    profile_folder = HERE / (name + '-remaining-profile-v1')
    profile = read(profile_folder / 'results.json')
    assert profile['script_sha256'] == sha(profile_folder / 'profile-hotspots-driver.py')
    assert sum(profile['aggregates']['mech']['exclusive_buckets'].values()) == profile['aggregates']['mech']['worker_observations']
    evidence[name] = dict(source_commit=commit, median_seconds=cohort['median_seconds'],
                          x_rust=cohort['x_rust'], faster_pairs=sum(a < b for a, b in zip(values['mech'], values['baseline'])),
                          hardware_medians=hardware['medians'], profile=profile['aggregates']['mech'],
                          instruction_range=[min(p['instructions'] for p in paths['paths']), max(p['instructions'] for p in paths['paths'])])
    roots.extend([timing_folder, build_folder, HERE / (name + '-hardware-v1'), HERE / ('compiler-v' + str(compiler))])

validation = {}
for label, count, commit in [
    ('direct-lookup-cache-focused-v2', 5, TRIALS[0][1]),
    ('direct-lookup-cache-steady-v1', 6, TRIALS[0][1]),
    ('direct-lookup-cache-growth-v1', 1, VALIDATED),
    ('direct-lookup-cache-native-v2', 374, VALIDATED),
    ('direct-lookup-cache-catalog-v1', 1, VALIDATED),
]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / label
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['source_commit'] == commit and summary['clean_revision_qualified']
    assert summary['all_owned_processes_reaped_and_groups_closed']
    validation[label] = count
    roots.append(folder)
changed = subprocess.check_output(['git', '-C', str(SOURCE), 'diff', '--name-only', TRIALS[0][1], VALIDATED], text=True).splitlines()
assert changed == ['hosts/gpu/src/native_artifact/program_packed_narrow_tests.rs']
for label, commit in [('direct-lookup-cache-focused-v1', '172bbbb02ef3fcc5c5931135736f810ccf1f0137'), ('direct-lookup-cache-native-v1', TRIALS[0][1])]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / label
    summary = read(folder / 'summary.json')
    assert summary['status'] != 'passed' and summary['source_commit'] == commit
    assert summary['clean_revision_qualified'] and summary['all_owned_processes_reaped_and_groups_closed']
    roots.append(folder)
thread_folder = HERE / 'direct-lookup-cache-thread-lifetimes-v6'
threads = read(thread_folder / 'results.json')
assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified'
assert threads['source'] == dict(commit=VALIDATED, status='')
assert threads['driver_sha256'] == sha(thread_folder / 'thread-driver.py')
assert threads['policy_sha256'] == POLICY_SHA and threads['benchmark_samples'] == 0
assert [row['subject'] for row in threads['subjects']] == ['baseline', 'mech', 'rust', 'rust', 'mech', 'baseline']
for index, row in enumerate(threads['subjects']):
    folder = thread_folder / f'{index}-{row["subject"]}'
    receipt = read(folder / 'process.json')
    assert receipt == row['process'] and not receipt['quantitative_benchmark']
    assert sha(folder / 'stdout.bin') == OUTPUT_SHA
    assert sha(folder / 'thread-observations.json') == row['raw_sha256']
    raw = read(folder / 'thread-observations.json')
    assert raw['threads'] == row['threads'] and len(raw['snapshots']) >= 2
    cpu = sum((r['user_ns'] + r['system_ns']) / 1e9 for r in row['threads'])
    assert cpu == row['observed_cpu_seconds_lower_bound']
    assert cpu <= (receipt['user_cpu_seconds'] + receipt['system_cpu_seconds']) * 1.1 + .02
    assert all(r['last_seen'] >= r['first_seen'] and r['observations'] > 0 for r in row['threads'])
roots.append(thread_folder)
for index in range(1, 6):
    folder = HERE / f'direct-lookup-cache-thread-lifetimes-v{index}'
    initial = read(folder / 'results.json')
    assert initial['status'] == 'collecting' and not initial['subjects']
    assert initial['driver_sha256'] == sha(folder / 'initial-driver.py')
    assert (folder / 'failure-note.json').is_file()
    receipt = read(folder / '0-baseline/process.json')
    assert not receipt['quantitative_benchmark']
    if index == 1:
        assert receipt['exit_status'] == -9
    else:
        assert receipt['exit_status'] == 0 and sha(folder / '0-baseline/stdout.bin') == OUTPUT_SHA
    roots.append(folder)
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        processes.add(path)
        process = read(path)
        assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
        assert process['inherited_common_mutex']
        if process['exit_status'] != 0:
            allowed = {HERE.parent / 'native-owner-dispatch-v1' / label / 'process.json' for label in ['direct-lookup-cache-focused-v1', 'direct-lookup-cache-native-v1']}
            allowed.add(HERE / 'direct-lookup-cache-thread-lifetimes-v1/0-baseline/process.json')
            assert path in allowed
assert negative == 11
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
OUT.mkdir(exist_ok=True)
result = dict(status='bounded-lookup-cache-trial-verified', evidence=evidence, validation=validation,
              negative_qualification_fixtures=negative, primary_full_observations=18,
              exact_code_profile_captures=3, terminal_owned_processes=len(processes),
              thread_observation_processes=6, retained_monitor_setup_attempts=5,
              canonical_data_sha256=DATA_SHA, canonical_benchmark_samples=0,
              driver_sha256=sha(Path(__file__)),
              production_equivalent_validation_commit=VALIDATED, production_diff=changed,
              scope='Six balanced complete-process cohorts, all complete outputs and physical updates, five actually admitted caches, unchanged source and secured policy, three exact-code profiles and terminal owned processes. Full validation differs from timed source only in the fixture that now counts owned cache bytes. The initial borrow error and stale exact-byte fixture failure remain. No Rust runtime parity is established.')
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'primary_full_observations', 'exact_code_profile_captures', 'negative_qualification_fixtures', 'terminal_owned_processes']}))
