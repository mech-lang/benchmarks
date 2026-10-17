"""Reconcile full Lean candidate samples and replay normalized source ownership."""
import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import shutil
import statistics

from lean_run import ROOT, FULL, sha, energy_output


def replay_counts(path, build, build_path):
    counts = json.loads(path.read_text())
    assert counts['status'] == 'QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES'
    assert counts['sources'] == build['sources'] and counts['build_report_sha256'] == sha(build_path)
    records = [json.loads(line) for line in (path.parent / 'native-reader.stdout').read_text().splitlines()]
    source = Path(build['source_directory'])
    replayed = []
    for record in records:
        file = Path(record['source'])
        if file.parent != source:
            continue
        raw = file.read_bytes()
        boundaries = [-1] + [i for i, byte in enumerate(raw) if byte == 10]
        line_for = lambda offset: bisect_right(boundaries, offset - 1)
        physical = set()
        for token in record['tokens']:
            start, end = token['start'], token['end']
            if start is None or end is None or start == end:
                continue
            assert 0 <= start < end <= len(raw)
            physical.update(range(line_for(start), line_for(end - 1) + 1))
        owners = Counter(line_for(item['start']) for item in record['do_statements'])
        normalized = len(physical) + sum(count - 1 for count in owners.values() if count > 1)
        unit = counts['units'][file.name]
        assert sha(file) == unit['sha256'] and unit['physical_loc'] == len(physical)
        assert unit['canonical_loc'] == normalized
        replayed.append(file.name)
    assert len(replayed) == 10
    for name, unit in counts['units'].items():
        file = source / name
        assert sha(file) == unit['sha256']
        if name.endswith('.c'):
            prior = unit['identical_source_count_evidence']
            assert sha(ROOT / prior['report']) == prior['report_sha256']
            assert sha(prior['original_source']) == prior['source_sha256'] == unit['sha256']
    for benchmark, bundle in counts['profiles'].items():
        assert bundle['files'] == build['profiles'][benchmark]['files']
        assert sum(counts['units'][name]['canonical_loc'] for name in bundle['files']) == bundle['canonical_loc']
    return counts, dict(status='PASSED', native_lean_units_replayed=replayed,
        byte_offsets='Independent newline-boundary index and binary search over retained native tokens and do-statement positions.',
        identical_authored_c_helpers_reverified=True, formatted_loc_claimed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cohort', nargs=4, action='append', metavar=('BUILD', 'COUNTS', 'WORK', 'FULL'), required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    profiles = []
    intervals = []
    closures = []
    for build_file, counts_file, work_file, full_file in args.cohort:
        build_path, counts_path, work_path, full_path = map(Path, (build_file, counts_file, work_file, full_file))
        build, work, full = [json.loads(path.read_text()) for path in (build_path, work_path, full_path)]
        assert build['status'] == 'COMPILED_AWAITING_CONFORMANCE'
        assert full['status'] == 'PASSED' and full['mode'] == 'full' and full['active'] is None and full['sources_unchanged']
        assert work['status'] == 'PASSED_STATIC_AND_BOUNDED_NATIVE_ALLOCATION_CHECK'
        assert build['sources'] == work['sources'] == full['sources']
        assert full['required_work']['sha256'] == sha(work_path)
        assert all(sha(ROOT / path) == digest for path, digest in build['sources'].items())
        bounded_path = Path(full['bounded_prerequisite']['path'])
        bounded = json.loads(bounded_path.read_text())
        assert sha(bounded_path) == full['bounded_prerequisite']['sha256'] == work['bounded_report_sha256']
        assert bounded['status'] == 'PASSED' and len(bounded['cases']) == 149 and bounded['sources'] == build['sources']
        counts, replay = replay_counts(counts_path, build, build_path)
        selected = set(full['binaries'])
        assert len(full['cases']) == full['benchmark_samples'] == 3 * len(selected)
        cohort = dict(variant=build['variant'], build=str(build_path), counts=str(counts_path), work=str(work_path), full=str(full_path),
                      hashes={str(p): sha(p) for p in (build_path, counts_path, work_path, full_path)}, normalized_count_replay=replay)
        closures.append(cohort)
        for benchmark in sorted(selected):
            compiled = build['profiles'][benchmark]
            assert sha(compiled['binary']) == compiled['binary_sha256'] == full['binaries'][benchmark] == bounded['binaries'][benchmark]
            rows = [row for row in full['cases'] if row['benchmark'] == benchmark]
            assert len(rows) == 3 and len({row['pid'] for row in rows}) == 3
            for row in rows:
                assert row['valid'] and row['exit_code'] == 0 and not row['timed_out']
                assert row['stderr']['bytes'] == 0 and row['elapsed_seconds'] > 0
                process = json.loads(Path(row['stdout']['path']).with_name('process.json').read_text())
                assert all(row[key] == value for key, value in process.items())
                for stream in ('stdout','stderr'):
                    file = Path(row[stream]['path'])
                    assert file.stat().st_size == row[stream]['bytes'] and sha(file) == row[stream]['sha256']
                if benchmark == 'nbody':
                    assert energy_output(Path(row['stdout']['path']).read_bytes(), b'-0.169075164\n-0.169059907\n')
                else:
                    assert (row['stdout']['bytes'], row['stdout']['sha256']) == FULL[benchmark][1:]
                assert row['competing_compilers_before'] == [] and 'AC Power' in row['power_before'] and 'AC Power' in row['power_after']
                intervals.append((datetime.fromisoformat(row['started_utc']), datetime.fromisoformat(row['finished_utc'])))
            samples = [row['elapsed_seconds'] for row in rows]
            profiles.append(dict(benchmark=benchmark, variant=build['variant'], files=counts['profiles'][benchmark]['files'],
                normalized_loc=counts['profiles'][benchmark]['canonical_loc'], physical_loc=counts['profiles'][benchmark]['physical_loc'],
                samples=samples, median_seconds=statistics.median(samples), sample_sd_seconds=statistics.stdev(samples),
                binary_sha256=compiled['binary_sha256'], source_directory=build['source_directory'],
                build_report=str(build_path), counts_report=str(counts_path), work_report=str(work_path), full_report=str(full_path)))
    intervals.sort()
    assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    assert len({(p['benchmark'],p['variant']) for p in profiles}) == len(profiles)
    report = dict(schema='lean-optimized-candidate-results.v1', status='FULL_SIZE_SAMPLES_AND_NORMALIZED_LOC_RECONCILED',
        benchmark_samples=len(intervals), profiles=profiles, cohorts=closures, timing_processes_serial=True,
        saved_stream_hashes_recomputed=True, process_records_reconciled=True, source_counts_independently_replayed=True,
        matched_mech_controls=0, existing_other_language_measurements_changed=False, formatted_loc_claimed=False,
        normalization='Native lexical ownership plus independent do-statement expansion, including every authored Lean/C compilation input.',
        global_optimality_claimed=False)
    args.output.mkdir(parents=True)
    shutil.copyfile(__file__, args.output / 'producer.py')
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'], len(profiles), 'profiles', len(intervals), 'samples', flush=True)


if __name__ == '__main__':
    main()
