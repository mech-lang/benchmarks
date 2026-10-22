"""Serial energy conformance, exact state comparison and interaction witnesses."""
import fcntl
import json
from pathlib import Path
import struct
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256']
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    out=HERE/'qualification-v1';out.mkdir(exist_ok=False)
    projections={}
    for label,source in SOURCES.items():
        t=source.read_text();t=t.replace('(defn main','(var pair-visits 0)\n(var position-visits 0)\n\n(defn main',1)
        # Counters must be defined before any function that refers to them.
        t=t.replace('(var pair-visits 0)\n(var position-visits 0)\n\n(defn main','(defn main',1)
        t='(var pair-visits 0)\n(var position-visits 0)\n'+t
        if label=='scalar-registers':
            t=t.replace('~(do\n          (def dx','~(do\n          (++ pair-visits)\n          (def dx',1)
            t=t.replace('(array/push moves ~(+= ,(slot i axis) (* ,timestep ,(slot i (+ axis 3)))))',
                '(array/push moves ~(do (++ position-visits) (+= ,(slot i axis) (* ,timestep ,(slot i (+ axis 3))))))')
        else:
            # Only advance is instrumented, not either energy evaluation.
            a=t.index('(defn advance');b=t.index('(defn main',a);part=t[a:b]
            part=part.replace('      (def b','      (++ pair-visits)\n      (def b',1)
            part=part.replace('(for axis 0 3 (put b axis','(for axis 0 3 (++ position-visits) (put b axis',1)
            assert '++ pair-visits' in part and '++ position-visits' in part
            t=t[:a]+part+t[b:]
        needle='  (print (string/format "%.9f" (energy system))))'
        assert t.count(needle)==1
        trace='''  (print (string/format "%.9f" (energy system)))
  (file/write stderr (string/format "W %.0f %.0f\\n" pair-visits position-visits))
  (each body system
    (each value body (file/write stderr (string/format "%.17g\\n" value)))))'''
        t=t.replace(needle,trace)
        target=out/(label+'-witness.janet');target.write_text(t);projections[label]=target
    report=dict(status='running',outputs=[],work_witnesses=[],benchmark_samples=0,chart_admission=False,
                source_sha256={k:process.sha(p) for k,p in SOURCES.items()},
                projection_sha256={k:process.sha(p) for k,p in projections.items()},controller_sha256=process.sha(Path(__file__)))
    process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for row in PLAN['schedule']:
            if row['benchmark']!='nbody':continue
            case=corpus['cases'][row['corpus_index']];expected=(corpus_path.parent/case['expected']['path']).read_bytes();n=int(row['command'][-1]);reference=None
            for label,source in SOURCES.items():
                d=out/f"{label}-{row['case']}";cmd=[PLAN['runtime'],'-R','-n',str(source),str(n)]
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                receipt=validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],expected)
                report['outputs'].append(dict(label=label,**receipt))
                d=out/f"{label}-witness-{row['case']}";cmd[3]=str(projections[label])
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                validate_success(case,(d/'stdout.bin').read_bytes(),b'',r['exit_status'],expected)
                lines=(d/'stderr.bin').read_bytes().splitlines()
                assert lines[0]==f'W {10*n} {15*n}'.encode(),(label,row['case'],lines[:1])
                assert len(lines)==36
                bits=[struct.pack('>d',float(v)) for v in lines[1:]]
                if reference is None:reference=bits
                else:assert bits==reference,(label,row['case'])
                report['work_witnesses'].append(dict(label=label,case=row['case'],n=n,pair_interactions=10*n,position_updates=15*n,complete_state_bits_match_parent=True,state_sha256=__import__('hashlib').sha256(b''.join(bits)).hexdigest()))
                process.save(out/'results.json',report)
        report['status']='all-energy-work-and-complete-state-contracts-pass';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],outputs=len(report['outputs']),witnesses=len(report['work_witnesses']))))

if __name__=='__main__':main()
