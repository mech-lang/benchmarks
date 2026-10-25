"""Build and prefix-qualify the immutable join/map candidate after regressions."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state,process
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
for name in ['pure-scalar-native-v1','pure-scalar-engine-v1','pure-scalar-credits-v1','pure-scalar-catalog-v1']:
 receipt=HERE.parent/'native-owner-dispatch-v1'/name
 r=read(receipt/'process.json');assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors']
 p=read(receipt/'source-provenance.json');assert p['clean_revision_qualified'] and p['before']['commit']==before['commit']
assert read(HERE/plan['compiler']/'results.json')['source_commit']==before['commit']
config=read(HERE/plan['parent_receipt']/'results.json')['configuration'];config.pop('reuse_build_receipt',None)
config.update(compiler=plan['compiler'],parent_receipt=plan['parent_receipt'],parent_binary=plan['parent_binary'],binary=plan['binary'],package=plan['package'],receipt=plan['receipt'],work_policy=69)
args=[sys.executable,str(STUDY/'measure-stage-driver.py')]
for key,value in config.items():
 if value is None or value is False:continue
 args.append('--'+key.replace('_','-'))
 if value is not True:args.append(str(value))
with (STUDY/'build-prefix.controller.stdout').open('xb') as out,(STUDY/'build-prefix.controller.stderr').open('xb') as err:
 result=subprocess.run(args,cwd=HERE,stdout=out,stderr=err)
print('build-prefix exit',result.returncode,flush=True)
if result.returncode:sys.exit(result.returncode)
r=read(HERE/plan['receipt']/'results.json');assert r['source_commit']==before['commit']
assert process.sha(STUDY/'measure-stage-driver.py')==r['study_driver_sha256']
(HERE/plan['receipt']/'measure-stage-driver.py').write_bytes((STUDY/'measure-stage-driver.py').read_bytes())
project=HERE/'.build'/(plan['binary']+'.project');parent=HERE/'.build'/(plan['parent_binary']+'.project')
for name in ['native-resources.json','program.mecb']:
 assert process.sha(project/name)==process.sha(parent/name)
assert source_state()==before
print('Join/map source, prefix outputs, composition counter, seven complete maps and existing codegen proofs verified',flush=True)
