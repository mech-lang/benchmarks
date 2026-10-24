"""Retain sampled kernel-entry routes; these are not syscall or CPU-time counts."""
from collections import Counter
import hashlib, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(HERE))
from profile_hotspots import leaves

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
counts=Counter(); examples={}; sources=[]
for i in range(1,4):
    report=HERE/f'full-profile-escrow-backoff8-v{i}/analysis.json'
    analysis=json.loads(report.read_text())
    assert analysis['machine_code_identical'] and analysis['completed_output_verified']
    sources.append(dict(path=str(report.relative_to(HERE)),sha256=sha(report)))
    for sample in analysis['samples']:
        path=HERE/sample['stacks']; assert sha(path)==sample['stacks_sha256']
        content=path.read_text()
        kernel={m[1] for line in content.splitlines() if '(in libsystem_kernel.dylib)' in line and (m:=re.match(r'^[\s+!:|]*\d+ (\S+)',line))}
        workers={t['thread'] for t in sample['threads'] if t['observed_native_worker']}
        for thread,symbol,count,context in leaves(content):
            if symbol not in kernel: continue
            key=('worker' if thread in workers else 'nonworker',symbol)
            counts[key]+=count
            examples.setdefault(key,context[-12:])
result=dict(status='sampled-kernel-entry-routes-retained',sources=sources,script_sha256=sha(Path(__file__)),parser_sha256=sha(HERE/'profile_hotspots.py'),
    routes=[dict(thread_role=role,symbol=symbol,exclusive_observations=count,example_ancestors=examples[(role,symbol)]) for (role,symbol),count in counts.most_common()],
    counter_semantics=dict(instructions='macOS process retired instructions include user and kernel execution; off-CPU waiting retires no instructions in the waiting thread.',sources=['https://github.com/apple-oss-distributions/shell_cmds/blob/main/time/time.c','https://github.com/apple-oss-distributions/top/blob/main/top.1','https://github.com/apple-oss-distributions/xnu/blob/main/doc/observability/recount.md']),
    scope='Stack observations at kernel entry include off-CPU waits. They neither count syscalls nor apportion system CPU seconds. Parent join waits must not be attributed to worker budget contention. Only three candidate captures are partitioned.')
(HERE/'escrow-backoff8-checkpoint-v1/kernel-routes.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['thread_role','symbol','exclusive_observations']} for r in result['routes']]))
