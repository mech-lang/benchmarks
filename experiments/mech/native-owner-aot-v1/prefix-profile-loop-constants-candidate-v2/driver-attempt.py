"""Pre-arm macOS sample for an exact executable copy before short launches."""
import argparse
import fcntl
import json
from pathlib import Path
import secrets
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('--build', required=True)
args = parser.parse_args()
out = HERE / args.receipt
out.mkdir(exist_ok=False)
build = json.loads((HERE / args.build / 'results.json').read_text())
source = Path(build['binary'])
assert process.sha(source) == build['binary_sha256']
name = 'mlcp-' + secrets.token_hex(4)
binary = HERE / '.build' / name
assert not binary.exists()
shutil.copy2(source, binary)
assert process.sha(binary) == build['binary_sha256']
env = build['environment']
inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
launch = HERE / 'full-timing-v1/launch.json'
assert process.sha(launch) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
samples, subjects = [], []
report = dict(status='sampling', source_commit=build['source_commit'],
              binary_sha256=build['binary_sha256'], binary_path=str(binary),
              object_sha256=build['object_sha256'], selected_bases=1000000,
              input_sha256=process.sha(inp), launch_sha256=process.sha(launch),
              expected_table_updates=6999961, completed_output_verified=False,
              samples=samples, subjects=subjects, native_counters=None,
              profiling_overhead_included=True, benchmark_samples=0,
              script_sha256=process.sha(Path(__file__)),
              scope='Sampler pre-armed with -wait for one random, unique executable name; exact unmodified executable bytes. Target remains an owned direct child; sampled PID must match. No debugger, stop signal, environment injection or timing observations.')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index in range(3):
        folder = out / str(index)
        folder.mkdir()
        launched = []

        def run_subject():
            if launched:
                return
            launched.append(True)
            native_path = folder / 'native.report.json'
            result = process.execute([str(binary), str(launch), str(native_path), '--'],
                                     folder / 'subject', env, lock, stdin=inp,
                                     deadline=30, quantitative=False)
            assert result['exit_status'] == 0
            assert process.sha(folder / 'subject/stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
            native = json.loads(native_path.read_text())
            assert native['shutdown'] == 'completed'
            assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 6999961
            assert native['native_packed_ssa_regions'] == native['native_parallel_peak_workers'] == 7
            subjects.append(dict(process=result, stdout_verified=True, native_report_sha256=process.sha(native_path)))
            report['native_counters'] = {key:value for key,value in native.items() if key.startswith('native_')}
            process.save(out / 'results.json', report)

        stacks = folder / 'stacks.txt'
        result = process.execute(['/usr/bin/sample', name, '2', '1', '-wait', '-mayDie', '-file', str(stacks)],
                                 folder / 'sampler', env, lock, deadline=12,
                                 monitor=run_subject, monitor_interval=0.15,
                                 quantitative=False)
        assert result['exit_status'] == 0 and len(launched) == 1
        content = stacks.read_text()
        assert 'Call graph:\n' in content
        pid = subjects[-1]['process']['pid']
        assert f'[{pid}]' in content.split('Call graph:\n', 1)[0]
        assert name in content.split('Call graph:\n', 1)[0]
        samples.append(dict(pid=pid, owned_direct_child=True, stacks=str(stacks),
                            stacks_sha256=process.sha(stacks), all_process_threads=True))
        process.save(out / 'results.json', report)
        print(f'Pre-armed prefix capture {index + 1} complete; output and updates verified.', flush=True)
report['status'] = 'profile-captured'
report['completed_output_verified'] = True
process.save(out / 'results.json', report)
