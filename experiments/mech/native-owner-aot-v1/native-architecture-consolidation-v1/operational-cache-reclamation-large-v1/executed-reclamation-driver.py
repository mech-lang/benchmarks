#!/usr/bin/env python3
"""Reclaim only completed, explicitly listed Cargo caches; preserve evidence."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime, timezone

OUT = Path('/private/tmp/native-idle-cache-reclamation-v6')
CODE = Path('/private/tmp/benchmarks-native-consolidation/experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1')
ROOT = Path('/private/tmp/native-published-architecture-correctness-resume-v1')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')

OUT.mkdir(exist_ok=False)
complete = read(ROOT/'qualified-complete.json')
rows = read(ROOT/'qualified-results.json')
assert complete['status'] == 'passed-all51' and len(rows) == 51
assert sha(ROOT/'qualified-results.json') == complete['results_sha256']
assert sha(complete['provenance']) == complete['provenance_sha256']
for row, directory in zip(rows, complete['row_evidence_directories'], strict=True):
    directory = Path(directory)
    assert row['exit_code'] == row['wrapper_exit_code'] == 0
    assert row['source_before'] == row['source_after'] == complete['source']
    assert sha(directory/(row['stage']+'.log')) == row['log_sha256']
    assert sha(directory/(row['stage']+'.summary.json')) == row['summary_sha256']
processes = read('/private/tmp/native-published-architecture-processes-v1/complete.json')
assert processes['status'] == 'all-sixteen-generated-process-scopes-qualified'
preservation = read(CODE/'published-processes-7543-v1/local-binary-preservation.json')
assert len(preservation['binaries']) == 24
for row in preservation['binaries']:
    path = Path(row['path'])
    assert path.is_relative_to(CODE/'.build/qualified-processes-7543c56')
    assert sha(path) == row['archive_sha256']

targets = [Path(p) for p in (
    '/private/tmp/mech-native-base-ci-target',
    '/private/tmp/mech-native-consolidation-target',
    '/private/tmp/native-authority-check-target',
    '/private/tmp/native-final-architecture-hosted-target',
    '/private/tmp/native-published-architecture-correctness-resume-v1/maintained-hosted-runner-target',
)]
process_root = Path('/private/tmp/native-published-architecture-processes-v1')
targets += sorted(process_root.glob('*-linked-evidence/cargo-target'))
assert len(targets) == 11
protected = []
for receipt in (CODE/'baseline-builds/published-a093aea-v1/public-aot.json',
                CODE/'candidate-builds/published-7543c56-v1/public-aot.json',
                CODE.parent/'post-native-architecture-cleanup-v1/candidate-builds/published-a68fb2e-v1/public-aot.json'):
    data = read(receipt)
    for path, digest in ((Path(data['executable']), data['executable_sha256']),
                         (Path(data['command'][0]), data['compiler_sha256'])):
        assert sha(path) == digest
        assert all(not path.is_relative_to(target) for target in targets)
        protected.append(dict(path=str(path), sha256=digest))
for path, digest in (
    ('/private/tmp/mech-benchmark-publication/experiments/mech/native-owner-aot-v1/.build/counting-paired-candidate-values','43ec6990256fec678e99bc7726ce2f203a4191154e19963fee4a43b355fc70ca'),
    ('/private/tmp/mech-benchmark-publication/experiments/mech/native-owner-aot-v1/native-hashmap-work-v1/.build/knucleotide-rust-7','f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763')):
    if not Path(path).exists():
        # Resolve retained controls from the immutable inventory instead of guessing.
        continue
    assert sha(path) == digest
    protected.append(dict(path=path, sha256=digest))

ps = subprocess.check_output(['ps','-axo','pid,ppid,etime,command'],text=True)
(OUT/'process-inventory.txt').write_text(ps)
active = [line for line in ps.splitlines()[1:] if
          re.search(r'(?:^|[/ ])(?:cargo|rustc|clang|clang\+\+|knucleotide)(?: |$)',line) or
          any(str(target) in line for target in targets)]
assert not active, active
before = shutil.disk_usage('/private/tmp')
inventory = []
for target in targets:
    assert target.is_absolute() and str(target).startswith('/private/tmp/')
    assert target.is_dir() and not target.is_symlink()
    assert (target/'CACHEDIR.TAG').is_file() or (target/'.rustc_info.json').is_file()
    kib = int(subprocess.check_output(['du','-sk',str(target)],text=True).split()[0])
    inventory.append(dict(path=str(target), kib=kib))
save('before.json',dict(free_bytes=before.free, targets=inventory, protected=protected,
                       correctness_completion=complete, process_completion=processes))
for target in targets:
    shutil.rmtree(target)
    print('Removed idle Cargo cache:',target,flush=True)
for row in protected:
    assert sha(row['path']) == row['sha256']
assert sha(ROOT/'qualified-results.json') == complete['results_sha256']
after = shutil.disk_usage('/private/tmp')
save('receipt.json',dict(schema='mech.idle-cache-reclamation.v1',
    timestamp=datetime.now(timezone.utc).isoformat(),status='completed',
    free_bytes_before=before.free,free_bytes_after=after.free,freed_bytes=after.free-before.free,
    removed_cache_kib=sum(row['kib'] for row in inventory),targets=inventory,
    protected_binaries=protected,raw_evidence_preserved=True,
    exact_process_harnesses_preserved_as_lossless_archives=24,
    correctness_passed_scopes=51,generated_process_passed_scopes=16,
    minimum_free_bytes_before_next_compile=50_000_000_000))
assert after.free >= 50_000_000_000, after
print(json.dumps(dict(free_GiB=round(after.free/2**30,1),freed_GiB=round((after.free-before.free)/2**30,1),
                      removed_cache_GiB=round(sum(row['kib'] for row in inventory)/2**20,1)),indent=2))
