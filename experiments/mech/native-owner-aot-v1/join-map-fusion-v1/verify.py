"""Recheck join/map outputs, actual selection, immutable code and all retained receipts."""
import hashlib
from pathlib import Path
import statistics
import sys
STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
DISPATCH = HERE.parent / 'native-owner-dispatch-v1'
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import process, read, source_state, check_native, OUTPUT_SHA, DATA_SHA, SOURCE_SHA, BYTECODE_SHA
sys.path.insert(0, str(HERE))
from analyze_profile import text_section

plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
paths = []
qualified = ['join-map-fusion-engine-v2', 'join-map-fusion-native-v2', 'join-map-fusion-catalog-v1']
expected_failures = {'join-map-fusion-layout-v1', 'join-map-fusion-capture-v1', 'join-map-fusion-contract-v1', 'join-map-fusion-contract-v2', 'join-map-fusion-native-v1'}
validation = []
for folder in sorted(DISPATCH.glob('join-map-fusion-*')):
    provenance = read(folder / 'source-provenance.json')
    assert provenance['source_unchanged'] and provenance['before'] == provenance['after']
    assert provenance['clean_revision_qualified'] and provenance['before']['clean']
    r = read(folder / 'process.json')
    assert r['exit_status'] == (101 if folder.name in expected_failures else 0)
    if folder.name in qualified:
        assert provenance['before']['commit'] == before['commit']
    validation.append(dict(name=folder.name, source_commit=provenance['before']['commit'], exit_status=r['exit_status'], receipt_sha256=process.sha(folder / 'process.json')))
    paths.append(folder / 'process.json')
assert expected_failures == {r['name'] for r in validation if r['exit_status'] != 0}
assert all(name in {r['name'] for r in validation} for name in qualified)
assert '27 passed; 0 failed' in (DISPATCH / 'join-map-fusion-engine-v2/stdout.bin').read_text()
assert '400 passed; 0 failed; 3 ignored' in (DISPATCH / 'join-map-fusion-native-v2/stdout.bin').read_text()
assert '1 passed; 0 failed' in (DISPATCH / 'join-map-fusion-catalog-v1/stdout.bin').read_text()
compiler = read(HERE / plan['compiler'] / 'results.json')
assert compiler['source_commit'] == before['commit'] and compiler['exit_status'] == 0
paths.extend((HERE / plan['compiler']).rglob('process.json'))
prefix = HERE / plan['receipt']
p = read(prefix / 'results.json')
parent = read(HERE / plan['parent_receipt'] / 'results.json')
assert p['status'] == 'all-outputs-and-update-counts-verified' and p['source_commit'] == before['commit']
assert p['study_driver_sha256'] == process.sha(STUDY / 'measure-stage-driver.py') == process.sha(prefix / 'measure-stage-driver.py')
assert p['source_sha256'] == SOURCE_SHA and p['bytecode_sha256'] == BYTECODE_SHA
assert p['object_sha256'] != parent['object_sha256'] and p['native_descriptor_sha256'] != parent['native_descriptor_sha256']
assert len(p['joined_map_proofs']) == 1
assert len(p['samples']) == 9 and len(p['native_executions']) == 8
for r in p['native_executions']:
    assert r['parallel_tasks'] == 7 and r['packed_map_updates'] == 6999961
    if r['label'] == 'candidate':
        assert r['fused_string_map_bytes'] == plan['prefix_fused_bytes']
for subject in ['candidate', 'baseline', 'rust']:
    values = [r['seconds'] for r in p['samples'] if r['label'] == subject]
    assert len(values) == 3 and statistics.median(values) == p['median_seconds'][subject]
    for rnd in ['warmup', '0', '1', '2']:
        assert process.sha(prefix / (rnd + '-' + subject) / 'stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
paths.extend(prefix.rglob('process.json'))
full = []
for batch in [1, 2]:
    folder = HERE / f'full-join-map-fusion-v{batch}'
    r = read(folder / 'results.json')
    assert r['status'] == 'all-join-map-fusion-full-outputs-updates-and-source-pins-verified'
    assert r['source'] == r['source_after'] == before
    assert r['plan_sha256'] == process.sha(STUDY / 'plan.json') and r['driver_sha256'] == process.sha(STUDY / 'measure.py')
    assert len(r['samples']) == 18 and r['excluded_warmups'] == r['excluded_outliers'] == 0
    for sample in r['samples']:
        receipt = HERE / sample['process']
        assert process.sha(receipt) == sample['process_sha256'] and process.sha(receipt.parent / 'stdout.bin') == OUTPUT_SHA
        if sample['subject'] != 'rust':
            native = receipt.parent.with_name(receipt.parent.name + '.native.json')
            assert process.sha(native) == sample['native_sha256']
            check_native(native)
            if sample['subject'] == 'candidate':
                assert read(native)['native_fused_string_map_bytes'] == plan['full_fused_bytes']
    for subject in ['candidate', 'parent', 'rust']:
        values = [s['seconds'] for s in r['samples'] if s['subject'] == subject]
        assert len(values) == 6 and statistics.median(values) == r['median_seconds'][subject]
        assert r['x_rust'][subject] == r['median_seconds'][subject] / r['median_seconds']['rust']
    paths.extend(folder.rglob('process.json'))
    full.append(r)
project = HERE / '.build' / (plan['binary'] + '.project')
parent_project = HERE / '.build' / (plan['parent_binary'] + '.project')
for name in ['native-resources.json', 'program.mecb']:
    assert process.sha(project / name) == process.sha(parent_project / name)
profile_folder = HERE / 'profile-join-map-fusion-build-v1'
profile = read(profile_folder / 'results.json')
assert profile['source_commit'] == before['commit'] and profile['whole_machine_code_matches_timed']
assert text_section(Path(profile['binary'])) == text_section(HERE / '.build' / plan['binary'])
assert hashlib.sha256(text_section(Path(profile['binary']))).hexdigest() == profile['machine_code_sha256']
paths.extend(profile_folder.rglob('process.json'))
analysis = read(STUDY / 'analysis.json')
assert analysis['status'] == 'exact-current-binary-observations-partitioned'
assert analysis['source'] == analysis['source_after'] == before
assert analysis['analysis_sha256'] == process.sha(STUDY / 'analyze.py')
for subject in ['mech', 'rust']:
    folder = STUDY / f'early-{subject}-profile-v1'
    capture = read(folder / 'results.json')
    assert capture['status'] == 'profile-captured' and capture['source'] == capture['source_after'] == before
    assert len(capture['samples']) == len(capture['subjects']) == 3
    assert capture['binary_sha256'] == analysis['languages'][subject]['binary_sha256']
    assert capture['script_sha256'] == process.sha(STUDY / 'profile-capture.py')
    for index, sample in enumerate(capture['samples']):
        sub = folder / f'sample-{index}'
        assert process.sha(sub / 'stacks.txt') == sample['stacks_sha256'] and sample['owned_direct_child']
        assert process.sha(sub / 'subject/stdout.bin') == OUTPUT_SHA
        if subject == 'mech':
            check_native(sub / 'native.report.json')
            assert read(sub / 'native.report.json')['native_fused_string_map_bytes'] == plan['full_fused_bytes']
    paths.extend(folder.rglob('process.json'))
counter = read(STUDY / 'counters/results.json')
assert counter['source'] == counter['source_after'] == before
assert len(counter['counters']) == 9 and counter['driver_sha256'] == process.sha(STUDY / 'counters.py')
for row in counter['counters']:
    folder = STUDY / 'counters' / f"counter-{row['order']}-{row['subject']}"
    assert process.sha(folder / 'stderr.bin') == row['stderr_sha256'] and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
    if row['subject'] != 'rust':
        check_native(folder.with_name(folder.name + '.native.json'))
        if row['subject'] == 'candidate':
            assert read(folder.with_name(folder.name + '.native.json'))['native_fused_string_map_bytes'] == plan['full_fused_bytes']
paths.extend((STUDY / 'counters').rglob('process.json'))
for path in set(paths):
    r = read(path)
    assert r['exit_status'] == (101 if path.parent.name in expected_failures else 0)
    assert r['inherited_common_mutex'] and r['reaped'] and r['group_closed']
    assert not r['cleanup_errors'] and not r['signals'] and r['birth_identity']['pid'] > 0
assert process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
assert process.sha(HERE / 'knucleotide-source-map.mec') == SOURCE_SHA and source_state() == before
binary = HERE / '.build' / plan['binary']
assert process.sha(binary) == p['candidate_sha256']
result = dict(status='join-map-output-selection-code-profile-counter-and-terminal-receipts-verified', source=before,
    retained_process_receipts=len(set(paths)), validation=validation, retained_failed_attempts=sorted(expected_failures),
    passed_engine_tests=27, passed_native_tests=400, passed_catalog_tests=1, ignored_existing_manual_tests=3,
    source_sha256=SOURCE_SHA, bytecode_sha256=BYTECODE_SHA, object_sha256=p['object_sha256'], candidate_sha256=p['candidate_sha256'],
    binary_file_bytes=binary.stat().st_size, whole_text_bytes=profile['machine_code_bytes'], whole_text_sha256=profile['machine_code_sha256'],
    counter_medians=counter['counter_medians'], full_sessions=[{k:r[k] for k in ['session','median_seconds','x_rust','median_peak_rss_bytes','paired_change_percent','paired_change_interval_95']} for r in full],
    primary_full_samples=36, primary_prefix_samples=9, excluded_prefix_warmups=3, excluded_full_warmups=0, excluded_outliers=0,
    driver_sha256=process.sha(Path(__file__)))
process.save(STUDY / 'verification.json', result)
print({k:result[k] for k in ['status','retained_process_receipts','primary_full_samples','binary_file_bytes']})
