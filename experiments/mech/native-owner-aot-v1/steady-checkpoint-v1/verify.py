"""Recompute the funded-loop checkpoint from its retained serial receipts."""
import hashlib
import json
import pathlib
import statistics
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
COMPILER = pathlib.Path('/private/tmp/mech-native-hashmap-performance')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


pins = {
    ROOT / 'data/benchmarks.json': '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7',
    STUDY / 'knucleotide-source-map.mec': 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da',
    STUDY.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7': 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763',
    ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin': '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',
    STUDY / '.build/counting-escrow-spin': '86f3a407052eb265930aab5a74235dec3ca29abc04a0d277ebfa5f41b8f162c5',
    STUDY / '.build/counting-steady': 'd3c88bd5dac3da4c5137c1fd716fc15204e936a65ddce1c48471251329e21835',
    STUDY / '.build/counting-steady-fold': '5b87a57ac53148b37b5aeab38703ba83c10663d418d2b4bb829d2027645e99a7',
}
for path, expected in pins.items():
    assert sha(path) == expected, str(path)
assert pathlib.Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837

cohorts = {}
for aggregate, runs in [
    ('full-steady-cohort-v1', [f'full-steady-matched-v{i}' for i in range(1, 4)]),
    ('full-steady-fold-cohort-v2', [f'full-steady-fold-v{i}' for i in range(1, 7)]),
]:
    result = read(STUDY / aggregate / 'results.json')
    assert result['status'] == 'all-cohorts-and-outputs-verified'
    samples = {label: [] for label in ('mech', 'baseline', 'rust')}
    paired_faster = 0
    for name in runs:
        folder = STUDY / name
        run = read(folder / 'results.json')
        assert run['status'] == 'full-output-and-update-counts-verified'
        assert sha(folder / 'launch.json') == result['launch_sha256'] == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
        assert run['expected_table_updates'] == 874999961
        assert run['source_sha256'] == result['source_sha256']
        for label in samples:
            process = read(folder / label / 'process.json')
            assert process['exit_status'] == 0 and process['reaped'] and process['group_closed']
            assert not process['cleanup_errors']
            assert sha(folder / label / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
            samples[label].append(process['elapsed_seconds'])
        paired_faster += samples['mech'][-1] < samples['baseline'][-1]
    assert samples == result['samples_seconds']
    for label, observations in samples.items():
        assert statistics.median(observations) == result['median_seconds'][label]
        assert statistics.stdev(observations) == result['stdev_seconds'][label]
        assert result['x_rust'][label] == statistics.median(observations) / statistics.median(samples['rust'])
    cohorts[aggregate] = dict(observations_per_subject=len(runs), paired_faster=paired_faster,
        median_seconds=result['median_seconds'], x_rust=result['x_rust'],
        reduction_percent=100 * (1 - result['median_seconds']['mech'] / result['median_seconds']['baseline']))

profiles = {}
for name in ('steady-remaining-profile-v1', 'steady-parent-remaining-profile-v1', 'steady-fold-remaining-profile-v1'):
    result = read(STUDY / name / 'results.json')
    assert result['taxonomy_version'] == 5
    assert sha(STUDY / name / 'profile-hotspots-driver.py') == result['script_sha256']
    for label, summary in result['aggregates'].items():
        assert sum(summary['exclusive_buckets'].values()) == summary['worker_observations']
        rows = result['samples'][label]
        assert sum(row['worker_observations'] for row in rows) == summary['worker_observations']
        for row in rows:
            assert sha(STUDY / row['stacks']) == row['stacks_sha256']
            assert sum(row['exclusive_buckets'].values()) == row['worker_observations']
    profiles[name] = result['aggregates']

changes = subprocess.check_output(['git', '-C', str(COMPILER), 'diff', '--name-only', 'f02fbe82', 'HEAD'], text=True).splitlines()
assert changes == ['hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
                   'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs']
assert not subprocess.check_output(['git', '-C', str(COMPILER), 'status', '--porcelain'])
validation = {}
for name in ('steady-fold-native-v2', 'steady-fold-catalog-v1'):
    summary = read(STUDY.parent / 'native-owner-dispatch-v1' / name / 'summary.json')
    assert summary['status'] == 'passed' and summary['clean_revision_qualified']
    assert summary['source_commit'] == '8eb6db853b2040d26ff89dcaa589b58be5a723ec'
    validation[name] = {k: summary[k] for k in ('passed', 'failed', 'ignored', 'source_commit')}

# Include every new stage's raw failures, builds, profiles, counters and timings.
# Parent comparison profiles are measurement children, not new benchmark runs.
prefixes = ('steady', 'full-steady', 'full-profile-steady', 'profile-steady')
roots = [p for p in STUDY.iterdir() if p.is_dir() and p.name.startswith(prefixes)]
roots += [STUDY / 'compiler-v47', STUDY / 'compiler-v48', STUDY / 'rust-full-profile-v16']
roots += [p for p in (STUDY.parent / 'native-owner-dispatch-v1').iterdir() if p.is_dir() and p.name.startswith('steady')]
json_count = processes = 0
for folder in roots:
    for path in folder.rglob('*.json'):
        if path == HERE / 'results.json':
            continue
        doc = read(path)
        json_count += 1
        if path.name == 'process.json':
            assert doc['reaped'] and doc['group_closed'] and not doc['cleanup_errors'], str(path)
            processes += 1

result = dict(status='funded-loop-checkpoint-verified', benchmark_samples=0,
    source_commit='8eb6db853b2040d26ff89dcaa589b58be5a723ec',
    timed_source_commit='f02fbe82f3b0dbf178ffc2f6b1c5431ce3643e63',
    post_timing_changes=changes, production_code_unchanged_after_timing=True,
    json_artifacts_parsed=json_count, terminal_owned_processes=processes,
    immutable_pins={str(p.relative_to(ROOT)): value for p, value in pins.items()},
    common_lock_inode=83858837, cohorts=cohorts, profiles=profiles, validation=validation,
    verifier_sha256=sha(pathlib.Path(__file__)),
    scope='Recomputed receipt statistics and immutable artifact checks. Failed attempts remain; no benchmark observation is excluded or reclassified as a passing observation.')
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'json_artifacts_parsed', 'terminal_owned_processes', 'cohorts', 'validation')}))
