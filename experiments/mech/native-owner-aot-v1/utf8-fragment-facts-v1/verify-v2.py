"""Verify the complete native fragment fact trial and its separate diagnostics."""
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
                   HERE / 'profile-utf8-fragment-facts-build-v1']
        folders += [HERE / f'full-utf8-fragment-facts-v{i}' for i in (1, 2)]
        folders += [dispatch / f'utf8-fragment-facts-{label}-v1' for label in ('engine', 'native', 'catalog')]
        receipts = sorted({p for folder in folders for p in folder.rglob('process.json')})
        assert len(receipts) == 91, len(receipts)
        for path in receipts:
            row = read(path)
            assert row['exit_status'] == 0 and row['reaped'] and row['group_closed'], path
            assert row['inherited_common_mutex'] and not row['cleanup_errors'] and not row['signals'], path
            assert not row.get('error') and not row.get('timed_out'), path
        counts = {}
        for label, expected in [('engine', 24), ('native', 387), ('catalog', 1)]:
            folder = dispatch / f'utf8-fragment-facts-{label}-v1'
            p = read(folder / 'source-provenance.json')
            assert p['clean_revision_qualified'] and p['before']['commit'] == before['commit']
            found = re.findall(r'test result: ok\. (\d+) passed; 0 failed;', (folder / 'stdout.bin').read_text())
            assert sum(map(int, found)) == expected
            counts[label] = expected
        for component, expected in [('core', 2), ('runtime', 9)]:
            folder = STUDY / (component + '-validation-v1')
            provenance = read(folder / 'source-provenance.json')
            assert provenance['source_unchanged'] and provenance['before'] == before
            found = re.findall(r'test result: ok\. (\d+) passed; 0 failed;', (folder / 'stdout.bin').read_text())
            assert sum(map(int, found)) == expected
            counts[component] = expected
        prefix = read(HERE / plan['receipt'] / 'results.json')
        assert prefix['status'] == 'all-outputs-and-update-counts-verified' and len(prefix['samples']) == 9
        assert prefix['source_commit'] == before['commit']
        assert prefix['study_driver_sha256'] == process.sha(STUDY / 'measure-stage-driver.py')
        for path in (HERE / plan['receipt']).glob('*/stdout.bin'):
            if path.parent.name != 'build':
                assert process.sha(path) == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
        sessions = []
        for batch in (1, 2):
            folder = HERE / f'full-utf8-fragment-facts-v{batch}'
            report = read(folder / 'results.json')
            assert report['status'] == 'all-utf8-fragment-facts-full-outputs-updates-and-source-pins-verified'
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
        profile = read(HERE / 'profile-utf8-fragment-facts-build-v1/results.json')
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
            assert len(selected) == 2
            for row in selected:
                pair.update(row['buckets'])
        counters = read(STUDY / 'counters/results.json')
        assert len(counters['counters']) == 9 and counters['source'] == counters['source_after'] == before
        threads = read(STUDY / 'thread-observations/results.json')
        assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified' and len(threads['subjects']) == 9
        thread_summary = {}
        for subject in ('mech', 'baseline', 'rust'):
            values = []
            for i, row in enumerate(threads['subjects']):
                if row['subject'] != subject:
                    continue
                folder = STUDY / 'thread-observations' / f'{i}-{subject}'
                assert process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                assert process.sha(folder / 'thread-observations.json') == row['raw_sha256']
                if subject != 'rust':
                    check_native(folder.parent / (folder.name + '.native.json'))
                main = next(t for t in row['threads'] if 'main' in t['names'])
                workers = [t for t in row['threads'] if t is not main and t['handle'] != 0
                           and t['user_ns'] + t['system_ns'] > 10_000_000]
                assert len(workers) == 7
                values.append(dict(first_worker_seen_seconds=min(t['first_seen'] for t in workers),
                    last_worker_first_seen_seconds=max(t['first_seen'] for t in workers),
                    worker_first_sighting_spread_seconds=max(t['first_seen'] for t in workers) - min(t['first_seen'] for t in workers),
                    main_cpu_seconds_lower_bound=(main['user_ns'] + main['system_ns']) / 1e9,
                    largest_worker_cpu_seconds_lower_bound=max((t['user_ns'] + t['system_ns']) / 1e9 for t in workers)))
            thread_summary[subject] = dict(samples=values, medians={k: statistics.median(r[k] for r in values) for k in values[0]})
        audit = read(STUDY / 'code-audit/results.json')
        assert audit['status'] == 'exact-fragment-fact-assembly-retained' and audit['source'] == audit['source_after'] == before
        assert audit['guest_object_unchanged']
        assert process.sha(STUDY / 'code-audit/byte-facts.s') == audit['retained_sha256']
        corrected = read(STUDY / 'code-audit/analysis-v2.json')
        assert corrected['source'] == corrected['source_after'] == before
        assert corrected['original_audit_sha256'] == process.sha(STUDY / 'code-audit/results.json')
        assert corrected['retained_sha256'] == audit['retained_sha256'] and corrected['native_processes_launched'] == 0
        assert corrected['vector_instructions'] and corrected['vector_load_instructions']
        assert source_state() == before and process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA
        result = dict(status='fragment-facts-native-study-verified', source=before,
            terminal_processes=len(receipts), test_executions=counts, sessions=sessions,
            thread_summary=thread_summary, critical_pair_observations=sum(pair.values()),
            critical_pair_percent={k: 100 * n / sum(pair.values()) for k, n in pair.items()},
            code_identity=dict(typed_ir=80, abi=28, work_policy=67, machine_code_sha256=profile['machine_code_sha256']),
            guest_object_unchanged=audit['guest_object_unchanged'], vector_instruction_count=len(corrected['vector_instructions']),
            verifier_sha256=process.sha(Path(__file__)), benchmark_samples=0,
            scope='Primary sessions, hardware counters, thread endpoints and sampled stack observations remain separate. Source and protected benchmark data are unchanged after execution.')
        process.save(STUDY / 'verification-v2.json', result)
        print('Verified', len(receipts), 'owned terminal processes;', counts, flush=True)


if __name__ == '__main__':
    main()
