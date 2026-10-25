"""Fresh exact-text profiles and counters, excluded from primary timings."""
import subprocess
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
for name in ['scalar-cold-origin-native-v1','scalar-cold-origin-catalog-v1']:
 assert read(HERE.parent/'native-owner-dispatch-v1'/name/'process.json')['exit_status']==0
def run(label,args):
 with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
  result=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
run('profile-build',['build_profile.py','--receipt','profile-scalar-cold-origins-build-v1','--source',plan['binary'],'--output','counting-scalar-cold-origins-profile','--package','owner-counting-scalar-cold-origins','--compiler',plan['compiler']])
run('profile-capture',['scalar-cold-origins-v1/profile-capture.py'])
run('profile-analysis',['scalar-cold-origins-v1/analyze.py'])
run('counter',['scalar-cold-origins-v1/counters.py'])
assert source_state()==before
print('Exact-text profiles and counter diagnostics completed',flush=True)
