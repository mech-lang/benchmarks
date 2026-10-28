#!/usr/bin/env python3
"""Compare the current green base and architecture, without collecting timings."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

OUT = Path(__file__).resolve().parent
TARGET = Path('/private/tmp/native-935-current-head-target-v1')
HARNESS = 'hosts/gpu/tests/native_architecture_equivalence.rs'
TEST = 'original_and_decoded_guest_code_and_descriptor_snapshots'
SUBJECTS = [
    ('934', Path('/private/tmp/mech-native-base-ci-green-v4'), 'b4e7b15168c9caced1dc10f5a487bd151a2ba976'),
    ('935', Path('/private/tmp/mech-native-consolidation-semantics-v1'), '36bcb9292ed40676a4547c91588c96735785b139'),
]
EXPECTED = {f'{case}-{route}.{suffix}' for case in ('scalar', 'aggregate', 'owner', 'owner-words')
            for route in ('source', 'decoded') for suffix in ('o', 'mecb', 'metadata.json', 'descriptor.json')}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def state(workspace):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=workspace, text=True).strip()
    return {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
            'status': git('status', '--porcelain=v1', '--untracked-files=all')}


def stage(workspace, evidence, name, command, env, timeout=1800, record=False):
    owner = workspace / 'scripts/run-native-plan-stage.py'
    cmd = [sys.executable, str(owner), '--stage', name, '--timeout-secs', str(timeout), '--log-dir', str(evidence)]
    if record:
        cmd += ['--record-test-executable', 'native_architecture_equivalence',
                '--test-executable-file', str(evidence / 'test-executable')]
    cmd += ['--', *command]
    save(evidence / (name + '.command.json'), {'command': command, 'wrapper': cmd, 'owner_sha256': sha(owner)})
    with (evidence / (name + '.driver.log')).open('wb') as log:
        p = subprocess.run(cmd, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT)
    summary = json.loads((evidence / (name + '.summary.json')).read_text())
    if p.returncode or summary['reason'] != 'exit' or summary['command_exit_status'] != 0 or summary['owned_group_cleanup'] != 'complete':
        raise RuntimeError(f'{name} failed: {summary}')
    return summary


def main():
    assert not TARGET.exists(), 'Require a new empty Cargo target; never reuse another source accidentally'
    assert shutil.disk_usage(OUT).free >= 50_000_000_000
    TARGET.mkdir()
    harness = OUT / 'snapshot-harness.rs'
    rows = []
    env = os.environ.copy()
    env.update(CARGO_TARGET_DIR=str(TARGET), CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='1',
               CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
               PYTHONDONTWRITEBYTECODE='1', M4='/opt/homebrew/Cellar/m4/1.4.21/bin/m4')
    for label, workspace, head in SUBJECTS:
        assert shutil.disk_usage(OUT).free >= 50_000_000_000
        before = state(workspace)
        assert before['commit'] == head and before['status'] == '', before
        evidence = OUT / ('snapshots-' + label)
        evidence.mkdir(exist_ok=False)
        path = workspace / HARNESS
        installed = not path.exists()
        if installed:
            with path.open('xb') as destination:
                destination.write(harness.read_bytes())
        assert sha(path) == sha(harness)
        during = state(workspace)
        assert during == dict(before, status='?? ' + HARNESS if installed else '')
        subject_env = dict(env, MECH_NATIVE_ARCHITECTURE_SNAPSHOT=str(evidence / 'snapshots'))
        save(evidence / 'context.json', {'source': before, 'source_during': during, 'harness_overlay': installed,
             'harness_sha256': sha(path), 'driver_sha256': sha(__file__), 'target_dir': str(TARGET),
             'cache_policy': 'Fresh target for 934; all workspace package artifacts removed before switching to 935',
             'environment_overrides': {key: subject_env[key] for key in ['CARGO_TARGET_DIR', 'CARGO_INCREMENTAL',
             'CARGO_BUILD_JOBS', 'CARGO_PROFILE_DEV_DEBUG', 'CARGO_PROFILE_TEST_DEBUG', 'M4', 'MECH_NATIVE_ARCHITECTURE_SNAPSHOT']},
             'primary_timing_samples': 0})
        try:
            command = ['cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1', '-p', 'mech-gpu',
                       '--no-default-features', '--features', 'canonical-native-program', '--test',
                       'native_architecture_equivalence', '--no-run', '--message-format=json-render-diagnostics']
            stage(workspace, evidence, 'compile', command, subject_env, record=True)
            executable = Path((evidence / 'test-executable').read_text().strip())
            save(evidence / 'executable.json', {'path': str(executable), 'sha256': sha(executable), 'source': before})
            with executable.open('rb') as source, gzip.open(evidence / 'test-executable.gz', 'wb') as destination:
                shutil.copyfileobj(source, destination)
            stage(workspace, evidence, 'execute', [str(executable), TEST, '--exact', '--test-threads=1', '--nocapture', '--color', 'never'], subject_env, timeout=300)
            log = (evidence / 'execute.log').read_text()
            summaries = re.findall(r'^test result:.*$', log, re.M)
            assert len(summaries) == 1 and re.fullmatch(r'test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in [0-9.]+s', summaries[0]), summaries
            assert log.count(f'test {TEST} ... ok') == 1
            directory = evidence / 'snapshots'
            assert {p.name for p in directory.iterdir()} == EXPECTED
            snapshots = {name: sha(directory / name) for name in sorted(EXPECTED)}
            if installed:
                assert sha(path) == sha(harness)
                path.unlink()
            assert state(workspace) == before
            row = {'subject': label, 'source': before, 'snapshots': snapshots, 'tests_passed': 1, 'primary_timing_samples': 0}
            rows.append(row)
            save(evidence / 'result.json', row)
            print(label, 'passed exact original/decoded snapshot test; retained all32 files', flush=True)
        except BaseException:
            # Keep any overlay and unfinished evidence if process closure has not
            # been proven, so interruption cannot erase the source witness.
            raise
        if label == '934':
            metadata = json.loads(subprocess.check_output(['cargo', '+nightly-2026-03-03', 'metadata', '--locked', '--offline', '--no-deps', '--format-version=1'], cwd=workspace, env=env, text=True))
            ids = set(metadata['workspace_members'])
            names = sorted(p['name'] for p in metadata['packages'] if p['id'] in ids)
            command = ['cargo', '+nightly-2026-03-03', 'clean']
            for name in names:
                command += ['-p', name]
            stage(workspace, evidence, 'remove-all-workspace-artifacts', command, env, timeout=300)
            save(OUT / 'source-switch.json', {'from': before, 'target_dir': str(TARGET), 'removed_workspace_packages': names,
                                           'preserved_baseline_harness': str(evidence / 'test-executable.gz')})
    assert rows[0]['snapshots'] == rows[1]['snapshots'], 'Current-head generated code or descriptors differ'
    save(OUT / 'current-head-snapshot-comparison.json', {'status': 'passed', 'subjects': rows,
         'exactly_identical_files': 32, 'driver_sha256': sha(__file__), 'primary_timing_samples': 0,
         'performance_qualified': False})
    print('PASS: all32 current 934/935 files are byte-identical; no timing claim', flush=True)


if __name__ == '__main__':
    main()
