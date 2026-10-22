"""Serial full-input comparison with complete output validation and closure."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'revcomp-streaming-v1'))
from build_baseline import ROOT,PLAN,process
HERE=Path(__file__).resolve().parent
import fcntl,hashlib,json,os,random,statistics
from pathlib import Path
B=HERE/'.build'
OLD=HERE.parent/'revcomp-streaming-v1/.build'
VARIANTS={'original4':(OLD/'mech-revcomp-parent',4),'compacted4':(OLD/'mech-revcomp-candidate',4),'reuse4':(B/'mech-revcomp-reuse',4),'reuse8':(B/'mech-revcomp-reuse',8),'rust8':(OLD/'rust-revcomp-1',8)}
INPUT=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
FULL_BYTES=254166745
FULL_SHA='e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'
RETAINED_MECH=.149272625
def sha_file(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):d.update(chunk)
 return d.hexdigest()
def main():
 assert json.loads((HERE/'qualification-v1/results.json').read_bytes())['status']=='all-61-parent-candidate-behaviors-identical'
 assert json.loads((HERE/'build-v1/results.json').read_bytes())['status']=='tests-and-build-pass-identical-native-object'
 assert INPUT.stat().st_size==FULL_BYTES and sha_file(INPUT)=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
 out=HERE/'run-v1';out.mkdir(exist_ok=False)
 pins={str(p):process.sha(p) for p in [*[v[0] for v in VARIANTS.values()],Path(__file__),HERE/'prepare.py',HERE.parent/'revcomp-streaming-v1/build_baseline.py',HERE/'qualify.py',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py',ROOT/'archive/workloads/revcomp/revcomp.mec',ROOT/'archive/workloads/revcomp/upstream/revcomp-rust-1.rs']}
 env={**PLAN['environment'],'RAYON_NUM_THREADS':'8'}
 report=dict(status='running',samples=[],telemetry=[],pins=pins,input=dict(path=str(INPUT),bytes=FULL_BYTES,sha256=sha_file(INPUT)),expected_output=dict(bytes=FULL_BYTES,sha256=FULL_SHA),runtime_environment=env,
  variants={k:dict(command=[str(p)],workers=w) for k,(p,w) in VARIANTS.items()},benchmark_samples=0,chart_admission=False,
  retained_mech_aot_reference_seconds=RETAINED_MECH,thermal_frequency_logging=False,
  timing_boundary='Fresh process from monotonic clock before fork through independently observed exit. Includes startup, input reading, native transformation, complete output, flush and shutdown. Full output validation and owned cleanup follow exit; no phase subtraction.',
  correctness_scope='Official generated FASTA workload; all 61 old/new behaviors match, with eleven pre-existing extended-source limitations retained explicitly.',
  output_retention='Full output written to a regular file, hashed after child closure, then removed with hash/size receipt; bounded complete captures retained.')
 def save():process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);report['mutex_inode']=os.fstat(lock.fileno()).st_ino
  def telemetry():
   i=len(report['telemetry']);snap={}
   for name,cmd in [('power',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm']),('memory',['/usr/bin/vm_stat']),('swap',['/usr/sbin/sysctl','vm.swapusage'])]:
    d=out/f'telemetry-{i:03d}-{name}';r=process.execute(cmd,d,env,lock)
    assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes();snap[name]=(d/'stdout.bin').read_text()
   assert "'AC Power'" in snap['power']
   assert {s.split()[-1] for s in snap['settings'].splitlines() if 'lowpowermode' in s}=={'0'}
   names={Path(s.split()[-1]).name for s in snap['processes'].splitlines()[1:] if s.split()};assert not names & {'cargo','rustc','clang','clang++','gcc','cc1','cc1plus','javac'},'Competing compiler'
   report['telemetry'].append(snap);save()
  try:
   telemetry()
   official=ROOT/'archive/workloads/revcomp/inputs';want=(official/'revcomp-output-1000.txt').read_bytes()
   assert sha_file(official/'revcomp-input-1000.txt')=='62d1e8d0df7938d2aefda9a37887e0389231ea72c099c29a51afb6edca1bdc73'
   assert hashlib.sha256(want).hexdigest()=='549dcdcc7df2685145e6cbdfd682469bd9c12ff1beec93c270f8ba447acd4855'
   for label,(binary,workers) in VARIANTS.items():
    d=out/f'official-{label}';r=process.execute([str(binary)],d,{**env,'MECH_SEQUENCE_PARTITIONS':str(workers)},lock,stdin=official/'revcomp-input-1000.txt',deadline=30)
    assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').read_bytes()==want,label
   report['official_input_all_five_pass']=True;save()
   rng=random.Random(20261022013)
   for trial in range(1,8):
    order=list(VARIANTS);rng.shuffle(order)
    for label in order:
     assert all(process.sha(Path(p))==h for p,h in pins.items());telemetry();binary,workers=VARIANTS[label];d=out/f'{trial:02d}-{label}'
     r=process.execute([str(binary)],d,{**env,'MECH_SEQUENCE_PARTITIONS':str(workers)},lock,stdin=INPUT,deadline=120,quantitative=True)
     assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').stat().st_size==FULL_BYTES and sha_file(d/'stdout.bin')==FULL_SHA,label
     omission=dict(bytes=FULL_BYTES,sha256=FULL_SHA,verified_complete=True,group_closed=r['group_closed'],reaped=r['reaped'],reason='Complete stdout hashed after child closure; large output omitted, never substituted during timing.')
     process.save(d/'stdout-omitted.json',omission);(d/'stdout.bin').unlink()
     row=dict(round=trial,label=label,seconds=r['elapsed_seconds'],x_retained_mech_aot=r['elapsed_seconds']/RETAINED_MECH,maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds'])
     report['samples'].append(row);report['benchmark_samples']+=1;save();print(json.dumps(row),flush=True)
   report['summary']={}
   for label in VARIANTS:
    times=[r['seconds'] for r in report['samples'] if r['label']==label];report['summary'][label]=dict(median_seconds=statistics.median(times),stdev_seconds=statistics.stdev(times),x_retained_mech_aot=statistics.median(times)/RETAINED_MECH,maximum_rss_bytes=max(r['maximum_rss_bytes'] for r in report['samples'] if r['label']==label))
   telemetry();report['status']='all-35-full-size-outputs-pass';save()
  except BaseException as error:report['status']='failed-not-admissible';report['error']=str(error);save();raise
if __name__=='__main__':main()
