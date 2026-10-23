"""Verify map installers without source/compiler features; no timing samples."""
import sys,json,fcntl,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
ROOT=Path('/private/tmp/mech-native-hashmap-performance')
out=HERE/sys.argv[1];assert not out.exists()
env=json.loads((HERE.parent/'canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env['TMPDIR']=str(HERE/'.build/tmp');Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
command=['/Users/cim310/.cargo/bin/cargo','test','--manifest-path',str(ROOT/'Cargo.toml'),'--offline','--locked','-p','mech-engine','--no-default-features','--features','map_ops,native-link','--test','map_native_linkage','--','--test-threads=1','--nocapture']
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=process.execute(command,out,env,lock,deadline=3600)
 print(json.dumps({k:r[k] for k in ['exit_status','elapsed_seconds','group_closed','reaped','cleanup_errors']}),flush=True)
 sys.exit(r['exit_status'])
