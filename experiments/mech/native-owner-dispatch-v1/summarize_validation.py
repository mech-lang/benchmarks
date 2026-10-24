"""Summarize completed serial validation receipts, including failed attempts."""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('receipts', nargs='+')
args = parser.parse_args()
for name in args.receipts:
    folder = HERE / name
    process = json.loads((folder / 'process.json').read_text())
    provenance = json.loads((folder / 'source-provenance.json').read_text())
    assert process['reaped'] and process['group_closed'] and not process['cleanup_errors']
    assert process['inherited_common_mutex'] and not process['quantitative_benchmark']
    assert provenance['source_unchanged']
    stdout = (folder / 'stdout.bin').read_text()
    suites = [dict(result=result, passed=int(passed), failed=int(failed), ignored=int(ignored))
              for result, passed, failed, ignored in re.findall(
                  r'test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;', stdout)]
    if process['exit_status'] == 0:
        assert suites and all(suite['result'] == 'ok' and suite['failed'] == 0 for suite in suites)
    result = dict(status='passed' if process['exit_status'] == 0 else 'failed-attempt-retained',
                  source_commit=provenance['before']['commit'],
                  clean_revision_qualified=provenance['clean_revision_qualified'],
                  exit_status=process['exit_status'], suites=suites,
                  passed=sum(suite['passed'] for suite in suites),
                  failed=sum(suite['failed'] for suite in suites),
                  ignored=sum(suite['ignored'] for suite in suites),
                  passing_tests=re.findall(r'^test (.+) \.\.\. ok$', stdout, re.M),
                  failed_tests=re.findall(r'^test (.+) \.\.\. FAILED$', stdout, re.M),
                  all_owned_processes_reaped_and_groups_closed=True, benchmark_samples=0,
                  evidence_sha256={filename: hashlib.sha256((folder / filename).read_bytes()).hexdigest()
                                   for filename in ('process.json', 'source-provenance.json', 'stdout.bin', 'stderr.bin')},
                  summarizer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Completed test executions and immutable source snapshots; not timing observations.')
    (folder / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(receipt=name, status=result['status'], passed=result['passed'], failed=result['failed'])))
