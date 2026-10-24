"""Qualify and measure the source-derived affine cursor against IR73."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == 'c7574fa952a9981e1b2b0659a510fc05eff1c2ff'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

run('arbitrary-states',['../native-owner-dispatch-v1/validate_native.py','affine-cursor-states-v1','steady_keeps_finite_caps_arbitrary_headers_seeds_and_refill_frontiers',str(SOURCE)])
run('range-frontiers',['../native-owner-dispatch-v1/validate_native.py','affine-cursor-ranges-v1','loop_invariants_preserve_first_selection_steady_ranges_cap_transitions_and_refill_frontiers',str(SOURCE)])
config = json.loads((HERE/'caller-extent-timing-v1/results.json').read_text())['configuration']
config.update(compiler='compiler-v58',parent_receipt='caller-extent-timing-v1',parent_binary='counting-caller-extent',binary='counting-affine-cursor',package='owner-counting-affine-cursor',receipt='affine-cursor-timing-v1')
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'affine-cursor-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'affine-cursor-timing-v1/measure-stage-driver.py').write_bytes(driver)
for index in range(1,7):
    order=json.loads((HERE/f'full-caller-extent-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','affine-cursor-timing-v1','--compiler','compiler-v58','--binary','counting-affine-cursor','--receipt',f'full-affine-cursor-v{index}','--parent-receipt','caller-extent-timing-v1','--parent-binary','counting-caller-extent','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-affine-cursor-cohort-v1',*[f'full-affine-cursor-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-affine-cursor-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
