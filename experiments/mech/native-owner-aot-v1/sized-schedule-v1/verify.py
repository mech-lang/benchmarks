"""Recompute size-first scheduling timings, qualification and diagnostics."""
from collections import Counter
import hashlib
import json
import math
import random
import re
import statistics
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
DISPATCH = HERE.parent / 'native-owner-dispatch-v1'
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from binary import macho, function_ranges


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_output(folder, mode='full'):
    expected = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7' if mode == 'full' else 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
    assert sha(folder / 'stdout.bin') == expected


def check_native(path, mode='full'):
    native = read(path)
    assert native['native_aot'] and not native['jit'] and native['policy'] == 'secured'
    assert native['shutdown'] == 'completed' and not native['resident_body_evaluation']
    assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == (874999961 if mode == 'full' else 6999961)
    assert native['native_hash_table_regions'] == native['native_parallel_tasks'] == 7
    if mode == 'full':
        assert native['native_parallel_peak_workers'] == 7 and native['native_direct_lookup_regions'] == 5


plan = read(STUDY / 'plan.json')
source = plan['source_commit']
predeclared = subprocess.check_output(['git', '-C', str(HERE.parents[2]), 'show',
    'd4db1786bc451d650087f14300a8b2eb5e48afe8:experiments/mech/native-owner-aot-v1/sized-schedule-v1/plan.json'])
assert hashlib.sha256(predeclared).hexdigest() == sha(STUDY / 'plan.json')
prefix_folder = HERE / plan['receipt']
prefix = read(prefix_folder / 'results.json')
parent = read(HERE / plan['parent_receipt'] / 'results.json')
assert prefix['source_commit'] == source and prefix['status'] == 'all-outputs-and-update-counts-verified'
assert prefix['object_sha256'] == parent['object_sha256'] == 'f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335'
assert prefix['bytecode_sha256'] == parent['bytecode_sha256'] == '050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
assert prefix['source_sha256'] == parent['source_sha256'] == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
assert sha(prefix_folder / 'measure-stage-driver.py') == prefix['study_driver_sha256']
project = HERE / '.build' / (plan['binary'] + '.project')
parent_project = HERE / '.build' / (plan['parent_binary'] + '.project')
same_build_inputs = {}
for name in ('native-descriptor.bin', 'native-descriptor.json', 'native-resources.json', 'program.o', 'program.mecb', 'object-identity.bin'):
    assert sha(project / name) == sha(parent_project / name)
    same_build_inputs[name] = sha(project / name)
validation, roots = {}, [prefix_folder, HERE / plan['compiler']]
for label in ('parallel', 'native', 'catalog', 'focused'):
    folder = DISPATCH / (f'sized-schedule-{label}-v1' if label != 'focused' else 'sized-schedule-focused-v3')
    receipt = read(folder / 'process.json')
    provenance = read(folder / 'source-provenance.json')
    assert provenance['source_unchanged'] and provenance['clean_revision_qualified']
    assert provenance['before']['commit'] == provenance['after']['commit'] == source
    rows = re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;', (folder / 'stdout.bin').read_text())
    assert rows and not sum(int(r[1]) for r in rows)
    validation[label] = sum(int(r[0]) for r in rows)
    assert validation[label] > 0
    summary = dict(status='passed', passed=validation[label], ignored=sum(int(r[2]) for r in rows),
        source_commit=source, clean_revision_qualified=True,
        all_owned_processes_reaped_and_groups_closed=receipt['reaped'] and receipt['group_closed'] and not receipt['cleanup_errors'],
        process_sha256=sha(folder / 'process.json'), provenance_sha256=sha(folder / 'source-provenance.json'))
    if (folder / 'summary.json').exists():
        assert read(folder / 'summary.json') == summary
    else:
        (folder / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    roots.append(folder)
assert validation == {'parallel': 13, 'native': 381, 'catalog': 1, 'focused': 2}
sessions = []
for batch in (1, 2):
    folder = HERE / f'full-sized-schedule-v{batch}'
    report = read(folder / 'results.json')
    assert report['status'] == 'all-sized-schedule-full-outputs-updates-and-source-pins-verified'
    assert report['driver_sha256'] == sha(STUDY / 'measure.py') and report['plan_sha256'] == sha(STUDY / 'plan.json')
    assert report['input_sha256'] == sha(HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin') == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    assert report['policy_sha256'] == sha(HERE / 'full-disjoint-state-v1/launch.json') == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
    assert report['canonical_data_sha256'] == '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
    assert report['source'] == report['source_after'] and report['source']['commit'] == source and not report['source']['status']
    assert report['orders'] == (plan['orders'] if batch == 1 else list(reversed(plan['orders'])))
    assert len(report['samples']) == 18
    for position in range(3):
        assert Counter(row[position] for row in report['orders']) == {s: 2 for s in plan['subjects']}
    values = {s: [] for s in plan['subjects']}
    for index, row in enumerate(report['samples']):
        order, position = divmod(index, 3)
        subject = report['orders'][order][position]
        assert (row['order'], row['position'], row['subject']) == (order, position, subject)
        process_path = HERE / row['process']
        assert sha(process_path) == row['process_sha256']
        receipt = read(process_path)
        assert receipt['elapsed_seconds'] == row['seconds'] and receipt['maximum_rss_bytes'] == row['maximum_rss_bytes']
        assert receipt['quantitative_benchmark'] and sha(Path(receipt['command'][0])) == report['pins'][subject]
        check_output(process_path.parent)
        if subject != 'rust':
            assert sha(Path(receipt['command'][2])) == row['native_sha256']
            check_native(Path(receipt['command'][2]))
        values[subject].append(row)
    for subject, observations in values.items():
        assert len(observations) == 6
        assert statistics.median(r['seconds'] for r in observations) == report['median_seconds'][subject]
        assert statistics.median(r['maximum_rss_bytes'] for r in observations) == report['median_peak_rss_bytes'][subject]
        assert statistics.stdev(r['seconds'] for r in observations) == report['standard_deviation_seconds'][subject]
        assert report['median_seconds'][subject] / report['median_seconds']['rust'] == report['x_rust'][subject]
    ratios = [math.log(c['seconds'] / p['seconds']) for c, p in zip(values['candidate'], values['parent'])]
    rng = random.Random(2026102404 + batch)
    boot = sorted(statistics.median(rng.choices(ratios, k=6)) for _ in range(20000))
    assert report['paired_change_percent'] == 100 * math.expm1(statistics.median(ratios))
    assert report['paired_change_interval_95'] == [100 * math.expm1(boot[i]) for i in (499, 19499)]
    assert report['faster_matched_pairs'] == sum(x < 0 for x in ratios)
    sessions.append({k: report[k] for k in ['median_seconds', 'x_rust', 'median_peak_rss_bytes', 'paired_change_percent', 'paired_change_interval_95']})
    roots.append(folder)
build = read(HERE / 'profile-sized-schedule-build-v1/results.json')
assert build['source_commit'] == source and build['whole_machine_code_matches_timed']
assert build['candidate_object_sha256'] == prefix['object_sha256']
roots.append(HERE / 'profile-sized-schedule-build-v1')
for index in (1, 2, 3):
    folder = HERE / f'full-profile-sized-schedule-v{index}'
    profile = read(folder / 'analysis.json')
    assert profile['source_commit'] == source and profile['machine_code_identical'] and profile['completed_output_verified']
    assert profile['timed_binary_sha256'] == prefix['candidate_sha256']
    roots.append(folder)
partition = read(HERE / 'sized-schedule-full-remaining-profile-v1/results.json')
assert partition['script_sha256'] == sha(HERE / 'profile_hotspots.py')
for item in partition['evidence']:
    assert sha(HERE / item['path']) == item['sha256']
diagnostic_folder = HERE / 'sized-schedule-diagnostics-v1'
diagnostics = read(diagnostic_folder / 'results.json')
assert diagnostics['status'] == 'all-sized-schedule-diagnostic-outputs-and-exact-sizes-verified'
assert diagnostics['driver_sha256'] == sha(STUDY / 'diagnostics.py')
assert diagnostics['source'] == diagnostics['source_after'] == report['source']
for subject, parsed in diagnostics['binary'].items():
    assert parsed == macho(Path(parsed['path']))[0]
    assert parsed['sha256'] == report['pins'][subject]
assert function_ranges(Path(build['binary'])) == diagnostics['candidate_function_extents']
assert len(diagnostics['snapshots']) == 3 and len(diagnostics['counters']) == 9
for row in diagnostics['snapshots']:
    folder = diagnostic_folder / ('snapshot-' + row['subject'])
    assert sha(folder / 'memory-observations.json') == row['raw_sha256']
    assert read(folder / 'process.json') == row['process']
    check_output(folder)
    if row['subject'] != 'rust':
        check_native(diagnostic_folder / (folder.name + '.native.json'))
    raw = read(folder / 'memory-observations.json')
    assert all(raw['identity'][key] == row['process']['birth_identity'][key] for key in ('pid', 'ppid', 'birth_seconds', 'birth_microseconds'))
    for capture in raw['captures']:
        tool_folder = diagnostic_folder / (folder.name + '-' + capture['tool'])
        assert read(tool_folder / 'process.json') == capture['process']
        assert sha(tool_folder / 'stdout.bin') == capture['stdout_sha256']
        assert sha(tool_folder / 'stderr.bin') == capture['stderr_sha256']
    heap = (diagnostic_folder / (folder.name + '-heap') / 'stdout.bin').read_text()
    match = re.search(r'All zones: (\d+) nodes \((\d+) bytes\)', heap)
    assert (int(match[1]), int(match[2])) == (row['live_allocations'], row['live_allocated_bytes'])
for row in diagnostics['counters']:
    folder = diagnostic_folder / f"counter-{row['order']}-{row['subject']}"
    assert read(folder / 'process.json') == row['process']
    check_output(folder)
    if row['subject'] != 'rust':
        check_native(diagnostic_folder / (folder.name + '.native.json'))
    assert sha(folder / 'stderr.bin') == row['stderr_sha256']
    text = (folder / 'stderr.bin').read_text()
    for key, label in [('instructions', 'instructions retired'), ('cycles', 'cycles elapsed'), ('involuntary_context_switches', 'involuntary context switches')]:
        assert int(re.findall(r'^\s*(\d+)\s+' + label + r'\s*$', text, re.M)[0]) == row[key]
    times = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', text)
    assert [row[k] for k in ('real_seconds', 'user_seconds', 'system_seconds')] == [float(times[i]) for i in (1, 2, 3)]
for subject, medians in diagnostics['counter_medians'].items():
    for key, value in medians.items():
        assert statistics.median(r[key] for r in diagnostics['counters'] if r['subject'] == subject) == value
roots.append(diagnostic_folder)
# Preserve both unsuccessful fixture versions and prove their exact revisions.
failed_tests = {}
for version, commit in [(1, 'd18a2b3a1072209150e5c747f95b3f548456bbd3'), (2, 'a2810acf5754d962d7e453baf749be8ce1daa936')]:
    folder = DISPATCH / f'sized-schedule-focused-v{version}'
    provenance = read(folder / 'source-provenance.json')
    assert provenance['source_unchanged'] and provenance['clean_revision_qualified']
    assert provenance['before']['commit'] == provenance['after']['commit'] == commit
    assert read(folder / 'process.json')['exit_status'] == 101
    assert re.search(r'test result: FAILED\. 0 passed; 2 failed;', (folder / 'stdout.bin').read_text())
    failed_tests[folder / 'process.json'] = 101
    roots.append(folder)

# Three raw prearmed captures remain. One contains no stack observations.
prefolder = HERE / 'prefix-profile-sized-schedule-prearmed-v1'
capture = read(prefolder / 'results.json')
analysis = read(prefolder / 'analysis.json')
assert capture['status'] == 'profile-captured' and capture['completed_output_verified']
assert capture['source_commit'] == source and capture['object_sha256'] == prefix['object_sha256']
assert len(capture['samples']) == len(capture['subjects']) == 3
assert analysis['selected_capture_indices'] == [0, 2] and analysis['attempted_capture_count'] == 3
assert analysis['machine_code_identical'] and analysis['machine_code_sha256'] == diagnostics['binary']['candidate']['machine_code_sha256']
for i, item in enumerate(capture['samples']):
    raw = prefolder / f'sample-{i}' / 'stacks.txt'
    assert sha(raw) == item['stacks_sha256']
    text = raw.read_text()
    assert f"(pid {item['pid']})" in text and item['owned_direct_child']
    graph = text.split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    assert bool(re.search(r'\d+ Thread_', graph)) == (i != 1)
    check_output(prefolder / f'sample-{i}' / 'subject', 'prefix')
    check_native(prefolder / f'sample-{i}' / 'native.report.json', 'prefix')
roots.append(prefolder)
for part in ['sized-schedule-full-remaining-profile-v1', 'sized-schedule-prefix-remaining-profile-v2']:
    r = read(HERE / part / 'results.json')
    assert r['script_sha256'] == sha(HERE / 'profile_hotspots.py')
    for item in r['evidence']:
        assert sha(HERE / item['path']) == item['sha256']

# The earlier normal attachment missed a successfully completed short subject.
missed = HERE / 'prefix-profile-sized-schedule-v1'
check_output(missed / 'subject', 'prefix')
subject = read(missed / 'subject/process.json')
assert subject['exit_status'] == 0 and subject['error'] == "[Errno 2] No such file or directory: '/private/tmp/mech-benchmark-publication/experiments/mech/native-owner-aot-v1/prefix-profile-sized-schedule-v1/sample-0/stacks.txt'"
assert not (missed / 'sample-0/stacks.txt').exists()
roots.append(missed)

# Counters and thread polling are separate diagnostic executions.
pcfolder = HERE / 'sized-schedule-prefix-counters-v1'
pc = read(pcfolder / 'results.json')
assert pc['status'] == 'all-prefix-counter-outputs-and-physical-updates-verified'
assert pc['source'] == pc['source_after'] == report['source']
assert pc['driver_sha256'] == sha(STUDY / 'prefix-counters.py') and len(pc['observations']) == 9
for row in pc['observations']:
    folder = pcfolder / f"{row['order']}-{row['subject']}"
    assert read(folder / 'process.json') == row['process']
    check_output(folder, 'prefix')
    if row['subject'] != 'rust':
        check_native(pcfolder / (folder.name + '.native.json'), 'prefix')
    assert sha(folder / 'stderr.bin') == row['stderr_sha256']
    raw = (folder / 'stderr.bin').read_text()
    for key, label in [('instructions', 'instructions retired'), ('cycles', 'cycles elapsed'), ('maximum_rss_bytes', 'maximum resident set size')]:
        assert int(re.findall(r'^\s*(\d+)\s+' + label + r'\s*$', raw, re.M)[0]) == row[key]
roots.append(pcfolder)
tfolder = HERE / 'sized-schedule-thread-lifetimes-v1'
t = read(tfolder / 'results.json')
assert t['status'] == 'all-owned-thread-observations-and-outputs-verified' and len(t['subjects']) == 6
assert t['driver_sha256'] == sha(STUDY / 'thread-driver.py')
assert all(t['source'][key] == report['source'][key] for key in ('commit', 'status'))
for folder in tfolder.iterdir():
    if folder.is_dir() and (folder / 'process.json').exists():
        check_output(folder)
        if not folder.name.endswith('rust'):
            check_native(tfolder / (folder.name + '.native.json'))
roots.append(tfolder)

processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes:
            continue
        processes.add(path)
        receipt = read(path)
        assert receipt['exit_status'] == failed_tests.get(path, 0) and receipt['reaped'] and receipt['group_closed'], path
        assert receipt['inherited_common_mutex'] and not receipt['cleanup_errors'], path
        if path != missed / 'subject/process.json':
            assert not receipt.get('error'), path
assert sha(HERE.parents[2] / 'data/benchmarks.json') == report['canonical_data_sha256']
assert Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
result = dict(status='sized-scheduling-study-verified', source_commit=source, parent_source_commit=plan['parent_source_commit'],
    verifier_sha256=sha(Path(__file__)), plan_sha256=sha(STUDY / 'plan.json'), validation=validation,
    validation_passes=sum(validation.values()), same_build_inputs=same_build_inputs,
    sessions=sessions, primary_full_input_processes=36, failed_fixture_versions_retained=2,
    prefix_profile_captures=3, prefix_captures_with_stacks=2, failed_normal_attachment_retained=True,
    terminal_owned_processes=len(processes), canonical_data_sha256=report['canonical_data_sha256'],
    decision='Retain the scheduling factor on its pushed branch. Both paired intervals include zero; marginal medians reverse direction in the repeat. No repeatable gain or Rust parity is established.')
(STUDY / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'validation_passes', 'primary_full_input_processes', 'terminal_owned_processes']}))
