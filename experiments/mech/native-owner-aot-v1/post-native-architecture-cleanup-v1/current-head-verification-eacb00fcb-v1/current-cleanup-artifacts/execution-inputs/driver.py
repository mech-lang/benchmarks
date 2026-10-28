#!/usr/bin/env python3
"""Compare current cleanup artifacts to the exact green architecture baseline."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
WORKSPACE = Path('/private/tmp/mech-post-native-semantics-v1')
HEAD = 'eacb00fcb3352fbbf3d4dddb7b983f4c130f4a7b'
TARGET = Path('/private/tmp/native-939-artifact-target-eacb00fcb-v1')
OUT = ROOT / 'current-cleanup-artifacts'
PRIOR = Path('/private/tmp/native-935-green-v1')
HELPER = PRIOR / 'compare-current-heads.py'
REFERENCE = PRIOR / 'current-head-snapshot-comparison.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    assert not TARGET.exists() and not OUT.exists(), 'Require fresh evidence and source-specific cache'
    assert shutil.disk_usage(ROOT).free >= 50_000_000_000
    spec = importlib.util.spec_from_file_location('executed_snapshot_owner', HELPER)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    before = owner.state(WORKSPACE)
    assert before['commit'] == HEAD and before['status'] == '', before
    reference = json.loads(REFERENCE.read_text())
    assert reference['status'] == 'passed'
    baseline = reference['subjects'][1]
    assert baseline['source']['commit'] == '36bcb9292ed40676a4547c91588c96735785b139'
    assert baseline['source']['status'] == '' and set(baseline['snapshots']) == owner.EXPECTED
    for name, digest in baseline['snapshots'].items():
        assert sha(PRIOR / 'snapshots-935/snapshots' / name) == digest
    harness = WORKSPACE / owner.HARNESS
    assert sha(harness) == sha(PRIOR / 'snapshot-harness.rs')
    OUT.mkdir()
    TARGET.mkdir()
    inputs = OUT / 'execution-inputs'
    inputs.mkdir()
    pins = {}
    for name, path in [('helper.py', HELPER), ('reference.json', REFERENCE),
                       ('harness.rs', harness), ('driver.py', Path(__file__).resolve()),
                       ('stage-owner.py', WORKSPACE / 'scripts/run-native-plan-stage.py')]:
        shutil.copyfile(path, inputs / name)
        pins[name] = {'path': str(path), 'sha256': sha(path)}
    env = os.environ.copy()
    assert not any(env.get(key) for key in ['RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_RUSTFLAGS'])
    overrides = {'CARGO_TARGET_DIR': str(TARGET), 'CARGO_INCREMENTAL': '0', 'CARGO_BUILD_JOBS': '1',
                 'CARGO_PROFILE_DEV_DEBUG': '0', 'CARGO_PROFILE_TEST_DEBUG': '0',
                 'PYTHONDONTWRITEBYTECODE': '1', 'M4': '/opt/homebrew/Cellar/m4/1.4.21/bin/m4',
                 'MECH_NATIVE_ARCHITECTURE_SNAPSHOT': str(OUT / 'snapshots')}
    env.update(overrides)
    save(OUT / 'context.json', {'source': before, 'baseline_source': baseline['source'],
         'source_workspace': str(WORKSPACE), 'target_dir': str(TARGET), 'environment_overrides': overrides,
         'inputs': pins, 'fresh_target': True, 'primary_timing_samples': 0})
    command = ['cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1', '-p', 'mech-gpu',
               '--no-default-features', '--features', 'canonical-native-program', '--test',
               'native_architecture_equivalence', '--no-run', '--message-format=json-render-diagnostics']
    owner.stage(WORKSPACE, OUT, 'compile', command, env, record=True)
    executable = Path((OUT / 'test-executable').read_text().strip())
    save(OUT / 'executable.json', {'source': before, 'path': str(executable), 'sha256': sha(executable)})
    with executable.open('rb') as source, gzip.open(OUT / 'test-executable.gz', 'wb', compresslevel=1) as destination:
        shutil.copyfileobj(source, destination)
    owner.stage(WORKSPACE, OUT, 'execute', [str(executable), owner.TEST, '--exact', '--test-threads=1', '--nocapture', '--color', 'never'], env, timeout=300)
    log = (OUT / 'execute.log').read_text()
    summaries = re.findall(r'^test result:.*$', log, re.M)
    assert len(summaries) == 1 and re.fullmatch(r'test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in [0-9.]+s', summaries[0]), summaries
    assert log.count(f'test {owner.TEST} ... ok') == 1
    directory = OUT / 'snapshots'
    assert {p.name for p in directory.iterdir()} == owner.EXPECTED
    actual = {name: sha(directory / name) for name in sorted(owner.EXPECTED)}
    assert actual == baseline['snapshots'], 'Cleanup changes a current-head object, descriptor, metadata or bytecode snapshot'
    assert owner.state(WORKSPACE) == before
    for item in pins.values():
        assert sha(Path(item['path'])) == item['sha256']
    save(OUT / 'result.json', {'status': 'passed', 'source': before, 'baseline_source': baseline['source'],
         'identical_files': 32, 'snapshots': actual, 'performance_qualified': False, 'primary_timing_samples': 0})
    print('PASS: all32 current935/939 artifact files are byte-identical; no timing claim', flush=True)


if __name__ == '__main__':
    main()
