"""Two predetermined five-subject balanced complete-process sessions."""
import fcntl,json,math,random,statistics,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA

def main():
 plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['source_commit'] and not before['status']
 gate=read(STUDY/'code-review.json');assert gate['source']==before and gate['proceed_to_primary'] and gate['inspection_sha256']==process.sha(STUDY/'code-inspection.json')
 candidate=read(HERE/plan['receipt']/'results.json');parent=read(HERE/plan['parent_receipt']/'results.json');ordinary=read(HERE/plan['ordinary_receipt']/'results.json');byte_parent=read(HERE/plan['byte_parent_receipt']/'results.json')
 targets=dict(candidate=HERE/'.build'/plan['binary'],parent=HERE/'.build'/plan['parent_binary'],ordinary=HERE/'.build'/plan['ordinary_binary'],byte_parent=HERE/'.build'/plan['byte_parent_binary'],rust=HERE.parent/'native-hashmap-work-v1/.build/knucleotide-rust-7')
 pins=dict(candidate=candidate['candidate_sha256'],parent=parent['candidate_sha256'],ordinary=ordinary['candidate_sha256'],byte_parent=byte_parent['candidate_sha256'],rust='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763')
 assert candidate['source_commit']==before['commit'] and len(candidate['compiled_join_map_copies'])==1
 for subject,binary in targets.items():assert process.sha(binary)==pins[subject]
 inp=HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin';policy=HERE/'full-disjoint-state-v1/launch.json';data=HERE.parents[2]/'data/benchmarks.json'
 assert process.sha(inp)==INPUT_SHA and process.sha(policy)==POLICY_SHA and process.sha(data)==DATA_SHA
 env=read(HERE/plan['compiler']/'results.json')['environment']
 with Path(PLAN['common_mutex']).open('a+') as lock:
  assert Path(PLAN['common_mutex']).stat().st_ino==83858837
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for batch in [1,2]:
   out=HERE/f'full-candidate-value-loads-state-v{batch}';out.mkdir(exist_ok=False)
   orders=plan['orders'] if batch==1 else list(reversed(plan['orders']))
   report=dict(status='running',source=before,session=batch,plan_sha256=process.sha(STUDY/'plan.json'),driver_sha256=process.sha(Path(__file__)),pins=pins,orders=orders,samples=[],input_sha256=INPUT_SHA,policy_sha256=POLICY_SHA,canonical_data_sha256=DATA_SHA,object_sha256=candidate['object_sha256'],excluded_warmups=0,excluded_outliers=0,scope='Ten fixed Williams orders, five subjects, secured complete startup through exit. All observations retained; no instrumentation and no concurrent subjects.')
   process.save(out/'results.json',report)
   for index,order in enumerate(orders):
    assert set(order)==set(targets)
    for position,subject in enumerate(order):
     assert process.sha(targets[subject])==pins[subject]
     folder=out/f'{index}-{position}-{subject}';native=out/(folder.name+'.native.json')
     command=[str(targets[subject])]+([] if subject=='rust' else [str(policy),str(native),'--'])
     receipt=process.execute(command,folder,env,lock,stdin=inp,deadline=30,quantitative=True)
     assert receipt['exit_status']==0 and process.sha(folder/'stdout.bin')==OUTPUT_SHA
     if subject!='rust':
      check_native(native);n=read(native);assert n['native_worker_credit_batches']==854497 and n['native_worker_credit_claims']>0
      if subject in ['candidate','parent','byte_parent']:assert n['native_fused_string_map_bytes']==125000000
     report['samples'].append(dict(order=index,position=position,subject=subject,seconds=receipt['elapsed_seconds'],maximum_rss_bytes=receipt['maximum_rss_bytes'],process=str((folder/'process.json').relative_to(HERE)),process_sha256=process.sha(folder/'process.json'),native_sha256=process.sha(native) if subject!='rust' else None))
     process.save(out/'results.json',report)
    print('session',batch,'order',index+1,'of',len(orders),'verified',flush=True)
   values={s:[r for r in report['samples'] if r['subject']==s] for s in targets}
   report['median_seconds']={s:statistics.median(r['seconds'] for r in rows) for s,rows in values.items()}
   report['x_rust']={s:v/report['median_seconds']['rust'] for s,v in report['median_seconds'].items()}
   report['median_peak_rss_bytes']={s:statistics.median(r['maximum_rss_bytes'] for r in rows) for s,rows in values.items()}
   report['standard_deviation_seconds']={s:statistics.stdev(r['seconds'] for r in rows) for s,rows in values.items()}
   report['paired_comparisons']={}
   for offset,control in enumerate(['parent','byte_parent','ordinary','rust']):
    logs=[math.log(c['seconds']/p['seconds']) for c,p in zip(values['candidate'],values[control])]
    rng=random.Random(plan['bootstrap_seed']+10*batch+offset)
    boot=sorted(statistics.median(rng.choices(logs,k=len(logs))) for _ in range(20000))
    report['paired_comparisons'][control]=dict(change_percent=100*math.expm1(statistics.median(logs)),interval_95=[100*math.expm1(boot[i]) for i in [499,19499]],faster_matched_pairs=sum(x<0 for x in logs),pairs=len(logs))
   assert source_state()==before and process.sha(data)==DATA_SHA
   report.update(source_after=before,status='all-direct-transform-five-subject-full-outputs-updates-and-source-pins-verified');process.save(out/'results.json',report)
   print(json.dumps({k:report[k] for k in ['session','median_seconds','x_rust','paired_comparisons','median_peak_rss_bytes']}),flush=True)
if __name__=='__main__':main()
