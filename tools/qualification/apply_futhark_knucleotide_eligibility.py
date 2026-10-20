#!/usr/bin/env python3
"""Apply the exact-source Futhark custom-table eligibility correction, without new measurements."""
import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = 'experiments/futhark/library-map-review-v1'
REVIEW = PACKET + '/review.json'
REVIEW_SHA = 'e0bd4d21b5d0c46e4fff59f53b1fde392ca0a159edea35f3bcc6271cedeaf82a'
TOOL = 'tools/qualification/apply_futhark_knucleotide_eligibility.py'
PREPARED = PACKET + '/correction-v1/prepared.json'
REPORT = PACKET + '/correction-v1/report.json'
MARKER = 'futhark_knucleotide_eligibility'
KEYS = ('knucleotide:futhark-knucleotide-compact', 'knucleotide:futhark-knucleotide-optimized')
MAINS = ('83dda7809af2c2884e0e977d3a90ad11b6c04f63593aa2860d1f9ed29090b06c',
         '86279a96aff35f6dc90a7ffff727c33cf9da642e647856e341139836aea97dc6')
SUPPORT = ('56b559f220977ddb2dfe2b6c4b847081fbba71bb181e9aaa5fac58cedbb3342d',
           '0014598c2062c35c3e0ad2b527e8ce6f359dead2ab2b558bfd9c10b5828ebad9',
           '0c1b898695cbe779412defe8208936b59631d4689f2b0230175575e5fe6ddcbf')
REASON = ('Excluded from chart comparisons: these exact retained Futhark sources use a suite-local custom hash table; '
          'the task requires an existing built-in/library table. Historical sources, counts and measurements remain retained.')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encoded(value):
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
    require(review['schema'] == 'futhark-knucleotide-policy-review.v1'
            and review['status'] == 'confirmed-exact-source-policy-violation'
            and [p['key'] for p in review['profiles']] == list(KEYS), 'Policy decision differs')
    for item in review['artifacts']:
        path = Path(item['path'])
        require(not path.is_absolute() and '..' not in path.parts, 'Unsafe evidence path')
        raw = (root / path).read_bytes()
        require(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'],
                'Policy/source evidence differs: ' + item['path'])
    return review, dict(review=dict(path=REVIEW, sha256=REVIEW_SHA),
                        controller=dict(path=TOOL, sha256=sha(root / TOOL)))


def language_aggregate(data, language):
    rows = catalog(data)
    groups = [(b['key'], g) for b in data['benchmarks'] for g in b['groups'] if g['language'] == language]
    result = dict(benchmarks=[key for key, _ in groups], count=len(groups))
    for kind in ('fast', 'small'):
        selected = [rows[g[kind]] for _, g in groups if g.get(kind)]
        result[kind] = dict(x=statistics.geometric_mean(p['x'] for p in selected),
                            y=statistics.geometric_mean(p['y'] for p in selected))
    return result


def append_catalog(before, root=ROOT):
    """Replay the correction after historical admissions; exact old profiles remain evidence."""
    review, refs = evidence(root)
    require(MARKER not in before, 'Futhark eligibility correction already applied')
    rows = catalog(before)
    for key, main, item in zip(KEYS, MAINS, review['profiles']):
        require(key in before['programs'] and key not in before.get('program_inventory', {}),
                'Unexpected original pool membership: ' + key)
        row = rows[key]
        require(row['key'] == key and row['language'] == 'futhark' and row['benchmark'] == 'knucleotide'
                and row['files'] == [main, *SUPPORT] and digest(row) == item['profile_sha256'],
                'Exact retained profile differs: ' + key)
        require(row.get('eligible_for_chart') is not False, 'Profile already excluded')
        for file_sha in row['files']:
            require(before['files'][file_sha]['sha256'] == file_sha
                    and hashlib.sha256(before['files'][file_sha]['code'].encode('utf-8')).hexdigest() == file_sha,
                    'Catalog source bytes differ: ' + file_sha)
    data = copy.deepcopy(before)
    for key in KEYS:
        row = data['programs'].pop(key)
        row.update(eligible_for_chart=False, exclusion_reason=REASON,
                   eligibility_correction=dict(schema='benchmark-eligibility-correction.v1',
                       eligible_for_chart=False, reason='suite-local-custom-hash-table',
                       evidence=refs, source_sha256=row['files'],
                       historical_measurement_preserved=True, historical_work_assertion_preserved=True))
        data.setdefault('program_inventory', {})[key] = row
        data['exclusions'].append(dict(key=key, language='futhark', benchmark='knucleotide',
                                       reason=REASON, source_sha256=row['files'][0], evidence=refs['review']))
    bench = next(b for b in data['benchmarks'] if b['key'] == 'knucleotide')
    groups = [g for g in bench['groups'] if g['language'] == 'futhark']
    require(len(groups) == 1 and set(groups[0]['programs']) == set(KEYS)
            and groups[0]['fast'] == KEYS[1] and groups[0]['small'] == KEYS[0], 'Futhark endpoint group differs')
    removed_group_index = bench['groups'].index(groups[0])
    bench['groups'].remove(groups[0])
    language = next(l for l in data['languages'] if l['key'] == 'futhark')
    previous_language = copy.deepcopy(language)
    require(language['unsupported_benchmarks'] == ['binarytrees'], 'Futhark unsupported coverage differs')
    require(set(language['timed_benchmarks']) == set(language['source_benchmarks'])
            and len(language['timed_benchmarks']) == 9 and 'knucleotide' in language['timed_benchmarks'],
            'Futhark historical coverage differs')
    historical = copy.deepcopy(language['timed_benchmarks'])
    language['historically_measured_benchmarks'] = historical
    language['unsupported_benchmarks'].append('knucleotide')
    for field in ('timed_benchmarks', 'source_benchmarks'):
        language[field].remove('knucleotide')
    language['coverage_note'] = ('Eight of ten workloads are eligible; nine were historically measured. '
        'Binary trees omits required per-node allocations. K-nucleotide uses a suite-local custom hash table, '
        'contrary to the existing-library requirement; its two historical profiles remain inspectable in Data.')
    # No other language/benchmark endpoint changes, and no global normalization
    # change is allowed through this narrow correction.
    for b in data['benchmarks']:
        candidates = [data['programs'][key] for g in b['groups'] for key in g['programs']
                      if data['programs'][key].get('eligible_for_chart') is not False]
        require(min(p['loc'] for p in candidates) == b['baseline_loc'], 'Global LOC baseline would change')
        require(min(p['seconds'] for p in candidates if p.get('seconds') is not None) == b['baseline_seconds'],
                'Global time baseline would change')
    require(not any(r['lang'] == 'futhark' for field in ('reference_summary', 'formatted_reference_summary')
                    for r in data.get(field, [])), 'New Futhark fixed summary needs separate review')
    data[MARKER] = dict(schema='futhark-knucleotide-eligibility-correction.v1', excluded_programs=list(KEYS),
        evidence=refs, no_eligible_fallback=True, removed_group=groups[0], removed_group_index=removed_group_index,
        previous_language=previous_language,
        eligible_workloads=8, historically_measured_workloads=9, total_workloads=10,
        before_aggregate=language_aggregate(before, 'futhark'), after_aggregate=language_aggregate(data, 'futhark'),
        aggregate_limit='Different coverage sets; before/after geometric means are not a matched-workload speedup.',
        source_bytes_changed=False, observations_changed=False, source_counts_changed=False,
        original_profiles_changed=False, timing_processes=0)
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
    path = ROOT / 'data/benchmarks.json'
    raw = path.read_bytes()
    before_sha = hashlib.sha256(raw).hexdigest()
    if args.prepare:
        after = append_catalog(load(path))
        prepared = encoded(after)
        require(sha(path) == before_sha, 'Canonical catalog changed during preparation')
        (ROOT / PREPARED).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / PREPARED).write_bytes(prepared)
        report = dict(schema='futhark-knucleotide-eligibility-preview.v1', before_sha256=before_sha,
            prepared_sha256=hashlib.sha256(prepared).hexdigest(), correction=after[MARKER], canonical_changed=False)
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
        print('Excluded two exact Futhark custom-table profiles; all historical source and observations retained.')


if __name__ == '__main__':
    main()
