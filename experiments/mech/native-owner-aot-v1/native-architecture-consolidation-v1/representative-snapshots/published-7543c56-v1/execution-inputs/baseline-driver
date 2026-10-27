#!/usr/bin/env python3
"""Six bounded baseline gates; only `--execute` starts compilation.

The last gate temporarily adds the exact previously recorded integration test
to the isolated baseline clone. The untracked overlay is pinned, reported, and
removed after its owned stage exits. Original before receipts are read-only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/private/tmp/mech-native-base-ci-repair-next')
HEAD = 'ddf8cbc3b17a644ea6292ee3bf0c4a9c63af4514'
TARGET = Path('/private/tmp/mech-native-base-ci-repair-next-target')
OUT = Path('/private/tmp/native-baseline-ddf8-prerequisites-v1')
PLAN = Path('/private/tmp/native-baseline-ddf8-prerequisites-plan-v1.json')
PLAN_SHA256 = 'ecac9e72fb4c5eefd05905ee47cb71dcd8c6b6e077ccd8294928e4feb9dff447'
OVERLAY = ROOT / 'hosts/gpu/tests/native_architecture_equivalence.rs'
RUST_RESULTS = re.compile(r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;', re.M)
CARGO = ['cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1']


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def source_state(overlay_digest=None):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    state = {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
             'status': git('status', '--porcelain=v1', '--untracked-files=all')}
    require(state['commit'] == HEAD, f'baseline source commit drift: {state}')
    expected_status = '' if overlay_digest is None else '?? ' + str(OVERLAY.relative_to(ROOT))
    require(state['status'] == expected_status, f'unexpected source changes: {state}')
    if overlay_digest is not None:
        require(OVERLAY.is_file() and not OVERLAY.is_symlink() and sha(OVERLAY) == overlay_digest,
                'temporary snapshot integration test changed')
    return state


def specifications():
    host = 'mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host'
    host_command = CARGO + ['-p', 'mech-stdlib', '-p', 'mech-gpu', '--no-default-features', '--features', host, '--lib']
    engine_command = CARGO + ['-p', 'mech-engine', '--no-default-features', '--features', 'full_compiler,native-artifact', '--lib']
    suffix = ['--', '--test-threads=1', '--nocapture']
    return [
        ('native-unit', host_command + ['native_artifact::'] + suffix),
        ('native-facts', engine_command + ['native_artifact::'] + suffix),
        ('native-lines', engine_command + ['native_text_line'] + suffix),
        ('worker-credit', engine_command + ['workers::'] + suffix),
        ('native-catalog', host_command + ['native_plan_catalog'] + suffix),
        ('representative-objects', CARGO + ['-p', 'mech-gpu', '--no-default-features', '--features',
            'canonical-native-program', '--test', 'native_architecture_equivalence',
            'original_and_decoded_guest_code_and_descriptor_snapshots', '--', '--exact',
            '--test-threads=1', '--nocapture']),
    ]


def snapshot_pins(directory):
    paths = sorted(directory.iterdir())
    require(all(path.is_file() and not path.is_symlink() for path in paths), 'unexpected snapshot entry')
    expected = {f'{case}-{route}.{suffix}' for case in ['scalar', 'aggregate', 'owner', 'owner-words']
                for route in ['source', 'decoded'] for suffix in ['o', 'descriptor.json', 'metadata.json', 'mecb']}
    require({path.name for path in paths} == expected, 'snapshot file set must contain exactly 32 expected artifacts')
    return {path.name: sha(path) for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    require(sha(PLAN) == PLAN_SHA256, 'prepared plan/provenance changed')
    plan = json.loads(PLAN.read_text())
    require(plan['head'] == HEAD and plan['workspace'] == str(ROOT) and plan['target'] == str(TARGET),
            'plan identity mismatch')
    initial = source_state()
    require(not OVERLAY.exists(), 'snapshot test overlay already exists')
    require(TARGET.is_dir() and not TARGET.is_symlink(), 'expected idle, same-checkout target missing')
    harness_path = Path(plan['snapshot_harness'])
    harness = harness_path.read_bytes()
    harness_digest = hashlib.sha256(harness).hexdigest()
    require(harness_digest == plan['snapshot_harness_sha256'], 'preserved snapshot harness changed')
    reference = Path(plan['snapshot_reference'])
    require(snapshot_pins(reference) == plan['snapshot_reference_sha256'], 'preserved baseline snapshots changed')
    specs = specifications()
    if not args.execute:
        print(json.dumps({'status': 'prepared-not-started', 'head': HEAD, 'target': str(TARGET),
                          'evidence': str(OUT), 'stages': specs, 'snapshot_files': 32,
                          'temporary_overlay': str(OVERLAY)}, indent=2))
        return
    require(not OUT.exists(), 'refusing to overwrite earlier evidence')
    OUT.mkdir()
    owner = ROOT / 'scripts/run-native-plan-stage.py'
    owner_digest = sha(owner)
    environment = os.environ.copy()
    environment.update(CARGO_TARGET_DIR=str(TARGET), CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='1',
                       CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0', PYTHONDONTWRITEBYTECODE='1')
    write(OUT / 'context.json', {'head': HEAD, 'source': initial, 'target': str(TARGET),
          'plan_sha256': sha(PLAN), 'driver_sha256': sha(Path(__file__).resolve()),
          'stage_owner_sha256': owner_digest, 'target_provenance': plan['target_provenance'],
          'snapshot_overlay': {'path': str(OVERLAY), 'sha256': harness_digest,
              'origin': str(harness_path), 'tracked': False, 'cleanup': 'remove after owned stage terminates'},
          'reference_snapshots': {'directory': str(reference), 'sha256': plan['snapshot_reference_sha256']},
          'old_results_reused': False, 'primary_timing_samples': 0})
    (OUT / 'snapshot-harness.rs').write_bytes(harness)
    rows = []

    def run(name, command, overlay_digest=None):
        before = source_state(overlay_digest)
        require(sha(owner) == owner_digest, 'bounded stage owner changed')
        env = environment.copy()
        if overlay_digest is not None:
            env['MECH_NATIVE_ARCHITECTURE_SNAPSHOT'] = str(OUT / 'snapshots')
        wrapper = [sys.executable, str(owner), '--stage', name, '--timeout-secs', '1800',
                   '--log-dir', str(OUT), '--'] + command
        started = time.monotonic()
        with (OUT / (name + '.console.log')).open('wb') as console:
            child = subprocess.Popen(wrapper, cwd=ROOT, env=env, stdout=console, stderr=subprocess.STDOUT)
            try:
                status = child.wait()
            except BaseException:
                # Keep the test overlay fixed until this owned stage terminates.
                child.send_signal(signal.SIGINT)
                child.wait()
                raise
        log_path = OUT / (name + '.log')
        summary_path = OUT / (name + '.summary.json')
        log = log_path.read_text(errors='replace') if log_path.exists() else ''
        counts = [list(map(int, match)) for match in RUST_RESULTS.findall(log)]
        row = {'stage': name, 'head': HEAD, 'command': command, 'wrapper': wrapper, 'exit_code': status,
               'counts': counts, 'seconds': time.monotonic() - started, 'source_before': before}
        failure = None
        try:
            after = source_state(overlay_digest)
            row['source_after'] = after
            summary = json.loads(summary_path.read_text())
            require(status == 0 and summary.get('stage') == name and summary.get('reason') == 'exit'
                    and summary.get('command_exit_status') == 0 and summary.get('owned_group_cleanup') == 'complete'
                    and summary.get('timeout_seconds') == 1800, f'{name}: bounded stage did not complete successfully')
            require(before == after and sha(owner) == owner_digest, f'{name}: source or owner drift')
            require(sorted(counts) == sorted(plan['expected_tests'][name]), f'{name}: unexpected/empty test summaries {counts}')
            row.update(log_sha256=sha(log_path), summary_sha256=sha(summary_path), process_summary=summary)
        except Exception as error:
            row['verification_error'] = str(error)
            row['exit_code'] = status or 1
            failure = error
        rows.append(row)
        write(OUT / 'results.json', rows)
        print(name, row['exit_code'], counts, flush=True)
        if failure is not None:
            raise failure

    for name, command in specs[:5]:
        run(name, command)
    source_state()
    overlay_created = False
    try:
        with OVERLAY.open('xb') as stream:
            overlay_created = True
            stream.write(harness)
        run(*specs[5], overlay_digest=harness_digest)
    finally:
        if overlay_created and OVERLAY.exists():
            require(not OVERLAY.is_symlink() and sha(OVERLAY) == harness_digest,
                    'overlay changed unexpectedly; preserve it for inspection')
            OVERLAY.unlink()
        write(OUT / 'overlay-cleanup.json', {'removed': not OVERLAY.exists(), 'source': source_state()})
    actual = snapshot_pins(OUT / 'snapshots')
    require(actual == plan['snapshot_reference_sha256'], '32 baseline artifacts differ from preserved 17539 snapshots')
    require(snapshot_pins(reference) == plan['snapshot_reference_sha256'], 'read-only reference snapshots changed')
    require(source_state() == initial, 'final baseline source changed')
    write(OUT / 'snapshot-comparison.json', {'count': 32, 'all_byte_identical': True,
          'reference_source': plan['previous_baseline_source'], 'current_source': HEAD, 'sha256': actual})
    write(OUT / 'complete.json', {'head': HEAD, 'status': 'baseline-prerequisites-passed',
          'stages': len(rows), 'snapshot_files': 32, 'snapshot_overlay_removed': not OVERLAY.exists(),
          'results_sha256': sha(OUT / 'results.json'), 'primary_timing_samples': 0})


if __name__ == '__main__':
    main()
