"""Unexecuted host-output adapter for the unchanged static LLDB intake probe.

Only the outer LLDB command invokes run(). It creates no inferior and performs
no launch, attach, connect, resume, or target expression evaluation.
"""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import stat
import traceback
import types


def write_all(fd, data):
    view = memoryview(data)
    while view:
        try:
            count = os.write(fd, view)
        except InterruptedError:
            continue
        if count <= 0:
            raise OSError('Incomplete direct descriptor write')
        view = view[count:]


def run(debugger, probe_path, probe_sha256, draft_sha256, trace_sha256):
    """Capture the probe's streams before writing to the owned descriptors.

    LLDB replaces sys.stdout with its command-output adapter. A Python flush
    followed by os._exit does not prove that LLDB's remaining output reached the
    parent. This adapter forwards every captured byte through the OS descriptors
    before the caller exits. The frozen observer still bounds time, RSS and files.
    """
    output, errors = io.StringIO(), io.StringIO()
    status = 1
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try:
            path = Path(probe_path)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise ValueError('Regular probe source required')
                source = stream.read(65537)
                after = os.fstat(stream.fileno())
            named = path.lstat()
            fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            if (len(source) > 65536
                    or hashlib.sha256(source).hexdigest() != probe_sha256
                    or any(getattr(before, k) != getattr(after, k)
                           or getattr(before, k) != getattr(named, k) for k in fields)):
                raise ValueError('Pinned probe changed')
            module = types.ModuleType('julia_entry_static_intake')
            module.__file__ = str(path)
            exec(compile(source, str(path), 'exec'), module.__dict__)
            status = module.entry(debugger, draft_sha256, trace_sha256)
            if type(status) is not int or status not in (0, 1):
                raise ValueError('Unexpected static probe status')
        except BaseException:
            traceback.print_exc()
            status = 1
    # The reviewed entry bounds its JSON to 1 MiB; all its actual bytes and error
    # text remain visible. Do not truncate or promote a partial capture.
    write_all(1, output.getvalue().encode('utf-8'))
    write_all(2, errors.getvalue().encode('utf-8'))
    return status


def command_source(transport_path, transport_sha256, probe_path, probe_sha256,
                   draft_sha256, trace_sha256):
    """One LLDB script command with an explicit failure-to-exit boundary."""
    body = '''import hashlib, os, traceback, types
status = 1
try:
    path = TRANSPORT_PATH
    with open(path, 'rb') as source:
        raw = source.read(65537)
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != TRANSPORT_SHA:
        raise ValueError('Pinned transport changed')
    module = types.ModuleType('julia_entry_intake_transport')
    module.__file__ = path
    exec(compile(raw, path, 'exec'), module.__dict__)
    status = module.run(lldb.debugger, PROBE_PATH, PROBE_SHA, DRAFT_SHA, TRACE_SHA)
    if type(status) is not int or status not in (0, 1):
        raise ValueError('Unexpected transport status')
except BaseException:
    status = 1
    pending = memoryview(traceback.format_exc().encode('utf-8'))
    try:
        while pending:
            try:
                count = os.write(2, pending)
            except InterruptedError:
                continue
            if count <= 0:
                raise OSError('Incomplete outer diagnostic write')
            pending = pending[count:]
    except BaseException:
        pass
finally:
    os._exit(status)
'''
    values = dict(TRANSPORT_PATH=transport_path, TRANSPORT_SHA=transport_sha256,
                  PROBE_PATH=probe_path, PROBE_SHA=probe_sha256,
                  DRAFT_SHA=draft_sha256, TRACE_SHA=trace_sha256)
    for name, value in values.items():
        body = body.replace(name, repr(str(value)))
    return 'script exec('+repr(body)+')\n'
