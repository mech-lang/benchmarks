"""One generic direct launch; no Julia, expressions, or benchmark execution."""
import json
import os
from pathlib import Path
import time
import traceback
import lldb


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def observe(debugger, request_path):
    request = json.loads(Path(request_path).read_text()); output = Path(request['output'])
    held = os.fstat(request['lock_fd']); named = os.stat(request['lock'])
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
    report = dict(status='failed', actual_benchmark_runs=0, Julia_runs=0,
                  target_expressions=0, permission_changes=0, events=[], settings=[])
    process = target = None
    debugger.SetAsync(True)
    try:
        for command in ('settings set target.disable-aslr false',
                        'settings set target.skip-prologue false',
                        'settings set target.inherit-env false',
                        'log enable -f ' + str(output/'gdb-remote.log') + ' gdb-remote packets process',
                        'log enable -f ' + str(output/'lldb-process.log') + ' lldb process',
                        'settings show target.disable-aslr target.skip-prologue target.inherit-env'):
            result = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(command, result)
            report['settings'].append(dict(command=command, succeeded=result.Succeeded(),
                                           stdout=result.GetOutput(), stderr=result.GetError()))
            assert result.Succeeded(), result.GetError()
        target = debugger.CreateTarget(request['executable']); assert target.IsValid()
        points = []
        for name in ('main', 'calibration_probe'):
            point = target.BreakpointCreateByName(name)
            assert point.IsValid() and point.GetNumLocations() > 0
            points.append(dict(name=name, id=point.GetID(), locations=point.GetNumLocations()))
        launch = lldb.SBLaunchInfo(request['arguments'])
        flags = (launch.GetLaunchFlags() & ~lldb.eLaunchFlagDisableASLR) | lldb.eLaunchFlagStopAtEntry
        launch.SetLaunchFlags(flags)
        launch.SetDetachOnError(False)
        launch.SetWorkingDirectory(request['cwd'])
        launch.SetEnvironmentEntries([key+'='+value for key, value in request['target_environment'].items()], False)
        for fd, path, read, write in ((0, '/dev/null', True, False),
                                     (1, str(output/'native.stdout'), False, True),
                                     (2, str(output/'native.stderr'), False, True)):
            assert launch.AddOpenFileAction(fd, path, read, write)
        save(output/'launch-entered.json', dict(flags=flags, disable_aslr=bool(flags & lldb.eLaunchFlagDisableASLR),
             stop_at_entry=bool(flags & lldb.eLaunchFlagStopAtEntry), breakpoints=points, settings=report['settings']))
        error = lldb.SBError(); process = target.Launch(launch, error)
        save(output/'launch-returned.json', dict(success=error.Success(), error=str(error),
             process_valid=process.IsValid(), pid=process.GetProcessID(), state=process.GetState()))
        assert error.Success() and process.IsValid(), str(error)
        report['pid'] = process.GetProcessID()
        listener = debugger.GetListener(); last_stop = None; names = []
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            state = process.GetState()
            if state == lldb.eStateExited:
                report['exit_status'] = process.GetExitStatus(); break
            assert state not in (lldb.eStateDetached, lldb.eStateInvalid, lldb.eStateCrashed, lldb.eStateSuspended), state
            if state == lldb.eStateStopped and process.GetStopID() != last_stop:
                last_stop = process.GetStopID(); assert len(report['events']) < 16
                row = dict(stop_id=last_stop, threads=[])
                for thread in process:
                    frame = thread.GetFrameAtIndex(0); module = frame.GetModule()
                    name = frame.GetFunctionName(); path = str(module.GetFileSpec()) if module.IsValid() else None
                    reason = thread.GetStopReason()
                    row['threads'].append(dict(id=thread.GetThreadID(), reason=reason, function=name, module=path))
                    if reason == lldb.eStopReasonBreakpoint and path and Path(path).resolve() == Path(request['executable']).resolve():
                        names.append(name)
                report['events'].append(row)
                with (output/'events.jsonl').open('a') as stream:
                    stream.write(json.dumps(row)+'\n'); stream.flush(); os.fsync(stream.fileno())
                continued = process.Continue(); assert continued.Success(), str(continued)
            event = lldb.SBEvent(); listener.WaitForEvent(1, event)
        else:
            raise TimeoutError('Generic helper event loop exceeded fifteen seconds')
        assert report.get('exit_status') == 0
        assert 'main' in names and 'calibration_probe' in names, names
        report.update(status='generic-direct-launch-observed', helper_function_stops=names)
    except BaseException as error:
        report.update(error=str(error) or type(error).__name__, error_type=type(error).__name__)
        (output/'observer-failure.log').write_text(traceback.format_exc())
    finally:
        if process is not None and process.IsValid() and process.GetState() not in (lldb.eStateExited, lldb.eStateInvalid):
            report['kill_result'] = str(process.Kill())
        if target is not None and target.IsValid():
            report['target_deleted'] = debugger.DeleteTarget(target)
        save(output/'observer-report.json', report)
    print(json.dumps(dict(status=report['status'], output=str(output))), flush=True)
