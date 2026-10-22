"""Complete stdout and exact arbitrary-precision advance/extract/removal states."""
import fcntl
import hashlib
import json
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,reference

CASES=(0,1,9,10,11,20,21,27,30,97,100,257)
HELPERS='''(var trace-advance 0)
(var trace-extract3 0)
(var trace-extract4 0)
(var trace-emitted 0)
(var trace-removals 0)
(var trace-inits 0)
(var trace-clears 0)
(ffi/defbind __gmpz_sizeinbase :ulong [z :ptr base :int])
(ffi/defbind __gmpz_get_str :ptr [out :ptr base :int z :ptr])
(defn trace-integer [z]
  (def text (buffer/new-filled (+ (__gmpz_sizeinbase z 10) 3) 0))
  (__gmpz_get_str text 10 z)
  (string/slice text 0 (string/find "\\0" text)))
(defn trace-state [tag k printed q r t]
  (file/write stderr (string/format "%s %.0f %.0f %s %s %s\\n"
    tag k printed (trace-integer q) (trace-integer r) (trace-integer t))))
'''

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    for row in PLAN['schedule']:
        if row['benchmark']=='pidigits':
            case=corpus['cases'][row['corpus_index']];want,_,_=reference(int(row['command'][-1]))
            assert want==(corpus_path.parent/case['expected']['path']).read_bytes()
    out=HERE/'qualification-v1';out.mkdir(exist_ok=False);projections={}
    for label,source in SOURCES.items():
        text=source.read_text();text=text.replace('(defn integer',HELPERS+'\n(defn integer',1)
        text=text.replace('  (__gmpz_init_set_ui z value)','  (++ trace-inits)\n  (__gmpz_init_set_ui z value)',1)
        text=text.replace('    (++ k)','    (++ trace-advance)\n    (++ k)',1)
        text=text.replace('    (__gmpz_mul_ui denominator denominator factor)','    (__gmpz_mul_ui denominator denominator factor)\n    (trace-state "A" k printed numerator accumulator denominator)',1)
        text=text.replace('      (__gmpz_fdiv_q digit combined denominator)','      (++ trace-extract3)\n      (__gmpz_fdiv_q digit combined denominator)',1)
        text=text.replace('      (__gmpz_fdiv_q next-digit combined denominator)','      (++ trace-extract4)\n      (__gmpz_fdiv_q next-digit combined denominator)\n      (file/write stderr (string/format "E %.0f %s %s\\n" k (trace-integer digit) (trace-integer next-digit)))',1)
        text=text.replace('      (when (zero? (__gmpz_cmp digit next-digit))','      (when (zero? (__gmpz_cmp digit next-digit))\n        (++ trace-emitted)\n        (file/write stderr (string/format "D %.0f %.0f %s\\n" (inc printed) k (trace-integer digit)))',1)
        text=text.replace('        (when (< printed target)','        (when (< printed target)\n          (++ trace-removals)',1)
        needle='          (__gmpz_mul_ui numerator numerator 10)))))';assert text.count(needle)==1
        text=text.replace(needle,'          (__gmpz_mul_ui numerator numerator 10)\n          (trace-state "R" k printed numerator accumulator denominator)))))')
        needle='  (each z [numerator denominator accumulator combined digit next-digit] (__gmpz_clear z)))';assert text.count(needle)==1
        text=text.replace(needle,'''  (trace-state "F" k printed numerator accumulator denominator)
  (file/write stderr (string/format "C %.0f %.0f %.0f %.0f %.0f\\n" trace-advance trace-extract3 trace-extract4 trace-emitted trace-removals))
  (each z [numerator denominator accumulator combined digit next-digit]
    (++ trace-clears)
    (__gmpz_clear z))
  (file/write stderr (string/format "L %.0f %.0f\\n" trace-inits trace-clears)))''')
        projection=out/(label+'-witness.janet');projection.write_text(text);projections[label]=projection
    report=dict(status='running',outputs=[],work_witnesses=[],benchmark_samples=0,chart_admission=False,
                source_sha256={k:process.sha(p) for k,p in SOURCES.items()},projection_sha256={k:process.sha(p) for k,p in projections.items()},reference_sha256=process.sha(HERE/'common.py'),controller_sha256=process.sha(Path(__file__)))
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for n in CASES:
            expected,trace,counts=reference(n,True)
            for label,source in SOURCES.items():
                d=out/f'{label}-n{n}';cmd=[PLAN['runtime'],'-R','-n',str(source),str(n)]
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').read_bytes()==expected,(label,n,(d/'stderr.bin').read_bytes())
                report['outputs'].append(dict(label=label,n=n,stdout_sha256=process.sha(d/'stdout.bin')))
                d=out/f'{label}-witness-n{n}';cmd[3]=str(projections[label])
                r=process.execute(cmd,d,PLAN['environment'],lock,deadline=120)
                assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==expected,(label,n,(d/'stderr.bin').read_bytes())
                assert (d/'stderr.bin').read_bytes()==trace,(label,n,(d/'stderr.bin').read_bytes()[:400])
                report['work_witnesses'].append(dict(label=label,n=n,**counts,all_integer_states_and_candidate_quotients_verified=True,complete_trace_sha256=hashlib.sha256(trace).hexdigest(),mpz_initializations=6,mpz_clears=6))
                process.save(out/'results.json',report)
        report['status']='all-complete-outputs-and-unbounded-integer-state-traces-pass';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],outputs=len(report['outputs']),work_witnesses=len(report['work_witnesses']))))

if __name__=='__main__':main()
