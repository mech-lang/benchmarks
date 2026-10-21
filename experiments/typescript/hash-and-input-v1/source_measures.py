#!/usr/bin/env python3
"""Use the catalog's pinned raw-source metrics on the four candidate sources."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build():
    native = load('typescript_source_proposal_metrics', HERE / 'qualify.py')
    metric_path = ROOT / 'tools/source_metrics.py'
    metrics = load('catalog_source_metrics', metric_path)
    encoder, tokenizer = metrics.tokenizer()
    assert encoder is not None and tokenizer['status'] == 'available'
    return dict(schema='typescript-input-map-source-measures.v1',
        metric_implementation=dict(path=str(metric_path.relative_to(ROOT)), sha256=native.sha(metric_path)),
        tokenizer=tokenizer, python=sys.version, zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
        scope='Complete authored TypeScript file, including all helpers, comments and blank rows; emitted JavaScript and diagnostic tools are excluded.',
        gzip_policy=dict(level=9, mtime=0, filename='', os_byte=255),
        normalized_source_count_status='Pending native AST owner extension/review for switch/case, structured type aliases and typed assertions in these exact sources.',
        native_formatter_status='No pinned native formatting qualification for these sources.',
        profiles={label: dict(source=str(source.relative_to(ROOT)), **metrics.measure(source.read_text(), encoder),
            normalized_source_units=None, canonical_formatted_loc=None,
            source_count_qualified=False) for label, source in native.SOURCES.items()},
        chart_admission=False, native_processes_started=0)


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
    print(json.dumps(dict(status='checked' if args.check else 'written', profiles=result['profiles'])), flush=True)
