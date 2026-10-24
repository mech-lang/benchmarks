"""Independently repeat the full-input alias-region trial against the accepted twelve-round parent."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == 'a94d34d60ab7bc503603217d0baa49397143eb09'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

for index in range(1,7):
    order=json.loads((HERE/f'full-lookup-split-v{index}/results.json').read_text())['configuration']['order']
    run('replication-'+str(index),['qualify_full.py','--timing','disjoint-state-timing-v1','--compiler','compiler-v68','--binary','counting-disjoint-state','--receipt',f'full-disjoint-state-v{index+6}','--parent-receipt','escrow-backoff12-timing-v1','--parent-binary','counting-escrow-backoff12','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('replication-cohort',['summarize_full.py','--receipt','full-disjoint-state-replication-v1',*[f'full-disjoint-state-v{i+6}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-disjoint-state-replication-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
