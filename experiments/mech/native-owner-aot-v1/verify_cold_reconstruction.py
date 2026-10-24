"""Verify two independent cold-reconstruction trials and their exact-code profiles."""
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
OUT = HERE / 'cold-reconstruction-checkpoint-v1'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
TRIALS = [
    ('cold-recipes', '69fc5812f0ec5f96e3526cdeb51be828370a282c', 59),
    ('cold-frame', '6d2e2673ea1d49d8ec16663dda012547f3ad1f4a', 60),
]


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
    if name == 'cold-frame':
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
    if name == 'cold-frame':
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
    paths = read(HERE / f'{name}-codegen-audit-v1/steady-paths-v2.json')
    assert paths['source_commit'] == commit and len(paths['paths']) == 38
    assert paths['script_sha256'] == sha(HERE / 'audit_steady_paths.py')
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
for name, commit, _ in TRIALS:
    for kind, count in [('focused', 4), ('steady', 6)]:
        label = f'{name}-{kind}-v1'
        folder = HERE.parent / 'native-owner-dispatch-v1' / label
        summary = read(folder / 'summary.json')
        assert summary['status'] == 'passed' and summary['passed'] == count and summary['source_commit'] == commit
        assert summary['clean_revision_qualified'] and summary['all_owned_processes_reaped_and_groups_closed']
        validation[label] = count
        roots.append(folder)
for label, count in [('cold-frame-native-v1', 369), ('cold-frame-catalog-v1', 1)]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / label
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['source_commit'] == TRIALS[1][1] and summary['clean_revision_qualified']
    assert summary['all_owned_processes_reaped_and_groups_closed']
    validation[label] = count
    roots.append(folder)
fresh_rust = read(HERE / 'rust-full-profile-v17/results.json')
assert fresh_rust['status'] == 'three-full-output-verified-profiles'
assert len(fresh_rust['subjects']) == 3
roots.append(HERE / 'rust-full-profile-v17')
fresh_partition = read(HERE / 'cold-frame-remaining-profile-v2/results.json')
assert fresh_partition['status'] == 'exclusive-worker-observations-partitioned'
assert fresh_partition['aggregates']['mech'] == evidence['cold-frame']['profile']
assert fresh_partition['script_sha256'] == sha(HERE / 'cold-frame-remaining-profile-v2/profile-hotspots-driver.py')
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        processes.add(path)
        process = read(path)
        assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
        assert process['inherited_common_mutex'] and process['exit_status'] == 0
assert negative == 21
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
OUT.mkdir(exist_ok=True)
result = dict(status='cold-reconstruction-trials-verified', evidence=evidence, validation=validation,
              negative_qualification_fixtures=negative, primary_full_observations=36,
              exact_code_profile_captures=6, terminal_owned_processes=len(processes),
              fresh_rust_profile_captures=3, fresh_comparison=fresh_partition['aggregates'],
              canonical_data_sha256=DATA_SHA, canonical_benchmark_samples=0,
              driver_sha256=sha(Path(__file__)),
              scope='Two independent six-cohort comparisons, all complete outputs and physical updates, unchanged secured policies and source, six exact-code profiles, original source-bound metadata and terminal owned processes. Focused suites are counted per immutable revision; no speedup or Rust parity is established.')
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'primary_full_observations', 'exact_code_profile_captures', 'negative_qualification_fixtures', 'terminal_owned_processes']}))
