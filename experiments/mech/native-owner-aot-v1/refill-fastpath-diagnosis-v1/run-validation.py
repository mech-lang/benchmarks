"""Run exact-revision native validation and build the compiler serially."""
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1'
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
HEAD='36a0d26e05b92f0f3fb21bdbd3605af2108ec882'
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
focused=json.loads((DISPATCH/'refill-fastpath-focused-v1/process.json').read_text())
assert focused['exit_status']==0 and focused['reaped'] and focused['group_closed']
def run(label,args,cwd):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode: sys.exit(result.returncode)
run('native',['validate_native.py','refill-fastpath-native-v1','native_artifact::',str(SOURCE)],DISPATCH)
run('catalog',['validate_native.py','refill-fastpath-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
run('validation-summary',['summarize_validation.py','refill-fastpath-focused-v1','refill-fastpath-native-v1','refill-fastpath-catalog-v1'],DISPATCH)
run('compiler',['build_cli.py','compiler-v63'],HERE)
