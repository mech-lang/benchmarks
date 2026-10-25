"""Fresh exact-text profiles and counters, excluded from primary timings."""
import subprocess
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
for name in ['scalar-tail-register-native-v4','scalar-tail-register-catalog-v1']:
 assert read(HERE.parent/'native-owner-dispatch-v1'/name/'process.json')['exit_status']==0
def run(label,args):
 with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
run('profile-build',['build_profile.py','--receipt','profile-scalar-tail-registers-build-v1','--source',plan['binary'],'--output','counting-scalar-tail-registers-profile','--package','owner-counting-scalar-tail-registers','--compiler',plan['compiler']])
run('profile-capture',['scalar-tail-registers-v1/profile-capture.py'])
run('profile-analysis',['scalar-tail-registers-v1/analyze.py'])
run('counter',['scalar-tail-registers-v1/counters.py'])
assert source_state()==before
print('Exact-text profiles and counter diagnostics completed',flush=True)
