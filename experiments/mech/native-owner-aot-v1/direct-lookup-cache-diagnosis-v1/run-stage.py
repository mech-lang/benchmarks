"""Qualify and measure bounded lookup caches against IR76."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == 'c7cda2018917a75bd014c07ee2777305d88832e7'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'cold-frame-timing-v1/results.json').read_text())['configuration']
config.update(compiler='compiler-v61',parent_receipt='cold-frame-timing-v1',parent_binary='counting-cold-frame',binary='counting-direct-lookup-cache',package='owner-counting-direct-lookup-cache',receipt='direct-lookup-cache-timing-v1',work_policy=66,require_direct_lookup_regions=5)
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'direct-lookup-cache-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'direct-lookup-cache-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-cold-frame-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','direct-lookup-cache-timing-v1','--compiler','compiler-v61','--binary','counting-direct-lookup-cache','--receipt',f'full-direct-lookup-cache-v{index}','--parent-receipt','cold-frame-timing-v1','--parent-binary','counting-cold-frame','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-direct-lookup-cache-cohort-v1',*[f'full-direct-lookup-cache-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-direct-lookup-cache-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
