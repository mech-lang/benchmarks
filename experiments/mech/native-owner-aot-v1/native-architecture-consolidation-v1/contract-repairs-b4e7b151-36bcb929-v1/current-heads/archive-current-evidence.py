#!/usr/bin/env python3
"""Publish exact-head contract/artifact receipts separately from frozen timings."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

LOCAL = Path(__file__).resolve().parent
STUDY = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1')
OUT = STUDY / 'contract-repairs-b4e7b151-36bcb929-v1'
comparison = json.loads((LOCAL / 'current-head-snapshot-comparison.json').read_text())
assert comparison['status'] == 'passed' and comparison['exactly_identical_files'] == 32
OUT.mkdir(exist_ok=False)
manifest = []
retained_local = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source, relative):
    destination = OUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == '.log' and source.stat().st_size > 256_000:
        destination = destination.with_name(destination.name + '.gz')
        with source.open('rb') as incoming, destination.open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as outgoing:
                shutil.copyfileobj(incoming, outgoing)
        encoding = 'gzip'
    else:
        shutil.copyfile(source, destination)
        encoding = 'identity'
    raw = source.read_bytes()
    archived = gzip.decompress(destination.read_bytes()) if encoding == 'gzip' else destination.read_bytes()
    assert raw == archived
    manifest.append({'source': str(source), 'archive_relative': str(destination.relative_to(OUT)),
                     'encoding': encoding, 'raw_bytes': len(raw), 'raw_sha256': sha(source),
                     'archive_sha256': sha(destination)})


for source in sorted(LOCAL.rglob('*')):
    if not source.is_file() or source.suffix == '.pyc' or '__pycache__' in source.parts:
        continue
    if source.name.endswith(('.resources.log', '.gz')):
        retained_local.append({'path': str(source), 'bytes': source.stat().st_size, 'sha256': sha(source),
                               'scope': 'Full diagnostic process tables and large non-timed test binaries remain retained locally'})
        continue
    copy(source, Path('current-heads') / source.relative_to(LOCAL))

base = Path('/private/tmp/native-934-admission-error-repair-v1')
for source in sorted(base.iterdir()):
    if not source.is_file() or source.name.endswith('.resources.log'):
        continue
    if source.suffix in {'.json', '.log', '.patch', '.py'} or source.name in {'native-test-executable-resumed'}:
        copy(source, Path('base-repair-validation') / source.name)

copy(Path('/private/tmp/native-stack-behavior-audit-v1/confirmed-findings.json'), Path('partial-compatibility-audit.json'))
readme = '''# Current-head contract and artifact validation

This evidence covers the repaired #934 head
`b4e7b15168c9caced1dc10f5a487bd151a2ba976` and architecture #935 head
`36bcb9292ed40676a4547c91588c96735785b139`. It collects no timing samples and
does not modify or qualify either historical frozen timing campaign.

- #934 CI run40533852218 passed. #935 run40533994980 attempt2 resumed only
  incomplete work after the earlier cancellation. The timestamped CI checkpoint
  here records progress, not a completed green result.
- The current #935 head has a [clean review with no findings](https://github.com/mech-lang/mech/pull/935#issuecomment-6451363674).
- All32 original/decoded object, descriptor, metadata and bytecode files are
  byte-identical between these two actual source heads. Both exact-one-test
  executions and complete process closure receipts passed. Baseline uses the
  byte-identical pinned harness overlay, removed after execution. A fresh Cargo
  target was used for #934; every workspace package artifact was removed before
  switching that target to #935. The two test executables were hash-pinned and
  retained locally before any later cache use.
- The architecture patch remains byte-for-byte identical to the historical
  `a093aea` to `7543c56` patch. The repairs restore indexed missing-key rejection,
  existing-key map footprint accounting, unused-Bool-schema admission and exact
  bounded-snapshot resource errors. No limit or failing expectation is relaxed.
- At repaired #934, all77 selected native tests pass: four structural-map tests
  and73 closed-map tests. Base-repair validation retains52 minimal-source,
  422 full-source and76 core-snapshot passes. The engine run has810 passes and
  one independently reproduced integration-baseline option-footprint failure;
  the raw failure is retained and is not relabelled as a passing scope.

The compatibility audit is partial. Historical 51-scope and16-process results
belong to `7543c56`, not this newer source. Current-head full correctness and
performance qualification remain separate requirements. The historical timing
studies still fail their original acceptance policy. This comparison is not an
adoption of these heads into those immutable timing plans.

`archive-manifest.json` pins every archived byte and lossless log compression.
Large non-timed test executables and diagnostic tables containing unrelated
processes remain retained locally with hashes in `retained-local.json`.
'''
(OUT / 'README.md').write_text(readme.replace('run405', 'run 405').replace('attempt2','attempt 2').replace('All32','All 32').replace('all77','all 77').replace('and73','and 73').replace('retains52','retains 52').replace('and76','and 76').replace('has810','has 810').replace('and16','and 16'))
(OUT / 'retained-local.json').write_text(json.dumps(retained_local, indent=2) + '\n')
(OUT / 'archive-manifest.json').write_text(json.dumps({'schema': 'mech.contract-repair-evidence.v1',
    'primary_timing_samples': 0, 'performance_qualified': False, 'files': manifest}, indent=2) + '\n')
print(json.dumps({'archive': str(OUT), 'files': len(manifest),
                  'bytes': sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
                  'performance_qualified': False}, indent=2))
