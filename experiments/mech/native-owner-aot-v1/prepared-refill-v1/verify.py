"""Recompute prepared-refill timings, qualification and diagnostics."""
from collections import Counter
import fcntl
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


mutex = Path('/private/tmp/mech-clbg-timing.lock').open('a+')
fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
plan = read(STUDY / 'plan.json')
source = plan['source_commit']
predeclared = subprocess.check_output(['git', '-C', str(HERE.parents[2]), 'show',
    'cef716ce863d0747e282643a295f262f11d1d436:experiments/mech/native-owner-aot-v1/prepared-refill-v1/plan.json'])
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
for label in ('native', 'catalog', 'focused'):
    folder = DISPATCH / f'prepared-refill-{label}-v1'
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
assert validation == {'native': 385, 'catalog': 1, 'focused': 2}
sessions = []
for batch in (1, 2):
    folder = HERE / f'full-prepared-refill-v{batch}'
    report = read(folder / 'results.json')
    assert report['status'] == 'all-prepared-refill-full-outputs-updates-and-source-pins-verified'
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
    rng = random.Random(2026102508 + batch)
    boot = sorted(statistics.median(rng.choices(ratios, k=6)) for _ in range(20000))
    assert report['paired_change_percent'] == 100 * math.expm1(statistics.median(ratios))
    assert report['paired_change_interval_95'] == [100 * math.expm1(boot[i]) for i in (499, 19499)]
    assert report['faster_matched_pairs'] == sum(x < 0 for x in ratios)
    sessions.append({k: report[k] for k in ['median_seconds', 'x_rust', 'median_peak_rss_bytes', 'paired_change_percent', 'paired_change_interval_95']})
    roots.append(folder)
build = read(HERE / 'profile-prepared-refill-build-v1/results.json')
assert build['source_commit'] == source and build['whole_machine_code_matches_timed']
assert build['candidate_object_sha256'] == prefix['object_sha256']
roots.append(HERE / 'profile-prepared-refill-build-v1')
for index in (1, 2, 3):
    folder = HERE / f'full-profile-prepared-refill-v{index}'
    profile = read(folder / 'analysis.json')
    assert profile['source_commit'] == source and profile['machine_code_identical'] and profile['completed_output_verified']
    assert profile['timed_binary_sha256'] == prefix['candidate_sha256']
    roots.append(folder)
partition = read(HERE / 'prepared-refill-full-remaining-profile-v1/results.json')
assert partition['script_sha256'] == sha(HERE / 'profile_hotspots.py')
for item in partition['evidence']:
    assert sha(HERE / item['path']) == item['sha256']
diagnostic_folder = HERE / 'prepared-refill-diagnostics-v1'
diagnostics = read(diagnostic_folder / 'results.json')
assert diagnostics['status'] == 'all-prepared-refill-diagnostic-outputs-and-exact-sizes-verified'
assert diagnostics['driver_sha256'] == sha(STUDY / 'diagnostics.py')
assert diagnostics['source'] == diagnostics['source_after'] == report['source']
for subject, parsed in diagnostics['binary'].items():
    assert parsed == macho(Path(parsed['path']))[0]
    assert parsed['sha256'] == report['pins'][subject]
assert function_ranges(Path(build['binary'])) == diagnostics['candidate_function_extents']
assert len(diagnostics['snapshots']) == 0 and len(diagnostics['counters']) == 9
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
# Prefix counters are separate diagnostic executions.
pcfolder = HERE / 'prepared-refill-prefix-counters-v1'
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
audit_folder = STUDY / 'code-audit'
audit = read(audit_folder / 'results.json')
assert audit['status'] == 'exact-refill-code-and-quote-layout-verified'
assert audit['source'] == audit['source_after'] == report['source']
assert audit['driver_sha256'] == sha(STUDY / 'audit.py')
for label, record in audit['records'].items():
    stem = 'prepared-refill' if label == 'candidate' else 'packed-domain-validation'
    profile_build = read(HERE / f'profile-{stem}-build-v1/results.json')
    assert record['binary_sha256'] == profile_build['binary_sha256']
    # Symbol-preserving files differ in file bytes from their shipped copies;
    # their entire machine-code section must match the respective timed file.
    assert record['machine_code_sha256'] == diagnostics['binary'][label]['machine_code_sha256']
    for index, function in enumerate(record['functions']):
        path = HERE / function['retained']
        assert sha(path) == function['retained_sha256']
        raw = audit_folder / f'{label}-assembly-{index}' / 'stdout.bin'
        assert sha(raw) == function['raw_output_sha256']
        lines = raw.read_text().splitlines()
        start = lines.index(function['symbol'] + ':')
        end = next((i for i in range(start + 1, len(lines)) if lines[i].endswith(':')), len(lines))
        assert path.read_text() == '\n'.join(lines[start:end]) + '\n'
        instructions = [(m[1], m[2]) for line in lines[start + 1:end]
            if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))]
        assert len(instructions) == function['instructions']
        assert function['divisions'] == [dict(address=at, instruction=text) for at, text in instructions if text.startswith('udiv')]
assert audit['quote_layout']['new_bytes'] == 40 and audit['quote_layout']['old_bytes'] == 72
assert sha(audit_folder / 'type-layout.rs') == audit['quote_layout']['harness_sha256']
assert sha(Path('/private/tmp/mech-native-hashmap-performance/hosts/gpu/src/native_artifact/program_packed_fuel.rs')) == audit['quote_layout']['actual_new_source_sha256']
assert (audit_folder / 'type-layout-run/stdout.bin').read_text().strip() == '40 72'
roots.append(audit_folder)
processes = set()
for root in roots:
    for path in root.rglob('process.json'):
        if path in processes:
            continue
        processes.add(path)
        receipt = read(path)
        assert receipt['exit_status'] == 0 and receipt['reaped'] and receipt['group_closed'], path
        assert receipt['inherited_common_mutex'] and not receipt['cleanup_errors'], path
        assert not receipt.get('error'), path
assert sha(HERE.parents[2] / 'data/benchmarks.json') == report['canonical_data_sha256']
assert Path('/private/tmp/mech-clbg-timing.lock').stat().st_ino == 83858837
antecedent = read(STUDY / 'retained-antecedent.json')
assert antecedent['original_plan_sha256'] == sha(STUDY / 'plan.json')
assert antecedent['recorded_before_new_full_input_observations']
assert antecedent['antecedent_source_commit'] == '36a0d26e05b92f0f3fb21bdbd3605af2108ec882'
antecedent_path = Path(antecedent['antecedent_checkpoint'])
if not antecedent_path.is_absolute():
    antecedent_path = HERE.parents[2] / antecedent_path
assert sha(antecedent_path) == antecedent['antecedent_checkpoint_sha256']
assert read(antecedent_path)['evidence']['refill-fastpath']['batches'] == antecedent['antecedent_result']
result = dict(status='prepared-refill-study-verified', source_commit=source, parent_source_commit=plan['parent_source_commit'],
    verifier_sha256=sha(Path(__file__)), plan_sha256=sha(STUDY / 'plan.json'), validation=validation,
    validation_passes=sum(validation.values()), same_build_inputs=same_build_inputs,
    sessions=sessions, primary_full_input_processes=36,
    terminal_owned_processes=len(processes), canonical_data_sha256=report['canonical_data_sha256'],
    decision='Report both separately balanced sessions, confidence intervals and counters. This is a smaller-quote interaction retest of the retained full-refill idea; preserve both prior outcomes and every earlier factor independently.')
(STUDY / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status', 'validation_passes', 'primary_full_input_processes', 'terminal_owned_processes']}))
