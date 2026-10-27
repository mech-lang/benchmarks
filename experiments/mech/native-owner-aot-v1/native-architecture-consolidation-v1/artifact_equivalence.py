#!/usr/bin/env python3
"""Exact-head public and representative artifact comparison through the shared process owner."""
if not __debug__:
    raise RuntimeError('Optimized Python disables required shared-controller checks')
import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from study import HERE, ROOT, STUDY_ID, build_receipt_path, process, read, read_plan, source_state

BASELINE = CODE / 'baseline-prerequisites-ddf8-v1'
TEST = 'original_and_decoded_guest_code_and_descriptor_snapshots'
HARNESS = 'hosts/gpu/tests/native_architecture_equivalence.rs'
EXPECTED = {f'{case}-{route}.{suffix}' for case in ('aggregate', 'owner', 'owner-words', 'scalar')
            for route in ('source', 'decoded') for suffix in ('o', 'mecb', 'metadata.json', 'descriptor.json')}
AOT = ('program.o', 'program.mecb', 'native-descriptor.json', 'native-descriptor.bin', 'object-identity.bin', 'native-resources.json')
# Match the inherited build protocol of the archived ddf8/final51 drivers.
# No public-AOT or primary timing environment is imported or modified here.
BUILD_OVERRIDES = {'CARGO_INCREMENTAL': '0', 'CARGO_BUILD_JOBS': '1',
                   'CARGO_PROFILE_DEV_DEBUG': '0', 'CARGO_PROFILE_TEST_DEBUG': '0',
                   'PYTHONDONTWRITEBYTECODE': '1'}
ABSENT_BUILD_FLAGS = ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_RUSTFLAGS',
                      'RUSTDOCFLAGS', 'CARGO_ENCODED_RUSTDOCFLAGS',
                      'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER')
BUILD_ENV_KEYS = ('PATH', 'HOME', 'CARGO_HOME', 'RUSTUP_HOME', 'RUSTUP_TOOLCHAIN', 'TMPDIR',
                  'LANG', 'LC_ALL', 'TZ', 'NO_COLOR', 'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET',
                  'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'CPATH', 'LIBRARY_PATH',
                  'LIBCLANG_PATH', 'MECH_GMP_LIBRARY', 'CC', 'CXX', 'AR', 'CFLAGS',
                  'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'PKG_CONFIG', 'PKG_CONFIG_PATH',
                  'PKG_CONFIG_LIBDIR', 'PKG_CONFIG_SYSROOT_DIR', 'CARGO_TARGET_DIR',
                  'MECH_NATIVE_ARCHITECTURE_SNAPSHOT', 'M4', *BUILD_OVERRIDES)


def build_environment(target, out):
    # Both prior drivers inherited the invoking shell. Their receipts did not
    # save the full inherited environment; claim protocol alignment, not a
    # reconstructed historical environment. Reject extra profile/flag knobs
    # instead of silently changing the warmed target's compilation profile.
    env = os.environ.copy()
    require(not any(key in env for key in ABSENT_BUILD_FLAGS), 'Unexpected Rust build override')
    require(not any(key.startswith('CARGO_TARGET_') and key.endswith('_RUSTFLAGS') for key in env), 'Unexpected target Rust flags')
    require(not any(key.startswith('CARGO_PROFILE_') and key not in BUILD_OVERRIDES for key in env), 'Unexpected Cargo profile override, including strip')
    env.update(BUILD_OVERRIDES, CARGO_TARGET_DIR=str(target),
               MECH_NATIVE_ARCHITECTURE_SNAPSHOT=str(out / 'snapshots'))
    # Retain ambient TMPDIR exactly as the correctness driver does. Record only
    # compiler-relevant values; unrelated inherited credentials are not evidence.
    record = {key: env.get(key) for key in BUILD_ENV_KEYS}
    record.update({key: None for key in (*ABSENT_BUILD_FLAGS, 'CARGO_PROFILE_DEV_STRIP', 'CARGO_PROFILE_TEST_STRIP')})
    return env, record


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': process.sha(path)}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def fresh(kind, run_id):
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]+', run_id)), 'Unsafe run ID')
    directory = HERE / kind / run_id
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def checked_process(receipt, deadline):
    require(receipt.get('exit_status') == 0, 'Process failed')
    require(not receipt.get('error') and not receipt.get('observer_still_waiting'), 'Process error or unfinished observer')
    require(receipt.get('cleanup_errors') == [] and receipt.get('group_closed') is True and receipt.get('reaped') is True, 'Incomplete cleanup')
    require(receipt.get('signals') == [], 'Unexpected process signals')
    require(receipt.get('inherited_common_mutex') is True and receipt.get('quantitative_benchmark') is False, 'Invalid process scope')
    require(receipt.get('deadline_seconds') == deadline, 'Unexpected deadline')


def snapshots(path):
    require(path.is_dir(), f'Missing snapshot directory: {path}')
    require({p.name for p in path.iterdir()} == EXPECTED, 'Expected exactly the 32 named snapshot files')
    require(all((path / name).is_file() and not (path / name).is_symlink() for name in EXPECTED), 'Snapshots must be regular files')
    return {name: process.sha(path / name) for name in sorted(EXPECTED)}


def baseline():
    manifest = read(BASELINE / 'archive-manifest.json')
    require(manifest['head'] == 'ddf8cbc3b17a644ea6292ee3bf0c4a9c63af4514' and manifest['status'] == 'passed', 'Wrong archived baseline')
    relevant = {'context.json', 'snapshot-comparison.json', 'snapshot-harness.rs'} | {'snapshots/' + name for name in EXPECTED}
    rows = {row['archive_relative']: row for row in manifest['files']}
    for name in relevant:
        require(rows[name]['encoding'] == 'identity' and process.sha(BASELINE / name) == rows[name]['raw_sha256'] == rows[name]['archive_sha256'], 'Archived baseline changed: ' + name)
    hashes = snapshots(BASELINE / 'snapshots')
    require(hashes == read(BASELINE / 'snapshot-comparison.json')['sha256'], 'Baseline snapshot pins disagree')
    return read(BASELINE / 'context.json')['source'], BASELINE / 'snapshots', hashes


def run_snapshot(args):
    plan = read_plan()
    workspace, target = args.workspace.resolve(), args.target_dir.resolve()
    key = 'implementation_base' if args.subject == 'I' else 'final_compiler_source'
    require(re.fullmatch(r'[0-9a-f]{40}', args.commit) and args.commit == plan[key], 'Source has not been explicitly adopted for this subject')
    before = source_state(workspace)
    require(before['commit'] == args.commit and before['status'] == '', 'Expected clean exact source')
    provenance = read(args.target_provenance)
    require(provenance['source'] == before and provenance['target_dir'] == str(target),
            'Target provenance must identify this exact source and Cargo cache')
    require(not target.is_relative_to(workspace) and not target.is_relative_to(ROOT), 'Target must be outside both repositories')
    subprocess.run(['git', '-C', str(workspace), 'ls-files', '--error-unmatch', HARNESS], check=True, stdout=subprocess.DEVNULL)
    _, _, reference = baseline()
    require(process.sha(workspace / HARNESS) == process.sha(BASELINE / 'snapshot-harness.rs'), 'Tracked snapshot harness differs from archived authority')
    out = fresh('representative-snapshots', args.run_id)
    env, recorded_env = build_environment(target, out)
    command = ['/Users/cim310/.cargo/bin/cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1',
               '-p', 'mech-gpu', '--no-default-features', '--features', 'canonical-native-program', '--test',
               'native_architecture_equivalence', TEST, '--', '--exact', '--test-threads=1', '--nocapture', '--color', 'never']
    owner = ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py'
    supervisor = ROOT / 'tools/qualification/prolog_supervisor.py'
    pins = [pin(p) for p in (Path(__file__), CODE / 'study.py', owner, supervisor, HERE / 'plan.json',
                            BASELINE / 'executed-driver.py', args.target_provenance, workspace / HARNESS, BASELINE / 'archive-manifest.json')]
    shutil.copyfile(__file__, out / 'executed-driver.py')
    shutil.copyfile(workspace / HARNESS, out / 'snapshot-harness.rs')
    shutil.copyfile(args.target_provenance, out / 'target-provenance.json')
    report = {'schema': 'mech.representative-snapshot-run.v1', 'status': 'prepared', 'study_id': STUDY_ID,
              'source': before, 'subject': args.subject, 'workspace': str(workspace), 'command': command, 'build_environment': recorded_env,
              'environment_scope': 'Inherited shell plus the same explicit overrides as ddf8/final51; compiler-relevant values only; no reconstructed historical environment claim',
              'pins': pins, 'performance_qualified': False, 'primary_timing_samples': 0}
    save(out / 'result.json', report)
    try:
        mutex = Path(plan['common_mutex'])
        require(mutex.is_file() and mutex.stat().st_ino == 83858837, 'Shared mutex inode changed')
        wrapper = 'import os,sys;os.chdir(sys.argv[1]);os.execve(sys.argv[2],sys.argv[2:],os.environ)'
        with mutex.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            report['mutex'] = {'path': str(mutex), 'inode': mutex.stat().st_ino}
            checked_process(process.execute([sys.executable, '-c', wrapper, str(workspace), *command],
                                             out / 'representative-objects', env, lock, deadline=1800, quantitative=False), 1800)
        text = (out / 'representative-objects/stdout.bin').read_text()
        passed = [line for line in text.splitlines() if line.startswith('test ') and line.endswith(' ... ok')]
        require(passed == [f'test {TEST} ... ok'], 'Exactly the named test must pass once')
        summaries = re.findall(r'^test result: .*$', text, re.M)
        require(len(summaries) == 1 and summaries[0].startswith('test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'), 'Invalid exact-one test summary')
        report['snapshots'] = snapshots(out / 'snapshots')
        require(report['snapshots'] == reference, 'Representative snapshots differ from ddf8 baseline')
        report['status'] = 'passed'
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        try:
            report['source_after'] = source_state(workspace)
            require(report['source_after'] == before, 'Source changed during snapshot stage')
            for item in pins:
                require(process.sha(Path(item['path'])) == item['sha256'], 'Pinned execution input changed')
        except BaseException as error:
            report.update(status='failed', integrity_error=repr(error))
            raise
        finally:
            report['process_evidence'] = {name: pin(out / 'representative-objects' / name) for name in ('process.json', 'stdout.bin', 'stderr.bin') if (out / 'representative-objects' / name).is_file()}
            save(out / 'result.json', report)
    print(json.dumps({'result': pin(out / 'result.json'), 'status': report['status'], 'snapshot_count': 32}))


def snapshot_receipt(reference):
    path = build_receipt_path(reference, shared=True)
    report = read(path)
    require(report['schema'] == 'mech.representative-snapshot-run.v1' and report['status'] == 'passed', 'Snapshot attempt did not pass')
    require(report['source'] == report['source_after'] and not report['source']['status'], 'Invalid snapshot source')
    require(report['primary_timing_samples'] == 0 and report['performance_qualified'] is False, 'Invalid snapshot scope')
    hashes = snapshots(path.parent / 'snapshots')
    require(hashes == report['snapshots'], 'Snapshot files changed')
    for name in ('process.json', 'stdout.bin', 'stderr.bin'):
        require(process.sha(path.parent / 'representative-objects' / name) == report['process_evidence'][name]['sha256'], 'Snapshot process evidence changed')
    checked_process(read(path.parent / 'representative-objects/process.json'), 1800)
    return report['source'], path.parent / 'snapshots', hashes


def compare(args):
    plan = read_plan()
    paths = {'I': build_receipt_path(plan.get('baseline_receipt'), shared=True), 'F': build_receipt_path(plan.get('candidate_receipt'))}
    receipts = {s: read(path) for s, path in paths.items()}
    for s, key in (('I', 'implementation_base'), ('F', 'final_compiler_source')):
        r = receipts[s]
        require(r['status'] == 'public-subject-built' and r['benchmark_samples'] == 0, 'Wrong public build receipt')
        require(r['source']['commit'] == plan[key] and not r['source']['status'], 'Public build source not adopted')
        require(source_state(Path(r['workspace'])) == r['source'], 'Public build workspace no longer matches')
        require(process.sha(Path(r['executable'])) == r['executable_sha256'], 'Public binary changed')
    candidate = json.loads(args.candidate_snapshots)
    require(candidate['study_id'] == STUDY_ID, 'Candidate snapshots must belong to this study')
    f_snapshot = snapshot_receipt(candidate)
    initial = json.loads(args.baseline_snapshots)
    require(initial['study_id'] == 'native-architecture-consolidation-v1',
            'Baseline snapshots must come from the architecture study')
    i_snapshot = snapshot_receipt(initial)
    snapshot_data = {'F': f_snapshot, 'I': i_snapshot}
    for s, (source, _, _) in snapshot_data.items():
        require(source == receipts[s]['source'], 'Snapshots and public build sources differ')
    controls = read(HERE / 'retained-controls.json')
    require(process.sha(Path(controls['W']['object_path'])) == controls['W']['object_sha256'], 'Retained W guest Object changed')
    require(receipts['F']['object_sha256'] == receipts['I']['object_sha256'] == controls['W']['object_sha256'], 'Public guest Objects differ from W')
    out = fresh('exact-head-equivalence', args.run_id)
    execution_pins = {name: pin(path) for name, path in {
        'driver': Path(__file__), 'study': CODE / 'study.py', 'campaign': CODE / 'campaign.py',
        'process': ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py',
        'supervisor': ROOT / 'tools/qualification/prolog_supervisor.py',
    }.items()}
    shutil.copyfile(__file__, out / 'executed-driver.py')
    require(process.sha(out / 'executed-driver.py') == execution_pins['driver']['sha256'], 'Executed driver copy differs')
    context = {'schema': 'mech.native-equivalence-inputs.v1', 'study_id': STUDY_ID, 'performance_qualified': False, 'primary_timing_samples': 0,
               'execution_pins': execution_pins,
               'plan': pin(HERE / 'plan.json'), 'receipts': {s: pin(p) for s, p in paths.items()},
               'candidate_snapshots': candidate, 'baseline_snapshots': initial,
               'retained_controls': pin(HERE / 'retained-controls.json'), 'W_object': pin(Path(controls['W']['object_path']))}
    save(out / 'context.json', context)
    for kind, names, key in [('public-aot', AOT, 'file'), ('representatives', sorted(EXPECTED), 'path')]:
        rows = []
        for name in names:
            row = {key: name}
            for s in ('F', 'I'):
                source = Path(receipts[s]['executable'] + '.project') / name if kind == 'public-aot' else snapshot_data[s][1] / name
                target = out / kind / s / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                row[s], row[s + '_file'] = process.sha(source), str(target.relative_to(HERE))
                require(process.sha(target) == row[s], 'Archive copy differs')
            row['equal'] = row['F'] == row['I']
            rows.append(row)
        report = {'F_source': receipts['F']['source'], 'I_source': receipts['I']['source'], 'files': rows}
        save(out / ('guest-code.json' if kind == 'public-aot' else 'representative-objects.json'), report)
        require(all(row['equal'] for row in rows), 'Equivalence failed: ' + kind)
        if kind == 'public-aot':
            pins = {row['file']: row['F'] for row in rows}
            require(pins['program.o'] == controls['W']['object_sha256'], 'Archived public guest Object differs from W')
            require(pins['program.mecb'] == plan['bytecode_sha256'], 'Public bytecode differs from the adopted plan')
    for item in [*execution_pins.values(), context['plan'], context['retained_controls'], *context['receipts'].values()]:
        require(process.sha(Path(item['path'])) == item['sha256'], 'Pinned comparison code or protocol input changed')
    print(json.dumps({'archive': str(out), 'guest_files': 6, 'representative_files': 32, 'primary_timing_samples': 0}))


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    sub = parser.add_subparsers(dest='mode', required=True)
    run = sub.add_parser('snapshots', allow_abbrev=False)
    run.add_argument('--subject', choices=('I', 'F'), required=True)
    run.add_argument('--workspace', type=Path, required=True)
    run.add_argument('--commit', required=True)
    run.add_argument('--target-dir', type=Path, required=True)
    run.add_argument('--target-provenance', type=Path, required=True)
    run.add_argument('--run-id', required=True)
    comparison = sub.add_parser('compare', allow_abbrev=False)
    comparison.add_argument('--run-id', required=True)
    comparison.add_argument('--candidate-snapshots', required=True, help='Pinned shared-receipt JSON: study_id, path, sha256')
    comparison.add_argument('--baseline-snapshots', required=True, help='Pinned exact-before snapshot receipt JSON; cleanup reuses architecture F')
    args = parser.parse_args()
    (run_snapshot if args.mode == 'snapshots' else compare)(args)


if __name__ == '__main__':
    main()
