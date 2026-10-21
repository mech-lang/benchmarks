#!/usr/bin/env python3
"""Raw source measures for six retained OCaml implementations and four drafts."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def build():
    path = ROOT / 'tools/source_metrics.py'
    spec = importlib.util.spec_from_file_location('ocaml_review_source_measures', path)
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    encoder, tokenizer = metrics.tokenizer()
    assert encoder is not None and tokenizer['status'] == 'available'
    review = HERE / 'review.json'
    proposals = [HERE.parent / packet / 'proposal.json'
                 for packet in ('rolling-v1', 'fasta-buffer-v1')]
    rows = [dict(profile=row['program'], **source)
            for row in json.loads(review.read_bytes())['inspected_profiles']
            for source in row['source_bundle'] if source['included_in_application_loc']]
    rows += [dict(profile=row['id'], **row['source']) for proposal in proposals
             for row in json.loads(proposal.read_bytes())['candidates']]
    values = {}
    for row in rows:
        source = ROOT / row['path']
        assert metrics.sha(source.read_bytes()) == row['sha256']
        values[row['profile']] = dict(path=row['path'], **metrics.measure(source.read_text(), encoder),
            normalized_source_units=None, native_formatted_loc=None,
            normalized_source_count_qualified=False, formatted_source_count_qualified=False)
    assert len(values) == len(rows) == 10
    return dict(schema='ocaml-inspected-and-candidate-raw-source-measures.v1',
        inputs={str(p.relative_to(ROOT)): metrics.sha(p.read_bytes())
                for p in (review, *proposals, path)},
        tokenizer=tokenizer, python=sys.version, zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        scope='Complete authored application file, including parser, modules, helpers, process control, comments and blank rows; no helper exclusion or invented scalar expansion.',
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
