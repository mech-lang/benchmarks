"""Verify the complete native aligned-probe trial and its separate diagnostics."""
from collections import Counter
import fcntl
from pathlib import Path
import re
import statistics
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import text_section
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, OUTPUT_SHA, DATA_SHA


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    dispatch = HERE.parent / 'native-owner-dispatch-v1'
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        folders = [STUDY, HERE / plan['compiler'], HERE / plan['receipt'],
                   HERE / 'profile-aligned-probe-groups-build-v1']
        folders += [HERE / f'full-aligned-probe-groups-v{i}' for i in (1, 2)]
        folders += [dispatch / f'aligned-probe-groups-{label}-v1' for label in ('focused', 'native', 'catalog')]
        receipts = sorted({p for folder in folders for p in folder.rglob('process.json')})
        assert len(receipts) == 90, len(receipts)
        for path in receipts:
            row = read(path)
            assert row['exit_status'] == 0 and row['reaped'] and row['group_closed'], path
            assert row['inherited_common_mutex'] and not row['cleanup_errors'] and not row['signals'], path
            assert not row.get('error') and not row.get('timed_out'), path
        counts = {}
        for label, expected in [('focused', 2), ('native', 387), ('catalog', 1)]:
            folder = dispatch / f'aligned-probe-groups-{label}-v1'
            p = read(folder / 'source-provenance.json')
            assert p['clean_revision_qualified'] and p['before']['commit'] == before['commit']
            found = re.findall(r'test result: ok\. (\d+) passed; 0 failed;', (folder / 'stdout.bin').read_text())
            assert sum(map(int, found)) == expected
            counts[label] = expected
        prefix = read(HERE / plan['receipt'] / 'results.json')
        assert prefix['status'] == 'all-outputs-and-update-counts-verified' and len(prefix['samples']) == 9
        assert prefix['source_commit'] == before['commit']
        assert prefix['study_driver_sha256'] == process.sha(STUDY / 'measure-stage-driver.py')
        for path in (HERE / plan['receipt']).glob('*/stdout.bin'):
            if path.parent.name != 'build':
                assert process.sha(path) == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
        sessions = []
        for batch in (1, 2):
            folder = HERE / f'full-aligned-probe-groups-v{batch}'
            report = read(folder / 'results.json')
            assert report['status'] == 'all-aligned-probe-groups-full-outputs-updates-and-source-pins-verified'
            assert report['source'] == report['source_after'] == before and len(report['samples']) == 18
            assert report['plan_sha256'] == process.sha(STUDY / 'plan.json')
            for row in report['samples']:
                path = HERE / row['process']
                assert process.sha(path) == row['process_sha256'] and process.sha(path.parent / 'stdout.bin') == OUTPUT_SHA
                if row['subject'] != 'rust':
                    native = folder / (path.parent.name + '.native.json')
                    check_native(native)
                    assert not read(native)['resident_body_evaluation']
                    assert process.sha(native) == row['native_sha256']
            sessions.append({k: report[k] for k in ('session', 'median_seconds', 'x_rust', 'paired_change_percent',
                                                    'paired_change_interval_95', 'median_change_percent', 'faster_matched_pairs')})
        project = HERE / '.build' / (plan['binary'] + '.project')
        parent = HERE / '.build' / (plan['parent_binary'] + '.project')
        for name in ('program.mecb', 'native-resources.json'):
            assert process.sha(project / name) == process.sha(parent / name)
        manifest = read(project / 'linked-manifest.json')['object']
        assert (manifest['typed_ir_version'], manifest['abi_version'], manifest['work_policy_version']) == (80, 28, 67)
        profile = read(HERE / 'profile-aligned-probe-groups-build-v1/results.json')
        assert text_section(Path(profile['binary'])) == text_section(HERE / '.build' / plan['binary'])
        for language in ('mech', 'rust'):
            folder = STUDY / ('early-' + language + '-profile-v1')
            report = read(folder / 'results.json')
            assert report['status'] == 'profile-captured' and report['completed_output_verified']
            assert report['source'] == report['source_after'] == before
            assert len(report['samples']) == len(report['subjects']) == 3
            for i, sample in enumerate(report['samples']):
                path = folder / f'sample-{i}' / 'stacks.txt'
                assert process.sha(path) == sample['stacks_sha256']
                assert sample['pid'] == report['subjects'][i]['process']['birth_identity']['pid']
                assert process.sha(path.parent / 'subject/stdout.bin') == OUTPUT_SHA
                if language == 'mech':
                    check_native(path.parent / 'native.report.json')
        analysis = read(STUDY / 'analysis.json')
        assert analysis['status'] == 'exact-current-binary-observations-partitioned'
        pair = Counter()
        for index in range(3):
            selected = sorted([r for r in analysis['languages']['mech']['workers'] if r['sample'] == index],
                              key=lambda r: r['observations'], reverse=True)[:2]
            assert all('packed_loop_284_funded' in r['top_symbols'][0]['symbol'] for r in selected)
            for row in selected:
                pair.update(row['buckets'])
        counters = read(STUDY / 'counters/results.json')
        assert len(counters['counters']) == 9 and counters['source'] == counters['source_after'] == before
        threads = read(STUDY / 'thread-observations-v2/results.json')
        assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified' and len(threads['subjects']) == 9
        thread_summary = {}
        for subject in ('mech', 'baseline', 'rust'):
            values = []
            for i, row in enumerate(threads['subjects']):
                if row['subject'] != subject:
                    continue
                folder = STUDY / 'thread-observations-v2' / f'{i}-{subject}'
                assert process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                assert process.sha(folder / 'thread-observations.json') == row['raw_sha256']
                if subject != 'rust':
                    check_native(folder.parent / (folder.name + '.native.json'))
                main = next(t for t in row['threads'] if 'main' in t['names'])
                workers = [t for t in row['threads'] if t is not main and t['handle'] != 0
                           and t['user_ns'] + t['system_ns'] > 10_000_000]
                assert len(workers) == 7
                values.append(dict(first_worker_seen_seconds=min(t['first_seen'] for t in workers),
                    main_cpu_seconds_lower_bound=(main['user_ns'] + main['system_ns']) / 1e9,
                    largest_worker_cpu_seconds_lower_bound=max((t['user_ns'] + t['system_ns']) / 1e9 for t in workers)))
            thread_summary[subject] = dict(samples=values, medians={k: statistics.median(r[k] for r in values) for k in values[0]})
        audit = read(STUDY / 'code-audit/results.json')
        assert audit['status'] == 'exact-probe-assembly-retained' and audit['source'] == audit['source_after'] == before
        for label, data in audit['records'].items():
            for function in data['functions']:
                assert process.sha(HERE / function['retained']) == function['retained_sha256']
        assert source_state() == before and process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
        result = dict(status='aligned-probe-native-study-verified', source=before,
            terminal_processes=len(receipts), test_executions=counts, sessions=sessions,
            thread_summary=thread_summary, critical_pair_observations=sum(pair.values()),
            critical_pair_percent={k: 100 * n / sum(pair.values()) for k, n in pair.items()},
            code_identity=dict(typed_ir=80, abi=28, work_policy=67, machine_code_sha256=profile['machine_code_sha256']),
            retained_controller_failure='First thread driver named the earlier prepared-refill parent. Hash guard stopped before any subject launched. Corrected version uses the actual shared-String-fact parent; no successful native run was repeated.',
            verifier_sha256=process.sha(Path(__file__)), benchmark_samples=0,
            scope='Primary sessions, hardware counters, thread endpoints and sampled stack observations remain separate. Source and protected benchmark data are unchanged after execution.')
        process.save(STUDY / 'verification.json', result)
        print('Verified', len(receipts), 'owned terminal processes;', counts, flush=True)


if __name__ == '__main__':
    main()
