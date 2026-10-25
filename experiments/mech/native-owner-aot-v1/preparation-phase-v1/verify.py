"""Recheck retained raw observations without executing benchmark subjects."""
from pathlib import Path
import sys
STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import process, read, check_native, OUTPUT_SHA
from parse import parse

report = read(STUDY / 'full-capture-v1/results.json')
assert report['status'] == 'all-diagnostic-outputs-updates-and-phase-boundaries-verified'
assert report['source_before'] == report['source_after'] and not report['source_before']['status']
assert len(report['samples']) == 12 and report['primary_benchmark_samples'] == 0
assert report['plan_sha256'] == process.sha(STUDY / 'plan.json')
assert report['driver_sha256'] == process.sha(STUDY / 'capture.py')
assert report['parser_sha256'] == process.sha(STUDY / 'parse.py')
for sample in report['samples']:
    folder = STUDY / 'full-capture-v1' / f"{sample['order']:02d}-{sample['position']}-{sample['subject']}"
    assert process.sha(folder / 'process.json') == sample['process_sha256']
    assert process.sha(folder / 'stdout.bin') == sample['stdout_sha256'] == OUTPUT_SHA
    if sample['subject'] == 'mech':
        assert parse(folder / 'stderr.bin') == sample['records'] == read(folder / 'phases.json')
        assert check_native(folder.with_suffix('.native.json')) == sample['native']
receipts = list(STUDY.rglob('process.json'))
assert len(receipts) == 14
for path in receipts:
    r = read(path)
    assert r['exit_status'] == 0 and r['reaped'] and r['group_closed']
    assert not r['signals'] and not r['cleanup_errors'], path
print('Verified 14 terminal native process receipts, 12 full captures and original output/update checks.')
