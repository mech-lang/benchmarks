#!/usr/bin/env python3
"""Serial public builds using the unchanged study and bounded process owners."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/private/tmp/benchmarks-native-consolidation')
CODE = ROOT / 'experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1'
OUT = Path('/private/tmp/native-published-public-builds-v1')
PREP = Path('/private/tmp/native-published-public-build-preparation-v1.py')
TARGET = Path('/private/tmp/mech-native-consolidation-perf-target')
JOBS = [
    ('baseline', CODE, 'build-baseline.py', 'a093aea452340a70c1e72a1f58bd831f1edef70f',
     '/private/tmp/mech-native-base-ci-repair-next', 'published-a093aea-v1', 'baseline-builds', []),
    ('architecture', CODE, 'build-candidate.py', '7543c56d5efc4df30d0b60961922024d74caa9d7',
     '/private/tmp/mech-native-consolidation-final', 'published-7543c56-v1', 'candidate-builds', []),
    ('cleanup', CODE.parent / 'post-native-architecture-cleanup-v1', 'build-candidate.py',
     'a68fb2e60d7afbc59bc146f8878b17181e275645', '/private/tmp/mech-post-native-authority-cleanup-v2',
     'published-a68fb2e-v1', 'candidate-builds', ['--study', 'post-native-architecture-cleanup-v1']),
]
OUT.mkdir(exist_ok=False)
shutil.copyfile(__file__, OUT / 'executed-driver.py')
rows = []
for name, base, script, head, workspace, run_id, kind, selection in JOBS:
    commands = [
        [sys.executable, str(PREP), 'clean', name],
        [sys.executable, str(CODE / script), *selection, '--workspace', workspace,
         '--target-dir', str(TARGET), '--run-id', run_id],
        [sys.executable, str(PREP), 'validate', name,
         '--receipt', f'{kind}/{run_id}/public-aot.json', '--commit', head],
    ]
    for stage, command in zip(('prepare', 'build', 'validate'), commands):
        print(name, stage, flush=True)
        with (OUT / f'{name}-{stage}.log').open('wb') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        row = dict(subject=name, stage=stage, head=head, command=command,
                   exit_code=result.returncode,
                   log_sha256=hashlib.sha256((OUT / f'{name}-{stage}.log').read_bytes()).hexdigest())
        rows.append(row)
        (OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
        if result.returncode:
            raise RuntimeError(f'{name}/{stage} failed; raw attempt retained')
receipts = [base / kind / run_id / 'adoption-validation.json'
            for _, base, _, _, _, run_id, kind, _ in JOBS]
reports = [json.loads(p.read_text()) for p in receipts]
assert all(r['guest_artifacts'] == reports[0]['guest_artifacts'] for r in reports)
(OUT / 'complete.json').write_text(json.dumps(dict(
    status='three-published-head-public-builds-validated-six-guest-artifacts-identical',
    receipts=[dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in receipts],
    guest_artifacts=reports[0]['guest_artifacts'], primary_timing_samples=0,
    performance_qualified=False), indent=2) + '\n')
print('All three public builds validated; no timing samples collected.', flush=True)
