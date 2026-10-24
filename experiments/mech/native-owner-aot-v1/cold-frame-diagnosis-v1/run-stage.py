"""Qualify and measure owned-frame cold reconstruction against IR75."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == '6d2e2673ea1d49d8ec16663dda012547f3ad1f4a'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'cold-recipes-timing-v1/results.json').read_text())['configuration']
config.update(compiler='compiler-v60',parent_receipt='cold-recipes-timing-v1',parent_binary='counting-cold-recipes',binary='counting-cold-frame',package='owner-counting-cold-frame',receipt='cold-frame-timing-v1')
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'cold-frame-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'cold-frame-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-cold-recipes-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','cold-frame-timing-v1','--compiler','compiler-v60','--binary','counting-cold-frame','--receipt',f'full-cold-frame-v{index}','--parent-receipt','cold-recipes-timing-v1','--parent-binary','counting-cold-recipes','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-cold-frame-cohort-v1',*[f'full-cold-frame-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-cold-frame-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
