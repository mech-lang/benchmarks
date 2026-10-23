"""Sample the owned full-input AOT process; these are not timing samples."""
import argparse, fcntl, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

parser = argparse.ArgumentParser()
parser.add_argument('receipt', nargs='?', default='full-profile-v2')
parser.add_argument('build', nargs='?', default='profile-build-v2')
parser.add_argument('--launch', default='full-timing-v1/launch.json')
parser.add_argument('--deadline', type=float, default=45)
parser.add_argument('--interval', type=float, default=10)
parser.add_argument('--sample-count', type=int, default=3, help='Maximum captures; a short completed run may yield fewer')
parser.add_argument('--sample-duration', type=int, default=2, help='Seconds per all-thread capture')
parser.add_argument('--require-completion', action='store_true')
parser.add_argument('--require-packed-map', action='store_true')
parser.add_argument('--require-packed-ssa', action='store_true')
parser.add_argument('--require-parallel', action='store_true')
args = parser.parse_args()
assert 0 < args.interval < args.deadline
assert 1 <= args.sample_count <= 100 and 1 <= args.sample_duration <= 30
out = HERE / args.receipt
out.mkdir(exist_ok=False)
build_folder = args.build
build = json.loads((HERE / build_folder / 'results.json').read_bytes())
binary = Path(build.get('binary', str(HERE / '.build/counting-profile')))
assert process.sha(binary) == build['binary_sha256']
inp = ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
assert process.sha(inp) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
env = build.get('environment') or json.loads((HERE / 'compiler-v2/results.json').read_bytes())['environment']
samples = []
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def monitor():
        if len(samples) >= args.sample_count:
            return
        folder = out / f'sample-{len(samples)}'
        folder.mkdir()
        r = process.execute(['/bin/ps', '-axo', 'pid=,ppid=,comm='], folder / 'inventory', env, lock, deadline=10)
        assert r['exit_status'] == 0
        rows = [line.split(None, 2) for line in (folder / 'inventory/stdout.bin').read_text().splitlines()]
        rows = [row for row in rows if len(row) == 3 and row[1] == str(os.getpid()) and row[2] == str(binary)]
        assert len(rows) == 1, rows
        pid = rows[0][0]
        # sample captures every thread in this owned process, including parked
        # callers and native workers. Its stack counts are not CPU utilization.
        r = process.execute(['/usr/bin/sample', pid, str(args.sample_duration), '1', '-mayDie', '-file', str(folder / 'stacks.txt')], folder / 'sampler', env, lock, deadline=args.sample_duration + 30)
        assert r['exit_status'] == 0, (folder / 'sampler/stderr.bin').read_text()
        stacks = folder / 'stacks.txt'
        assert 'Call graph:\n' in stacks.read_text(), 'Sampler did not retain a call graph'
        samples.append(dict(pid=int(pid),owned_direct_child=True,stacks=str(stacks),stacks_sha256=process.sha(stacks),all_process_threads=True))
        print(f'Captured full-input stack sample {len(samples)}.', flush=True)

    try:
        r = process.execute([str(binary), str(HERE / args.launch), str(out / 'native.report.json'), '--'], out / 'subject', env, lock, stdin=inp, deadline=args.deadline, monitor=monitor, monitor_interval=args.interval, quantitative=False)
    except AssertionError:
        r = json.loads((out / 'subject/process.json').read_bytes())
        assert r.get('error') == 'Owned process deadline' and r['reaped'] and r['group_closed'] and not r['cleanup_errors']
    completed = r['exit_status'] == 0
    native = None
    if completed:
        assert process.sha(out / 'subject/stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        native = json.loads((out / 'native.report.json').read_text())
        assert native['shutdown'] == 'completed'
        assert native['native_hash_table_regions'] == 7 and native['native_hash_table_updates'] == 874999961
        if args.require_packed_map:
            assert native['native_packed_map_regions'] == 7 and native['native_packed_map_updates'] == 874999961
        if args.require_packed_ssa:
            assert native['native_packed_ssa_regions'] == 7
        if args.require_parallel:
            assert native['native_parallel_batches'] == 1 and native['native_parallel_regions'] == 2
            assert native['native_parallel_tasks'] == 7 and native['native_parallel_peak_workers'] == 7
    if args.require_completion:
        assert completed, 'Full profiling execution did not complete successfully'
    assert samples, 'Execution ended before any stacks were captured; reduce --interval'
    process.save(out / 'results.json', dict(status='profile-captured',source_commit=build.get('source_commit'),binary_sha256=process.sha(binary),object_sha256=build['object_sha256'],input_sha256=process.sha(inp),selected_bases=125000000,profiling_overhead_included=True,benchmark_samples=0,samples=samples,process=r,configuration=vars(args),launch_sha256=process.sha(HERE / args.launch),completed_output_verified=completed,native_counters={key:value for key,value in native.items() if key.startswith('native_')} if native else None,native_report_sha256=process.sha(out / 'native.report.json') if native else None,sampling_scope='All observed process threads; includes parked/waiting threads, partial unwinds and profiling overhead; thread samples must not be added as wall time'))
    print('Full-input profile complete; subject reaped.', flush=True)
