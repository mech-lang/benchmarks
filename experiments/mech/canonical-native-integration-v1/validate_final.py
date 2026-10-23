"""Prepare the exact integrated head; keep compiler tools separate from timed applications."""
import sys,json,fcntl,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process,WORKSPACE
HEAD='bbd66acb9b3beacdc95356084df259ca172c8b98'
UPSTREAM='1e9e6aac12170dbfcc9686f95909a11e0804a8bb'
def clean():
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==HEAD
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
def main():
 clean();old=json.loads((HERE/'validation-v1/record-runtime/process.json').read_bytes());assert old['reaped'] and old['group_closed'] and not old['cleanup_errors'] and old['exit_status']==-15
 out=HERE/'validation-v2';out.mkdir(exist_ok=False);b=HERE/'.build';b.mkdir(exist_ok=True)
 env={**PLAN['environment'],'PATH':'/Users/cim310/.cargo/bin:/usr/bin:/bin','HOME':'/Users/cim310','C_INCLUDE_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/include','LIBRARY_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/lib','RUSTFLAGS':'-L native=/opt/homebrew/Cellar/gmp/6.3.0/lib','CARGO_TARGET_DIR':str(WORKSPACE/'target'),'CARGO_BUILD_JOBS':'1','CARGO_PROFILE_DEV_DEBUG':'0','CARGO_PROFILE_DEV_STRIP':'symbols','CARGO_PROFILE_TEST_DEBUG':'0'}
 cargo='/Users/cim310/.cargo/bin/cargo';manifest=str(WORKSPACE/'Cargo.toml');legacy=WORKSPACE/'target/release/mech';legacy_sha='5445d4b291972badef19ac655728675ee972618fbe47c899ecfd5c514a2582fa';assert process.sha(legacy)==legacy_sha
 report=dict(status='running',integration_commit=HEAD,pr909_commit=UPSTREAM,environment=env,benchmark_samples=0,steps=[],tool_profile='dev: opt-level 0, debug 0, symbols stripped',canonical_test_profile='test: opt-level 0, debug 0, symbols stripped',record_test_profile='release: reuse the completed full-math preparation cache',measured_application_profile='release Rust shell/libraries and Cranelift opt_level=speed; tool build excluded')
 process.save(out/'results.json',report)
 commands=[('record-runtime',[cargo,'test','--manifest-path',manifest,'--release','--offline','--locked','-p','mech-gpu','--features','sequence-cli,system-gmp','--lib','sequence::runtime','--','--test-threads=1','--nocapture']),('canonical-host',[cargo,'test','--manifest-path',manifest,'--offline','--locked','-p','mech-stdlib','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host','--test','canonical_hosted_artifact','--','--test-threads=1','--nocapture']),('compiler',[cargo,'build','--manifest-path',manifest,'--offline','--locked','--bin','mech','--no-default-features','--features','cli_core,full_compiler,cranelift_build,system_gmp,mech-build/standard-hosts'])]
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   for label,command in commands:
    clean();print('Starting',label,flush=True)
    r=process.execute(command,out/label,env,lock,deadline=3600)
    report['steps'].append(dict(label=label,exit_status=r['exit_status']));process.save(out/'results.json',report)
    assert r['exit_status']==0,(out/label/'stderr.bin').read_text()[-6000:]
    clean();print('Passed',label,flush=True)
   shutil.copy2(WORKSPACE/'target/debug/mech',b/'mech-canonical');report['compiler_sha256']=process.sha(b/'mech-canonical');report['status']='integration-tests-and-compiler-build-passed'
  except BaseException as error:
   report['status']='failed';report['failure']=repr(error);raise
  finally:
   report['legacy_emitter_unchanged_sha256']=process.sha(legacy);assert report['legacy_emitter_unchanged_sha256']==legacy_sha
   process.save(out/'results.json',report)
if __name__=='__main__':main()
