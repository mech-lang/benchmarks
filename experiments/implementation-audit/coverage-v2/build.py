#!/usr/bin/env python3
"""Extend the frozen exact-source coverage reconciliation with the C# review."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / 'coverage-v1/build.py'
BASE_SHA = '8499a06fee0c7e5834d73c9b66cda8fa9a67f5eed10101900faa5474c706d753'


def build():
    raw = BASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_SHA:
        raise ValueError('Frozen coverage reconciliation changed')
    spec = importlib.util.spec_from_file_location('frozen_exact_source_coverage_v1', BASE)
    base = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(BASE), 'exec'), base.__dict__)
    base.SUPPLEMENTS += (('csharp', ROOT / 'experiments/csharp/source-review-v1/review.json'),)
    result = base.build()
    result['schema'] = 'exact-source-review-coverage.v2'
    result['inputs'].append(base.pin(Path(__file__)))
    result['reconciliation'] = dict(base_builder=base.pin(BASE),
        extension='Append the exact C# static review; preserve prior coverage and all native/count qualification boundaries.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    path = HERE / 'coverage.json'
    if args.check:
        if json.loads(path.read_bytes()) != result:
            raise ValueError('Coverage reconciliation differs')
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result['summary']))
