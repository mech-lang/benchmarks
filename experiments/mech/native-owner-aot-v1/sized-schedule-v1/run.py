"""Focused validation, standalone build, two serial cohorts, then full validation."""
import json
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
DISPATCH = HERE.parent / 'native-owner-dispatch-v1'
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import read, source_state, process

plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']


def run(label, arguments, cwd=HERE):
    with (STUDY / (label + '.controller.stdout')).open('wb') as stdout, (STUDY / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=cwd, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


run('parallel', ['validate_native.py', 'sized-schedule-parallel-v1', 'parallel', str(SOURCE)], DISPATCH)
run('compiler', ['build_cli.py', plan['compiler']])
config = read(HERE / plan['parent_receipt'] / 'results.json')['configuration']
config.pop('reuse_build_receipt', None)
config.update(compiler=plan['compiler'], parent_receipt=plan['parent_receipt'], parent_binary=plan['parent_binary'],
              binary=plan['binary'], package='owner-counting-sized-schedule', receipt=plan['receipt'])
arguments = ['measure_stage.py']
for key, value in config.items():
    if value is None or value is False:
        continue
    arguments.append('--' + key.replace('_', '-'))
    if value is not True:
        arguments.append(str(value))
run('build-prefix', arguments)
result = read(HERE / plan['receipt'] / 'results.json')
assert result['source_commit'] == before['commit']
project = HERE / '.build' / (plan['binary'] + '.project')
parent = HERE / '.build' / (plan['parent_binary'] + '.project')
for name in ('native-descriptor.bin', 'native-descriptor.json', 'native-resources.json', 'program.o', 'program.mecb', 'object-identity.bin'):
    assert process.sha(project / name) == process.sha(parent / name), name
driver = HERE / 'measure_stage.py'
assert process.sha(driver) == result['study_driver_sha256']
(HERE / plan['receipt'] / 'measure-stage-driver.py').write_bytes(driver.read_bytes())
run('full', ['sized-schedule-v1/measure.py'])
run('native', ['validate_native.py', 'sized-schedule-native-v1', 'native_artifact::', str(SOURCE)], DISPATCH)
run('catalog', ['validate_native.py', 'sized-schedule-catalog-v1', 'native_plan_catalog', str(SOURCE)], DISPATCH)
assert source_state() == before
print('All scheduling trial stages completed at the unchanged source revision', flush=True)
