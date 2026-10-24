"""Validate the immutable alias-region candidate, then build its CLI serially."""
import subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1'
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
HEAD='9f6896b529e1057767503cc2ee6d98e3719617e4'
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
def run(label,args,cwd):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode: sys.exit(result.returncode)
run('native',['validate_native.py','disjoint-state-native-v1','native_artifact::',str(SOURCE)],DISPATCH)
run('catalog',['validate_native.py','disjoint-state-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
run('compiler',['build_cli.py','compiler-v68'],HERE)
