"""Bound one direct debugger/helper launch under the benchmark serialization lock."""
import ctypes
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
LOCK = Path('/tmp/mech-clbg-timing.lock')
HELPER = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/julia-aot-comparison/20261012/jobs/generic-attach-calibration-v1/build/generic-helper')
LLDB = Path('/Library/Developer/CommandLineTools/usr/bin/lldb')
PINS = {HELPER: 'd73d21f1772ecdda84659e82a33761694f09b438e8a6dc7d4517994b72b472b0',
        LLDB: 'cf8f665b6c5b2007c958c7acdf5245f2595b50e4d251a48afc191bfb6699d44c'}


class BSDInfo(ctypes.Structure):
    _fields_ = [(key, ctypes.c_uint32) for key in ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]
    _fields_ += [('comm', ctypes.c_char*16), ('name', ctypes.c_char*32)]
    _fields_ += [(key, ctypes.c_uint32) for key in ('nfiles','pgid','jobc','tdev','tpgid')]
    _fields_ += [('nice',ctypes.c_int32), ('birth_seconds',ctypes.c_uint64), ('birth_microseconds',ctypes.c_uint64)]


LIB = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
LIB.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
LIB.proc_pidinfo.restype = ctypes.c_int
LIB.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
LIB.proc_listallpids.restype = ctypes.c_int


def identity(pid):
    info = BSDInfo()
    if LIB.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info)) != ctypes.sizeof(info):
        return None
    assert info.pid == pid and info.birth_seconds > 0
    return {key: getattr(info, key) for key in ('pid','ppid','pgid','status','birth_seconds','birth_microseconds')}


def same(left, right):
    return left and right and all(left[key] == right[key] for key in ('pid','birth_seconds','birth_microseconds'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def no_core():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def main():
    with LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        held = os.fstat(lock.fileno()); named = LOCK.stat()
        assert (held.st_dev,held.st_ino) == (named.st_dev,named.st_ino) and held.st_ino == 79859134
        assert ctypes.sizeof(BSDInfo) == 136
        assert identity(os.getpid())['pid'] == os.getpid()
        for path, digest in PINS.items():
            assert sha(path) == digest, str(path)
        output = HERE/'result'; output.mkdir()
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', HOME='/Users/cim310', LANG='C', LC_ALL='C',
                           PYTHONDONTWRITEBYTECODE='1', LLDB_DEBUGSERVER_LOG_FILE=str(output/'debugserver.log'),
                           LLDB_DEBUGSERVER_LOG_FLAGS='0xffffffff')
        request = dict(output=str(output), executable=str(HELPER), arguments=['--run','direct-launch-aslr-v1'],
                       cwd=str(HELPER.parent), target_environment={key:environment[key] for key in ('PATH','HOME','LANG','LC_ALL')},
                       lock=str(LOCK),lock_fd=lock.fileno())
        save(output/'request.json', request)
        command = [str(LLDB), '--no-lldbinit', '--batch',
                   '-o','command script import '+str(HERE/'observer.py'),
                   '-o','script observer.observe(lldb.debugger, '+repr(str(output/'request.json'))+')']
        report = dict(status='running', started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      command=command, environment=environment, cwd=str(HERE), common_mutex=str(LOCK),
                      common_mutex_inode=held.st_ino, exclusive_common_mutex=True,
                      native_launch_timeout_seconds=25, cleanup_timeout_seconds=4,
                      actual_benchmark_runs=0, Julia_runs=0, permission_changes=0, automatic_retry=False,
                      pins={str(path):digest for path,digest in PINS.items()}, owned_processes=[], signals=[])
        report['controller_sha256'] = sha(Path(__file__))
        report['observer_sha256'] = sha(HERE/'observer.py')
        save(output/'report.json', report)
        process = None; owned = {}; root_id = None
        def collect():
            capacity = LIB.proc_listallpids(None,0)+128
            buffer = (ctypes.c_int*capacity)()
            count = LIB.proc_listallpids(buffer,ctypes.sizeof(buffer)); assert 0 <= count <= capacity
            rows = {pid:info for pid in buffer[:count] if pid > 0 and (info := identity(pid))}
            changed = True
            while changed:
                changed = False
                for pid, info in rows.items():
                    parent = info['ppid']
                    if pid not in owned and parent in owned and same(owned[parent], rows.get(parent)):
                        owned[pid] = info; changed = True
            report['owned_processes'] = list(owned.values())
            return [info for pid, saved in owned.items() if (info := rows.get(pid)) and same(saved,info) and info['status'] != 5]
        try:
            with (output/'lldb.stdout').open('xb') as stdout, (output/'lldb.stderr').open('xb') as stderr:
                process = subprocess.Popen(command, cwd=HERE, env=environment, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=True, pass_fds=(lock.fileno(),), preexec_fn=no_core)
                root_id = identity(process.pid); assert root_id and root_id['pgid'] == process.pid
                owned[process.pid] = root_id; report['owned_lldb'] = root_id
                deadline = time.monotonic()+25
                while process.poll() is None and time.monotonic() < deadline:
                    collect(); time.sleep(0.05)
                report['timeout'] = process.poll() is None
                report['status'] = 'timed-out' if report['timeout'] else 'debugger-returned'
        except BaseException as error:
            report.update(status='failed-supervisor',error=str(error) or type(error).__name__)
            (output/'supervisor-failure.log').write_text(traceback.format_exc())
        finally:
            if process is not None:
                live = collect()
                # Exact kernel birth identity plus observed descendant relation gates every signal.
                # The direct unreaped session leader additionally owns its process group.
                if process.poll() is None and same(root_id,identity(process.pid)):
                    assert os.getpgid(process.pid) == process.pid
                    os.killpg(process.pid, signal.SIGKILL)
                    report['signals'].append(dict(kind='owned-session-group',pgid=process.pid,signal='SIGKILL'))
                for info in reversed(live):
                    if info['pid'] != process.pid and same(info,identity(info['pid'])):
                        try: os.kill(info['pid'],signal.SIGKILL)
                        except ProcessLookupError: continue
                        report['signals'].append(dict(kind='owned-descendant',identity=info,signal='SIGKILL'))
                process.wait(timeout=2); report['lldb_exit_status'] = process.returncode
                deadline = time.monotonic()+2
                while (live := collect()) and time.monotonic() < deadline:
                    time.sleep(0.05)
                report['remaining_owned_processes'] = live
            report['pins_unchanged_at_end'] = all(sha(path) == digest for path,digest in PINS.items())
            report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report['output_sha256'] = {path.name:sha(path) for path in output.iterdir() if path.is_file() and path.name != 'report.json'}
            save(output/'report.json', report)
        print(json.dumps({key:report[key] for key in ('status','lldb_exit_status','timeout','remaining_owned_processes','pins_unchanged_at_end')}))


if __name__ == '__main__':
    main()
