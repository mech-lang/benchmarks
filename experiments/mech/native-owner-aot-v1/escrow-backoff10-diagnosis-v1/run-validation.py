"""Run exact-revision native validation and build the compiler serially."""
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1'
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
HEAD='0b4ce3e7c316ae4248399c3ce1b2ed14b8eb65e2'
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
def run(label,args,cwd):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode: sys.exit(result.returncode)
run('engine',['validate_native.py','escrow-backoff10-engine-v1','resident::budget::workers::',str(SOURCE),'--engine-budget'],DISPATCH)
run('native',['validate_native.py','escrow-backoff10-native-v1','native_artifact::',str(SOURCE)],DISPATCH)
run('catalog',['validate_native.py','escrow-backoff10-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
run('validation-summary',['summarize_validation.py','escrow-backoff10-engine-v1','escrow-backoff10-native-v1','escrow-backoff10-catalog-v1'],DISPATCH)
run('compiler',['build_cli.py','compiler-v65'],HERE)
