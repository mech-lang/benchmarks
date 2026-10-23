"""Sample the exact upstream Rust executable on full input, without rebuilding it."""
import fcntl
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

out = HERE / sys.argv[1]
out.mkdir(exist_ok=False)
binary = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
assert process.sha(binary) == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
source = HERE.parents[2] / 'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs'
assert process.sha(source) == '47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
assert process.sha(inp) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
env = json.loads((HERE / 'compiler-v6/results.json').read_text())['environment']
report = dict(status='sampling', binary_sha256=process.sha(binary), source_sha256=process.sha(source),
              input_sha256=process.sha(inp), selected_bases=125000000, subjects=[],
              benchmark_samples=0, profiling_overhead_included=True,
              scope='Exact timed upstream binary; three separate full-input processes; samples only')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index in range(3):
        folder = out / str(index)
        folder.mkdir()
        sample = {}

        def monitor():
            if sample:
                return
            r = process.execute(['/bin/ps', '-axo', 'pid=,ppid=,comm='], folder / 'inventory', env, lock, deadline=10)
            assert r['exit_status'] == 0
            rows = [line.split(None, 2) for line in (folder / 'inventory/stdout.bin').read_text().splitlines()]
            rows = [row for row in rows if len(row) == 3 and row[1] == str(os.getpid()) and row[2] == str(binary)]
            assert len(rows) == 1, rows
            pid = rows[0][0]
            r = process.execute(['/usr/bin/sample', pid, '1', '1', '-mayDie', '-file', str(folder / 'stacks.txt')],
                                folder / 'sampler', env, lock, deadline=15)
            assert r['exit_status'] == 0, (folder / 'sampler/stderr.bin').read_text()
            sample.update(pid=int(pid), owned_direct_child=True, stacks_sha256=process.sha(folder / 'stacks.txt'))

        r = process.execute([str(binary)], folder / 'subject', env, lock, stdin=inp,
                            deadline=30, monitor=monitor, monitor_interval=0.03, quantitative=False)
        assert r['exit_status'] == 0
        assert process.sha(folder / 'subject/stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        assert sample, 'The short-lived subject completed before a stack sample was captured'
        report['subjects'].append(dict(sample=sample, process=r, stdout_verified=True))
        process.save(out / 'results.json', report)
        print(f'Rust full-input profile {index + 1} captured; complete output verified.', flush=True)
report['status'] = 'three-full-output-verified-profiles'
process.save(out / 'results.json', report)
