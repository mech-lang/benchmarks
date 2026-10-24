"""Verify retained source-proof and cursor trials, without pooling cohorts."""
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
OUT = HERE / 'cursor-profile-checkpoint-v1'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
TRIALS = [
    ('proved-graphemes', 'f1323c0383927e461a0c70f34872b1e6e44f9657', 57, [2]),
    ('affine-cursor', 'c7574fa952a9981e1b2b0659a510fc05eff1c2ff', 58, [1, 2, 3]),
]


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True).strip()


assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
assert sha(HERE / 'knucleotide-source-map.mec') == SOURCE_SHA
assert Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
assert git('rev-parse', '36914cd38^{tree}') == git('rev-parse', '393d23b24^{tree}')
roots, evidence, negative = [], {}, 0
for name, commit, compiler, captures in TRIALS:
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
                prepaid_extent=True, caller_prepaid_extent=True)
    if name == 'affine-cursor': args['affine_cursor'] = True
    assert qualify(timing['compiled_steady_loops'], **args) == timing['qualified_steady_regions']
    if name == 'affine-cursor':
        invalid = [dict(native_calls=1), dict(maximum_source_instructions=513),
                   dict(specialized_widths=[1, 18]), dict(fuel_check_edges=[None, None]),
                   dict(header_snapshot_edges=[]), dict(peeled_probe_nodes=[]),
                   dict(prepaid_stop_edges=[]), dict(fuel_reconstructed_at_exits=False),
                   dict(prepaid_extent_arguments=1), dict(cursor_range_site=-1),
                   dict(cursor_index_word=-1), dict(cursor_recurrence_edges=[])]
        for mutation in invalid:
            records = copy.deepcopy(timing['compiled_steady_loops'])
            records[0].update(mutation)
            try: qualify(records, **args)
            except (AssertionError, KeyError): negative += 1
            else: raise AssertionError('Malformed source-bound qualification accepted')
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
    for index in captures:
        folder = HERE / f'full-profile-{name}-v{index}'
        analysis = read(folder / 'analysis.json')
        assert analysis['source_commit'] == commit and analysis['machine_code_identical']
        assert analysis['completed_output_verified'] and analysis['timed_binary_sha256'] == timing['candidate_sha256']
        roots.append(folder)
    hardware = read(HERE / (name + '-hardware-v1/results.json'))
    assert hardware['status'] == 'all-complete-outputs-updates-and-hardware-counters-verified'
    assert hardware['source_commit'] == commit and len(hardware['observations']) == 9
    profile = read(HERE / (name + '-remaining-profile-v1/results.json'))
    assert sum(profile['aggregates']['mech']['exclusive_buckets'].values()) == profile['aggregates']['mech']['worker_observations']
    evidence[name] = dict(source_commit=commit, median_seconds=cohort['median_seconds'],
                          x_rust=cohort['x_rust'], faster_pairs=sum(a < b for a, b in zip(values['mech'], values['baseline'])),
                          hardware_medians=hardware['medians'], profile=profile['aggregates']['mech'])
    roots.extend([timing_folder, build_folder, HERE / (name + '-hardware-v1'), HERE / ('compiler-v' + str(compiler))])

validation = {}
for name, count, commit in [
    ('proved-graphemes-domain-v1', 1, TRIALS[0][1]), ('proved-graphemes-closed-v1', 64, TRIALS[0][1]),
    ('affine-cursor-focused-v1', 4, TRIALS[1][1]), ('affine-cursor-states-v1', 1, TRIALS[1][1]),
    ('affine-cursor-ranges-v1', 1, TRIALS[1][1]), ('affine-cursor-native-v1', 365, TRIALS[1][1]),
    ('affine-cursor-catalog-v1', 1, TRIALS[1][1]),
]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / name
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count and summary['source_commit'] == commit
    assert summary['clean_revision_qualified'] and summary['all_owned_processes_reaped_and_groups_closed']
    validation[name] = count; roots.append(folder)
objects = read(HERE / 'proved-graphemes-diagnosis-v1/object-identity.json')
assert objects['identical'] and len(set(objects['object_sha256'].values())) == 1
paths = read(HERE / 'affine-cursor-codegen-audit-v1/steady-paths-v2.json')
assert len(paths['paths']) == 38 and paths['script_sha256'] == sha(HERE / 'audit_steady_paths.py')
assert paths['source_commit'] == TRIALS[1][1]
roots.append(HERE / 'full-profile-proved-graphemes-v1')
processes, failures = set(), []
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        processes.add(path); process = read(path)
        assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
        assert process['inherited_common_mutex']
        if process['exit_status'] != 0:
            assert path == HERE / 'full-profile-proved-graphemes-v1/subject/process.json'
            assert process['exit_status'] == 1
            failures.append(str(path.relative_to(ROOT)))
assert negative == 12 and len(failures) == 1
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
OUT.mkdir(exist_ok=True)
result = dict(status='cursor-and-source-proof-trials-verified', evidence=evidence, validation=validation,
              negative_qualification_fixtures=negative, primary_full_observations=36,
              exact_code_profile_captures=4, terminal_owned_processes=len(processes),
              expected_failed_setup_processes=failures, canonical_data_sha256=DATA_SHA,
              canonical_benchmark_samples=0, driver_sha256=sha(Path(__file__)),
              scope='Two independent six-cohort comparisons; complete outputs, update counts, secured policies, immutable source/test revisions, exact-code profiles, structural metadata rejection, reverted source-proof tree and terminal owned processes. No pooled cohorts or causal attribution of small timing differences.')
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'primary_full_observations', 'exact_code_profile_captures', 'negative_qualification_fixtures', 'terminal_owned_processes']}))
