"""Resume qualification at the retained successful frozen app build."""
import subprocess
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1';SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan-v2.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
assert read(DISPATCH/'borrowed-offset-cursor-prefix-native-v1/process.json')['exit_status']==0
assert read(HERE/plan['compiler']/'results.json')['source_commit']==before['commit']
def run(label,arguments,cwd=HERE):
    with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
        result=subprocess.run([sys.executable,*arguments],cwd=cwd,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode:sys.exit(result.returncode)
config=read(HERE/plan['reuse_build_receipt']/'results.json')['configuration']
config.update(receipt=plan['receipt'],reuse_build_receipt=plan['reuse_build_receipt'])
args=['borrowed-offset-cursor-v1/'+plan['qualification_driver']]
for key,value in config.items():
    if value is None or value is False:continue
    args.append('--'+key.replace('_','-'))
    if value is not True:args.append(str(value))
run('build-prefix-v2',args)
r=read(HERE/plan['receipt']/'results.json');assert r['source_commit']==before['commit']
driver=STUDY/plan['qualification_driver'];assert process.sha(driver)==r['study_driver_sha256']
(HERE/plan['receipt']/'measure-stage-driver.py').write_bytes(driver.read_bytes())
project=HERE/'.build'/(plan['binary']+'.project');parent=HERE/'.build'/(plan['parent_binary']+'.project')
for name in ['native-resources.json','program.mecb']:
    assert process.sha(project/name)==process.sha(parent/name)
assert process.sha(project/'program.o')!=process.sha(parent/'program.o')
run('full-v2',['borrowed-offset-cursor-v1/measure-v2.py'])
run('native',['validate_native.py','borrowed-offset-cursor-native-v1','native_artifact::',str(SOURCE)],DISPATCH)
run('catalog',['validate_native.py','borrowed-offset-cursor-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
assert source_state()==before
print('Direct-offset candidate qualification completed at unchanged source',before['commit'],flush=True)
