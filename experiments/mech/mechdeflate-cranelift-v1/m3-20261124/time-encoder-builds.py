"""Serial source-to-executable measurements with a prebuilt compiler and fixed host support."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import statistics
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--recipe', type=Path, required=True)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--mech-root', type=Path, required=True)
parser.add_argument('--bench-root', type=Path, required=True)
parser.add_argument('--repeats', type=int, default=3)
args = parser.parse_args()
assert args.repeats >= 1
assert not args.output.exists()
args.output.mkdir(parents=True)
package = args.bench_root / 'experiments/mech/mechdeflate-cranelift-v1'
base = args.bench_root / 'experiments/mech/mechdeflate-81-v1'
helpers = runpy.run_path(str(base / 'rebuild.py'))
helpers['remove_build_overrides']()
recipe = json.loads(args.recipe.read_text())
original = json.loads((base / 'recipe.json').read_text())
original['source_commit'] = recipe['source_commit']
source = helpers['check_checkout'](args.mech_root, original)
flags = helpers['load_flags'](original)
environment = dict(os.environ)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(command, log, env):
    with log.open('w') as stream:
        subprocess.run(command, stdout=stream, stderr=stream, env=env, cwd=args.mech_root, check=True)

roles = {}
for name, role in recipe['roles'].items():
    settings = flags.copy()
    profiles = role['profile_inputs_sha256']
    used = set()
    for key, value in role['settings_delta'].items():
        if value is None:
            settings.pop(key, None)
        elif key == 'MECH_COMPACT_ROOT_TAIL_PROFILE':
            path = package / value
            assert sha(path) == profiles[value]
            used.add(value)
            settings[key] = str(path)
        elif key in helpers['PATH_SETTINGS']:
            entries = []
            for entry in value.split(';'):
                symbol, relative = entry.split('@', 1)
                path = package / relative
                assert sha(path) == profiles[relative]
                used.add(relative)
                entries.append(symbol + '@' + str(path))
            settings[key] = ';'.join(entries)
        else:
            settings[key] = value
    assert used == profiles.keys()
    variant = args.build / name
    receipt = json.loads((variant / 'receipt.json').read_text())
    assert receipt['source_commit'] == recipe['source_commit']
    assert sha(receipt['encoder_command'][0]) == receipt['compiler_sha256']
    for path, expected in role['artifacts'].items():
        assert sha(variant / 'bound' / path) == expected
    whole = args.build / 'silesia-support'
    encoder_link = ['/usr/bin/clang', '-arch', 'arm64', '-mmacosx-version-min=15.0', '-Wl,-dead_strip',
                    str(whole / 'clock.o'), str(whole / 'libmech_silesia.a'),
                    str(variant / 'bound/program.o'), str(package / 'support/mimalloc-2.1.7.o'),
                    '-o', str(variant / 'silesia-encoder')]
    roles[name] = {'receipt': receipt, 'flags': settings, 'encoder_link': encoder_link}

record = {'scope': __doc__, 'source_commit': recipe['source_commit'], 'source_sha256': sha(source),
          'recipe_sha256': sha(args.recipe), 'measurements': [],
          'roles': {name: {'compiler_sha256': row['receipt']['compiler_sha256'], 'flags': row['flags'],
                           'source_to_object_command': row['receipt']['encoder_command'],
                           'worker_link_command': row['receipt']['worker_command'],
                           'encoder_link_command': row['encoder_link'],
                           'artifacts': recipe['roles'][name]['artifacts']} for name, row in roles.items()}}
for scope in ['encoder', 'worker']:
    for repeat in range(args.repeats):
        order = list(roles)
        if repeat % 2:
            order.reverse()
        for name in order:
            role = roles[name]
            receipt = role['receipt']
            log = args.output / (scope + '-' + str(repeat) + '-' + name)
            start = time.perf_counter()
            run(receipt['encoder_command'], log.with_suffix('.emit.log'), environment | role['flags'])
            object_done = time.perf_counter()
            for filename in recipe['roles'][name]['artifacts']:
                shutil.copyfile(args.build / name / 'frontend' / filename,
                                args.build / name / 'bound' / filename)
            command = role['encoder_link'] if scope == 'encoder' else receipt['worker_command']
            run(command, log.with_suffix('.link.log'), environment)
            complete = time.perf_counter()
            # Verification is after the full elapsed measurement.
            for path, expected in recipe['roles'][name]['artifacts'].items():
                assert sha(args.build / name / 'bound' / path) == expected
            executable = args.build / name / ('silesia-encoder' if scope == 'encoder' else 'bound/mech-worker')
            expected_executable = receipt['silesia_actor_sha256' if scope == 'encoder' else 'worker_sha256']
            assert sha(executable) == expected_executable
            row = {'scope': scope, 'role': name, 'repeat': repeat,
                   'source_through_executable_seconds': complete - start,
                   'source_through_object_seconds': object_done - start,
                   'link_seconds': complete - object_done,
                   'executable_sha256': expected_executable}
            record['measurements'].append(row)
            (args.output / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
            print(json.dumps(row), flush=True)
record['medians_seconds'] = {
    scope: {name: statistics.median(row['source_through_executable_seconds']
                                    for row in record['measurements'] if row['scope'] == scope and row['role'] == name)
            for name in roles} for scope in ['encoder', 'worker']}
(args.output / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
