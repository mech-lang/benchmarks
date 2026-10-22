"""Generate the independent full stdout before any subject measurement."""
import fcntl
import json
import sys
from pathlib import Path
from common import HERE,ROOT,PLAN,process

fixture=json.loads((HERE.parent/'knucleotide-bytes-v1/input-generation-v1/input.json').read_bytes())
stdin=Path(fixture['path'])
assert stdin.stat().st_size==254166745 and process.sha(stdin)==fixture['sha256']
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=HERE/'reference-v1';out.mkdir(exist_ok=False)
    r=process.execute([sys.executable,str(HERE/'reference.py')],out/'capture',PLAN['environment'],lock,stdin,deadline=300)
    assert r['exit_status']==0 and not (out/'capture/stderr.bin').read_bytes()
    actual=out/'capture/stdout.bin'
    expected=dict(bytes=actual.stat().st_size,sha256=process.sha(actual),reference_sha256=process.sha(HERE/'reference.py'),input=fixture,
                  boundary='Independent untimed Python reference on the exact retained full FASTA; output hash after complete execution and group closure.')
    target=HERE.parent/'.build/inputs/revcomp-n25000000.expected';actual.replace(target)
    expected['path']=str(target);expected['capture_stdout_moved_to_ignored_build_path']=True
    process.save(out/'expected.json',expected)
    print(json.dumps({k:v for k,v in expected.items() if k in ('bytes','sha256')}))
