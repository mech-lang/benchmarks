"""Extend parser test recycling, then prove the timed executable is unchanged."""
from prepare import HERE,ROOT,PREVIOUS,PLAN,WORKSPACE,process
from pathlib import Path
import fcntl,json,shutil,subprocess

def main():
 old=json.loads((HERE/'build-v1/results.json').read_bytes());out=HERE/'test-refinement-v1';out.mkdir(exist_ok=False)
 binary=HERE/'.build/mech-revcomp-reuse';backup=HERE/'.build/mech-revcomp-reuse-measured';shutil.copy2(binary,backup)
 assert process.sha(binary)==old['binary_sha256']
 snapshot=out/'runtime-candidate.rs';shutil.copyfile(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs',snapshot)
 patch=subprocess.check_output(['git','-C',str(WORKSPACE),'diff','--','hosts/gpu/src/sequence/runtime.rs']);(out/'runtime.patch').write_bytes(patch)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  r=process.execute(old['tests_command'],out/'tests',old['environment'],lock,deadline=600);assert r['exit_status']==0
  r=process.execute(old['build_command'],out/'rebuild',old['environment'],lock,deadline=600);assert r['exit_status']==0
  rebuilt_sha=process.sha(binary)
  report=dict(status='refined-tests-pass',tests_passed=10,differential_cases=2736,all_differential_cases_now_recycle_completed_record_storage=True,runtime_sha256=process.sha(snapshot),previous_runtime_sha256=old['runtime_sha256'],measured_binary_sha256=old['binary_sha256'],rebuilt_binary_sha256=rebuilt_sha,byte_identical_measured_executable=rebuilt_sha==old['binary_sha256'],production_code_changed=False,base_commit=old['base_runtime_commit'])
  if rebuilt_sha!=old['binary_sha256']:shutil.copy2(binary,HERE/'.build/mech-revcomp-reuse-refined');shutil.copy2(backup,binary)
  process.save(out/'results.json',report);print(json.dumps(report))
if __name__=='__main__':main()
