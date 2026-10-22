"""An owned worker error must fail the application before any depth summaries."""
import fcntl
import json
from pathlib import Path
from common import HERE,PLAN,process,expected

source=HERE/'sources/threaded-cached.janet';text=source.read_text()
needle='  (def [depth workers id] task)';assert text.count(needle)==1
out=HERE/'failure-v1';out.mkdir(exist_ok=False)
projection=out/'owned-failure.janet';projection.write_text(text.replace(needle,needle+'\n  (when (= id 0) (error "owned-tree-worker-probe"))'))
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=out/'capture';r=process.execute([PLAN['runtime'],'-R','-n',str(projection),'9','7'],d,PLAN['environment'],lock)
    assert r['exit_status']==1 and (d/'stdout.bin').read_bytes()==expected(9).splitlines(keepends=True)[0]
    assert (d/'stderr.bin').read_bytes().startswith(b'error: Tree worker failed: owned-tree-worker-probe\n')
    process.save(out/'results.json',dict(status='owned-worker-error-propagates-without-depth-summaries',source_sha256=process.sha(source),projection_sha256=process.sha(projection),exit_status=1,expected_partial_stdout_sha256=process.sha(d/'stdout.bin'),benchmark_samples=0))
print('Owned worker failure passes')
