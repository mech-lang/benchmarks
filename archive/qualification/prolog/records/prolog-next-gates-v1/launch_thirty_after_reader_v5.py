"""Launch the existing thirty work probes after actual six/reader31 closure."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OLD = HOST / 'benchmarks/clbg'
NEW = Path('/Users/cim310/mech-lang/benchmarks/benchmarks/clbg')
CAPTURE = NEW / 'continuation/jobs/prolog-next-gates-source-capture-v1'
PY = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path, digest):
    assert sha(path) == digest and not path.stat().st_mode & 0o222, path
    return json.loads(path.read_bytes())


print('WAIT common: launch only thirty reviewed Prolog work observations', flush=True)
with Path('/tmp/mech-clbg-timing.lock').open('r+') as common:
    fcntl.flock(common, fcntl.LOCK_EX)
    actual, named = os.fstat(common.fileno()), Path('/tmp/mech-clbg-timing.lock').stat()
    assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
    six = read(NEW / 'continuation/jobs/prolog-prepared-work-six-v2-closed-review/receipt.json',
        '1257cb69626a1f1fd4fbfa051329c80b2023875800a51a01dc5696144b92e43f')
    reader = read(NEW / 'continuation/jobs/prolog-original-reader31-v5-closed-review/receipt.json',
        '61aa28c91bb0504b9daa9d752943e79e223d0f8f0838ad9a17459f8de9d8c617')
    assert six['status'] == 'passed-closed-six-Prolog-work-fixtures' and six['metrics'] == dict(tests=6, new_native_commands=0)
    assert reader['status'] == 'passed-closed-Prolog-reader31' and reader['metrics']['tests'] == 31
    assert six['error'] is reader['error'] is None
    packet = CAPTURE / 'work-source-packet.json'
    packet_sha = '379a3d6e2f5e5aad5af89b78c436db79bb3b5c01067266de40583b25f1ee67c9'
    captures = read(packet, packet_sha)
    assert captures['schema'] == 'frozen-prolog-prepared-work-v2' and len(captures['pins']) == 9
    for path, digest in captures['pins'].items(): assert sha(path) == digest
    launch_capture = read(CAPTURE / 'receipt.json', '36827f87daba0ca932baf586348480d4d482ae40c706906cfb9ad8f881ba1f9d')
    assert sha(launch_capture['launcher']) == launch_capture['launcher_sha256']
    worker = OLD / 'prolog-comparison/20261013/revisions/prepared-work-v2/run.py'
    output = worker.parents[2] / 'work-qualification/prepared-work-v2-probes-v1'
    owner = OLD / 'continuation/owned-jobs/prolog-prepared-work-thirty-v2'
    assert not output.exists() and not owner.exists()
    argv = [PY, '-I', '-S', '-B', '-u', str(worker), '--work-probes', '--packet', str(packet),
        '--packet-sha256', packet_sha, '--fixture-owner', str(OLD / 'continuation/owned-jobs/prolog-prepared-work-six-v2'),
        '--fixture-terminal-sha256', six['durable_terminal_sha256'],
        '--fixture-report-sha256', six['report_sha256'], '--fixture-body-sha256', six['body_terminal_sha256']]
    result = subprocess.run([PY, '-I', '-S', '-B', '-u', launch_capture['launcher'],
        '--job', 'prolog-prepared-work-thirty-v2', '--cwd', str(HOST), '--command-json', json.dumps(argv)],
        capture_output=True, check=False)
    dest = NEW / 'continuation/jobs/prolog-prepared-work-thirty-v2-launch-copy'
    dest.mkdir(parents=True, exist_ok=False)
    (dest / 'stdout').write_bytes(result.stdout)
    (dest / 'stderr').write_bytes(result.stderr)
    (dest / 'result.json').write_text(json.dumps(dict(exit_status=result.returncode, command=argv,
        stdout_sha256=sha(dest / 'stdout'), stderr_sha256=sha(dest / 'stderr'),
        retained_reader_closure_sha256='61aa28c91bb0504b9daa9d752943e79e223d0f8f0838ad9a17459f8de9d8c617',
        automatic_retry=False, qualification_granted=False), indent=2) + '\n')
    assert result.returncode == 0 and result.stderr == b'', result
    print(result.stdout.decode(), end='', flush=True)
