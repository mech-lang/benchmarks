"""Validate the immutable alias-region candidate, then build its CLI serially."""
import subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1'
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
HEAD='e82ed4d54d4490102ac41192d1fcbf492d467e08'
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
def run(label,args,cwd):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode: sys.exit(result.returncode)
run('lines',['validate_native.py','preparation-interactions-lines-v1','text_lines::chunks::',str(SOURCE),'--engine-budget'],DISPATCH)
run('workers',['validate_native.py','preparation-interactions-workers-v1','resident::budget::workers::',str(SOURCE),'--engine-budget'],DISPATCH)
run('native',['validate_native.py','preparation-interactions-native-v1','native_artifact::',str(SOURCE)],DISPATCH)
run('catalog',['validate_native.py','preparation-interactions-catalog-v1','native_plan_catalog',str(SOURCE)],DISPATCH)
run('compiler',['build_cli.py','compiler-v69'],HERE)
