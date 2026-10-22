"""Qualify standard seven-thread histograms, transfer, join and error handling."""
import fcntl
import json
from pathlib import Path
import hashlib
import qualify as base

HERE=Path(__file__).resolve().parent
ROOT=base.ROOT
process=base.process


def main():
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    for name,pin in plan['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    source=HERE/'sources/threaded-modulo.janet'
    out=HERE/'threaded-qualification-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',source_sha256=process.sha(source),controller_sha256=process.sha(Path(__file__)),
                outputs=[],work_witnesses=[],workers=7,benchmark_samples=0,chart_admission=False)
    text=source.read_text();needle='    (put tables width table))';assert text.count(needle)==1
    trace='''    (put tables width table))
  (each width widths
    (def counts (tables width))
    (file/write stderr (string/format "H %d %d\\n" width (length counts)))
    (def trace-entries (seq [[key count] :pairs counts] [key count]))
    (sort trace-entries (fn [[a _] [b _]] (< a b)))
    (each [key count] trace-entries
      (file/write stderr (string/format "%.0f %d\\n" key count))))'''
    projection=out/'threaded-witness.janet';projection.write_text(text.replace(needle,trace))
    failure=out/'threaded-failure.janet'
    needle='  (def counts @{})';assert text.count(needle)==1
    failure.write_text(text.replace(needle,'  (when (= width 6) (error "owned-thread-probe"))\n'+needle))
    report['projection_sha256']=process.sha(projection);report['failure_source_sha256']=process.sha(failure)
    corpus_path=ROOT/plan['corpus'];corpus=json.loads(corpus_path.read_bytes())
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for row in plan['schedule']:
            if row['benchmark']!='knucleotide':continue
            case=corpus['cases'][row['corpus_index']]
            raw=(ROOT/row['stdin']).read_bytes();expected=(corpus_path.parent/case['expected']['path']).read_bytes()
            witness=base.witness(base.sequence(raw))
            for label,path in [('normal',source),('witness',projection)]:
                directory=out/f"{label}-{row['case']}"
                r=process.execute([plan['runtime'],'-R','-n',str(path)],directory,plan['environment'],lock,ROOT/row['stdin'])
                stderr=(directory/'stderr.bin').read_bytes()
                base.validate_success(case,(directory/'stdout.bin').read_bytes(),b'' if label=='witness' else stderr,r['exit_status'],expected)
                if label=='witness':
                    assert stderr==witness
                    report['work_witnesses'].append(dict(case=row['case'],full_histograms=7,complete_histogram_sha256=hashlib.sha256(witness).hexdigest()))
                else:report['outputs'].append(dict(case=row['case'],complete_stdout_valid=True))
                process.save(out/'results.json',report)
        directory=out/'worker-failure'
        stdin=ROOT/next(r['stdin'] for r in plan['schedule'] if r['benchmark']=='knucleotide')
        r=process.execute([plan['runtime'],'-R','-n',str(failure)],directory,plan['environment'],lock,stdin)
        assert r['exit_status']==1 and not (directory/'stdout.bin').read_bytes()
        assert b'Histogram worker failed: owned-thread-probe' in (directory/'stderr.bin').read_bytes()
        report['owned_worker_failure_propagated_and_process_closed']=True
        report['status']='14-threaded-outputs-98-full-histograms-and-worker-failure-pass'
        process.save(out/'results.json',report)
    print(report['status'])

if __name__=='__main__':main()
