"""Serial qualification of the PR 909 integration; no benchmark timing claims."""
import sys, json, fcntl, shutil, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN, process, WORKSPACE

def main():
 out=HERE/'validation-v1';out.mkdir(exist_ok=False)
 build=HERE/'.build';build.mkdir(exist_ok=True)
 env={**PLAN['environment'],'PATH':'/Users/cim310/.cargo/bin:/usr/bin:/bin','HOME':'/Users/cim310','C_INCLUDE_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/include','LIBRARY_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/lib','RUSTFLAGS':'-L native=/opt/homebrew/Cellar/gmp/6.3.0/lib','CARGO_TARGET_DIR':str(WORKSPACE/'target'),'CARGO_BUILD_JOBS':'1'}
 cargo='/Users/cim310/.cargo/bin/cargo'
 manifest=str(WORKSPACE/'Cargo.toml')
 report=dict(status='running',integration_commit=subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip(),pr909_commit='c5b0b3a35b7537358361529aa5a6148464ec415d',environment=env,benchmark_samples=0,steps=[])
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  compiler=WORKSPACE/'target/release/mech';backup=build/'legacy-emitter-6de19875e'
  assert process.sha(compiler)=='5445d4b291972badef19ac655728675ee972618fbe47c899ecfd5c514a2582fa'
  shutil.copy2(compiler,backup)
  try:
   commands=[('record-runtime',[cargo,'test','--manifest-path',manifest,'--release','--offline','--locked','-p','mech-gpu','--features','sequence-cli,system-gmp','--lib','sequence::runtime','--','--test-threads=1','--nocapture']),('canonical-host',[cargo,'test','--manifest-path',manifest,'--release','--offline','--locked','-p','mech-stdlib','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host','--test','canonical_hosted_artifact','--','--test-threads=1','--nocapture']),('compiler',[cargo,'build','--manifest-path',manifest,'--release','--offline','--locked','--bin','mech','--no-default-features','--features','cli_core,full_compiler,cranelift_build,system_gmp,mech-build/standard-hosts'])]
   for label,command in commands:
    print('Starting',label,flush=True)
    r=process.execute(command,out/label,env,lock,deadline=2400)
    report['steps'].append(dict(label=label,exit_status=r['exit_status']));process.save(out/'results.json',report)
    assert r['exit_status']==0,(out/label/'stderr.bin').read_text()[-6000:]
    print('Passed',label,flush=True)
   shutil.copy2(compiler,build/'mech-canonical')
   report['compiler_sha256']=process.sha(build/'mech-canonical')
   report['status']='integration-tests-and-compiler-build-passed'
  finally:
   shutil.copy2(backup,compiler)
   report['legacy_emitter_restored_sha256']=process.sha(compiler)
   process.save(out/'results.json',report)
if __name__=='__main__':main()
