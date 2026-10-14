#!/usr/bin/env python3
"""Locate a historical benchmark path after the repository reorganization."""
from pathlib import Path
import argparse
import csv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='original repository path or path relative to benchmarks/clbg')
    args = parser.parse_args()
    path = args.path
    if '/benchmarks/clbg/' in path:
        path = 'benchmarks/clbg/' + path.split('/benchmarks/clbg/', 1)[1]
    candidates = {path, 'benchmarks/clbg/' + path}
    with (ROOT / 'migration/reorganization-paths.tsv').open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['original_path'] in candidates:
                print(ROOT / row['current_path'])
                return
    parser.error('path is not in the preserved archive map')


if __name__ == '__main__':
    main()
