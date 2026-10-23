import sys,json,fcntl,os,hashlib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
ROOT=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else Path('/private/tmp/mech-native-hashmap-performance')

def source_state():
 def git(*args):
  return subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),*args])
 status=git('status','--porcelain=v1','--untracked-files=all').decode()
 return dict(commit=git('rev-parse','HEAD').decode().strip(),
             tree=git('rev-parse','HEAD^{tree}').decode().strip(),
             clean=not status,status_porcelain_v1=status,
             tracked_diff_sha256=hashlib.sha256(git('diff','--binary','HEAD','--')).hexdigest())

out=HERE/sys.argv[1];assert not out.exists()
env=json.loads((HERE.parent/'canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env['TMPDIR']=str(HERE/'.build/tmp');Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
command=['/Users/cim310/.cargo/bin/cargo','test','--manifest-path',str(ROOT/'Cargo.toml'),'--offline','--locked','-p','mech-stdlib','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host','--lib',sys.argv[2],'--','--test-threads=1','--nocapture']
if len(sys.argv)>4:
 assert sys.argv[4]=='--no-run'
 command.insert(command.index('--'),'--no-run')
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=source_state()
 validator_sha256=process.sha(Path(__file__))
 try:
  r=process.execute(command,out,env,lock,deadline=3600)
 finally:
  after=source_state()
  if out.exists():
   # The process receipt remains byte-for-byte owned by its supervisor. This
   # sidecar records source snapshots, including unsuccessful test runs.
   process.save(out/'source-provenance.json',dict(
    schema='mech.native-validation-source.v1',workspace=str(ROOT),
    validator_sha256=validator_sha256,
    environment_sha256=hashlib.sha256(json.dumps(env,sort_keys=True).encode()).hexdigest(),
    before=before,after=after,source_unchanged=before==after,
    clean_revision_qualified=before==after and before['clean'],
    scope='Git state sampled before and after serial validation; dirty source is recorded but not qualified as an immutable revision. Untracked file contents are not hashed.'))
 assert before==after,'Source changed during validation; see source-provenance.json'
 print(json.dumps({k:r[k] for k in ['exit_status','elapsed_seconds','group_closed','reaped','cleanup_errors']}),flush=True)
 sys.exit(r['exit_status'])
