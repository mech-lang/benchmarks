#!/usr/bin/env python3
"""Attribute an existing snapshot failure using controlled historical hunks."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

W = Path('/private/tmp/mech-native-semantic-fingerprint-attribution-v1')
E = Path('/private/tmp/native-semantic-fingerprint-attribution-v1')
HEAD = 'ddf8cbc3b17a644ea6292ee3bf0c4a9c63af4514'
FILES = ['src/engine/src/source_semantics/frontend.rs',
         'src/engine/src/source_semantics/application.rs']
assert not E.exists()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=W, text=True).strip() == HEAD
assert not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=W, text=True)
E.mkdir()
original = {name: (W / name).read_bytes() for name in FILES}
def sha(data):
    return hashlib.sha256(data).hexdigest()

# The entire predicate-type insertion from 6e53189b7 is the first experiment.
predicate_patch = subprocess.check_output(
    ['git', 'diff', '6e53189b7^', '6e53189b7', '--', FILES[0]], cwd=W)
(E / 'predicate-type-original.patch').write_bytes(predicate_patch)
subprocess.run(['git', 'apply', '--reverse', '-'], input=predicate_patch, cwd=W, check=True)

environment = os.environ.copy()
environment.update(CARGO_TARGET_DIR='/private/tmp/mech-native-base-ci-repair-next-target',
                   CARGO_INCREMENTAL='0', CARGO_PROFILE_DEV_DEBUG='0',
                   CARGO_PROFILE_TEST_DEBUG='0', CARGO_BUILD_JOBS='1')
command = ['cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1',
           '-p', 'mech-engine', '--no-default-features', '--features',
           'full_source,resident-artifact', '--test', 'canonical_executable_semantics',
           'every_semantic_rule_meets_its_required_witness_outcome', '--', '--exact',
           '--test-threads=1', '--nocapture']
rows = []

def run(stage, expected_exit, expected_changed):
    patch = subprocess.check_output(['git', 'diff', '--', *FILES], cwd=W)
    (E / (stage + '.patch')).write_bytes(patch)
    before = {name: sha((W / name).read_bytes()) for name in FILES}
    wrapper = [sys.executable, str(W / 'scripts/run-native-plan-stage.py'),
               '--stage', stage, '--timeout-secs', '1800', '--log-dir', str(E), '--', *command]
    result = subprocess.run(wrapper, cwd=W, env=environment)
    log = (E / (stage + '.log')).read_text()
    summary = json.loads((E / (stage + '.summary.json')).read_text())
    changed = re.findall(r'^([a-z-]+)\t(\d+)\t(\d+)$', log, re.M)
    row = dict(stage=stage, source_head=HEAD, source_before=before,
               source_after={name: sha((W / name).read_bytes()) for name in FILES},
               command=command, wrapper=wrapper, exit_code=result.returncode,
               summary=summary, changed_fingerprints=changed,
               log_sha256=sha((E / (stage + '.log')).read_bytes()),
               experimental_patch_sha256=sha(patch))
    rows.append(row)
    (E / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
    assert row['source_before'] == row['source_after']
    assert result.returncode == expected_exit, row
    assert [r[0] for r in changed] == expected_changed, changed
    assert summary['owned_group_cleanup'] == 'complete', summary
    if not expected_exit:
        assert 'test result: ok. 1 passed; 0 failed; 0 ignored;' in log

try:
    run('without-predicate-type-insertion', 101, ['application-expression'])
    # Preserve all other compiler edits and restore only the historical detail.
    path = W / FILES[1]
    text = path.read_text()
    current = '''detail: Some(match count {
                    crate::IterationCount::Literal(count) => count.to_string(),
                    crate::IterationCount::Elements { input } => {
                        format!("element counts input {input}")
                    }
                }),'''
    assert text.count(current) == 1
    path.write_text(text.replace(current, 'detail: Some(format!("{count:?}")),', 1))
    run('without-predicate-type-and-old-iteration-detail', 0, [])
finally:
    for name, contents in original.items():
        (W / name).write_bytes(contents)
    assert not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=W, text=True)

(E / 'complete.json').write_text(json.dumps(dict(
    status='attributed-to-two-intended-historical-changes', source_head=HEAD,
    predicate_type_commit='6e53189b7d2132752224fe385ac5aca657df2b65',
    iteration_detail_commit='d7fc265be',
    initial_file_sha256={name: sha(data) for name, data in original.items()},
    results_sha256=sha((E / 'results.json').read_bytes()),
    source_restored_clean=True, primary_timing_samples=0), indent=2) + '\n')
