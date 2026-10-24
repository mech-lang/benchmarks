"""Run exact-revision native validation and build the compiler serially."""
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
DISPATCH=HERE.parent/'native-owner-dispatch-v1'
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
HEAD='438646017717a5c4392721f13c6f935e88c59527'
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
def run(label,args,cwd):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=cwd,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode: sys.exit(result.returncode)
run('engine',['validate_native.py','escrow-backoff12-engine-v1','resident::budget::workers::',str(SOURCE),'--engine-budget'],DISPATCH)
run('compiler',['build_cli.py','compiler-v66'],HERE)
