"""Serial full-output/rejection contracts and per-record visit witnesses."""
import fcntl
import hashlib
import json
from common import HERE,ROOT,PLAN,SOURCES,process,validate,oracle

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    out=HERE/'qualification-v2';out.mkdir(exist_ok=False)
    cases=[]
    for row in PLAN['schedule']:
        if row['benchmark']!='revcomp':continue
        raw=(ROOT/row['stdin']).read_bytes();case=corpus['cases'][row['corpus_index']]
        expected,error,_=oracle(raw)
        if error is None:assert expected==(corpus_path.parent/case['expected']['path']).read_bytes()
        else:assert error[0]==case['expected_invalid_byte']
        cases.append((row['case'],ROOT/row['stdin']))
    # Cross the actual chunk flush and a partial row before an invalid byte.
    boundary=((1048576+60)//61)*60
    extra={f'chunk-{n}':b'>chunk\n'+(b'aCgTuMrWsYkVhDbN'*((n+14)//15))[:n]+b'\n' for n in (boundary-1,boundary,boundary+1,2*boundary+61)}
    extra['invalid-after-chunk']=b'>bad\n?'+b'A'*(boundary+67)+b'\n'
    extra['lowercase-invalid']=b'>bad\nACzTG\n'
    extra['invalid-next-record']=b'>first\nAC?GT\n>second\nACGT\n'
    for name,raw in extra.items():
        p=out/(name+'.stdin');p.write_bytes(raw);cases.append((name,p))
    projections={}
    for label,source in SOURCES.items():
        text=source.read_text()
        if label=='dense-chunk':
            text=text.replace('    (var offset','    (var visits 0)\n    (var offset',1).replace('      (def byte','      (++ visits)\n      (def byte',1)
            needle='    (file/write stdout output)))'
            text=text.replace(needle,'    (file/write stdout output)\n    (eprintf "W %d %d" (length bases) visits)))')
        else:
            text=text.replace('    (for i','    (var visits 0)\n    (for i',1).replace('      (def byte','      (++ visits)\n      (def byte',1)
            needle='    (when (> (length row) 0) (file/write stdout row "\\n"))))'
            assert text.count(needle)==1
            text=text.replace(needle,'    (when (> (length row) 0) (file/write stdout row "\\n"))\n    (eprintf "W %d %d" (length bases) visits)))')
        p=out/(label+'-witness.janet');p.write_text(text);projections[label]=p
    report=dict(status='running',outputs=[],work_witnesses=[],benchmark_samples=0,chart_admission=False,
                sources={k:dict(path=str(p.relative_to(ROOT)),sha256=process.sha(p)) for k,p in SOURCES.items()},
                controller_sha256=process.sha(Path(__file__)),oracle_sha256=process.sha(HERE/'common.py'))
    process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for case,stdin in cases:
            raw=stdin.read_bytes();expected,error,work=oracle(raw)
            for label,source in SOURCES.items():
                d=out/f'{label}-{case}'
                r=process.execute([PLAN['runtime'],'-R','-n',str(source)],d,PLAN['environment'],lock,stdin,deadline=120)
                validate((d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],raw,source)
                report['outputs'].append(dict(label=label,case=case,stdin=str(stdin.relative_to(ROOT)),stdin_sha256=process.sha(stdin),stdout_sha256=process.sha(d/'stdout.bin'),invalid=error is not None))
                if error is None:
                    d=out/f'{label}-witness-{case}'
                    r=process.execute([PLAN['runtime'],'-R','-n',str(projections[label])],d,PLAN['environment'],lock,stdin,deadline=120)
                    assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==expected
                    assert (d/'stderr.bin').read_bytes()==''.join(f'W {n} {v}\n' for n,v in work).encode()
                    report['work_witnesses'].append(dict(label=label,case=case,records=len(work),base_visits=sum(n for n,_ in work)))
                process.save(out/'results.json',report)
        report['status']='all-complete-output-rejection-and-visit-contracts-pass';process.save(out/'results.json',report)
    print(json.dumps(dict(status=report['status'],outputs=len(report['outputs']),witnesses=len(report['work_witnesses']))))

from pathlib import Path
if __name__=='__main__':main()
