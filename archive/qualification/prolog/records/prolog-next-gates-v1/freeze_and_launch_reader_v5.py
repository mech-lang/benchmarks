"""Freeze the narrow source-path repair and launch only the corrected reader31."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
WORK = OLD / 'prolog-comparison/20261013/revisions/prepared-work-v2'
READER = NEW / 'loc-normalization/20261013/prolog-proposal-v5'
OUT = NEW / 'continuation/jobs/prolog-reader31-v5-source-capture-v1'
PY = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
FILES = ('run_fixtures.py', 'foreign_prolog.py', 'test_prolog.py', 'scan_source.pl', 'REVIEW.md')


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


print('WAIT common: freeze repaired Prolog reader31 and launch once', flush=True)
with Path('/tmp/mech-clbg-timing.lock').open('r+') as common:
    fcntl.flock(common, fcntl.LOCK_EX)
    actual, named = os.fstat(common.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
    assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
    assert not OUT.exists() and not (READER / 'jobs/reader31-v1').exists()
    assert not (NEW / 'continuation/owned-jobs/prolog-original-reader31-v5').exists()
    failed = NEW / 'continuation/jobs/prolog-original-reader31-v4-closed-review/receipt.json'
    assert sha(failed) == 'c41ca6eab3e8a8f43ac5842c566480ece9806e3af9eb557576b7e05775db6229'
    OUT.mkdir(parents=True)
    prior_capture = NEW / 'continuation/jobs/prolog-reader31-v4-source-capture-v1/receipt.json'
    assert sha(prior_capture) == 'f2878f94ca8af1ae0ddb04ae347ea3a4f78fe3d0d70b7ccd99fc0647d9020596'
    prior_value = json.loads(prior_capture.read_bytes())
    grounding = prior_capture.with_name('path-grounding.json')
    assert sha(grounding) == prior_value['path_grounding_sha256']
    prior = prior_capture.with_name('reader-source-packet.json')
    assert sha(prior) == '027a652b2c535f1343c3c76a8eca3ff543bcd9b051409c21f9f2c708ccaca6bc'
    old_pins = json.loads(prior.read_bytes())['pins']
    for path, digest in old_pins.items(): assert sha(path) == digest
    sources = [READER / name for name in FILES] + [WORK / 'qualified_preparation.py', WORK / 'REVIEW.md']
    pins = {}
    for path in sources:
        assert path.is_file() and not path.is_symlink()
        path.chmod(0o444)
        pins[str(path.resolve())] = sha(path)
    image = Path(PY).resolve(strict=True)
    assert sha(image) == old_pins[str(image)]
    pins[str(image)] = sha(image)
    packet = OUT / 'reader-source-packet.json'
    save(packet, dict(schema='frozen-prolog-reader31-actual-preparation-v5', pins=pins))
    launcher = NEW / 'continuation/launch_durable_v1.py'
    assert launcher.read_bytes() == (OLD / 'continuation/launch_durable_v1.py').read_bytes()
    command = [PY, '-I', '-S', '-B', '-u', str(READER / 'run_fixtures.py'),
        '--packet', str(packet), '--packet-sha256', sha(packet), '--output', str(READER / 'jobs/reader31-v1')]
    save(OUT / 'receipt.json', dict(status='actual-reader-v5-source-captured-awaiting31',
        captured_at=datetime.now(timezone.utc).isoformat(), packet=str(packet), packet_sha256=sha(packet),
        pin_count=len(pins), pins=pins, preserved_failed_v4_sha256=sha(failed),
        retained_path_grounding=dict(path=str(grounding), sha256=sha(grounding)), target_command=command,
        cwd=str(NEW.parents[1]), launcher=str(launcher), launcher_sha256=sha(launcher),
        preserved_six_fixture_sha256='1257cb69626a1f1fd4fbfa051329c80b2023875800a51a01dc5696144b92e43f',
        automatic_retry=False, successful_fixture_reexecutions=0, original_preparation_reexecutions=0))
    result = subprocess.run([PY, '-I', '-S', '-B', '-u', str(launcher),
        '--job', 'prolog-original-reader31-v5', '--cwd', str(NEW.parents[1]), '--command-json', json.dumps(command)],
        capture_output=True, check=False)
    (OUT / 'launch.stdout').write_bytes(result.stdout)
    (OUT / 'launch.stderr').write_bytes(result.stderr)
    save(OUT / 'launch-result.json', dict(exit_status=result.returncode,
        stdout_sha256=sha(OUT / 'launch.stdout'), stderr_sha256=sha(OUT / 'launch.stderr')))
    assert result.returncode == 0 and result.stderr == b'', result
    print(json.dumps(dict(receipt=str(OUT / 'receipt.json'), receipt_sha256=sha(OUT / 'receipt.json'),
        packet_sha256=sha(packet), worker_sha256=pins[str((READER / 'run_fixtures.py').resolve())],
        durable_launch=json.loads(result.stdout))), flush=True)
