"""Independent exact-state oracle for noncanonical positions, masses and time steps."""
import fcntl
import hashlib
import json
from pathlib import Path
import struct
from common import HERE,ROOT,PLAN,SOURCES,process
from reference import integrate

CASES=[(0,0,.01),(1,1,.005),(-2,2,.02),(3,17,.01),(-1,1000,.02),(2,10000,.005)]
MAIN='''(defn main [& args]
  (def seed (scan-number (get args 1)))
  (def n (scan-number (get args 2)))
  (def dt (scan-number (get args 3)))
  (def system (bodies))
  (for i 0 5
    (def b (get system i))
    (for axis 0 3
      (put b axis (+ (get b axis) (* seed 0.03 (inc i) (inc axis))))
      (put b (+ axis 3) (+ (get b (+ axis 3)) (* 0.001 seed (- i axis)))))
    (when (> i 0) (put b 6 (* (get b 6) (+ 1 (* 0.01 seed (inc i)))))))
  (for axis 0 3
    (var momentum 0)
    (each b system (+= momentum (* (get b (+ axis 3)) (get b 6))))
    (put (get system 0) (+ axis 3) (/ (- momentum) solar-mass)))
  ADVANCE
  (each b system (each value b (print (string/format "%.17g" value)))))
'''

def main():
    out=HERE/'perturbed-v1';out.mkdir(exist_ok=False)
    projections={}
    for label,source in SOURCES.items():
        text=source.read_text();text=text[:text.index('(defn main')]
        step='(advance-n system dt n)' if label=='scalar-registers' else '(repeat n (advance system dt))'
        target=out/(label+'.janet');target.write_text(text+MAIN.replace('ADVANCE',step));projections[label]=target
    report=dict(status='running',cases=[],benchmark_samples=0,chart_admission=False,source_sha256={k:process.sha(p) for k,p in SOURCES.items()},projection_sha256={k:process.sha(p) for k,p in projections.items()},reference_sha256=process.sha(HERE/'reference.py'),controller_sha256=process.sha(Path(__file__)))
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for slot,(seed,steps,dt) in enumerate(CASES):
            want=[struct.pack('>d',v) for b in integrate(seed,steps,dt) for v in b]
            for label,source in projections.items():
                d=out/f'{slot:02d}-{label}'
                r=process.execute([PLAN['runtime'],'-R','-n',str(source),str(seed),str(steps),str(dt)],d,PLAN['environment'],lock,deadline=120)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                raw=(d/'stdout.bin').read_bytes().splitlines();assert len(raw)==35
                actual=[struct.pack('>d',float(v)) for v in raw]
                assert actual==want,(seed,steps,dt,label)
                report['cases'].append(dict(label=label,slot=slot,seed=seed,n=steps,dt=dt,state_sha256=hashlib.sha256(b''.join(actual)).hexdigest(),all_35_state_values_bit_exact_to_independent_python=True))
                process.save(out/'results.json',report)
        report['status']='all-perturbed-state-bits-match-independent-reference';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],cases=len(report['cases']))))

if __name__=='__main__':main()
