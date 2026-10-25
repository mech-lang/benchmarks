"""Recompute every buffer observation and qualify early full-input captures."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA, DATA_SHA
sys.path.insert(0, str(HERE))
from analyze_profile import text_section, stack_threads
from profile_hotspots import leaves


def native(path, mode):
    if mode == 'full':
        check_native(path)
    else:
        n = read(path)
        assert n['native_hash_table_updates'] == n['native_packed_map_updates'] == 6999961
        assert n['policy'] == 'secured' and n['shutdown'] == 'completed'
        assert n['native_parallel_tasks'] == 7 and 1 <= n['native_parallel_peak_workers'] <= 7


plan = read(STUDY / 'plan.json')
pilot = read(STUDY / 'results.json')
assert pilot['status'] == 'all-host-input-chunk-pilot-stages-verified'
assert pilot['source'] == pilot['source_after'] and pilot['source']['commit'] == plan['source_commit']
assert not pilot['source']['status']
assert pilot['driver_sha256'] == process.sha(STUDY / 'pilot.py')
assert pilot['plan_sha256'] == process.sha(STUDY / 'plan.json')
predeclared = subprocess.check_output(['git', '-C', str(HERE.parents[2]), 'show',
    'c9ee00e8390e21f2289958bf87b8c1260af88880:experiments/mech/native-owner-aot-v1/host-input-chunk-v1/plan.json'])
assert hashlib.sha256(predeclared).hexdigest() == pilot['plan_sha256']
original = HERE / '.build' / (plan['baseline_binary'] + '.project')
baseline = read(HERE / plan['baseline_receipt'] / 'results.json')
assert process.sha(original / 'program.o') == pilot['object_sha256'] == baseline['object_sha256']
assert pilot['object_sha256'] == 'f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335'
targets = dict(baseline=HERE / '.build' / plan['baseline_binary'],
    rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
for label, chunk in plan['variants'].items():
    build = pilot['builds'][label]
    folder = STUDY / ('build-' + label)
    assert build['chunk_bytes'] == chunk and read(folder / 'process.json') == build['process']
    expected_main = (original / 'src/main.rs').read_text().replace(
        '.with_text_capture(launch.input_text_bytes, 64 * 1024)',
        f'.with_text_capture(launch.input_text_bytes, {chunk})')
    assert (folder / 'src-main.rs').read_text() == expected_main
    assert process.sha(folder / 'src-main.rs') == build['main_sha256']
    assert process.sha(folder / 'build.rs') == build['build_sha256']
    assert process.sha(folder / 'linked-manifest.json') == build['manifest_sha256']
    manifest = read(folder / 'linked-manifest.json')
    assert manifest['pins']['src/main.rs'] == build['main_sha256']
    assert manifest['pins']['build.rs'] == build['build_sha256']
    build_text = (folder / 'build.rs').read_text()
    expected = json.loads(json.loads(re.search(r'const EXPECTED: &str = ("(?:[^"\\]|\\.)*");', build_text)[1]))
    assert expected == {k: v for k, v in manifest['pins'].items() if k != 'build.rs'}
    project = Path(build['project'])
    for name, pin in build['unchanged_inputs'].items():
        assert process.sha(project / name) == process.sha(original / name) == pin
    binary = Path(build['binary'])
    assert process.sha(binary) == build['binary_sha256']
    assert hashlib.sha256(text_section(binary)).hexdigest() == build['machine_code_sha256']
    assert len(text_section(binary)) == build['machine_code_bytes']
    targets[label] = binary
sessions = []
sample_count = 0
for relative in pilot['sessions']:
    folder = (HERE / relative).parent
    report = read(folder / 'results.json')
    mode, session = report['mode'], report['session']
    assert report['status'] == 'all-host-chunk-outputs-updates-and-pins-verified'
    assert report['source'] == report['source_after'] == pilot['source']
    assert report['driver_sha256'] == pilot['driver_sha256'] and report['plan_sha256'] == pilot['plan_sha256']
    assert report['orders'] == (plan['orders'] if session == 1 else list(reversed(plan['orders'])))
    assert len(report['samples']) == 16 and report['excluded_warmups'] == report['excluded_outliers'] == 0
    for position in range(4):
        assert Counter(order[position] for order in report['orders']) == {s: 1 for s in targets}
    assert report['input_sha256'] == (INPUT_SHA if mode == 'full' else 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb')
    assert report['policy_sha256'] == (POLICY_SHA if mode == 'full' else '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec')
    assert report['canonical_data_sha256'] == DATA_SHA
    values = {s: [] for s in targets}
    for index, row in enumerate(report['samples']):
        order, position = divmod(index, 4)
        subject = report['orders'][order][position]
        assert (row['order'], row['position'], row['subject']) == (order, position, subject)
        path = HERE / row['process']
        assert process.sha(path) == row['process_sha256']
        receipt = read(path)
        assert receipt['quantitative_benchmark'] and receipt['elapsed_seconds'] == row['seconds']
        assert receipt['maximum_rss_bytes'] == row['maximum_rss_bytes']
        assert process.sha(Path(receipt['command'][0])) == report['pins'][subject] == process.sha(targets[subject])
        assert process.sha(path.parent / 'stdout.bin') == (OUTPUT_SHA if mode == 'full' else 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa')
        if subject != 'rust':
            native_path = Path(receipt['command'][2])
            assert process.sha(native_path) == row['native_sha256']
            native(native_path, mode)
        values[subject].append(row)
    for subject, rows in values.items():
        assert len(rows) == 4
        assert report['median_seconds'][subject] == statistics.median(r['seconds'] for r in rows)
        assert report['median_peak_rss_bytes'][subject] == statistics.median(r['maximum_rss_bytes'] for r in rows)
        assert report['standard_deviation_seconds'][subject] == statistics.stdev(r['seconds'] for r in rows)
        assert report['x_rust'][subject] == report['median_seconds'][subject] / report['median_seconds']['rust']
    for variant_index, label in enumerate(sorted(plan['variants'])):
        logs = [math.log(c['seconds'] / p['seconds']) for c, p in zip(values[label], values['baseline'])]
        rng = random.Random(2026102505 + 10 * session + variant_index)
        boot = sorted(statistics.median(rng.choices(logs, k=len(logs))) for _ in range(20000))
        expected = dict(change_percent=100 * math.expm1(statistics.median(logs)),
            interval_95=[100 * math.expm1(boot[i]) for i in (499, 19499)], faster_pairs=sum(x < 0 for x in logs),
            median_change_percent=100 * (report['median_seconds'][label] / report['median_seconds']['baseline'] - 1))
        assert report['paired_changes'][label] == expected
    sessions.append({k: report[k] for k in ['mode', 'session', 'median_seconds', 'x_rust', 'median_peak_rss_bytes', 'paired_changes']})
    sample_count += len(report['samples'])
assert sample_count == 48 and len(sessions) == 3
profile_summary = {}
for language in ('mech', 'rust'):
    folder = STUDY / ('early-' + language + '-profile-v1')
    capture = read(folder / 'results.json')
    analysis = read(folder / 'main-analysis.json')
    assert capture['status'] == 'profile-captured' and capture['completed_output_verified']
    assert capture['source'] == capture['source_after'] == pilot['source']
    assert capture['script_sha256'] == process.sha(STUDY / 'early-profile.py')
    assert analysis['analysis_script_sha256'] == process.sha(STUDY / 'early-analysis.py')
    assert process.sha(folder / 'symbols.txt') == analysis['raw_symbols_sha256']
    assert process.sha(folder / 'symbols-demangled.txt') == analysis['demangled_symbols_sha256']
    assert len(capture['samples']) == len(capture['subjects']) == len(analysis['capture_inventory']) == 3
    assert process.sha(Path(capture['binary_path'])) == capture['binary_sha256']
    assert hashlib.sha256(text_section(Path(capture['binary_path']))).hexdigest() == capture['machine_code_sha256']
    main_count = 0
    for index, item in enumerate(capture['samples']):
        sample = folder / f'sample-{index}'
        assert process.sha(sample / 'stacks.txt') == item['stacks_sha256']
        subject = read(sample / 'subject/process.json')
        assert subject == capture['subjects'][index]['process']
        assert subject['birth_identity']['pid'] == item['pid'] and item['owned_direct_child']
        assert process.sha(sample / 'subject/stdout.bin') == OUTPUT_SHA
        if language == 'mech':
            native(sample / 'native.report.json', 'full')
        content = (sample / 'stacks.txt').read_text()
        assert f"[{item['pid']}]" in content.split('Call graph:\n', 1)[0]
        graph = content.split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
        has_stacks = bool(re.search(r'\d+ Thread_', graph))
        assert has_stacks == analysis['capture_inventory'][index]['has_stacks']
        if has_stacks:
            threads = stack_threads(content, {})
            main_threads = {t['thread'] for t in threads if t['main_thread']}
            total = sum(n for thread, _, n, _ in leaves(content) if thread in main_threads)
            assert total == sum(t['samples'] for t in threads if t['main_thread'])
            main_count += total
    assert main_count == analysis['main_observations']
    profile_summary[language] = dict(main_observations=main_count, captures=3,
        binary_sha256=capture['binary_sha256'], machine_code_sha256=capture['machine_code_sha256'])
mech_analysis = read(STUDY / 'early-mech-profile-v1/analysis.json')
assert mech_analysis['machine_code_identical'] and mech_analysis['completed_output_verified']
assert mech_analysis['timed_binary_sha256'] == baseline['candidate_sha256']
receipts = list(STUDY.rglob('process.json'))
for path in receipts:
    receipt = read(path)
    assert receipt['exit_status'] == 0 and receipt['reaped'] and receipt['group_closed'], path
    assert not receipt['cleanup_errors'] and not receipt.get('error') and receipt['inherited_common_mutex'], path
assert process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
result = dict(status='host-input-buffer-pilot-and-early-profiles-verified', source=pilot['source'],
    plan_sha256=pilot['plan_sha256'], verifier_sha256=process.sha(Path(__file__)),
    complete_process_timing_observations=sample_count, full_input_observations=32,
    prefix_observations=16, sessions=sessions, early_profiles=profile_summary,
    terminal_owned_process_receipts=len(receipts), canonical_data_sha256=DATA_SHA,
    decision='Retain all buffer variants and every observation. Full-session directions reverse and the largest buffer regresses the short-input cohort; leave the production default unchanged. Early full-input captures identify input preparation and final joining as further profiling targets without assigning stack counts to wall time.')
process.save(STUDY / 'verification.json', result)
print(json.dumps({k: result[k] for k in ['status', 'complete_process_timing_observations', 'terminal_owned_process_receipts']}))
