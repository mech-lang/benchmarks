"""Draft LLDB client: connect only to the owner's already stopped target.

Invoked by a separately registered LLDB CLI child with --no-lldbinit. It never
launches a target and never evaluates target expressions. Exact native API and
configuration compatibility remain unexecuted.
"""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import traceback


def require(value, message):
    if not value:
        raise ValueError(message)


def regular_bytes(path, limit):
    descriptor = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Regular owned input required')
        raw = stream.read(limit+1)
    require(len(raw) <= limit, 'Owned input exceeds bound')
    return raw


def run(debugger, config_path, config_sha256):
    import lldb
    config_path = Path(config_path)
    raw = regular_bytes(config_path, 65536)
    require(hashlib.sha256(raw).hexdigest() == config_sha256, 'Owned client configuration changed')
    config = json.loads(raw)
    require(config['subject_arguments'] == ['1'] and type(config['subject_pid']) is int
            and config['subject_pid'] > 0, 'Only the owned input-1 subject is permitted')
    require(config['subject_birth']['pid'] == config['subject_pid'], 'Owned birth record differs')
    require(config['socket_path'].startswith(config['private_socket_directory']+'/'),
            'Endpoint is outside its prepared private directory')
    endpoint_info = Path(config['socket_path']).lstat()
    require(stat.S_ISSOCK(endpoint_info.st_mode)
            and endpoint_info.st_uid == os.getuid()
            and (endpoint_info.st_dev, endpoint_info.st_ino) ==
                (config['socket_identity']['device'], config['socket_identity']['inode']),
            'Owned socket endpoint required')
    directory_info = Path(config['private_socket_directory']).lstat()
    require(stat.S_ISDIR(directory_info.st_mode) and directory_info.st_uid == os.getuid()
            and stat.S_IMODE(directory_info.st_mode) == 0o700
            and (directory_info.st_dev, directory_info.st_ino) ==
                (config['socket_directory_identity']['device'], config['socket_directory_identity']['inode']),
            'Original private debugger directory required')
    trace_path = Path(__file__).with_name('trace.py')
    specification = importlib.util.spec_from_file_location('julia_entry_trace', trace_path)
    trace_module = importlib.util.module_from_spec(specification)
    trace_raw = regular_bytes(trace_path, 65536)
    require(hashlib.sha256(trace_raw).hexdigest() == config['trace_sha256'], 'Prepared trace source changed')
    exec(compile(trace_raw, str(trace_path), 'exec'), trace_module.__dict__)
    event_path = Path(config['events']['path'])
    fd = os.open(event_path, os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW|os.O_NONBLOCK)
    event_info = os.fstat(fd)
    require(stat.S_ISREG(event_info.st_mode) and event_info.st_size == 0
            and event_info.st_dev == config['events']['device']
            and event_info.st_ino == config['events']['inode'], 'Fresh owner-created event file required')
    def emit(event):
        raw = json.dumps(event, sort_keys=True, separators=(',', ':')).encode()+b'\n'
        require(os.fstat(fd).st_size+len(raw) <= config['events']['maximum_bytes'],
                'Diagnostic event byte bound exceeded')
        position = 0
        while position < len(raw):
            count = os.write(fd, raw[position:])
            require(count > 0, 'Incomplete diagnostic event write')
            position += count
        os.fsync(fd)
    process = None
    try:
        # These command names are source-supported settings; local support must
        # be checked before any subject is spawned during eventual preparation.
        for command in ('settings set target.load-script-from-symbol-file false',
                        'settings set symbols.enable-external-lookup false'):
            result = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(command, result)
            require(result.Succeeded(), 'Required debugger setting unavailable: '+command)
            emit(dict(kind='debugger-setting', command=command,
                      stdout=result.GetOutput(), stderr=result.GetError()))
        debugger.SetAsync(False)
        target = debugger.CreateTarget(config['modules']['main']['path'])
        require(target.IsValid(), 'Unable to create exact executable target')
        main = target.FindModule(lldb.SBFileSpec(config['modules']['main']['path']))
        module_spec = lldb.SBModuleSpec()
        module_spec.SetFileSpec(lldb.SBFileSpec(config['modules']['runtime']['path']))
        module_spec.SetSymbolFileSpec(lldb.SBFileSpec(config['runtime_dwarf']))
        runtime = target.AddModule(module_spec)
        require(main.IsValid() and runtime.IsValid(), 'Exact main/runtime modules unavailable')
        listener = lldb.SBListener('julia-entry-owned-events')
        mask = lldb.SBTarget.eBroadcastBitModulesLoaded | lldb.SBTarget.eBroadcastBitModulesUnloaded
        require(listener.StartListeningForEvents(target.GetBroadcaster(), mask) & mask == mask,
                'Unable to subscribe to all target module changes')
        trace = trace_module.Trace(lldb, target, dict(main=main, runtime=runtime),
                                   config['modules'], emit)
        error = lldb.SBError()
        process = target.ConnectRemote(listener, 'unix-connect://'+config['socket_path'],
                                       'gdb-remote', error)
        require(error.Success() and process.IsValid() and process.GetState() == lldb.eStateStopped,
                'Owned remote did not expose a stopped subject')
        trace.bind_owned_process(process, config['subject_pid'], config['subject_birth'])
        emit(dict(kind='initial-owned-stop', pid=process.GetProcessID(),
                  stop_id=process.GetStopID(), thread_stops=[
                      dict(thread_id=thread.GetThreadID(), reason=thread.GetStopReason(),
                           pc=hex(thread.GetFrameAtIndex(0).GetPC())) for thread in process]))
        def drain_events():
            count = 0
            event = lldb.SBEvent()
            while listener.GetNextEvent(event):
                count += 1
                require(count <= 512, 'Debugger event queue exceeded bound')
                if lldb.SBTarget.EventIsTargetEvent(event):
                    trace.module_event(event)
                elif lldb.SBProcess.EventIsProcessEvent(event):
                    emit(dict(kind='process-state-event', state=lldb.SBProcess.GetStateFromEvent(event),
                              restarted=lldb.SBProcess.GetRestartedFromEvent(event)))
                else:
                    raise ValueError('Unknown subscribed debugger event')
        drain_events()
        deadline = time.monotonic()+config['maximum_seconds']
        while True:
            require(time.monotonic() < deadline, 'Client diagnostic deadline exceeded')
            # Synchronous Continue returns at the next actual stop/exit. Queue
            # notifications are retained separately, never counted as visits.
            continued = process.Continue()
            require(continued.Success(), 'Owned target could not continue')
            drain_events()
            if process.GetState() == lldb.eStateExited:
                trace.finished(process)
                require(process.GetExitStatus() == 0, 'Owned target exited unsuccessfully')
                break
            require(process.GetState() == lldb.eStateStopped, 'Unexpected owned process state')
            trace.stopped(process)
        emit(dict(kind='client-complete', target_exit_status=process.GetExitStatus(),
                  semantic_review_qualified=False, timing_qualified=False, chart_admission=False))
    except BaseException as error:
        # The outer owner retains all three children and must kill/reap them;
        # do not detach/resume or create a replacement subject here.
        try:
            emit(dict(kind='client-failed', error_type=type(error).__name__, error=str(error),
                      semantic_review_qualified=False, timing_qualified=False, chart_admission=False))
        except BaseException:
            # A full/failed event sink must not replace the initiating error.
            pass
        raise
    finally:
        os.close(fd)


def entry(debugger, config_path, config_sha256):
    """The owner's fixed LLDB script exits with this status, never auto-resumes."""
    try:
        run(debugger, config_path, config_sha256)
        return 0
    except BaseException:
        traceback.print_exc()
        return 1
