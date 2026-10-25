"""Recheck the separate copy-phase study without executing native subjects."""
import importlib.util
from pathlib import Path
import sys
STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
PHASE = HERE / 'preparation-phase-v1'
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import process, read, source_state, check_native, OUTPUT_SHA
spec = importlib.util.spec_from_file_location('phase_parse', PHASE / 'parse.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
plan = read(STUDY / 'phase-plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
out = STUDY / 'phase-comparison-v1'
report = read(out / 'results.json')
assert report['status'] == 'copy-phase-outputs-original-updates-and-boundaries-verified'
assert report['source_before'] == report['source_after'] == before
assert report['plan_sha256'] == process.sha(STUDY / 'phase-plan.json')
assert report['driver_sha256'] == process.sha(STUDY / 'phase-compare.py')
assert report['parser_sha256'] == process.sha(PHASE / 'parse.py')
assert report['probe_sha256'] == process.sha(PHASE / 'phase_probe.rs')
assert report['primary_benchmark_samples'] == 0 and len(report['samples']) == 12
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
with inp.open('rb') as source:
    rows = sum(chunk.count(b'\n') for chunk in iter(lambda: source.read(1024 * 1024), b''))
for sample in report['samples']:
    folder = out / f"{sample['order']:02d}-{sample['position']}-{sample['subject']}"
    assert process.sha(folder / 'process.json') == sample['process_sha256']
    assert process.sha(folder / 'stdout.bin') == sample['stdout_sha256'] == OUTPUT_SHA
    assert parser.parse(folder / 'stderr.bin') == sample['records'] == read(folder / 'phases.json')
    assert sample['records']['rows']['direct_rows'] == rows
    native = folder.with_name(folder.name + '.native.json')
    assert process.sha(native) == sample['native_sha256'] and check_native(native) == sample['native']
build = read(PHASE / 'build-linecopy-v2/results.json')
assert build['source_before'] == build['source_after'] == before
assert build['guest_object_sha256'] == read(STUDY / 'verification.json')['object_sha256']
paths = list(out.rglob('process.json')) + list((PHASE / 'build-linecopy-v2').rglob('process.json'))
assert len(paths) == 14
for path in paths:
    r = read(path)
    assert r['exit_status'] == 0 and r['inherited_common_mutex'] and r['reaped'] and r['group_closed']
    assert not r['cleanup_errors'] and not r['signals']
assert source_state() == before
process.save(STUDY / 'phase-verification.json', dict(
    status='copy-phase-build-and-13-diagnostic-executions-verified', source=before,
    production_source=plan['production_source'], retained_process_receipts=len(paths),
    primary_benchmark_samples=0, original_rows_per_full_capture=rows,
    primary_verification_sha256=process.sha(STUDY / 'verification.json'),
    driver_sha256=process.sha(Path(__file__))))
print('Verified 14 additional terminal receipts, unchanged guest and complete row coverage in all 12 full captures.')
