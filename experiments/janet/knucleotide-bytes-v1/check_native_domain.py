"""Execute the native power-of-four arithmetic contract under the common mutex."""
import fcntl
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('knuc_domain_owned',HERE.parent/'native-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
with Path(plan['common_mutex']).open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=HERE/'native-domain-v1'
    r=m.execute([plan['runtime'],'-R','-n',str(HERE/'modulo-domain.janet')],out,plan['environment'],lock)
    assert r['exit_status']==0 and not (out/'stderr.bin').read_bytes() and (out/'stdout.bin').read_bytes()==b'72360\n'
    m.save(out/'result.json',dict(status='72360-native-domain-checks-pass',source_sha256=m.sha(HERE/'modulo-domain.janet'),runtime_sha256=m.sha(Path(plan['runtime'])),benchmark_samples=0,chart_admission=False))
print('72360-native-domain-checks-pass')
