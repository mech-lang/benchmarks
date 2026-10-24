"""Verify both full-input alias-region cohorts, source pins, limits and exact-code diagnostics."""
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
OUT = HERE / 'disjoint-state-checkpoint-v1'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
TRIALS = [('disjoint-state', 'a94d34d60ab7bc503603217d0baa49397143eb09', 68)]
VALIDATED = 'a94d34d60ab7bc503603217d0baa49397143eb09'
PARENT = '438646017717a5c4392721f13c6f935e88c59527'


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
    if name == 'disjoint-state':
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
    evidence[name] = dict(source_commit=commit, batches=batches, decision=read(HERE / 'disjoint-state-diagnosis-v1/decision.json')['decision'],
                          hardware_medians=hardware['medians'], profile=profile['aggregates']['mech'],
                          instruction_range=[min(p['instructions'] for p in paths['paths']), max(p['instructions'] for p in paths['paths'])])
    roots.extend([timing_folder, build_folder, HERE / (name + '-hardware-v1'), HERE / ('compiler-v' + str(compiler))])

plan_path = HERE / 'disjoint-state-diagnosis-v1/expanded-plan.json'
plan = read(plan_path)
assert plan['source_commit'] == VALIDATED and plan['observations_per_subject'] == 30
assert plan['excluded_warmups'] == plan['excluded_outliers'] == 0
assert len(plan['orders']) == 30
for prior in plan['previous_batch_receipts']: assert sha(HERE / prior['path']) == prior['sha256']
for start in range(0, 30, 6):
    assert len({tuple(order) for order in plan['orders'][start:start+6]}) == 6
expanded_path = HERE / 'full-disjoint-state-expanded-cohort-v1/results.json'
expanded = read(expanded_path)
assert expanded['status'] == 'all-cohorts-and-outputs-verified' and expanded['source_commit'] == VALIDATED
assert expanded['launch_sha256'] == POLICY_SHA and expanded['selected_bases'] == 125000000
assert expanded['expected_table_updates'] == 874999961
values = {subject: [] for subject in ['rust', 'mech', 'baseline']}
for index, order in enumerate(plan['orders'], 1):
    folder = HERE / f'full-disjoint-state-expanded-v{index}'
    raw = read(folder / 'results.json')
    assert raw['status'] == 'full-output-and-update-counts-verified'
    assert raw['source_commit'] == VALIDATED and raw['candidate_sha256'] == timing['candidate_sha256']
    assert raw['source_sha256'] == SOURCE_SHA and raw['bytecode_sha256'] == BYTECODE_SHA
    assert raw['configuration']['order'] == order
    assert sha(folder / 'launch.json') == raw['launch_sha256'] == POLICY_SHA
    for subject in values:
        process = read(folder / subject / 'process.json')
        assert process['exit_status'] == 0 and process['quantitative_benchmark']
        assert sha(folder / subject / 'stdout.bin') == OUTPUT_SHA
        values[subject].append(process['elapsed_seconds'])
    for filename in ['native.report.json', 'baseline.native.report.json']:
        native = read(folder / filename)
        assert native['native_aot'] and not native['jit'] and native['policy'] == 'secured'
        assert native['shutdown'] == 'completed'
        assert native['native_parallel_tasks'] == native['native_parallel_peak_workers'] == 7
        assert native['native_hash_table_regions'] == native['native_packed_ssa_regions'] == 7
        assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 874999961
        assert native['native_direct_lookup_regions'] == 5
    roots.append(folder)
for subject, samples in values.items():
    assert samples == expanded['samples_seconds'][subject]
    assert statistics.median(samples) == expanded['median_seconds'][subject]
    assert statistics.median(samples) / statistics.median(values['rust']) == expanded['x_rust'][subject]
expanded_gain = 100 * (1-expanded['median_seconds']['mech']/expanded['median_seconds']['baseline'])
expanded_pairs = sum(a < b for a,b in zip(values['mech'],values['baseline']))
expanded_passes = expanded_gain >= 1 and expanded_pairs >= 20
assert read(HERE / 'disjoint-state-diagnosis-v1/decision.json')['expanded_passes_promotion_threshold'] == expanded_passes
evidence['disjoint-state']['expanded'] = dict(median_seconds=expanded['median_seconds'],x_rust=expanded['x_rust'],improvement_percent=expanded_gain,faster_pairs=expanded_pairs,passes_promotion_threshold=expanded_passes)

prefix_batches = {}
for name in ['disjoint-state-timing-v1']:
    folder = HERE / name
    report = read(folder / 'results.json')
    assert report['source_commit'] == VALIDATED and report['status'] == 'all-outputs-and-update-counts-verified'
    assert report['candidate_sha256'] == timing['candidate_sha256'] and report['baseline_sha256'] == timing['baseline_sha256']
    assert report['source_sha256'] == SOURCE_SHA and report['bytecode_sha256'] == BYTECODE_SHA
    assert report['input_bases'] == 1000000 and report['expected_table_updates'] == 6999961
    assert report['study_driver_sha256'] == sha(folder / 'measure-stage-driver.py')
    assert len(report['samples']) == 9
    for label in ['candidate', 'baseline', 'rust']:
        samples = [row['seconds'] for row in report['samples'] if row['label'] == label]
        assert len(samples) == 3 and statistics.median(samples) == report['median_seconds'][label]
        assert report['x_rust'][label] == report['median_seconds'][label] / report['median_seconds']['rust']
        for index in ['warmup', 0, 1, 2]:
            assert sha(folder / f'{index}-{label}' / 'stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
    if name.endswith('repeat-v1'):
        reuse = read(folder / 'reused-build.json')
        assert reuse['receipt'] == 'disjoint-state-timing-v1' and reuse['timing_observations_reused'] == 0
        assert reuse['executable_sha256'] == timing['candidate_sha256']
        assert reuse['source_results_sha256'] == sha(HERE / 'disjoint-state-timing-v1/results.json')
    prefix_batches[name] = dict(median_seconds=report['median_seconds'], x_rust=report['x_rust'],
        change_percent=100*(report['median_seconds']['candidate']/report['median_seconds']['baseline']-1))
    roots.append(folder)

validation = {}
for label, count in [('disjoint-state-native-v2', 379), ('disjoint-state-catalog-v1', 1)]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / label
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['source_commit'] == VALIDATED and summary['clean_revision_qualified']
    assert summary['all_owned_processes_reaped_and_groups_closed']
    validation[label] = count
    roots.append(folder)
changed = subprocess.check_output(['git', '-C', str(SOURCE), 'diff', '--name-only',
    PARENT, VALIDATED], text=True).splitlines()
assert changed == ['hosts/gpu/src/native_artifact/' + name for name in [
    'compiler.rs', 'compiler_memory_regions.rs', 'iteration_compiler.rs',
    'program_borrowed_codegen.rs', 'program_identity.rs', 'program_prefix_codegen.rs',
    'program_prefix_window_tests.rs', 'program_tail_codegen.rs']]
manifest = read(HERE / '.build/counting-disjoint-state.project/linked-manifest.json')['object']
assert manifest['typed_ir_version'] == 79 and manifest['abi_version'] == 28 and manifest['work_policy_version'] == 66
parent = read(HERE / 'full-escrow-backoff12-cohort-v1/results.json')
assert cohort['object_sha256'] != parent['object_sha256'], 'The new alias-region IR must regenerate the Mech object'
assert cohort['baseline_source_commit'] == PARENT
assert cohort['baseline_sha256'] == parent['candidate_sha256']
threads_folder = HERE / 'disjoint-state-thread-lifetimes-v1'
threads = read(threads_folder / 'results.json')
assert threads['source']['commit'] == VALIDATED and not threads['source']['status']
assert threads['driver_sha256'] == sha(HERE / 'disjoint-state-diagnosis-v1/thread-driver.py')
assert len(threads['subjects']) == 6 and threads['benchmark_samples'] == 0
roots.append(threads_folder)
for filename, driver in [('kernel-routes.json', 'kernel_routes.py'), ('preparation.json', 'preparation.py')]:
    detail = read(HERE / 'disjoint-state-checkpoint-v1' / filename)
    assert detail['script_sha256'] == sha(HERE / 'disjoint-state-diagnosis-v1' / driver)
    assert detail['parser_sha256'] == sha(HERE / 'profile_hotspots.py')
    for source in detail['sources']:
        assert sha(HERE / source['path']) == source['sha256']
assert read(HERE / 'disjoint-state-diagnosis-v1/decision.json')['source_commit'] == VALIDATED
failed_folder = HERE.parent / 'native-owner-dispatch-v1/disjoint-state-native-v1'
correction = read(HERE / 'disjoint-state-diagnosis-v1/compile-correction.json')
assert correction['corrected_commit'] == VALIDATED and correction['timing_observations'] == 0
assert sha(failed_folder / 'process.json') == correction['process_sha256']
assert read(failed_folder / 'process.json')['exit_status'] == 101
assert read(failed_folder / 'source-provenance.json')['clean_revision_qualified']
assert read(failed_folder / 'source-provenance.json')['before']['commit'] == correction['initial_commit']
assert subprocess.check_output(['git','-C',str(SOURCE),'diff','--name-only',correction['initial_commit'],VALIDATED],text=True).splitlines() == ['hosts/gpu/src/native_artifact/program_prefix_window_tests.rs']
roots.append(failed_folder)
prefix_partial = HERE / 'disjoint-state-prefix-thread-lifetimes-v1'
prefix_complete = HERE / 'disjoint-state-prefix-thread-lifetimes-v2'
partial = read(prefix_partial / 'results.json')
assert partial['status'] == 'collecting' and len(partial['subjects']) == 2
correction = read(HERE / 'disjoint-state-diagnosis-v1/prefix-thread-correction.json')
assert sha(prefix_partial / 'results.json') == correction['initial_results_sha256']
assert correction['primary_timing_observations'] == 0
for row in correction['retained_terminal_processes']: assert sha(HERE / row['path']) == row['sha256']
assert len(list(prefix_partial.glob('*/process.json'))) == 3
prefix = read(prefix_complete / 'results.json')
assert prefix['status'] == 'all-owned-thread-observations-and-outputs-verified'
assert prefix['input_mode'] == 'prefix' and prefix['benchmark_samples'] == 0 and len(prefix['subjects']) == 4
assert prefix['driver_sha256'] == sha(HERE / 'disjoint-state-diagnosis-v1/thread-prefix-driver-v2.py')
assert prefix['source']['commit'] == VALIDATED and not prefix['source']['status']
for index, subject in enumerate(prefix['subjects']):
    folder = prefix_complete / f"{index}-{subject['subject']}"
    assert sha(folder / 'thread-observations.json') == subject['raw_sha256']
    assert sha(folder / 'stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
roots.extend([prefix_partial,prefix_complete])
decision = read(HERE / 'disjoint-state-diagnosis-v1/decision.json')
assert decision['decision'] == 'reverted-after-expanded-full-input-regression'
assert decision['primary_observations'] == 126 and not decision['expanded_passes_promotion_threshold']
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse',decision['revert_commit']+'^{tree}'],text=True).strip() == decision['restored_tree']
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse',PARENT+'^{tree}'],text=True).strip() == decision['restored_tree']
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        processes.add(path)
        process = read(path)
        assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
        assert process['inherited_common_mutex']
        assert process['exit_status'] == (101 if root == failed_folder else 0)
assert negative == 18
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
OUT.mkdir(exist_ok=True)
result = dict(status='disjoint-state-trial-verified', evidence=evidence, validation=validation, prefix_batches=prefix_batches,
              negative_qualification_fixtures=negative, primary_full_observations=18, replication_full_observations=18,
              expanded_full_observations=90, exact_code_profile_captures=3, terminal_owned_processes=len(processes),
              canonical_data_sha256=DATA_SHA, canonical_benchmark_samples=0,
              driver_sha256=sha(Path(__file__)),
              validation_commit=VALIDATED, changed_paths=changed,
              scope='Two separate six-order complete-process cohorts and one separately predeclared thirty-order confirmation retain all observations, outputs and physical updates. The program source, bytecode, secured work policy and seven-worker count are unchanged. IR79 partitions only owner-constructed error-origin, borrowed-view and non-map Tail metadata; calls remain full alias barriers. Exact-revision tests include incremental Unicode delivery and finite-limit/first-failure comparisons with region tagging disabled. Three profiles match the timed binary entire machine-code section. Counters and thread polling are separate diagnostics, not primary timings. Canonical benchmark data is unchanged; Rust runtime parity remains incomplete.')
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'primary_full_observations', 'replication_full_observations', 'expanded_full_observations', 'exact_code_profile_captures', 'negative_qualification_fixtures', 'terminal_owned_processes']}))
