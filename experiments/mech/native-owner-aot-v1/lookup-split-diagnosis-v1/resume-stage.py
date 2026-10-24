"""Qualify and measure separate lookup functions against IR77."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '65dfd8bef29a8aef4cddd6926ff6461a959c24be'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'direct-lookup-cache-timing-v1/results.json').read_text())['configuration']
config.update(compiler='compiler-v62',parent_receipt='direct-lookup-cache-timing-v1',parent_binary='counting-direct-lookup-cache',binary='counting-lookup-split',package='owner-counting-lookup-split',receipt='lookup-split-timing-v2',work_policy=66,require_direct_lookup_regions=5,reuse_build_receipt='lookup-split-timing-v1')
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'lookup-split-timing-v2/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'lookup-split-timing-v2/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-direct-lookup-cache-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','lookup-split-timing-v2','--compiler','compiler-v62','--binary','counting-lookup-split','--receipt',f'full-lookup-split-v{index}','--parent-receipt','direct-lookup-cache-timing-v1','--parent-binary','counting-direct-lookup-cache','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-lookup-split-cohort-v1',*[f'full-lookup-split-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-lookup-split-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
