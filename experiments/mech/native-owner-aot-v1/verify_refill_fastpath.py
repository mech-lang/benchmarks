"""Verify both batches of the rejected full-refill experiment and its exact-code evidence."""
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
OUT = HERE / 'refill-fastpath-checkpoint-v1'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
TRIALS = [('refill-fastpath', '36a0d26e05b92f0f3fb21bdbd3605af2108ec882', 63)]
VALIDATED = '36a0d26e05b92f0f3fb21bdbd3605af2108ec882'
REVERT = 'c4db5641680c171f362f79b809fd80f57c6e7639'
PARENT = '65dfd8bef29a8aef4cddd6926ff6461a959c24be'


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
    args['lookup_split'] = True
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
    if name == 'refill-fastpath':
        mutations += [lambda r: r[0]['cold_snapshot_recipes'][0].update(reload_words=[9, 12])]
    mutations += [
        lambda r: r[0].update(lookup_cache_selection_word=18),
        lambda r: r[0]['lookup_cache_function'].update(lookup_mode='hash'),
        lambda r: r[0]['lookup_cache_function'].update(specialized_widths=[1, 2]),
        lambda r: r[0]['lookup_cache_function'].update(lookup_cache_function={}),
        lambda r: r[0]['lookup_cache_function'].update(code_bytes=0),
        lambda r: r[0]['lookup_cache_function'].update(native_calls=1),
        lambda r: r[0]['lookup_cache_function'].update(caller_instructions=1),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(records)
        mutate(bad)
        try:
            qualify(bad, **args)
        except (AssertionError, KeyError):
            negative += 1
        else:
            raise AssertionError('Malformed cold snapshot accepted')
    batches = {}
    for first, suffix in [(1, 'cohort-v1'), (7, 'replication-v1')]:
        cohort = read(HERE / ('full-' + name + '-' + suffix + '/results.json'))
        assert cohort['status'] == 'all-cohorts-and-outputs-verified'
        assert cohort['source_commit'] == commit and cohort['launch_sha256'] == POLICY_SHA
        assert cohort['selected_bases'] == 125000000 and cohort['expected_table_updates'] == 874999961
        values = {subject: [] for subject in ['rust', 'mech', 'baseline']}
        for index in range(first, first + 6):
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
        batches[suffix] = dict(median_seconds=cohort['median_seconds'], x_rust=cohort['x_rust'], faster_pairs=sum(a < b for a,b in zip(values['mech'], values['baseline'])), candidate_change_percent=100 * (statistics.median(values['mech']) / statistics.median(values['baseline']) - 1))
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
    paths = read(HERE / f'{name}-codegen-audit-v1/steady-paths-split.json')
    assert paths['source_commit'] == commit and len(paths['paths']) == 50
    assert paths['script_sha256'] == sha(HERE / 'audit_split_paths.py')
    hardware = read(HERE / (name + '-hardware-v1/results.json'))
    assert hardware['status'] == 'all-complete-outputs-updates-and-hardware-counters-verified'
    assert hardware['source_commit'] == commit and len(hardware['observations']) == 9
    profile_folder = HERE / (name + '-remaining-profile-v1')
    profile = read(profile_folder / 'results.json')
    assert profile['script_sha256'] == sha(profile_folder / 'profile-hotspots-driver.py')
    assert sum(profile['aggregates']['mech']['exclusive_buckets'].values()) == profile['aggregates']['mech']['worker_observations']
    evidence[name] = dict(source_commit=commit, batches=batches, decision='reverted: initial gain did not reproduce',
                          hardware_medians=hardware['medians'], profile=profile['aggregates']['mech'],
                          instruction_range=[min(p['instructions'] for p in paths['paths']), max(p['instructions'] for p in paths['paths'])])
    audit = read(HERE / f'{name}-codegen-audit-v1/runtime-refill.json')
    assert audit['script_sha256'] == sha(HERE / f'{name}-diagnosis-v1/audit-refill.py')
    for record in audit['records'].values():
        for function in record['functions']:
            assert sha(HERE / function['path']) == function['sha256']
    roots.extend([timing_folder, build_folder, HERE / (name + '-hardware-v1'), HERE / ('compiler-v' + str(compiler))])

validation = {}
for label, count in [('refill-fastpath-focused-v1', 5), ('refill-fastpath-native-v1', 382), ('refill-fastpath-catalog-v1', 1)]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / label
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['source_commit'] == VALIDATED and summary['clean_revision_qualified']
    assert summary['all_owned_processes_reaped_and_groups_closed']
    validation[label] = count
    roots.append(folder)
changed = subprocess.check_output(['git', '-C', str(SOURCE), 'diff', '--name-only',
    '65dfd8bef29a8aef4cddd6926ff6461a959c24be', VALIDATED], text=True).splitlines()
assert sorted(changed) == sorted([
    'hosts/gpu/src/native_artifact/program_packed_map.rs',
    'hosts/gpu/src/native_artifact/program_packed_map_tests.rs',
    'hosts/gpu/src/native_artifact/program_packed_refill_tests.rs'])
parent = read(HERE / 'full-lookup-split-cohort-v1/results.json')
assert cohort['object_sha256'] == parent['object_sha256'], 'Generated Mech object must be unchanged'
assert cohort['baseline_source_commit'] == '65dfd8bef29a8aef4cddd6926ff6461a959c24be'
assert cohort['baseline_sha256'] == parent['candidate_sha256']
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse',REVERT + '^'],text=True).strip() == VALIDATED
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse',REVERT + '^{tree}'],text=True) == subprocess.check_output(['git','-C',str(SOURCE),'rev-parse',PARENT + '^{tree}'],text=True)
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        processes.add(path)
        process = read(path)
        assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
        assert process['inherited_common_mutex']
        assert process['exit_status'] == 0
assert negative == 18
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
OUT.mkdir(exist_ok=True)
result = dict(status='rejected-full-refill-fastpath-trial-verified', evidence=evidence, validation=validation,
              negative_qualification_fixtures=negative, primary_full_observations=18, replication_full_observations=18, revert_commit=REVERT, production_tree_matches=PARENT,
              exact_code_profile_captures=3, terminal_owned_processes=len(processes),
              canonical_data_sha256=DATA_SHA, canonical_benchmark_samples=0,
              driver_sha256=sha(Path(__file__)),
              validation_commit=VALIDATED, changed_paths=changed,
              scope='Two separately reported sets of six balanced complete-process cohorts; candidate reverted after the apparent gain did not reproduce, all complete outputs and physical updates, four bounded emitted lookup functions, five actually admitted caches, unchanged source and secured policy, three exact-code profiles and terminal owned processes. Full validation uses the exact timed revision. The generated Mech object matches the parent; only runtime refill selection and its tests changed. One cached function uses ordinary source/live exit snapshots after optional recipe metadata admission declined. No Rust runtime parity is established.')
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'primary_full_observations', 'replication_full_observations', 'exact_code_profile_captures', 'negative_qualification_fixtures', 'terminal_owned_processes']}))
