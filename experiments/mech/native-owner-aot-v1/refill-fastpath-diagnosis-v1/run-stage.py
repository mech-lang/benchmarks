"""Qualify and measure the unchanged source with precomputed full refills against IR78."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '36a0d26e05b92f0f3fb21bdbd3605af2108ec882'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'lookup-split-timing-v2/results.json').read_text())['configuration']
config.pop('reuse_build_receipt', None)
config.update(compiler='compiler-v63',parent_receipt='lookup-split-timing-v2',parent_binary='counting-lookup-split',binary='counting-refill-fastpath',package='owner-counting-refill-fastpath',receipt='refill-fastpath-timing-v1',work_policy=66,require_direct_lookup_regions=5)
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'refill-fastpath-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'refill-fastpath-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-lookup-split-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','refill-fastpath-timing-v1','--compiler','compiler-v63','--binary','counting-refill-fastpath','--receipt',f'full-refill-fastpath-v{index}','--parent-receipt','lookup-split-timing-v2','--parent-binary','counting-lookup-split','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-refill-fastpath-cohort-v1',*[f'full-refill-fastpath-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-refill-fastpath-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
