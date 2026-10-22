"""Complete bounded stdout and independently checked full hash-table witnesses."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('janet_knuc_owned',HERE.parent/'native-v1/run.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success


def sequence(raw):
    active=False;finished=False;selected=bytearray()
    for line in raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n').split(b'\n'):
        if line.startswith(b';'):continue
        if active:
            if line.startswith(b'>'):active=False;finished=True
            else:selected.extend(line)
        elif not finished and (line==b'>THREE' or line.startswith((b'>THREE ',b'>THREE\t'))):active=True
    return bytes(b'ACGT'.index(c) for c in selected.upper())


def witness(bases):
    out=[]
    for width in (1,2,3,4,6,12,18):
        counts={};key=0;modulus=4**width
        for i,byte in enumerate(bases):
            key=(key*4+byte)%modulus
            if i+1>=width:counts[key]=counts.get(key,0)+1
        out.append(f'H {width} {len(counts)}\n')
        for key,count in sorted(counts.items()):out.append(f'{key} {count}\n')
    return ''.join(out).encode()


def main():
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    for name,pin in plan['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    sources={n:HERE/'sources'/(n+'.janet') for n in ('byte-modulo','line-modulo')}
    out=HERE/'modulo-qualification-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',benchmark_samples=0,chart_admission=False,outputs=[],work_witnesses=[],
                controller_sha256=process.sha(Path(__file__)),sources={k:dict(path=str(p.relative_to(ROOT)),sha256=process.sha(p)) for k,p in sources.items()})
    projections={}
    for label,source in sources.items():
        text=source.read_text()
        needle='  counts)'
        assert text.count(needle)==1
        trace='''  (file/write stderr (string/format "H %d %d\\n" width (length counts)))
  (def trace-entries (seq [[key count] :pairs counts] [key count]))
  (sort trace-entries (fn [[a _] [b _]] (< a b)))
  (each [key count] trace-entries
    (file/write stderr (string/format "%.0f %d\\n" key count)))
  counts)'''
        projection=out/(label+'-witness.janet');projection.write_text(text.replace(needle,trace));projections[label]=projection
    report['projection_sha256']={label:process.sha(p) for label,p in projections.items()}
    corpus_path=ROOT/plan['corpus'];corpus=json.loads(corpus_path.read_bytes())
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for row in plan['schedule']:
            if row['benchmark']!='knucleotide':continue
            case=corpus['cases'][row['corpus_index']]
            raw=(ROOT/row['stdin']).read_bytes();expected=(corpus_path.parent/case['expected']['path']).read_bytes()
            bases=sequence(raw);histograms=witness(bases)
            for label,source in sources.items():
                command=[plan['runtime'],'-R','-n',str(source)]
                directory=out/f"{label}-{row['case']}"
                result=process.execute(command,directory,plan['environment'],lock,ROOT/row['stdin'])
                receipt=validate_success(case,(directory/'stdout.bin').read_bytes(),(directory/'stderr.bin').read_bytes(),result['exit_status'],expected)
                report['outputs'].append(dict(label=label,**receipt))
                directory=out/f"{label}-witness-{row['case']}";command[3]=str(projections[label])
                result=process.execute(command,directory,plan['environment'],lock,ROOT/row['stdin'])
                validate_success(case,(directory/'stdout.bin').read_bytes(),b'',result['exit_status'],expected)
                assert (directory/'stderr.bin').read_bytes()==histograms,(label,row['case'])
                report['work_witnesses'].append(dict(label=label,case=row['case'],bases=len(bases),full_histograms=7,
                                                  complete_histogram_stream_sha256=__import__('hashlib').sha256(histograms).hexdigest(),all_key_counts_verified=True))
                process.save(out/'results.json',report)
        report['status']='28-complete-outputs-and-196-full-histograms-pass';process.save(out/'results.json',report)
    print(report['status'])

if __name__=='__main__':main()
