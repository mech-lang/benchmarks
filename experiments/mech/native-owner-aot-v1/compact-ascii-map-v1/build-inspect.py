"""Build the qualified compact-map binary and capture its actual code before primary timings."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
for name in ['compact-ascii-native-v2','compact-ascii-engine-v1','compact-ascii-credits-v1','compact-ascii-catalog-v1']:
 p=HERE.parent/'native-owner-dispatch-v1'/name
 r=read(p/'process.json');provenance=read(p/'source-provenance.json')
 assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['signals'] and not r['cleanup_errors']
 assert provenance['clean_revision_qualified'] and provenance['before']['commit']==before['commit']
for label,args in [
 ('compiler',[str(HERE/'build_cli.py'),plan['compiler']]),
 ('qualify-prefix',[str(STUDY/'qualify-prefix.py')]),
 ('code-inspection',[str(STUDY/'inspect-code.py')]),
]:
 assert source_state()==before
 with (STUDY/(label+'.controller.stdout')).open('xb') as out,(STUDY/(label+'.controller.stderr')).open('xb') as err:
  r=subprocess.run([sys.executable,*args],cwd=HERE,stdout=out,stderr=err)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
assert source_state()==before
print('Compiler, separate prefix and static object capture completed; full timings require a reviewed assembly gate.',flush=True)
