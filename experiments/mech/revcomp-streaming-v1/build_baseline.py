"""Build the unchanged Mech source against the unchanged compiler baseline."""
import fcntl,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('owned',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py');process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((ROOT/'experiments/janet/bounded-v1/plan-v1.json').read_bytes());WORKSPACE=Path('/private/tmp/mech-pidigits-performance')
def main():
 b=HERE/'.build';b.mkdir(exist_ok=True);out=HERE/'baseline-build-v1';out.mkdir(exist_ok=False)
 env={**PLAN['environment'],'PATH':'/Users/cim310/.cargo/bin:/usr/bin:/bin','HOME':'/Users/cim310','C_INCLUDE_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/include','LIBRARY_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/lib','RUSTFLAGS':'-L native=/opt/homebrew/Cellar/gmp/6.3.0/lib','CARGO_TARGET_DIR':str(WORKSPACE/'target')}
 source=ROOT/'archive/workloads/revcomp/revcomp.mec';compiler=WORKSPACE/'target/release/mech';binary=b/'mech-revcomp-parent'
 command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name','mech-revcomp-parent','-o',str(binary)]
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=process.execute(command,out/'build',env,lock,deadline=600)
  assert r['exit_status']==0,(out/'build/stderr.bin').read_text()[-3000:]
 report=dict(status='baseline-built',command=command,source_sha256=process.sha(source),compiler_sha256=process.sha(compiler),binary_sha256=process.sha(binary),runtime_source_sha256=process.sha(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs'),environment=env,compiler_commit='6de19875e2266f39c93712800c400672a44b98c9',benchmark_samples=0)
 process.save(out/'results.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
