"""One owned Julia diagnostic and a target-only administrator stack capture.

Run as cim310 after `sudo -v` in the same terminal. No settings are changed.
The unchanged controller owns, bounds, and cleans up the Julia/debugger children.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
ROOT = Path('/private/tmp/mech-benchmark-completion')
HERE = ROOT/'experiments/julia-aot/entry-dispatch-v1'
PRIVATE = Path('/private/tmp/mech-history-candidate-validation')
CONTROLLER = HERE/'controller.py'
CONTROLLER_SHA = '522ed3718398788aabe6410d4ce257175afb6dbef85acdfcc0c18cbfa96a156d'
INTAKE = PRIVATE/'julia-entry-tool-intake-v1/tool-intake.json'
INTAKE_SHA = 'f379276b43b96a11f6746e556256424eccc003426b5a0f37b5b8058f2811ed68'
PLAN = HERE/'plan-v4.json'
RUN = HERE/'run-v4'
SUPPLEMENT = PRIVATE/'julia-entry-run-v4-stack'


def checked(path, expected):
    assert path.is_file() and not path.is_symlink(), str(path)
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, str(path)
    return raw


def same_birth(kernel, expected):
    current = kernel.identity(expected['pid'])
    assert current and all(current[k] == expected[k] for k in
        ('pid', 'ppid', 'pgid', 'birth_seconds', 'birth_microseconds'))
    return current


def main():
    assert os.getuid() == 501 and os.geteuid() == 501, 'Run as cim310, not root.'
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    assert sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode
    controller = checked(CONTROLLER, CONTROLLER_SHA)
    checked(INTAKE, INTAKE_SHA)
    assert not PLAN.exists() and not RUN.exists() and not SUPPLEMENT.exists()
    # This never requests or reads a password. `sudo -v` must precede this script.
    subprocess.run(['/usr/bin/sudo', '-n', '-v'], check=True, timeout=10,
                   stdin=subprocess.DEVNULL)
    SUPPLEMENT.mkdir(mode=0o700)
    spec = importlib.util.spec_from_file_location('retained_julia_controller', CONTROLLER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(controller, str(CONTROLLER), 'exec'), module.__dict__)
    kernel_module = module.load_source('retained_julia_kernel_helpers',
        ROOT/'tools/qualification/kotlin_helpers.py',
        'd92e0b247d7d45bca1216a0e85335fe0e31a24cc1d607b4b97928115a232fd25')
    kernel = kernel_module.Kernel()
    prefix = [str(PYTHON), '-I', '-S', '-B', str(CONTROLLER)]
    subprocess.run(prefix + ['prepare', '--intake', str(INTAKE),
        '--intake-sha256', INTAKE_SHA, '--plan', str(PLAN), '--output', str(RUN)],
        check=True, timeout=30)
    plan_sha = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    receipt = dict(schema='julia-owned-admin-stack-capture-v1',
        started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        plan=dict(path=str(PLAN), sha256=plan_sha), settings_changed=False,
        native_timing_sample=False, errors=[])
    process = None
    try:
        with (SUPPLEMENT/'controller.stdout').open('xb') as stdout, \
                (SUPPLEMENT/'controller.stderr').open('xb') as stderr:
            process = subprocess.Popen(prefix + ['run', '--plan', str(PLAN),
                '--plan-sha256', plan_sha], stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr)
            print('Started one bounded diagnostic. Waiting for its owned debugger.', flush=True)
            deadline = time.monotonic() + 15
            server = None
            while server is None:
                assert process.poll() is None, 'Controller exited before debugger registration.'
                assert time.monotonic() < deadline, 'Debugger registration timeout.'
                journal = RUN/'owner.jsonl'
                if journal.exists():
                    # Only complete newline-terminated journal entries are consumed.
                    lines = journal.read_bytes().split(b'\n')[:-1]
                    for line in lines:
                        event = json.loads(line)
                        if event.get('kind') == 'owned-child-registered' and event.get('role') == 'debugserver':
                            server = event
                if server is None:
                    time.sleep(0.05)
            expected = server['identity']
            assert expected['ppid'] == process.pid and expected['pgid'] == expected['pid']
            receipt['target_registration'] = server
            time.sleep(1)
            receipt['target_before'] = same_birth(kernel, expected)
            command = ['/usr/bin/sudo', '-n', '/usr/sbin/spindump', str(expected['pid']),
                '1', '10', '-onlyTarget', '-timelimit', '10', '-stdout', '-noFile', '-noBinary']
            receipt['stack_command'] = command
            with (SUPPLEMENT/'debugserver-stack.txt').open('xb') as stdout, \
                    (SUPPLEMENT/'spindump.stderr').open('xb') as stderr:
                captured = subprocess.run(command, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, timeout=15)
            receipt['spindump_exit_code'] = captured.returncode
            receipt['target_after'] = same_birth(kernel, expected)
            print('Stack attempt saved. Waiting for the diagnostic to finish and clean up.', flush=True)
            receipt['controller_exit_code'] = process.wait(timeout=130)
    except BaseException as error:
        receipt['errors'].append(dict(type=type(error).__name__, message=str(error)))
    finally:
        if process is not None and process.poll() is None:
            # Signal only this directly owned controller; it reaps its own children.
            process.send_signal(signal.SIGTERM)
            try:
                receipt['controller_exit_code'] = process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                receipt['errors'].append(dict(type='CleanupTimeout',
                    message='Owned controller did not return; no unrelated process was signaled.'))
        receipt['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt['files'] = {p.name:dict(bytes=p.stat().st_size,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in SUPPLEMENT.iterdir() if p.is_file()}
        with (SUPPLEMENT/'receipt.json').open('x') as output:
            json.dump(receipt, output, indent=2)
            output.write('\n')
        print('Saved evidence to ' + str(SUPPLEMENT), flush=True)
    return 0 if not receipt['errors'] and receipt.get('spindump_exit_code') == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
