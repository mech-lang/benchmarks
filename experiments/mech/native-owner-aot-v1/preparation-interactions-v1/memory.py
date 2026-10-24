"""Separate, owned-process memory timelines and stopped-process size snapshots."""
import ctypes
import fcntl
import json
import os
import signal
import sys
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(STUDY))
from measure import PLAN, process, read, source_state, check_native, OUTPUT_SHA
from prolog_supervisor import Kernel, same_birth


class TaskInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ('virtual_size', 'resident_size', 'total_user', 'total_system',
                 'threads_user', 'threads_system')]
    _fields_ += [(name, ctypes.c_int32) for name in
                 ('policy', 'faults', 'pageins', 'cow_faults', 'messages_sent',
                  'messages_received', 'syscalls_mach', 'syscalls_unix', 'csw',
                  'threadnum', 'numrunning', 'priority')]


# SDK sys/resource.h, struct rusage_info_v4. All time fields retain their
# native units; only documented byte fields are used as byte measurements.
class UsageInfo(ctypes.Structure):
    _fields_ = [('uuid', ctypes.c_uint8 * 16)]
    _fields_ += [(name, ctypes.c_uint64) for name in
                 ('user_time', 'system_time', 'pkg_idle_wkups', 'interrupt_wkups',
                  'pageins', 'wired_size', 'resident_size', 'phys_footprint',
                  'proc_start_abstime', 'proc_exit_abstime', 'child_user_time',
                  'child_system_time', 'child_pkg_idle_wkups',
                  'child_interrupt_wkups', 'child_pageins', 'child_elapsed_abstime',
                  'diskio_bytesread', 'diskio_byteswritten', 'cpu_time_qos_default',
                  'cpu_time_qos_maintenance', 'cpu_time_qos_background',
                  'cpu_time_qos_utility', 'cpu_time_qos_legacy',
                  'cpu_time_qos_user_initiated', 'cpu_time_qos_user_interactive',
                  'billed_system_time', 'serviced_system_time', 'logical_writes',
                  'lifetime_max_phys_footprint', 'instructions', 'cycles',
                  'billed_energy', 'serviced_energy', 'interval_max_phys_footprint',
                  'runnable_time')]


assert ctypes.sizeof(TaskInfo) == 96 and ctypes.sizeof(UsageInfo) == 296
kernel = Kernel()
library = kernel.library
library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
library.proc_pidpath.restype = ctypes.c_int
library.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
library.proc_pid_rusage.restype = ctypes.c_int


def guarded(identity, binary):
    current = kernel.identity(identity['pid'])
    if current is None:
        return False
    assert same_birth(current, identity) and current['ppid'] == os.getpid()
    path = ctypes.create_string_buffer(4096)
    if library.proc_pidpath(identity['pid'], path, len(path)) <= 0:
        return False
    assert Path(os.fsdecode(path.value)).resolve() == binary.resolve()
    return True


def discover(binary):
    capacity = library.proc_listallpids(None, 0) + 256
    assert 0 < capacity < 65536
    pids = (ctypes.c_int * capacity)()
    count = library.proc_listallpids(pids, ctypes.sizeof(pids))
    assert 0 <= count < capacity
    matches = []
    for pid in pids[:count]:
        identity = kernel.identity(pid)
        if identity and identity['ppid'] == os.getpid():
            path = ctypes.create_string_buffer(4096)
            if library.proc_pidpath(pid, path, len(path)) > 0:
                if Path(os.fsdecode(path.value)).resolve() == binary.resolve():
                    matches.append(identity)
    assert len(matches) <= 1
    return matches[0] if matches else None


def sample(identity, binary):
    if not guarded(identity, binary):
        return None
    task, usage = TaskInfo(), UsageInfo()
    size = library.proc_pidinfo(identity['pid'], 4, 0, ctypes.byref(task), ctypes.sizeof(task))
    if not size:
        return None
    assert size == ctypes.sizeof(task)
    ok = library.proc_pid_rusage(identity['pid'], 4, ctypes.byref(usage))
    if ok:
        # The owned child may finish between two independent read-only queries.
        assert kernel.identity(identity['pid']) is None
        return None
    return dict(resident_bytes=task.resident_size, virtual_bytes=task.virtual_size,
                physical_footprint_bytes=usage.phys_footprint,
                lifetime_peak_physical_footprint_bytes=usage.lifetime_max_phys_footprint,
                page_faults=task.faults, pageins=task.pageins, cow_faults=task.cow_faults,
                threads=task.threadnum, running_threads=task.numrunning)


def main():
    assert len(sys.argv) == 3 and sys.argv[1] in ('timeline', 'snapshot')
    mode = sys.argv[1]
    out = HERE / sys.argv[2]
    out.mkdir(exist_ok=False)
    timing = read(HERE / 'full-preparation-interactions-v1/results.json')
    plan = read(STUDY / 'plan.json')
    targets = {s: HERE / '.build' / p['binary'] for s, p in timing['pins'].items() if s != 'rust'}
    targets['rust'] = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
    for subject, binary in targets.items():
        assert process.sha(binary) == timing['pins'][subject]['binary_sha256']
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    policy = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == timing['input_sha256'] and process.sha(policy) == timing['policy_sha256']
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    report = dict(status='collecting', mode=mode, source=before, driver_sha256=process.sha(Path(__file__)),
                  input_sha256=timing['input_sha256'], policy_sha256=timing['policy_sha256'],
                  observations=[], benchmark_samples=0,
                  scope='Separate diagnostic executions of exact timed binaries. Timelines use libproc on birth-verified direct children; sampled RSS peaks are lower bounds, wait4 RSS is a whole-process high-water mark, physical footprint is a different OS accounting measure. Snapshot executions stop only the owned child after seven workers are visible, take content-free vmmap/heap size summaries, then always resume it. Snapshot elapsed times and memory under inspection are not benchmark observations. No task-port or security setting changes.')
    process.save(out / 'results.json', report)
    orders = [plan['orders'][i] for i in (0, 7, 14)] if mode == 'timeline' else [plan['subjects']]
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, order in enumerate(orders):
            for subject in order:
                binary = targets[subject]
                folder = out / f'{index}-{subject}'
                native_path = out / (folder.name + '.native.json')
                identity, snapshots, captures = None, [], []
                captured = False
                origin = time.monotonic_ns()
                def monitor():
                    nonlocal identity, captured
                    if identity is None:
                        identity = discover(binary)
                    if identity is None:
                        return
                    observation = sample(identity, binary)
                    if observation is None:
                        return
                    snapshots.append(dict(seconds=(time.monotonic_ns() - origin) / 1e9, **observation))
                    if mode != 'snapshot' or captured or observation['threads'] < 8:
                        return
                    captured = True
                    assert guarded(identity, binary)
                    os.kill(identity['pid'], signal.SIGSTOP)
                    try:
                        for tool, arguments in [('vmmap', ['-summary', '-wide']),
                                                ('heap', ['--noContent', '--sortBySize', '--showSizes'])]:
                            assert guarded(identity, binary)
                            receipt = process.execute(['/usr/bin/' + tool, *arguments, str(identity['pid'])],
                                        out / (folder.name + '-' + tool), env, lock, deadline=15, quantitative=False)
                            captures.append(dict(tool=tool, process=receipt,
                                stdout_sha256=process.sha(out / (folder.name + '-' + tool) / 'stdout.bin'),
                                stderr_sha256=process.sha(out / (folder.name + '-' + tool) / 'stderr.bin')))
                    finally:
                        if guarded(identity, binary):
                            os.kill(identity['pid'], signal.SIGCONT)
                command = [str(binary)]
                if subject != 'rust':
                    command += [str(policy), str(native_path), '--']
                receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=45,
                                          monitor=monitor, monitor_interval=.001, quantitative=False)
                assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                assert identity and same_birth(identity, receipt['birth_identity']) and len(snapshots) >= 2
                if subject != 'rust':
                    check_native(native_path)
                if mode == 'snapshot':
                    assert captured and len(captures) == 2
                raw = dict(identity=identity, snapshots=snapshots, captures=captures)
                process.save(folder / 'memory-observations.json', raw)
                report['observations'].append(dict(subject=subject, order=index, process=receipt,
                    sampled_peak_rss_bytes=max(s['resident_bytes'] for s in snapshots),
                    sampled_peak_physical_footprint_bytes=max(s['physical_footprint_bytes'] for s in snapshots),
                    observed_lifetime_peak_physical_footprint_bytes=max(s['lifetime_peak_physical_footprint_bytes'] for s in snapshots),
                    samples=len(snapshots), captures=[dict(tool=c['tool'], exit_status=c['process']['exit_status']) for c in captures],
                    raw_sha256=process.sha(folder / 'memory-observations.json')))
                process.save(out / 'results.json', report)
                print(f'{mode} {index}-{subject}: {len(snapshots)} memory samples, output verified', flush=True)
    assert source_state() == before
    report['source_after'] = before
    report['status'] = 'all-owned-memory-observations-and-outputs-verified'
    process.save(out / 'results.json', report)


if __name__ == '__main__':
    main()
