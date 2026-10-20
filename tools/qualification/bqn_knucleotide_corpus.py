"""Replay all retained k-nucleotide edge cases against pinned BQN candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = [c for c in json.loads((CORPUS/'manifest.json').read_text())['cases'] if c['benchmark'] == 'knucleotide']
    reports = []
    for case in cases:
        for field in ['stdin', 'expected']:
            path = CORPUS/case[field]['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == case[field]['sha256']
        directory = args.output/case['case']
        subprocess.run([sys.executable, str(ROOT/'tools/qualification/bqn_knucleotide_run.py'),
            '--sources', *args.sources, '--input', str(CORPUS/case['stdin']['path']),
            '--expected', str(CORPUS/case['expected']['path']), '--output', str(directory)], check=True)
        reports.append({'case': case['case'], 'report': str(directory.relative_to(ROOT)/'report.json'),
            'sha256': hashlib.sha256((directory/'report.json').read_bytes()).hexdigest()})
    report = {'schema': 'bqn-knucleotide-corpus.v1', 'status': 'PASSED', 'chart_admission': False,
        'case_count': len(cases), 'sources': args.sources, 'reports': reports,
        'controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'corpus_sha256': hashlib.sha256((CORPUS/'manifest.json').read_bytes()).hexdigest()}
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')

if __name__ == '__main__': main()
