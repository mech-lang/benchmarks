"""Compare both exact binaries over the complete retained revcomp corpus."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'revcomp-streaming-v1'))
from build_baseline import ROOT,PLAN,process
HERE=Path(__file__).resolve().parent
import fcntl,json
from pathlib import Path

def main():
 out=HERE/'qualification-v1';out.mkdir(exist_ok=False);corpus_path=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json';corpus=json.loads(corpus_path.read_bytes())
 sources={'parent':HERE.parent/'revcomp-streaming-v1/.build/mech-revcomp-candidate','candidate':HERE/'.build/mech-revcomp-reuse'}
 env={**PLAN['environment'],'MECH_SEQUENCE_PARTITIONS':'4','RAYON_NUM_THREADS':'8'}
 report=dict(status='running',corpus_sha256=process.sha(corpus_path),binaries={k:process.sha(p) for k,p in sources.items()},cases=[],existing_source_contract_differences=[],new_regressions=[],benchmark_samples=0)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for case in (r for r in corpus['cases'] if r['benchmark']=='revcomp'):
   stdin=corpus_path.parent/case['stdin']['path'];assert process.sha(stdin)==case['stdin']['sha256'];observed={}
   for label,binary in sources.items():
    d=out/f"{label}-{case['case']}";r=process.execute([str(binary)],d,env,lock,stdin=stdin,deadline=30)
    observed[label]=dict(exit_status=r['exit_status'],stdout_sha256=process.sha(d/'stdout.bin'),stderr_sha256=process.sha(d/'stderr.bin'))
   assert observed['parent']==observed['candidate'],(case['case'],observed)
   valid=(observed['candidate']['exit_status']==0 and observed['candidate']['stdout_sha256']==case.get('expected',{}).get('sha256') and observed['candidate']['stderr_sha256']==process.sha(out/f"candidate-{case['case']}"/'stderr.bin')) if case['expected_exit']==0 else observed['candidate']['exit_status']!=0
   if case['expected_exit']==0:valid=valid and not (out/f"candidate-{case['case']}"/'stderr.bin').read_bytes()
   result=dict(case=case['case'],parent=observed['parent'],candidate=observed['candidate'],shared_reference_contract_met=valid)
   report['cases'].append(result)
   if not valid:report['existing_source_contract_differences'].append(case['case'])
   process.save(out/'results.json',report)
 report['status']='all-61-parent-candidate-behaviors-identical';process.save(out/'results.json',report);print(json.dumps({'status':report['status'],'cases':len(report['cases']),'existing_source_contract_differences':report['existing_source_contract_differences']},indent=2))
if __name__=='__main__':main()
