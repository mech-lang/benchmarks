"""Capture the reviewed existing Prolog packets and launch only six fixtures."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
CLBG = HOST / 'benchmarks/clbg'
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
WORK = CLBG / 'prolog-comparison/20261013/revisions/prepared-work-v2'
READER = CLBG / 'loc-normalization/20261013/prolog-proposal-v3'
PY = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
OUT = NEW / 'continuation/jobs/prolog-next-gates-source-capture-v1'
LAUNCHER = CLBG / 'continuation/launch_durable_v1.py'
WORK_FILES = ('run.py', 'qualified_preparation.py', 'fixture_runner.py',
    'instrument_sources.py', 'work_proofs.py', 'test_work_proofs.py', 'observer.pl', 'REVIEW.md')
READER_FILES = ('run_fixtures.py', 'foreign_prolog.py', 'test_prolog.py', 'scan_source.pl', 'REVIEW.md')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


assert sys.dont_write_bytecode and Path(sys.executable).resolve() == Path(PY).resolve()
print('WAIT common: freeze reviewed Prolog13 and launch six pure fixtures', flush=True)
with Path('/tmp/mech-clbg-timing.lock').open('r+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    held, named = os.fstat(lock.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
    assert not OUT.exists()
    for path in (WORK.parents[1] / 'work-qualification/prepared-work-v2-fixtures-v1',
                 WORK.parents[1] / 'work-qualification/prepared-work-v2-probes-v1',
                 READER / 'jobs/reader31-v1'):
        assert not path.exists(), ('Preserve existing output', path)
    for name in ('prolog-prepared-work-six-v2', 'prolog-original-reader31-v3', 'prolog-prepared-work-thirty-v2'):
        assert not (CLBG / 'continuation/owned-jobs' / name).exists(), name
    OUT.mkdir(parents=True)
    authored = [WORK / name for name in WORK_FILES] + [READER / name for name in READER_FILES]
    captures = {}
    for path in authored:
        assert path.is_file() and not path.is_symlink()
        counterpart = NEW / path.relative_to(CLBG)
        assert counterpart.is_file() and path.read_bytes() == counterpart.read_bytes(), path
        path.chmod(0o444)
        counterpart.chmod(0o444)
        captures[str(path.resolve())] = sha(path)
    image = Path(PY).resolve(strict=True)
    captures[str(image)] = sha(image)
    work_pins = {str((WORK / name).resolve()): captures[str((WORK / name).resolve())] for name in WORK_FILES}
    work_pins[str(image)] = captures[str(image)]
    reader_sources = [READER / name for name in READER_FILES] + [WORK / 'qualified_preparation.py', WORK / 'REVIEW.md']
    reader_pins = {str(path.resolve()): captures[str(path.resolve())] for path in reader_sources}
    reader_pins[str(image)] = captures[str(image)]
    work_packet, reader_packet = OUT / 'work-source-packet.json', OUT / 'reader-source-packet.json'
    save(work_packet, dict(schema='frozen-prolog-prepared-work-v2', pins=work_pins))
    save(reader_packet, dict(schema='frozen-prolog-reader31-actual-preparation-v3', pins=reader_pins))
    launcher_digest = sha(LAUNCHER)
    assert LAUNCHER.read_bytes() == (NEW / 'continuation/launch_durable_v1.py').read_bytes()
    argv = [PY, '-I', '-S', '-B', '-u', str(WORK / 'run.py'), '--fixtures',
        '--packet', str(work_packet), '--packet-sha256', sha(work_packet)]
    receipt = dict(status='reviewed-source-packets-captured-awaiting-six-fixtures',
        captured_at=datetime.now(timezone.utc).isoformat(), mutex_inode=held.st_ino,
        work_packet=str(work_packet), work_packet_sha256=sha(work_packet), work_pin_count=len(work_pins),
        reader_packet=str(reader_packet), reader_packet_sha256=sha(reader_packet), reader_pin_count=len(reader_pins),
        authored_file_count=len(authored), launcher=str(LAUNCHER), launcher_sha256=launcher_digest,
        target_command=argv, cwd=str(HOST), qualification_granted=False, automatic_retry=False,
        successful_preparation_reexecutions=0, original_QLF_rebuilds=0, original_WAM_reexecutions=0)
    save(OUT / 'receipt.json', receipt)
    result = subprocess.run([PY, '-I', '-S', '-B', '-u', str(LAUNCHER),
        '--job', 'prolog-prepared-work-six-v2', '--cwd', str(HOST), '--command-json', json.dumps(argv)],
        capture_output=True, check=False)
    (OUT / 'launch.stdout').write_bytes(result.stdout)
    (OUT / 'launch.stderr').write_bytes(result.stderr)
    save(OUT / 'launch-result.json', dict(exit_status=result.returncode,
        stdout_sha256=sha(OUT / 'launch.stdout'), stderr_sha256=sha(OUT / 'launch.stderr'),
        source_capture_sha256=sha(OUT / 'receipt.json'), automatic_retry=False, qualification_granted=False))
    assert result.returncode == 0 and result.stderr == b'', result
    assert sha(LAUNCHER) == launcher_digest
    print(json.dumps(dict(receipt=str(OUT / 'receipt.json'), receipt_sha256=sha(OUT / 'receipt.json'),
        work_packet_sha256=sha(work_packet), reader_packet_sha256=sha(reader_packet),
        durable_launch=json.loads(result.stdout))), flush=True)
