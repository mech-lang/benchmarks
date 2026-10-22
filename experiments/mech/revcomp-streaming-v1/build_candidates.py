"""Build changed general Mech runtime and unchanged published Rust source serially."""
from build_baseline import HERE,ROOT,WORKSPACE,PLAN,process
import fcntl,json,shutil
from pathlib import Path

def main():
 baseline=json.loads((HERE/'baseline-build-v1/results.json').read_bytes());env=baseline['environment'];out=HERE/'candidate-build-v1';out.mkdir(exist_ok=False);b=HERE/'.build'
 compiler=WORKSPACE/'target/release/mech';source=ROOT/'archive/workloads/revcomp/revcomp.mec';binary=b/'mech-revcomp-candidate'
 command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name','mech-revcomp-candidate','-o',str(binary)]
 assert process.sha(compiler)==baseline['compiler_sha256'] and process.sha(source)==baseline['source_sha256']
 report=dict(status='running',environment=env,compiler_sha256=process.sha(compiler),source_sha256=process.sha(source),runtime_source_sha256=process.sha(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs'),benchmark_samples=0)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  r=process.execute(command,out/'mech-build',env,lock,deadline=600);assert r['exit_status']==0,(out/'mech-build/stderr.bin').read_text()[-3000:]
  old=b/'mech-revcomp-parent.project';new=b/'mech-revcomp-candidate.project';objects={}
  for name in ('source.mec','mech-sequence.o','constants.json','resource-requirements.json'):
   assert (old/name).read_bytes()==(new/name).read_bytes(),name
   objects[name]=process.sha(new/name)
  report['mech']=dict(command=command,binary_sha256=process.sha(binary),unchanged_emitted_inputs=objects)
  package=b/'rust-1';(package/'src').mkdir(parents=True,exist_ok=False);original=ROOT/'archive/workloads/revcomp/upstream/revcomp-rust-1.rs';shutil.copyfile(original,package/'src/main.rs')
  (package/'Cargo.toml').write_text('[package]\nname="revcomp-rust-published"\nversion="0.0.0"\nedition="2021"\n[dependencies]\nmemchr="=2.8.3"\nrayon="=1.12.0"\n[workspace]\n')
  rust_env={**env,'RUSTFLAGS':'-C target-cpu=native'};cmd=['/Users/cim310/.cargo/bin/cargo','build','--release','--offline','--manifest-path',str(package/'Cargo.toml')]
  r=process.execute(cmd,out/'rust-build',rust_env,lock,deadline=600);assert r['exit_status']==0,(out/'rust-build/stderr.bin').read_text()[-3000:]
  rust=WORKSPACE/'target/release/revcomp-rust-published';assert process.sha(original)==process.sha(package/'src/main.rs');shutil.copy2(rust,b/'rust-revcomp-1')
  report['rust']=dict(command=cmd,binary_sha256=process.sha(b/'rust-revcomp-1'),application_source_sha256=process.sha(original),application_bytes_unchanged=True)
 report['status']='both-binaries-built-Mech-native-object-identical';process.save(out/'results.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
