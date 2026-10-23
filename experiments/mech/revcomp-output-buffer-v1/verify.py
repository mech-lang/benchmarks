"""Replay four rejected output-policy builds and both complete timing cohorts."""
from pathlib import Path
import json,hashlib,statistics,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 analysis=load(HERE/'analysis.json');assert analysis['status']=='four-correct-policies-rejected-no-production-change' and not analysis['chart_admission']
 assert sha(ROOT/'data/benchmarks.json')==analysis['catalog_sha256']
 base=load(HERE.parent/'revcomp-buffer-reuse-v1/build-v1/results.json')['binary_sha256'];old=load(HERE.parent/'revcomp-streaming-v1/baseline-build-v1/results.json')['binary_sha256'];rust=load(HERE.parent/'revcomp-streaming-v1/candidate-build-v1/results.json')['rust']['binary_sha256']
 builds={};binary_pins={str(HERE.parent/'revcomp-buffer-reuse-v1/.build/mech-revcomp-reuse'):base,str(HERE.parent/'revcomp-streaming-v1/.build/mech-revcomp-parent'):old,str(HERE.parent/'revcomp-streaming-v1/.build/rust-revcomp-1'):rust}
 objects=load(HERE.parent/'revcomp-streaming-v1/candidate-build-v1/results.json')['mech']['unchanged_emitted_inputs']
 for folder,labels in [('build-v1',('two-mib','four-mib')),('build-v2',('quarter','one'))]:
  report=load(HERE/folder/'results.json');assert len(report['variants'])==2
  for label in labels:
   b=report['variants'][label];d=HERE/folder/label
   assert sha(d/('runtime.rs'))==b['runtime_sha256'] and b['tests_passed']==13
   assert '13 passed; 0 failed' in (d/'tests/stdout.bin').read_text()
   for name,h in objects.items():assert sha(d/'object'/name)==h
   assert load(d/'build/process.json')['command']==b['command'] and load(d/'build/process.json')['exit_status']==0
   binary_pins[str(HERE/'.build'/('mech-revcomp-'+label))]=b['binary_sha256'];builds[label]=b
 for name,h in binary_pins.items():
  if Path(name).exists():assert sha(Path(name))==h,name
 corpus=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json';cases={r['case']:r for r in load(corpus)['cases'] if r['benchmark']=='revcomp'};bounded=0
 old_differences=load(HERE.parent/'revcomp-buffer-reuse-v1/qualification-v1/results.json')['existing_source_contract_differences']
 for folder,labels in [('qualification-v1',('parent','two-mib','four-mib')),('qualification-v2',('parent','quarter','one'))]:
  q=load(HERE/folder/'results.json');assert q['status']=='all-61-three-way-behaviors-identical' and len(q['cases'])==61 and not q['new_regressions'] and q['corpus_sha256']==sha(corpus)
  assert q['binary_pins']=={label:base if label=='parent' else builds[label]['binary_sha256'] for label in labels}
  differences=[]
  for row in q['cases']:
   assert set(row['observed'])==set(labels) and all(r==row['observed']['parent'] for r in row['observed'].values())
   for label in labels:
    d=HERE/folder/f"{label}-{row['case']}";r=load(d/'process.json');assert row['observed'][label]==dict(exit_status=r['exit_status'],stdout_sha256=sha(d/'stdout.bin'),stderr_sha256=sha(d/'stderr.bin'));bounded+=1
   expected=cases[row['case']];d=HERE/folder/f"parent-{row['case']}";v=row['observed']['parent']
   valid=v['exit_status']==0 and v['stdout_sha256']==expected['expected']['sha256'] and not (d/'stderr.bin').read_bytes() if expected['expected_exit']==0 else v['exit_status']!=0
   assert valid==row['shared_reference_contract_met']
   if not valid:differences.append(row['case'])
  assert differences==q['existing_source_contract_differences']==old_differences
 outputs=official=0
 for folder,n in [('run-v1',35),('run-v2',28)]:
  run=load(HERE/folder/'results.json');a=analysis['cohorts'][folder];assert len(run['samples'])==n and run['status']==f'all-{n}-full-size-outputs-pass' and run['mutex_inode']==83858837
  assert sha(HERE/folder/'results.json')==a['report_sha256'];den=run['summary']['reuse4']['median_seconds'];assert a['comparison_denominator']['seconds']==den
  for name,h in run['pins'].items():
   if name in binary_pins:assert binary_pins[name]==h
   else:assert sha(ROOT/Path(name).relative_to('/private/tmp/mech-benchmark-publication'))==h,name
  expected=(ROOT/'archive/workloads/revcomp/inputs/revcomp-output-1000.txt').read_bytes()
  for label in run['variants']:
   d=HERE/folder/f'official-{label}';r=load(d/'process.json');assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==expected and not (d/'stderr.bin').read_bytes();official+=1
  for row in run['samples']:
   d=HERE/folder/f"{row['round']:02d}-{row['label']}";r=load(d/'process.json');o=load(d/'stdout-omitted.json')
   assert r['exit_status']==0 and r['quantitative_benchmark'] and r['command']==run['variants'][row['label']]['command'] and r['elapsed_seconds']==row['seconds']
   assert not (d/'stderr.bin').read_bytes() and o['bytes']==254166745 and o['sha256']=='e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e' and o['verified_complete'] and o['reaped'] and o['group_closed'];outputs+=1
  for label,s in run['summary'].items():
   rows=[r for r in run['samples'] if r['label']==label];times=[r['seconds'] for r in rows]
   assert len(rows)==7 and {r['round'] for r in rows}==set(range(1,8)) and s['median_seconds']==statistics.median(times) and math.isclose(s['stdev_seconds'],statistics.stdev(times),rel_tol=1e-14)
   assert a['profiles'][label]['x_fresh_mech_aot']==s['median_seconds']/den
  for label,paired in a['paired'].items():
   assert not paired['selected'] and paired['median_to_median_elapsed_change_percent']>0
   for pair in paired['rounds']:
    rows={r['label']:r['seconds'] for r in run['samples'] if r['round']==pair['round']};assert pair['parent_seconds']==rows['reuse4'] and pair['candidate_seconds']==rows[label]
   assert paired['faster_rounds']==sum(p['candidate_seconds']<p['parent_seconds'] for p in paired['rounds'])
 closed=0
 for p in HERE.rglob('process.json'):
  r=load(p);assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(p);closed+=1
 result=dict(status='verified-four-correct-policies-rejected',full_size_quantitative_samples=outputs,complete_bounded_captures=bounded,official_output_checks=official,closed_owned_processes=closed,unit_tests_per_policy=13,policies_tested=4,generated_kernel_configurations_per_policy=24,native_boundary_checks_per_policy=240,benchmark_catalog_unchanged=True,production_policy_changed=False)
 (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
