"""Reuse qualified executables with finite limits sized for the standard input."""
import sys,json,fcntl,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
sys.path.insert(0,str(HERE.parent/'canonical-native-integration-v1'))
from qualify import oracle
WORKSPACE=Path('/private/tmp/mech-native-hashmap-performance')
def closed(path,expected=0):
 r=json.loads(path.read_bytes());assert r['exit_status']==expected and r['reaped'] and r['group_closed'] and not r['cleanup_errors'];return r

def main():
 seed=HERE/'qualification-v2';prior=json.loads((seed/'results.json').read_bytes())
 assert prior['status']=='failed' and 'OutputElements' in prior['failure']
 closed(seed/'full-source/process.json',1)
 prepared=json.loads((HERE/'compiler-v1/results.json').read_bytes());env=prepared['environment']
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==prepared['source_commit']
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 standard='--standard-policy' in sys.argv
 out=HERE/('qualification-v4' if standard else 'qualification-v3');out.mkdir(exist_ok=False)
 variants=prior['variants'];assert set(variants)=={'source','decoded'}
 assert variants['source']['binary_sha256']==variants['decoded']['binary_sha256']
 for variant in variants:
  binary=HERE/'.build'/('knucleotide-'+variant);assert process.sha(binary)==variants[variant]['binary_sha256']
  for i in range(6):closed(seed/f'{variant}-case-{i}/process.json')
  assert closed(seed/f'{variant}-denied/process.json',1)
 policy=json.loads(json.dumps(prior['policy']))
 # Full input has 4,166,671 physical lines. Semantic output allowances cover
 # original text/lines values even when emitted row cursors avoid allocation.
 # Physical ownership still has the unchanged 1GiB shared memory limit.
 policy['library'].update(output_elements=8000000,output_bytes=4294967296,retained_nodes=32000000)
 if standard:
  previous=HERE/'qualification-v3'
  assert 'TemporaryBytes' in json.loads((previous/'results.json').read_bytes())['failure']
  closed(previous/'full-source/process.json',1)
  origin=WORKSPACE/'docs/validation/canonical-knucleotide-owned-string-footprint-v1.json'
  historical=json.loads(origin.read_bytes())
  assert historical['program_source_sha256']==prior['source_sha256']
  policy=historical['finite_launch_policy']
  assert policy['grants']==prior['policy']['grants'] and policy['max_ports']==prior['policy']['max_ports']
  policy['work']=1<<56
  policy['library'].update(compute_work=1<<54,comparison_work=1<<50)
  process.save(out/'policy-origin.json',dict(source=str(origin),sha256=process.sha(origin),field='finite_launch_policy',scope='Reuse recorded full-input resource caps only; no timing or algorithm qualification is inherited. Increase only finite compute/comparison work bounds for the restored table work.'))
 launch=out/'launch.json';process.save(launch,policy)
 denied=out/'denied.json';process.save(denied,{**policy,'grants':policy['grants'][1:]})
 full=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin';assert process.sha(full)==prior['input_sha256']
 report=dict(status='running',source_commit=prior['source_commit'],preparation_reused_from=str(seed),source_sha256=prior['source_sha256'],input_sha256=prior['input_sha256'],input_bytes=full.stat().st_size,selected_bases=125000000,required_table_regions=7,required_table_updates=874999961,hash_table_work_preserved=False,benchmark_admission_allowed=False,policy=policy,policy_sha256=process.sha(launch),variants=variants,samples=[],policy_correction='Reuse recorded standard full-input finite resource caps, including 3GiB shared physical memory and 1GiB temporary allowance; unchanged binary and authority. Larger finite work bounds cover the restored hash-table work.' if standard else 'Raise finite semantic output limits for 4,166,671 physical input lines; unchanged binary, authority and physical-memory limit.')
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def execute(command,directory,stdin=None,extra=None,deadline=120):
   return process.execute(command,directory,{**env,**(extra or {})},lock,stdin=stdin,deadline=deadline,quantitative=False)
  try:
   for label,command in [('hardware',['/usr/sbin/sysctl','machdep.cpu.brand_string','hw.model','hw.memsize','hw.ncpu']),('os',['/usr/bin/sw_vers']),('power-source',['/usr/bin/pmset','-g','batt']),('power-settings',['/usr/bin/pmset','-g','custom'])]:
    r=execute(command,out/label,deadline=30);assert r['exit_status']==0
   for variant in ['source','decoded']:
    binary=HERE/'.build'/('knucleotide-'+variant)
    for i in range(6):
     inp=seed/f'input-{i}.fasta';dest=out/f'{variant}-case-{i}';receipt=out/f'{variant}-case-{i}.report.json'
     r=execute([str(binary),str(launch),str(receipt),'--'],dest,inp)
     assert r['exit_status']==0,(dest/'stderr.bin').read_text()[-4000:]
     assert (dest/'stdout.bin').read_bytes()==oracle(inp.read_bytes())
     native=json.loads(receipt.read_bytes())
     assert native['native_aot'] and not native['jit'] and not native['source_parser'] and not native['resident_body_evaluation'] and native['shutdown']=='completed'
    dest=out/f'{variant}-denied';receipt=out/f'{variant}-denied.report.json'
    r=execute([str(binary),str(denied),str(receipt),'--'],dest,seed/'input-0.fasta',extra={'MECH_NATIVE_SECURITY':'trusted'})
    assert r['exit_status']!=0 and not (dest/'stdout.bin').read_bytes() and not receipt.exists()
   for variant in ['source','decoded']:
    binary=HERE/'.build'/('knucleotide-'+variant);label='full-'+variant;dest=out/label;receipt=out/(label+'.report.json')
    print('Full correctness and table work:',variant,flush=True)
    r=execute([str(binary),str(launch),str(receipt),'--'],dest,full,deadline=900)
    assert r['exit_status']==0,(dest/'stderr.bin').read_text()[-4000:]
    assert process.sha(dest/'stdout.bin')=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    native=json.loads(receipt.read_bytes())
    assert native['route']=='canonical-artifact-program-object-secured-cli' and native['native_aot'] and not native['jit'] and not native['source_parser'] and not native['resident_body_evaluation'] and native['shutdown']=='completed'
    assert native['native_hash_table_regions']==7 and native['native_hash_table_updates']==874999961,native
    report.setdefault('full_checks',{})[variant]=dict(stdout_sha256=process.sha(dest/'stdout.bin'),hash_table_regions=native['native_hash_table_regions'],hash_table_updates=native['native_hash_table_updates'],security_report=str(receipt),process=str(dest/'process.json'))
    process.save(out/'results.json',report);print('Passed',variant,flush=True)
   for variant in variants:assert process.sha(HERE/'.build'/('knucleotide-'+variant))==variants[variant]['binary_sha256']
   report.update(status='public-source-decoded-security-full-output-and-table-work-passed',hash_table_work_preserved=True,benchmark_admission_reason='Correctness and required work passed. A measured cohort and admission remain separate.')
  except BaseException as error:
   report.update(status='failed',failure=repr(error));raise
  finally:
   assert not report['samples'];process.save(out/'results.json',report)
if __name__=='__main__':main()
