#!/usr/bin/env python3
"""Complementary exact-text measures for the Janet source overlays and parents."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def build():
    path=ROOT/'tools/source_metrics.py'
    spec=importlib.util.spec_from_file_location('janet_overlay_metrics',path)
    metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
    encoder,tokenizer=metrics.tokenizer()
    assert encoder is not None and tokenizer['status']=='available'
    profiles={}
    for version in ('source-v2','source-v3'):
        for benchmark in ('regexredux','spectralnorm','revcomp'):
            source=HERE/version/(benchmark+'.janet')
            profiles[str(source.relative_to(ROOT))]=dict(**metrics.measure(source.read_text(),encoder),
                normalized_source_units=None,native_formatted_loc=None,
                normalized_source_count_qualified=False,formatted_source_count_qualified=False)
    return dict(schema='janet-source-overlay-measures.v1',profiles=profiles,
        metric_implementation=dict(path=str(path.relative_to(ROOT)),sha256=metrics.sha(path.read_bytes())),
        runner_sha256=metrics.sha(Path(__file__).read_bytes()), tokenizer=tokenizer,
        python=sys.version,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        scope='Entire authored application file, including comments, blank rows and every helper. Unchanged general runtime and Spork library are external dependencies.',
        chart_admission=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build();output=HERE/'source-overlay-measures-v1.json'
    if args.check: assert json.loads(output.read_bytes())==result
    else: output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',profiles=len(result['profiles']))))
