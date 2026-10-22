"""Capture lossless native CSTs without executing input programs."""
import fcntl
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('owned',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py');process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((ROOT/'experiments/janet/bounded-v1/plan-v1.json').read_bytes())
def main():
    out=HERE/'native-v1';out.mkdir(exist_ok=False);exe=HERE/'.build/target/release/mech-source-owners-capture'
    sources={p.stem:p for p in (ROOT/'experiments/mech/pidigits-performance-v1/sources').glob('*.mec')}
    report={'status':'running','input_programs_executed':False,'helper_sha256':process.sha(exe),'helper_source_sha256':process.sha(HERE/'helper/src/main.rs'),'sources':{}}
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,p in sorted(sources.items()):
            d=out/name;r=process.execute([str(exe),str(p)],d,PLAN['environment'],lock)
            assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
            x=json.loads((d/'stdout.bin').read_bytes());assert x['source'].encode()==p.read_bytes()
            report['sources'][name]={'source_sha256':process.sha(p),'capture_sha256':process.sha(d/'stdout.bin'),'diagnostics':x['diagnostics']}
        report['status']='three-lossless-native-cst-captures-complete';process.save(out/'results.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
