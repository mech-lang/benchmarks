"""Build the public CLI separately from timed generated applications."""
import sys,json,fcntl,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
ROOT=Path('/private/tmp/mech-native-hashmap-performance')
out=HERE/sys.argv[1];assert not out.exists()
assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'])
head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
env=json.loads((HERE.parent/'canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env['TMPDIR']=str(HERE/'.build/tmp');Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
command=['/Users/cim310/.cargo/bin/cargo','build','--manifest-path',str(ROOT/'Cargo.toml'),'--offline','--locked','--bin','mech','--no-default-features','--features','cli_core,full_compiler,cranelift_build,system_gmp,mech-build/standard-hosts']
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=process.execute(command,out,env,lock,deadline=3600)
 report=dict(source_commit=head,environment=env,process_receipt=str(out/'process.json'),exit_status=r['exit_status'],benchmark_samples=0,tool_profile='dev: opt-level 0, debug 0, symbols stripped',generated_application_profile='release Rust libraries and shell; Cranelift opt_level=speed')
 if r['exit_status']==0:
  binary=HERE/'.build/mech-canonical';shutil.copy2(Path(env['CARGO_TARGET_DIR'])/'debug/mech',binary)
  report['compiler_sha256']=process.sha(binary);report['status']='compiler-built'
 else:report['status']='failed'
 assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==head
 assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'])
 process.save(out/'results.json',report)
 print(json.dumps(report),flush=True);sys.exit(r['exit_status'])
