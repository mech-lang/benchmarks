"""Retain the rejected immutable-input trial without filtering observations."""
import hashlib
import json
import pathlib
import statistics
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


aggregate = read(STUDY / 'full-snapshot-cohort-v1/results.json')
assert aggregate['status'] == 'all-cohorts-and-outputs-verified'
samples = {label: [] for label in ('rust', 'mech', 'baseline')}
folders = [STUDY / f'full-snapshot-v{i}' for i in range(1, 7)]
for folder in folders:
    assert sha(folder / 'launch.json') == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
    for label in samples:
        result = read(folder / label / 'process.json')
        assert result['exit_status'] == 0
        assert sha(folder / label / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        samples[label].append(result['elapsed_seconds'])
assert samples == aggregate['samples_seconds']
for label, values in samples.items():
    assert statistics.median(values) == aggregate['median_seconds'][label]
    assert statistics.stdev(values) == aggregate['stdev_seconds'][label]
    assert aggregate['x_rust'][label] == statistics.median(values) / statistics.median(samples['rust'])
prefix = read(STUDY / 'snapshot-timing-v1/results.json')
assert prefix['candidate_sha256'] == sha(STUDY / '.build/counting-snapshot')
assert sha(STUDY / 'snapshot-timing-v1/measure-stage-driver.py') == prefix['study_driver_sha256']
profile = read(STUDY / 'profile-snapshot-build-v1/results.json')
assert profile['whole_machine_code_matches_timed']
analysis = read(STUDY / 'full-profile-snapshot-v1/analysis.json')
assert analysis['machine_code_identical'] and analysis['completed_output_verified']
partition = read(STUDY / 'snapshot-remaining-profile-v1/results.json')
for label, summary in partition['aggregates'].items():
    assert sum(summary['exclusive_buckets'].values()) == summary['worker_observations']
    for row in partition['samples'][label]:
        assert sha(STUDY / row['stacks']) == row['stacks_sha256']
folders += [STUDY / name for name in ('snapshot-timing-v1', 'profile-snapshot-build-v1',
    'full-profile-snapshot-v1', 'compiler-v49')]
folders += [STUDY.parent / 'native-owner-dispatch-v1' / name for name in ('snapshot-focused-v1', 'snapshot-focused-v2')]
processes = []
for folder in folders:
    for path in folder.rglob('process.json'):
        result = read(path)
        assert result['reaped'] and result['group_closed'] and not result['cleanup_errors']
        processes.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), exit_status=result['exit_status']))
assert sha(ROOT / 'data/benchmarks.json') == '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
assert pathlib.Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
result = dict(status='rejected-and-restored', benchmark_samples=0,
    experiment_source_commit='4f0c56493dcf170b2e84580b252bfdbaeff40945',
    restoration_source_commit='aff3f28bb', restored_tree='c832b33d844696e17c8f501f64d0fb4ee264d1c9',
    original_validated_head='8eb6db853b2040d26ff89dcaa589b58be5a723ec',
    full_median_seconds=aggregate['median_seconds'], full_x_rust=aggregate['x_rust'],
    full_samples_seconds=samples, excluded_observations=0,
    full_runtime_increase_percent=100 * (aggregate['median_seconds']['mech'] / aggregate['median_seconds']['baseline'] - 1),
    faster_pairs=sum(a < b for a, b in zip(samples['mech'], samples['baseline'])),
    prefix_median_seconds=prefix['median_seconds'], prefix_x_rust=prefix['x_rust'],
    prefix_scope='Three observations and one excluded warmup per subject; no full-input pooling.',
    profile=partition['aggregates']['mech'], owned_processes=processes,
    validation='Six focused checks passed; initial missing test import and zero-interval profiler setup failure remain. Full native suite was not run for the rejected trial; restoration matches the previously validated tree.',
    finding='Six unchanged entry words per loop can be left in caller storage. Code shrank 984 to 872 bytes and stack 96 to 80 bytes, but full timings regress in five of six pairs. Smaller code is not sufficient evidence of faster execution.',
    source_input_policy_and_canonical_data_unchanged=True, verifier_sha256=sha(pathlib.Path(__file__)))
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('status', 'full_median_seconds', 'full_x_rust', 'full_runtime_increase_percent', 'faster_pairs')}))
