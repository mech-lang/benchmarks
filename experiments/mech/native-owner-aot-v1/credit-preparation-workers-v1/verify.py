"""Verify the separate clock/counter campaign and every owned native receipt."""
import json,hashlib,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import source_state,check_native,OUTPUT_SHA,DATA_SHA
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['diagnostic_source'] and not before['status']
build=read(STUDY/'build-credit-v1/results.json');capture=read(STUDY/'capture-v1/results.json')
assert build['status']=='diagnostic-host-built' and build['source_before']==build['source_after']==before
assert capture['status']=='all-twelve-full-boundaries-phases-outputs-and-updates-verified' and capture['source_before']==capture['source_after']==before
assert capture['primary_benchmark_samples']==capture['excluded_runs']==0
assert capture['plan_sha256']==sha(STUDY/'plan.json') and capture['driver_sha256']==sha(STUDY/'capture.py')
assert capture['worker_parser_sha256']==sha(STUDY/'worker-parse.py') and capture['phase_parser_sha256']==sha(STUDY/'phase-parse.py')
assert build['driver_sha256']==sha(STUDY/'build.py') and build['spec_sha256']==sha(STUDY/'build-credit.json')
assert build['probe_sha256']==sha(STUDY/'phase_probe.rs') and build['worker_probe_sha256']==sha(STUDY/'worker_probe.rs')
root=Path('/private/tmp/mech-native-hashmap-performance')/'hosts/gpu/src/native_artifact'
assert sha(root/'program_preparation_probe.rs')==sha(STUDY/'phase_probe.rs') and sha(root/'program_worker_cpu_probe.rs')==sha(STUDY/'worker_probe.rs')
assert sha(Path(build['binary']))==build['binary_sha256']
primary=HERE/'.build/counting-worker-local-credit.project';diagnostic=HERE/'.build/counting-credit-preparation-workers.project'
for name in ['program.o','program.mecb','native-resources.json','native-descriptor.bin']:
 assert sha(primary/name)==sha(diagnostic/name)
pins=read(STUDY/'build-credit-v1/pin-update.json');assert pins['checks_removed']==0
assert {k for k in pins['before'] if pins['before'][k]!=pins['after'][k]}=={'src/main.rs','build.rs'}
paths=list((STUDY/'build-credit-v1').rglob('process.json'))
assert len(capture['prefix'])==2 and len(capture['samples'])==12
for r in capture['samples']:
 folder=STUDY/r['folder'];assert sha(folder/'process.json')==r['process_sha256'] and sha(folder/'stdout.bin')==OUTPUT_SHA
 assert sha(folder/'workers.json')==r['workers_sha256']
 if r['subject']=='credit':
  assert sha(folder/'phases.json')==r['phases_sha256']
  native=folder.with_name(folder.name+'.native.json');assert sha(native)==r['native_sha256'];check_native(native)
  assert read(native)['native_worker_credit_batches']==854497
 paths.append(folder/'process.json')
for r in capture['prefix']:
 folder=STUDY/'capture-v1'/('prefix-'+r['subject']);assert sha(folder/'process.json')==r['process_sha256']
 assert sha(folder/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa';paths.append(folder/'process.json')
for p in paths:
 r=read(p);assert r['exit_status']==0 and r['inherited_common_mutex'] and r['reaped'] and r['group_closed'] and not r['signals'] and not r['cleanup_errors'] and not r['quantitative_benchmark']
analysis=read(STUDY/'analysis.json');assert analysis['status']=='complete-boundaries-analyzed' and len(analysis['worker_samples'])==84
assert len(analysis['workers'])==14 and all(r['samples']==6 for r in analysis['workers'])
assert sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA and source_state()==before
result=dict(status='combined-phase-width-diagnostic-and-terminal-receipts-verified',source=before,production_source=plan['production_source'],guest_object_sha256=sha(primary/'program.o'),native_receipts=len(paths),full_processes=12,prefix_qualifications=2,worker_intervals=84,primary_benchmark_samples=0,analysis_sha256=sha(STUDY/'analysis.json'),verifier_sha256=sha(Path(__file__)))
(STUDY/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
