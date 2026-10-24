"""Recompute all four broader compiler trials from their retained receipts."""
import ast
import copy
import hashlib
import json
import pathlib
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
WORKSPACE = pathlib.Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(STUDY))
from analyze_profile import text_section


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == '9dd35e68a5e46b77823ce86c98a2252bdb2be9fe'
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
assert pathlib.Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
pins = {
    ROOT / 'data/benchmarks.json': '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7',
    STUDY / 'knucleotide-source-map.mec': 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da',
    ROOT / 'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs': '47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851',
    STUDY.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7': 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763',
    ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin': '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',
    STUDY / 'rust-span-diagnostic-v2/input.fasta': 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb',
    STUDY / '.build/counting-productive-entry': '812f0cb6498a005c3682050c34ceae397604ea37ba13deb40810a3798501a327',
    STUDY / '.build/counting-steady-fold': '5b87a57ac53148b37b5aeab38703ba83c10663d418d2b4bb829d2027645e99a7',
}
for path, expected in pins.items():
    assert sha(path) == expected, str(path)

cohorts = {}
for stage in ('snapshot', 'width-specialization', 'fuel-edges', 'productive-entry'):
    aggregate = read(STUDY / f'full-{stage}-cohort-v1/results.json')
    assert aggregate['source_sha256'] == pins[STUDY / 'knucleotide-source-map.mec']
    assert aggregate['input_sha256'] == pins[ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin']
    assert aggregate['bytecode_sha256'] == aggregate['baseline_bytecode_sha256'] == '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
    assert aggregate['minimum_parallel_peak'] == aggregate['require_parallel_tasks'] == 7
    samples = {label: [] for label in ('mech', 'baseline', 'rust')}
    for i in range(1, 7):
        folder = STUDY / f'full-{stage}-v{i}'
        result = read(folder / 'results.json')
        assert result['status'] == 'full-output-and-update-counts-verified'
        assert result['expected_table_updates'] == 874999961
        assert sha(folder / 'launch.json') == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
        for label in samples:
            process = read(folder / label / 'process.json')
            assert process['exit_status'] == 0
            assert sha(folder / label / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
            samples[label].append(process['elapsed_seconds'])
    assert samples == aggregate['samples_seconds']
    for label, values in samples.items():
        assert statistics.median(values) == aggregate['median_seconds'][label]
        assert statistics.stdev(values) == aggregate['stdev_seconds'][label]
        assert aggregate['x_rust'][label] == statistics.median(values) / statistics.median(samples['rust'])
    cohorts[stage] = dict(median_seconds=aggregate['median_seconds'], x_rust=aggregate['x_rust'],
        faster_pairs=sum(a < b for a, b in zip(samples['mech'], samples['baseline'])),
        control_source_commit=aggregate['baseline_source_commit'], observations_per_subject=6)

identities = {}
for stage in ('snapshot', 'width-specialization', 'fuel-edges', 'productive-entry'):
    timing = read(STUDY / f'{stage}-timing-v1/results.json')
    assert sha(STUDY / f'{stage}-timing-v1/measure-stage-driver.py') == timing['study_driver_sha256']
    build = read(STUDY / f'profile-{stage}-build-v1/results.json')
    binary = STUDY / '.build' / timing['configuration']['binary']
    assert sha(binary) == timing['candidate_sha256']
    assert text_section(pathlib.Path(build['binary'])) == text_section(binary)
    partition = read(STUDY / f'{stage}-remaining-profile-v1/results.json')
    assert sha(STUDY / f'{stage}-remaining-profile-v1/profile-hotspots-driver.py') == partition['script_sha256']
    for label, summary in partition['aggregates'].items():
        assert sum(summary['exclusive_buckets'].values()) == summary['worker_observations']
        for sample in partition['samples'][label]:
            assert sha(STUDY / sample['stacks']) == sample['stacks_sha256']
    identities[stage] = dict(timed_binary_sha256=sha(binary), profile_binary_sha256=build['binary_sha256'],
        machine_code_bytes=build['machine_code_bytes'], entire_machine_code_identical=True)

timing = read(STUDY / 'productive-entry-timing-v1/results.json')
descriptor = read(STUDY / '.build/counting-productive-entry.project/native-descriptor.json')['descriptor']
tree = ast.parse((STUDY / 'measure_stage.py').read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'require_steady_loops')
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), 'retained-stage-qualifier', 'exec'), namespace)
arguments = [timing['compiled_steady_loops'], descriptor, timing['compiled_outlined_loops'],
             timing['compiled_guarded_loops'], timing['compiled_loop_invariants'], timing['compiled_lookup_facts']]
options = dict(pre_data_passes=1, specialize_widths=True, fuel_edge_checks=True, productive_entry=True)
assert len(namespace['require_steady_loops'](*copy.deepcopy(arguments), **options)) == 2
fixtures = {}
for mutation in ('native_call', 'missing_width', 'missing_initial_edge', 'wrong_index', 'wrong_endpoint'):
    mutated = copy.deepcopy(arguments)
    record = mutated[0][0]
    if mutation == 'native_call': record['native_calls'] = 1
    if mutation == 'missing_width': record['specialized_widths'].pop()
    if mutation == 'missing_initial_edge': record['fuel_check_edges'].remove(None)
    if mutation == 'wrong_index': record['entry_stop_index_word'] = 9999
    if mutation == 'wrong_endpoint': record['entry_stop_endpoint_words'].reverse()
    try:
        namespace['require_steady_loops'](*mutated, **options)
    except (AssertionError, KeyError, IndexError):
        fixtures[mutation] = 'rejected'
    else:
        raise AssertionError(f'{mutation} accepted')

validation = {}
for stage in ('productive-entry-native-v1', 'productive-entry-catalog-v1'):
    summary = read(STUDY.parent / 'native-owner-dispatch-v1' / stage / 'summary.json')
    assert summary['status'] == 'passed' and summary['clean_revision_qualified']
    assert summary['source_commit'] == timing['source_commit']
    validation[stage] = {key: summary[key] for key in ('passed', 'failed', 'ignored', 'source_commit')}

stages = ('snapshot', 'width-specialization', 'fuel-edges', 'productive-entry')
folders = [folder for folder in STUDY.iterdir() if folder.is_dir() and
           any(folder.name.startswith(prefix + stage) for stage in stages for prefix in ('', 'full-', 'full-profile-', 'profile-'))]
folders += [STUDY / 'invariant-snapshot-diagnosis-v1']
folders += [STUDY / f'compiler-v{i}' for i in range(49, 53)]
folders += [folder for folder in (STUDY.parent / 'native-owner-dispatch-v1').iterdir()
            if folder.is_dir() and folder.name.startswith(stages)]
processes = json_count = 0
for folder in folders:
    for path in folder.rglob('*.json'):
        document = read(path)
        json_count += 1
        if path.name == 'process.json':
            assert document['reaped'] and document['group_closed'] and not document['cleanup_errors'], str(path)
            processes += 1

result = dict(status='broader-compiler-strategy-checkpoint-verified', benchmark_samples=0,
    source_commit=timing['source_commit'], native_ir_abi_work_versions=[69, 27, 65],
    immutable_pins={str(path.relative_to(ROOT)): value for path, value in pins.items()},
    common_lock_inode=83858837, cohorts=cohorts, exact_code_profiles=identities,
    positive_qualified_source_regions=2, negative_qualifier_fixtures=fixtures,
    validation=validation, json_artifacts_parsed=json_count, terminal_owned_process_receipts=processes,
    full_quantitative_observations=72, full_observations_excluded=0,
    prefix_scope='Separate three-observation cohorts, one excluded warmup per subject; original and direct-reference prefix cohorts both retained.',
    verifier_sha256=sha(pathlib.Path(__file__)),
    scope='Recomputed statistics, exact-code identities, negative metadata fixtures, finite policy/output/data pins and complete owned-process cleanup. This does not assign time shares to instructions or prove Rust parity.')
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('status', 'json_artifacts_parsed', 'terminal_owned_process_receipts', 'cohorts', 'validation')}))
