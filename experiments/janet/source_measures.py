#!/usr/bin/env python3
"""Retain the catalog's raw-source measures for every active Janet draft."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def build():
    path = ROOT / 'tools/source_metrics.py'
    spec = importlib.util.spec_from_file_location('janet_catalog_source_measures', path)
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    encoder, tokenizer = metrics.tokenizer()
    assert encoder is not None and tokenizer['status'] == 'available'
    manifest_path = HERE / 'source-manifest-v1.json'
    manifest = json.loads(manifest_path.read_bytes())
    profiles = {}
    for row in manifest['sources']:
        source = ROOT / row['path']
        assert metrics.sha(source.read_bytes()) == row['sha256']
        profiles[row['benchmark']] = dict(source=row['path'], **metrics.measure(source.read_text(), encoder),
            normalized_source_units=None, native_formatted_loc=None,
            normalized_source_count_qualified=False, formatted_source_count_qualified=False)
    return dict(schema='janet-raw-source-measures.v1', source_manifest_sha256=metrics.sha(manifest_path.read_bytes()),
        metric_implementation=dict(path=str(path.relative_to(ROOT)), sha256=metrics.sha(path.read_bytes())),
        tokenizer=tokenizer, python=sys.version, zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        scope='Complete authored Janet application file, including every helper and GMP FFI declaration, comments and blank rows. Unmodified external libraries and the runtime remain dependencies.',
        profiles=profiles, source_count_status='Native normalized owner rules and pinned formatting remain pending; raw physical rows do not substitute for them.',
        chart_admission=False, native_processes_started=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    output = HERE / 'source-measures-v1.json'
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        with output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'written', sources=len(result['profiles']))))
