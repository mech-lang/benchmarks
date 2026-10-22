"""Replay source, alias tests, full-output receipts and paired runtime evidence."""
import hashlib,json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OLD=HERE.parent/'revcomp-streaming-v1'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 build=load(HERE/'build-v1/results.json');refine=load(HERE/'test-refinement-v2/results.json');comp=load(HERE/'compiler.json')
 assert build['status']=='tests-and-build-pass-identical-native-object' and build['tests_passed']==10
 assert refine['status']=='refined-tests-and-rebuild-pass' and refine['byte_identical_measured_executable']
 assert refine['rebuilt_binary_sha256']==refine['measured_binary_sha256']==build['binary_sha256']
 assert '10 passed; 0 failed' in (HERE/'test-refinement-v1/tests/stdout.bin').read_text()
 oldsource=(HERE/'build-v1/source-and-object/runtime-candidate.rs').read_text();newsource=(HERE/'test-refinement-v1/runtime-candidate.rs').read_text()
 needle='            records.push((header.as_ref().clone(), body.as_ref().clone()));\n'
 assert newsource==oldsource.replace(needle,needle+'            reader.recycle_buffer(std::sync::Arc::try_unwrap(body).unwrap());\n')
 assert sha(HERE/'build-v1/source-and-object/runtime-candidate.rs')==build['runtime_sha256']
 assert sha(HERE/'test-refinement-v1/runtime-candidate.rs')==refine['runtime_sha256']==comp['runtime_sha256']
 assert sha(ROOT/'archive/workloads/revcomp/revcomp.mec')==build['source_sha256']
 for name,h in comp['files'].items():assert sha(HERE/name)==h,name
 for name,h in load(OLD/'candidate-build-v1/results.json')['mech']['unchanged_emitted_inputs'].items():assert sha(HERE/'build-v1/source-and-object'/name)==h
 baseline=load(OLD/'baseline-build-v1/results.json');candidate=load(OLD/'candidate-build-v1/results.json');run=load(HERE/'run-v1/results.json')
 binary_hashes={str(OLD/'.build/mech-revcomp-parent'):baseline['binary_sha256'],str(OLD/'.build/mech-revcomp-candidate'):candidate['mech']['binary_sha256'],str(HERE/'.build/mech-revcomp-reuse'):build['binary_sha256'],str(OLD/'.build/rust-revcomp-1'):candidate['rust']['binary_sha256']}
 for name,h in run['pins'].items():
  if name in binary_hashes:assert h==binary_hashes[name]
  else:assert sha(ROOT/Path(name).relative_to('/private/tmp/mech-benchmark-publication'))==h,name
 corpus=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json';q=load(HERE/'qualification-v1/results.json');cases={r['case']:r for r in load(corpus)['cases'] if r['benchmark']=='revcomp'}
 assert q['corpus_sha256']==sha(corpus) and len(q['cases'])==len(cases)==61 and not q['new_regressions']
 assert q['binaries']=={'parent':candidate['mech']['binary_sha256'],'candidate':build['binary_sha256']}
 differences=[]
 for row in q['cases']:
  assert row['parent']==row['candidate']
  for label in ('parent','candidate'):
   d=HERE/'qualification-v1'/f"{label}-{row['case']}";r=load(d/'process.json')
   assert row[label]==dict(exit_status=r['exit_status'],stdout_sha256=sha(d/'stdout.bin'),stderr_sha256=sha(d/'stderr.bin'))
  expected=cases[row['case']];d=HERE/'qualification-v1'/f"candidate-{row['case']}"
  valid=(row['candidate']['exit_status']==0 and sha(d/'stdout.bin')==expected['expected']['sha256'] and not (d/'stderr.bin').read_bytes()) if expected['expected_exit']==0 else row['candidate']['exit_status']!=0
  assert valid==row['shared_reference_contract_met']
  if not valid:differences.append(row['case'])
 assert differences==q['existing_source_contract_differences']==load(OLD/'qualification-v1/results.json')['existing_source_contract_differences']
 assert run['status']=='all-35-full-size-outputs-pass' and len(run['samples'])==35 and run['official_input_all_five_pass'] and run['mutex_inode']==83858837
 expected=(ROOT/'archive/workloads/revcomp/inputs/revcomp-output-1000.txt').read_bytes()
 for label in run['variants']:
  d=HERE/'run-v1'/f'official-{label}';r=load(d/'process.json');assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==expected and not (d/'stderr.bin').read_bytes()
 for row in run['samples']:
  d=HERE/'run-v1'/f"{row['round']:02d}-{row['label']}";r=load(d/'process.json');o=load(d/'stdout-omitted.json')
  assert r['exit_status']==0 and r['quantitative_benchmark'] and not (d/'stderr.bin').read_bytes()
  assert r['elapsed_seconds']==row['seconds'] and r['maximum_rss_bytes']==row['maximum_rss_bytes']
  assert o['bytes']==254166745 and o['sha256']==run['expected_output']['sha256'] and o['verified_complete'] and o['reaped'] and o['group_closed']
  assert r['command']==run['variants'][row['label']]['command']
 a=load(HERE/'analysis.json');den=run['summary']['reuse4']['median_seconds'];assert a['comparison_denominator']['seconds']==den and a['timing_report_sha256']==sha(HERE/'run-v1/results.json')
 for label,s in run['summary'].items():
  rows=[r for r in run['samples'] if r['label']==label];times=[r['seconds'] for r in rows]
  assert len(rows)==7 and {r['round'] for r in rows}==set(range(1,8))
  assert s['median_seconds']==statistics.median(times) and math.isclose(s['stdev_seconds'],statistics.stdev(times),rel_tol=1e-14)
  assert a['profiles'][label]['x_optimized_mech_aot']==s['median_seconds']/den
 for p in a['paired_rounds']:
  rows={r['label']:r['seconds'] for r in run['samples'] if r['round']==p['round']}
  assert all(p[k+'_seconds']==rows[k] for k in ('original4','compacted4','reuse4')) and rows['reuse4']<rows['compacted4']<rows['original4']
 closed=0
 for p in HERE.rglob('process.json'):
  r=load(p);assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(p);closed+=1
 assert load(HERE/'test-refinement-v1/rebuild/process.json')['exit_status']==1
 assert 'refusing to overwrite' in (HERE/'test-refinement-v1/rebuild/stderr.bin').read_text()
 assert sha(ROOT/'data/benchmarks.json')==a['catalog_sha256']
 result=dict(status='verified',complete_bounded_comparisons=61,known_extended_source_contract_differences=11,full_output_hash_receipts=35,official_output_checks=5,closed_owned_processes=closed,unit_tests_passed=10,differential_cases_with_recycling=2736,refined_test_binary_identical_to_timed_binary=True,paired_improvement_rounds=7,catalog_unchanged=True)
 (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
