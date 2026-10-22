"""Native floating division/floor bounds for every measured-domain partition."""
import fcntl
from pathlib import Path
from common import HERE,PLAN,process

source=HERE/'sources/threaded-cached.janet';text=source.read_text()
assert '(math/floor (/ (* count id) workers))' in text and '(math/floor (/ (* count (inc id)) workers))' in text
out=HERE/'partition-domain-v1';out.mkdir(exist_ok=False)
projection=out/'bounds.janet'
projection.write_text('''(defn main [& args]
  (for depth 6 22
    (for workers 1 8
      (loop [d :range [4 (inc depth) 2]]
        (def count (math/pow 2 (+ 4 depth (- d))))
        (for id 0 workers
          (def start (math/floor (/ (* count id) workers)))
          (def end (math/floor (/ (* count (inc id)) workers)))
          (print (string/format "%d %d %d %d %d %d" depth workers d id start end)))))))
''')
expected=[]
for depth in range(6,22):
 for workers in range(1,8):
  for d in range(4,depth+1,2):
   count=2**(4+depth-d);last=0
   for id in range(workers):
    start=count*id//workers;end=count*(id+1)//workers
    assert start==last;last=end
    expected.append(f'{depth} {workers} {d} {id} {start} {end}\n')
   assert last==count
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=out/'capture';r=process.execute([PLAN['runtime'],'-R','-n',str(projection)],d,PLAN['environment'],lock)
 assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').read_bytes()==''.join(expected).encode()
 process.save(out/'results.json',dict(status='all-native-bounds-match-exact-integer-partitions',partitions=len(expected),depths=[6,21],workers=[1,7],source_sha256=process.sha(source),projection_sha256=process.sha(projection),complete_disjoint_coverage=True,benchmark_samples=0))
print('Native partition bounds verified:',len(expected))
