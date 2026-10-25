"""Full native and catalog qualification after three actual counter differential tests."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
dispatch=HERE.parent/'native-owner-dispatch-v1'
focused=dispatch/'scalar-traversal-count-focused-v3'
r=read(focused/'process.json');p=read(focused/'source-provenance.json')
assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['signals'] and not r['cleanup_errors']
assert p['clean_revision_qualified'] and p['before']['commit']==before['commit']
assert '3 passed; 0 failed' in (focused/'stdout.bin').read_text()
for label,folder,pattern,count in [('native','scalar-traversal-count-native-v1','native_artifact::',396),('catalog','scalar-traversal-count-catalog-v1','native_plan_catalog',1)]:
 with (STUDY/(label+'.controller.stdout')).open('xb') as out,(STUDY/(label+'.controller.stderr')).open('xb') as err:
  r=subprocess.run([sys.executable,str(dispatch/'validate_native.py'),folder,pattern,'/private/tmp/mech-native-hashmap-performance'],cwd=dispatch,stdout=out,stderr=err)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
 assert f'{count} passed; 0 failed' in (dispatch/folder/'stdout.bin').read_text()
 assert source_state()==before
print('Counter differential, full native and catalog checks qualified at unchanged clean revision',flush=True)
