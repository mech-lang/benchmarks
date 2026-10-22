"""Inspect existing per-record phase diagnostics without changing or timing code."""
import sys,json,fcntl,hashlib,re,random
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
PREVIOUS=HERE.parent/'revcomp-streaming-v1';B=PREVIOUS/'.build'
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):d.update(b)
 return d.hexdigest()
def main():
 out=HERE/'captures-v1';out.mkdir(exist_ok=False)
 baseline=json.loads((PREVIOUS/'baseline-build-v1/results.json').read_bytes());candidate=json.loads((PREVIOUS/'candidate-build-v1/results.json').read_bytes())
 variants={'parent4':(B/'mech-revcomp-parent',baseline['binary_sha256'],4),'candidate4':(B/'mech-revcomp-candidate',candidate['mech']['binary_sha256'],4),'candidate8':(B/'mech-revcomp-candidate',candidate['mech']['binary_sha256'],8)}
 inp=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin';input_sha='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa';output_sha='e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'
 assert inp.stat().st_size==254166745 and sha(inp)==input_sha
 env={**PLAN['environment'],'MECH_BYTE_PROFILE':'1','RAYON_NUM_THREADS':'8'}
 report=dict(status='running',benchmark_samples=0,diagnostic_only=True,source_changed=False,phase_clock='Existing runtime Instant::elapsed instrumentation around each read, native call and text write; excludes other process phases.',samples=[],input_sha256=input_sha,output_sha256=output_sha,environment=env,script_sha256=sha(Path(__file__)),binary_pins={k:v[1] for k,v in variants.items()},parent_study_seal_sha256=sha(PREVIOUS/'seal.json'))
 def save():process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);report['mutex_inode']=__import__('os').fstat(lock.fileno()).st_ino
  for name,cmd in [('power',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm'])]:
   r=process.execute(cmd,out/name,env,lock);assert r['exit_status']==0
  assert "'AC Power'" in (out/'power/stdout.bin').read_text()
  assert {s.split()[-1] for s in (out/'settings/stdout.bin').read_text().splitlines() if 'lowpowermode' in s}=={'0'}
  names={Path(s.split()[-1]).name for s in (out/'processes/stdout.bin').read_text().splitlines()[1:] if s.split()};assert not names&{'cargo','rustc','clang','clang++','gcc','cc1','cc1plus','javac'}
  rng=random.Random(20261022012)
  for trial in range(1,4):
   order=list(variants);rng.shuffle(order)
   for label in order:
    binary,pin,workers=variants[label];assert sha(binary)==pin;dest=out/f'{trial:02d}-{label}'
    r=process.execute([str(binary)],dest,{**env,'MECH_SEQUENCE_PARTITIONS':str(workers)},lock,stdin=inp,deadline=120)
    assert r['exit_status']==0 and sha(dest/'stdout.bin')==output_sha and (dest/'stdout.bin').stat().st_size==254166745
    diagnostics=(dest/'stderr.bin').read_text();rows=[]
    for line in diagnostics.splitlines():
     m=re.fullmatch(r'byte-record-profile bytes=(\d+) read=([\d.]+) compute=([\d.]+) write=([\d.]+)',line);assert m,line
     rows.append(dict(bytes=int(m[1]),read_seconds=float(m[2]),compute_seconds=float(m[3]),write_seconds=float(m[4])))
    assert [r['bytes'] for r in rows]==[50000000,75000000,125000000]
    process.save(dest/'stdout-omitted.json',dict(bytes=254166745,sha256=output_sha,verified_complete=True,reaped=r['reaped'],group_closed=r['group_closed'],reason='Complete diagnostic output checked after process closure, then omitted.'))
    (dest/'stdout.bin').unlink();report['samples'].append(dict(round=trial,label=label,records=rows,phase_totals={p:sum(x[p+'_seconds'] for x in rows) for p in ('read','compute','write')}));save();print(label,trial,flush=True)
  report['status']='nine-closed-instrumented-full-outputs-pass';save()
if __name__=='__main__':main()
