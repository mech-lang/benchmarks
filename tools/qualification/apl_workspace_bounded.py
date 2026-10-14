"""Five serial GNU APL workspace checks; no full-size timing admission.

Preparation and execution require the original free common timing mutex. The
local observer preserves the frozen observer's direct kernel monitoring while
separating artifact storage from the exact retained working directory. There is
no sampler child. Every native child is reaped before the next command.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/apl/binarytrees-workspace-v1'
SPEC = PACKET/'bounded-next-run.json'
SPEC_SHA = '4986eef6eabbdb0db171910fe6143b7eb3141d6174e62567dc98d5049223fbd8'
INSPECTOR = ROOT/'tools/qualification/julia_native_inspection.py'
INSPECTOR_SHA = '877bda82e014e16a5380cc46b283ba90dca71f02c4a285994df5c54ab883489a'
RUNTIME_SCOPE = ROOT/'experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json'
RUNTIME_SCOPE_SHA = '76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6'
KIND = 'apl-workspace-bounded'
SUCCESS = 'five-bounded-workspace-captures-awaiting-independent-work-review'
FILE_LIMIT = 1024**2
RSS_LIMIT = 10*1024**3
FALSE_GATES = ('required_work_qualified', 'canonical_source_count_qualified', 'full_timing_qualified', 'chart_admission')
IDS = ('configuration','workspace-readback','allocation-ownership','whole-subject-n4','whole-subject-n10')
EMPTY_SHA = hashlib.sha256(b'').hexdigest()


def require(value, message):
    if not value: raise AssertionError(message)


def load_inspector():
    raw = INSPECTOR.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == INSPECTOR_SHA, 'Frozen static inspector changed')
    spec = importlib.util.spec_from_file_location('apl_static_dependency_inspector', INSPECTOR)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(INSPECTOR), 'exec'), module.__dict__)
    return module


j = load_inspector()
kb = j.kb
# Private module instance only; immutable source and other controllers unchanged.
kb.FILE_LIMIT = FILE_LIMIT
kb.RSS_LIMIT = RSS_LIMIT
sha, physical, pin = j.sha, j.physical, j.pin


def document(path, digest, pins):
    return json.loads(pin(pins, path, digest).read_bytes())


def environment(directory):
    return dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C',
                HOME=str(directory/'home'), TMPDIR=str(directory/'tmp'),
                OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')


def lock_identity(lock):
    require(type(lock.fileno()) is int and lock.fileno() >= 64, 'Inherited timing lock must be FD >=64; FD3 is APL output')
    kb.kh.verify_lock(lock)
    fd = os.fstat(lock.fileno()); named = kb.LOCK.stat()
    require((fd.st_dev,fd.st_ino) == (named.st_dev,named.st_ino) and fd.st_ino == kb.LOCK_INODE,
            'Held timing mutex descriptor/path identity differs')
    return dict(fd=lock.fileno(),device=fd.st_dev,inode=fd.st_ino)


@contextmanager
def held_mutex():
    # Duplicate before flock; keep the high descriptor alive through terminal
    # creation and all process cleanup. pass_fds clears CLOEXEC in each child.
    with kb.LOCK.open('rb') as original:
        fd = fcntl.fcntl(original.fileno(), fcntl.F_DUPFD_CLOEXEC, 64)
        with os.fdopen(fd, 'rb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
            lock_identity(lock)
            yield lock
            lock_identity(lock)


def validate_spec(spec):
    require(spec['schema'] == 'apl-binarytrees-workspace-bounded-source-spec-v1' and
            spec['status'] == 'source-prepared-native-validation-unexecuted' and
            spec['qualification']['native_processes'] == 0 and
            all(value is False for key,value in spec['qualification'].items() if key != 'native_processes') and
            spec['future_full_study']['authorized_by_this_spec'] is False, 'Bounded-only source specification required')
    rows = spec['commands']; require(len(rows) == 5 and tuple(r['id'] for r in rows) == IDS, 'Exact five command order required')
    launcher = spec['launcher_runtime_path']; subject = spec['subject_runtime_path']
    setup = spec['authored_files']['setup.apl']['path']; readback = spec['authored_files']['readback.apl']['path']
    witness = spec['authored_files']['allocation-witness.apl']['path']
    commands = [[launcher,'--cc','1','--cfg'],
        [launcher,'--cc','1','--OFF','-f',readback,'-f',setup,'-f',readback],
        [launcher,'--cc','1','-f',setup,'-f',witness],
        [launcher,'--cc','1','-f',setup,'-f',subject,'--','4'],
        [launcher,'--cc','1','-f',setup,'-f',subject,'--','10']]
    for index,row in enumerate(rows):
        require(row['argv'] == commands[index] and row['cwd'] == str(Path(launcher).parent) and
                row['required_environment'] == {'LC_ALL':'C'} and row['stdin'] == 'DEVNULL' and
                type(row['expected_exit_status']) is int and row['expected_exit_status'] == 0 and
                row['timeout_seconds'] == (60 if index == 4 else 30) and
                row['maximum_process_group_rss_mib'] == 10240 and
                row['stdout_limit_bytes'] == row['stderr_limit_bytes'] == FILE_LIMIT,
                'Bounded command or resource policy differs')
    policy = spec['supervision']
    require(policy['common_mutex_path'] == str(kb.LOCK) and policy['common_mutex_inode'] == kb.LOCK_INODE and
            policy['minimum_inherited_lock_fd'] == 64 and policy['cleanup_seconds'] == kb.CLEANUP_TIMEOUT == 5 and
            all(policy[k] is True for k in ('continuous_ownership_required','fresh_owned_session_per_command',
                'native_and_sampler_reaping_required','empty_group_required','no_retries',
                'pin_replay_and_preparation_require_free_common_mutex')), 'Owned serial policy differs')
    return rows


def configuration_pattern(config, version):
    # Exact text/order from pinned UserPreferences::show_configure_options.
    match = re.search(r'^#define cfg_CONFIGURE_ARGS (".*")$', config, re.M)
    require(match is not None, 'Retained configure arguments missing')
    configure = json.loads(match[1])
    prefix = ('\nconfigurable options:\n---------------------\n'
        '    ASSERT_LEVEL_WANTED=1 (default)\n    SECURITY_LEVEL_WANTED=0 (default)\n'
        '    APSERVER_PATH=/tmp/GNU-APL/APserver (default)\n    APSERVER_PORT=16366 (default)\n'
        '    APSERVER_TRANSPORT=0 (default)\n    CORE_COUNT_WANTED=-2  (= argv (--cc))\n'
        '    DYNAMIC_LOG_WANTED=no (default)\n    MAX_RANK_WANTED=8 (default)\n'
        '    RATIONAL_NUMBERS_WANTED=no (default)\n    SHORT_VALUE_LENGTH_WANTED=12, therefore:\n')
    middle = (r'        sizeof\(Value\)       : (?P<value>[1-9][0-9]*) bytes\n'
              r'        sizeof\(Cell\)        :  (?P<cell>[1-9][0-9]*) bytes\n'
              r'        sizeof\(Value header\): (?P<header>[1-9][0-9]*) bytes\n')
    suffix = ('\n    VALUE_CHECK_WANTED=no (default)\n    VALUE_HISTORY_WANTED=no (default)\n'
        '    VF_TRACING_WANTED=no (default)\n    VISIBLE_MARKERS_WANTED=no (default)\n\n'
        'how ./configure was (probably) called:\n--------------------------------------\n    '+configure+'\n\n'+version+'\n')
    return re.escape(prefix)+middle+re.escape(suffix)


def check_output(slot, stdout, stderr, pattern):
    require(len(stdout) <= FILE_LIMIT and len(stderr) <= FILE_LIMIT, 'Stream exceeded 1MiB bound')
    if slot['id'] == 'configuration':
        require(stdout == b'', 'Configuration unexpectedly wrote application stdout')
        match = re.fullmatch(pattern, stderr.decode('utf-8'))
        require(match is not None, 'Unknown configuration stderr; complete raw bytes retained')
        sizes = {name:int(value) for name,value in match.groupdict().items()}
        require(sizes['value'] == sizes['header']+12*sizes['cell'], 'Actual configuration sizes are inconsistent')
        return dict(configuration_sizes=sizes,short_value_length=12,exact_output=True)
    require(stderr == b'', 'Unknown APL stderr; complete raw bytes retained')
    require(stdout == slot['expected_stdout_utf8'].encode(), 'Exact bounded APL output mismatch')
    return dict(exact_output=True)


def preference_paths(prefix, directories):
    names = ['preferences','parallel_thresholds']
    paths = [prefix/'etc/gnu-apl.d'/name for name in names]
    for directory in directories:
        paths += [directory/'home'/suffix/name for suffix in ('.gnu-apl','.config/gnu-apl') for name in names]
    return paths


def verify(pins, resolutions, absent, lock):
    j.verify(pins, resolutions, absent)
    lock_identity(lock)


def build_plan(output):
    physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(), 'Fresh packet output required')
    pins = {}; spec = document(SPEC, SPEC_SHA, pins); rows = validate_spec(spec)
    scope = document(RUNTIME_SCOPE, RUNTIME_SCOPE_SHA, pins)
    require(scope['runtime']['path'] == spec['runtime_binary']['path'] and
            scope['runtime']['sha256'] == spec['runtime_binary']['sha256'], 'Retained APL runtime differs')
    for field in ('runtime_binary','launcher','unchanged_subject','prior_failed_attempt','prior_failed_supervisor','saved_n10_oracle'):
        ref=spec[field];path=pin(pins,ref['path'],ref['sha256'])
        if 'bytes' in ref: require(path.stat().st_size == ref['bytes'], 'Retained source/evidence size differs')
    for ref in list(spec['authored_files'].values())+list(spec['runtime_source_evidence'].values()):
        path=pin(pins,ref['path'],ref['sha256']);require(path.stat().st_size == ref['bytes'], 'Bounded input size differs')
    pin(pins,spec['launcher_runtime_path'],spec['launcher']['sha256'])
    pin(pins,spec['subject_runtime_path'],spec['unchanged_subject']['sha256'])
    for path,digest in scope['required_inherited_pins'].items(): pin(pins,path,digest)
    for path,digest in ((Path(__file__).resolve(),None),(Path(__file__).with_name('test_apl_workspace_bounded.py'),None),
        (PACKET/'README.md',None),(INSPECTOR,INSPECTOR_SHA),(j.OBSERVER,j.OBSERVER_SHA),
        (Path(kb.kh.__file__),kb.HELPER_CONTROLLER_SHA),(Path(kb.eb.__file__),kb.REFERENCE_CONTROLLER_SHA),
        (kb.kh.PYTHON,kb.kh.PYTHON_SHA),(Path('/bin/sh'),None),(Path('/usr/bin/dirname'),None)):
        pin(pins,path,digest)
    native = [Path(spec['runtime_binary']['path']).resolve(),Path('/bin/sh').resolve(),Path('/usr/bin/dirname').resolve()]
    closure=j.tool_closure(native,pins)
    schedule=[dict(row,directory=f'{index:02}-'+row['id']) for index,row in enumerate(rows)]
    absent=set(closure['unavailable_candidates'])
    for path in preference_paths(native[0].parent.parent,[output/s['directory'] for s in schedule]):
        if path.is_file(): pin(pins,path)
        else:
            require(not os.path.lexists(path),'Nonregular or dangling APL preference path');absent.add(str(path))
    config=Path(spec['runtime_source_evidence']['config.h']['path']).read_text()
    require(rows[-1]['expected_stdout_utf8'].encode() == Path(spec['saved_n10_oracle']['path']).read_bytes(),
            'Retained N10 oracle differs')
    return dict(schema='apl-workspace-five-bounded-plan-v1',status='prepared-awaiting-independent-review',
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),output=str(output),
        specification=dict(path=str(SPEC),sha256=SPEC_SHA),pins=pins,
        input_resolutions={name:str(Path(name).resolve()) for name in pins},absent_inputs=sorted(absent),
        static_runtime_closure=closure,configuration_pattern=configuration_pattern(config,scope['runtime']['version']),
        schedule=schedule,native_commands=5,maximum_live_native_groups=1,automatic_retries=0,
        sampler_processes=0,monitoring='direct in-process kernel identity/group/RSS observations',
        minimum_inherited_lock_fd=64,common_mutex_inode=kb.LOCK_INODE,benchmark_samples=0,
        **{k:False for k in FALSE_GATES})


def pump_stdout(process, payload, output, deadline, tick):
    """Drain bounded stdout while stdin is the actual DEVNULL descriptor."""
    require(payload == b'' and process.stdin is None, 'This stage accepts no stdin transport substitution')
    with selectors.DefaultSelector() as selector:
        os.set_blocking(process.stdout.fileno(),False)
        selector.register(process.stdout,selectors.EVENT_READ)
        while selector.get_map():
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise subprocess.TimeoutExpired(process.args,kb.TIMEOUT)
            tick()
            for key,mask in selector.select(min(.05,remaining)):
                raw=os.read(process.stdout.fileno(),kb.PIPE_CHUNK)
                if raw:
                    output.write(raw);output.flush()
                    require(output.tell() <= FILE_LIMIT,'Stdout exceeded 1MiB capture threshold')
                else:
                    selector.unregister(process.stdout);process.stdout.close()


# Ownership/cleanup body adapted from frozen kotlin_bounded_v2.observe.
def observe(slot, directory, lock, launched, pattern, *, kernel=None,
            launch=subprocess.Popen, transfer=None, drainer=None):
    command, env, payload = slot['argv'], environment(directory), b''
    kind = KIND
    kb.TIMEOUT = slot['timeout_seconds']
    inherited = lock_identity(lock)
    transfer = pump_stdout if transfer is None else transfer
    drainer = kb.drain if drainer is None else drainer
    kernel = kernel if kernel is not None else kb.Kernel()
    record = dict(status='starting',kind=kind,command=command,environment=env,cwd=slot['cwd'],artifact_directory=str(directory),
        inherited_lock_descriptor=inherited,sampler_processes=0,stdin_transport='DEVNULL',
        started_at=datetime.now(timezone.utc).isoformat(),process_timeout_seconds=kb.TIMEOUT,
        cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,inherited_common_mutex=True,common_mutex_inode=kb.LOCK_INODE,
        native_process_started=False,stop_signals=[],cleanup_errors=[],benchmark_samples=0,
        stdin_bytes=len(payload),stdin_sha256=hashlib.sha256(payload).hexdigest(),
        observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=FILE_LIMIT,
        stdout_capture_limit_bytes=FILE_LIMIT+kb.PIPE_CHUNK,stdout_transport='OS pipe, retained as received',
        stderr_transport='exclusive artifact',source_work_qualified=False,chart_admission=False)
    process = None; reaped = False
    kb.save(directory/'start.json',record)
    try:
        lock_identity(lock)
        with (directory/'stdout.bin').open('xb') as stdout,(directory/'stderr.bin').open('xb') as stderr:
            deadline = time.monotonic()+kb.TIMEOUT
            with kb.atomic() as mask:
                def child_setup():
                    signal.pthread_sigmask(signal.SIG_SETMASK,mask)
                    fd = os.fstat(lock.fileno())
                    require((fd.st_dev,fd.st_ino) == (inherited['device'],inherited['inode']) and
                            os.get_inheritable(lock.fileno()), 'Child inherited mutex identity differs')
                    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
                    resource.setrlimit(resource.RLIMIT_FSIZE,(FILE_LIMIT,FILE_LIMIT))
                process = launch(command,cwd=slot['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                    stderr=stderr,start_new_session=True,pass_fds=(lock.fileno(),),preexec_fn=child_setup)
                # Popen returning is the native-start boundary. Count that
                # fact before any fallible observation or artifact write.
                record.update(status='running',pid=process.pid,pgid=process.pid,native_process_started=True,child_setup_verified=True)
                launched(process.pid)
                record['identity'] = kernel.identity(process.pid)
                kb.save(directory/'active.json',record)
            require(record['identity'] and record['identity']['ppid'] == os.getpid() and
                    record['identity']['pgid'] == process.pid, 'Missing owned native identity')
            tick = lambda:kb.monitor(kernel,process,record,directory)
            transfer(process,payload,stdout,deadline,tick)
            while True:
                identity,group = tick()
                if identity['status'] == 5:
                    record['leader_identity_before_reap'] = identity
                    record['remaining_process_group'] = group
                    require(not group, 'Native command left live descendants')
                    break
                if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(command,kb.TIMEOUT)
                time.sleep(0.01)
            with kb.atomic():
                record['exit_status'] = process.wait(timeout=max(0.001,deadline-time.monotonic()))
                reaped = True
            require(record['exit_status'] == 0, 'Native command exited unsuccessfully')
        record['output_validation'] = check_output(slot, (directory/'stdout.bin').read_bytes(),
                                                  (directory/'stderr.bin').read_bytes(), pattern)
        record['status'] = 'native-passed'
    except BaseException as error:
        record.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__,
                      timed_out=isinstance(error,subprocess.TimeoutExpired))
        if process is not None and not reaped:
            with kb.atomic():
                deadline = time.monotonic()+kb.CLEANUP_TIMEOUT
                try:
                    # Never poll/reap before the group is empty. The unreaped
                    # direct child's PID remains reserved even as a zombie.
                    try:
                        try:
                            needs_signal = bool(kernel.group(process.pid))
                        except BaseException as query_error:
                            record['cleanup_errors'].append(str(query_error) or type(query_error).__name__)
                            record['cleanup_signal_fallback'] = 'unreaped-owned-direct-child-kernel-query-failed'
                            needs_signal = True
                        if needs_signal:
                            os.killpg(process.pid,signal.SIGKILL); record['stop_signals'].append(int(signal.SIGKILL))
                    except ProcessLookupError: pass
                except BaseException as cleanup:
                    record['cleanup_errors'].append(str(cleanup) or type(cleanup).__name__)
                try: drainer(process.stdout,directory/'stdout.bin',deadline)
                except BaseException as cleanup:
                    record['cleanup_errors'].append(str(cleanup) or type(cleanup).__name__)
                try:
                    while remaining := kernel.group(process.pid):
                        record['remaining_after_cleanup'] = remaining
                        require(time.monotonic() < deadline, 'Owned group survived cleanup deadline')
                        time.sleep(0.01)
                    record['remaining_after_cleanup'] = []
                    record['exit_status'] = process.wait(timeout=max(0.001,deadline-time.monotonic()))
                    reaped = True
                except BaseException as cleanup:
                    record['cleanup_errors'].append(str(cleanup) or type(cleanup).__name__)
        raise
    finally:
        with kb.atomic():
            if process is not None:
                for stream in (process.stdin,process.stdout):
                    if stream is not None:
                        try: stream.close()
                        except BaseException as error: record['cleanup_errors'].append(str(error))
            record['direct_child_reaped'] = reaped
            for name in ('stdout','stderr'):
                path = directory/(name+'.bin')
                try:
                    require(path.is_file(), 'Missing '+str(path))
                    record[name+'_bytes'],record[name+'_sha256'] = path.stat().st_size,sha(path)
                except BaseException as error:
                    record.setdefault('artifact_errors',[]).append(dict(path=str(path),error=str(error) or type(error).__name__))
            record['finished_at'] = datetime.now(timezone.utc).isoformat()
            peak = record['observed_peak_process_group_rss_bytes']
            record['live_rss_observation_obtained'] = peak > 0
            record['observed_peak_process_group_rss_bytes'] = peak if peak > 0 else None
            record['rss_observation_complete'] = False
            record['memory_usage_qualified'] = False
            record['rss_monitoring_scope'] = 'Sampled live group RSS only; unobserved peaks are not proven below the guard.'
            if record['cleanup_errors'] or record.get('artifact_errors'): record['status'] = 'failed-cleanup-or-artifacts'
            kb.save(directory/'process.json',record)
            lock_identity(lock)
            require(not record['cleanup_errors'] and not record.get('artifact_errors'), 'Cleanup or output retention failed')
    return record


def inventory(directory, exclude=()):
    physical(directory);require(directory.is_dir(),'Artifact directory missing')
    found={}
    for path in sorted(directory.rglob('*')):
        mode=path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'Linked or nonregular bounded artifact')
        name=str(path.relative_to(directory))
        if stat.S_ISREG(mode) and name not in exclude:
            require(path.stat().st_size <= FILE_LIMIT+kb.PIPE_CHUNK,'Bounded artifact exceeds retention ceiling')
            found[name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    require(len(found) <= 27,'Unexpected bounded file inventory')
    return found


def stamp(value):
    parsed=datetime.fromisoformat(value);require(parsed.tzinfo is not None,'Timezone required');return parsed


def checked_capture(slot, directory, parent, inherited, pattern):
    start,active,final=[json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start,active,final):
        require(record['command'] == slot['argv'] and record['environment'] == environment(directory) and
            record['cwd'] == slot['cwd'] and record['artifact_directory'] == str(directory) and
            record['kind'] == KIND and record['started_at'] == start['started_at'] and
            record['stdin_bytes'] == 0 and record['stdin_sha256'] == EMPTY_SHA and record['stdin_transport'] == 'DEVNULL' and
            record['inherited_common_mutex'] is True and record['inherited_lock_descriptor'] == inherited and
            type(inherited['fd']) is int and inherited['fd'] >= 64 and inherited['inode'] == kb.LOCK_INODE and
            record['common_mutex_inode'] == kb.LOCK_INODE and record['sampler_processes'] == 0 and
            record['process_timeout_seconds'] == slot['timeout_seconds'] and record['cleanup_timeout_seconds'] == 5 and
            record['maximum_process_group_rss_bytes'] == RSS_LIMIT and record['native_file_limit_bytes'] == FILE_LIMIT and
            record['stdout_capture_limit_bytes'] == FILE_LIMIT+kb.PIPE_CHUNK and
            record['stdout_transport'] == 'OS pipe, retained as received' and record['stderr_transport'] == 'exclusive artifact' and
            record['benchmark_samples'] == 0 and record['source_work_qualified'] is record['chart_admission'] is False,
            'Native launch contract differs')
    identity,leader,pid=final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status'] == 'starting' and start['native_process_started'] is False and
        active['status'] == 'running' and active['native_process_started'] is active['child_setup_verified'] is True and
        final['native_process_started'] is final['child_setup_verified'] is True and active['identity'] == identity and
        type(parent) is int and parent > 0 and identity['ppid'] == parent and
        all(type(identity[k]) is int and identity[k] == leader[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds')) and
        type(pid) is int and pid > 0 and active['pid'] == active['pgid'] == pid == final['pgid'] == identity['pid'] == identity['pgid'] and
        leader['status'] == 5 and final['direct_child_reaped'] is True and
        final['remaining_process_group'] == final.get('remaining_after_cleanup',[]) == [] and
        final['stop_signals'] == final['cleanup_errors'] == [] and not final.get('artifact_errors') and
        not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False and
        final['status'] == 'native-passed' and type(final['exit_status']) is int and final['exit_status'] == 0 and
        not final.get('error') and not final.get('error_type') and
        type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples'] > 0 and
        stamp(start['started_at']) <= stamp(final['finished_at']), 'Native ownership or normal exit differs')
    peak=final['observed_peak_process_group_rss_bytes']
    require(final['rss_observation_complete'] is final['memory_usage_qualified'] is False and
            final['rss_monitoring_scope'] == 'Sampled live group RSS only; unobserved peaks are not proven below the guard.' and
            ((peak is None and final['live_rss_observation_obtained'] is False) or
             (type(peak) is int and 0 < peak <= RSS_LIMIT and final['live_rss_observation_obtained'] is True)),
            'RSS observation availability or scope differs')
    raw={}
    for name in ('stdout','stderr'):
        path=directory/(name+'.bin');raw[name]=path.read_bytes()
        require(len(raw[name]) == final[name+'_bytes'] and hashlib.sha256(raw[name]).hexdigest() == final[name+'_sha256'],
                'Captured stream changed')
    validation=check_output(slot,raw['stdout'],raw['stderr'],pattern)
    require(final['output_validation'] == validation,'Output validation receipt differs')
    snapshot=inventory(directory)
    require(set(snapshot) == {'start.json','active.json','process.json','stdout.bin','stderr.bin'},'Unexpected native artifacts')
    return dict(id=slot['id'],directory=slot['directory'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        output_validation=validation,process_sha256=snapshot['process.json']['sha256'],
        observed_peak_process_group_rss_bytes=peak,live_rss_observation_obtained=final['live_rss_observation_obtained'],
        rss_observation_complete=False,memory_usage_qualified=False,
        **{k:False for k in FALSE_GATES}),snapshot


def finish(report, plan, output, pins, resolutions, lock):
    errors=[];available={};held=False
    try:
        verify(pins,resolutions,plan['absent_inputs'],lock);held=True
        entries,attempts=report['registered_commands'],report['attempted_commands']
        require(attempts == [s['directory'] for s in plan['schedule'][:len(attempts)]] and len(attempts) <= 5,
                'Attempt sequence contains a retry, omission or extra command')
        require(len(entries) == report['native_processes_started'] <= len(attempts) and
                [e['directory'] for e in entries] == attempts[:len(entries)] and
                len({e['pid'] for e in entries}) == len(entries),'Native registration differs')
        receipts={str(p.relative_to(output)) for p in output.glob('*/process.json')}
        require(receipts == {d+'/process.json' for d in attempts},'Native receipt inventory differs')
        for directory in attempts:
            record=json.loads((output/directory/'process.json').read_bytes())
            expected=next((e for e in entries if e['directory'] == directory),None)
            require(record['cleanup_errors'] == [] and not record.get('artifact_errors'),'Native cleanup/artifact failure')
            if expected:
                require(record['native_process_started'] is True and record['pid'] == expected['pid'] and
                        record['direct_child_reaped'] is True and record.get('remaining_process_group',[]) ==
                        record.get('remaining_after_cleanup',[]) == [],'Owned native not reaped or group survived')
            else:require(record['native_process_started'] is False and not record.get('pid'),'Unregistered native process')
        for slot,capture in zip(plan['schedule'],report['captures']):
            current,snapshot=checked_capture(slot,output/slot['directory'],os.getpid(),report['inherited_lock_descriptor'],plan['configuration_pattern'])
            require(current == capture and snapshot == report['validated_artifacts'][slot['directory']],'Validated capture changed')
        require(len(report['captures']) == len(report['validated_artifacts']),'Capture snapshot inventory differs')
        for previous,current in zip(report['captures'],report['captures'][1:]):
            require(stamp(previous['finished_at']) <= stamp(current['started_at']),'Bounded native commands overlapped')
        if report['status'] == SUCCESS:
            require(len(report['captures']) == len(entries) == len(attempts) == 5,'Incomplete five-command stage')
        available=inventory(output,('report.json','terminal.json'))
        for directory,snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')} == snapshot,
                    'Final inventory adopted changed validated bytes')
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,artifacts=available)
    if errors:report['status']='failed-integrity'
    expected_report=(json.dumps(report,indent=2)+'\n').encode('utf-8')
    kb.save(output/'report.json',report)
    try:
        closure=inventory(output,('terminal.json',))
        require({n:v for n,v in closure.items() if n != 'report.json'} == available,'Final artifact closure changed')
        require(closure['report.json'] == dict(bytes=len(expected_report),sha256=hashlib.sha256(expected_report).hexdigest()),
                'Final report differs from validated ledger bytes')
        held=False;verify(pins,resolutions,plan['absent_inputs'],lock);held=True
        require(inventory(output,('terminal.json',)) == closure,'Artifact/report changed during final input replay')
        held=False;lock_identity(lock);held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={}
        kb.save(output/'report.json',report)
    terminal=dict(schema='apl-workspace-five-bounded-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),available_evidence=closure,integrity_errors=errors,
        native_processes_started=report['native_processes_started'],capture_count=len(report['captures']),
        common_mutex_held=held,inherited_lock_descriptor=report['inherited_lock_descriptor'],
        common_mutex_inode=kb.LOCK_INODE,sampler_processes=0,benchmark_samples=0,
        **{k:False for k in FALSE_GATES})
    with (output/'terminal.json').open('x') as stream:stream.write(json.dumps(terminal,indent=2)+'\n')


def run_plan(plan, plan_path, plan_sha, lock):
    output=Path(plan['output']);pins=dict(plan['pins']);pin(pins,plan_path,plan_sha)
    resolutions=dict(plan['input_resolutions'],**{str(plan_path):str(plan_path.resolve())})
    inherited=lock_identity(lock);verify(pins,resolutions,plan['absent_inputs'],lock)
    output.mkdir(parents=True,exist_ok=False)
    report=dict(schema='apl-workspace-five-bounded-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        controller_sha256=sha(__file__),pins=pins,input_resolutions=resolutions,absent_inputs=plan['absent_inputs'],
        inherited_lock_descriptor=inherited,started_at=datetime.now(timezone.utc).isoformat(),active=None,
        attempted_commands=[],registered_commands=[],native_processes_started=0,captures=[],validated_artifacts={},
        sampler_processes=0,benchmark_samples=0,**{k:False for k in FALSE_GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            verify(pins,resolutions,plan['absent_inputs'],lock)
            directory=output/slot['directory'];directory.mkdir()
            for name in ('home','tmp'):(directory/name).mkdir()
            with kb.atomic():
                report['attempted_commands'].append(slot['directory']);kb.save(output/'report.json',report)
            def launched(pid):
                report['native_processes_started']+=1
                report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
                report['active']=dict(directory=slot['directory'],pid=pid);kb.save(output/'report.json',report)
            observe(slot,directory,lock,launched,plan['configuration_pattern'])
            capture,snapshot=checked_capture(slot,directory,os.getpid(),inherited,plan['configuration_pattern'])
            with kb.atomic():
                report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
                report['active']=None;kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
    finally:
        with kb.atomic():finish(report,plan,output,pins,resolutions,lock)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run');run.add_argument('--plan',type=Path,required=True);run.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();physical(args.plan)
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize and
            Path(sys.executable).resolve() == kb.kh.PYTHON.resolve(),'Use exact retained Python -I -S -B without -O')
    def interrupted(signum,frame):raise KeyboardInterrupt('APL bounded stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    with held_mutex() as lock:
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA,'Retained Python changed')
        if args.mode == 'prepare':
            require(not args.plan.exists() and not args.plan.is_relative_to(args.output),'Fresh external plan required')
            plan=build_plan(args.output);verify(plan['pins'],plan['input_resolutions'],plan['absent_inputs'],lock)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('x') as stream:stream.write(json.dumps(plan,indent=2)+'\n')
            print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes_started=0)));return 0
        plan=document(args.plan,args.plan_sha256,{})
        require(plan == build_plan(Path(plan['output'])),'Concrete prepared plan differs')
        report=run_plan(plan,args.plan,args.plan_sha256,lock)
    print(json.dumps(dict(status=report['status'],captures=len(report['captures']),report_sha256=sha(Path(plan['output'])/'report.json'))))
    return 0 if report['status'] == SUCCESS else 1


if __name__ == '__main__':raise SystemExit(main())
