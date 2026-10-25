"""Verify corrected-baseline qualification, measurements and retained failures."""
from pathlib import Path
import json
import statistics
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent;DISPATCH=HERE.parent/'native-owner-dispatch-v1'
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA,BYTECODE_SHA
plan=read(STUDY/'plan.json');commit=plan['source_commit'];before=source_state()
assert before['commit']==commit and not before['status']
checks={
 'resource-admission-fixes-validation-v1':101,
 'resource-admission-fixes-byte-regression-v2':101,
 'resource-admission-fixes-byte-diagnostic-v3':101,
 'resource-admission-fixes-parallel-v4':0,
 'resource-admission-fixes-validation-v2':101,
 'resource-admission-fixes-validation-v3':0,
 'resource-admission-fixes-catalog-v1':0,
}
paths=[];failed=[]
for name,status in checks.items():
 folder=DISPATCH/name;p=folder/'process.json';d=read(p);assert d['exit_status']==status
 v=read(folder/'source-provenance.json')
 assert v['clean_revision_qualified'] and v['source_unchanged'] and v['before']==v['after']
 if name in ['resource-admission-fixes-validation-v3','resource-admission-fixes-catalog-v1']:assert v['before']['commit']==commit
 if status:failed.append(dict(receipt=str(p.relative_to(HERE.parent)),source=v['before']['commit'],exit_status=status))
 paths.append(p)
assert '392 passed; 0 failed; 3 ignored' in (DISPATCH/'resource-admission-fixes-validation-v3/stdout.bin').read_text()
assert '1 passed; 0 failed' in (DISPATCH/'resource-admission-fixes-catalog-v1/stdout.bin').read_text()
compiler=read(HERE/plan['compiler']/'results.json');assert compiler['source_commit']==commit and compiler['exit_status']==0
paths.extend((HERE/plan['compiler']).rglob('process.json'))
prefix=HERE/plan['receipt'];p=read(prefix/'results.json')
assert p['status']=='all-outputs-and-update-counts-verified' and p['source_commit']==commit
assert p['study_driver_sha256']==process.sha(STUDY/'measure-stage-driver.py')==process.sha(prefix/'measure-stage-driver.py')
assert p['source_sha256']==SOURCE_SHA and p['bytecode_sha256']==BYTECODE_SHA
assert p['object_sha256']==read(HERE/plan['parent_receipt']/'results.json')['object_sha256']
assert p['native_descriptor_sha256']==read(HERE/plan['parent_receipt']/'results.json')['native_descriptor_sha256']
assert len(p['samples'])==9 and len(p['native_executions'])==8
for r in p['native_executions']:
 assert r['parallel_tasks']==7 and r['packed_map_updates']==6999961
for subject in ['candidate','baseline','rust']:
 vals=[r['seconds'] for r in p['samples'] if r['label']==subject];assert len(vals)==3
 assert statistics.median(vals)==p['median_seconds'][subject]
 for rnd in ['warmup','0','1','2']:
  folder=prefix/(rnd+'-'+subject)
  assert process.sha(folder/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
paths.extend(prefix.rglob('process.json'))
full=[]
for batch in [1,2]:
 folder=HERE/f'full-resource-admission-fixes-v{batch}';d=read(folder/'results.json')
 assert d['status']=='all-resource-admission-fixes-full-outputs-updates-and-source-pins-verified'
 assert d['source']==d['source_after']==before
 assert d['plan_sha256']==process.sha(STUDY/'plan.json') and d['driver_sha256']==process.sha(STUDY/'measure.py')
 assert len(d['samples'])==18 and d['excluded_warmups']==d['excluded_outliers']==0
 for r in d['samples']:
  receipt=HERE/r['process'];assert process.sha(receipt)==r['process_sha256']
  assert process.sha(receipt.parent/'stdout.bin')==OUTPUT_SHA
  if r['subject']!='rust':
   n=receipt.parent.with_name(receipt.parent.name+'.native.json')
   assert process.sha(n)==r['native_sha256'];check_native(n)
 for subject in ['candidate','parent','rust']:
  vals=[r['seconds'] for r in d['samples'] if r['subject']==subject];assert len(vals)==6
  assert statistics.median(vals)==d['median_seconds'][subject]
  assert d['x_rust'][subject]==d['median_seconds'][subject]/d['median_seconds']['rust']
 paths.extend(folder.rglob('process.json'));full.append(d)
project=HERE/'.build'/(plan['binary']+'.project');parent=HERE/'.build'/(plan['parent_binary']+'.project')
for name in ['native-resources.json','program.mecb','program.o']:
 assert process.sha(project/name)==process.sha(parent/name)
for path in set(paths):
 d=read(path)
 assert d['inherited_common_mutex'] and d['reaped'] and d['group_closed']
 assert not d['cleanup_errors'] and not d['signals'] and d['birth_identity']['pid']>0
 if d['exit_status']!=0:assert path.parent.name in checks and checks[path.parent.name]==d['exit_status']
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
assert source_state()==before
binary=HERE/'.build'/plan['binary'];assert process.sha(binary)==p['candidate_sha256']
result=dict(status='all-corrected-baseline-outputs-admission-tests-pins-and-terminal-processes-verified',source=before,passed_native_tests=392,passed_catalog_tests=1,ignored_existing_manual_tests=3,retained_process_receipts=len(set(paths)),preserved_failures=failed,source_sha256=SOURCE_SHA,bytecode_sha256=BYTECODE_SHA,object_sha256=p['object_sha256'],candidate_sha256=p['candidate_sha256'],binary_file_bytes=binary.stat().st_size,full_sessions=[{k:d[k] for k in ['session','median_seconds','x_rust','median_peak_rss_bytes','paired_change_percent','paired_change_interval_95']} for d in full],primary_full_samples=36,primary_prefix_samples=9,excluded_prefix_warmups=3,excluded_full_warmups=0,excluded_outliers=0,driver_sha256=process.sha(Path(__file__)))
process.save(STUDY/'verification.json',result)
print(json.dumps({k:result[k] for k in ['status','retained_process_receipts','primary_full_samples','binary_file_bytes','full_sessions']}))
