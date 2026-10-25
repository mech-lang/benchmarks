"""Verify the shared String-fact trial without pooling its diagnostic runs."""
from collections import Counter
import fcntl
from pathlib import Path
import statistics
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import text_section
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, read, process, source_state, check_native, OUTPUT_SHA, DATA_SHA


def main():
    plan = read(STUDY / 'execution-plan.json')
    before = source_state()
    assert not before['status']
    production = read(HERE / 'full-shared-string-facts-v1/results.json')['source']
    assert production['commit'] == plan['source_commit']
    changes = subprocess.check_output(['git', '-C', '/private/tmp/mech-native-hashmap-performance',
        'diff', '--name-only', plan['source_commit'], before['commit']], text=True).splitlines()
    assert set(changes) == {'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
                            'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs'}
    dispatch = HERE.parent / 'native-owner-dispatch-v1'
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locations = [STUDY, HERE / plan['compiler'], HERE / plan['reuse_build_receipt'],
                     HERE / plan['receipt'], HERE / 'profile-shared-string-facts-build-v1']
        locations += [HERE / f'full-shared-string-facts-v{i}' for i in (1, 2)]
        locations += [dispatch / f'shared-string-facts-{label}-v1' for label in ('focused', 'native', 'catalog', 'line-policy', 'map-policy')]
        receipts = sorted({p for folder in locations for p in folder.rglob('process.json')})
        assert len(receipts) >= 91
        for path in receipts:
            r = read(path)
            expected_exit = 101 if path == dispatch / 'shared-string-facts-native-v1/process.json' else 0
            assert r['exit_status'] == expected_exit and r['group_closed'] and r['reaped'], path
            assert r['inherited_common_mutex'] and not r['cleanup_errors'] and not r['signals'], path
            assert not r.get('error') and not r.get('timed_out'), path
        assert read(STUDY / 'core-validation-v1/source-provenance.json')['source_unchanged']
        core_text = (STUDY / 'core-validation-v1/stdout.bin').read_text()
        assert '44 passed; 0 failed' in core_text
        test_counts = dict(core=44)
        for label in ('focused', 'catalog', 'line-policy', 'map-policy'):
            folder = dispatch / f'shared-string-facts-{label}-v1'
            provenance = read(folder / 'source-provenance.json')
            assert provenance['clean_revision_qualified']
            assert provenance['before']['commit'] == (before['commit'] if label.endswith('-policy') else production['commit'])
            import re
            matches = re.findall(r'test result: ok\. (\d+) passed; 0 failed;', (folder / 'stdout.bin').read_text())
            assert matches
            test_counts[label] = sum(map(int, matches))
        failed_native = (dispatch / 'shared-string-facts-native-v1/stdout.bin').read_text()
        assert '383 passed; 2 failed; 3 ignored' in failed_native
        test_counts['native_initial_passed'] = 383
        test_counts['native_initial_failed_version_assertions'] = 2
        prefix = read(HERE / plan['receipt'] / 'results.json')
        assert prefix['status'] == 'all-outputs-and-update-counts-verified'
        assert prefix['source_commit'] == production['commit'] and len(prefix['samples']) == 9
        assert prefix['study_driver_sha256'] == process.sha(STUDY / 'measure-stage-driver.py')
        for path in (HERE / plan['receipt']).glob('*/stdout.bin'):
            assert process.sha(path) == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
        full = []
        for batch in (1, 2):
            folder = HERE / f'full-shared-string-facts-v{batch}'
            report = read(folder / 'results.json')
            assert report['status'] == 'all-shared-string-facts-full-outputs-updates-and-source-pins-verified'
            assert report['source'] == report['source_after'] == production and len(report['samples']) == 18
            assert report['plan_sha256'] == process.sha(STUDY / 'execution-plan.json')
            for row in report['samples']:
                path = HERE / row['process']
                assert process.sha(path) == row['process_sha256'] and process.sha(path.parent / 'stdout.bin') == OUTPUT_SHA
                if row['subject'] != 'rust':
                    native = folder / (path.parent.name + '.native.json')
                    check_native(native)
                    assert process.sha(native) == row['native_sha256']
            full.append({k: report[k] for k in ('session', 'median_seconds', 'x_rust', 'paired_change_percent',
                                               'paired_change_interval_95', 'median_change_percent')})
        profile = read(HERE / 'profile-shared-string-facts-build-v1/results.json')
        assert text_section(Path(profile['binary'])) == text_section(HERE / '.build' / plan['binary'])
        for language in ('mech', 'rust'):
            folder = STUDY / ('early-' + language + '-profile-v1')
            report = read(folder / 'results.json')
            assert report['status'] == 'profile-captured' and report['completed_output_verified']
            assert report['source'] == report['source_after'] == production
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
        counters = read(STUDY / 'counters/results.json')
        assert counters['status'] == 'all-shared-string-fact-diagnostic-outputs-and-exact-sizes-verified'
        assert len(counters['counters']) == 9
        threads = read(STUDY / 'thread-observations/results.json')
        assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified' and len(threads['subjects']) == 9
        thread_summary = {}
        for subject in ('mech', 'baseline', 'rust'):
            rows = []
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
                rows.append(dict(first_worker_seen_seconds=min(t['first_seen'] for t in workers),
                    main_cpu_seconds_lower_bound=(main['user_ns'] + main['system_ns']) / 1e9,
                    largest_worker_cpu_seconds_lower_bound=max((t['user_ns'] + t['system_ns']) / 1e9 for t in workers)))
            thread_summary[subject] = dict(samples=rows, medians={k: statistics.median(r[k] for r in rows) for k in rows[0]})
        assert process.sha(HERE.parents[2] / 'data/benchmarks.json') == DATA_SHA and source_state() == before
        process.save(STUDY / 'verification.json', dict(status='shared-string-fact-study-verified', source=production, qualification_source=before, production_source_changes=changes,
            terminal_process_receipts=len(receipts), test_executions=test_counts, full_sessions=full,
            thread_summary=thread_summary, image_qualification=read(STUDY / 'image-qualification.json'),
            verifier_sha256=process.sha(Path(__file__)), benchmark_samples=0,
            retained_controller_stops=['Initial wrapper expected work-policy 66 instead of intended 67.',
                                       'Initial descriptor comparison expected identical admission sizes despite the new inline cell.'],
            scope='Successful completed build and prefix observations are reused, never rerun to repair analysis. Both wrapper failures remain retained. Full sessions and all diagnostics are separately reported; CPU endpoints and first sightings are coarse observations.'))
        print('Verified', len(receipts), 'terminal processes and', test_counts, flush=True)


if __name__ == '__main__':
    main()
