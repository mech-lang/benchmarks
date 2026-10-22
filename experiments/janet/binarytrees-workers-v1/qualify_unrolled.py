"""Complete output and fresh-node/visit witnesses for serial and partitioned work."""
import fcntl
import hashlib
import json
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,expected,work

CASES=(0,4,7,9,10,12)

SOURCES={name:HERE/'sources'/(name+'.janet') for name in ('unrolled','threaded-unrolled')}

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256']
    out=HERE/'unrolled-qualification-v1';out.mkdir(exist_ok=False)
    projections={}
    for label,source in SOURCES.items():
        text=source.read_text();a=text.index('(defn tree');b=text.index('(defn check',a)
        text=text[:a]+'''(var allocations 0)
(var checks 0)
(var seen @{})
(defn tree [depth]
  (++ allocations)
  (def node (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))
  (assert (not (get seen node)) "Shared mutable tree node")
  (put seen node true)
  node)

'''+text[b:]
        text=text.replace('(defn check [node]\n','(defn check [node]\n  (++ checks)\n',1)
        text=text.replace('      (def left-left', '      (++ checks)\n      (def left-left',1)
        text=text.replace('      (def right-left', '      (++ checks)\n      (def right-left',1)
        needle='           depth (check retained))))';assert text.count(needle)==1
        if label.startswith('threaded-'):
            text=text.replace('(defn work [task]\n','(defn work [task]\n  (set allocations 0)\n  (set checks 0)\n  (set seen @{})\n',1)
            assert text.count('  rows)')==1
            text=text.replace('  rows)','  [rows allocations checks (length seen)])',1)
            text=text.replace('(def row (get worker-results row-index))','(def row (get (get worker-results 0) row-index))',1)
            trace='''           depth (check retained)))
  (file/write stderr (string/format "M %.0f %.0f %.0f\\n" allocations checks (length seen)))
  (for id 0 workers
    (def result (get results id))
    (file/write stderr (string/format "W %.0f %.0f %.0f %.0f\\n" id (get result 1) (get result 2) (get result 3)))))'''
        else:
            trace='''           depth (check retained)))
  (file/write stderr (string/format "M %.0f %.0f %.0f\\n" allocations checks (length seen))))'''
        text=text.replace(needle,trace)
        target=out/(label+'-witness.janet');target.write_text(text);projections[label]=target
    report=dict(status='running',outputs=[],work_witnesses=[],benchmark_samples=0,chart_admission=False,
                sources={k:dict(path=str(p.relative_to(ROOT)),sha256=process.sha(p)) for k,p in SOURCES.items()},projection_sha256={k:process.sha(p) for k,p in projections.items()},controller_sha256=process.sha(Path(__file__)))
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for n in CASES:
            want=expected(n);depth=max(6,n);main_nodes,short=work(n)
            for label,source in SOURCES.items():
                for workers in ((1,2,3,7) if label.startswith('threaded-') else (1,)):
                    stem=f'{label}-n{n}-w{workers}'
                    args=[str(n),str(workers)] if label.startswith('threaded-') else [str(n)]
                    d=out/stem;cmd=[PLAN['runtime'],'-R','-n',str(source),*args]
                    r=process.execute(cmd,d,PLAN['environment'],lock,deadline=180)
                    assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').read_bytes()==want,(stem,(d/'stderr.bin').read_bytes())
                    report['outputs'].append(dict(label=label,n=n,workers=workers,stdout_sha256=process.sha(d/'stdout.bin')))
                    d=out/(stem+'-witness');cmd[3]=str(projections[label])
                    r=process.execute(cmd,d,PLAN['environment'],lock,deadline=180)
                    assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==want,(stem,(d/'stderr.bin').read_bytes())
                    if label.startswith('threaded-'):
                        trace=f'M {main_nodes} {main_nodes} {main_nodes}\n'
                        for id in range(workers):
                            nodes=0
                            for level in range(4,depth+1,2):
                                count=2**(4+depth-level);start=count*id//workers;end=count*(id+1)//workers
                                nodes+=(end-start)*(2**(level+1)-1)
                            trace+=f'W {id} {nodes} {nodes} {nodes}\n'
                    else:trace=f'M {main_nodes+short} {main_nodes+short} {main_nodes+short}\n'
                    assert (d/'stderr.bin').read_bytes()==trace.encode(),(stem,(d/'stderr.bin').read_bytes())
                    report['work_witnesses'].append(dict(label=label,n=n,workers=workers,total_distinct_nodes=main_nodes+short,total_check_visits=main_nodes+short,main_retained_and_stretch_nodes=main_nodes,worker_allocation_partition_verified=True))
                    process.save(out/'results.json',report)
        report['status']='all-bounded-outputs-and-distinct-node-partitions-pass';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],outputs=len(report['outputs']),work_witnesses=len(report['work_witnesses']))))

if __name__=='__main__':main()
