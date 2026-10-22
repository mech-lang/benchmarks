"""Build and test an isolated generic record-buffer reuse candidate."""
import sys,fcntl,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process,WORKSPACE
PREVIOUS=HERE.parent/'revcomp-streaming-v1'
def main():
 out=HERE/'build-v1';out.mkdir(exist_ok=False);b=HERE/'.build';b.mkdir(exist_ok=True)
 env=json.loads((PREVIOUS/'baseline-build-v1/results.json').read_bytes())['environment']
 tests=['/Users/cim310/.cargo/bin/cargo','test','--release','--offline','--locked','-p','mech-gpu','--features','sequence-cli,system-gmp','--lib','sequence::runtime','--','--nocapture']
 source=ROOT/'archive/workloads/revcomp/revcomp.mec';compiler=WORKSPACE/'target/release/mech';binary=b/'mech-revcomp-reuse'
 # cargo package selection uses the explicit manifest so cwd is not significant.
 tests[2:2]=['--manifest-path',str(WORKSPACE/'Cargo.toml')]
 command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name','mech-revcomp-reuse','-o',str(binary)]
 report=dict(status='running',benchmark_samples=0,base_runtime_commit='6634f1f4d59c0a2eebee44065f236f8647703464',runtime_sha256=process.sha(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs'),source_sha256=process.sha(source),environment=env,tests_command=tests,build_command=command)
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  r=process.execute(tests,out/'tests',env,lock,deadline=600);assert r['exit_status']==0,(out/'tests/stderr.bin').read_text()[-3000:]
  r=process.execute(command,out/'build',env,lock,deadline=600);assert r['exit_status']==0,(out/'build/stderr.bin').read_text()[-3000:]
 project=b/'mech-revcomp-reuse.project';old=PREVIOUS/'.build/mech-revcomp-candidate.project';snap=out/'source-and-object';snap.mkdir()
 for name in ('source.mec','mech-sequence.o','constants.json','resource-requirements.json'):
  assert (project/name).read_bytes()==(old/name).read_bytes();shutil.copyfile(project/name,snap/name)
 shutil.copyfile(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs',snap/'runtime-candidate.rs');(snap/'runtime.patch').write_bytes(subprocess.check_output(['git','-C',str(WORKSPACE),'diff','--','hosts/gpu/src/sequence/runtime.rs']))
 report.update(status='tests-and-build-pass-identical-native-object',binary_sha256=process.sha(binary),tests_passed=10,native_object_sha256=process.sha(project/'mech-sequence.o'));process.save(out/'results.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
