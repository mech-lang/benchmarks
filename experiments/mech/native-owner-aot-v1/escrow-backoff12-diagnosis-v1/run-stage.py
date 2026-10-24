"""Qualify and measure the unchanged source with a longer bounded spin against the accepted ten-round version."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '438646017717a5c4392721f13c6f935e88c59527'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'escrow-backoff10-timing-v1/results.json').read_text())['configuration']
config.pop('reuse_build_receipt', None)
config.update(compiler='compiler-v66',parent_receipt='escrow-backoff10-timing-v1',parent_binary='counting-escrow-backoff10',binary='counting-escrow-backoff12',package='owner-counting-escrow-backoff12',receipt='escrow-backoff12-timing-v1',work_policy=66,require_direct_lookup_regions=5)
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'escrow-backoff12-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'escrow-backoff12-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-lookup-split-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','escrow-backoff12-timing-v1','--compiler','compiler-v66','--binary','counting-escrow-backoff12','--receipt',f'full-escrow-backoff12-v{index}','--parent-receipt','escrow-backoff10-timing-v1','--parent-binary','counting-escrow-backoff10','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-escrow-backoff12-cohort-v1',*[f'full-escrow-backoff12-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-escrow-backoff12-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
