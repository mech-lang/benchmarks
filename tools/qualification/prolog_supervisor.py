"""Bound the parent side of the frozen sampler without changing native timing."""
import ctypes
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import time
import types


class SupervisorDeadlineError(RuntimeError):
    pass


class OwnedCleanupError(RuntimeError):
    pass


@contextmanager
def lifecycle_atomic():
    mask = signal.pthread_sigmask(signal.SIG_BLOCK,
        {signal.SIGALRM,signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK,mask)


class BSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]
    _fields_ += [('comm',ctypes.c_char*16),('name',ctypes.c_char*32)]
    _fields_ += [(name,ctypes.c_uint32) for name in ('nfiles','pgid','jobc','tdev','tpgid')]
    _fields_ += [('nice',ctypes.c_int32),('birth_seconds',ctypes.c_uint64),('birth_microseconds',ctypes.c_uint64)]


class Kernel:
    """Read kernel process identities directly; no ps subprocess can stall cleanup."""
    def __init__(self):
        self.library = ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
        self.library.proc_pidinfo.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        self.library.proc_pidinfo.restype = ctypes.c_int
        self.library.proc_listallpids.argtypes = [ctypes.c_void_p,ctypes.c_int]
        self.library.proc_listallpids.restype = ctypes.c_int
        assert ctypes.sizeof(BSDInfo) == 136

    def identity(self,pid):
        info = BSDInfo()
        if self.library.proc_pidinfo(pid,3,0,ctypes.byref(info),ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        assert info.pid == pid and info.birth_seconds > 0
        return {name:getattr(info,name) for name in
                ('pid','ppid','pgid','status','birth_seconds','birth_microseconds')}

    def group_members(self,pgid):
        capacity = self.library.proc_listallpids(None,0)+256
        assert capacity > 0
        buffer = (ctypes.c_int*capacity)()
        count = self.library.proc_listallpids(buffer,ctypes.sizeof(buffer))
        assert 0 <= count < capacity, 'Process inventory overflow or failure'
        return [row for pid in buffer[:count] if pid > 0 and (row := self.identity(pid))
                and row['pgid'] == pgid and row['status'] != 5]


def same_birth(left,right):
    return left and right and all(left[key] == right[key] for key in ('pid','birth_seconds','birth_microseconds'))


class Owner:
    def __init__(self,kernel=None):
        self.kernel = kernel if kernel is not None else Kernel()
        self.children = {}; self.groups = {}; self.events = []; self.signals = []
        self.pipe_fds = set(); self.read_fds = set(); self.buffers = {}; self.closed_groups = set()

    def identity(self,pid):
        return self.kernel.identity(pid)

    def pipe(self):
        with lifecycle_atomic():
            read,write = os.pipe(); self.pipe_fds.update((read,write)); self.read_fds.add(read)
            self.buffers[read] = b''
        return read,write

    def close(self,fd):
        with lifecycle_atomic():
            os.close(fd); self.pipe_fds.discard(fd)

    def fork(self):
        with lifecycle_atomic():
            child = os.fork()
            if child:
                self.children[child] = dict(identity=None,reaped=False)
                self.groups[child] = None
                self.children[child]['identity'] = self.groups[child] = self.identity(child)
        return child

    def read(self,fd,size):
        with lifecycle_atomic():
            raw = os.read(fd,size)
            if fd in self.read_fds:
                self.buffers[fd] += raw
                while b'\n' in self.buffers[fd]:
                    line,self.buffers[fd] = self.buffers[fd].split(b'\n',1)
                    event = json.loads(line)
                    if event.get('type') == 'native-group-started':
                        pid = event['pid']
                        assert type(pid) is int and pid > 0 and event['pgid'] == pid
                        assert event['inherited_common_mutex'] is True
                        assert pid not in self.groups, 'Duplicate native registration'
                        self.groups[pid] = None
                        self.events.append(event)
                        self.groups[pid] = self.identity(pid)
        return raw

    def waitpid(self,pid,options):
        assert pid in self.children and not self.children[pid]['reaped']
        deadline = time.monotonic()+3
        while True:
            with lifecycle_atomic():
                result = os.waitpid(pid,options | os.WNOHANG)
                if result[0]:
                    self.children[pid]['reaped'] = True
                    return result
            if options & os.WNOHANG:
                return result
            if time.monotonic() >= deadline:
                raise OwnedCleanupError('Owned sampler did not exit within three seconds after SIGKILL')
            time.sleep(0.01)

    def kill(self,pid,signum):
        assert pid in self.children and not self.children[pid]['reaped'], 'Not an unreaped owned child'
        # An unreaped direct child retains its PID even after exit.
        try: os.kill(pid,signum)
        except ProcessLookupError: return
        self.signals.append(dict(kind='direct-child',pid=pid,signal=signum))

    def group_members(self,pgid):
        assert pgid in self.groups, 'Group was not created by this attempt'
        members = self.kernel.group_members(pgid)
        if not members:
            self.closed_groups.add(pgid)
        return members

    def kill_group(self,pgid):
        members = self.group_members(pgid)
        if not members:
            return
        assert pgid not in self.closed_groups, 'Previously empty group identifier was reused'
        current = self.identity(pgid)
        if current is not None:
            assert same_birth(self.groups[pgid],current), 'Owned group leader identity changed'
        # A surviving group retains the ID of its original, possibly reaped,
        # leader. Only groups registered by this fork/launch may reach here.
        try: os.killpg(pgid,signal.SIGKILL)
        except ProcessLookupError: pass
        self.signals.append(dict(kind='owned-group',pgid=pgid,signal=int(signal.SIGKILL)))
        deadline = time.monotonic()+3
        while self.group_members(pgid):
            if time.monotonic() >= deadline:
                raise OwnedCleanupError('Owned process group remains after bounded cleanup')
            time.sleep(0.01)

    def cleanup(self):
        errors = []
        # Drain registrations before any signal; a stopped sampler may have
        # written its authoritative native group immediately before interruption.
        for fd in self.read_fds & self.pipe_fds:
            try:
                while self.read(fd,4096): pass
            except BlockingIOError: pass
            except BaseException as error: errors.append(str(error) or type(error).__name__)
        for pid in self.children:
            if not self.children[pid]['reaped']:
                try: self.kill(pid,signal.SIGKILL)
                except BaseException as error: errors.append(str(error) or type(error).__name__)
        for pgid in self.groups:
            try: self.kill_group(pgid)
            except BaseException as error: errors.append(str(error) or type(error).__name__)
        for pid in self.children:
            if not self.children[pid]['reaped']:
                try: self.waitpid(pid,0)
                except BaseException as error: errors.append(str(error) or type(error).__name__)
        for fd in list(self.pipe_fds):
            try: self.close(fd)
            except BaseException as error: errors.append(str(error) or type(error).__name__)
        return errors

    def __getattr__(self,name):
        return getattr(os,name)


class Harness:
    def __init__(self,original,owner):
        self.original,self.owner = original,owner

    def group_members(self,pgid): return self.owner.group_members(pgid)
    def kill_group(self,pgid): return self.owner.kill_group(pgid)
    def __getattr__(self,name): return getattr(self.original,name)


def one_attempt(guard,harness,row,manifest,report,round_index,lock_fd,owner_factory=Owner):
    owner = owner_factory()
    index = len(report['attempts'])+1
    path = guard.OUT/'outer-supervisor'/f'{index:03d}-{row["id"]}.json'
    record = dict(status='running',deadline_seconds=manifest['supervisor_timeout_seconds'],
                  native_timeout_seconds=manifest['timeout_seconds'],common_mutex_fd=lock_fd,
                  common_mutex_held_through_cleanup=True,native_execute_unchanged=True,
                  native_validation_unchanged=True,deadline_expired=False)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0,0.0), 'Unexpected existing supervisor alarm'
    previous = signal.getsignal(signal.SIGALRM)
    namespace = dict(guard.one_attempt.__globals__)
    def original_sampler(proxy,*arguments):
        # The forked sampler receives its original harness, including the
        # unchanged execute, validators, resource monitor and cleanup functions.
        return guard.sampler(proxy.original,*arguments)
    namespace.update(os=owner,identity=owner.identity,sampler=original_sampler)
    operation = types.FunctionType(guard.one_attempt.__code__,namespace,
                                  guard.one_attempt.__name__,guard.one_attempt.__defaults__,guard.one_attempt.__closure__)
    def expired(signum,frame):
        record['deadline_expired'] = True
        raise SupervisorDeadlineError('Independent sampler supervisor deadline expired')
    try:
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,manifest['supervisor_timeout_seconds'])
        result = operation(Harness(harness,owner),row,manifest,report,round_index,lock_fd)
        if record['deadline_expired']:
            raise SupervisorDeadlineError('Supervisor deadline was caught inside the frozen guard')
        record['status'] = 'returned'
        return result
    except BaseException as error:
        record.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        cleanup = owner.cleanup()
        signal.signal(signal.SIGALRM,previous)
        record.update(owned_sampler_children=owner.children,native_registrations=owner.events,
                      owned_groups=owner.groups,signals=owner.signals,cleanup_errors=cleanup)
        if cleanup:
            record['status'] = 'failed-owned-cleanup'
        guard.save(path,record)
        report.setdefault('independent_supervisors',[]).append(dict(path=str(path),sha256=guard.sha(path),status=record['status']))
        if cleanup:
            raise OwnedCleanupError('Independent cleanup failed; ownership evidence retained')
