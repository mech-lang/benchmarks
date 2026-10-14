"""Capture actual reviewed source digests and launch one original22 replay."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
P = NEW / 'prolog-comparison/20261013/revisions/original-source-admission-v1'
OUT = NEW / 'continuation/jobs/prolog-original22-source-capture-v1'
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


print('WAIT common: freeze reviewed Prolog source22 replay and launch once', flush=True)
with Path('/tmp/mech-clbg-timing.lock').open('r+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    held, named = os.fstat(lock.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
    assert not OUT.exists()
    assert not (P.parents[1] / 'source-counts/original22-replay-v1').exists()
    assert not (NEW / 'continuation/owned-jobs/prolog-original22-owner-replay-v1').exists()
    OUT.mkdir(parents=True)
    pins = {}
    for name in ('replay.py', 'evidence.py', 'REVIEW.md'):
        source = P / name
        assert source.is_file() and not source.is_symlink()
        source.chmod(0o444)
        pins[str(source)] = sha(source)
    scored = OLD / 'prolog-comparison/20261013/revisions/scored-work-review-v1/REVIEW.md'
    assert scored.read_bytes() == (NEW / scored.relative_to(OLD)).read_bytes()
    assert not scored.stat().st_mode & 0o222
    pins[str(scored)] = sha(scored)
    image = Path(PYTHON).resolve(strict=True)
    assert sha(image) == 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
    pins[str(image)] = sha(image)
    launcher = NEW / 'continuation/launch_durable_v1.py'
    pins[str(launcher)] = sha(launcher)
    argv = [PYTHON, '-I', '-S', '-B', '-u', str(P / 'replay.py'),
        '--worker-sha256', pins[str(P / 'replay.py')], '--evidence-sha256', pins[str(P / 'evidence.py')],
        '--review-sha256', pins[str(P / 'REVIEW.md')], '--scored-review-sha256', pins[str(scored)]]
    receipt = dict(status='reviewed-Prolog-original22-source-captured-awaiting-actual-replay',
        pins=pins, target_command=argv, cwd=str(NEW.parents[1]), common_mutex_inode=held.st_ino,
        independent_source_review='APL full three-file source acceptance; no blocker',
        subject_runs=0, preparation_or_fixture_reexecutions=0, automatic_retry=False, qualification_granted=False)
    with (OUT / 'receipt.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    (OUT / 'receipt.json').chmod(0o444)
    actual = subprocess.run([PYTHON, '-I', '-S', '-B', '-u', str(launcher),
        '--job', 'prolog-original22-owner-replay-v1', '--cwd', str(NEW.parents[1]), '--command-json', json.dumps(argv)],
        capture_output=True, check=False)
    (OUT / 'launch.stdout').write_bytes(actual.stdout)
    (OUT / 'launch.stderr').write_bytes(actual.stderr)
    assert actual.returncode == 0 and actual.stderr == b'', actual
    print(json.dumps(dict(receipt=str(OUT / 'receipt.json'), receipt_sha256=sha(OUT / 'receipt.json'),
        source_pins=pins, durable_launch=json.loads(actual.stdout))), flush=True)
