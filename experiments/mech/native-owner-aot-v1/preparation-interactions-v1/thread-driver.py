"""Poll owned children through libproc; retain CPU/lifetime observations, not timings."""
import ctypes
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process
from prolog_supervisor import Kernel, same_birth

OUTPUT_SHA = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
POLICY_SHA = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'


class ThreadInfo(ctypes.Structure):
    _fields_ = [('user_ns', ctypes.c_uint64), ('system_ns', ctypes.c_uint64)]
    _fields_ += [(name, ctypes.c_int32) for name in
                ('cpu_usage', 'policy', 'run_state', 'flags', 'sleep_time', 'curpri', 'priority', 'maxpriority')]
    _fields_ += [('name', ctypes.c_char * 64)]


kernel = Kernel()
library = kernel.library
library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
library.proc_pidpath.restype = ctypes.c_int
assert ctypes.sizeof(ThreadInfo) == 112


def poll_threads(identity, expected_path):
    current = kernel.identity(identity['pid'])
    if current is None: return []
    assert same_birth(current, identity) and current['ppid'] == os.getpid()
    path = ctypes.create_string_buffer(4096)
    if library.proc_pidpath(identity['pid'], path, len(path)) <= 0: return []
    assert Path(os.fsdecode(path.value)).resolve() == expected_path.resolve()
    ids = (ctypes.c_uint64 * 256)()
    count = library.proc_pidinfo(identity['pid'], 6, 0, ids, ctypes.sizeof(ids))
    assert 0 <= count < ctypes.sizeof(ids) and count % 8 == 0
    result = []
    for handle in ids[:count // 8]:
        info = ThreadInfo()
        size = library.proc_pidinfo(identity['pid'], 5, handle, ctypes.byref(info), ctypes.sizeof(info))
        if size == 0: continue  # A thread may retire between these two queries.
        assert size == ctypes.sizeof(info)
        result.append(dict(handle=handle, user_ns=info.user_ns, system_ns=info.system_ns,
                           run_state=info.run_state, name=os.fsdecode(bytes(info.name))))
    return result


def main():
    assert len(sys.argv) in (2, 3) and (len(sys.argv) == 2 or sys.argv[2] == '--prefix')
    prefix = len(sys.argv) == 3
    output_sha = 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa' if prefix else OUTPUT_SHA
    policy_sha = '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec' if prefix else POLICY_SHA
    updates = 6999961 if prefix else 874999961
    out = HERE / sys.argv[1]
    out.mkdir(exist_ok=False)
    timing = json.loads((HERE / 'preparation-combined-timing-v1/results.json').read_text())
    env = json.loads((HERE / 'compiler-v69/results.json').read_text())['environment']
    targets = dict(mech=HERE / '.build/counting-preparation-combined',
                   baseline=HERE / '.build/counting-escrow-backoff12',
                   rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    factorial = json.loads((HERE / 'full-preparation-interactions-v1/results.json').read_text())
    for subject, label in [('mech', 'combined'), ('baseline', 'baseline'), ('rust', 'rust')]:
        assert process.sha(targets[subject]) == factorial['pins'][label]['binary_sha256']
    policy = HERE / ('full-timing-v1/launch.json' if prefix else 'full-disjoint-state-v1/launch.json')
    assert process.sha(policy) == policy_sha
    inp = HERE / 'rust-span-diagnostic-v2/input.fasta' if prefix else HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    assert process.sha(inp) == ('e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb' if prefix else '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa')
    source = Path('/private/tmp/mech-native-hashmap-performance')
    def git_state():
        return dict(commit=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
                    status=subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True))
    before = git_state()
    assert not before['status']
    report = dict(status='collecting', source=before, driver_sha256=process.sha(Path(__file__)),
                  input_sha256=process.sha(inp), policy_sha256=policy_sha, benchmark_samples=0, input_mode='prefix' if prefix else 'full',
                  subjects=[], scope='Read-only libproc polling of birth-verified direct children. CPU endpoints are lower bounds; observations miss work after a thread\'s last poll. Opaque thread handles are not OS sample thread IDs. Polling affects execution and these processes are not primary timings. State observations do not divide elapsed time or identify source widths.')
    process.save(out / 'results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, subject in enumerate(['baseline', 'mech', 'rust', 'rust', 'mech', 'baseline']):
            folder = out / f'{index}-{subject}'
            snapshots, discovery, identity = [], [], None
            polls = 0
            origin = time.monotonic_ns()
            def monitor():
                nonlocal identity, polls
                polls += 1
                if identity is None:
                    capacity = library.proc_listallpids(None, 0) + 256
                    assert 0 < capacity < 65536
                    children = (ctypes.c_int * capacity)()
                    count = library.proc_listallpids(children, ctypes.sizeof(children))
                    assert 0 <= count < len(children)
                    matches = []
                    for pid in children[:count]:
                        candidate = kernel.identity(pid)
                        path = ctypes.create_string_buffer(4096)
                        if candidate and candidate['ppid'] == os.getpid() and library.proc_pidpath(pid, path, len(path)) > 0:
                            observed_path = Path(os.fsdecode(path.value)).resolve()
                            if len(discovery) < 3: discovery.append(dict(parent=os.getpid(), count=count, pid=pid, identity=candidate, path=str(observed_path), expected=str(targets[subject].resolve())))
                            if observed_path == targets[subject].resolve(): matches.append(candidate)
                    if not matches: return
                    assert len(matches) == 1
                    identity = matches[0]
                threads = poll_threads(identity, targets[subject])
                snapshots.append(dict(seconds=(time.monotonic_ns() - origin) / 1e9, threads=threads))
            native_path = out / f'{index}-{subject}.native.json'
            command = [str(targets[subject])]
            if subject != 'rust': command += [str(policy), str(native_path), '--']
            receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30,
                                      monitor=monitor, monitor_interval=.001, quantitative=False)
            assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == output_sha
            process.save(folder / 'monitor-discovery.json', dict(identity=identity, discovery=discovery, snapshots=len(snapshots), polls=polls))
            assert identity and same_birth(identity, receipt['birth_identity']) and len(snapshots) >= 2
            records = {}
            for snapshot in snapshots:
                for thread in snapshot['threads']:
                    handle = thread['handle']
                    if handle not in records:
                        records[handle] = dict(handle=handle, first_seen=snapshot['seconds'], last_seen=snapshot['seconds'],
                                               user_ns=0, system_ns=0, names=[], states={}, observations=0)
                    row = records[handle]
                    assert thread['user_ns'] >= row['user_ns'] and thread['system_ns'] >= row['system_ns'], 'Reused opaque thread handle'
                    row.update(last_seen=snapshot['seconds'], user_ns=thread['user_ns'], system_ns=thread['system_ns'])
                    row['observations'] += 1
                    row['states'][thread['run_state']] = row['states'].get(thread['run_state'], 0) + 1
                    if thread['name'] not in row['names']: row['names'].append(thread['name'])
            total_cpu = sum((r['user_ns'] + r['system_ns']) / 1e9 for r in records.values())
            assert total_cpu <= (receipt['user_cpu_seconds'] + receipt['system_cpu_seconds']) * 1.1 + .02
            if subject != 'rust':
                native = json.loads(native_path.read_text())
                assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == updates
                assert native['native_parallel_tasks'] == 7
                assert 1 <= native['native_parallel_peak_workers'] <= 7
                if not prefix: assert native['native_parallel_peak_workers'] == 7
                assert native['policy'] == 'secured' and native['shutdown'] == 'completed'
                if subject == 'mech': assert native['native_direct_lookup_regions'] == 5
            process.save(folder / 'thread-observations.json', dict(identity=identity, snapshots=snapshots,
                         threads=list(records.values()), observed_cpu_seconds_lower_bound=total_cpu))
            report['subjects'].append(dict(subject=subject, process=receipt,
                         threads=list(records.values()), observed_cpu_seconds_lower_bound=total_cpu,
                         raw_sha256=process.sha(folder / 'thread-observations.json')))
            process.save(out / 'results.json', report)
            print(f'{index}-{subject}: {len(records)} threads, complete output verified', flush=True)
    assert git_state() == before
    report['status'] = 'all-owned-thread-observations-and-outputs-verified'
    process.save(out / 'results.json', report)


if __name__ == '__main__': main()
