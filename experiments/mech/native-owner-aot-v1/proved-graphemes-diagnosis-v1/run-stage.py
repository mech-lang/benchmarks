"""Run the source-proof runtime trial against its unchanged compiler parent."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == 'f1323c0383927e461a0c70f34872b1e6e44f9657'
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip()

def run(label, args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)

config = json.loads((HERE/'caller-extent-timing-v1/results.json').read_text())['configuration']
config.update(compiler='compiler-v57',parent_receipt='caller-extent-timing-v1',parent_binary='counting-caller-extent',binary='counting-proved-graphemes',package='owner-counting-proved-graphemes',receipt='proved-graphemes-timing-v1')
args = ['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
run('prefix',args)
report=json.loads((HERE/'proved-graphemes-timing-v1/results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(HERE/'proved-graphemes-timing-v1/measure-stage-driver.py').write_bytes(driver)
objects={name:hashlib.sha256((HERE/'.build'/('counting-'+name+'.project')/'program.o').read_bytes()).hexdigest() for name in ['caller-extent','proved-graphemes']}
(OUT/'object-identity.json').write_text(json.dumps(dict(object_sha256=objects,identical=len(set(objects.values()))==1,scope='Entire emitted Mech object, including every generated source function; linked runtime differs.'),indent=2)+'\n')
assert len(set(objects.values()))==1,'Unexpected generated-program change in runtime-only trial'
for index in range(1,7):
    order=json.loads((HERE/f'full-caller-extent-v{index}/results.json').read_text())['configuration']['order']
    run('full-'+str(index),['qualify_full.py','--timing','proved-graphemes-timing-v1','--compiler','compiler-v57','--binary','counting-proved-graphemes','--receipt',f'full-proved-graphemes-v{index}','--parent-receipt','caller-extent-timing-v1','--parent-binary','counting-caller-extent','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('cohort',['summarize_full.py','--receipt','full-proved-graphemes-cohort-v1',*[f'full-proved-graphemes-v{i}' for i in range(1,7)]])
cohort=json.loads((HERE/'full-proved-graphemes-cohort-v1/results.json').read_text())
print(json.dumps({key:cohort[key] for key in ['status','median_seconds','x_rust']}),flush=True)
