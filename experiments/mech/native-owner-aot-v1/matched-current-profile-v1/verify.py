"""Verify all fresh measurements and derive diagnostic thread summaries."""
from collections import Counter
import fcntl
import json
from pathlib import Path
import statistics
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import text_section
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, OUTPUT_SHA


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == plan['mutex_inode']
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipts = list(STUDY.rglob('process.json'))
        assert len(receipts) == 40
        for path in receipts:
            r = read(path)
            assert r['exit_status'] == 0 and r['reaped'] and r['group_closed']
            assert r['inherited_common_mutex'] and not r['cleanup_errors'] and not r['signals']
            assert not r.get('error') and not r.get('timed_out')
        for mode, count in [('timings', 12), ('counters', 6)]:
            report = read(STUDY / mode / 'results.json')
            assert report['status'] == 'all-complete-process-outputs-and-update-counts-verified'
            assert len(report['samples']) == count and report['source'] == report['source_after'] == before
            for row in report['samples']:
                folder = STUDY / mode / f"{row['order']}-{row['position']}-{row['subject']}"
                assert process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                if row['subject'] == 'mech':
                    native = STUDY / mode / (folder.name + '.native.json')
                    check_native(native)
                    assert process.sha(native) == row['native_sha256']
        build = read(HERE / plan['profile_build'] / 'results.json')
        timed = HERE / '.build' / plan['baseline_binary']
        assert text_section(Path(build['binary'])) == text_section(timed)
        for language in ('mech', 'rust'):
            folder = STUDY / ('early-' + language + '-profile-v1')
            report = read(folder / 'results.json')
            assert report['status'] == 'profile-captured' and report['completed_output_verified']
            assert report['source'] == report['source_after'] == before
            assert len(report['samples']) == len(report['subjects']) == 3
            assert process.sha(Path(report['binary_path'])) == report['binary_sha256']
            for index, sample in enumerate(report['samples']):
                path = folder / f'sample-{index}' / 'stacks.txt'
                assert process.sha(path) == sample['stacks_sha256']
                assert sample['pid'] == report['subjects'][index]['process']['birth_identity']['pid']
                assert process.sha(path.parent / 'subject/stdout.bin') == OUTPUT_SHA
                if language == 'mech':
                    check_native(path.parent / 'native.report.json')
        threads = read(STUDY / 'thread-observations/results.json')
        assert threads['status'] == 'all-owned-thread-observations-and-outputs-verified'
        assert len(threads['subjects']) == 6
        assert threads['source'] == {key: before[key] for key in threads['source']}
        thread_summary = {}
        for language in ('mech', 'rust'):
            rows = []
            for index, row in enumerate(threads['subjects']):
                if row['subject'] != language:
                    continue
                folder = STUDY / 'thread-observations' / f'{index}-{language}'
                assert process.sha(folder / 'thread-observations.json') == row['raw_sha256']
                assert process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                if language == 'mech':
                    check_native(folder.parent / (folder.name + '.native.json'))
                main_thread = next(t for t in row['threads'] if 'main' in t['names'])
                # Ignore pre-exec handle zero and idle pool management threads.
                workers = [t for t in row['threads'] if t is not main_thread and t['handle'] != 0
                           and (t['user_ns'] + t['system_ns']) / 1e9 > .01]
                assert len(workers) == 7
                main_cpu = (main_thread['user_ns'] + main_thread['system_ns']) / 1e9
                first = min(t['first_seen'] for t in workers)
                rows.append(dict(first_worker_observed_seconds=first,
                    main_cpu_seconds_lower_bound=main_cpu,
                    longest_worker_cpu_seconds_lower_bound=max((t['user_ns'] + t['system_ns']) / 1e9 for t in workers),
                    worker_cpu_seconds_lower_bound=sum((t['user_ns'] + t['system_ns']) / 1e9 for t in workers),
                    observed_worker_span_seconds=max(t['last_seen'] for t in workers) - first,
                    process_seconds_diagnostic=row['process']['elapsed_seconds']))
            thread_summary[language] = dict(samples=rows,
                medians={k: statistics.median(r[k] for r in rows) for k in rows[0]})
        analysis = read(STUDY / 'analysis.json')
        assert analysis['status'] == 'exact-current-binary-observations-partitioned'
        assert analysis['source'] == analysis['source_after'] == before
        mech = analysis['languages']['mech']
        long_counts, selected = Counter(), []
        for index in range(3):
            workers = [w for w in mech['workers'] if w['sample'] == index]
            longest = sorted(workers, key=lambda r: r['observations'], reverse=True)[:2]
            assert all('packed_loop_284_funded' in w['top_symbols'][0]['symbol'] for w in longest)
            for worker in longest:
                long_counts.update(worker['buckets'])
            selected.append(dict(sample=index, threads=[w['thread'] for w in longest]))
        assert source_state() == before
        result = dict(status='all-current-matched-profile-evidence-verified',
            source=before, terminal_receipts=len(receipts), primary_timing_processes=12,
            profile_subjects=6, profile_samplers=6, counter_processes=6, thread_polling_processes=6,
            symbol_tools=4, expected_updates_per_mech_run=874999961,
            whole_machine_code_matches_timed=True, thread_summary=thread_summary,
            longest_mech_worker_pair=dict(selection='Two longest observed worker roots in each profile; both execute the ordinary hashed funded loop.',
                threads=selected, observations=sum(long_counts.values()), buckets=dict(long_counts),
                percent={k: 100 * n / sum(long_counts.values()) for k, n in long_counts.items()}),
            verification_sha256=process.sha(Path(__file__)),
            analysis_sha256=process.sha(STUDY / 'analysis.json'), benchmark_samples=0,
            scope='Thread CPU readings are endpoint lower bounds; first/last sightings are coarse polling observations, not exact phase clocks. Diagnostic runs remain separate from primary timings.')
        process.save(STUDY / 'verification.json', result)
        print(json.dumps(dict(terminal_receipts=len(receipts), thread_summary=thread_summary,
                              longest_mech_worker_pair=result['longest_mech_worker_pair']), indent=2))


if __name__ == '__main__':
    main()
