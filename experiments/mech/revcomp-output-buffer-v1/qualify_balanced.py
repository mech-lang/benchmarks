"""Compare both native output policies against the frozen prior binary."""
from build import HERE,ROOT,PLAN,process
from pathlib import Path
import json,fcntl

def main():
 out=HERE/'qualification-v2';out.mkdir(exist_ok=False);corpus_path=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json';corpus=json.loads(corpus_path.read_bytes())
 binaries={'parent':HERE.parent/'revcomp-buffer-reuse-v1/.build/mech-revcomp-reuse','quarter':HERE/'.build/mech-revcomp-quarter','one':HERE/'.build/mech-revcomp-one'}
 report=dict(status='running',cases=[],benchmark_samples=0,new_regressions=[],existing_source_contract_differences=[],binary_pins={k:process.sha(p) for k,p in binaries.items()},corpus_sha256=process.sha(corpus_path))
 env={**PLAN['environment'],'RAYON_NUM_THREADS':'8','MECH_SEQUENCE_PARTITIONS':'4'}
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for case in (r for r in corpus['cases'] if r['benchmark']=='revcomp'):
   inp=corpus_path.parent/case['stdin']['path'];assert process.sha(inp)==case['stdin']['sha256'];observed={}
   for label,binary in binaries.items():
    d=out/f"{label}-{case['case']}";r=process.execute([str(binary)],d,env,lock,stdin=inp)
    observed[label]=dict(exit_status=r['exit_status'],stdout_sha256=process.sha(d/'stdout.bin'),stderr_sha256=process.sha(d/'stderr.bin'))
   assert observed['parent']==observed['quarter']==observed['one'],(case['case'],observed)
   d=out/f"parent-{case['case']}";v=observed['parent'];valid=v['exit_status']==0 and v['stdout_sha256']==case['expected']['sha256'] and not (d/'stderr.bin').read_bytes() if case['expected_exit']==0 else v['exit_status']!=0
   if not valid:report['existing_source_contract_differences'].append(case['case'])
   report['cases'].append(dict(case=case['case'],observed=observed,shared_reference_contract_met=valid));process.save(out/'results.json',report)
 report['status']='all-61-three-way-behaviors-identical';process.save(out/'results.json',report);print(json.dumps({'status':report['status'],'cases':len(report['cases']),'existing_source_contract_differences':report['existing_source_contract_differences']}))
if __name__=='__main__':main()
