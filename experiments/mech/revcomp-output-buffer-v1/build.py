"""Test and build two general native wrapping output budgets, serially."""
import sys,json,fcntl,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process,WORKSPACE

def main():
 out=HERE/'build-v1';out.mkdir(exist_ok=False);b=HERE/'.build';b.mkdir(exist_ok=True)
 env=json.loads((HERE.parent/'revcomp-buffer-reuse-v1/build-v1/results.json').read_bytes())['environment']
 runtime=WORKSPACE/'hosts/gpu/src/sequence/runtime.rs';original=runtime.read_text();two='const NATIVE_WRAP_OUTPUT_BUDGET: usize = 2 * 1024 * 1024;';assert original.count(two)==1
 compiler=WORKSPACE/'target/release/mech';source=ROOT/'archive/workloads/revcomp/revcomp.mec'
 report=dict(status='running',base_runtime_commit='fca1ba1f7462a555eb56833ad32135408a140a72',compiler_cli_sha256=process.sha(compiler),source_sha256=process.sha(source),benchmark_samples=0,environment=env,variants={})
 def save():process.save(out/'results.json',report)
 save()
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   for label,mib in [('two-mib',2),('four-mib',4)]:
    runtime.write_text(original.replace(two,f'const NATIVE_WRAP_OUTPUT_BUDGET: usize = {mib} * 1024 * 1024;'))
    dest=out/label;dest.mkdir();shutil.copyfile(runtime,dest/'runtime.rs');(dest/'runtime.patch').write_bytes(subprocess.check_output(['git','-C',str(WORKSPACE),'diff','--','hosts/gpu/src/sequence/runtime.rs']))
    cmd=['/Users/cim310/.cargo/bin/cargo','test','--manifest-path',str(WORKSPACE/'Cargo.toml'),'--release','--offline','--locked','-p','mech-gpu','--features','sequence-cli,system-gmp','--lib','sequence::runtime','--','--nocapture']
    r=process.execute(cmd,dest/'tests',env,lock,deadline=600);assert r['exit_status']==0,(dest/'tests/stderr.bin').read_text()[-3000:]
    binary=b/('mech-revcomp-'+label);command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name','mech-revcomp-'+label,'-o',str(binary)]
    r=process.execute(command,dest/'build',env,lock,deadline=600);assert r['exit_status']==0,(dest/'build/stderr.bin').read_text()[-3000:]
    project=b/(binary.name+'.project');objects={};snap=dest/'object';snap.mkdir()
    for name in ('source.mec','mech-sequence.o','constants.json','resource-requirements.json'):
     p=project/name;assert p.read_bytes()==(HERE.parent/'revcomp-buffer-reuse-v1/build-v1/source-and-object'/name).read_bytes(),name;shutil.copyfile(p,snap/name);objects[name]=process.sha(p)
    report['variants'][label]=dict(command=command,tests_command=cmd,tests_passed=13,source_sha256=process.sha(source),runtime_sha256=process.sha(runtime),binary_sha256=process.sha(binary),native_output_budget_bytes=mib*1024*1024,unchanged_objects=objects);save();print(label,'built and tested',flush=True)
   report['status']='both-budgets-build-and-tests-pass-native-object-identical';save()
  finally:runtime.write_text(original)
if __name__=='__main__':main()
