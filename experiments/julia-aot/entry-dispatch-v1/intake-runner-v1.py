"""Two authorized tool observations; never launch or attach a Julia process."""
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
OUT = HERE/'intake-run-v1'
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
    pin(DEBUGSERVER)
    draft_sha = pin(HERE/'plan-draft.json'); trace_sha = pin(HERE/'trace.py')
    probe_sha = pin(HERE/'intake_probe.py')
    draft = json.loads((HERE/'plan-draft.json').read_bytes())
    pin(draft['subject']['path'], draft['subject']['sha256'])
    runtime = draft['retained_runtime']
    for path_key, sha_key in [('path','sha256'),('matching_dwarf_path','matching_dwarf_sha256'),
                              ('matching_header_path','matching_header_sha256')]:
        pin(runtime[path_key],runtime[sha_key])
    pin(E/draft['prerequisite']['path'],draft['prerequisite']['sha256'])
    OUT.mkdir(mode=0o700)
    commands_file = OUT/'static-api.lldb'
    script = ('script import hashlib, os, sys, types; '
        + 'p='+repr(str(HERE/'intake_probe.py'))+'; b=open(p,"rb").read(); '
        + 'assert hashlib.sha256(b).hexdigest()=='+repr(probe_sha)+'; '
        + 'm=types.ModuleType("julia_entry_static_intake"); m.__file__=p; exec(compile(b,p,"exec"),m.__dict__); '
        + 's=m.entry(lldb.debugger,'+repr(draft_sha)+','+repr(trace_sha)+'); '
        + 'sys.stdout.flush(); sys.stderr.flush(); os._exit(s)\n')
    write(commands_file,script.encode()); pin(commands_file)
    plan = dict(schema='julia-entry-two-tool-intake-plan-v1', subject_executions=0,
        commands=[[str(DEBUGSERVER),'--help'],[str(LLDB),'--no-lldbinit','--batch','--source',str(commands_file)]],
        observer_sha256=OBSERVER_SHA, process_timeout_seconds=30, cleanup_timeout_seconds=5,
        process_group_rss_limit_bytes=2*1024**3, stream_limit_bytes=8*1024**2,
        inherited_mutex_fd=lock.fileno(), common_mutex_inode=79859134, pins=dict(pins), resolutions=dict(resolutions))
    write(OUT/'plan.json',encoded(plan)); pin(OUT/'plan.json')
    report = dict(schema='julia-entry-two-tool-intake-results-v1', status='running',
        started_at=datetime.now(timezone.utc).isoformat(), controller_pid=os.getpid(),
        subject_executions=0, benchmark_samples=0, commands=[], native_owner_qualified=False,
        runtime_aot_proven=False, timing_qualified=False, chart_admission=False)
    kernel = kb.Kernel()
    for index, command in enumerate(plan['commands']):
        directory = OUT/('00-debugserver-help' if index == 0 else '01-static-api')
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
        final = json.loads((directory/'process.json').read_bytes())
        require(final['direct_child_reaped'] is True and final['cleanup_errors'] == []
                and not final.get('artifact_errors') and final.get('remaining_after_cleanup',[]) == []
                and final.get('remaining_process_group',[]) == [], 'Tool cleanup not proven')
        require(kernel.identity(item['pid']) is None and kernel.group(item['pid']) == [], 'Tool process/group remains')
        item['process'] = final
        kb.save(OUT/'progress.json',report)
    verify(); kb.kh.verify_lock(lock)
    artifacts = {str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(OUT.rglob('*')) if p.is_file()}
    report.update(status='two-tool-observations-closed-awaiting-intake-review',
        finished_at=datetime.now(timezone.utc).isoformat(), input_pins=pins,
        input_resolutions=resolutions, artifacts=artifacts, common_mutex_held_through_closure=True,
        all_owned_processes_absent=True, all_owned_groups_empty=True)
    write(OUT/'report.json',encoded(report))
    for name, expected in artifacts.items():
        require(sha(OUT/name) == expected['sha256'], 'Final output changed')
    verify(); kb.kh.verify_lock(lock)
    print(json.dumps(dict(status=report['status'], report=str(OUT/'report.json'),
        report_sha256=sha(OUT/'report.json'), processes=[x['pid'] for x in report['commands']],subject_executions=0)))
