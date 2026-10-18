#!/usr/bin/env python3
"""Apply the reviewed application-LOC correction; benchmark programs are not run."""
import argparse
import gzip
import json
from pathlib import Path

from source_accounting import ROOT, PACKET, historical_catalog, sha, transform
from source_accounting_counts import qualify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    packet = ROOT / PACKET
    current = json.loads((ROOT / 'data/benchmarks.json').read_text())
    if args.check:
        historical_catalog(ROOT, current)
        before = json.loads(gzip.decompress((packet / 'before.json.gz').read_bytes()))
        expected = qualify(before, json.loads((ROOT / 'data/source-size-review.json').read_text()))
        assert expected == json.loads((packet / 'partitions.json').read_text())
        print('Application LOC, source partitions and historical preservation verified')
        return
    assert 'source_accounting' not in current, 'Already applied; use --check'
    before_raw = (ROOT / 'data/benchmarks.json').read_bytes()
    assert before_raw == gzip.decompress((packet / 'before.json.gz').read_bytes())
    review_raw = (ROOT / 'data/source-size-review.json').read_bytes()
    partitions = qualify(current, json.loads(review_raw))
    encoded_partitions = (json.dumps(partitions, indent=2, ensure_ascii=False) + '\n').encode()
    (packet / 'partitions.json').write_bytes(encoded_partitions)
    after, report = transform(current, json.loads(review_raw), partitions)
    allowed = {'loc', 'canonical_loc', 'physical_loc', 'formatted_loc', 'formatted_x',
               'file_roles', 'x', 'source_accounting'}
    for pool in ('programs', 'program_inventory'):
        assert current[pool].keys() == after[pool].keys()
        for key, original in current[pool].items():
            changed = after[pool][key]
            assert {k:v for k,v in original.items() if k not in allowed} == {
                k:v for k,v in changed.items() if k not in allowed}, key
    assert current['files'] == after['files'], 'Source bytes or original file metadata changed'
    receipt = dict(schema='benchmark-source-accounting-transition.v1',
                   before_catalog_sha256=sha(before_raw), review_sha256=sha(review_raw),
                   partitions_sha256=sha(encoded_partitions), transformation=report,
                   source_bytes_unchanged=True, timing_fields_unchanged=True,
                   historical_publication_snapshots_unchanged=True)
    output = (json.dumps(after, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    if args.apply:
        (packet / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        (ROOT / 'data/benchmarks.json').write_bytes(output)
        assert historical_catalog(ROOT, json.loads(output)) == current
    else:
        (packet / 'candidate.json.gz').write_bytes(gzip.compress(output, mtime=0))
    print(json.dumps(dict(status='APPLIED' if args.apply else 'PREPARED',
                         changed_profiles=len(report['changed_profiles']), baselines=report['baselines'])))


if __name__ == '__main__':
    main()
