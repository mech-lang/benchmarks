"""Build and execute the native Boolean-extension witnesses from a Mech checkout."""
from argparse import ArgumentParser
from pathlib import Path
import json
import subprocess
import reproduce


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument('--mech-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path)
    args = parser.parse_args()
    root, out = args.mech_root.resolve(), args.output.resolve()
    out.mkdir(parents=True)
    target = args.target_dir.resolve() if args.target_dir else out / 'target'
    compiler = reproduce.build_compiler(root, out, target)
    test = root / 'hosts/gpu/src/native_artifact/program/codegen/byte_boolean_tests.rs'
    manifest = out / 'compiler-driver/Cargo.toml'
    manifest.write_text(manifest.read_text() + '\n[[test]]\nname = "byte_boolean_extensions"\npath = ' + json.dumps(str(test)) + '\n')
    build = json.loads((out / 'compiler-build.json').read_text())
    command = [x for x in build['command'] if x not in ['--bin', 'compile_profile']]
    command[2] = 'test'
    command += ['--no-run', '--test', 'byte_boolean_extensions', '--message-format=json']
    with (out / 'probe-build.stdout').open('w') as stdout, (out / 'probe-build.stderr').open('w') as stderr:
        subprocess.run(command, cwd=root, env=reproduce.clean_environment() | build['environment'], stdout=stdout, stderr=stderr, check=True)
    executables = []
    for line in (out / 'probe-build.stdout').read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get('reason') == 'compiler-artifact' and row.get('executable') and row['target']['name'] == 'byte_boolean_extensions':
            executables.append(Path(row['executable']))
    binary, = executables
    runs = []
    for ccmp in ['off', 'on']:
        for mode in ['0', '1']:
            folder = out / (ccmp + '-' + mode)
            folder.mkdir()
            flags = {'MECH_ARM64_REUSE_I8_DEFINITIONS': 'all', 'MECH_ARM64_REUSE_I8_BOOLEAN_DEFINITIONS': mode, 'MECH_BOOLEAN_EXTENSION_PROBE': str(folder)}
            if ccmp == 'on':
                flags['MECH_ARM64_CCMP_SHARED_BOOLEAN'] = '1'
            command = [str(binary), '--nocapture', '--test-threads=1']
            log = folder / 'tests.log'
            with log.open('w') as stream:
                subprocess.run(command, env=reproduce.clean_environment() | flags, stdout=stream, stderr=stream, check=True)
            assert 'test result: ok. 2 passed; 0 failed;' in log.read_text()
            calls = sum(json.loads((folder / (group + '.json')).read_text())['native_observations'] for group in ['clean', 'fallback'])
            runs.append({'ccmp': ccmp, 'mode': mode, 'command': command, 'flags': flags, 'passed': 2, 'native_calls': calls, 'log': str(log.relative_to(out)), 'log_sha256': reproduce.digest(log)})
    changes, excluded = [], []
    for ccmp in ['off', 'on']:
        for group in ['clean', 'fallback']:
            left = {r['name']: r for r in json.loads((out / (ccmp + '-0') / (group + '.json')).read_text())['functions']}
            right = {r['name']: r for r in json.loads((out / (ccmp + '-1') / (group + '.json')).read_text())['functions']}
            assert left.keys() == right.keys()
            for name, row in left.items():
                other = right[name]
                changed = row['body'] != other['body']
                if row['form'] == 'Parameter' or (row['form'] in ['TooDeep', 'TooWide'] and row['opt'] == 'none'):
                    assert not changed, (ccmp, name)
                    excluded.append(name)
                if changed:
                    changes.append({'ccmp': ccmp, 'name': name, 'form': row['form'], 'opt': row['opt'], 'off_bytes': len(row['body']), 'on_bytes': len(other['body'])})
        assert any(r['ccmp'] == ccmp and r['form'] == 'Or' and r['opt'] == 'none' for r in changes)
    assert len(changes) == 1360 and len(excluded) == 320
    calls = sum(r['native_calls'] for r in runs)
    assert calls == 4177920
    record = {'verified': True, 'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'compiler_sha256': reproduce.digest(compiler), 'probe_binary_sha256': reproduce.digest(binary), 'test_source_sha256': reproduce.digest(test), 'native_calls': calls, 'native_test_executions': 8, 'runs': runs, 'changed_functions': changes, 'excluded_exact_functions': len(excluded), 'scope': 'Native mathematical-reference and memory checks with dirty inputs, mixed widths, shared users, aliases, guarded pointers, ordinary/combined comparisons and bounded-proof fallbacks. Construction and checks are separate from all primary clocks.'}
    (out / 'probe-verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ['verified', 'source_commit', 'native_calls', 'native_test_executions']}, indent=2))


if __name__ == '__main__':
    main()
