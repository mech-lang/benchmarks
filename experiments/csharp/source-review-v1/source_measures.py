#!/usr/bin/env python3
"""Raw source measures for ten retained C# bundles and five uncompiled drafts."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKETS = ('spectral-scratch-v1', 'knucleotide-general-v1', 'regex-managed-v1',
           'regex-generated-v1', 'revcomp-short-read-v1')


def build():
    path = ROOT / 'tools/source_metrics.py'
    spec = importlib.util.spec_from_file_location('csharp_review_raw_measures', path)
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    encoder, tokenizer = metrics.tokenizer()
    assert encoder is not None and tokenizer['status'] == 'available'
    review = HERE / 'review.json'
    proposals = [HERE.parent / packet / 'proposal.json' for packet in PACKETS]
    bundles = {}
    for row in json.loads(review.read_bytes())['inspected_profiles']:
        included = [s for s in row['source_bundle'] if s['included_in_application_loc']]
        assert len(included) == 1
        source = included[0]
        identity = (source['path'], source['sha256'])
        if identity not in bundles:
            bundles[identity] = dict(profile=row['program'], profiles_sharing_source=[], **source)
        bundles[identity]['profiles_sharing_source'].append(row['program'])
    rows = list(bundles.values())
    rows += [dict(profile=value['id'], **value['source']) for value in
             (json.loads(proposal.read_bytes()) for proposal in proposals)]
    values = {}
    for row in rows:
        source = ROOT / row['path']
        assert metrics.sha(source.read_bytes()) == row['sha256']
        values[row['profile']] = dict(path=row['path'], profiles_sharing_source=row.get('profiles_sharing_source', []),
            **metrics.measure(source.read_text(), encoder), normalized_source_units=None,
            native_formatted_loc=None, normalized_source_count_qualified=False,
            formatted_source_count_qualified=False)
    assert len(values) == len(rows) == 15
    return dict(schema='csharp-inspected-and-candidate-raw-source-measures.v1',
        inputs={str(p.relative_to(ROOT)): metrics.sha(p.read_bytes()) for p in (review, *proposals, path)},
        tokenizer=tokenizer, python=sys.version, zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        scope='Complete authored application source, including every compatibility method, FFI declaration, parser, orchestration, comment and blank row. Build recipes, diagnostic projections and emitted compiler code are separately identified; native source boundaries remain unqualified.',
        profiles=values, native_processes_started=0, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    path = HERE / 'source-measures-v1.json'
    if args.check:
        assert json.loads(path.read_bytes()) == result
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'written', sources=len(result['profiles']),
                          native_processes_started=0)))
