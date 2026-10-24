"""Verify the broader strategy checkpoint from retained raw evidence."""
import ast
import copy
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parents[2]
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
SOURCE_COMMIT = '393d23b24b80cad13e2c2b0284823290d7bafacf'
SOURCE_SHA = 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
BYTECODE_SHA = '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
DATA_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
FULL_POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
FULL_OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
STAGES = [('cold-snapshots',70),('direct-entry',71),('funded-extent',72),('caller-extent',73)]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def git(*args): return subprocess.check_output(['git','--no-optional-locks','-C',str(WORKSPACE),*args],text=True).strip()


assert git('rev-parse','HEAD') == SOURCE_COMMIT and not git('status','--porcelain')
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
assert sha(HERE / 'knucleotide-source-map.mec') == SOURCE_SHA
script = HERE / 'measure_stage.py'
tree = ast.parse(script.read_text())
function = next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name == 'require_steady_loops')
namespace = {}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(script),'exec'),namespace)
qualify = namespace['require_steady_loops']
evidence = {}
roots = []
negative_count = 0
for name, version in STAGES:
    timing = read(HERE / (name+'-timing-v1/results.json'))
    assert timing['status'] == 'all-outputs-and-update-counts-verified'
    assert timing['source_sha256'] == SOURCE_SHA and timing['bytecode_sha256'] == BYTECODE_SHA
    assert sha(HERE / (name+'-timing-v1/measure-stage-driver.py')) == timing['study_driver_sha256']
    binary = HERE / '.build' / ('counting-'+name)
    assert sha(binary) == timing['candidate_sha256']
    descriptor = read(HERE / '.build' / ('counting-'+name+'.project/native-descriptor.json'))['descriptor']
    arguments = dict(descriptor=descriptor,loops=timing['compiled_outlined_loops'],
        guarded=timing['compiled_guarded_loops'],invariants=timing['compiled_loop_invariants'],
        lookups=timing['compiled_lookup_facts'],pre_data_passes=1,
        specialize_widths=True,fuel_edge_checks=True,productive_entry=True,
        separate_header_snapshots=True,peeled_entry_probes=version>=71,
        prepaid_extent=version>=72,caller_prepaid_extent=version>=73)
    qualified = qualify(timing['compiled_steady_loops'],**arguments)
    assert qualified == timing['qualified_steady_regions']
    if version == 73:
        assert timing['source_commit'] == SOURCE_COMMIT
        mutations = [
            lambda r: r.update(native_calls=1),
            lambda r: r.update(maximum_source_instructions=513),
            lambda r: r.update(specialized_widths=[1,18]),
            lambda r: r.update(fuel_check_edges=[None,None]),
            lambda r: r.update(header_snapshot_edges=[]),
            lambda r: r.update(peeled_probe_nodes=[]),
            lambda r: r.update(prepaid_stop_edges=[]),
            lambda r: r.update(fuel_reconstructed_at_exits=False),
            lambda r: r.update(prepaid_extent_arguments=1),
        ]
        for mutation in mutations:
            records = copy.deepcopy(timing['compiled_steady_loops'])
            mutation(records[0])
            try: qualify(records,**arguments)
            except (AssertionError,KeyError): negative_count += 1
            else: raise AssertionError('A malformed native qualification was accepted')
    cohort = read(HERE / ('full-'+name+'-cohort-v1/results.json'))
    assert cohort['status'] == 'all-cohorts-and-outputs-verified'
    assert cohort['source_commit'] == timing['source_commit']
    assert cohort['selected_bases'] == 125000000 and cohort['expected_table_updates'] == 874999961
    assert cohort['source_sha256'] == SOURCE_SHA and cohort['bytecode_sha256'] == BYTECODE_SHA
    assert cohort['launch_sha256'] == FULL_POLICY_SHA
    values = {key:[] for key in ['rust','mech','baseline']}
    for index in range(1,7):
        folder = HERE / f'full-{name}-v{index}'
        result = read(folder / 'results.json')
        assert result['status'] == 'full-output-and-update-counts-verified'
        assert result['launch_sha256'] == FULL_POLICY_SHA == sha(folder / 'launch.json')
        assert result['candidate_sha256'] == timing['candidate_sha256']
        assert result['source_sha256'] == SOURCE_SHA and result['bytecode_sha256'] == BYTECODE_SHA
        for subject in values:
            assert sha(folder / subject / 'stdout.bin') == FULL_OUTPUT_SHA
            receipt = read(folder / subject / 'process.json')
            assert receipt['quantitative_benchmark'] and receipt['exit_status'] == 0
            values[subject].append(receipt['elapsed_seconds'])
        for filename in ['native.report.json','baseline.native.report.json']:
            report = read(folder / filename)
            assert report['native_aot'] and not report['jit'] and report['policy'] == 'secured'
            assert report['shutdown'] == 'completed'
            assert report['native_parallel_tasks'] == report['native_parallel_peak_workers'] == 7
            assert report['native_hash_table_regions'] == report['native_packed_ssa_regions'] == 7
            assert report['native_hash_table_updates'] == report['native_packed_map_updates'] == 874999961
        roots.append(folder)
    for subject, samples in values.items():
        assert cohort['samples_seconds'][subject] == samples
        assert cohort['median_seconds'][subject] == statistics.median(samples)
        assert cohort['x_rust'][subject] == statistics.median(samples) / statistics.median(values['rust'])
    build = read(HERE / ('profile-'+name+'-build-v1/results.json'))
    assert build['source_commit'] == timing['source_commit'] and build['whole_machine_code_matches_timed']
    for index in range(1,4):
        folder = HERE / f'full-profile-{name}-v{index}'
        analysis = read(folder / 'analysis.json')
        assert analysis['source_commit'] == timing['source_commit']
        assert analysis['machine_code_identical'] and analysis['completed_output_verified']
        assert analysis['timed_binary_sha256'] == timing['candidate_sha256']
        roots.append(folder)
    paths = read(HERE / (name+'-codegen-audit-v1/steady-paths-v2.json'))
    assert paths['source_commit'] == timing['source_commit'] and len(paths['paths']) == 38
    assert paths['script_sha256'] == sha(HERE / 'audit_steady_paths.py')
    evidence[name] = dict(source_commit=timing['source_commit'],
        median_seconds=cohort['median_seconds'],x_rust=cohort['x_rust'],
        faster_pairs=sum(a < b for a,b in zip(values['mech'],values['baseline'])),
        reduction_percent=100*(1-cohort['median_seconds']['mech']/cohort['median_seconds']['baseline']),
        static_instructions=[min(p['instructions'] for p in paths['paths']),max(p['instructions'] for p in paths['paths'])])
    roots.extend([HERE / (name+'-timing-v1'),HERE / ('profile-'+name+'-build-v1')])
    hardware = HERE / (name+'-hardware-v1')
    if hardware.exists(): roots.append(hardware)

validation = {}
for name, count in [('cold-snapshots-native-v1',364),('cold-snapshots-catalog-v1',1),
                    ('direct-entry-hash-v1',3),('direct-entry-focused-v1',6),
                    ('funded-extent-focused-v3',6),('caller-extent-focused-v1',6),
                    ('caller-extent-native-v1',365),('caller-extent-catalog-v1',1)]:
    folder = HERE.parent / 'native-owner-dispatch-v1' / name
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['passed'] == count
    assert summary['clean_revision_qualified'] and summary['all_owned_processes_reaped_and_groups_closed']
    if name.startswith('caller-extent'): assert summary['source_commit'] == SOURCE_COMMIT
    validation[name] = count
    roots.append(folder)
for name in ['funded-extent-focused-v1','funded-extent-focused-v2']:
    folder = HERE.parent / 'native-owner-dispatch-v1' / name
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'failed-attempt-retained' and summary['failed'] == 1
    roots.append(folder)

backend = read(HERE / 'backend-comparison-v4/results.json')
assert backend['status'] == 'all-backend-diagnostic-outputs-verified'
assert backend['source_unchanged'] and backend['source_state_before']['commit'] == SOURCE_COMMIT
assert backend['canonical_benchmark_samples'] == 0 and len(backend['samples']) == 48
assert sha(HERE / 'backend-comparison-v4/backend-driver.py') == backend['driver_sha256']
for mode in backend['statistics']:
    denominator = statistics.median(s['seconds'] for s in backend['samples'] if s['input']==mode and s['subject']=='rust')
    for subject, result in backend['statistics'][mode].items():
        samples = [s['seconds'] for s in backend['samples'] if s['input']==mode and s['subject']==subject]
        assert len(samples) == 6 and result['median_seconds'] == statistics.median(samples)
        assert result['x_rust'] == statistics.median(samples)/denominator
roots.extend(HERE / name for name in ['backend-component-v1','backend-component-v2',
    'backend-comparison-v1','backend-comparison-v2','backend-comparison-v3','backend-comparison-v4',
    'productive-entry-prefix-profile-v1'])
roots.extend(HERE / ('compiler-v'+str(version)) for version in range(53,57))
processes, nonzero = set(), []
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes: continue
        receipt = read(path); processes.add(path)
        assert receipt['reaped'] and receipt['group_closed'] and not receipt['cleanup_errors'], path
        assert receipt['inherited_common_mutex'], path
        if receipt['exit_status'] != 0:
            label = str(path.relative_to(ROOT))
            assert any(name in label for name in ['funded-extent-focused-v1','funded-extent-focused-v2',
                'backend-comparison-v1','backend-comparison-v2','backend-comparison-v3']), label
            nonzero.append(dict(path=label,exit_status=receipt['exit_status']))
assert git('rev-parse','HEAD') == SOURCE_COMMIT and not git('status','--porcelain')
assert sha(ROOT / 'data/benchmarks.json') == DATA_SHA
result = dict(status='broader-strategy-checkpoint-verified',source_commit=SOURCE_COMMIT,
    evidence=evidence,validation=validation,negative_qualification_fixtures=negative_count,
    terminal_owned_processes=len(processes),expected_nonzero_processes=nonzero,
    primary_full_observations=72,backend_diagnostic_observations=48,
    backend_statistics=backend['statistics'],canonical_data_sha256=DATA_SHA,
    driver_sha256=sha(Path(__file__)),canonical_benchmark_samples=0,
    scope='Four separate six-cohort primary comparisons, complete outputs/updates/policies, twelve exact-code profiles, immutable test revisions, malformed-metadata rejection, matched backend diagnostics and terminal process ownership. No pooled timings or excluded full-input observations.')
(HERE / 'strategy-search-v2/results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','terminal_owned_processes','primary_full_observations','backend_diagnostic_observations','negative_qualification_fixtures']}))
