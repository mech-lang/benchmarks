#!/usr/bin/env python3
"""Qualify the current downstream stack with fresh bounded receipts."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

WORKSPACE = Path('/private/tmp/mech-native-stack-repair')
HEAD = '8fdc971f46776cfbf50128aeb68c192d2f086c7c'
TARGET = Path('/private/tmp/mech-native-stack-target')
OUT = Path('/private/tmp/native-adopted-stack-qualification-v1')
BASE_DRIVER = Path('/private/tmp/native-final-correctness-driver-v1.py')
spec = importlib.util.spec_from_file_location('correctness', BASE_DRIVER)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def main():
    initial = checks.source_state(WORKSPACE, HEAD)
    stages = [row for row in checks.stage_specs(OUT) if row['stage'] in {
        'none-check', 'scalar-runtime-check', 'program-runtime-check',
        'host-runtime-check', 'scalar-compiler-check', 'program-compiler-check',
        'program-integration', 'format', 'unsafe', 'runtime-factory-safety',
        'build-analysis-layout', 'warning-policy', 'module-layout', 'planning-quarantine',
    }]
    for name, feature in [('scalar-status', 'canonical-native'),
                          ('program-status', 'canonical-native-program')]:
        stages.append(dict(stage=name, tests=True, expected_harnesses=1,
            timeout_seconds=1800, command=checks.CARGO + ['-p', 'mech-gpu',
            '--no-default-features', '--features', feature, '--lib', '--',
            'narrow_scalar_tests', 'lexical_integrity_status_tests',
            '--test-threads=1', '--nocapture']))
    for name in ['live_control', 'deflate_primitives']:
        stages.append(dict(stage=name, tests=True, expected_harnesses=1,
            timeout_seconds=1800, command=checks.CARGO + ['-p', 'mech-runtime',
            '--no-default-features', '--features', 'full_source,resident-routing-source',
            '--test', 'source_acceptance', name, '--', '--test-threads=1', '--nocapture']))
    assert len(stages) == len({r['stage'] for r in stages}) == 18
    OUT.mkdir(exist_ok=False)
    env = os.environ.copy()
    env.update(CARGO_TARGET_DIR=str(TARGET), CARGO_INCREMENTAL='0',
               CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
               CARGO_BUILD_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
    owner = WORKSPACE / 'scripts/run-native-plan-stage.py'
    pins = {str(path): checks.sha(path) for path in [Path(__file__), BASE_DRIVER, owner]}
    checks.write(OUT / 'context.json', dict(source=initial, stages=stages,
        drivers=pins, environment={key:env[key] for key in [
        'CARGO_TARGET_DIR','CARGO_INCREMENTAL','CARGO_PROFILE_DEV_DEBUG',
        'CARGO_PROFILE_TEST_DEBUG','CARGO_BUILD_JOBS']}, reused_results=False,
        primary_samples=0))
    rows = []
    for stage in stages:
        name = stage['stage']
        assert checks.source_state(WORKSPACE, HEAD) == initial
        assert all(checks.sha(Path(path)) == digest for path,digest in pins.items())
        wrapper = [sys.executable, str(owner), '--stage', name, '--timeout-secs',
                   str(stage['timeout_seconds']), '--log-dir', str(OUT), '--'] + stage['command']
        start = time.monotonic()
        with (OUT / (name + '.console.log')).open('wb') as console:
            result = subprocess.run(wrapper, cwd=WORKSPACE, env=env,
                                    stdout=console, stderr=subprocess.STDOUT)
        log_path = OUT / (name + '.log')
        log = log_path.read_text(errors='replace')
        row = dict(stage=name, head=HEAD, command=stage['command'], wrapper=wrapper,
            exit_code=result.returncode, seconds=time.monotonic()-start,
            counts=[tuple(map(int,c)) for c in checks.RUST_RESULTS.findall(log)])
        error = None
        try:
            after = checks.source_state(WORKSPACE, HEAD)
            summary_path = OUT / (name + '.summary.json')
            checks.validate_stage(stage, log, json.loads(summary_path.read_text()),
                                  result.returncode, initial, after)
            row.update(source_before=initial, source_after=after,
                       log_sha256=checks.sha(log_path), summary_sha256=checks.sha(summary_path))
        except Exception as failure:
            error = failure
            row.update(exit_code=result.returncode or 1, verification_error=str(failure))
        rows.append(row)
        checks.write(OUT / 'results.json', rows)
        print(name, row['exit_code'], row['counts'], flush=True)
        if error is not None:
            raise error
    checks.write(OUT / 'complete.json', dict(source=initial, status='passed',
        stages=len(rows), results_sha256=checks.sha(OUT / 'results.json'), primary_samples=0))


if __name__ == '__main__':
    main()
