"""Audit retained diagnostic receipts and all source/data/binary pins."""
import json
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA
from parse import parse
plan=read(STUDY/'capture-plan.json');run=read(STUDY/'full-capture-v1/results.json')
assert run['status']=='all-eighteen-diagnostic-outputs-widths-and-updates-verified'
assert run['plan_sha256']==process.sha(STUDY/'capture-plan.json')
assert run['driver_sha256']==process.sha(STUDY/'capture.py')
assert run['source_before']==run['source_after']==plan['source']
assert plan['parser_sha256']==process.sha(STUDY/'parse.py')
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
assert process.sha(HERE/'full-disjoint-state-v1/launch.json')==POLICY_SHA
assert process.sha(HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin')==INPUT_SHA
for subject,pin in plan['subjects'].items():
 assert process.sha(Path(pin['binary']))==pin['binary_sha256']
 assert process.sha(STUDY/pin['build_receipt'])==pin['build_receipt_sha256']
 build=read(STUDY/pin['build_receipt']);assert build['probe_sha256']==process.sha(STUDY/'worker_probe.rs')
 assert build['source_before']==build['source_after'] and not build['source_before']['status']
 if subject!='rust':
  pins=read(STUDY/Path(pin['build_receipt']).parent/'pin-update.json')
  assert pins['checks_removed']==0
  assert {k for k in pins['before'] if pins['before'][k]!=pins['after'][k]}=={'src/main.rs','build.rs'}
for sample in run['samples']:
 assert process.sha(STUDY/sample['process'])==sample['process_sha256']
 assert process.sha(STUDY/sample['traces'])==sample['traces_sha256']
 folder=(STUDY/sample['process']).parent
 assert parse(folder/'stderr.bin',sample['subject'])==read(STUDY/sample['traces'])
 assert process.sha(folder/'stdout.bin')==OUTPUT_SHA
 if sample['subject']!='rust':
  p=folder.with_name(folder.name+'.native.json')
  assert process.sha(p)==sample['native_sha256'] and check_native(p)==sample['native']
assert len(run['samples'])==18
for subject in ['aligned','facts','rust']:assert sum(r['subject']==subject for r in run['samples'])==6
receipts=list(STUDY.rglob('process.json'));failures=[]
for p in receipts:
 d=read(p)
 assert d['inherited_common_mutex'] and not d['quantitative_benchmark']
 assert d['reaped'] and d['group_closed'] and not d['cleanup_errors'] and not d['signals']
 assert d['birth_identity']['pid']>0
 if d['exit_status']!=0:
  assert p.relative_to(STUDY).as_posix()=='build-aligned-v1/build/process.json' and d['exit_status']==101
  failures.append(str(p.relative_to(STUDY)))
assert len(failures)==1
result=dict(status='all-retained-diagnostics-and-one-preserved-build-failure-verified',terminal_process_receipts=len(receipts),successful_processes=len(receipts)-1,preserved_build_failures=failures,primary_benchmark_samples=0,driver_sha256=process.sha(Path(__file__)),analysis_sha256=process.sha(STUDY/'analysis.json'))
process.save(STUDY/'verification.json',result)
print(json.dumps(result))
