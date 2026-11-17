#!/usr/bin/env python3
"""Build a revision-specific worker in a separate directory; never use an installed Mech."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(args):
    mech = args.mech.resolve()
    revision = command('git', 'rev-parse', 'HEAD', cwd=mech)
    expected = command('git', 'rev-parse', args.revision + '^{commit}', cwd=mech)
    if revision != expected:
        raise ValueError(f'checkout is {revision}; expected {expected}')
    status = command('git', 'status', '--porcelain', '--untracked-files=no', cwd=mech)
    if status and not args.allow_dirty:
        raise ValueError('compiler has tracked edits; select a clean checkout or use --allow-dirty')
    if not (mech / 'src/runtime/src/runtime/program/compiler.rs').is_file():
        raise ValueError('this adapter requires the canonical ProgramCompiler architecture; supply an older-revision adapter separately')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    adapter = args.adapter.resolve()
    (output / 'src').mkdir(exist_ok=True)
    shutil.copyfile(adapter, output / 'src/main.rs')
    # JSON string escaping is also valid for these TOML basic strings.
    escaped = json.dumps(str(mech))[1:-1]
    manifest = (ROOT / 'suite/workers/Cargo.toml.in').read_text().replace('@MECH@', escaped)
    (output / 'Cargo.toml').write_text(manifest)
    if not (output / 'Cargo.lock').exists() and (mech / 'Cargo.lock').exists():
        shutil.copyfile(mech / 'Cargo.lock', output / 'Cargo.lock')
    environment = dict(os.environ, RUSTC_BOOTSTRAP='1', CARGO_TARGET_DIR=str(output / 'target'))
    build_command = ['cargo', 'build', '--release', '--manifest-path', str(output / 'Cargo.toml')]
    if not args.online:
        build_command.append('--offline')
    if args.native:
        build_command.extend(['--features', 'native'])
    subprocess.run(build_command, env=environment, check=True)
    binary = output / 'target/release/mech-benchmark-worker'
    provenance = {
        'protocol': 1, 'revision': revision, 'source_checkout': str(mech),
        'dirty': bool(status), 'tracked_diff_sha256': hashlib.sha256(subprocess.check_output(
            ['git', 'diff', 'HEAD', '--binary'], cwd=mech)).hexdigest(),
        'binary': str(binary), 'binary_sha256': sha(binary),
        'adapter_sha256': sha(adapter), 'manifest_sha256': sha(output / 'Cargo.toml'),
        'lock_sha256': sha(output / 'Cargo.lock'),
        'rustc': command('rustc', '-Vv'), 'cargo': command('cargo', '-V'),
        'build_command': build_command, 'feature_profile': 'full_compiler + resident-artifact',
        'native_generation': args.native,
        'build_environment': {key: environment[key] for key in
            ('RUSTC_BOOTSTRAP', 'CARGO_TARGET_DIR', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS') if key in environment},
    }
    (output / 'worker.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'Worker ready: {output / "worker.json"}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mech', required=True, type=Path)
    parser.add_argument('--revision', required=True, help='exact intended revision, checked against HEAD')
    parser.add_argument('--output', required=True, type=Path, help='separate directory for this revision')
    parser.add_argument('--adapter', type=Path, default=ROOT / 'suite/workers/main.rs')
    parser.add_argument('--allow-dirty', action='store_true')
    parser.add_argument('--online', action='store_true', help='allow Cargo dependency downloads')
    parser.add_argument('--native', action='store_true', help='include the canonical native object/application generator')
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
