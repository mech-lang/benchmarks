#!/usr/bin/env python3
"""Source draft: prepare or own one input-1 Julia entry diagnostic.

Preparation requires a separately reviewed local debugger intake. This file
does not discover tools, perform capability probes, or qualify fallback/AOT.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
KERNEL = ROOT/'tools/qualification/kotlin_bounded_v2.py'
KERNEL_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
HELPERS = {
    'kotlin_helpers.py': 'd92e0b247d7d45bca1216a0e85335fe0e31a24cc1d607b4b97928115a232fd25',
    'elixir_bounded.py': 'b5cc9fbe2847048206771fa4eb13551380f3e3c998f72def77bd37963fbfaa75',
}
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}
LIMITS = dict(wall_seconds=120, normal_exit_group_grace_seconds=5,
              forced_cleanup_grace_seconds=5, combined_rss_bytes=2*1024**3,
              stdout_bytes=1024**2, stderr_bytes=1024**2, event_bytes=4*1024**2)
FALSE_FLAGS = dict(native_owner_qualified=False, actual_ir_removal_qualified=False,
                   fallback_closure_qualified=False, runtime_aot_proven=False,
                   timing_qualified=False, chart_admission=False)
CAPABILITIES = ('darwin_suspended_spawn_abi', 'owned_debugserver_unix_attach',
                'lldb_no_init_batch_source', 'lldb_python_client_apis',
                'required_debugger_settings', 'matching_module_uuids',
                'matching_codeinstance_dwarf_fields')


def require(value, message):
    if not value:
        raise ValueError(message)


def raw(path, maximum=None):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular file required: '+str(path))
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                'Input replaced during open: '+str(path))
        value = stream.read() if maximum is None else stream.read(maximum+1)
        after = os.fstat(stream.fileno())
    named = path.lstat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    require(all(getattr(before, k) == getattr(after, k) == getattr(named, k) for k in fields),
            'Input changed during read: '+str(path))
    require(maximum is None or len(value) <= maximum, 'File exceeds bound: '+str(path))
    return value


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def checked(path, expected, maximum=None):
    value = raw(path, maximum)
    require(digest(value) == expected, 'Input digest differs: '+str(path))
    return value


def load_source(name, path, expected):
    value = checked(path, expected, 1024**2)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(value, str(path), 'exec'), module.__dict__)
    return module


def write_new(path, value):
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())
    return dict(sha256=digest(value), bytes=len(value))


def lock_identity(lock):
    opened, named = os.fstat(lock.fileno()), LOCK.lstat()
    require(stat.S_ISREG(named.st_mode) and opened.st_ino == LOCK_INODE
            and (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino),
            'Common named mutex identity changed')


def verify_pins(pins):
    observations = {}
    for name, expected in pins.items():
        path = Path(name)
        require(path.is_absolute() and path.resolve(strict=True) == path,
                'Physical absolute input path required: '+name)
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode), 'Regular pinned input required: '+name)
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                    'Pinned input replaced during open: '+name)
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = os.fstat(stream.fileno())
        info = path.lstat()
        require(actual == expected and all(getattr(before, k) == getattr(after, k) == getattr(info, k)
                for k in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                'Pinned input changed during verification: '+name)
        observations[name] = tuple(getattr(info, k) for k in
            ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
    return observations


def verify_fast(observations, lock):
    lock_identity(lock)
    for name, expected in observations.items():
        info = Path(name).lstat()
        require(stat.S_ISREG(info.st_mode) and tuple(getattr(info, k) for k in
            ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')) == expected,
            'Prepared input identity changed during capture: '+name)


def prepare_document(intake_path, intake_sha, output):
    """Metadata-only construction, after explicit local-tool intake review."""
    require(intake_path.is_absolute() and intake_path.resolve(strict=True) == intake_path,
            'Physical absolute intake required')
    intake_raw = checked(intake_path, intake_sha, 8*1024**2)
    intake = json.loads(intake_raw)
    require(intake['schema'] == 'julia-entry-debugger-tool-intake-v1'
            and intake['status'] == 'reviewed-local-debugger-transport-and-api-intake'
            and intake['subject_executions'] == 0,
            'A reviewed zero-subject tool intake is required')
    require(set(intake['capabilities']) == set(CAPABILITIES)
            and all(x is True for x in intake['capabilities'].values()),
            'Missing reviewed local transport/API capability')
    require(intake['closure_scope'] == 'physical-tools-scripting-runtime-and-declared-dependencies',
            'Explicit debugger dependency scope required')
    pins = dict(intake['pins'])
    require(str(intake_path) not in pins, 'Intake cannot pin itself')
    for role in ('lldb', 'debugserver', 'scripting_python'):
        require(intake['tools'][role] in pins, 'Unpinned debugger tool: '+role)
    require(intake['capability_evidence'] and all(
        r['path'] in pins and pins[r['path']] == r['sha256'] for r in intake['capability_evidence']),
        'Capability observations must have exact physical evidence pins')
    draft_path = HERE/'plan-draft.json'
    draft_raw = raw(draft_path, 65536)
    draft = json.loads(draft_raw)
    require(draft['subject']['arguments'] == ['1'] and draft['prepared'] is False
            and draft['proposed_owner_limits'] == LIMITS,
            'Fixed diagnostic scope or bounds changed')
    expected = {draft['subject']['path']: draft['subject']['sha256'],
        draft['retained_runtime']['path']: draft['retained_runtime']['sha256'],
        draft['retained_runtime']['matching_dwarf_path']: draft['retained_runtime']['matching_dwarf_sha256'],
        draft['retained_runtime']['matching_header_path']: draft['retained_runtime']['matching_header_sha256'],
        str(ROOT/draft['prerequisite']['path']): draft['prerequisite']['sha256'],
        str(KERNEL): KERNEL_SHA, str(PYTHON): PYTHON_SHA}
    expected.update({str(ROOT/'tools/qualification'/name): value for name, value in HELPERS.items()})
    for name, value in expected.items():
        require(pins.get(name) == value, 'Intake changed or omitted fixed input: '+name)
    require(set(intake['modules']) == {'main', 'runtime'}, 'Exactly two prepared modules required')
    for role, path in (('main', draft['subject']['path']), ('runtime', draft['retained_runtime']['path'])):
        require(intake['modules'][role]['path'] == path and intake['modules'][role]['uuid'],
                'Prepared module identity differs: '+role)
    require(intake['subject_environment'].get('JULIA_LOAD_CODEGEN_LIB') == '0',
            'The retained codegen-library policy must remain unchanged')
    for field in ('subject_environment', 'debugger_environment'):
        environment = intake[field]
        require(environment and all(isinstance(k, str) and isinstance(v, str)
            and k and '=' not in k and '\0' not in k+v for k, v in environment.items()),
            'Complete explicit environment required: '+field)
        require(not any(k.startswith(('DYLD_', 'LD_', 'PYTHON')) for k in environment),
                'Unreviewed loader/Python environment override')
    cwd = Path(intake['cwd'])
    require(cwd.is_absolute() and cwd.resolve(strict=True) == cwd and cwd.is_dir(),
            'Physical working directory required')
    for name in ('controller.py', 'owned_processes.py', 'client.py', 'trace.py'):
        pins[str(HERE/name)] = digest(raw(HERE/name, 1024**2))
    pins[str(draft_path)] = digest(draft_raw)
    pins[str(intake_path)] = intake_sha
    return dict(schema='julia-entry-dispatch-plan-v1', prepared=True,
        intake=dict(path=str(intake_path), sha256=intake_sha), output=str(output),
        tools=intake['tools'], modules=intake['modules'],
        runtime_dwarf=draft['retained_runtime']['matching_dwarf_path'],
        subject_environment=intake['subject_environment'], debugger_environment=intake['debugger_environment'],
        cwd=str(cwd), pins=pins, limits=LIMITS, subject_arguments=['1'],
        maximum_subject_processes=1, automatic_retries=0, **FALSE_FLAGS)


def artifact_inventory(output, excluded=()):
    result = {}
    for path in sorted(output.iterdir()):
        if path.name in excluded:
            continue
        value = raw(path, 4*1024**2)
        result[path.name] = dict(sha256=digest(value), bytes=len(value))
    return result


def run(plan_path, plan_sha, lock):
    require(plan_path.is_absolute() and plan_path.resolve(strict=True) == plan_path,
            'Physical absolute prepared plan required')
    plan_raw = checked(plan_path, plan_sha, 8*1024**2)
    plan = json.loads(plan_raw)
    output = Path(plan['output'])
    require(output.is_absolute() and output.parent.resolve(strict=True) == output.parent
            and not output.exists() and not output.is_symlink(), 'Fresh physical output required')
    rebuilt = prepare_document(Path(plan['intake']['path']), plan['intake']['sha256'], output)
    require(plan == rebuilt, 'Prepared plan does not exactly rebuild from reviewed intake')
    observations = verify_pins(plan['pins'])
    observations[str(plan_path)] = tuple(getattr(plan_path.stat(), k) for k in
        ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
    kb = load_source('julia_entry_kernel', KERNEL, KERNEL_SHA)
    owner_module = load_source('julia_entry_owner', HERE/'owned_processes.py',
                               plan['pins'][str(HERE/'owned_processes.py')])
    kernel = kb.Kernel()
    output.mkdir(mode=0o700)
    socket_dir = Path(tempfile.mkdtemp(prefix='jld-', dir='/private/tmp'))
    socket_identity = socket_dir.stat()
    endpoint = socket_dir/'debug.sock'
    report = dict(schema='julia-entry-dispatch-capture-v1', plan_sha256=plan_sha,
        status='capture-incomplete', errors=[], started_at=datetime.now(timezone.utc).isoformat(),
        private_socket_directory=str(socket_dir), children=[], requested_commands={}, **FALSE_FLAGS)
    files, streams, snapshots, file_identities = [], {}, {}, {}
    endpoint_identity = None
    normal_cleanup_attempted = False
    owner = None
    with ExitStack() as stack:
        for name, bound in [('subject.stdout', LIMITS['stdout_bytes']), ('subject.stderr', LIMITS['stderr_bytes']),
                ('debugserver.stdout', LIMITS['stdout_bytes']), ('debugserver.stderr', LIMITS['stderr_bytes']),
                ('debugger.stdout', LIMITS['stdout_bytes']), ('debugger.stderr', LIMITS['stderr_bytes']),
                ('trace.jsonl', LIMITS['event_bytes']), ('owner.jsonl', LIMITS['event_bytes'])]:
            path = output/name
            fd = os.open(path, os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            streams[name] = stack.enter_context(os.fdopen(fd, 'w+b', buffering=0))
            files.append((path, bound))
            info = os.fstat(fd)
            file_identities[name] = (info.st_dev, info.st_ino)
        def verify_outputs():
            directory = socket_dir.lstat()
            require(stat.S_ISDIR(directory.st_mode) and directory.st_uid == os.getuid()
                and stat.S_IMODE(directory.st_mode) == 0o700
                and (directory.st_dev, directory.st_ino) == (socket_identity.st_dev, socket_identity.st_ino),
                'Private debugger directory changed')
            if endpoint_identity is not None:
                try:
                    endpoint_now = endpoint.lstat()
                except FileNotFoundError:
                    server_record = next(c for c in owner.children if c.role == 'debugserver')
                    require(server_record.reaped or owner.identity(server_record)['status'] == 5,
                            'Debugger endpoint disappeared before server exit')
                else:
                    require(stat.S_ISSOCK(endpoint_now.st_mode)
                        and (endpoint_now.st_dev, endpoint_now.st_ino) == endpoint_identity,
                        'Owned debugger endpoint changed')
            for path, bound in files:
                info = path.lstat()
                require(stat.S_ISREG(info.st_mode) and info.st_size <= bound
                    and (info.st_dev, info.st_ino) == file_identities[path.name],
                    'Owned capture path replaced or exceeded its bound: '+path.name)
        def emit(event):
            value = json.dumps(event, sort_keys=True, separators=(',', ':')).encode()+b'\n'
            stream = streams['owner.jsonl']
            require(stream.tell()+len(value) <= LIMITS['event_bytes'], 'Owner journal exceeded bound')
            stream.write(value); os.fsync(stream.fileno())
        deadline = time.monotonic()+LIMITS['wall_seconds']
        owner = owner_module.OwnedProcesses(kernel, kb.atomic, lock,
            lambda: verify_fast(observations, lock), lambda: lock_identity(lock), emit, deadline)
        try:
            null = stack.enter_context(open(os.devnull, 'rb'))
            report['requested_commands']['subject'] = [plan['modules']['main']['path'], '1']
            subject = owner.spawn_target(plan['modules']['main']['path'], plan['subject_environment'],
                plan['cwd'], (null, streams['subject.stdout'], streams['subject.stderr']), LIMITS['stdout_bytes'])
            report['requested_commands']['debugserver'] = [plan['tools']['debugserver'], str(endpoint),
                '--attach='+str(subject.pid)]
            server = owner.spawn_tool('debugserver', report['requested_commands']['debugserver'],
                plan['debugger_environment'], plan['cwd'],
                streams['debugserver.stdout'], streams['debugserver.stderr'], LIMITS['stdout_bytes'])
            while not endpoint.exists():
                verify_outputs()
                owner.monitor(files, LIMITS['combined_rss_bytes'])
                require(owner.identity(server)['status'] != 5, 'Debugserver exited before endpoint readiness')
                time.sleep(0.01)
            endpoint_info = endpoint.lstat()
            require(stat.S_ISSOCK(endpoint_info.st_mode) and endpoint_info.st_uid == os.getuid(),
                    'Unexpected debugger endpoint type/owner')
            endpoint_identity = (endpoint_info.st_dev, endpoint_info.st_ino)
            event_info = os.fstat(streams['trace.jsonl'].fileno())
            config = dict(subject_pid=subject.pid, subject_birth=subject.identity, subject_arguments=['1'],
                modules=plan['modules'], runtime_dwarf=plan['runtime_dwarf'], socket_path=str(endpoint),
                private_socket_directory=str(socket_dir), trace_sha256=plan['pins'][str(HERE/'trace.py')],
                socket_identity=dict(device=endpoint_info.st_dev, inode=endpoint_info.st_ino),
                socket_directory_identity=dict(device=socket_identity.st_dev, inode=socket_identity.st_ino),
                events=dict(path=str(output/'trace.jsonl'), device=event_info.st_dev, inode=event_info.st_ino,
                            maximum_bytes=LIMITS['event_bytes']), maximum_seconds=LIMITS['wall_seconds'])
            config_raw = encoded(config)
            snapshots['client-config.json'] = write_new(output/'client-config.json', config_raw)
            # A single fixed script loads exact source bytes; it does not import
            # user modules or evaluate any expression inside the Julia process.
            command = ('script import hashlib, pathlib, sys, os; '
                f'p=pathlib.Path({str(HERE/"client.py")!r}); b=p.read_bytes(); '
                f'assert hashlib.sha256(b).hexdigest()=={plan["pins"][str(HERE/"client.py")]!r}; '
                'g={"__file__":str(p),"__name__":"julia_owned_client"}; exec(compile(b,str(p),"exec"),g); '
                f's=g["entry"](lldb.debugger,{str(output/"client-config.json")!r},{digest(config_raw)!r}); '
                'sys.stdout.flush(); sys.stderr.flush(); os._exit(s)\n').encode()
            snapshots['client.lldb'] = write_new(output/'client.lldb', command)
            report['requested_commands']['debugger'] = [plan['tools']['lldb'], '--no-lldbinit', '--batch',
                '--source', str(output/'client.lldb')]
            owner.spawn_tool('debugger', report['requested_commands']['debugger'],
                plan['debugger_environment'], plan['cwd'],
                streams['debugger.stdout'], streams['debugger.stderr'], LIMITS['event_bytes'])
            while True:
                verify_outputs()
                owner.monitor(files, LIMITS['combined_rss_bytes'])
                if all(owner.identity(child)['status'] == 5 for child in owner.children):
                    break
                time.sleep(0.01)
            # Set the attempt marker in the same atomic scope as cleanup. Its
            # normal path already guarantees one forced phase on failure; the
            # finalizer must not add a third five-second phase afterward.
            with kb.atomic():
                normal_cleanup_attempted = True
                owner.cleanup(False)
            require(all(c.reaped and c.exit_status == 0 for c in owner.children),
                    'All three owned children must exit normally and be reaped')
            trace_raw = raw(output/'trace.jsonl', LIMITS['event_bytes'])
            snapshots['trace.jsonl'] = dict(sha256=digest(trace_raw), bytes=len(trace_raw))
            trace = [json.loads(line) for line in trace_raw.splitlines()]
            require(trace and trace[-1].get('kind') == 'client-complete'
                and sum(e.get('kind') == 'client-complete' for e in trace) == 1
                and sum(e.get('kind') == 'initial-owned-stop' and e.get('pid') == subject.pid for e in trace) == 1
                and not any(e.get('kind') == 'client-failed' for e in trace),
                'Complete single-process client observation missing')
            report['status'] = 'raw-entry-capture-complete-awaiting-semantic-review'
        except BaseException as error:
            report['errors'].append(dict(type=type(error).__name__, message=str(error)))
        finally:
            # A failure before client return still owns every registered PID.
            with kb.atomic():
                try:
                    if not normal_cleanup_attempted and any(not c.reaped and c.spawned for c in owner.children):
                        owner.cleanup(True)
                except BaseException as error:
                    report['errors'].append(dict(type=type(error).__name__, message=str(error)))
                report['children'] = [dict(role=c.role, pid=c.pid, birth=c.identity,
                    parent_observations=c.parent_observations, reaped=c.reaped, exit_status=c.exit_status)
                    for c in owner.children]
                report['native_processes_started'] = sum(c.spawned for c in owner.children)
                report['subject_processes_started'] = sum(c.spawned and c.role == 'subject' for c in owner.children)
                report['peak_rss_bytes'] = owner.peak_rss
                report['live_rss_observation_obtained'] = owner.peak_rss is not None
                report['memory_usage_qualified'] = False
                report['monitor_samples'] = owner.monitor_samples
                report['finished_at'] = datetime.now(timezone.utc).isoformat()
                if SIGNALS & signal.sigpending():
                    report['errors'].append(dict(type='PendingSignal', message='Signal pending during closure'))
                try:
                    for stream in streams.values():
                        stream.flush(); os.fsync(stream.fileno())
                    verify_outputs()
                    for name, expected in snapshots.items():
                        require(dict(sha256=digest(raw(output/name)), bytes=(output/name).stat().st_size) == expected,
                                'Prepared client artifact changed: '+name)
                    complete = artifact_inventory(output)
                    require(all(complete.get(name) == expected for name, expected in snapshots.items()),
                            'Initial inventory differs from prevalidated client evidence')
                    snapshots = complete
                    verify_pins(plan['pins']); checked(plan_path, plan_sha); lock_identity(lock)
                    require(artifact_inventory(output) == snapshots, 'Capture changed during final input replay')
                except BaseException as error:
                    report['errors'].append(dict(type=type(error).__name__, message=str(error)))
                if report['errors']:
                    report['status'] = 'entry-capture-failed-unqualified'
                report_raw = encoded(report)
                report_pin = write_new(output/'report.json', report_raw)
                terminal_errors = []
                try:
                    verify_pins(plan['pins']); checked(plan_path, plan_sha)
                    verify_outputs()
                    require(artifact_inventory(output, ('report.json',)) == snapshots,
                            'Capture changed while writing report')
                    checked(output/'report.json', report_pin['sha256'])
                    lock_identity(lock)
                except BaseException as error:
                    terminal_errors.append(dict(type=type(error).__name__, message=str(error)))
                if SIGNALS & signal.sigpending():
                    terminal_errors.append(dict(type='PendingSignal', message='Signal pending at terminal closure'))
                terminal = dict(schema='julia-entry-dispatch-terminal-v1', report=report_pin,
                    status=report['status'] if not terminal_errors else 'terminal-closure-failed-unqualified',
                    artifact_inventory=snapshots, errors=terminal_errors,
                    all_owned_children_reaped=all(c.reaped for c in owner.children),
                    common_mutex_held=not terminal_errors, common_mutex_inode=LOCK_INODE, **FALSE_FLAGS)
                write_new(output/'terminal.json', encoded(terminal))
                # Preserve the private endpoint directory as named evidence.
                # No filesystem cleanup can obscure a late replacement after
                # the terminal was written; it contains no executable inputs.
    require(not report['errors'] and not terminal_errors, 'Julia diagnostic did not close successfully')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preparing = commands.add_parser('prepare')
    preparing.add_argument('--intake', type=Path, required=True)
    preparing.add_argument('--intake-sha256', required=True)
    preparing.add_argument('--plan', type=Path, required=True)
    preparing.add_argument('--output', type=Path, required=True)
    running = commands.add_parser('run')
    running.add_argument('--plan', type=Path, required=True)
    running.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated
        and sys.flags.no_site and sys.flags.dont_write_bytecode and not sys.flags.optimize,
        'Use the retained Python with -I -S -B and no -O')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Owned Julia diagnostic interrupted: '+str(signum))
    for signum in SIGNALS:
        signal.signal(signum, interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); lock_identity(lock)
        checked(PYTHON, PYTHON_SHA)
        if args.action == 'prepare':
            require(args.plan.is_absolute() and args.output.is_absolute()
                and not args.plan.exists() and not args.output.exists()
                and args.plan.parent.resolve(strict=True) == args.plan.parent
                and args.output.parent.resolve(strict=True) == args.output.parent
                and not args.plan.is_relative_to(args.output), 'Fresh physical plan/output required')
            document = prepare_document(args.intake, args.intake_sha256, args.output)
            verify_pins(document['pins']); lock_identity(lock)
            write_new(args.plan, encoded(document))
        else:
            run(args.plan, args.plan_sha256, lock)


if __name__ == '__main__':
    main()
