#!/usr/bin/env python3
"""Guard the exact-source Lean4 map-work eligibility correction; no new measurements."""
import argparse
import copy
import fcntl
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = 'experiments/lean4/library-map-review-v1'
REVIEW = PACKET + '/review.json'
REVIEW_SHA = 'c447a09ed5760790301f2abebaa956a03c0442c88e55cfb1638bf8cae95ea52b'
TOOL = 'tools/qualification/apply_lean4_knucleotide_eligibility.py'
PREPARED = PACKET + '/correction-v1/.build/candidate-data.json'
REPORT = PACKET + '/correction-v1/report.json'
MARKER = 'lean4_knucleotide_eligibility'
KEYS = ('knucleotide:lean4-knucleotide-native-v1', 'knucleotide:lean4-knucleotide-optimized-v1')
MAINS = ('e3aa2ec057ae485f939062523f90e5427cf214cfc5c36a8e090a4e5ecd7a2e3a',
         'e2cb4dc950de63f0cb3ceded840eda8057c71a8307d82fe80e6928a3d9bb33c0')
COMMON = '316669c9da08e0fe7f6c0ef0409537ecaa73dbedeb353e27b525c927fc53d54e'
FORMAT = 'efa69b65452aef20b0b9d60a24f95bcc13a08d03e607d1f4fe411948f3a16000'
BUNDLES = ((MAINS[0], COMMON, FORMAT), (MAINS[1], FORMAT))
REASON = ('Excluded from chart comparisons: these exact suite-authored Lean4 sources use dense counters and '
          'query-only rolling scans, omitting required built-in/library hash-table accumulation for all seven widths. '
          'Historical sources, counts and measurements remain retained.')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encoded(value):
    # Preserve input object order; a narrow metadata correction must not reorder
    # every unrelated catalog field in its prepared serialization.
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: require(False, 'Nonfinite JSON: ' + value))


def catalog(data):
    for key, row in data.get('program_inventory', {}).items():
        require(key not in data['programs'] or data['programs'][key] == row, 'Conflicting profile: ' + key)
    return {**data.get('program_inventory', {}), **data['programs']}


def evidence(root):
    root = Path(root).resolve()
    require(sha(root / REVIEW) == REVIEW_SHA, 'Policy review identity differs')
    review = load(root / REVIEW)
    require(review['schema'] == 'lean4-knucleotide-policy-review.v1'
            and review['status'] == 'confirmed-exact-source-policy-violation'
            and [p['key'] for p in review['profiles']] == list(KEYS), 'Policy decision differs')
    require(review['rule']['snapshot'] == 'experiments/futhark/library-map-review-v1/primary/knucleotide-description.html'
            and review['decision']['eligible_workloads_after'] == 9
            and review['decision']['no_eligible_fallback'] is True, 'Required algorithm or coverage differs')
    for item in review['artifacts']:
        path = Path(item['path'])
        require(not path.is_absolute() and '..' not in path.parts, 'Unsafe evidence path')
        raw = (root / path).read_bytes()
        require(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'],
                'Policy/source evidence differs: ' + item['path'])
    return review, dict(review=dict(path=REVIEW, sha256=REVIEW_SHA),
                        controller=dict(path=TOOL, sha256=sha(root / TOOL)))


def language_aggregate(data):
    rows = catalog(data)
    groups = [(b['key'], g) for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'lean4']
    result = dict(benchmarks=[key for key, _ in groups], count=len(groups))
    for kind in ('fast', 'small'):
        selected = [rows[g[kind]] for _, g in groups]
        result[kind] = {axis: statistics.geometric_mean(p[axis] for p in selected) for axis in ('x', 'y')}
    return result


def minima(data, benchmark):
    rows = [data['programs'][key] for group in benchmark['groups'] for key in group['programs']
            if data['programs'][key].get('eligible_for_chart') is not False]
    return min(p['loc'] for p in rows), min(p['seconds'] for p in rows if p.get('seconds') is not None)


def append_catalog(before, root=ROOT):
    """Replay only this policy correction after prior admissions; retain all old evidence."""
    review, refs = evidence(root)
    require(MARKER not in before, 'Lean4 eligibility correction already applied')
    rows = catalog(before)
    require({key for key, row in rows.items() if row['language'] == 'lean4'
             and row['benchmark'] == 'knucleotide'} == set(KEYS), 'Unreviewed Lean4 k-nucleotide fallback')
    for key, bundle, item in zip(KEYS, BUNDLES, review['profiles']):
        require(key in before['programs'] and key in before.get('program_inventory', {}),
                'Unexpected original pool membership: ' + key)
        row = rows[key]
        require(row['key'] == key and row['language'] == 'lean4' and row['benchmark'] == 'knucleotide'
                and row['files'] == list(bundle) and digest(row) == item['profile_sha256']
                and row['authorship']['origin_status'] == 'suite-authored',
                'Exact retained profile differs: ' + key)
        require(row.get('eligible_for_chart') is not False, 'Profile already excluded')
        for file_sha in bundle:
            require(before['files'][file_sha]['sha256'] == file_sha
                    and hashlib.sha256(before['files'][file_sha]['code'].encode('utf-8')).hexdigest() == file_sha,
                    'Catalog source bytes differ: ' + file_sha)
    data = copy.deepcopy(before)
    previous_eligibility = {key: {field: copy.deepcopy(rows[key][field])
                                for field in ('eligible_for_chart', 'exclusion_reason', 'eligibility_correction')
                                if field in rows[key]} for key in KEYS}
    for key in KEYS:
        row = data['programs'].pop(key)
        row.update(eligible_for_chart=False, exclusion_reason=REASON,
                   eligibility_correction=dict(schema='benchmark-eligibility-correction.v1',
                       eligible_for_chart=False, reason='dense-and-query-only-counting-omits-library-map-work',
                       evidence=refs, source_sha256=row['files'],
                       historical_measurement_preserved=True, historical_work_assertion_preserved=True))
        data['program_inventory'][key] = row
        data['exclusions'].append(dict(key=key, language='lean4', benchmark='knucleotide',
                                      reason=REASON, source_sha256=row['files'][0], evidence=refs['review']))
    bench = next(b for b in data['benchmarks'] if b['key'] == 'knucleotide')
    groups = [g for g in bench['groups'] if g['language'] == 'lean4']
    require(len(groups) == 1 and groups[0]['programs'] == list(KEYS)
            and groups[0]['fast'] == groups[0]['small'] == KEYS[0]
            and groups[0].get('formatted_fast') is groups[0].get('formatted_small') is None,
            'Lean4 endpoint group differs')
    removed_group_index = bench['groups'].index(groups[0])
    bench['groups'].remove(groups[0])
    language = next(l for l in data['languages'] if l['key'] == 'lean4')
    previous_language = copy.deepcopy(language)
    require(not language.get('unsupported_benchmarks')
            and set(language['timed_benchmarks']) == set(language['source_benchmarks'])
            and len(language['timed_benchmarks']) == 10 and 'knucleotide' in language['timed_benchmarks'],
            'Lean4 historical coverage differs')
    require(not language.get('formatted_timed_benchmarks') and not language.get('formatted_source_benchmarks'),
            'New Lean4 formatted coverage needs separate review')
    language['historically_measured_benchmarks'] = copy.deepcopy(language['timed_benchmarks'])
    language['unsupported_benchmarks'] = ['knucleotide']
    for field in ('timed_benchmarks', 'source_benchmarks'):
        language[field].remove('knucleotide')
    language['coverage_note'] = ('Nine of ten workloads are eligible; all ten were historically measured. '
        'The two suite-authored k-nucleotide profiles omit required library hash-table accumulation; '
        'their exact sources, counts, samples and historical work assertions remain inspectable in Data.')
    previous_references = [copy.deepcopy(r) for r in data.get('reference_summary', []) if r['lang'] == 'lean4']
    require(len(previous_references) == 1
            and set(previous_references[0]['measured_benchmarks']) == set(previous_language['timed_benchmarks']),
            'Lean4 fixed reference summary differs')
    require(not any(r['lang'] == 'lean4' for r in data.get('formatted_reference_summary', [])),
            'New Lean4 formatted reference needs separate review')
    aggregate = language_aggregate(data)
    require(aggregate['count'] == 9 and 'knucleotide' not in aggregate['benchmarks'], 'Eligible coverage differs')
    reference = next(r for r in data['reference_summary'] if r['lang'] == 'lean4')
    reference['measured_benchmarks'].remove('knucleotide')
    for kind in ('fast', 'small'):
        reference[kind] = aggregate[kind]
    for old_b, new_b in zip(before['benchmarks'], data['benchmarks']):
        require(minima(before, old_b) == minima(data, new_b), 'Global eligible minima would change')
    data[MARKER] = dict(schema='lean4-knucleotide-eligibility-correction.v1', excluded_programs=list(KEYS),
        evidence=refs, no_eligible_fallback=True, removed_group=groups[0], removed_group_index=removed_group_index,
        previous_language=previous_language, previous_reference_summary=previous_references,
        previous_profile_eligibility=previous_eligibility,
        eligible_workloads=9, historically_measured_workloads=10, total_workloads=10,
        before_aggregate=language_aggregate(before), after_aggregate=aggregate,
        aggregate_limit='Different coverage sets; before/after geometric means are not a matched-workload speedup.',
        source_bytes_changed=False, observations_changed=False, source_counts_changed=False,
        historical_work_assertions_changed=False, protected_upstream_profiles_changed=False, timing_processes=0)
    require(data['files'] == before['files'], 'Source records changed')
    after_rows = catalog(data)
    require(after_rows.keys() == rows.keys(), 'Historical profile disappeared')
    for key, row in rows.items():
        if key not in KEYS:
            require(after_rows[key] == row, 'Unrelated profile changed: ' + key)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-before-sha256')
    parser.add_argument('--expected-prepared-sha256')
    args = parser.parse_args()
    require(args.prepare != args.apply, 'Choose exactly one of --prepare/--apply')
    with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        guarded(args)


def guarded(args):
    path = ROOT / 'data/benchmarks.json'
    before_sha = sha(path)
    if args.prepare:
        prepared_catalog = append_catalog(load(path))
        prepared = encoded(prepared_catalog)
        require(sha(path) == before_sha, 'Canonical catalog changed during preparation')
        (ROOT / PREPARED).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / PREPARED).write_bytes(prepared)
        report = dict(schema='lean4-knucleotide-eligibility-preview.v1', before_sha256=before_sha,
            prepared_sha256=hashlib.sha256(prepared).hexdigest(), correction=prepared_catalog[MARKER],
            canonical_changed=False, timing_processes=0)
        (ROOT / REPORT).write_bytes(encoded(report))
        print(json.dumps({key: report[key] for key in ('before_sha256', 'prepared_sha256', 'canonical_changed')}))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256, 'Apply requires reviewed hashes')
        require(before_sha == args.expected_before_sha256 and sha(ROOT / PREPARED) == args.expected_prepared_sha256,
                'Reviewed catalog/preview identity differs')
        prepared = encoded(append_catalog(load(path)))
        require(prepared == (ROOT / PREPARED).read_bytes(), 'Prepared correction does not reproduce')
        require(sha(path) == before_sha, 'Canonical catalog changed during replay')
        path.write_bytes(prepared)
        print('Excluded two exact Lean4 map-work profiles; all historical sources and observations retained.')


if __name__ == '__main__':
    main()
