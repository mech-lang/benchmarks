"""Complete-process timing attempt on the standard nucleotide workload."""
import fcntl,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
out=HERE/'full-timing-v1';out.mkdir(exist_ok=False)
q=json.loads((HERE/'candidate-timing-v1/results.json').read_bytes());assert q['status']=='measured-identical-input-and-output-verified'
binary=HERE/'.build/counting-candidate';assert process.sha(binary)==q['candidate_sha256']
inp=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin';assert process.sha(inp)=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
policy=out/'launch.json';policy.write_bytes((HERE.parent/'native-hashmap-batch-v1/qualification-v1/launch.json').read_bytes())
env=json.loads((HERE/'compiler-v2/results.json').read_bytes())['environment']
report=dict(status='running',source_commit=q['source_commit'],binary_sha256=process.sha(binary),input_sha256=process.sha(inp),input_bytes=inp.stat().st_size,selected_bases=125000000,launch_sha256=process.sha(policy),scope='standard full input; fresh secured startup through exit; build and validation excluded',samples=[])
process.save(out/'results.json',report)
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  r=process.execute([str(binary),str(policy),str(out/'native.report.json'),'--'],out/'subject',env,lock,stdin=inp,deadline=180,quantitative=True)
  assert r['exit_status']==0,(out/'subject/stderr.bin').read_text()[-6000:]
  assert process.sha(out/'subject/stdout.bin')=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
  n=json.loads((out/'native.report.json').read_bytes());assert n['native_aot'] and not n['jit'] and not n['resident_body_evaluation'] and n['shutdown']=='completed'
  report.update(status='full-input-output-verified',samples=[dict(seconds=r['elapsed_seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],x_mech_aot=1.0)],denominator='This full-input candidate Mech AOT execution')
 except BaseException as error:
  report.update(status='not-a-successful-timing',failure=repr(error))
  if (out/'subject/process.json').exists(): report['process']=json.loads((out/'subject/process.json').read_bytes())
 finally:
  process.save(out/'results.json',report);print(json.dumps(report),flush=True)
