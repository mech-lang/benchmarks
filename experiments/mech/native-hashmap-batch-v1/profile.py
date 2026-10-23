"""One owned CPU-stack diagnostic; no benchmark timing observations."""
import fcntl,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
def main():
 q=json.loads((HERE/'qualification-v1/results.json').read_bytes())
 assert q['status']=='public-source-decoded-security-full-output-and-table-work-passed' and q['hash_table_work_preserved']
 env=json.loads((HERE/'compiler-v1/results.json').read_bytes())['environment']
 binary=HERE/'.build/knucleotide-source';assert process.sha(binary)==q['variants']['source']['binary_sha256']
 inp=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin';assert process.sha(inp)==q['input_sha256']
 out=HERE/'profile-v1';out.mkdir(exist_ok=False)
 policy=HERE/'qualification-v1/launch.json';assert process.sha(policy)==q['policy_sha256']
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  sampled=False
  def monitor():
   nonlocal sampled
   if sampled:return
   sampled=True
   r=process.execute(['/bin/ps','-axo','pid=,ppid=,comm='],out/'process-inventory',env,lock,deadline=10)
   assert r['exit_status']==0
   rows=[line.split(None,2) for line in (out/'process-inventory/stdout.bin').read_text().splitlines()]
   rows=[row for row in rows if len(row)==3 and row[1]==str(os.getpid()) and row[2]==str(binary)]
   assert len(rows)==1,rows
   pid=rows[0][0]
   r=process.execute(['/usr/bin/sample',pid,'2','1','-mayDie','-file',str(out/'stacks.txt')],out/'sampler',env,lock,deadline=30)
   process.save(out/'sampler-result.json',dict(exit_status=r['exit_status'],target_pid=int(pid),target_is_owned_direct_child=True))
  r=process.execute([str(binary),str(policy),str(out/'security.json'),'--'],out/'subject',env,lock,stdin=inp,deadline=900,monitor=monitor,monitor_interval=.2,quantitative=False)
  assert r['exit_status']==0 and process.sha(out/'subject/stdout.bin')=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
  n=json.loads((out/'security.json').read_bytes());assert n['native_hash_table_regions']==7 and n['native_hash_table_updates']==874999961
  process.save(out/'results.json',dict(status='profiled-complete-output-and-table-work-pass',source_commit=q['source_commit'],binary_sha256=process.sha(binary),benchmark_samples=0,profiling_overhead_included=True,sampler=json.loads((out/'sampler-result.json').read_bytes())))
if __name__=='__main__':main()
