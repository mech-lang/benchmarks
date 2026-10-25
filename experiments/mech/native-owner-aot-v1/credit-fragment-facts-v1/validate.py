"""Sequential component and full native validation for the exact interaction revision."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
dispatch=HERE.parent/'native-owner-dispatch-v1'
source='/private/tmp/mech-native-hashmap-performance'
stages=[
 ('core',[str(STUDY/'validate-components.py'),'core'],HERE,STUDY/'core-validation-v1',2),
 ('runtime',[str(STUDY/'validate-components.py'),'runtime'],HERE,STUDY/'runtime-validation-v1',9),
 ('engine',[str(dispatch/'validate_native.py'),'credit-fragment-facts-engine-v1','native_worker',source,'--engine-budget'],dispatch,dispatch/'credit-fragment-facts-engine-v1',36),
 ('lines',[str(dispatch/'validate_native.py'),'credit-fragment-facts-lines-v1','native_text_line',source,'--engine-budget'],dispatch,dispatch/'credit-fragment-facts-lines-v1',27),
 ('native',[str(dispatch/'validate_native.py'),'credit-fragment-facts-native-v1','native_artifact::',source],dispatch,dispatch/'credit-fragment-facts-native-v1',393),
 ('catalog',[str(dispatch/'validate_native.py'),'credit-fragment-facts-catalog-v1','native_plan_catalog',source],dispatch,dispatch/'credit-fragment-facts-catalog-v1',1),
]
for name,args,cwd,folder,count in stages:
 assert source_state()==before
 with (STUDY/(name+'.controller.stdout')).open('xb') as out,(STUDY/(name+'.controller.stderr')).open('xb') as err:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=out,stderr=err)
 print(name,'exit',result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
 r=read(folder/'process.json');assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors'] and not r['signals']
 stdout=(folder/'stdout.bin').read_text()
 assert f'{count} passed; 0 failed' in stdout,(name,'unexpected test count')
 assert source_state()==before
print('All six validation stages passed at unchanged clean source',flush=True)
