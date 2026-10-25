"""Sequential fixed-source qualification of actual direct-copy kernels and programs."""
import subprocess,sys,re
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state
plan=read(STUDY/'development-plan-v1.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
dispatch=HERE.parent/'native-owner-dispatch-v1';prior=dispatch/'joined-transform-codegen-v2'
r=read(prior/'process.json');p=read(prior/'source-provenance.json')
assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['signals'] and not r['cleanup_errors']
assert p['clean_revision_qualified'] and p['before']['commit']==before['commit']
assert '3 passed; 0 failed' in (prior/'stdout.bin').read_text()
for label,pattern,extra,minimum in [('focused','fused_join_map',[],7),('loans','native_text_line_join_loan',['--engine-budget'],2),('native','native_artifact::',[],404),('engine','native_text_line',['--engine-budget'],30),('credits','workers::',['--engine-budget'],36),('catalog','native_plan_catalog',[],1)]:
 folder='joined-transform-'+label+'-v1'
 with (STUDY/(label+'.controller.stdout')).open('xb') as out,(STUDY/(label+'.controller.stderr')).open('xb') as err:
  r=subprocess.run([sys.executable,str(dispatch/'validate_native.py'),folder,pattern,'/private/tmp/mech-native-hashmap-performance',*extra],cwd=dispatch,stdout=out,stderr=err)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
 text=(dispatch/folder/'stdout.bin').read_text();actual=sum(int(n) for n in re.findall(r'test result: ok\. (\d+) passed; 0 failed',text))
 assert actual>=minimum
 print(label,'qualified passed checks',actual,flush=True)
 assert source_state()==before
print('Direct kernels, full source, ownership, full native, line storage, finite credits and catalog qualified',flush=True)
