"""Full-size complete-output and actual dual-extraction counts, untimed."""
import fcntl
import hashlib
import json
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,reference

SOURCES={name:HERE/'sources'/(name+'.janet') for name in ('compact-positive',)}

out=HERE/'composed-full-work-v1';out.mkdir(exist_ok=False)
want,_,counts=reference(10000)
evidence=ROOT/'archive/comparisons/additional-languages/20261009-full-suite/results/timings.json'
retained=json.loads(evidence.read_bytes())['programs']['pidigits:mech-control']['full_validation']
assert len(want)==retained['bytes']==16893 and hashlib.sha256(want).hexdigest()==retained['sha256']=='bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'
(out/'expected.stdout').write_bytes(want)
report=dict(status='running',n=10000,profiles={},reference_counts=counts,expected=dict(bytes=len(want),sha256=hashlib.sha256(want).hexdigest()),reference_sha256=process.sha(HERE/'common.py'),historical_output_reference=dict(path=str(evidence.relative_to(ROOT)),sha256=process.sha(evidence)),benchmark_samples=0,chart_admission=False)
prefix='''(var count-advance 0)
(var count-extract3 0)
(var count-extract4 0)
(var count-emitted 0)
(var count-removals 0)
(var count-inits 0)
(var count-clears 0)
'''
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for label,source in SOURCES.items():
        text=prefix+source.read_text();division='__gmpz_tdiv_q' if label=='compact-positive' else '__gmpz_fdiv_q'
        text=text.replace('  (__gmpz_init_set_ui z value)','  (++ count-inits)\n  (__gmpz_init_set_ui z value)',1)
        text=text.replace('    (++ k)','    (++ count-advance)\n    (++ k)',1)
        text=text.replace(f'      ({division} digit combined denominator)',f'      (++ count-extract3)\n      ({division} digit combined denominator)',1)
        text=text.replace(f'      ({division} next-digit combined denominator)',f'      (++ count-extract4)\n      ({division} next-digit combined denominator)',1)
        text=text.replace('      (when (zero? (__gmpz_cmp digit next-digit))','      (when (zero? (__gmpz_cmp digit next-digit))\n        (++ count-emitted)',1)
        text=text.replace('        (when (< printed target)','        (when (< printed target)\n          (++ count-removals)',1)
        needle='  (each z [numerator denominator accumulator combined digit next-digit] (__gmpz_clear z)))';assert text.count(needle)==1
        text=text.replace(needle,'''  (each z [numerator denominator accumulator combined digit next-digit]
    (++ count-clears) (__gmpz_clear z))
  (file/write stderr (string/format "C %.0f %.0f %.0f %.0f %.0f %.0f %.0f\\n"
    count-advance count-extract3 count-extract4 count-emitted count-removals count-inits count-clears)))''')
        projection=out/(label+'-witness.janet');projection.write_text(text);d=out/label
        r=process.execute([PLAN['runtime'],'-R','-n',str(projection),'10000'],d,PLAN['environment'],lock,deadline=300)
        trace=f"C {counts['advance_steps']} {counts['extract3_calls']} {counts['extract4_calls']} 10000 9999 6 6\n".encode()
        assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==want and (d/'stderr.bin').read_bytes()==trace,(label,(d/'stderr.bin').read_bytes())
        report['profiles'][label]=dict(source_sha256=process.sha(source),projection_sha256=process.sha(projection),**counts,mpz_initializations=6,mpz_clears=6,complete_output_valid=True)
        process.save(out/'results.json',report)
    report['status']='one-composed-full-size-output-and-dual-extraction-work-counts-pass';process.save(out/'results.json',report)
print(json.dumps(dict(status=report['status'],counts=counts)))
