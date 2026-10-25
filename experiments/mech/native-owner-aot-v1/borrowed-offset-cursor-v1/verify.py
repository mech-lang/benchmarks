"""Verify corrected-baseline qualification, measurements and retained failures."""
from pathlib import Path
import json
import statistics
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent;DISPATCH=HERE.parent/'native-owner-dispatch-v1'
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA,BYTECODE_SHA
plan=read(STUDY/'plan-v2.json');commit=plan['source_commit'];before=source_state()
assert before['commit']==commit and not before['status']
checks={
 'borrowed-offset-cursor-engine-v1':0,
 'borrowed-offset-cursor-prefix-native-v1':0,
 'borrowed-offset-cursor-native-v1':0,
 'borrowed-offset-cursor-catalog-v1':0,
}
paths=[];failed=[]
for name,status in checks.items():
 folder=DISPATCH/name;p=folder/'process.json';d=read(p);assert d['exit_status']==status
 v=read(folder/'source-provenance.json')
 assert v['clean_revision_qualified'] and v['source_unchanged'] and v['before']==v['after']
 if name in checks:assert v['before']['commit']==commit
 if status:failed.append(dict(receipt=str(p.relative_to(HERE.parent)),source=v['before']['commit'],exit_status=status))
 paths.append(p)
assert '392 passed; 0 failed; 3 ignored' in (DISPATCH/'borrowed-offset-cursor-native-v1/stdout.bin').read_text()
assert '1 passed; 0 failed' in (DISPATCH/'borrowed-offset-cursor-catalog-v1/stdout.bin').read_text()
compiler=read(HERE/plan['compiler']/'results.json');assert compiler['source_commit']==commit and compiler['exit_status']==0
paths.extend((HERE/plan['compiler']).rglob('process.json'))
prefix=HERE/plan['receipt'];p=read(prefix/'results.json')
assert p['status']=='all-outputs-and-update-counts-verified' and p['source_commit']==commit
assert p['study_driver_sha256']==process.sha(STUDY/'measure-stage-driver-v2.py')==process.sha(prefix/'measure-stage-driver.py')
assert p['source_sha256']==SOURCE_SHA and p['bytecode_sha256']==BYTECODE_SHA
assert p['object_sha256']!=read(HERE/plan['parent_receipt']/'results.json')['object_sha256']
assert p['native_descriptor_sha256']!=read(HERE/plan['parent_receipt']/'results.json')['native_descriptor_sha256']
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
 folder=HERE/f'full-borrowed-offset-cursor-v{batch}';d=read(folder/'results.json')
 assert d['status']=='all-borrowed-offset-cursor-full-outputs-updates-and-source-pins-verified'
 assert d['source']==d['source_after']==before
 assert d['plan_sha256']==process.sha(STUDY/'plan-v2.json') and d['driver_sha256']==process.sha(STUDY/'measure-v2.py')
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
for name in ['native-resources.json','program.mecb']:
 assert process.sha(project/name)==process.sha(parent/name)
# The first standalone build succeeded; only its old-ABI audit stopped.
initial=HERE/plan['reuse_build_receipt'];previous=read(initial/'results.json')
assert not previous['samples'] and not previous['native_executions']
assert previous['candidate_sha256']==p['candidate_sha256']
assert previous['study_driver_sha256']==process.sha(STUDY/'measure-stage-driver.py')
audit_failure=read(STUDY/'audit-failure-v1.json')
assert audit_failure['primary_benchmark_samples']==0 and audit_failure['controller_exit_status']==1
assert audit_failure['controller_stderr_sha256']==process.sha(STUDY/'build-prefix.controller.stderr')
reuse=read(prefix/'reused-build.json')
assert reuse['timing_observations_reused']==0
assert reuse['source_results_sha256']==process.sha(initial/'results.json')
assert reuse['process_receipt_sha256']==process.sha(initial/'build/process.json')
paths.extend(initial.rglob('process.json'))
profile_path=HERE/'profile-borrowed-offset-cursor-build-v1'
profile=read(profile_path/'results.json')
assert profile['source_commit']==commit and profile['whole_machine_code_matches_timed']
from analyze_profile import text_section
import hashlib
assert text_section(Path(profile['binary']))==text_section(HERE/'.build'/plan['binary'])
assert hashlib.sha256(text_section(Path(profile['binary']))).hexdigest()==profile['machine_code_sha256']
paths.extend(profile_path.rglob('process.json'))
analysis=read(STUDY/'analysis.json');assert analysis['status']=='exact-current-binary-observations-partitioned'
assert analysis['source']==analysis['source_after']==before
assert analysis['analysis_sha256']==process.sha(STUDY/'analyze.py')
for subject in ['mech','rust']:
 folder=STUDY/f'early-{subject}-profile-v1';capture=read(folder/'results.json')
 assert capture['status']=='profile-captured' and capture['source']==capture['source_after']==before
 assert len(capture['samples'])==len(capture['subjects'])==3
 assert capture['binary_sha256']==analysis['languages'][subject]['binary_sha256']
 assert capture['script_sha256']==process.sha(STUDY/'profile-capture.py')
 for i,sample in enumerate(capture['samples']):
  sub=folder/f'sample-{i}'
  assert process.sha(sub/'stacks.txt')==sample['stacks_sha256']
  assert sample['owned_direct_child']
  assert process.sha(sub/'subject/stdout.bin')==OUTPUT_SHA
  if subject=='mech':check_native(sub/'native.report.json')
 paths.extend(folder.rglob('process.json'))
counter=read(STUDY/'counters/results.json')
assert counter['source']==counter['source_after']==before
assert len(counter['counters'])==9 and counter['driver_sha256']==process.sha(STUDY/'counters.py')
for row in counter['counters']:
 folder=STUDY/'counters'/f"counter-{row['order']}-{row['subject']}"
 assert process.sha(folder/'stderr.bin')==row['stderr_sha256']
 assert process.sha(folder/'stdout.bin')==OUTPUT_SHA
 if row['subject']!='rust':check_native(folder.with_name(folder.name+'.native.json'))
paths.extend((STUDY/'counters').rglob('process.json'))
code=read(STUDY/'code-audit/results.json')
assert code['whole_profile_text_matches_primary'] and code['source']==code['source_after']==before
assert code['whole_text_sha256']==profile['machine_code_sha256']
assert code['object_sha256']==p['object_sha256']
assert code['fragments_sha256']==process.sha(STUDY/'code-audit/compact-row-fragments.s')
paths.extend((STUDY/'code-audit').rglob('process.json'))
for path in set(paths):
 d=read(path)
 assert d['inherited_common_mutex'] and d['reaped'] and d['group_closed']
 assert not d['cleanup_errors'] and not d['signals'] and d['birth_identity']['pid']>0
 if d['exit_status']!=0:assert path.parent.name in checks and checks[path.parent.name]==d['exit_status']
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
assert source_state()==before
binary=HERE/'.build'/plan['binary'];assert process.sha(binary)==p['candidate_sha256']
result=dict(status='all-direct-offset-outputs-code-profiles-counters-and-terminal-processes-verified',source=before,passed_engine_tests=24,passed_focused_prefix_tests=29,passed_native_tests=392,passed_catalog_tests=1,ignored_existing_manual_tests=3,retained_process_receipts=len(set(paths)),preserved_native_failures=failed,preserved_checker_stop=audit_failure,source_sha256=SOURCE_SHA,bytecode_sha256=BYTECODE_SHA,object_sha256=p['object_sha256'],candidate_sha256=p['candidate_sha256'],binary_file_bytes=binary.stat().st_size,whole_text_bytes=profile['machine_code_bytes'],whole_text_sha256=profile['machine_code_sha256'],counter_medians=counter['counter_medians'],full_sessions=[{k:d[k] for k in ['session','median_seconds','x_rust','median_peak_rss_bytes','paired_change_percent','paired_change_interval_95']} for d in full],primary_full_samples=36,primary_prefix_samples=9,excluded_prefix_warmups=3,excluded_full_warmups=0,excluded_outliers=0,driver_sha256=process.sha(Path(__file__)))
process.save(STUDY/'verification.json',result)
print(json.dumps({k:result[k] for k in ['status','retained_process_receipts','primary_full_samples','binary_file_bytes','full_sessions']}))
