"""Separate output-copy avoidance from larger write grouping after rejected budgets."""
from build import HERE,ROOT,PLAN,process,WORKSPACE
from pathlib import Path
import json,fcntl,shutil,subprocess

def main():
 out=HERE/'build-v2';out.mkdir(exist_ok=False);b=HERE/'.build';env=json.loads((HERE/'build-v1/results.json').read_bytes())['environment']
 runtime=WORKSPACE/'hosts/gpu/src/sequence/runtime.rs';original=runtime.read_text();budget='const NATIVE_WRAP_OUTPUT_BUDGET: usize = 2 * 1024 * 1024;';capacity='const STREAM_WRITE_BUFFER_CAPACITY: usize = 1024 * 1024;';assert original.count(budget)==original.count(capacity)==1
 plan={'quarter':dict(output_budget=262144,stream_capacity=131072),'one':dict(output_budget=1048576,stream_capacity=524288)}
 report=dict(status='running',base_runtime_commit='fca1ba1f7462a555eb56833ad32135408a140a72',plan=plan,reason='Larger native spans bypassed the outer buffer but regressed elapsed time. Preserve approximately baseline or smaller write grouping while removing the extra copy.',benchmark_samples=0,environment=env,variants={});process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   for label,policy in plan.items():
    runtime.write_text(original.replace(budget,f"const NATIVE_WRAP_OUTPUT_BUDGET: usize = {policy['output_budget']};").replace(capacity,f"const STREAM_WRITE_BUFFER_CAPACITY: usize = {policy['stream_capacity']};"))
    dest=out/label;dest.mkdir();shutil.copyfile(runtime,dest/'runtime.rs');(dest/'runtime.patch').write_bytes(subprocess.check_output(['git','-C',str(WORKSPACE),'diff','--','hosts/gpu/src/sequence/runtime.rs']))
    test=json.loads((HERE/'build-v1/results.json').read_bytes())['variants']['two-mib']['tests_command'];r=process.execute(test,dest/'tests',env,lock,deadline=600);assert r['exit_status']==0,(dest/'tests/stderr.bin').read_text()[-3000:]
    binary=b/('mech-revcomp-'+label);source=ROOT/'archive/workloads/revcomp/revcomp.mec';compiler=WORKSPACE/'target/release/mech'
    command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name',binary.name,'-o',str(binary)];r=process.execute(command,dest/'build',env,lock,deadline=600);assert r['exit_status']==0,(dest/'build/stderr.bin').read_text()[-3000:]
    project=b/(binary.name+'.project');snap=dest/'object';snap.mkdir();objects={}
    for name in ('source.mec','mech-sequence.o','constants.json','resource-requirements.json'):
     p=project/name;assert p.read_bytes()==(HERE/'build-v1/two-mib/object'/name).read_bytes();shutil.copyfile(p,snap/name);objects[name]=process.sha(p)
    report['variants'][label]=dict(command=command,tests_command=test,tests_passed=13,runtime_sha256=process.sha(runtime),source_sha256=process.sha(source),binary_sha256=process.sha(binary),policy=policy,unchanged_objects=objects);process.save(out/'results.json',report);print(label,'built and tested',flush=True)
   report['status']='both-balanced-budgets-build-and-tests-pass-native-object-identical';process.save(out/'results.json',report)
  finally:runtime.write_text(original)
if __name__=='__main__':main()
