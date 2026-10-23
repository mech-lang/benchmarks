"""Owned CPU-stack profile of the measured preserved executable; not a timing sample."""
import fcntl,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
out=HERE/'available-profile-v1';out.mkdir(exist_ok=False)
measured=json.loads((HERE/'available-timing-v1/results.json').read_bytes())
binary=HERE.parent/'native-state-aot-v1/.build/counting-source'
assert process.sha(binary)==measured['binary_sha256']
env=json.loads((HERE.parent/'canonical-native-integration-v1/validation-v2/results.json').read_bytes())['environment']
sampled=False
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def monitor():
  global sampled
  if sampled:return
  sampled=True
  r=process.execute(['/bin/ps','-axo','pid=,ppid=,comm='],out/'inventory',env,lock,deadline=10)
  assert r['exit_status']==0
  rows=[line.split(None,2) for line in (out/'inventory/stdout.bin').read_text().splitlines()]
  rows=[row for row in rows if len(row)==3 and row[1]==str(os.getpid()) and row[2]==str(binary)]
  assert len(rows)==1,rows
  pid=rows[0][0]
  r=process.execute(['/usr/bin/sample',pid,'2','1','-mayDie','-file',str(out/'stacks.txt')],out/'sampler',env,lock,deadline=30)
  assert r['exit_status']==0,(out/'sampler/stderr.bin').read_text()
  process.save(out/'sampler.json',dict(target_pid=int(pid),target_is_owned_direct_child=True))
 r=process.execute([str(binary),str(HERE/'available-timing-v1/launch.json'),str(out/'native.report.json'),'--'],out/'subject',env,lock,stdin=HERE/'available-timing-v1/input.fasta',deadline=180,monitor=monitor,monitor_interval=.15,quantitative=False)
 assert r['exit_status']==0
 assert (out/'subject/stdout.bin').read_bytes()==(HERE/'available-timing-v1/run-0/stdout.bin').read_bytes()
 process.save(out/'results.json',dict(status='profiled-output-verified',source_commit=measured['source_commit'],binary_sha256=process.sha(binary),input_sha256=measured['input_sha256'],profiling_overhead_included=True,benchmark_samples=0,stacks_sha256=process.sha(out/'stacks.txt')))
 print('Profile captured; complete output verified.',flush=True)
