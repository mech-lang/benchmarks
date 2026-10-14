"""Replay manually reviewed line accounting for all ten exact Scala sources.

The independent expectations below were derived by reading each original source
and its native owner map. They are not read from projected totals. Every other
occupied source row contains one authored unit under the common rule; signature
continuations, composed expressions and packed control/header rows are explicit.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'experiments/scala/source-counts-v1/canonical-owner-review-v1'
REVIEW_SHA = '25fde663cc9a774fd0d6668434919c1014a8984478c180b3a9bed00f42c69869'
ADAPTER_SHA = '6b5293e8aaae5084ebd075df4f16d5ca57e97583b6312078d407a01e418b1fa6'
TEST_SHA = '500c90618cd9f92e87be07254261f3415521b0cf76ec4eb0db8134a8f8daba4c'
SOURCES = {
    'binarytrees': 'bdcebd103b9da8de792d8f59da68125aad57d1bb286f10a4074506cb8d5a518b',
    'fannkuchredux': 'ba8c9dd5dafea3ecca8e9033e3f608120f6b922c58d3a702933adf7819812762',
    'fasta': 'a3e2f78453acff46081258324f49040b8a9a93ce48377eae1a5a3d5c30ae37f1',
    'knucleotide': '8ab9a123c499bbad40b3c09aebf0910dc6977ec564bb3d025941206fc6a2d269',
    'mandelbrot': 'de29618bbbfb47d11770eb62e771e5e659a8707a2781fbc5df7eb324e71471b7',
    'nbody': '74b6a0eb04fa87240d47b903969898314c400e8715c436515d503f6f4112957b',
    'pidigits': '5dca3a4127f2283792a2dfa0fc1fff47366d70405b28d14d156c8b0609408ad5',
    'regexredux': '3e4db60819b528f72b39d7d2571a9c8493b054c13cee95f6b56a831e0cbbc362',
    'revcomp': 'bd54d135034e035e77594fc22cec60b943356452ec5f5cb0fa50c27bfa381b6f',
    'spectralnorm': '4b945cbdfb8c7944c8c7874055211e43800a58ad1e71bd44e520d346ae114115',
}
FINAL = 'Written try close, finally header, and unbraced shutdown call'
DELTAS = {
    'binarytrees': {
        10: (3, 'Class header and two explicit constructor val fields'),
        12: (0, 'Scalar conditional belongs to expression-method declaration on line 11'),
        16: (0, 'Scalar conditional belongs to expression-method declaration on line 15'),
        17: (0, 'Alternate scalar value remains in the same expression method'), 47: (3, FINAL)},
    'fannkuchredux': {
        11: (0, 'Plain constructor formals continue the class header'),
        12: (0, 'Parent type and opening brace continue the class header'),
        95: (2, 'If header and unbraced nextPermutation call'), 131: (3, FINAL)},
    'fasta': {24: (0, 'Expression method body remains composed with line 23 header'),
        38: (2, 'While header and independent compound update'),
        41: (2, 'If header and unbraced output call'), 50: (2, 'If header and unbraced output call')},
    'knucleotide': {
        14: (2, 'Case header and scalar result'), 15: (2, 'Case header and scalar result'),
        16: (2, 'Case header and scalar result'), 17: (2, 'Case header and scalar result'),
        18: (2, 'Case header and explicit throw expression'),
        31: (2, 'If header and independent assignment'),
        32: (2, 'Written previous branch close and one joined else-if header'),
        51: (2, 'If header and unbraced counts.update call'),
        83: (3, 'First tuple callback header, body and written close'),
        84: (3, 'Second chained tuple callback header, body and written close'),
        90: (2, 'Written previous branch close and else header')},
    'mandelbrot': {58: (3, FINAL)},
    'nbody': {},
    'pidigits': {25: (2, 'While header and unbraced padding call'),
                29: (2, 'Written previous branch close and else header')},
    'regexredux': {27: (2, 'While header and compound count update'), 49: (3, FINAL)},
    'revcomp': {39: (2, 'If header and unbraced output call'),
        49: (3, 'Written branch close, one joined else-if header, and unbraced append call')},
    'spectralnorm': {11: (0, 'Formal parameters and opening brace continue the method header'),
                     64: (3, FINAL)},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise AssertionError('Manual review source binding changed: '+str(path))
    return raw


def require(value, message):
    if not value:
        raise AssertionError(message)


def review_one(name, source, projection):
    text = source.decode('utf-8')
    source_lines = text.splitlines()
    tokens = {t['token_id']: t for t in projection['token_ownership']}
    require(len(tokens) == len(projection['token_ownership']), 'Duplicate owner token')
    counts, by_line, occupied = Counter(), {}, set()
    seen = []
    for token in tokens.values():
        a, b = token['utf8_span']
        require(source[a:b].decode() == token['source_text'], 'Owner token bytes changed')
        line = source[:a].decode().count('\n')+1
        occupied.update(range(line, line+token['source_text'].count('\n')+1))
    for event in projection['canonical_events']:
        a, b = event['utf8_span']
        require(source[a:b].decode() == event['source_text'], 'Owner event bytes changed')
        for token_id in event['token_ids']:
            require(token_id in tokens and tokens[token_id]['owner_event'] == event['id'], 'Owner linkage differs')
        seen.extend(event['token_ids'])
        if not event['units']:
            continue
        if event['kind'] == 'physical-data-rows':
            rows = event['reason']['physical_rows']
            require(event['units'] == len(rows) == len(set(rows)), 'Data rows are not one unit each')
        else:
            require(event['units'] == 1, 'Unexpected multiple-weight executable owner')
            start = min(tokens[i]['utf8_span'][0] for i in event['token_ids'])
            rows = [source[:start].decode().count('\n')+1]
        for line in rows:
            counts[line] += 1
            by_line.setdefault(line, []).append(event['id'])
    require(len(seen) == len(set(seen)) and set(seen) == set(tokens), 'Missing or duplicated token ownership')
    require(set(DELTAS[name]).issubset(occupied), 'Manual adjustment targets a non-code source row')
    expected = {line: DELTAS[name].get(line, (1, None))[0] for line in occupied}
    require(dict(counts) == {line: count for line, count in expected.items() if count},
            'Actual owner accounting differs from independent source review: '+name)
    require(projection['diagnostics'] == [] and projection['all_meaningful_tokens_owned'] is True,
            'Unresolved application owner')
    total = sum(expected.values())
    require(projection['candidate_normalized_loc'] == total and projection['physical_loc'] == len(occupied),
            'Application totals disagree with independently reviewed rows')
    require(projection['normalized_loc'] is None and projection['canonical_LOC_admitted'] is False
            and projection['chart_admission'] is False, 'Producer prematurely admitted application')
    return dict(benchmark=name, source_sha256=SOURCES[name], canonical_loc=total,
        physical_loc=len(occupied), reviewed_owner_events=len(projection['canonical_events']),
        unique_tokens_checked=len(tokens), all_owner_slices_verified=True,
        all_application_owners_manually_reviewed=True,
        line_accounting=[dict(line=line, source=source_lines[line-1], units=expected[line],
            owner_events=by_line.get(line, []), rationale=DELTAS[name].get(line,
                (1, 'One authored unit or one retained physical data row'))[1]) for line in sorted(occupied)])


def audit():
    review = json.loads(checked(PACKET/'results-v1/review.json', REVIEW_SHA))
    checked(ROOT/'tools/scala_source_units_reviewed.py', ADAPTER_SHA)
    checked(ROOT/'tools/test_scala_source_units_reviewed.py', TEST_SHA)
    cases = []
    require([row['id'] for row in review['applications']] == ['scala-'+name+'-jvm-v1' for name in SOURCES],
            'Wrong application inventory')
    for name, source_digest in SOURCES.items():
        source = checked(ROOT/'experiments/scala/source-v1'/name/'Main.scala', source_digest)
        filename = 'scala-'+name+'-jvm-v1.json'
        expected = review['artifacts'][filename]
        raw = checked(PACKET/'results-v1'/filename, expected['sha256'])
        require(len(raw) == expected['bytes'], 'Projection length changed')
        projection = json.loads(raw)
        require(projection['source_sha256'] == source_digest, 'Projection/source mismatch')
        case = review_one(name, source, projection)
        case.update(projection=filename, projection_sha256=expected['sha256'])
        cases.append(case)
    return dict(schema='scala-application-manual-owner-review-v1',
        status='all-ten-source-owner-maps-manually-reviewed-awaiting-independent-admission',
        rule='canonical-source-units-20261012-approved-rule-v2',
        projection_review_sha256=REVIEW_SHA, adapter_sha256=ADAPTER_SHA, tests_sha256=TEST_SHA,
        audit_source_sha256=sha(Path(__file__).read_bytes()), applications=cases,
        native_executions=0, source_work_qualified=False, canonical_LOC_admitted=False,
        full_timings_qualified=False, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Fresh additive review file required')
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps([dict(benchmark=c['benchmark'], canonical_loc=c['canonical_loc'],
                           physical_loc=c['physical_loc']) for c in result['applications']]))
