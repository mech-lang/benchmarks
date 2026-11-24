"""Build a compiler from a Mech checkout and reproduce exact native artifacts."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent

def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build_compiler(mech, output, target):
    driver = output / 'compiler-driver'
    driver.mkdir()
    original = (HERE / 'compiler-driver/Cargo.toml.in').read_text()
    pieces = re.split(r'(?m)^(\[.*\])\n', original)
    manifest = pieces[0]
    for header, body in zip(pieces[1::2], pieces[2::2]):
        if header in ('[[bin]]', '[[test]]'):
            if 'name = "compile_profile"' not in body:
                continue
            body = re.sub(r'(?m)^path = .*$', 'path = "compile_profile.rs"', body)
        body = re.sub(r'path = "\.\./\.\./\.\./([^"]+)"',
                      lambda m: 'path = ' + json.dumps(str(mech / m[1])), body)
        manifest += header + '\n' + body
    (driver / 'Cargo.toml').write_text(manifest)
    source = (HERE / 'compiler-driver/compile_profile.rs.in').read_text()
    source = re.sub(r'#\[path = "\.\./\.\./\.\./([^"]+)"\]',
                    lambda m: '#[path = ' + json.dumps(str(mech / m[1])) + ']', source)
    (driver / 'compile_profile.rs').write_text(source)
    shutil.copyfile(HERE / 'compiler-driver/Cargo.lock', driver / 'Cargo.lock')
    command = ['cargo', '+nightly-2026-03-03', 'build', '--locked', '--release',
               '--config', 'profile.release.package.libmimalloc-sys.opt-level=1',
               '--manifest-path', str(driver / 'Cargo.toml'), '--target-dir', str(target),
               '--bin', 'compile_profile']
    profile = {'CARGO_BUILD_JOBS': '1', 'CARGO_PROFILE_RELEASE_OPT_LEVEL': '3',
               'CARGO_PROFILE_RELEASE_DEBUG': 'false', 'CARGO_PROFILE_RELEASE_LTO': 'false',
               'CARGO_PROFILE_RELEASE_CODEGEN_UNITS': '16', 'CARGO_INCREMENTAL': '0'}
    start = time.monotonic()
    with (output / 'compiler-build.log').open('w') as log:
        subprocess.run(command, cwd=mech, env=clean_environment() | profile,
                       stdout=log, stderr=log, check=True)
    compiler = output / 'compile_profile'
    shutil.copy2(target / 'release/compile_profile', compiler)
    record = {'command': command, 'environment': profile,
              'seconds': time.monotonic() - start, 'compiler_sha256': digest(compiler),
              'scope': 'Compiler construction only; excluded from codec build timings.'}
    (output / 'compiler-build.json').write_text(json.dumps(record, indent=2) + '\n')
    return compiler


def clean_environment():
    return {k: v for k, v in os.environ.items() if not k.startswith('MECH_')}


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument('--mech-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path)
    parser.add_argument('--compiler', type=Path, help='Use an already built compiler.')
    parser.add_argument('--role', action='append', help='Default: control and fp2.')
    parser.add_argument('--checked', action='store_true')
    args = parser.parse_args()
    mech = args.mech_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True)
    recipes = json.loads((HERE / 'recipes.json').read_text())
    source = mech / recipes['codec_source']
    assert digest(source) == recipes['codec_source_sha256']
    for name, pin in recipes['compiler_templates'].items():
        path = HERE / 'compiler-driver' / (name if name == 'Cargo.lock' else name + '.in')
        assert digest(path) == pin['sha256']
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=mech, text=True).strip()
    compiler = args.compiler.resolve() if args.compiler else build_compiler(
        mech, output, args.target_dir.resolve() if args.target_dir else output / 'target')
    records = []
    for role in args.role or ['control', 'fp2']:
        recipe = recipes['roles'][role]
        flags = recipe['flags'].copy()
        for key in ('MECH_COMPACT_PHASE_BLOCK_LAYOUT', 'MECH_COMPACT_PHASE_REGISTER_WEIGHTS'):
            if key not in flags:
                continue
            entries = []
            for entry in flags[key].split(';'):
                if not entry:
                    continue
                symbol, relative = entry.split('@', 1)
                path = HERE / relative
                assert digest(path) == path.stem
                entries.append(symbol + '@' + str(path))
            flags[key] = ';'.join(entries)
        if args.checked:
            flags['MECH_COMPACT_PAIR_REGISTER_SPILLS'] = 'checked'
        folder = output / role
        folder.mkdir()
        command = [str(compiler), str(source), str(folder / 'frontend'), 'compact']
        with (folder / 'compile.log').open('w') as log:
            subprocess.run(command, cwd=mech, env=clean_environment() | flags,
                           stdout=log, stderr=log, check=True)
        actual = {name: digest(folder / 'frontend' / name) for name in recipe['artifacts']}
        assert actual == recipe['artifacts'], (role, actual, recipe['artifacts'])
        records.append({'role': role, 'checked': args.checked, 'command': command,
                        'artifacts': actual, 'all_three_exact': True})
        print(role, 'object, metadata and canonical bytecode match exactly', flush=True)
    result = {'source_commit': commit, 'qualified_source_commit': recipes['compiler_source_commit'],
              'compiler_sha256': digest(compiler), 'records': records,
              'scope': 'Source emission only. No new runtime or source-through-link timing claim.'}
    (output / 'reproduction.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
