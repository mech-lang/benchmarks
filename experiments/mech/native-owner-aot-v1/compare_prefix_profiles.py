"""Compare explicitly selected diagnostic prefix captures without Rust mixing."""
import argparse
from collections import Counter
import json
from pathlib import Path
from profile_hotspots import summarize
from analyze_profile import sha

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', required=True)
parser.add_argument('--baseline', required=True)
parser.add_argument('--receipt', required=True)
args = parser.parse_args()
out = HERE / args.receipt
out.mkdir(exist_ok=False)
reports = {}
for label, name in [('candidate', args.candidate), ('baseline', args.baseline)]:
    capture = json.loads((HERE / name / 'results.json').read_text())
    analysis = json.loads((HERE / name / 'analysis.json').read_text())
    assert capture['selected_bases'] == 1000000 and analysis['machine_code_identical'] and analysis['completed_output_verified']
    assert analysis['selected_capture_indices'] == [0] and analysis['attempted_capture_count'] == 3
    records, totals, count = [], Counter(), 0
    for item in analysis['samples']:
        workers = {t['thread'] for t in item['threads'] if t['observed_native_worker']}
        assert len(workers) == 7
        record = summarize(HERE / item['stacks'], workers, 'mech', item['observed_workers']['thread_samples'])
        assert record['stacks_sha256'] == item['stacks_sha256']
        records.append(record)
        totals.update(record['exclusive_buckets'])
        count += record['worker_observations']
    assert count > 0 and sum(totals.values()) == count
    reports[label] = dict(source_commit=analysis['source_commit'], timed_binary_sha256=analysis['timed_binary_sha256'],
                          profile_analysis=str((HERE / name / 'analysis.json').relative_to(HERE)),
                          profile_analysis_sha256=sha((HERE / name / 'analysis.json').read_bytes()),
                          worker_observations=count, buckets=dict(totals),
                          percent={k: 100*v/count for k,v in totals.items()}, samples=records)
result = dict(status='diagnostic-first-prefix-captures-compared', selected_bases=1000000, reports=reports,
              script_sha256=sha(Path(__file__).read_bytes()), classifier_sha256=sha((HERE / 'profile_hotspots.py').read_bytes()),
              taxonomy_version=4, benchmark_samples=0,
              scope='First pre-armed exact-byte executable-copy capture per subject, each observing seven workers. Each job attempted three captures; later empty/partial traces remain retained and are excluded by explicit index selection for coverage, never by timing. Cold-copy loader/sampler overhead and low observation counts limit causal claims; worker percentages include waits, are not wall-time shares and do not explain the entire warm-process regression. Rust full-input profiles are not mixed into this prefix comparison.')
(out / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
(out / 'classifier.py').write_bytes((HERE / 'profile_hotspots.py').read_bytes())
print(json.dumps({k:{'observations':v['worker_observations'],'percent':v['percent']} for k,v in reports.items()},indent=2))
