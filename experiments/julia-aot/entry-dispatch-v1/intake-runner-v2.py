"""Unexecuted repair invocation; requires serial-lane release before use.

Two tool observations only. Preserve v1; never launch/attach a Julia process.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import types
from datetime import datetime, timezone

E = Path('/private/tmp/mech-benchmark-completion')
HERE = E/'experiments/julia-aot/entry-dispatch-v1'
OUT = HERE/'intake-run-v2'
TRANSPORT = HERE/'intake-transport-v2/transport.py'
PRIOR_REPORT = HERE/'intake-run-v1/report.json'
PRIOR_REPORT_SHA = '7e5e0c48704a77e25d189af56d4252e9b80d4e1af334b2aff57baf9583b84e4e'
PRIOR_DISPOSITION = HERE/'intake-run-v1/disposition.json'
PRIOR_DISPOSITION_SHA = '1bdad46318de831892b4ba85e3cb7e669ebc326877f787a6ae7faaa0f180d17f'
OBSERVER = E/'tools/qualification/kotlin_bounded_v2.py'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
INVENTORY = Path('/private/tmp/mech-history-candidate-validation/julia-entry-intake-inventory-v1.json')
DEBUGSERVER = Path('/Library/Developer/CommandLineTools/Library/PrivateFrameworks/LLDB.framework/Versions/A/Resources/debugserver')
LLDB = Path('/Library/Developer/CommandLineTools/usr/bin/lldb')
pins, resolutions = {}, {}

def require(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    path = Path(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode), 'Not a regular input: '+str(path))
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    named = path.stat()
    require(all(getattr(before, k) == getattr(opened, k) == getattr(after, k) == getattr(named, k)
                for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')), 'Input changed: '+str(path))
    return result

def pin(path, expected=None):
    path = Path(path)
    result = sha(path)
    require(expected is None or result == expected, 'Recorded input differs: '+str(path))
    require(str(path) not in pins or pins[str(path)] == result, 'Conflicting input')
    pins[str(path)] = result
    resolutions[str(path)] = str(path.resolve(strict=True))
    return result

def verify():
    for name, expected in pins.items():
        require(sha(name) == expected and str(Path(name).resolve(strict=True)) == resolutions[name],
                'Input closure changed: '+name)

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()

def write(path, value):
    with path.open('xb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())

def stopped(number, frame):
    raise KeyboardInterrupt('Stop signal '+str(number))

for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(number, stopped)

with Path('/tmp/mech-clbg-timing.lock').open('rb') as low:
    fd = fcntl.fcntl(low.fileno(), fcntl.F_DUPFD_CLOEXEC, 64)
with os.fdopen(fd, 'rb') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    pin(OBSERVER, OBSERVER_SHA)
    kb = types.ModuleType('julia_entry_intake_observer'); kb.__file__ = str(OBSERVER)
    exec(compile(OBSERVER.read_bytes(), str(OBSERVER), 'exec'), kb.__dict__)
    kb.kh.verify_lock(lock)
    require((kb.TIMEOUT,kb.CLEANUP_TIMEOUT,kb.RSS_LIMIT,kb.FILE_LIMIT) == (30,5,2*1024**3,8*1024**2),
            'Frozen observer limits changed')
    pin(Path(sys.executable), 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e')
    pin(E/'tools/qualification/kotlin_helpers.py', kb.HELPER_CONTROLLER_SHA)
    pin(E/'tools/qualification/elixir_bounded.py', kb.REFERENCE_CONTROLLER_SHA)
    pin(Path(__file__).resolve()); pin(INVENTORY)
    inventory = json.loads(INVENTORY.read_bytes())
    prior = inventory['old_tool_observations']
    for role in ('version','location','scripting_resource_path'):
        for part in ('receipt','stdout'):
            ref = prior[role][part]; pin(E/ref['path'], ref['recorded_sha256'])
    for row in prior['recorded_tool_pins']:
        pin(row['path'], row['recorded_sha256'])
    pin(PRIOR_REPORT, PRIOR_REPORT_SHA); pin(PRIOR_DISPOSITION, PRIOR_DISPOSITION_SHA)
    old_report = json.loads(PRIOR_REPORT.read_bytes())
    pin(DEBUGSERVER, old_report['input_pins'][str(DEBUGSERVER)])
    draft_sha = pin(HERE/'plan-draft.json', 'b44246c20da2faddee25f9fb4c4e01e98d80a8fc8045e3596086437479823702')
    trace_sha = pin(HERE/'trace.py', '865f13a064045c6b3d569b01aacfbc138d32b4d2a24de9a577cc0dd19c03668c')
    probe_sha = pin(HERE/'intake_probe.py', '5edd95e8ae8b5ceee57444050a7e47b8969f862b5ab77f77137edb2af19415b6')
    transport_sha = pin(TRANSPORT)
    transport_raw = TRANSPORT.read_bytes()
    require(hashlib.sha256(transport_raw).hexdigest() == transport_sha, 'Transport source changed')
    transport = types.ModuleType('julia_entry_intake_transport'); transport.__file__ = str(TRANSPORT)
    exec(compile(transport_raw, str(TRANSPORT), 'exec'), transport.__dict__)
    draft = json.loads((HERE/'plan-draft.json').read_bytes())
    pin(draft['subject']['path'], draft['subject']['sha256'])
    runtime = draft['retained_runtime']
    for path_key, sha_key in [('path','sha256'),('matching_dwarf_path','matching_dwarf_sha256'),
                              ('matching_header_path','matching_header_sha256')]:
        pin(runtime[path_key],runtime[sha_key])
    pin(E/draft['prerequisite']['path'],draft['prerequisite']['sha256'])
    OUT.mkdir(mode=0o700)
    commands_file = OUT/'static-api.lldb'
    script = transport.command_source(TRANSPORT, transport_sha, HERE/'intake_probe.py',
                                      probe_sha, draft_sha, trace_sha)
    write(commands_file,script.encode()); pin(commands_file)
    plan = dict(schema='julia-entry-two-tool-intake-plan-v1', subject_executions=0,
        commands=[[str(DEBUGSERVER),'--log-file=stderr'],[str(LLDB),'--no-lldbinit','--batch','--source',str(commands_file)]],
        preserved_prior_failure=dict(report=str(PRIOR_REPORT),report_sha256=PRIOR_REPORT_SHA,
            disposition=str(PRIOR_DISPOSITION),disposition_sha256=PRIOR_DISPOSITION_SHA),
        observer_sha256=OBSERVER_SHA, process_timeout_seconds=30, cleanup_timeout_seconds=5,
        process_group_rss_limit_bytes=2*1024**3, stream_limit_bytes=8*1024**2,
        inherited_mutex_fd=lock.fileno(), common_mutex_inode=79859134, pins=dict(pins), resolutions=dict(resolutions))
    write(OUT/'plan.json',encoded(plan)); pin(OUT/'plan.json')
    report = dict(schema='julia-entry-two-tool-intake-results-v1', status='running',
        started_at=datetime.now(timezone.utc).isoformat(), controller_pid=os.getpid(),
        subject_executions=0, benchmark_samples=0, commands=[], static_api_complete=False,
        preserved_prior_failure=plan['preserved_prior_failure'],
        native_owner_qualified=False, local_debugger_intake_qualified=False,
        runtime_aot_proven=False, timing_qualified=False, chart_admission=False)
    kernel = kb.Kernel()
    validated_artifacts = {str(commands_file.relative_to(OUT)):
        dict(bytes=len(script.encode()),sha256=hashlib.sha256(script.encode()).hexdigest())}
    for index, command in enumerate(plan['commands']):
        directory = OUT/('00-debugserver-usage' if index == 0 else '01-static-api')
        directory.mkdir(mode=0o700)
        for name in ('home','tmp'): (directory/name).mkdir(mode=0o700)
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',
            HOME=str(directory/'home'),TMPDIR=str(directory/'tmp'),
            OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
        item = dict(command=command, directory=str(directory), environment=environment, pid=None)
        report['commands'].append(item)
        def launched(pid):
            item['pid'] = pid
            kb.save(OUT/'progress.json',report)
        kb.kh.verify_lock(lock); verify()
        try:
            kb.observe(command,environment,directory,b'',lock,launched,kind='julia-entry-no-subject-tool-intake',kernel=kernel)
        except Exception as error:
            item['observer_error'] = str(error)
            item['observer_error_type'] = type(error).__name__
        captured = {name:(directory/name).read_bytes() for name in
                    ('start.json','active.json','process.json','stdout.bin','stderr.bin')}
        final = json.loads(captured['process.json'])
        for stream in ('stdout','stderr'):
            require(len(captured[stream+'.bin']) == final[stream+'_bytes']
                    and hashlib.sha256(captured[stream+'.bin']).hexdigest() == final[stream+'_sha256'],
                    'Captured stream differs from closed native receipt: '+stream)
        require(final['direct_child_reaped'] is True and final['cleanup_errors'] == []
                and not final.get('artifact_errors') and final.get('remaining_after_cleanup',[]) == []
                and final.get('remaining_process_group',[]) == [], 'Tool cleanup not proven')
        require(kernel.identity(item['pid']) is None and kernel.group(item['pid']) == [], 'Tool process/group remains')
        item['process'] = final
        if index == 1:
            try:
                require(final['status'] == 'native-passed' and final['exit_status'] == 0,
                        'Static API native command did not pass')
                output = captured['stdout.bin']
                beginning = 0 if output.startswith(b'{\n') else output.index(b'\n{\n')+1
                structured = json.loads(output[beginning:])
                require(structured['schema'] == 'julia-entry-zero-subject-api-observation-v1'
                    and structured['status'] == 'zero-subject-static-api-observation-complete'
                    and structured['subject_executions'] == 0
                    and structured['native_inferior_created'] is False
                    and structured['breakpoints'] == 27
                    and structured['codeinstance_type']['bytes'] == 128,
                    'Incomplete or unexpected static API result')
                require(all(structured[k] is False for k in ('owned_transport_native_verified',
                    'native_owner_qualified','actual_ir_removal_qualified','fallback_closure_qualified',
                    'runtime_aot_proven','timing_qualified','chart_admission')),
                    'Static observation promoted an unobserved gate')
                require(structured['source_pins'] == dict(draft_sha256=draft_sha,trace_sha256=trace_sha)
                    and all(all(members.values()) for members in structured['api_member_presence'].values())
                    and len(structured['settings']) == 2
                    and all(item['succeeded'] is True for item in structured['settings']),
                    'Static source/API/settings evidence differs')
                for path, uuid in ((draft['subject']['path'],'ABB0315D-ABDF-3208-A9E7-97CD2EF84005'),
                                   (runtime['path'],'A9EAD8CA-7573-3B14-8DD6-39BDC818E737')):
                    require(sum(m['path'] == path and m['uuid'] == uuid for m in structured['modules']) == 1,
                            'Final prepared module identity missing or duplicated')
                require(structured['runtime_symbol_file'] == runtime['matching_dwarf_path'],
                        'Final debug-file identity differs')
                observation_raw = encoded(structured)
                write(directory/'observation.json',observation_raw)
                captured['observation.json'] = observation_raw
                report['static_api_complete'] = True
            except Exception as error:
                item['output_contract_error'] = str(error)
                item['output_contract_error_type'] = type(error).__name__
        for name, raw in captured.items():
            validated_artifacts[str((directory/name).relative_to(OUT))] = dict(
                bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        kb.save(OUT/'progress.json',report)
    verify(); kb.kh.verify_lock(lock)
    artifacts = {str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(OUT.rglob('*')) if p.is_file()}
    require(all(artifacts.get(name) == expected for name, expected in validated_artifacts.items()),
            'Validated capture changed before artifact inventory')
    report.update(status=('two-tool-observations-closed-awaiting-intake-review' if report['static_api_complete']
                          else 'two-tool-observations-closed-with-static-output-failure'),
        finished_at=datetime.now(timezone.utc).isoformat(), input_pins=pins,
        input_resolutions=resolutions, artifacts=artifacts, common_mutex_held_through_closure=True,
        all_owned_processes_absent=True, all_owned_groups_empty=True)
    report_raw = encoded(report)
    report_sha = hashlib.sha256(report_raw).hexdigest()
    write(OUT/'report.json',report_raw)
    verify()
    for name, expected in artifacts.items():
        require((OUT/name).stat().st_size == expected['bytes']
                and sha(OUT/name) == expected['sha256'], 'Final output changed')
    require((OUT/'report.json').read_bytes() == report_raw, 'Final serialized report changed')
    kb.kh.verify_lock(lock)
    print(json.dumps(dict(status=report['status'], report=str(OUT/'report.json'),
        report_sha256=report_sha, processes=[x['pid'] for x in report['commands']],subject_executions=0)))
