import hashlib,json,os,pathlib,re,subprocess,sys
out=pathlib.Path(__file__).parent;root=pathlib.Path('/private/tmp/mech-native-base-ci-green-v4');source=json.loads((out/'source.json').read_text())
env=os.environ.copy();env.update(M4='/opt/homebrew/Cellar/m4/1.4.21/bin/m4',CARGO_TARGET_DIR='/private/tmp/native-ci-stack-repair-target',CARGO_INCREMENTAL='0',CARGO_BUILD_JOBS='1',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0')
rows=[]
def stable():assert hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=root)).hexdigest()==source['patch_sha256']
def stage(name,command):
 stable();cmd=[sys.executable,str(root/'scripts/run-native-plan-stage.py'),'--stage',name,'--timeout-secs','1800','--log-dir',str(out),'--',*command]
 with (out/(name+'.driver.log')).open('wb') as log:r=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 s=json.loads((out/(name+'.summary.json')).read_text());assert s['owned_group_cleanup']=='complete' and s['reason']=='exit'
 text=(out/(name+'.log')).read_text();counts=re.findall(r'test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;',text)
 row=dict(stage=name,command=command,exit_code=r.returncode,summary=s,counts=[list(map(int,x)) for x in counts]);rows.append(row);(out/'source-profile-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,r.returncode,counts,flush=True);stable()
 if r.returncode:sys.exit(r.returncode)
base=['cargo','+nightly-2026-03-03']
common=['--locked','--offline','-j1','-p','mech-engine','--no-default-features']
stage('narrow-source-check',base+['check',*common,'--features','source'])
cmd=base+['test',*common,'--features','source']
for name in ['canonical_source_profile','canonical_source_review','canonical_source_collections','canonical_boolean_match']:cmd+=['--test',name]
stage('narrow-source-tests',cmd)
cmd=base+['test',*common,'--features','full_source,resident-artifact']
for name in ['canonical_document_state','canonical_document_streaming','canonical_source_semantics','canonical_source_review','canonical_source_structures','canonical_source_collections','canonical_boolean_match','canonical_source_completion','canonical_executable_semantics']:cmd+=['--test',name]
stage('full-source-tests',cmd)
(out/'source-profiles-complete.json').write_text(json.dumps(dict(status='passed',source=source,stages=len(rows)),indent=2)+'\n')
