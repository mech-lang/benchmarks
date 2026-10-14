"""Bounded, unreaped-leader supervision for the unscored vendor SDK generator."""
import ctypes
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

CLEANUP_TIMEOUT = 5
MONITOR_TIMEOUT = 5
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def new_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


@contextmanager
def atomic():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        yield previous
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


class BSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]
    _fields_ += [('comm',ctypes.c_char*16),('name',ctypes.c_char*32)]
    _fields_ += [(name,ctypes.c_uint32) for name in ('nfiles','pgid','jobc','tdev','tpgid')]
    _fields_ += [('nice',ctypes.c_int32),('birth_seconds',ctypes.c_uint64),('birth_microseconds',ctypes.c_uint64)]


class Kernel:
    """The qualified Kotlin helper's zombie-aware identity read; never reaps."""
    def __init__(self):
        self.library = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        self.library.proc_pidinfo.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        self.library.proc_pidinfo.restype = ctypes.c_int
        require(ctypes.sizeof(BSDInfo) == 136, 'Unexpected kernel identity layout')

    def identity(self, pid):
        info = BSDInfo()
        # PROC_PIDTBSDINFO requires arg != 0 to include unreaped zombies.
        if self.library.proc_pidinfo(pid,3,1,ctypes.byref(info),ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        require(info.pid == pid and info.birth_seconds > 0, 'Invalid kernel identity')
        return {name:getattr(info,name) for name in
                ('pid','ppid','pgid','status','birth_seconds','birth_microseconds')}


def owned_identity(kernel, process, initial=None):
    identity = kernel.identity(process.pid)
    require(identity and identity['ppid'] == os.getpid() and identity['pgid'] == process.pid,
            'Missing owned native identity before reap')
    if initial is not None:
        require(all(identity[key] == initial[key] for key in
                ('pid','ppid','pgid','birth_seconds','birth_microseconds')),
                'Native leader identity changed before reap')
    return identity


def members(pgid, *, timeout):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,stat='], capture_output=True,
                            text=True, timeout=timeout, check=True)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split()
        require(len(fields) == 3 and all(x.isdecimal() for x in fields[:2]),
                'Malformed process-group observation')
        pid, group = map(int, fields[:2])
        if group == pgid and not fields[2].startswith('Z'):
            rows.append(dict(pid=pid, pgid=group, status=fields[2]))
    return rows


def cleanup_owned(process, record):
    deadline = time.monotonic()+CLEANUP_TIMEOUT

    def remaining_time():
        remaining = deadline-time.monotonic()
        require(remaining > 0, 'Process-group cleanup deadline expired')
        return remaining

    # Only an unreaped direct child reserves the leader's PID. Never use a
    # numeric process-group ID to signal after wait/poll has released that PID.
    if process.returncode is None:
        record['cleanup_signal_identity'] = 'unreaped-direct-child'
        try:
            os.killpg(process.pid, signal.SIGKILL)
            record['stop_signals'].append(int(signal.SIGKILL))
        except ProcessLookupError:
            pass
        except BaseException as error:
            record['cleanup_errors'].append(str(error) or type(error).__name__)
    else:
        record['cleanup_signal_skipped_reason'] = 'direct-child-already-reaped'
        if record.get('remaining_process_group') == []:
            record['remaining_after_cleanup'] = []
            return
    try:
        while True:
            record['monitor_processes'] += 1
            remaining = members(process.pid, timeout=remaining_time())
            record['remaining_after_cleanup'] = remaining
            if not remaining:
                break
            time.sleep(min(0.05, remaining_time()))
        if process.returncode is None:
            process.wait(timeout=remaining_time())
    except BaseException as error:
        record['cleanup_errors'].append(str(error) or type(error).__name__)


def lock_identity(common_fd):
    held, named = os.fstat(common_fd), Path('/tmp/mech-clbg-timing.lock').stat()
    require((held.st_dev,held.st_ino) == (named.st_dev,named.st_ino) and held.st_ino == 79859134,
            'Common lock identity changed')
    return held


def owned_command(command, environment, output, common_fd, timeout, name, cwd, *, kernel=None):
    output = Path(output)
    held = lock_identity(common_fd)
    detail = dict(command=command, environment=environment, cwd=str(cwd), pid=None, pgid=None,
        started_at=datetime.now(timezone.utc).isoformat(), timeout_seconds=timeout,
        process_monitor_call_timeout_seconds=MONITOR_TIMEOUT, cleanup_total_timeout_seconds=CLEANUP_TIMEOUT,
        inherited_common_mutex=True, common_mutex_inode=held.st_ino,
        stop_signals=[], cleanup_errors=[], monitor_errors=[], monitor_processes=0,
        exit_status=None, final_exit_status=None, direct_child_reaped=False,
        stdout_path=str(output/(name+'.stdout')), stderr_path=str(output/(name+'.stderr')))
    process = None
    failure = None
    try:
        kernel = kernel if kernel is not None else Kernel()
        with Path(detail['stdout_path']).open('xb') as stdout, Path(detail['stderr_path']).open('xb') as stderr:
            deadline = time.monotonic()+timeout

            def remaining_time():
                remaining = deadline-time.monotonic()
                require(remaining > 0, 'Vendor SDK generation deadline expired')
                return remaining

            # Register ownership before a handled stop can interrupt launch.
            # The child restores the prior mask before executing the runtime.
            with atomic() as mask:
                def child_setup():
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
                process = subprocess.Popen(command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=True, pass_fds=(common_fd,),
                    preexec_fn=child_setup)
                detail.update(pid=process.pid, pgid=process.pid)
                new_json(output/(name+'-started.json'), detail)
            detail['identity'] = owned_identity(kernel, process)
            while True:
                remaining_time()
                identity = owned_identity(kernel, process, detail['identity'])
                detail['monitor_processes'] += 1
                try:
                    group = members(process.pid, timeout=min(MONITOR_TIMEOUT, remaining_time()))
                except BaseException as error:
                    detail['monitor_errors'].append(str(error) or type(error).__name__)
                    raise
                detail['remaining_process_group'] = group
                if identity['status'] == 5:
                    detail['leader_identity_before_reap'] = identity
                    require(not group, 'Vendor SDK leader exited with live descendants')
                    break
                time.sleep(min(0.05, remaining_time()))
            # A signal between waitpid and returncode assignment must not make
            # a released numeric PID appear to still belong to this child.
            with atomic():
                detail['exit_status'] = process.wait(timeout=remaining_time())
            require(detail['exit_status'] == 0, 'Vendor SDK command exited abnormally')
    except BaseException as error:
        failure = error
        detail.update(error=str(error) or type(error).__name__, error_type=type(error).__name__)
    finally:
        with atomic():
            if process is not None and process.returncode is None:
                cleanup_owned(process, detail)
            if process is not None:
                detail.update(final_exit_status=process.returncode, direct_child_reaped=process.returncode is not None)
            detail['finished_at'] = datetime.now(timezone.utc).isoformat()
            new_json(output/(name+'.json'), detail)
    if failure is not None:
        raise failure
    require(not detail['cleanup_errors'] and detail['direct_child_reaped'], 'Vendor SDK process cleanup incomplete')
    return dict(detail=detail)
