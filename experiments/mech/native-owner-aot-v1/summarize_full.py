"""Summarize complete full-input cohorts without dropping any observations."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('runs', nargs='+')
args = parser.parse_args()
assert len(args.runs) >= 3 and len(set(args.runs)) == len(args.runs)
reports = [json.loads((HERE / run / 'results.json').read_text()) for run in args.runs]
identity = ['source_commit', 'baseline_source_commit', 'source_sha256', 'input_sha256',
            'candidate_sha256', 'baseline_sha256', 'rust_sha256', 'launch_sha256',
            'selected_bases', 'expected_table_updates', 'require_packed_map',
            'require_packed_ssa', 'require_parallel_tasks', 'minimum_parallel_peak']
first = reports[0]
samples = {}
receipts = []
for run, report in zip(args.runs, reports):
    assert report['status'] == 'full-output-and-update-counts-verified'
    assert all(report.get(key) == first.get(key) for key in identity)
    labels = [sample['label'] for sample in report['samples']]
    assert len(labels) == len(set(labels)) and set(labels) == set(s['label'] for s in first['samples'])
    for sample in report['samples']:
        label = sample['label']
        process = json.loads((HERE / run / label / 'process.json').read_text())
        assert process['exit_status'] == 0 and process['reaped'] and process['group_closed']
        assert not process['cleanup_errors'] and process['quantitative_benchmark']
        assert sample['seconds'] == process['elapsed_seconds']
        output = (HERE / run / label / 'stdout.bin').read_bytes()
        assert hashlib.sha256(output).hexdigest() == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        samples.setdefault(label, []).append(sample['seconds'])
    path = HERE / run / 'results.json'
    receipts.append({'path': str(path.relative_to(HERE)),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'order': labels})
medians = {label: statistics.median(values) for label, values in samples.items()}
summary = {key: first.get(key) for key in identity}
summary.update(status='all-cohorts-and-outputs-verified', cohort_count=len(reports),
               scope='Fresh complete processes, including secured startup/shutdown; no excluded warmups or outliers; cohorts run serially in their recorded orders',
               evidence=receipts, samples_seconds=samples, median_seconds=medians,
               stdev_seconds={label: statistics.stdev(values) for label, values in samples.items()},
               x_rust={label: value / medians['rust'] for label, value in medians.items()},
               speedup_over_parent=medians['baseline'] / medians['mech'] if 'baseline' in medians else None)
out = HERE / args.receipt
out.mkdir(exist_ok=False)
(out / 'results.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
