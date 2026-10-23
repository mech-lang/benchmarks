"""Profile the exact control binary on the full input; not a timing cohort."""
import fcntl
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

out = HERE / 'full-profile-v1'
out.mkdir(exist_ok=False)
timing = json.loads((HERE / 'timing-v1/results.json').read_text())
assert timing['status'] == 'all-outputs-and-table-updates-verified'
binary = HERE / '.build/string-maps'
assert process.sha(binary) == timing['control_sha256']
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
assert process.sha(inp) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
samples = []
env = timing['environment']
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def monitor():
        if len(samples) >= 3:
            return
        folder = out / f'sample-{len(samples)}'
        folder.mkdir()
        r = process.execute(['/bin/ps', '-axo', 'pid=,ppid=,comm='], folder / 'inventory', env, lock, deadline=10)
        assert r['exit_status'] == 0
        rows = [line.split(None, 2) for line in (folder / 'inventory/stdout.bin').read_text().splitlines()]
        rows = [row for row in rows if len(row) == 3 and row[1] == str(os.getpid()) and row[2] == str(binary)]
        assert len(rows) == 1, rows
        pid = rows[0][0]
        r = process.execute(['/usr/bin/sample', pid, '1', '1', '-mayDie', '-file', str(folder / 'stacks.txt')], folder / 'sampler', env, lock, deadline=20)
        assert r['exit_status'] == 0
        samples.append(dict(pid=int(pid), owned_direct_child=True, stacks_sha256=process.sha(folder / 'stacks.txt')))
        print('Captured storage control sample', len(samples), flush=True)

    r = process.execute([str(binary)], out / 'subject', env, lock, stdin=inp, deadline=120,
                        monitor=monitor, monitor_interval=2, quantitative=False)
    assert r['exit_status'] == 0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors']
    assert process.sha(out / 'subject/stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    proof = json.loads((out / 'subject/stderr.bin').read_text())
    assert proof == dict(tables=7, updates=874999961, bases=125000000)
    assert len(samples) == 3
    process.save(out / 'results.json', dict(status='exact-control-profile-and-full-output-verified',
                 binary_sha256=process.sha(binary), input_sha256=process.sha(inp), samples=samples,
                 work=proof, benchmark_samples=0, profiling_overhead_included=True, process=r))
    print('Full control output and all 874,999,961 updates verified; owned process reaped.', flush=True)
