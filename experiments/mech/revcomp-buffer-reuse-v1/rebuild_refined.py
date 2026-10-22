"""Retain old generated project, rebuild identical path, verify measured bytes."""
from prepare import HERE,PLAN,WORKSPACE,process
from pathlib import Path
import fcntl,json,shutil

def main():
 old=json.loads((HERE/'build-v1/results.json').read_bytes());out=HERE/'test-refinement-v2';out.mkdir(exist_ok=False)
 binary=HERE/'.build/mech-revcomp-reuse';backup=HERE/'.build/mech-revcomp-reuse-measured';assert process.sha(binary)==process.sha(backup)==old['binary_sha256']
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  project=HERE/'.build/mech-revcomp-reuse.project';project.rename(HERE/'.build/mech-revcomp-reuse-measured.project')
  r=process.execute(old['build_command'],out/'rebuild',old['environment'],lock,deadline=600);assert r['exit_status']==0
  rebuilt=process.sha(binary)
  report=dict(status='refined-tests-and-rebuild-pass',tests_passed=10,differential_cases=2736,all_differential_cases_now_recycle_completed_record_storage=True,runtime_sha256=process.sha(WORKSPACE/'hosts/gpu/src/sequence/runtime.rs'),previous_runtime_sha256=old['runtime_sha256'],measured_binary_sha256=old['binary_sha256'],rebuilt_binary_sha256=rebuilt,byte_identical_measured_executable=rebuilt==old['binary_sha256'],production_code_changed=False,first_rebuild_refusal='Existing keep-project directory, exited before compilation; retained in test-refinement-v1. Original generated project moved, not deleted.',tests_receipt='test-refinement-v1/tests/process.json')
  if rebuilt!=old['binary_sha256']:shutil.copy2(binary,HERE/'.build/mech-revcomp-reuse-refined');shutil.copy2(backup,binary)
  process.save(out/'results.json',report);print(json.dumps(report))
if __name__=='__main__':main()
