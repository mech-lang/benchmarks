#!/usr/bin/env python3
"""Verify all raw published-head changed-input receipts without collecting timings."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/private/tmp/benchmarks-native-consolidation')
BASE = ROOT / 'experiments/mech/native-owner-aot-v1'
CODE = BASE / 'native-architecture-consolidation-v1'
DRIVER = CODE / 'changed-inputs.py'
OWNER = ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py'
RETAINED = Path('/private/tmp/mech-benchmark-publication')
POLICY = RETAINED / 'experiments/mech/native-owner-aot-v1/full-disjoint-state-v1/launch.json'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state(workspace):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args], text=True).strip()
    return dict(commit=git('rev-parse', 'HEAD'), tree=git('rev-parse', 'HEAD^{tree}'), status=git('status', '--porcelain'))


births = set()
for study, run_id in [('native-architecture-consolidation-v1', 'published-7543c56-v1'),
                      ('post-native-architecture-cleanup-v1', 'published-a68fb2e-v1')]:
    here = BASE / study
    out = here / ('changed-inputs-' + run_id)
    result = out / 'results.json'
    report, plan = read(result), read(here / 'plan.json')
    assert report['study_id'] == study and report['status'] == 'seven-independent-oracles-and-fourteen-pinned-AOT-executions-verified'
    assert report['benchmark_samples'] == 0 and report['driver_sha256'] == sha(DRIVER)
    assert len(report['cases']) == 7
    assert [row['name'] for row in report['cases']] == ['one-key-short', 'query-boundaries', 'random-single-row', 'random-short-rows', 'random-ordinary-rows', 'growth-and-partial-credit', 'repeated-wide-key']
    before = plan['baseline_receipt']
    baseline = BASE / before['study_id'] / before['path'] if isinstance(before, dict) else here / before
    if isinstance(before, dict):
        assert sha(baseline) == before['sha256']
    receipts = dict(I=read(baseline), F=read(here / plan['candidate_receipt']))
    for subject, receipt in receipts.items():
        assert receipt['source'] == state(receipt['workspace']) and not receipt['source']['status']
        assert receipt['executable_sha256'] == report['pins'][subject] == sha(receipt['executable'])
    assert report['source'] == report['source_after'] == receipts['F']['source']
    assert sha(POLICY) == plan['policy_sha256']
    process_pins = []
    for row in report['cases']:
        case = out / row['name']
        assert sha(case / 'input.fasta') == row['input_sha256']
        assert sha(case / 'expected.stdout') == row['expected_stdout_sha256']
        expected_updates = sum(max(0, row['bases'] - width + 1) for width in (1, 2, 3, 4, 6, 12, 18))
        assert expected_updates == row['expected_updates']
        assert [item['subject'] for item in row['executions']] == ['F', 'I']
        for item in row['executions']:
            subject = item['subject']
            path = case / subject / 'process.json'
            raw = read(path)
            native_path = case / (subject + '.native.json')
            command = [receipts[subject]['executable'], str(POLICY), str(native_path), '--']
            assert raw['command'] == command and sha(path) == item['process_sha256']
            assert raw['exit_status'] == 0 and raw['deadline_seconds'] == 30
            assert raw['group_closed'] is True and raw['reaped'] is True
            assert raw['cleanup_errors'] == raw['signals'] == []
            assert raw['inherited_common_mutex'] is True and raw['quantitative_benchmark'] is False
            assert raw['controller_sha256'] == sha(OWNER)
            assert not raw.get('error') and not raw.get('observer_still_waiting')
            birth = raw['birth_identity']
            identity = (birth['pid'], birth['birth_seconds'], birth['birth_microseconds'])
            assert identity not in births
            births.add(identity)
            assert (case / subject / 'stdout.bin').read_bytes() == (case / 'expected.stdout').read_bytes()
            assert sha(case / subject / 'stdout.bin') == item['stdout_sha256'] == row['expected_stdout_sha256']
            assert (case / subject / 'stderr.bin').is_file()
            assert sha(native_path) == item['native_sha256']
            native = read(native_path)
            assert native['native_aot'] is True and native['jit'] is False
            assert native['policy'] == 'secured' and native['shutdown'] == 'completed'
            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == expected_updates == item['updates']
            assert native['native_parallel_tasks'] == 7 and native['native_fused_string_map_bytes'] == row['bases']
            process_pins.append(dict(path=str(path.relative_to(here)), sha256=sha(path)))
    shutil.copyfile(DRIVER, out / 'executed-driver.py')
    shutil.copyfile(__file__, out / 'independent-validation.py')
    (out / 'independent-validation.json').write_text(json.dumps(dict(
        status='all-seven-cases-and-fourteen-owned-published-AOT-processes-verified',
        study_id=study, source={s: r['source'] for s, r in receipts.items()},
        results_sha256=sha(result), driver_sha256=sha(DRIVER), process_controller_sha256=sha(OWNER),
        validator_sha256=sha(__file__), policy_sha256=sha(POLICY),
        runtime_environment_receipt=plan['runtime_environment_receipt'],
        executable_pins=report['pins'], processes=process_pins, primary_timing_samples=0,
        performance_qualified=False), indent=2) + '\n')
    print(study, '7 direct-oracle cases /14 raw processes validated', flush=True)
assert len(births) == 28
