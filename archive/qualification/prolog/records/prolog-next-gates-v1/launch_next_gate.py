"""Launch exactly one next reviewed gate after verified actual closure."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
CLBG = HOST / 'benchmarks/clbg'
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
WORK = CLBG / 'prolog-comparison/20261013/revisions/prepared-work-v2'
READER = CLBG / 'loc-normalization/20261013/prolog-proposal-v3'
CAPTURE = NEW / 'continuation/jobs/prolog-next-gates-source-capture-v1'
PY = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
SIX = NEW / 'continuation/jobs/prolog-prepared-work-six-v2-closed-review/receipt.json'
SIX_SHA = '1257cb69626a1f1fd4fbfa051329c80b2023875800a51a01dc5696144b92e43f'
WORK_SHA = '379a3d6e2f5e5aad5af89b78c436db79bb3b5c01067266de40583b25f1ee67c9'
READER_SHA = 'f7a6ea214d92da47f3f00f565d1651ca3c49f02b437fcb9117d3641f0dbf63e8'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path, digest):
    assert sha(path) == digest and not path.stat().st_mode & 0o222, path
    return json.loads(path.read_bytes())


parser = argparse.ArgumentParser()
parser.add_argument('--gate', choices=('reader', 'work'), required=True)
parser.add_argument('--reader-closed-sha256')
args = parser.parse_args()
assert bool(args.reader_closed_sha256) is (args.gate == 'work')
print('WAIT common: launch reviewed Prolog ' + args.gate, flush=True)
with Path('/tmp/mech-clbg-timing.lock').open('r+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    held, named = os.fstat(lock.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
    capture = read(CAPTURE / 'receipt.json', '36827f87daba0ca932baf586348480d4d482ae40c706906cfb9ad8f881ba1f9d')
    assert sha(capture['launcher']) == capture['launcher_sha256']
    six = read(SIX, SIX_SHA)
    assert six['status'] == 'passed-closed-six-Prolog-work-fixtures' and six['error'] is None
    assert six['metrics'] == dict(tests=6, new_native_commands=0) and six['verified_pins'] == 14652
    if args.gate == 'reader':
        packet = read(CAPTURE / 'reader-source-packet.json', READER_SHA)
        command = [PY, '-I', '-S', '-B', '-u', str(READER / 'run_fixtures.py'),
            '--packet', str(CAPTURE / 'reader-source-packet.json'), '--packet-sha256', READER_SHA,
            '--output', str(READER / 'jobs/reader31-v1')]
        name, output = 'prolog-original-reader31-v3', READER / 'jobs/reader31-v1'
    else:
        closed = read(NEW / 'continuation/jobs/prolog-original-reader31-v3-closed-review/receipt.json', args.reader_closed_sha256)
        assert closed['status'] == 'passed-closed-Prolog-reader31' and closed['metrics']['tests'] == 31 and closed['error'] is None
        packet = read(CAPTURE / 'work-source-packet.json', WORK_SHA)
        command = [PY, '-I', '-S', '-B', '-u', str(WORK / 'run.py'), '--work-probes',
            '--packet', str(CAPTURE / 'work-source-packet.json'), '--packet-sha256', WORK_SHA,
            '--fixture-owner', str(CLBG / 'continuation/owned-jobs/prolog-prepared-work-six-v2'),
            '--fixture-terminal-sha256', six['durable_terminal_sha256'],
            '--fixture-report-sha256', six['report_sha256'], '--fixture-body-sha256', six['body_terminal_sha256']]
        name, output = 'prolog-prepared-work-thirty-v2', WORK.parents[1] / 'work-qualification/prepared-work-v2-probes-v1'
    for path, digest in packet['pins'].items():
        assert sha(path) == digest
    assert not output.exists() and not (CLBG / 'continuation/owned-jobs' / name).exists()
    result = subprocess.run([PY, '-I', '-S', '-B', '-u', capture['launcher'],
        '--job', name, '--cwd', str(HOST), '--command-json', json.dumps(command)],
        capture_output=True, check=False)
    destination = NEW / 'continuation/jobs' / (name + '-launch-copy')
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'stdout').write_bytes(result.stdout)
    (destination / 'stderr').write_bytes(result.stderr)
    (destination / 'result.json').write_text(json.dumps(dict(exit_status=result.returncode,
        stdout_sha256=sha(destination / 'stdout'), stderr_sha256=sha(destination / 'stderr'),
        command=command, cwd=str(HOST), automatic_retry=False, qualification_granted=False), indent=2) + '\n')
    assert result.returncode == 0 and result.stderr == b'', result
    print(result.stdout.decode(), end='', flush=True)
