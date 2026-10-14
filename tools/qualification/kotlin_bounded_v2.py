#!/usr/bin/env python3
"""Prepare/run 156 bounded actual-main checks of the twenty retained Kotlin forms.

Both commands require the unchanged, free common timing mutex. prepare is a
hash/metadata operation; run compiles one NEW diagnostic Java wrapper and invokes
retained Kotlin mains, without recompiling any subject or regenerating oracles.
Neither operation admits source work, LOC, subject JIT methods or full timings.
"""
import argparse
import ctypes
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
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/kotlin'
EXPERIMENT = BASE/'bounded-work-v1'
HELPER = BASE/'helper-semantics/run-v3/report.json'
HELPER_SHA = '066592dc37ccf0ca60e5795e02c680a088e8fe9c17448baa049693d77c5679ad'
TERMINAL_SHA = 'c8ffede3ba3ff3dd3827237e50d0b40b2f56fae40b02ea1409acc7c0411e1731'
HELPER_CONTROLLER_SHA = 'd92e0b247d7d45bca1216a0e85335fe0e31a24cc1d607b4b97928115a232fd25'
REFERENCE_CONTROLLER_SHA = 'b5cc9fbe2847048206771fa4eb13551380f3e3c998f72def77bd37963fbfaa75'
TIMEOUT = 30
CLEANUP_TIMEOUT = 5
RSS_LIMIT = 2*1024*1024*1024
FILE_LIMIT = 8*1024*1024
PIPE_CHUNK = 65536
RUNTIME_KEYS = ('JAVA_HOME','RUNTIME_VERSION','VENDOR','OS_ARCH','VM_NAME','VM_INFO',
                'COMPILER','PROCESSORS','MAX_HEAP','FILE_ENCODING','collectors')


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def module(name, expected):
    path = ROOT/'tools/qualification'/name
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Dependency controller changed: '+name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),result.__dict__)
    return result


# Import only definitions from immutable, already reviewed controllers; no main,
# preflight, corpus hashing or native process runs at import time.
kh = module('kotlin_helpers.py', HELPER_CONTROLLER_SHA)
eb = module('elixir_bounded.py', REFERENCE_CONTROLLER_SHA)
save, atomic = kh.save, kh.atomic
LOCK, LOCK_INODE, FLAGS = kh.LOCK, kh.LOCK_INODE, kh.FLAGS
CASE_NAMES, NUMERIC, STREAMS = eb.CASE_NAMES, eb.NUMERIC, eb.STREAMS


def bounded_schedule(rows):
    require(len(rows) == 20 and {r['id'] for r in rows} ==
            {'kotlin-'+b+'-'+v for b in CASE_NAMES for v in ('compact','optimized')},
            'Exactly twenty retained forms required')
    count = 0
    for row in rows:
        bench = row['benchmark']
        require(row['id'] == 'kotlin-'+bench+'-'+row['variant'] and
                [c['case'] for c in row['bounded_cases']] == CASE_NAMES[bench], 'Case inventory/order differs')
        for case in row['bounded_cases']:
            expected_n = int(case['case'][2:]) if bench in NUMERIC else 0
            require(type(case['n']) is int and case['n'] == expected_n and
                    (case['stdin'] is not None) == (bench in STREAMS), 'Unexpected size/input substitution')
            count += 1
    require(count == 156, 'Expected 156 bounded cases')


def aliases(rows):
    result = []
    for bench in CASE_NAMES:
        pair = sorted((r for r in rows if r['benchmark'] == bench),key=lambda r:r['variant'])
        require(len(pair) == 2 and [r['variant'] for r in pair] == ['compact','optimized'], 'Missing alias pair')
        def source_hashes(row): return {x['role']:x['sha256'] for x in row['physical_inputs']}
        def class_hashes(row): return {x['relative_path']:x['sha256'] for x in row['class_artifacts']}
        require(source_hashes(pair[0]) == source_hashes(pair[1]) and
                class_hashes(pair[0]) == class_hashes(pair[1]), 'Previously identical alias bytes differ')
        result.append(dict(benchmark=bench,profile_ids=[r['id'] for r in pair],
            alias_of=[r['alias_of'] for r in pair],source_hashes=source_hashes(pair[0]),
            class_hashes=class_hashes(pair[0]),distinct_optimization_claimed=False))
    return result


def prepare(args):
    require(not args.plan.exists() and not args.output.exists(), 'Fresh plan/output required')
    require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan must be outside output')
    evidence = eb.Evidence()
    helper = evidence.read(HELPER,HELPER_SHA)
    terminal = evidence.read(HELPER.with_name('terminal.json'),TERMINAL_SHA)
    require(helper['status'] == terminal['status'] == 'twenty-retained-helper-semantics-passed' and
            helper['helper_formatting_and_stdio_qualified'] is True and
            terminal['report_sha256'] == HELPER_SHA and
            helper['integrity_errors'] == terminal['integrity_errors'] == terminal['artifact_errors'] == [] and
            helper['subject_main_executions'] == helper['benchmark_samples'] == 0 and
            helper['diagnostic_compiler_launches'] == 1 and helper['helper_jvm_launches'] == 20,
            'Closed helper semantics missing')
    # All physically resolved closure bytes are pinned by the successful helper
    # report. Historical editorial substitutions remain explicit in that report;
    # they do not change expected scored-source/class/runtime bytes.
    for path,digest in helper['pins'].items(): evidence.bind(path,digest,original=True)
    for record in helper['closed_evidence_resolution'].values():
        evidence.bind(record['resolved_path'],record['active_sha256'],original=True)
    for name,item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe helper artifact')
        path = evidence.bind(HELPER.parent/name,item['sha256'],original=True)
        require(path.stat().st_size == item['bytes'], 'Helper artifact size changed')
    compiled = evidence.read(kh.PREPARATION,kh.PREPARATION_SHA)
    require(compiled['status'] == 'Kotlin20-classes-and-bytecode-captured-awaiting-scored-owner-and-runtime-review' and
            compiled['total_compiled_profiles'] == len(compiled['profiles']) == 20 and
            compiled['subject_main_executions'] == 0 and compiled['chart_admission'] is False,
            'Wrong retained cohort')
    require([r['id'] for r in compiled['profiles']] == helper['completed_profile_ids'], 'Helper cohort differs')
    storage_path = BASE/'additive-compile-owners-v1/artifact-storage.json'
    storage_doc = evidence.read(storage_path,helper['pins'][str(storage_path)])
    require(storage_doc['schema'] == 'kotlin-retained-generated-artifacts-v1' and
            storage_doc['original_execution_paths_unchanged'] is True, 'Wrong retained-artifact schema')
    storage = {r['execution_path']:r for r in storage_doc['artifacts']}
    require(len(storage) == len(storage_doc['artifacts']), 'Duplicate class storage mapping')
    review_path = BASE/'source-owner-review-v1/review.json'
    review = evidence.read(review_path,helper['pins'][str(review_path)])
    require(review['schema'] == 'kotlin-source-owner-review-v1' and
            review['status'] == 'source-and-retained-disassembly-reviewed-runtime-gates-open' and
            [r['id'] for r in review['profiles']] == helper['completed_profile_ids'], 'Wrong source/owner review')
    specification_path = BASE/'source-owner-review-v1/bounded-checks.json'
    specification = evidence.read(specification_path,helper['pins'][str(specification_path)])
    require(specification['limits'] == dict(process_timeout_seconds=TIMEOUT,
            group_cleanup_timeout_seconds=CLEANUP_TIMEOUT,maximum_live_subject_processes=1,automatic_retries=0),
            'Bounded limits differ from retained specification')
    references = eb.reference_cases(evidence)
    rows = []; runtime_expected = None; java = None; stdlib = None
    for row,reviewed in zip(compiled['profiles'],review['profiles']):
        bench,variant = row['benchmark'],row['variant']
        require(row['id'] == 'kotlin-'+bench+'-'+variant and bench in CASE_NAMES, 'Unexpected profile')
        sources = row['physical_inputs']
        require(len(sources) == len(reviewed['source_inputs']) == 2 and
                {x['role'] for x in sources} == {'application','application-helper'} and
                all(x['counted'] is True for x in sources) and row['source_to_compile_command_binding'] is True,
                'Complete counted source bundle required')
        source_copies = []
        for item,checked in zip(sources,reviewed['source_inputs']):
            require(item['path'] == checked['physical_path'] and item['sha256'] == checked['recorded_sha256'] and
                    item['role'] == checked['role'] and checked['counted'] is True, 'Source review identity differs')
            evidence.bind(item['path'],item['sha256'],original=True)
            copy = evidence.ref(ROOT/checked['reviewed_source'],item['sha256'],original=True)
            source_copies.append(dict(role=item['role'],**copy))
        require(next(s['sha256'] for s in sources if s['role'] == 'application-helper') == kh.SUPPORT_SOURCE_SHA,
                'Wrong counted helper')
        for key in ('compile_command','bytecode_reader'):
            require(row[key]['exit_status'] == row[key]['final_exit_status'] == 0, 'Compile/owner command failed')
        original,classes = kh.class_directory(row,storage,lambda p,h:evidence.bind(p,h,original=True))
        artifacts = [dict(path=str(classes/Path(a['path']).relative_to(original)),
            relative_path=str(Path(a['path']).relative_to(original)),original_path=a['path'],
            sha256=a['sha256'],bytes=a['bytes']) for a in row['generated_artifacts']]
        owners = {a['relative_path'][:-6].replace('/','.') for a in artifacts if a['relative_path'].endswith('.class')}
        require(owners == set(row['class_owner_names']) == {x['owner'] for x in reviewed['class_owners']} and
                'clbg.Support' in owners and 'clbg.'+bench+'.MainKt' in owners,
                'Exact main/helper/generated owner inventory differs')
        require({a['path']:a['sha256'] for a in row['generated_artifacts'] if a['path'].endswith('.class')} ==
                {x['physical_path']:x['recorded_sha256'] for x in reviewed['class_owners']}, 'Class review hashes differ')
        evidence.bind(ROOT/reviewed['disassembly_path'],reviewed['recorded_disassembly_sha256'],original=True)
        command = row['runtime_command']; candidates = row['runtime_classpath_candidates']
        require(len(candidates) == 1 and candidates[0]['sha256'] == kh.STDLIB_SHA,
                'Exactly the original Kotlin stdlib is required')
        rowjava,rowstdlib = Path(command[0]),Path(candidates[0]['path'])
        require(command == [str(rowjava)]+FLAGS+['-Duser.home='+row['runtime_environment']['HOME'],
            '-Djava.io.tmpdir='+row['runtime_environment']['TMPDIR'].rstrip('/'),
            '-cp',str(original)+os.pathsep+str(rowstdlib),'clbg.'+bench+'.MainKt','{n}'], 'Original main launch differs')
        if java is None: java,stdlib = rowjava,rowstdlib
        require(java == rowjava and stdlib == rowstdlib and row['runtime_environment']['JAVACMD'] == str(java),
                'Cohort runtime differs')
        summary_path = HELPER.parent/row['id']/'summary.json'
        summary = evidence.read(summary_path,helper['pins'][str(summary_path)])
        observed = {key:summary['runtime'][key] for key in RUNTIME_KEYS}
        if runtime_expected is None: runtime_expected = observed
        require(observed == runtime_expected, 'Qualified helper runtimes differ')
        rows.append(dict(id=row['id'],benchmark=bench,variant=variant,alias_of=row['alias_of'],
            physical_inputs=sources,reviewed_source_copies=source_copies,class_artifacts=artifacts,
            class_owner_names=row['class_owner_names'],original_classes=str(original),classes=str(classes),
            class_directory_relocated=original != classes,retained_runtime_command=command,
            runtime_environment=row['runtime_environment'],main_owner='clbg.'+bench+'.MainKt',
            bounded_cases=references[bench]))
    bounded_schedule(rows)
    alias_pairs = aliases(rows)
    for path in (java,java.with_name('javac'),stdlib):
        require(str(path) in helper['pins'], 'Runtime bytes were not pinned by successful helper receipt')
        evidence.bind(path,helper['pins'][str(path)],original=True)
    for path in (Path(__file__).resolve(),ROOT/'tools/qualification/kotlin_helpers.py',
            ROOT/'tools/qualification/elixir_bounded.py',ROOT/'migration/reorganization-paths.tsv',
            EXPERIMENT/'BoundedProbe.java',kh.PYTHON):
        evidence.bind(path,sha(path),original=True)
    require(evidence.pins[str(kh.PYTHON)] == kh.PYTHON_SHA, 'Wrong controller interpreter')
    plan = dict(schema='kotlin-retained-classes-bounded-plan-v1',status='prepared-awaiting-reviewed-native-execution',
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),
        probe_source=str(EXPERIMENT/'BoundedProbe.java'),output=str(args.output.resolve()),
        java=str(java),javac=str(java.with_name('javac')),stdlib=str(stdlib),runtime_expected=runtime_expected,
        profiles=rows,alias_pairs=alias_pairs,pins=evidence.pins,helper_report_sha256=HELPER_SHA,
        helper_terminal_sha256=TERMINAL_SHA,reference_report_sha256=eb.REFERENCE_REPORT_SHA,
        distinct_reference_cases=78,planned_subject_main_invocations=156,planned_diagnostic_compiler_commands=1,
        process_timeout_seconds=TIMEOUT,cleanup_timeout_seconds=CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=RSS_LIMIT,native_file_limit_bytes=FILE_LIMIT,
        stdout_capture_limit_bytes=FILE_LIMIT+PIPE_CHUNK,maximum_live_subject_processes=1,automatic_retries=0,
        subject_recompilations=0,oracle_generator_executions=0,benchmark_samples=0,
        source_work_qualified=False,subject_JIT_method_evidence_qualified=False,
        actual_subject_runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,chart_admission=False)
    args.plan.parent.mkdir(parents=True,exist_ok=True)
    require(not args.plan.exists(), 'Plan appeared during preparation')
    save(args.plan,plan)
    print(json.dumps(dict(status=plan['status'],plan=str(args.plan),sha256=sha(args.plan),native_executions=0)))


class TaskInfo(ctypes.Structure):
    # Darwin SDK sys/proc_info.h: struct proc_taskinfo, PROC_PIDTASKINFO = 4.
    _fields_ = [(name,ctypes.c_uint64) for name in
        ('virtual_size','resident_size','total_user','total_system','threads_user','threads_system')]
    _fields_ += [(name,ctypes.c_int32) for name in ('policy','faults','pageins','cow_faults',
        'messages_sent','messages_received','syscalls_mach','syscalls_unix','csw','threadnum','numrunning','priority')]


class Kernel(kh.Kernel):
    def resident_bytes(self, identity):
        require(ctypes.sizeof(TaskInfo) == 96, 'Unexpected kernel task-info layout')
        # Task teardown can precede the BSD zombie transition. Retry only a
        # failed task-info read while the complete original identity is live.
        # Four 5 ms pauses consume the existing process deadline; no reset.
        for attempt in range(5):
            info = TaskInfo()
            size = self.library.proc_pidinfo(identity['pid'],4,0,ctypes.byref(info),ctypes.sizeof(info))
            after = self.identity(identity['pid'])
            if after is None:
                # A missing BSD record alone is not evidence of process exit.
                try:
                    os.kill(identity['pid'],0)
                except ProcessLookupError:
                    return 0
                raise AssertionError('Kernel identity unavailable for existing process during RSS read')
            require(all(after[k] == identity[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds')),
                    'Process identity changed during RSS read')
            if after['status'] == 5:
                return 0
            if size == ctypes.sizeof(info):
                return info.resident_size
            require(attempt < 4, 'Kernel RSS read failed for live owned process after 5 attempts')
            time.sleep(0.005)


def monitor(kernel, process, record, directory):
    identity = kernel.identity(process.pid)
    require(identity is not None and all(identity[k] == record['identity'][k]
            for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds')),
            'Owned direct-child identity changed before reap')
    group = kernel.group(process.pid)
    rss = sum(kernel.resident_bytes(p) for p in group)
    record['observed_peak_process_group_rss_bytes'] = max(record['observed_peak_process_group_rss_bytes'],rss)
    record['kernel_monitor_samples'] += 1
    require(rss <= RSS_LIMIT, 'Bounded process group exceeded RSS limit')
    for name in ('stderr.bin','classes.log','gc.log','summary.json'):
        path = directory/name
        require(not path.exists() or path.stat().st_size <= FILE_LIMIT, 'Native file exceeded bound: '+name)
    return identity,group


def pump(process,payload,output,deadline,tick):
    offset = 0
    with selectors.DefaultSelector() as selector:
        os.set_blocking(process.stdout.fileno(),False)
        selector.register(process.stdout,selectors.EVENT_READ)
        if payload:
            os.set_blocking(process.stdin.fileno(),False)
            selector.register(process.stdin,selectors.EVENT_WRITE)
        else:
            process.stdin.close()
        while selector.get_map():
            remaining = deadline-time.monotonic()
            if remaining <= 0: raise subprocess.TimeoutExpired(process.args,TIMEOUT)
            tick()
            for key,mask in selector.select(min(0.05,remaining)):
                if key.fileobj is process.stdout:
                    data = os.read(process.stdout.fileno(),PIPE_CHUNK)
                    if data:
                        output.write(data); output.flush()
                        require(output.tell() <= FILE_LIMIT, 'Stdout exceeded bounded capture threshold')
                    else:
                        selector.unregister(process.stdout); process.stdout.close()
                else:
                    try: offset += os.write(process.stdin.fileno(),payload[offset:offset+PIPE_CHUNK])
                    except BrokenPipeError:
                        selector.unregister(process.stdin); process.stdin.close()
                        require(offset == len(payload), 'Child closed stdin before complete payload')
                    else:
                        if offset == len(payload):
                            selector.unregister(process.stdin); process.stdin.close()


def drain(stream,path,deadline):
    """Retain partial output up to a hard FILE_LIMIT+PIPE_CHUNK capture bound."""
    if stream.closed: return
    os.set_blocking(stream.fileno(),False)
    with path.open('r+b') as output,selectors.DefaultSelector() as selector:
        output.seek(0,os.SEEK_END); selector.register(stream,selectors.EVENT_READ)
        while True:
            require(time.monotonic() < deadline, 'Output pipe did not close within cleanup deadline')
            if not selector.select(min(0.05,max(0,deadline-time.monotonic()))): continue
            room = FILE_LIMIT+PIPE_CHUNK-output.tell()
            require(room > 0, 'Stdout capture hard bound reached; further bytes unavailable')
            data = os.read(stream.fileno(),min(PIPE_CHUNK,room))
            if not data: return
            output.write(data); output.flush()


def observe(command,environment,directory,payload,lock,launched,*,kind='bounded-main',
            kernel=None,launch=subprocess.Popen,transfer=pump,drainer=drain):
    kernel = kernel if kernel is not None else Kernel()
    record = dict(status='starting',kind=kind,command=command,environment=environment,cwd=str(directory),
        started_at=datetime.now(timezone.utc).isoformat(),process_timeout_seconds=TIMEOUT,
        cleanup_timeout_seconds=CLEANUP_TIMEOUT,inherited_common_mutex=True,common_mutex_inode=LOCK_INODE,
        native_process_started=False,stop_signals=[],cleanup_errors=[],benchmark_samples=0,
        stdin_bytes=len(payload),stdin_sha256=hashlib.sha256(payload).hexdigest(),
        observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0,
        maximum_process_group_rss_bytes=RSS_LIMIT,native_file_limit_bytes=FILE_LIMIT,
        stdout_capture_limit_bytes=FILE_LIMIT+PIPE_CHUNK,stdout_transport='OS pipe, retained as received',
        stderr_transport='exclusive artifact',source_work_qualified=False,chart_admission=False)
    process = None; reaped = False
    save(directory/'start.json',record)
    try:
        kh.verify_lock(lock)
        with (directory/'stdout.bin').open('xb') as stdout,(directory/'stderr.bin').open('xb') as stderr:
            deadline = time.monotonic()+TIMEOUT
            with atomic() as mask:
                def child_setup():
                    signal.pthread_sigmask(signal.SIG_SETMASK,mask)
                    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
                    resource.setrlimit(resource.RLIMIT_FSIZE,(FILE_LIMIT,FILE_LIMIT))
                process = launch(command,cwd=directory,env=environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                    stderr=stderr,start_new_session=True,pass_fds=(lock.fileno(),),preexec_fn=child_setup)
                # Popen returning is the native-start boundary. Count that
                # fact before any fallible observation or artifact write.
                record.update(status='running',pid=process.pid,pgid=process.pid,native_process_started=True)
                launched(process.pid)
                record['identity'] = kernel.identity(process.pid)
                save(directory/'active.json',record)
            require(record['identity'] and record['identity']['ppid'] == os.getpid() and
                    record['identity']['pgid'] == process.pid, 'Missing owned native identity')
            tick = lambda:monitor(kernel,process,record,directory)
            transfer(process,payload,stdout,deadline,tick)
            while True:
                identity,group = tick()
                if identity['status'] == 5:
                    record['leader_identity_before_reap'] = identity
                    record['remaining_process_group'] = group
                    require(not group, 'Native command left live descendants')
                    break
                if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(command,TIMEOUT)
                time.sleep(0.01)
            with atomic():
                record['exit_status'] = process.wait(timeout=max(0.001,deadline-time.monotonic()))
                reaped = True
            require(record['exit_status'] == 0, 'Native command exited unsuccessfully')
        require((directory/'stderr.bin').read_bytes() == b'', 'Unexpected stderr; raw bytes retained')
        if kind == 'diagnostic-compile':
            require((directory/'stdout.bin').read_bytes() == b'', 'Diagnostic compiler stdout not empty')
        record['status'] = 'native-passed'
    except BaseException as error:
        record.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__,
                      timed_out=isinstance(error,subprocess.TimeoutExpired))
        if process is not None and not reaped:
            with atomic():
                deadline = time.monotonic()+CLEANUP_TIMEOUT
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
        with atomic():
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
            if record['cleanup_errors'] or record.get('artifact_errors'): record['status'] = 'failed-cleanup-or-artifacts'
            save(directory/'process.json',record)
            kh.verify_lock(lock)
            require(not record['cleanup_errors'] and not record.get('artifact_errors'), 'Cleanup or output retention failed')
    return record


def uri_path(source):
    parsed = urlparse(source)
    require(parsed.scheme == 'file' and parsed.netloc in ('','localhost'), 'Expected local file origin')
    return Path(unquote(parsed.path)).resolve()


def validate_log(text,classes,stdlib,probe_classes,owners):
    observed = {}
    for line in text.splitlines():
        if '[class,load]' not in line: continue
        match = re.search(r'\[class,load\]\s+(\S+) source: (.+)$',line)
        require(match, ('Unrecognized class-load evidence',line))
        owner,source = match.groups()
        if owner.startswith('clbg.'): require(owner in owners, ('Unretained benchmark owner',owner))
        if source.startswith('file:'):
            expected = classes if owner in owners else stdlib if owner.startswith('kotlin.') else probe_classes
            require(uri_path(source) == expected and
                    (owner in owners or owner.startswith('kotlin.') or owner in
                     {'boundedqualification.BoundedProbe','boundedqualification.BoundedProbe$SubjectLoader'}),
                    ('Unexpected non-platform class origin',owner,source))
        else:
            hidden = re.fullmatch(r'(.+)\$\$Lambda(?:\$\d+)?/0x[0-9a-fA-F]+',owner)
            enclosing = hidden[1] if hidden else None
            host_origin = observed.get(source,'')
            platform_lambda = enclosing is not None and (enclosing == source or enclosing.startswith(source+'$')) and \
                source.startswith(('java.','jdk.','sun.','com.sun.')) and \
                host_origin.startswith(('jrt:/','shared objects file')) and observed.get(enclosing) == host_origin
            require(source.startswith(('jrt:/','shared objects file')) or
                    source == '__JVM_LookupDefineClass__' and owner.startswith(('java.','jdk.')) or platform_lambda,
                    ('Unknown class origin',owner,source))
        observed[owner] = source
    require('boundedqualification.BoundedProbe' in observed and 'clbg.Support' in observed,
            'Incomplete main/helper class-load evidence')
    return observed


def validate_summary(summary,row,case,plan,probe_classes,directory,options):
    require(summary['status'] == 'passed' and summary['benchmark_main_invocations'] == 1 and
            summary['benchmark_main_executions'] == 1 and summary['benchmark_main_returns'] == 1 and
            summary['benchmark_main_returned'] is True and summary['main_loaded'] is True and
            summary['main_initialized'] is True and summary['main_owner'] == row['main_owner'] and
            summary['main_arguments'] == [str(case['n'])], 'Exact retained main was not called and returned once')
    classes,stdlib = Path(row['classes']),Path(plan['stdlib'])
    require(summary['subject_owner_names'] == row['class_owner_names'] and
            summary['denied_owners'] == ['clbg.UnexpectedOwner'], 'Wrong exact owner inventory/canary')
    require(uri_path(summary['main_code_source']) == classes and
            uri_path(summary['main_resource']) == classes/Path(row['main_owner'].replace('.','/')+'.class'),
            'Main class origin differs')
    origins = summary['non_platform_class_origins']
    require(row['main_owner'] in origins and 'clbg.Support' in origins, 'Actual main/helper load missing')
    resources = summary['non_platform_class_resources']
    require(set(resources) == set(origins), 'Loaded resource/origin inventories differ')
    for owner,source in origins.items():
        require(owner in row['class_owner_names'] or owner.startswith('kotlin.'), 'Unretained loader owner')
        expected = classes if owner in row['class_owner_names'] else stdlib
        require(uri_path(source) == expected, 'Loader origin differs')
        resource_name = owner.replace('.','/')+'.class'
        if owner in row['class_owner_names']:
            require(uri_path(resources[owner]) == classes/resource_name, 'Subject class resource differs')
        else:
            resource = resources[owner]
            require(resource.startswith('jar:') and '!/' in resource, 'Expected stdlib jar resource')
            jar,relative = resource[4:].split('!/',1)
            require(uri_path(jar) == stdlib and relative == resource_name, 'Stdlib class resource differs')
    inventory = summary['owner_inventory']
    require([item['owner'] for item in inventory] == row['class_owner_names'], 'Owner resource inventory differs')
    for item in inventory:
        require(uri_path(item['expected_code_source']) == classes and
                uri_path(item['resource']) == classes/(item['owner'].replace('.','/')+'.class'),
                'Retained owner resource differs')
    require(uri_path(summary['probe_code_source']) == probe_classes and
            uri_path(summary['probe_resource']) == probe_classes/'boundedqualification/BoundedProbe.class' and
            [uri_path(x) for x in summary['loader_urls']] == [classes,stdlib] and
            summary['loader_parent'] == 'jdk.internal.loader.ClassLoaders$PlatformClassLoader' and
            summary['denied_owner_canary'] is True, 'Diagnostic loader origin/configuration differs')
    require({key:summary['runtime'][key] for key in RUNTIME_KEYS} == plan['runtime_expected'], 'Runtime identity differs')
    runtime = summary['runtime']
    require(runtime['flags'] == options and runtime['CLASS_PATH'] == str(probe_classes) and
            runtime['USER_HOME'] == str(directory/'home') and runtime['JAVA_TMPDIR'] == str(directory/'tmp') and
            runtime['JVM_MAIN'] == 'boundedqualification.BoundedProbe', 'Runtime command/configuration differs')


def run(args,lock):
    require(sha(args.plan) == args.plan_sha256, 'Plan differs from reviewed hash')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'kotlin-retained-classes-bounded-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['planned_subject_main_invocations'] == 156 and plan['distinct_reference_cases'] == 78 and
            plan['planned_diagnostic_compiler_commands'] == 1, 'Wrong bounded plan/controller')
    bounded_schedule(plan['profiles']); require(aliases(plan['profiles']) == plan['alias_pairs'], 'Alias inventory differs')
    output = Path(plan['output']); require(not output.exists(), 'Fresh output required; no automatic retry')
    pins = dict(plan['pins']); pins[str(args.plan.resolve())] = args.plan_sha256
    for path,digest in pins.items(): require(sha(path) == digest, 'Preflight input changed: '+path)
    output.mkdir(parents=True)
    report = dict(schema='kotlin-retained-classes-bounded-results-v1',status='running',
        started_at=datetime.now(timezone.utc).isoformat(),plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,
        pins=pins,profiles=[],cases=[],alias_pairs=plan['alias_pairs'],active=None,native_launch_requests=0,
        native_processes_started=0,diagnostic_compiler_processes_started=0,bounded_jvm_processes_started=0,
        qualified_bounded_cases=0,native_process_ids=[],observed_subject_main_invocations=0,
        observed_subject_main_returns=0,subject_recompilations=0,oracle_generator_executions=0,benchmark_samples=0,
        bounded_outputs_qualified=False,source_work_qualified=False,subject_JIT_method_evidence_qualified=False,
        actual_subject_runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,chart_admission=False)
    save(output/'report.json',report)
    def register(kind,directory,profile_id=None,label=None):
        report['native_launch_requests'] += 1
        report['active'] = dict(kind=kind,id=profile_id,case=label,receipt=str(directory/'process.json'),pid=None)
        save(output/'report.json',report)
        def launched(pid):
            report['native_processes_started'] += 1
            report['diagnostic_compiler_processes_started' if kind == 'diagnostic-compile' else 'bounded_jvm_processes_started'] += 1
            report['native_process_ids'].append(dict(kind=kind,id=profile_id,case=label,pid=pid,pgid=pid))
            report['active']['pid'] = pid; save(output/'report.json',report)
        return launched
    try:
        compile_case = output/'diagnostic-compile'; compile_case.mkdir()
        env = kh.environment(plan['profiles'][0]['runtime_environment'],compile_case)
        probe_classes = output/'probe-classes'; probe_classes.mkdir()
        source_copy = compile_case/'BoundedProbe.java'; source_copy.write_bytes(Path(plan['probe_source']).read_bytes())
        require(sha(source_copy) == pins[plan['probe_source']], 'Probe changed while copying')
        command = [plan['javac']]+['-J'+flag for flag in FLAGS]+[
            '-J-Duser.home='+str(compile_case/'home'),'-J-Djava.io.tmpdir='+str(compile_case/'tmp'),
            '--release','17','-d',str(probe_classes),str(source_copy)]
        observe(command,env,compile_case,b'',lock,register('diagnostic-compile',compile_case),kind='diagnostic-compile')
        generated = {str(p.relative_to(probe_classes)) for p in probe_classes.rglob('*') if p.is_file()}
        require(generated == {'boundedqualification/BoundedProbe.class','boundedqualification/BoundedProbe$SubjectLoader.class'},
                'Unexpected diagnostic generated class set')
        for relative in generated:
            path = probe_classes/relative; raw = path.read_bytes()
            require(raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8],'big') == 61, 'Wrong diagnostic class target')
            pins[str(path)] = sha(path)
        report['active'] = None; save(output/'report.json',report)
        for row in plan['profiles']:
            for case in row['bounded_cases']:
                kh.verify_lock(lock)
                # Directory inventories are rechecked even when all known files
                # still hash correctly, so extra classes cannot enter the loader.
                actual = {str(p.relative_to(row['classes'])) for p in Path(row['classes']).rglob('*') if p.is_file()}
                require(actual == {a['relative_path'] for a in row['class_artifacts']} and
                        not any(p.is_symlink() for p in Path(row['classes']).rglob('*')), 'Subject class directory changed')
                hot = row['physical_inputs']+row['class_artifacts']+[case['expected']]
                if case['stdin']: hot.append(case['stdin'])
                for item in hot: require(sha(item['path']) == item['sha256'], 'Active source/class/reference changed')
                for relative in generated:
                    path = probe_classes/relative; require(sha(path) == pins[str(path)], 'Diagnostic class changed')
                directory = output/row['id']/case['case']; directory.mkdir(parents=True)
                env = kh.environment(row['runtime_environment'],directory)
                payload = Path(case['stdin']['path']).read_bytes() if case['stdin'] else b''
                expected = Path(case['expected']['path']).read_bytes()
                (directory/'stdin.bin').write_bytes(payload); (directory/'expected.stdout').write_bytes(expected)
                (directory/'owners.txt').write_text('\n'.join(row['class_owner_names'])+'\n')
                options = FLAGS+[f'-Duser.home={directory}/home',f'-Djava.io.tmpdir={directory}/tmp',
                    f'-Xlog:class+load=info:file={directory}/classes.log:uptime,tags',
                    f'-Xlog:gc*=info:file={directory}/gc.log:uptime,tags']
                command = [plan['java']]+options+['-cp',str(probe_classes),'boundedqualification.BoundedProbe',
                    row['classes'],plan['stdlib'],str(directory/'owners.txt'),str(directory/'summary.json'),
                    row['main_owner'],str(case['n'])]
                observe(command,env,directory,payload,lock,register('bounded-main',directory,row['id'],case['case']))
                summary = json.loads((directory/'summary.json').read_bytes())
                validate_summary(summary,row,case,plan,probe_classes,directory,options)
                observed = validate_log((directory/'classes.log').read_text(),Path(row['classes']),
                    Path(plan['stdlib']),probe_classes,set(row['class_owner_names']))
                require(row['main_owner'] in observed, 'Class log omits retained main')
                logged = {owner:source for owner,source in observed.items()
                          if owner.startswith(('clbg.','kotlin.'))}
                require(set(logged) == set(summary['non_platform_class_origins']) and
                        all(uri_path(source) == uri_path(summary['non_platform_class_origins'][owner])
                            for owner,source in logged.items()), 'JVM and loader origin observations differ')
                require('Using G1' in (directory/'gc.log').read_text(), 'Missing G1 runtime evidence')
                validation = eb.output_validation(row['benchmark'],(directory/'stdout.bin').read_bytes(),expected)
                validated = dict(status='bounded-output-passed',id=row['id'],case=case['case'],n=case['n'],
                    reference_evidence=case,validation=validation,loaded_classes=observed,
                    main_invocations=1,main_returns=1,exact_retained_main_and_helper_loaded=True,
                    runtime_identity_observed=True,subject_recompilations=0,benchmark_samples=0,
                    source_work_qualified=False,full_timings_qualified=False,chart_admission=False)
                save(directory/'validated.json',validated)
                report['cases'].append(dict(id=row['id'],case=case['case'],process=str(directory/'process.json'),
                    process_sha256=sha(directory/'process.json'),validated=str(directory/'validated.json'),
                    validated_sha256=sha(directory/'validated.json'),status=validated['status']))
                report['qualified_bounded_cases'] += 1; report['active'] = None; save(output/'report.json',report)
            report['profiles'].append(row['id']); save(output/'report.json',report)
            print('Validated retained Kotlin bounded outputs: '+row['id'],flush=True)
        require(report['bounded_jvm_processes_started'] == report['qualified_bounded_cases'] == 156 and
                report['diagnostic_compiler_processes_started'] == 1 and len(report['profiles']) == 20,
                'Incomplete bounded execution ledger')
        report.update(status='all20-bounded-output-passed-awaiting-work-JIT-and-LOC',bounded_outputs_qualified=True)
    except BaseException as error:
        report.update(status='failed',bounded_outputs_qualified=False,error=str(error) or type(error).__name__,
                      error_type=type(error).__name__)
        raise
    finally:
        with atomic():
            native_records = []; record_errors = []
            for path in output.rglob('process.json'):
                try:
                    receipt = json.loads(path.read_bytes())
                    if receipt['native_process_started']:
                        native_records.append(dict(path=str(path.relative_to(output)),pid=receipt['pid'],kind=receipt['kind'],
                            status=receipt['status'],direct_child_reaped=receipt['direct_child_reaped']))
                    summary_path = path.with_name('summary.json')
                    if receipt['kind'] == 'bounded-main' and summary_path.is_file():
                        summary = json.loads(summary_path.read_bytes())
                        report['observed_subject_main_invocations'] += summary['benchmark_main_invocations']
                        report['observed_subject_main_returns'] += summary['benchmark_main_returns']
                except BaseException as error: record_errors.append(dict(path=str(path),error=str(error)))
            report['registered_native_commands'] = native_records
            if len(native_records) != report['native_processes_started']:
                record_errors.append(dict(error='Native launch and final process-receipt counts differ'))
            if report['bounded_outputs_qualified'] and not (
                    len(native_records) == 157 and report['observed_subject_main_invocations'] ==
                    report['observed_subject_main_returns'] == 156 and
                    all(r['status'] == 'native-passed' and r['direct_child_reaped'] for r in native_records)):
                record_errors.append(dict(error='Successful native/main observation inventory incomplete'))
            report['process_receipt_errors'] = record_errors
            integrity_errors = []
            for path,digest in pins.items():
                try: require(sha(path) == digest, 'Pinned input changed')
                except BaseException as error: integrity_errors.append(dict(path=path,error=str(error)))
            report['integrity_errors'] = integrity_errors
            if integrity_errors or record_errors: report.update(status='failed-input-or-native-integrity',bounded_outputs_qualified=False)
            report['finished_at'] = datetime.now(timezone.utc).isoformat(); save(output/'report.json',report)
            artifacts = {}; artifact_errors = []
            for path in output.rglob('*'):
                if path.is_file():
                    try: artifacts[str(path.relative_to(output))] = dict(sha256=sha(path),bytes=path.stat().st_size)
                    except BaseException as error: artifact_errors.append(dict(path=str(path),error=str(error)))
            if artifact_errors:
                report.update(status='failed-artifact-integrity',bounded_outputs_qualified=False,artifact_errors=artifact_errors)
                save(output/'report.json',report)
                artifacts['report.json'] = dict(sha256=sha(output/'report.json'),bytes=(output/'report.json').stat().st_size)
            kh.verify_lock(lock)
            save(output/'terminal.json',dict(status=report['status'],report_sha256=sha(output/'report.json'),
                available_evidence=artifacts,integrity_errors=integrity_errors,artifact_errors=artifact_errors,
                process_receipt_errors=record_errors,native_processes_started=report['native_processes_started'],
                diagnostic_compiler_processes_started=report['diagnostic_compiler_processes_started'],
                bounded_jvm_processes_started=report['bounded_jvm_processes_started'],
                observed_subject_main_invocations=report['observed_subject_main_invocations'],
                observed_subject_main_returns=report['observed_subject_main_returns'],
                qualified_bounded_cases=report['qualified_bounded_cases'],common_mutex_held=True,common_mutex_inode=LOCK_INODE,
                subject_recompilations=0,benchmark_samples=0,source_work_qualified=False,
                canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False))
            require(not integrity_errors and not artifact_errors and not record_errors, 'Input/output/native integrity failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    prepare_parser = sub.add_parser('prepare'); prepare_parser.add_argument('--plan',type=Path,required=True)
    prepare_parser.add_argument('--output',type=Path,required=True)
    run_parser = sub.add_parser('run'); run_parser.add_argument('--plan',type=Path,required=True)
    run_parser.add_argument('--plan-sha256',required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kh.PYTHON.resolve() and sys.flags.isolated and
            sys.flags.no_site and sys.flags.dont_write_bytecode, 'Use pinned Python with -I -S -B')
    def interrupted(signum,frame): raise KeyboardInterrupt('Kotlin bounded qualification interrupted: '+str(signum))
    for sig in kh.SIGNALS: signal.signal(sig,interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); kh.verify_lock(lock)
        if args.action == 'prepare': prepare(args)
        else: run(args,lock)


if __name__ == '__main__': main()
