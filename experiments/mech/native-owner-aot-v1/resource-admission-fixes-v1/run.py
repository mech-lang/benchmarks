"""Qualify the corrected baseline before the next preparation experiment."""
import subprocess
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1';SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
native=DISPATCH/'resource-admission-fixes-validation-v3'
assert read(native/'process.json')['exit_status']==0
provenance=read(native/'source-provenance.json')
assert provenance['clean_revision_qualified'] and provenance['before']['commit']==before['commit']
def run(label,arguments,cwd=HERE):
    with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
        result=subprocess.run([sys.executable,*arguments],cwd=cwd,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode:sys.exit(result.returncode)
run('catalog',['validate_native.py','resource-admission-fixes-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
run('compiler',['build_cli.py',plan['compiler']])
config=read(HERE/plan['parent_receipt']/'results.json')['configuration'];config.pop('reuse_build_receipt',None)
config.update(compiler=plan['compiler'],parent_receipt=plan['parent_receipt'],parent_binary=plan['parent_binary'],binary=plan['binary'],package='owner-counting-resource-admission-fixes',receipt=plan['receipt'])
args=['resource-admission-fixes-v1/measure-stage-driver.py']
for key,value in config.items():
    if value is None or value is False:continue
    args.append('--'+key.replace('_','-'))
    if value is not True:args.append(str(value))
run('build-prefix',args)
result=read(HERE/plan['receipt']/'results.json')
assert result['source_commit']==before['commit']
assert process.sha(STUDY/'measure-stage-driver.py')==result['study_driver_sha256']
(HERE/plan['receipt']/'measure-stage-driver.py').write_bytes((STUDY/'measure-stage-driver.py').read_bytes())
project=HERE/'.build'/(plan['binary']+'.project');parent=HERE/'.build'/(plan['parent_binary']+'.project')
for name in ['native-resources.json','program.mecb']:
    assert process.sha(project/name)==process.sha(parent/name)
run('full',['resource-admission-fixes-v1/measure.py'])
assert source_state()==before
print('Corrected baseline qualification completed at unchanged source',before['commit'],flush=True)
