"""Bound the self-counter probe under the shared benchmark lock."""
import fcntl
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent
HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
before=source_state()
assert before['commit']=='76d17b03f7536132369b7d221f18727a1a045d03' and not before['status']
env=read(HERE/'compiler-v76/results.json')['environment']
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=process.execute([sys.executable,str(STUDY/'pilot.py')],STUDY/'counter-pilot-v1',env,lock,deadline=30,quantitative=False)
    process.save(STUDY/'counter-pilot-v1/source-provenance.json',dict(before=before,after=source_state(),driver_sha256=process.sha(Path(__file__)),probe_sha256=process.sha(STUDY/'pilot.py')))
    assert source_state()==before and result['exit_status']==0
    row=read(STUDY/'counter-pilot-v1/stdout.bin')
    print(row['status'],row['level_names'],row['timebase'],flush=True)
