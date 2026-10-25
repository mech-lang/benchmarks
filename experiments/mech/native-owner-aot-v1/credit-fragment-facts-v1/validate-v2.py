"""Resume the exact interaction validation after rejecting a zero-test worker filter."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
dispatch=HERE.parent/'native-owner-dispatch-v1'
source='/private/tmp/mech-native-hashmap-performance'
for component,count in [('core',2),('runtime',9)]:
 folder=STUDY/(component+'-validation-v1')
 r=read(folder/'process.json');p=read(folder/'source-provenance.json')
 assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors'] and not r['signals']
 assert p['before']==p['after']==before and p['source_unchanged']
 assert f'{count} passed; 0 failed' in (folder/'stdout.bin').read_text()
zero=dispatch/'credit-fragment-facts-engine-v1'
assert '0 passed; 0 failed' in (zero/'stdout.bin').read_text()
assert read(zero/'source-provenance.json')['before']['commit']==before['commit']
stages=[
 ('engine-v2',[str(dispatch/'validate_native.py'),'credit-fragment-facts-engine-v2','workers::',source,'--engine-budget'],dispatch,dispatch/'credit-fragment-facts-engine-v2',36),
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
print('Four remaining validation stages passed; original two component passes retained; zero-test worker run excluded',flush=True)
