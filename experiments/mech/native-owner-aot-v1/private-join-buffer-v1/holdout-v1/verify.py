"""Verify the single predetermined uninstrumented holdout and all terminal receipts."""
from pathlib import Path
import statistics,sys,json
OUT=Path(__file__).resolve().parent;STUDY=OUT.parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA
r=read(OUT/'capture/results.json');plan=read(OUT/'plan.json');before=source_state()
assert r['source']==r['source_after']==before and before['commit']==plan['observer_source'] and not before['status']
assert r['binary_build_source']==plan['candidate_build_source']=='88b883b4cfcdc8625440b3f075c8334bfeb09382'
assert r['holdout_plan_sha256']==process.sha(OUT/'plan.json') and r['driver_sha256']==process.sha(OUT/'measure.py')
assert r['excluded_warmups']==r['excluded_outliers']==0 and len(r['samples'])==18 and r['session']==3
assert r['input_sha256']==INPUT_SHA and r['policy_sha256']==POLICY_SHA and r['canonical_data_sha256']==DATA_SHA
build=read(HERE/'private-join-buffer-timing-v1/results.json')
assert build['source_commit']==r['binary_build_source'] and r['pins']['candidate']==build['candidate_sha256']
for subject,path in [('candidate',HERE/'.build/counting-private-join-buffer'),('parent',HERE/'.build/counting-credit-fragment-facts'),('rust',HERE.parent/'native-hashmap-work-v1/.build/knucleotide-rust-7')]:
 assert process.sha(path)==r['pins'][subject]
 vals=[s['seconds'] for s in r['samples'] if s['subject']==subject];assert len(vals)==6
 assert statistics.median(vals)==r['median_seconds'][subject] and r['x_rust'][subject]==r['median_seconds'][subject]/r['median_seconds']['rust']
paths=[]
for s in r['samples']:
 p=HERE/s['process'];assert process.sha(p)==s['process_sha256'] and process.sha(p.parent/'stdout.bin')==OUTPUT_SHA
 n=read(p);assert n['exit_status']==0 and n['reaped'] and n['group_closed'] and n['inherited_common_mutex'] and n['quantitative_benchmark'] and not n['signals'] and not n['cleanup_errors']
 assert b'PPHASE_V1' not in (p.parent/'stderr.bin').read_bytes()
 if s['subject']!='rust':
  native=p.parent.with_name(p.parent.name+'.native.json');assert process.sha(native)==s['native_sha256'];check_native(native)
  assert read(native)['native_worker_credit_batches']==854497
  if s['subject']=='candidate':assert read(native)['native_fused_string_map_bytes']==125000000
 paths.append(p)
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA and source_state()==before
result=dict(status='predetermined-uninstrumented-holdout-and-all-terminal-receipts-verified',source=before,candidate_build_source=r['binary_build_source'],native_processes=len(paths),excluded_observations=0,median_seconds=r['median_seconds'],x_rust=r['x_rust'],paired_change_percent=r['paired_change_percent'],paired_change_interval_95=r['paired_change_interval_95'],faster_matched_pairs=r['faster_matched_pairs'],driver_sha256=process.sha(OUT/'measure.py'),verifier_sha256=process.sha(Path(__file__)))
process.save(OUT/'verification.json',result);print(result)
