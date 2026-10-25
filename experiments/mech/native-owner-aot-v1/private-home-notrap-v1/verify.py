"""Verify current-source direct copying, all measurements and every terminal receipt."""
from pathlib import Path
import hashlib,json,math,statistics,sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent;DISPATCH=HERE.parent/'native-owner-dispatch-v1'
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA,BYTECODE_SHA
sys.path.insert(0,str(HERE))
from analyze_profile import text_section
plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
qualified=['private-home-notrap-prefix-v1','private-home-notrap-native-v1','private-home-notrap-engine-v1','private-home-notrap-credits-v1','private-home-notrap-catalog-v1']
failures=set()
paths=[];validation=[]
for folder in sorted(DISPATCH.glob('private-home-notrap-*')):
 r=read(folder/'process.json');s=read(folder/'source-provenance.json')
 assert s['source_unchanged'] and s['clean_revision_qualified'] and s['before']==s['after'] and s['before']['clean']
 assert r['exit_status']==(101 if folder.name in failures else 0)
 if folder.name in qualified:assert s['before']['commit']==before['commit']
 validation.append(dict(name=folder.name,source_commit=s['before']['commit'],exit_status=r['exit_status'],qualified=folder.name in qualified));paths.append(folder/'process.json')
for name,count in zip(qualified,[8,406,30,36,1]):
 assert f'{count} passed; 0 failed' in (DISPATCH/name/'stdout.bin').read_text()
assert '406 passed; 0 failed; 3 ignored' in (DISPATCH/'private-home-notrap-native-v1/stdout.bin').read_text()
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
assert inspection['source']==before and inspection['script_sha256']==process.sha(STUDY/'inspect-code.py')
assert inspection['status']=='private-home-object-captured-awaiting-assembly-review' and not inspection['review_required']
assert inspection['candidate_object_sha256']==r['object_sha256']
gate=read(STUDY/'code-review.json');assert gate['source']==before and not gate['proceed_to_primary'] and gate['inspection_sha256']==process.sha(STUDY/'code-inspection.json')
assert {c['control'] for c in inspection['comparisons']}=={'parent','byte_parent','ordinary'}
for control in inspection['comparisons']:
 assert len(control['functions'])==(9 if control['control']=='ordinary' else 10) and all(f['qualified'] for f in control['functions'])
assert not inspection['assembly']['candidate']['field_sequences']['confirmed_discarded_pointer_sequences']
assert inspection['static_root_reduction']['opaque_call_count_unchanged']
parent_comparison=next(c for c in inspection['comparisons'] if c['control']=='parent')
assert all(f['identical'] for f in parent_comparison['functions'] if f['symbol']!='_mech_canonical_program_entry_v1')
for row in inspection['static_disassembly']:
 folder=STUDY/row['folder'];assert process.sha(folder/'process.json')==row['process_sha256'] and process.sha(folder/'stdout.bin')==row['stdout_sha256'];paths.append(folder/'process.json')
project=HERE/'.build'/(plan['binary']+'.project')
for binary in [plan['parent_binary'],plan['byte_parent_binary'],plan['ordinary_binary']]:
 for name in ['program.mecb','native-resources.json']:assert process.sha(project/name)==process.sha(HERE/'.build'/(binary+'.project')/name)
audit=read(STUDY/'ownership-audit-v2.json');assert audit['audited_source']==before['commit'] and audit['implemented']
root=Path('/private/tmp/mech-native-hashmap-performance')
for file,digest in audit['source_sha256'].items():assert process.sha(root/file)==digest
parent_comparison=next(c for c in inspection['comparisons'] if c['control']=='parent')
assert len(parent_comparison['functions'])==10 and all(f['identical'] for f in parent_comparison['functions'])
assert not any(inspection['static_root_reduction'][k] for k in ['instructions','loads','stores'])
assert inspection['static_root_reduction']['opaque_call_count_unchanged']
assert not (HERE/'full-private-home-notrap-v1').exists() and not (HERE/'full-private-home-notrap-v2').exists()
for path in set(paths):
 p=read(path);assert p['exit_status']==0 and p['inherited_common_mutex'] and p['reaped'] and p['group_closed'] and not p['signals'] and not p['cleanup_errors']
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA and process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA and source_state()==before
result=dict(status='private-home-contract-correctness-and-identical-generated-code-verified-no-full-timing-campaign',source=before,retained_process_receipts=len(set(paths)),validation=validation,passed_native_tests=406,passed_line_tests=30,passed_credit_tests=36,passed_catalog_tests=1,focused_window_tests=8,ignored_existing_manual_tests=3,primary_full_samples=0,primary_prefix_samples=9,excluded_prefix_warmups=3,candidate_sha256=r['candidate_sha256'],object_sha256=r['object_sha256'],all_ten_generated_functions_identical_to_parent=True,full_timing_skipped=True,performance_promotion=False,inspection_sha256=process.sha(STUDY/'code-inspection.json'),review_sha256=process.sha(STUDY/'code-review.json'),ownership_audit_sha256=process.sha(STUDY/'ownership-audit-v2.json'),verifier_sha256=process.sha(Path(__file__)))
process.save(STUDY/'verification.json',result);print({k:result[k] for k in ['status','retained_process_receipts','primary_full_samples']})
