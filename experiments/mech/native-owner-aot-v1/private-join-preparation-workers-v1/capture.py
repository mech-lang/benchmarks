"""Collect fresh exact-boundary diagnostics; no primary timing observations."""
import fcntl,importlib.util
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA

def parser(name):
 spec=importlib.util.spec_from_file_location(name,STUDY/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.parse
worker_parse=parser('worker-parse');phase_parse=parser('phase-parse')
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['diagnostic_source'] and not before['status']
mech=read(STUDY/'build-candidate-v1/results.json')
rust_path=HERE/'worker-completion-v1/build-rust-v1/results.json';rust=read(rust_path)
assert mech['status']=='diagnostic-host-built' and mech['source_before']==mech['source_after']==before
assert rust['status']=='diagnostic-rust-built' and rust['binary_sha256']=='8edae977edd205240def5fa6e69cd7e00fd1c81c6de7a33bfcd934a21a1f9551'
assert rust['probe_sha256']==process.sha(STUDY/'worker_probe.rs')
assert process.sha(HERE/'worker-completion-v1/rust-instrumented.rs')==rust['source_sha256']
assert process.sha(HERE.parents[2]/'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs')=='47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
assert process.sha(HERE.parent/'native-hashmap-work-v1/.build/knucleotide-rust-7')=='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
parent_path=HERE/'credit-fragment-preparation-workers-v1/build-candidate-v1/results.json';parent=read(parent_path)
assert process.sha(parent_path)==plan['parent_build_receipt_sha256'] and parent['source_before']['commit']==plan['parent_diagnostic_source']
assert parent['guest_object_sha256']!=mech['guest_object_sha256'] and parent['probe_sha256']==mech['probe_sha256'] and parent['worker_probe_sha256']==mech['worker_probe_sha256']
assert mech['guest_object_sha256']==read(HERE/'private-join-buffer-timing-v1/results.json')['object_sha256']
assert parent['guest_object_sha256']==read(HERE/'credit-fragment-facts-timing-v1/results.json')['object_sha256']
subjects={'candidate':mech,'parent':parent,'rust':rust}
for build in subjects.values():assert process.sha(Path(build['binary']))==build['binary_sha256']
canonical=HERE.parents[2]/'data/benchmarks.json';inp=HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin';policy=HERE/'full-disjoint-state-v1/launch.json'
assert process.sha(canonical)==DATA_SHA and process.sha(inp)==INPUT_SHA and process.sha(policy)==POLICY_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
out=STUDY/'capture-v1';out.mkdir(exist_ok=False)
report=dict(status='qualifying-prefix',source_before=before,production_source=plan['production_source'],plan_sha256=process.sha(STUDY/'plan.json'),driver_sha256=process.sha(Path(__file__)),worker_parser_sha256=process.sha(STUDY/'worker-parse.py'),phase_parser_sha256=process.sha(STUDY/'phase-parse.py'),rust_build_receipt_sha256=process.sha(rust_path),primary_benchmark_samples=0,excluded_runs=0,subjects={k:dict(binary=v['binary'],binary_sha256=v['binary_sha256']) for k,v in subjects.items()},prefix=[],samples=[])
process.save(out/'results.json',report)
with Path(PLAN['common_mutex']).open('a+') as lock:
 assert Path(PLAN['common_mutex']).stat().st_ino==83858837
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for subject,build in subjects.items():
  prefix=HERE/'rust-span-diagnostic-v2/input.fasta';launch=HERE/'full-timing-v1/launch.json'
  assert process.sha(prefix)=='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
  assert process.sha(launch)=='3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
  folder=out/('prefix-'+subject);native=out/(folder.name+'.native.json')
  command=[build['binary']]+([] if subject=='rust' else [str(launch),str(native),'--'])
  r=process.execute(command,folder,mech['environment'],lock,stdin=prefix,deadline=30,quantitative=False)
  assert r['exit_status']==0 and process.sha(folder/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
  traces=worker_parse(folder/'stderr.bin',subject);process.save(folder/'workers.json',traces)
  if subject!='rust':
   n=read(native);assert n['native_hash_table_updates']==n['native_packed_map_updates']==6999961
   assert n['native_parallel_tasks']==7 and n['native_worker_credit_batches']>0 and n['policy']=='secured' and n['shutdown']=='completed'
   if subject=='candidate':assert n['native_fused_string_map_bytes']==1000000
   process.save(folder/'phases.json',phase_parse(folder/'stderr.bin'))
  report['prefix'].append(dict(subject=subject,process_sha256=process.sha(folder/'process.json'),output_verified=True));process.save(out/'results.json',report)
  print(subject,'prefix and all boundaries qualified',flush=True)
 report['status']='collecting-full';process.save(out/'results.json',report)
 for index,order in enumerate(plan['orders']):
  for position,subject in enumerate(order):
   build=subjects[subject];binary=Path(build['binary']);assert process.sha(binary)==build['binary_sha256']
   folder=out/f'{index:02d}-{position}-{subject}';native=out/(folder.name+'.native.json')
   command=[str(binary)]+([] if subject=='rust' else [str(policy),str(native),'--'])
   r=process.execute(command,folder,mech['environment'],lock,stdin=inp,deadline=30,quantitative=False)
   assert r['exit_status']==0 and process.sha(folder/'stdout.bin')==OUTPUT_SHA
   traces=worker_parse(folder/'stderr.bin',subject);process.save(folder/'workers.json',traces)
   phases=None
   if subject!='rust':
    check_native(native);n=read(native);assert n['native_worker_credit_batches']==854497
    if subject=='candidate':assert n['native_fused_string_map_bytes']==125000000
    phases=phase_parse(folder/'stderr.bin');assert phases['rows']['direct_rows']==4166671
    process.save(folder/'phases.json',phases)
   report['samples'].append(dict(subject=subject,order=index,position=position,folder=str(folder.relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),workers_sha256=process.sha(folder/'workers.json'),phases_sha256=process.sha(folder/'phases.json') if phases else None,native_sha256=process.sha(native) if subject!='rust' else None,output_sha256=OUTPUT_SHA))
   process.save(out/'results.json',report)
  print('diagnostic order',index+1,'of',len(plan['orders']),'verified',flush=True)
 assert source_state()==before and process.sha(canonical)==DATA_SHA
report.update(status='all-eighteen-full-boundaries-phases-outputs-and-updates-verified',source_after=source_state());process.save(out/'results.json',report)
