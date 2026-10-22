import importlib.util,json,fcntl
from pathlib import Path
p=Path(__file__).resolve();root=p.parents[3]
spec=importlib.util.spec_from_file_location('owned_lexical',root/'experiments/janet/native-v1/run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
plan=json.loads((root/'experiments/janet/bounded-v1/plan-v1.json').read_bytes());plan['environment']['JANET_PATH']=str(root/'experiments/janet/dependencies-v2/spork-format')
with Path(plan['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=p.parent/'probe-v1'
 r=m.execute([plan['runtime'],'-R','-n',str(p.parent/'count.janet'),str(root/'experiments/janet/source-v3/spectralnorm.janet')],d,plan['environment'],lock)
 print(r['exit_status']);print((d/'stdout.bin').read_text());print((d/'stderr.bin').read_text())
