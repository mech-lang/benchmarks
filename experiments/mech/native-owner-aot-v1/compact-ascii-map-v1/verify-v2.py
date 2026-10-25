"""Verify current-source direct copying, all measurements and every terminal receipt."""
from pathlib import Path
import hashlib,json,math,statistics,sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent;DISPATCH=HERE.parent/'native-owner-dispatch-v1'
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA,BYTECODE_SHA
sys.path.insert(0,str(HERE))
from analyze_profile import text_section
plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
qualified=['compact-ascii-native-v2','compact-ascii-engine-v1','compact-ascii-credits-v1','compact-ascii-catalog-v1']
failures={'compact-ascii-plan-v1','compact-ascii-native-v1'}
paths=[];validation=[]
for folder in sorted(DISPATCH.glob('compact-ascii-*')):
 r=read(folder/'process.json');s=read(folder/'source-provenance.json')
 assert s['source_unchanged'] and s['clean_revision_qualified'] and s['before']==s['after'] and s['before']['clean']
 assert r['exit_status']==(101 if folder.name in failures else 0)
 if folder.name in qualified:assert s['before']['commit']==before['commit']
 validation.append(dict(name=folder.name,source_commit=s['before']['commit'],exit_status=r['exit_status'],qualified=folder.name in qualified));paths.append(folder/'process.json')
for name,count in zip(qualified,[410,30,36,1]):
 assert f'{count} passed; 0 failed' in (DISPATCH/name/'stdout.bin').read_text()
assert '410 passed; 0 failed; 3 ignored' in (DISPATCH/'compact-ascii-native-v2/stdout.bin').read_text()
compiler=read(HERE/plan['compiler']/'results.json');assert compiler['source_commit']==before['commit'] and compiler['exit_status']==0
paths.extend((HERE/plan['compiler']).rglob('process.json'))
prefix=HERE/plan['receipt'];r=read(prefix/'results.json')
assert r['status']=='all-outputs-and-update-counts-verified' and r['source_commit']==before['commit']
assert r['source_sha256']==SOURCE_SHA and r['bytecode_sha256']==BYTECODE_SHA
assert r['study_driver_sha256']==process.sha(STUDY/'measure-stage-driver.py')==process.sha(prefix/'measure-stage-driver.py')
assert len(r['compiled_join_map_copies'])==len(r['joined_map_proofs'])==1
assert len(r['samples'])==9 and len(r['native_executions'])==8
for row in r['native_executions']:
 assert row['parallel_tasks']==7 and row['packed_map_updates']==6999961
 if row['label']=='candidate':assert row['fused_string_map_bytes']==1000000 and row['worker_credit_batches']>0
for subject in ['candidate','baseline','rust']:
 vals=[s['seconds'] for s in r['samples'] if s['label']==subject];assert len(vals)==3 and statistics.median(vals)==r['median_seconds'][subject]
 for tag in ['warmup','0','1','2']:assert process.sha(prefix/(tag+'-'+subject)/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
paths.extend(prefix.rglob('process.json'))
inspection=read(STUDY/'code-inspection.json')
assert inspection['source']==before and inspection['script_sha256']==process.sha(STUDY/'inspect-code-v2.py')
assert inspection['status']=='compact-mapping-two-lookup-leaves-full-fallback-and-unchanged-counting-qualified' and not inspection['review_required']
assert inspection['candidate_object_sha256']==r['object_sha256'] and inspection['assembly_gate_qualified']
gate=read(STUDY/'code-review.json');assert gate['source']==before and gate['proceed_to_primary'] and gate['inspection_sha256']==process.sha(STUDY/'code-inspection.json')
assert {c['control'] for c in inspection['comparisons']}=={'parent','byte_parent','ordinary'}
assert len(inspection['new_functions'])==4
for control in inspection['comparisons']:
 assert len(control['functions'])==(9 if control['control']=='ordinary' else 10) and all(f['qualified'] for f in control['functions'])
 unchanged=[f for f in control['functions'] if f['symbol']!='_mech_canonical_program_entry_v1' and not f['expected_mapping_change']]
 assert len(unchanged)==7 and all(f['identical'] for f in unchanged)
for name in ['joined','ordinary']:
 q=inspection['assembly'][name]
 assert q['full']['vector_lookups']==8 and q['projected']['vector_lookups']==2
 assert q['full']['narrowing_instructions']==q['projected']['narrowing_instructions']==0
 assert len(q['dispatch']['calls'])==2 and len(q['dispatch']['conditional_branches'])==1
assert inspection['assembly']['joined']['full']['table_vector_registers_hoisted']==8
assert inspection['assembly']['joined']['projected']['table_vector_registers_hoisted']==2
for row in inspection['static_disassembly']:
 folder=STUDY/row['folder'];assert process.sha(folder/'process.json')==row['process_sha256'] and process.sha(folder/'stdout.bin')==row['stdout_sha256'];paths.append(folder/'process.json')
project=HERE/'.build'/(plan['binary']+'.project')
for binary in [plan['parent_binary'],plan['byte_parent_binary'],plan['ordinary_binary']]:
 for name in ['program.mecb','native-resources.json']:assert process.sha(project/name)==process.sha(HERE/'.build'/(binary+'.project')/name)
full=[]
for batch in [1,2]:
 folder=HERE/f'full-compact-ascii-map-v{batch}';s=read(folder/'results.json')
 assert s['status']=='all-direct-transform-five-subject-full-outputs-updates-and-source-pins-verified'
 assert s['source']==s['source_after']==before and s['plan_sha256']==process.sha(STUDY/'plan.json') and s['driver_sha256']==process.sha(STUDY/'measure.py')
 assert s['input_sha256']==INPUT_SHA and s['policy_sha256']==POLICY_SHA and s['canonical_data_sha256']==DATA_SHA
 assert len(s['samples'])==50 and s['excluded_warmups']==s['excluded_outliers']==0
 for row in s['samples']:
  receipt=HERE/row['process'];assert process.sha(receipt)==row['process_sha256'] and process.sha(receipt.parent/'stdout.bin')==OUTPUT_SHA
  if row['subject']!='rust':
   n=receipt.parent.with_name(receipt.parent.name+'.native.json');assert process.sha(n)==row['native_sha256'];check_native(n)
   assert read(n)['native_worker_credit_batches']==854497
   if row['subject'] in ['candidate','parent','byte_parent']:assert read(n)['native_fused_string_map_bytes']==125000000
 for subject in ['candidate','parent','byte_parent','ordinary','rust']:
  vals=[row['seconds'] for row in s['samples'] if row['subject']==subject];assert len(vals)==10 and statistics.median(vals)==s['median_seconds'][subject]
  assert s['x_rust'][subject]==s['median_seconds'][subject]/s['median_seconds']['rust']
 for control in ['parent','byte_parent','ordinary','rust']:
  c=[row['seconds'] for row in s['samples'] if row['subject']=='candidate'];v=[row['seconds'] for row in s['samples'] if row['subject']==control]
  logs=[math.log(a/b) for a,b in zip(c,v)];p=s['paired_comparisons'][control]
  assert p['pairs']==10 and p['faster_matched_pairs']==sum(x<0 for x in logs)
  assert p['change_percent']==100*math.expm1(statistics.median(logs))
 paths.extend(folder.rglob('process.json'));full.append(s)
profile_dir=HERE/'profile-compact-ascii-map-build-v1';profile=read(profile_dir/'results.json')
assert profile['source_commit']==before['commit'] and profile['whole_machine_code_matches_timed']
binary=HERE/'.build'/plan['binary'];assert process.sha(binary)==r['candidate_sha256']
assert text_section(Path(profile['binary']))==text_section(binary)
assert hashlib.sha256(text_section(binary)).hexdigest()==profile['machine_code_sha256'];paths.extend(profile_dir.rglob('process.json'))
analysis=read(STUDY/'analysis.json');assert analysis['status']=='exact-current-binary-observations-partitioned' and analysis['source']==analysis['source_after']==before
assert analysis['analysis_sha256']==process.sha(STUDY/'analyze.py')
for subject in ['mech','rust']:
 folder=STUDY/f'early-{subject}-profile-v1';capture=read(folder/'results.json')
 assert capture['source']==capture['source_after']==before and capture['status']=='profile-captured' and len(capture['samples'])==len(capture['subjects'])==3
 assert capture['script_sha256']==process.sha(STUDY/'profile-capture.py') and capture['binary_sha256']==analysis['languages'][subject]['binary_sha256']
 for index,row in enumerate(capture['samples']):
  sub=folder/f'sample-{index}';assert process.sha(sub/'stacks.txt')==row['stacks_sha256'] and row['owned_direct_child'] and process.sha(sub/'subject/stdout.bin')==OUTPUT_SHA
  if subject=='mech':check_native(sub/'native.report.json');assert read(sub/'native.report.json')['native_fused_string_map_bytes']==125000000
 paths.extend(folder.rglob('process.json'))
counter=read(STUDY/'counters/results.json');assert counter['source']==counter['source_after']==before and len(counter['counters'])==20
assert counter['driver_sha256']==process.sha(STUDY/'counters.py')
for row in counter['counters']:
 folder=STUDY/'counters'/f"counter-{row['order']}-{row['subject']}"
 assert process.sha(folder/'stdout.bin')==OUTPUT_SHA and process.sha(folder/'stderr.bin')==row['stderr_sha256']
 if row['subject']!='rust':
  n=folder.with_name(folder.name+'.native.json');check_native(n);assert read(n)['native_worker_credit_batches']==854497
  if row['subject'] in ['candidate','parent','byte_parent']:assert read(n)['native_fused_string_map_bytes']==125000000
paths.extend((STUDY/'counters').rglob('process.json'))
for path in set(paths):
 p=read(path);assert p['exit_status']==(101 if path.parent.name in failures else 0) and p['inherited_common_mutex'] and p['reaped'] and p['group_closed'] and not p['signals'] and not p['cleanup_errors']
proof=read(STUDY/'source-map-equivalence.json');assert proof['source_sha256']==SOURCE_SHA and len(proof['ascii_cases'])==128 and all(row['original']==row['projected'] for row in proof['ascii_cases'])
audit=read(STUDY/'frame-audit-v2.json');assert audit['source_commit']==before['commit'] and audit['abi_version']==33
for row in audit['files']:assert process.sha(Path('/private/tmp/mech-native-hashmap-performance')/row['path'])==row['sha256']
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA and process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA and source_state()==before
result=dict(status='compact-map-current-source-output-code-profile-counter-and-terminal-receipts-verified',source=before,retained_process_receipts=len(set(paths)),validation=validation,passed_native_tests=410,passed_line_tests=30,passed_credit_tests=36,passed_catalog_tests=1,focused_window_tests=8,ignored_existing_manual_tests=3,primary_full_samples=100,primary_prefix_samples=9,excluded_prefix_warmups=3,excluded_full_warmups=0,excluded_outliers=0,candidate_sha256=r['candidate_sha256'],object_sha256=r['object_sha256'],binary_file_bytes=binary.stat().st_size,whole_text_bytes=profile['machine_code_bytes'],whole_text_sha256=profile['machine_code_sha256'],assembly=inspection['assembly'],counter_medians=counter['counter_medians'],full_sessions=[{k:s[k] for k in ['session','median_seconds','x_rust','paired_comparisons','median_peak_rss_bytes']} for s in full],verifier_sha256=process.sha(Path(__file__)))
process.save(STUDY/'verification.json',result);print({k:result[k] for k in ['status','retained_process_receipts','primary_full_samples','binary_file_bytes']})
