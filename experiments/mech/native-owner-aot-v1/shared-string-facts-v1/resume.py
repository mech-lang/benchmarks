"""Resume after correcting the qualification wrapper's expected work policy."""
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
DISPATCH = HERE.parent / 'native-owner-dispatch-v1'
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import read, source_state, process

plan = read(STUDY / 'execution-plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']


def run(label, arguments, cwd=HERE):
    with (STUDY / (label + '.controller.stdout')).open('xb') as stdout, (STUDY / (label + '.controller.stderr')).open('xb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=cwd, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


config = read(HERE / plan['reuse_build_receipt'] / 'results.json')['configuration']
config.update(work_policy=67, reuse_build_receipt=plan['reuse_build_receipt'], receipt=plan['receipt'])
arguments = ['shared-string-facts-v1/measure-stage-driver.py']
for key, value in config.items():
    if value is None or value is False:
        continue
    arguments.append('--' + key.replace('_', '-'))
    if value is not True:
        arguments.append(str(value))
run('prefix-resumed', arguments)
result = read(HERE / plan['receipt'] / 'results.json')
assert result['source_commit'] == before['commit']
project = HERE / '.build' / (plan['binary'] + '.project')
parent = HERE / '.build' / (plan['parent_binary'] + '.project')
for name in ('native-descriptor.bin', 'native-resources.json', 'program.mecb'):
    assert process.sha(project / name) == process.sha(parent / name), name
driver = STUDY / 'measure-stage-driver.py'
assert process.sha(driver) == result['study_driver_sha256']
(HERE / plan['receipt'] / 'measure-stage-driver.py').write_bytes(driver.read_bytes())
run('full', ['shared-string-facts-v1/measure.py'])
run('native', ['validate_native.py', 'shared-string-facts-native-v1', 'native_artifact::', str(SOURCE)], DISPATCH)
run('catalog', ['validate_native.py', 'shared-string-facts-catalog-v1', 'native_plan_catalog', str(SOURCE)], DISPATCH)
assert source_state() == before
print('All resumed timing and qualification stages completed at unchanged source', flush=True)
