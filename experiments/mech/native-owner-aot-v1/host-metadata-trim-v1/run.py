"""Validate one committed host-only candidate, then build it serially."""
import fcntl
import json
import re
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
DISPATCH = HERE.parent / 'native-owner-dispatch-v1'
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state

plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']


def run(label, args, cwd):
    with (STUDY / (label + '.controller.stdout')).open('wb') as stdout, (STUDY / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *args], cwd=cwd, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


for label, pattern, extra in [('engine', 'native_artifact::', ['--engine-budget']),
                              ('native', 'native_artifact::', []),
                              ('catalog', 'native_plan_catalog', [])]:
    name = f'host-metadata-trim-{label}-v1'
    run(label, ['validate_native.py', name, pattern, str(SOURCE), *extra], DISPATCH)
    folder = DISPATCH / name
    receipt = read(folder / 'process.json')
    provenance = read(folder / 'source-provenance.json')
    assert provenance['clean_revision_qualified'] and provenance['source_unchanged']
    matches = re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;', (folder / 'stdout.bin').read_text())
    assert matches and sum(int(m[0]) for m in matches) > 0
    process.save(folder / 'summary.json', dict(status='passed', passed=sum(int(m[0]) for m in matches),
        ignored=sum(int(m[2]) for m in matches), source_commit=before['commit'],
        clean_revision_qualified=True, all_owned_processes_reaped_and_groups_closed=receipt['reaped'] and receipt['group_closed'] and not receipt['cleanup_errors'],
        process_sha256=process.sha(folder / 'process.json'), provenance_sha256=process.sha(folder / 'source-provenance.json')))
env = read(HERE / 'compiler-v69/results.json')['environment']
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    receipt = process.execute(['/Users/cim310/.cargo/bin/cargo', 'check', '--manifest-path', str(SOURCE / 'Cargo.toml'),
        '--offline', '--locked', '-p', 'mech-engine', '--no-default-features', '--features', 'native-artifact'],
        STUDY / 'featureless-check', env, lock, deadline=600, quantitative=False)
    assert receipt['exit_status'] == 0
assert source_state() == before
run('compiler', ['build_cli.py', plan['compiler']], HERE)
config = read(HERE / 'preparation-combined-timing-v1/results.json')['configuration']
config.pop('reuse_build_receipt', None)
config.update(compiler=plan['compiler'], parent_receipt=plan['parent_receipt'], parent_binary=plan['parent_binary'],
              binary=plan['binary'], package='owner-counting-host-metadata-trim', receipt=plan['receipt'])
arguments = ['measure_stage.py']
for key, value in config.items():
    if value is None or value is False:
        continue
    arguments.append('--' + key.replace('_', '-'))
    if value is not True:
        arguments.append(str(value))
run('build-prefix', arguments, HERE)
folder = HERE / plan['receipt']
result = read(folder / 'results.json')
assert result['source_commit'] == before['commit']
assert result['object_sha256'] == read(HERE / plan['parent_receipt'] / 'results.json')['object_sha256']
project = HERE / '.build' / (plan['binary'] + '.project')
parent = HERE / '.build' / (plan['parent_binary'] + '.project')
for name in ('native-descriptor.bin', 'native-descriptor.json', 'native-resources.json', 'program.o', 'program.mecb', 'object-identity.bin'):
    assert process.sha(project / name) == process.sha(parent / name), name
driver = HERE / 'measure_stage.py'
assert process.sha(driver) == result['study_driver_sha256']
(folder / 'measure-stage-driver.py').write_bytes(driver.read_bytes())
assert source_state() == before
print('Same Object, descriptor, resources and source verified', flush=True)
