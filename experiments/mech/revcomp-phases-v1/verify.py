"""Replay retained instrumented records and complete-output hash receipts."""
import hashlib,json,re,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=load(HERE/'captures-v1/results.json');assert d['status']=='nine-closed-instrumented-full-outputs-pass' and len(d['samples'])==9
 assert d['benchmark_samples']==0 and d['diagnostic_only'] and not d['source_changed'] and d['mutex_inode']==83858837
 assert d['script_sha256']==sha(HERE/'run.py') and d['parent_study_seal_sha256']==sha(HERE.parent/'revcomp-streaming-v1/seal.json')
 for row in d['samples']:
  p=HERE/'captures-v1'/f"{row['round']:02d}-{row['label']}";r=load(p/'process.json');o=load(p/'stdout-omitted.json')
  assert r['exit_status']==0 and not r['quantitative_benchmark'] and r['reaped'] and r['group_closed'] and not r['cleanup_errors']
  assert o['bytes']==254166745 and o['sha256']==d['output_sha256'] and o['verified_complete'] and o['reaped'] and o['group_closed']
  actual=[]
  for line in (p/'stderr.bin').read_text().splitlines():
   m=re.fullmatch(r'byte-record-profile bytes=(\d+) read=([\d.]+) compute=([\d.]+) write=([\d.]+)',line);assert m
   actual.append(dict(bytes=int(m[1]),read_seconds=float(m[2]),compute_seconds=float(m[3]),write_seconds=float(m[4])))
  assert actual==row['records'] and [r['bytes'] for r in actual]==[50000000,75000000,125000000]
  assert row['phase_totals']=={p:sum(r[p+'_seconds'] for r in actual) for p in ('read','compute','write')}
 closed=0
 for p in HERE.rglob('process.json'):
  r=load(p);assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'];closed+=1
 baseline=load(HERE.parent/'revcomp-streaming-v1/analysis.json')['comparison_denominator'];profiles={}
 for name in sorted(d['binary_pins']):
  rows=[r for r in d['samples'] if r['label']==name];assert {r['round'] for r in rows}=={1,2,3}
  profiles[name]={p:dict(median_phase_seconds=statistics.median(r['phase_totals'][p] for r in rows),fraction_of_accepted_whole_mech_aot=statistics.median(r['phase_totals'][p] for r in rows)/baseline['seconds']) for p in ('read','compute','write')}
 result=dict(status='verified-diagnostic-only',closed_owned_processes=closed,instrumented_full_output_hash_receipts=9,accepted_whole_mech_aot_reference=baseline,phase_summaries=profiles,benchmark_samples=0,limitations=['Instrumented phase clocks are not whole-process benchmark samples.','Separately rounded phase medians need not sum to a whole-process median.','No allocation trace is present; reuse remains a hypothesis to qualify and measure.'])
 (HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
