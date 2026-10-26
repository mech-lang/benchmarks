from pathlib import Path
import json, os, re, subprocess, time
ROOT=Path('/private/tmp/mech-post-native-cleanup')
OUT=Path('/private/tmp/post-native-cleanup-qualification-v3')
OUT.mkdir(exist_ok=False)
HEAD='83ee4903a541acb174cc25822c22ad50980e6223'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
ENV=os.environ.copy();ENV.update(CARGO_INCREMENTAL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0', CARGO_TARGET_DIR='/private/tmp/mech-post-native-cleanup-target')
rows=[]
def run(name,command,tests=False,timeout=1800,extra=None):
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
    wrapper=['python3','scripts/run-native-plan-stage.py','--stage',name,'--timeout-secs',str(timeout),'--log-dir',str(OUT),'--']+command
    before=time.time()
    with (OUT/(name+'.console.log')).open('w') as log:
        result=subprocess.run(wrapper,cwd=ROOT,env=ENV|dict(extra or {}),stdout=log,stderr=subprocess.STDOUT)
    output=(OUT/(name+'.log')).read_text(errors='replace')
    counts=[list(map(int,x)) for x in re.findall(r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;',output,re.M)]
    row=dict(stage=name,head=HEAD,command=command,exit_code=result.returncode,seconds=time.time()-before,counts=counts)
    rows.append(row);(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(name,result.returncode,counts,flush=True)
    assert result.returncode==0,(name,output[-7000:])
    if tests: assert counts and sum(c[0] for c in counts)>0 and not any(c[1] for c in counts),(name,counts)
def test(name,packages,features,selection,extra=None):
    command=['cargo','+nightly-2026-03-03','test','--locked','--offline','-j1']
    for package in packages:command+=['-p',package]
    command+=['--no-default-features','--features',features]+selection+['--','--test-threads=1','--nocapture']
    run(name,command,True,extra=extra)
test('program-integration',['mech-gpu'],'canonical-native-program',['--test','canonical_artifact_program'])
test('representative-objects',['mech-gpu'],'canonical-native-program',['--test','native_architecture_equivalence'],{'MECH_NATIVE_ARCHITECTURE_SNAPSHOT':str(OUT/'snapshots')})
assert len(list((OUT/'snapshots').iterdir()))==32
before=Path('/private/tmp/native-consolidation-final-equivalence-v1/snapshots')
assert all(path.read_bytes()==(before/path.name).read_bytes() for path in (OUT/'snapshots').iterdir())
(OUT/'complete.json').write_text(json.dumps(dict(head=HEAD,status='passed',stages=len(rows),representative_files=32,representative_files_equal_to='01b8b397011b6a774b7d9f730578a4ef92bf30f6'),indent=2)+'\n')
print('complete',HEAD,flush=True)
