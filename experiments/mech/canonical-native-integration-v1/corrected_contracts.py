"""Serial final-head contract checks for the two inherited PR 909 CI failures."""
import sys,json,fcntl,subprocess,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process,WORKSPACE

def main():
 initial=json.loads((HERE/'validation-v2/results.json').read_bytes())
 assert initial['status']=='integration-tests-and-compiler-build-passed'
 out=HERE/'corrected-contracts-v1';out.mkdir(exist_ok=False)
 commit=subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()
 assert commit=='bbd66acb9b3beacdc95356084df259ca172c8b98'
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 changes=subprocess.check_output(['git','-C',str(WORKSPACE),'diff','--name-only','1e9e6aac12170dbfcc9686f95909a11e0804a8bb',commit],text=True).splitlines()
 assert sorted(changes)==sorted(['hosts/gpu/src/sequence/runtime.rs','hosts/gpu/tests/support/canonical_hosted_benchmark.rs'])
 env=initial['environment'];cargo='/Users/cim310/.cargo/bin/cargo';common=[cargo,'test','--manifest-path',str(WORKSPACE/'Cargo.toml'),'--offline','--locked']
 report=dict(status='running',source_commit=commit,upstream_commit='1e9e6aac12170dbfcc9686f95909a11e0804a8bb',remaining_changes=changes,environment=env,benchmark_samples=0,steps=[])
 process.save(out/'results.json',report)
 commands=[('match-lowering',common+['-p','mech-stdlib','--no-default-features','--features','full_compiler,native-artifact','--test','native_artifact_match_lowering','--test','native_artifact_iteration_lowering','--','--test-threads=1','--nocapture']),('native-image-wire',common+['-p','mech-stdlib','-p','mech-engine','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host','--lib','native_artifact::program_image','--','--test-threads=1','--nocapture']),('native-window-codegen',common+['-p','mech-stdlib','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host','--lib','native_artifact::program_compiler::window_codegen::tests','--','--test-threads=1','--nocapture']),('same-binary-policy-contracts',common+['-p','mech-stdlib','-p','mech-gpu','--no-default-features','--features','mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-benchmark-policy','--test','canonical_hosted_artifact','--','--test-threads=1','--nocapture'])]
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for label,command in commands:
   print('Starting',label,flush=True)
   r=process.execute(command,out/label,env,lock,deadline=2400)
   report['steps'].append(dict(label=label,exit_status=r['exit_status']));process.save(out/'results.json',report)
   assert r['exit_status']==0,(out/label/'stderr.bin').read_text()[-6000:]
   stdout=(out/label/'stdout.bin').read_text();counts=[int(n) for n in re.findall(r'test result: ok\. (\d+) passed',stdout)];assert sum(counts)>0,stdout[-5000:]
   report['steps'][-1]['tests_passed']=sum(counts);process.save(out/'results.json',report)
   print('Passed',label,flush=True)
  report['status']='final-head-native-contracts-passed';process.save(out/'results.json',report)
if __name__=='__main__':main()
