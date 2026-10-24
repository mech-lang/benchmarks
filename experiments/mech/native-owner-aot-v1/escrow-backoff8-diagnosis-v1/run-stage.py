"""Qualify and measure the unchanged source with a longer bounded spin against IR78."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '2ac58b364c22be15aa0ba0e232409c1ce8c93327'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'lookup-split-timing-v2/results.json').read_text())['configuration']
config.pop('reuse_build_receipt', None)
config.update(compiler='compiler-v64',parent_receipt='lookup-split-timing-v2',parent_binary='counting-lookup-split',binary='counting-escrow-backoff8',package='owner-counting-escrow-backoff8',receipt='escrow-backoff8-timing-v1',work_policy=66,require_direct_lookup_regions=5)
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'escrow-backoff8-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'escrow-backoff8-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-lookup-split-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','escrow-backoff8-timing-v1','--compiler','compiler-v64','--binary','counting-escrow-backoff8','--receipt',f'full-escrow-backoff8-v{index}','--parent-receipt','lookup-split-timing-v2','--parent-binary','counting-lookup-split','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-escrow-backoff8-cohort-v1',*[f'full-escrow-backoff8-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-escrow-backoff8-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
