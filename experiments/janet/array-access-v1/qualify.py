"""Complete bounded output, distinct tree allocation and full permutation witnesses."""
import fcntl
import hashlib
import json
import math
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success

def permutation_stream(n):
    """Factoradic unranking, independent of the application carry generator."""
    for ordinal in range(math.factorial(n) if n else 0):
        rank=ordinal;p=list(range(n))
        for i in range(n-1,0,-1):
            digit,rank=divmod(rank,math.factorial(i))
            p[:i+1]=p[digit:i+1]+p[:digit]
        original=p[:];flips=0
        while p[0]:
            last=p[0]+1;p[:last]=p[:last][::-1];flips+=1
        yield (str(ordinal)+' '+str(flips)+' '+''.join(str(v)+',' for v in original)+'\n').encode()

def main():
    for name,pin in PLAN['pins'].items():
        path=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(path)==pin['sha256']
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    out=HERE/'qualification-v1';out.mkdir(exist_ok=False)
    projections={}
    for label,(benchmark,source) in SOURCES.items():
        text=source.read_text()
        if benchmark=='binarytrees':
            a=text.index('(defn tree');b=text.index('(defn check',a)
            text=text[:a]+'''(var allocations 0)
(var checks 0)
(def seen @{})
(defn tree [depth]
  (++ allocations)
  (def node (if (zero? depth) @[nil nil]
    @[(tree (dec depth)) (tree (dec depth))]))
  (assert (not (get seen node)) "Shared mutable tree node")
  (put seen node true)
  node)

'''+text[b:]
            text=text.replace('(defn check [node]\n','(defn check [node]\n  (++ checks)\n',1)
            needle='           depth (check retained))))'
            assert text.count(needle)==1
            text=text.replace(needle,'           depth (check retained)))\n  (file/write stderr (string/format "W %.0f %.0f %.0f\\n" allocations checks (length seen))))')
        else:
            # Record the entire permutation before flipping mutates the copy.
            needle='        (set maximum (max maximum flips))'
            trace='''        (file/write stderr (string/format "%.0f %.0f " ordinal flips))
        (each value original (file/write stderr (string/format "%.0f," value)))
        (file/write stderr "\\n")
'''
            assert text.count(needle)==1;text=text.replace(needle,trace+needle)
        target=out/(label+'-witness.janet');target.write_text(text);projections[label]=target
    report=dict(status='running',outputs=[],work_witnesses=[],benchmark_samples=0,chart_admission=False,
                source_sha256={k:process.sha(p) for k,(_,p) in SOURCES.items()},projection_sha256={k:process.sha(p) for k,p in projections.items()},controller_sha256=process.sha(Path(__file__)))
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for row in PLAN['schedule']:
            if row['benchmark'] not in ('binarytrees','fannkuchredux'):continue
            case=corpus['cases'][row['corpus_index']];expected=(corpus_path.parent/case['expected']['path']).read_bytes();n=int(row['command'][-1])
            for label,(benchmark,source) in SOURCES.items():
                if benchmark!=row['benchmark']:continue
                d=out/f"{label}-{row['case']}";cmd=[PLAN['runtime'],'-R','-n',str(source),str(n)]
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                receipt=validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],expected)
                report['outputs'].append(dict(label=label,**receipt))
                d=out/f"{label}-witness-{row['case']}";cmd[3]=str(projections[label])
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                validate_success(case,(d/'stdout.bin').read_bytes(),b'',r['exit_status'],expected)
                if benchmark=='binarytrees':
                    depth=max(6,n)
                    count=(2**(depth+2)-1)+(2**(depth+1)-1)+sum(2**(4+depth-level)*(2**(level+1)-1) for level in range(4,depth+1,2))
                    assert (d/'stderr.bin').read_bytes()==f'W {count} {count} {count}\n'.encode()
                    witness=dict(distinct_mutable_nodes=count,allocations=count,node_check_visits=count,formula_used_only_in_reference_not_application=True)
                else:
                    reference=b''.join(permutation_stream(n));assert (d/'stderr.bin').read_bytes()==reference,(label,row['case'])
                    witness=dict(all_permutations=math.factorial(n) if n else 0,complete_permutation_and_flip_stream_sha256=hashlib.sha256(reference).hexdigest(),factoradic_order_independently_verified=True)
                report['work_witnesses'].append(dict(label=label,case=row['case'],benchmark=benchmark,n=n,**witness));process.save(out/'results.json',report)
        report['status']='all-bounded-output-and-full-work-witnesses-pass';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],outputs=len(report['outputs']),work_witnesses=len(report['work_witnesses']))))

if __name__=='__main__':main()
