"""Unexecuted Darwin ownership component for the input-1 LLDB diagnostic.

The reviewed caller supplies the exact pinned Kernel and atomic from
kotlin_bounded_v2, a held common lock, a pin/lock check, and exclusive raw files.
This module never discovers or attaches to an existing unowned subject.
"""
import ctypes
import os
import resource
import signal
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Child:
    def __init__(self, role):
        self.role = role
        # This slot is registered in the persistent journal before posix_spawn.
        self.pid_slot = ctypes.c_int(0)
        self.process = None
        self.spawned = False
        self.identity = None
        self.reaped = False
        self.exit_status = None
        self.parent_observations = []

    @property
    def pid(self):
        return self.process.pid if self.process is not None else self.pid_slot.value


class SuspendedSpawn:
    """SDK spawn.h ABI; construction and use are deferred until native release."""
    def __init__(self):
        require(sys.platform == 'darwin' and ctypes.sizeof(ctypes.c_void_p) == 8,
                'Only the retained 64-bit Darwin spawn ABI is supported')
        self.lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
        pointer = ctypes.POINTER(ctypes.c_void_p)
        declarations = {
            'posix_spawnattr_init': [pointer],
            'posix_spawnattr_destroy': [pointer],
            'posix_spawnattr_setflags': [pointer, ctypes.c_short],
            'posix_spawnattr_setpgroup': [pointer, ctypes.c_int],
            'posix_spawnattr_setsigmask': [pointer, ctypes.POINTER(ctypes.c_uint32)],
            'posix_spawnattr_setsigdefault': [pointer, ctypes.POINTER(ctypes.c_uint32)],
            'posix_spawn_file_actions_init': [pointer],
            'posix_spawn_file_actions_destroy': [pointer],
            'posix_spawn_file_actions_adddup2': [pointer, ctypes.c_int, ctypes.c_int],
            'posix_spawn_file_actions_addinherit_np': [pointer, ctypes.c_int],
            'posix_spawn_file_actions_addchdir_np': [pointer, ctypes.c_char_p],
            'posix_spawn': [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, pointer,
                            pointer, ctypes.POINTER(ctypes.c_char_p),
                            ctypes.POINTER(ctypes.c_char_p)],
        }
        for name, arguments in declarations.items():
            function = getattr(self.lib, name)
            function.argtypes, function.restype = arguments, ctypes.c_int

    def call(self, name, *args):
        result = getattr(self.lib, name)(*args)
        if result:
            raise OSError(result, name+': '+os.strerror(result))

    def spawn(self, child, executable, environment, cwd, streams, mutex_fd):
        require(len(streams) == 3 and mutex_fd >= 3, 'Explicit stdio and mutex FD required')
        args = [os.fsencode(executable), b'1']
        env = [os.fsencode(key+'='+value) for key, value in sorted(environment.items())]
        require(all(b'\0' not in item for item in args+env), 'NUL in process configuration')
        argv = (ctypes.c_char_p*(len(args)+1))(*args, None)
        envp = (ctypes.c_char_p*(len(env)+1))(*env, None)
        attr, actions = ctypes.c_void_p(), ctypes.c_void_p()
        attr_ready = actions_ready = False
        try:
            self.call('posix_spawnattr_init', ctypes.byref(attr)); attr_ready = True
            self.call('posix_spawn_file_actions_init', ctypes.byref(actions)); actions_ready = True
            # Retained SDK sys/spawn.h: SETPGROUP|SETSIGDEF|SETSIGMASK|
            # START_SUSPENDED|CLOEXEC_DEFAULT. No ASLR or runtime-policy change.
            self.call('posix_spawnattr_setflags', ctypes.byref(attr), 0x0002|0x0004|0x0008|0x0080|0x4000)
            self.call('posix_spawnattr_setpgroup', ctypes.byref(attr), 0)
            empty, defaults = ctypes.c_uint32(0), ctypes.c_uint32(0xffffffff)
            self.call('posix_spawnattr_setsigmask', ctypes.byref(attr), ctypes.byref(empty))
            self.call('posix_spawnattr_setsigdefault', ctypes.byref(attr), ctypes.byref(defaults))
            self.call('posix_spawn_file_actions_addchdir_np', ctypes.byref(actions), os.fsencode(cwd))
            for destination, stream in enumerate(streams):
                self.call('posix_spawn_file_actions_adddup2', ctypes.byref(actions), stream.fileno(), destination)
            self.call('posix_spawn_file_actions_addinherit_np', ctypes.byref(actions), mutex_fd)
            self.call('posix_spawn', ctypes.byref(child.pid_slot), args[0],
                      ctypes.byref(actions), ctypes.byref(attr), argv, envp)
            child.spawned = True
        finally:
            # The caller's journal already owns child.pid_slot if spawn returned.
            errors = []
            for ready, name, value in (
                    (actions_ready, 'posix_spawn_file_actions_destroy', actions),
                    (attr_ready, 'posix_spawnattr_destroy', attr)):
                if ready:
                    result = getattr(self.lib, name)(ctypes.byref(value))
                    if result:
                        errors.append(name+': '+os.strerror(result))
            require(not errors, '; '.join(errors))


class OwnedProcesses:
    """One subject plus explicit debugserver/client children; no opaque launch."""
    def __init__(self, kernel, atomic, lock, verify_inputs, verify_lock, emit, deadline):
        self.kernel, self.atomic, self.lock = kernel, atomic, lock
        self.verify_inputs, self.emit, self.deadline = verify_inputs, emit, deadline
        self.verify_lock = verify_lock
        self.children = []
        self.peak_rss = None
        self.monitor_samples = 0

    def register_identity(self, child, initially_stopped=False):
        identity = self.kernel.identity(child.pid)
        require(identity is not None and identity['pid'] == child.pid
                and identity['ppid'] == os.getpid() and identity['pgid'] == child.pid,
                'Missing direct-child birth/group identity: '+child.role)
        if initially_stopped:
            require(identity['status'] == 4, 'Subject was not kernel-stopped before debugger attachment')
        child.identity = identity
        child.parent_observations.append(identity['ppid'])
        self.emit(dict(kind='owned-child-registered', role=child.role, identity=identity))

    def spawn_target(self, executable, environment, cwd, streams, file_limit):
        require(not self.children, 'The single suspended subject must be created first')
        self.verify_inputs()
        child = Child('subject')
        self.children.append(child)
        spawn = SuspendedSpawn()
        with self.atomic():
            old_core, old_file = resource.getrlimit(resource.RLIMIT_CORE), resource.getrlimit(resource.RLIMIT_FSIZE)
            try:
                require(old_file[1] == resource.RLIM_INFINITY or file_limit <= old_file[1],
                        'Prepared file bound exceeds inherited hard limit')
                resource.setrlimit(resource.RLIMIT_CORE, (0, old_core[1]))
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, old_file[1]))
                spawn.spawn(child, executable, environment, cwd, streams, self.lock.fileno())
                self.register_identity(child, initially_stopped=True)
            finally:
                resource.setrlimit(resource.RLIMIT_FSIZE, old_file)
                resource.setrlimit(resource.RLIMIT_CORE, old_core)
        return child

    def spawn_tool(self, role, argv, environment, cwd, stdout, stderr, file_limit):
        require(role in ('debugserver', 'debugger') and all(c.role != role for c in self.children),
                'Exactly one explicit child per debugger role')
        subject = self.children[0]
        require(subject.role == 'subject' and subject.identity is not None and not subject.reaped,
                'Subject ownership must precede debugger creation')
        if role == 'debugserver':
            require(len(argv) == 3 and os.path.isabs(argv[1])
                    and argv[-1] == '--attach='+str(subject.pid),
                    'Debugserver may attach only to the owned child through the private socket')
        else:
            require(any(c.role == 'debugserver' and c.identity for c in self.children),
                    'Debugserver ownership must precede client creation')
        self.verify_inputs()
        child = Child(role)
        self.children.append(child)
        with self.atomic() as previous_mask:
            def setup():
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
            child.process = subprocess.Popen(argv, cwd=cwd, env=environment,
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                start_new_session=True, pass_fds=(self.lock.fileno(),), preexec_fn=setup)
            child.spawned = True
            self.register_identity(child)
        return child

    def identity(self, child):
        current = self.kernel.identity(child.pid)
        require(current is not None and child.identity is not None,
                'Owned identity unavailable before reap: '+child.role)
        require(all(current[key] == child.identity[key] for key in
                    ('pid', 'pgid', 'birth_seconds', 'birth_microseconds')),
                'Owned birth/group identity changed: '+child.role)
        parents = {os.getpid()}
        if child.role == 'subject':
            # A traced child can be temporarily parented to its owned tracer.
            parents.update(c.pid for c in self.children if c.role == 'debugserver' and not c.reaped)
        require(current['ppid'] in parents, 'Unrecognized owned-child parent transition')
        if current['ppid'] not in child.parent_observations:
            child.parent_observations.append(current['ppid'])
            self.emit(dict(kind='owned-parent-transition', role=child.role, identity=current))
        return current

    def monitor(self, files, rss_limit):
        require(time.monotonic() < self.deadline, 'Owned diagnostic deadline exceeded')
        self.verify_lock()
        live = {}
        for child in self.children:
            if not child.spawned or child.reaped:
                continue
            self.identity(child)
            for identity in self.kernel.group(child.pid):
                live[identity['pid']] = identity
        owners = {child.pid: child for child in self.children if child.spawned and not child.reaped}
        rss = sum(self.resident_bytes(owners.get(identity['pid']), identity)
                  for identity in live.values())
        if live and rss > 0:
            self.peak_rss = max(self.peak_rss or 0, rss)
        self.monitor_samples += 1
        require(rss <= rss_limit, 'Combined owned groups exceeded the RSS bound')
        for path, limit in files:
            info = path.lstat()
            import stat
            require(stat.S_ISREG(info.st_mode) and info.st_size <= limit,
                    'Capture path became nonregular or exceeded its bound: '+str(path))

    def resident_bytes(self, child, identity):
        for attempt in range(3):
            try:
                return self.kernel.resident_bytes(identity)
            except AssertionError as error:
                # The immutable kernel checker also compares PPID. Only the
                # exact known subject's verified root/tracer transition permits
                # a retry, never a missing identity, changed birth, or RSS error.
                if (str(error) != 'Process identity changed during RSS read'
                        or child is None or child.role != 'subject' or attempt == 2):
                    raise
                after = self.identity(child)
                parents = {os.getpid()} | {c.pid for c in self.children
                    if c.role == 'debugserver' and not c.reaped}
                require(identity['ppid'] in parents and after['ppid'] in parents
                        and identity['ppid'] != after['ppid']
                        and all(identity[key] == after[key] for key in
                            ('pid', 'pgid', 'birth_seconds', 'birth_microseconds')),
                        'RSS failure is not a verified owned tracer-parent transition')
                self.emit(dict(kind='rss-parent-transition-retry', before=identity, after=after,
                               attempt=attempt+1))
                identity = after
                require(time.monotonic() < self.deadline, 'Owned diagnostic deadline exceeded')
                time.sleep(0.005)

    def cleanup(self, terminate):
        """Normal closure failures always escalate; the initiating error survives."""
        if terminate:
            return self._cleanup_once(True)
        try:
            return self._cleanup_once(False)
        except BaseException as original:
            try:
                self._cleanup_once(True)
            except BaseException as cleanup_error:
                raise BaseExceptionGroup('Normal closure and forced owned cleanup failed',
                                         [original, cleanup_error])
            raise

    def _cleanup_once(self, terminate):
        """Retain all leaders until groups empty; one bounded cleanup phase."""
        errors = []
        deadline = time.monotonic()+5
        with self.atomic():
            if terminate:
                for child in reversed(self.children):
                    if not child.spawned or child.reaped:
                        continue
                    try:
                        sent = False
                        if child.identity is None:
                            # Failed registration still leaves the un-reaped
                            # direct child owned by this journal. The subject
                            # has never resumed; Popen tools started new sessions.
                            if child.role == 'subject':
                                os.kill(child.pid, signal.SIGKILL)
                            else:
                                require(child.process is not None, 'Missing direct-child Popen ownership')
                                os.killpg(child.pid, signal.SIGKILL)
                            sent = True
                        else:
                            self.identity(child)
                            if self.kernel.group(child.pid):
                                os.killpg(child.pid, signal.SIGKILL)
                                sent = True
                        if sent:
                            self.emit(dict(kind='owned-cleanup-signal', role=child.role,
                                           pid=child.pid, signal=int(signal.SIGKILL)))
                    except ProcessLookupError:
                        pass
                    except BaseException as error:
                        errors.append(child.role+': '+str(error))
            # Reap debugger/server before the subject so tracer parenting has
            # ended. No PID/group is used again after its recorded reap.
            for child in reversed(self.children):
                if not child.spawned or child.reaped:
                    continue
                try:
                    if child.identity is not None:
                        self.identity(child)
                    while self.kernel.group(child.pid):
                        require(time.monotonic() < deadline, 'Owned group survived cleanup deadline')
                        time.sleep(0.01)
                    if child.process is not None:
                        status = child.process.wait(timeout=max(0.001, deadline-time.monotonic()))
                    else:
                        while True:
                            pid, raw_status = os.waitpid(child.pid, os.WNOHANG)
                            if pid:
                                require(pid == child.pid and (os.WIFEXITED(raw_status) or os.WIFSIGNALED(raw_status)),
                                        'Unexpected owned wait status')
                                status = os.waitstatus_to_exitcode(raw_status)
                                break
                            require(time.monotonic() < deadline, 'Owned subject was not reaped')
                            time.sleep(0.01)
                    child.exit_status, child.reaped = status, True
                    self.emit(dict(kind='owned-child-reaped', role=child.role, pid=child.pid, status=status))
                except BaseException as error:
                    errors.append(child.role+': '+str(error))
        require(not errors, '; '.join(errors))
