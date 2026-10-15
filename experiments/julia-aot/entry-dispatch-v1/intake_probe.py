"""Unexecuted LLDB batch probe: inspect APIs and files, never create an inferior.

The owned outer command pins this source, plan-draft.json and trace.py. Call
entry(lldb.debugger, draft_sha256, trace_sha256) and preserve its return status.
This module contains no launch, connect, attach, resume or target evaluation.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import traceback

HERE = Path(__file__).resolve().parent
UUIDS = dict(main='ABB0315D-ABDF-3208-A9E7-97CD2EF84005',
             runtime='A9EAD8CA-7573-3B14-8DD6-39BDC818E737')
SETTINGS = ('settings set target.load-script-from-symbol-file false',
            'settings set symbols.enable-external-lookup false')
API_MEMBERS = {
    'SBTarget': ('ConnectRemote', 'AddModule', 'GetProcess', 'GetBroadcaster',
                 'BreakpointCreateBySBAddress'),
    'SBProcess': ('ReadMemory', 'GetUniqueID', 'GetStopID', 'Continue', 'GetState', 'GetExitStatus'),
    'SBModuleSpec': ('SetFileSpec', 'SetSymbolFileSpec'),
    'SBListener': ('StartListeningForEvents', 'GetNextEvent'),
    'SBModule': ('FindFirstType', 'ResolveFileAddress', 'GetSymbolFileSpec'),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(path, expected):
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'Regular pinned source required')
        value = stream.read(65537)
        after = os.fstat(stream.fileno())
    named = path.lstat()
    require(len(value) <= 65536 and hashlib.sha256(value).hexdigest() == expected
            and all(getattr(before, key) == getattr(after, key) == getattr(named, key)
                for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
            'Pinned source changed or exceeded its bound')
    return value


def probe(debugger, draft_sha256, trace_sha256, result):
    import lldb
    draft = json.loads(checked(HERE/'plan-draft.json', draft_sha256))
    require(draft['prepared'] is False and draft['subject']['arguments'] == ['1'],
            'Only the fixed unprepared diagnostic specification is accepted')
    trace_raw = checked(HERE/'trace.py', trace_sha256)
    spec = importlib.util.spec_from_file_location('julia_entry_intake_trace', HERE/'trace.py')
    trace_module = importlib.util.module_from_spec(spec)
    exec(compile(trace_raw, str(HERE/'trace.py'), 'exec'), trace_module.__dict__)
    events = []
    result.update(schema='julia-entry-zero-subject-api-observation-v1',
        status='incomplete', subject_executions=0, native_inferior_created=False,
        debugger_version=lldb.SBDebugger.GetVersionString(),
        scripting=dict(version=sys.version, executable=sys.executable, prefix=sys.prefix,
                       lldb_wrapper=lldb.__file__),
        source_pins=dict(draft_sha256=draft_sha256, trace_sha256=trace_sha256), events=events)
    members = {name: {member: callable(getattr(getattr(lldb, name, None), member, None))
                     for member in required} for name, required in API_MEMBERS.items()}
    result['api_member_presence'] = members
    require(all(all(found.values()) for found in members.values()), 'Required local Python API member absent')
    result['unexercised_process_methods'] = list(API_MEMBERS['SBProcess'])+['SBTarget.ConnectRemote']
    result['settings'] = []
    for command in SETTINGS:
        observed = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand(command, observed)
        result['settings'].append(dict(command=command, succeeded=observed.Succeeded(),
            stdout=observed.GetOutput(), stderr=observed.GetError()))
        require(observed.Succeeded(), 'Required local debugger setting unavailable')
    debugger.SetAsync(False)
    target = debugger.CreateTarget(draft['subject']['path'])
    require(target.IsValid() and not target.GetProcess().IsValid(),
            'Static intake must have no inferior process')
    main = target.FindModule(lldb.SBFileSpec(draft['subject']['path']))
    module_spec = lldb.SBModuleSpec()
    module_spec.SetFileSpec(lldb.SBFileSpec(draft['retained_runtime']['path']))
    module_spec.SetSymbolFileSpec(lldb.SBFileSpec(draft['retained_runtime']['matching_dwarf_path']))
    runtime = target.AddModule(module_spec)
    require(main.IsValid() and runtime.IsValid(), 'Exact file modules unavailable')
    type_ = runtime.FindFirstType('jl_code_instance_t')
    require(type_.IsValid() and type_.GetNumberOfFields() <= 256,
            'Runtime debug type unavailable or unexpectedly large')
    result['codeinstance_type'] = dict(name=type_.GetName(), bytes=type_.GetByteSize(), raw_fields=[
        dict(name=(field := type_.GetFieldAtIndex(index)).GetName(),
             offset=field.GetOffsetInBytes(), bytes=field.GetType().GetByteSize(),
             type=field.GetType().GetName()) for index in range(type_.GetNumberOfFields())])
    expected = dict(main=dict(path=draft['subject']['path'], uuid=UUIDS['main']),
                    runtime=dict(path=draft['retained_runtime']['path'], uuid=UUIDS['runtime']))
    listener = lldb.SBListener('julia-entry-no-subject-intake')
    mask = lldb.SBTarget.eBroadcastBitModulesLoaded | lldb.SBTarget.eBroadcastBitModulesUnloaded
    accepted = listener.StartListeningForEvents(target.GetBroadcaster(), mask)
    require(accepted & mask == mask, 'Local module-event subscription unavailable')
    trace = trace_module.Trace(lldb, target, dict(main=main, runtime=runtime), expected, events.append)
    result['codeinstance_type']['required_layout'] = trace.ci_layout
    result['modules'] = trace.verify_identity()
    result['runtime_symbol_file'] = runtime.GetSymbolFileSpec().fullpath
    require(result['runtime_symbol_file'] == draft['retained_runtime']['matching_dwarf_path'],
            'LLDB selected a different runtime debug file')
    result['breakpoints'] = len(trace.breakpoints)
    result['module_subscription_mask'] = accepted
    require(not target.GetProcess().IsValid(), 'Static intake unexpectedly acquired an inferior')
    result.update(status='zero-subject-static-api-observation-complete',
        owned_transport_native_verified=False, native_owner_qualified=False,
        actual_ir_removal_qualified=False, fallback_closure_qualified=False,
        runtime_aot_proven=False, timing_qualified=False, chart_admission=False)
    return result


def entry(debugger, draft_sha256, trace_sha256):
    result = {}
    try:
        result = probe(debugger, draft_sha256, trace_sha256, result)
        raw = json.dumps(result, indent=2)+'\n'
        require(len(raw.encode()) <= 1024**2, 'Static API observation exceeds output bound')
        sys.stdout.write(raw); sys.stdout.flush()
        return 0
    except BaseException:
        traceback.print_exc()
        result['status'] = 'zero-subject-api-observation-failed'
        raw = json.dumps(result, indent=2)+'\n'
        if len(raw.encode()) <= 1024**2:
            sys.stdout.write(raw); sys.stdout.flush()
        return 1
