"""Serial FASTA outputs, actual-source draw witnesses and search-equivalence checks."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('janet_fasta_owned',HERE.parent/'native-v1/run.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success


def main():
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    for name,pin in plan['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    sources={'compact':HERE/'sources/compact.janet'}
    out=HERE/'compact-qualification-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',benchmark_samples=0,chart_admission=False,
                sources={label:dict(path=str(p.relative_to(ROOT)),sha256=process.sha(p)) for label,p in sources.items()},
                controller_sha256=process.sha(Path(__file__)),outputs=[],witnesses=[])
    corpus_path=ROOT/plan['corpus'];corpus=json.loads(corpus_path.read_bytes())
    projections={}
    for label,source in sources.items():
        text=source.read_text()
        assert text.count('(set seed (% (+ (* seed 3877) 29573) 139968))')==1
        text='(var draw-count 0)\n'+text.replace('(set seed (% (+ (* seed 3877) 29573) 139968))','(++ draw-count)\n    (set seed (% (+ (* seed 3877) 29573) 139968))')
        assert text.count('(random-record (* 5 n) homo))')==1
        text=text.replace('(random-record (* 5 n) homo))','(random-record (* 5 n) homo)\n  (file/write stderr (string/format "%d %d\\n" draw-count seed)))')
        projection=out/(label+'-witness.janet');projection.write_text(text);projections[label]=projection
    report['projection_sha256']={label:process.sha(p) for label,p in projections.items()}
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def run(source,directory,n=None,stdin=None):
            command=[plan['runtime'],'-R','-n',str(source)]+([str(n)] if n is not None else [])
            return process.execute(command,directory,plan['environment'],lock,stdin)
        for row in plan['schedule']:
            if row['benchmark']!='fasta':continue
            case=corpus['cases'][row['corpus_index']];expected=(corpus_path.parent/case['expected']['path']).read_bytes()
            seed=42
            for _ in range(8*case['n']):seed=(seed*3877+29573)%139968
            for label,source in sources.items():
                directory=out/f"{label}-{row['case']}"
                result=run(source,directory,case['n'],ROOT/row['stdin'])
                receipt=validate_success(case,(directory/'stdout.bin').read_bytes(),(directory/'stderr.bin').read_bytes(),result['exit_status'],expected)
                report['outputs'].append(dict(label=label,**receipt))
                directory=out/f"{label}-witness-{row['case']}"
                result=run(projections[label],directory,case['n'],ROOT/row['stdin'])
                assert (directory/'stderr.bin').read_bytes()==f"{8*case['n']} {seed}\n".encode()
                validate_success(case,(directory/'stdout.bin').read_bytes(),b'',result['exit_status'],expected)
                report['witnesses'].append(dict(label=label,case=case['case'],draws=8*case['n'],final_seed=seed,stdout_valid=True))
                process.save(out/'results.json',report)
        report['status']='16-compact-bounded-outputs-and-16-draw-witnesses-pass'
        process.save(out/'results.json',report)
    print(report['status'])


if __name__=='__main__':main()
