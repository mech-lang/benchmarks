"""Qualify and measure fused CRLF payload/offset construction against the accepted twelve-round runtime."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '8c9713b5a77e44175609d5dadef5d86a8b480593'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

for index in range(1,7):
    order=json.loads((HERE/f'full-lookup-split-v{index}/results.json').read_text())['configuration']['order']
    run('replication-'+str(index),['qualify_full.py','--timing','line-offset-crlf-timing-v1','--compiler','compiler-v67','--binary','counting-line-offset-crlf','--receipt',f'full-line-offset-crlf-v{index+6}','--parent-receipt','escrow-backoff12-timing-v1','--parent-binary','counting-escrow-backoff12','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('replication-cohort',['summarize_full.py','--receipt','full-line-offset-crlf-replication-v1',*[f'full-line-offset-crlf-v{i+6}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-line-offset-crlf-replication-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
