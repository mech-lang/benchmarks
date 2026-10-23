"""Sample complete diagnostic-prefix executions, including later table publication."""
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
build = json.loads((HERE / sys.argv[2] / 'results.json').read_text())
binary = Path(build['binary'])
assert process.sha(binary) == build['binary_sha256']
inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
expected = (HERE / 'rust-span-diagnostic-v2/expected.txt').read_bytes()
env = build['environment']
captures = []
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index in range(3):
        folder = out / f'sample-{index}'
        folder.mkdir()
        captured = []

        def monitor():
            if captured:
                return
            inventory = folder / 'inventory'
            result = process.execute(['/bin/ps', '-axo', 'pid=,ppid=,comm='],
                                     inventory, env, lock, deadline=10)
            assert result['exit_status'] == 0
            rows = [line.split(None, 2) for line in (inventory / 'stdout.bin').read_text().splitlines()]
            pids = [row[0] for row in rows if len(row) == 3
                    and row[1] == str(os.getpid()) and row[2] == str(binary)]
            assert len(pids) == 1, pids
            result = process.execute(['/usr/bin/sample', pids[0], '2', '1', '-mayDie',
                                      '-file', str(folder / 'stacks.txt')],
                                     folder / 'sampler', env, lock, deadline=30)
            assert result['exit_status'] == 0, (folder / 'sampler/stderr.bin').read_text()
            captured.append(dict(pid=int(pids[0]), owned_direct_child=True,
                                 stacks=str(folder / 'stacks.txt')))

        native_path = folder / 'native.report.json'
        result = process.execute([str(binary), str(HERE / 'full-timing-v1/launch.json'),
                                  str(native_path), '--'],
                                 folder / 'subject', env, lock, stdin=inp, deadline=45,
                                 monitor=monitor, monitor_interval=0.02, quantitative=False)
        assert result['exit_status'] == 0 and result['reaped'] and result['group_closed']
        assert (folder / 'subject/stdout.bin').read_bytes() == expected
        native = json.loads(native_path.read_text())
        assert native['shutdown'] == 'completed'
        assert native['native_hash_table_regions'] == 7
        assert native['native_hash_table_updates'] == 6999961
        assert len(captured) == 1
        captures.extend(captured)
        print(f'Prefix profile {index + 1}: completed, exact output and all updates verified.', flush=True)

process.save(out / 'results.json', dict(
    status='profile-captured', source_commit=build['source_commit'],
    binary_sha256=process.sha(binary), object_sha256=build['object_sha256'],
    input_sha256=process.sha(inp), selected_bases=1000000,
    profiling_overhead_included=True, benchmark_samples=0, samples=captures,
    scope='Three serial complete prefix executions; samples begin shortly after launch and may omit early startup; not timing measurements'))
