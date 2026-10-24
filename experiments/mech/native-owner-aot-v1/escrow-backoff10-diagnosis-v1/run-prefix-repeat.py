"""Repeat the prefix separately after its initial regression; reuse only build bytes."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
initial=HERE/'escrow-backoff10-timing-v1/results.json'
config=json.loads(initial.read_text())['configuration']
config.update(receipt='escrow-backoff10-prefix-repeat-v1',reuse_build_receipt='escrow-backoff10-timing-v1')
args=['measure_stage.py']
for key,value in config.items():
    if value is None or value is False: continue
    args.append('--'+key.replace('_','-'))
    if value is not True: args.append(str(value))
with (OUT/'prefix-repeat.controller.stdout').open('wb') as stdout, (OUT/'prefix-repeat.controller.stderr').open('wb') as stderr:
    result=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
print('prefix-repeat exit',result.returncode,flush=True)
if result.returncode: sys.exit(result.returncode)
folder=HERE/config['receipt']
report=json.loads((folder/'results.json').read_text())
driver=(HERE/'measure_stage.py').read_bytes()
assert hashlib.sha256(driver).hexdigest()==report['study_driver_sha256']
(folder/'measure-stage-driver.py').write_bytes(driver)
print(json.dumps({k:report[k] for k in ['status','median_seconds','x_rust']}),flush=True)
