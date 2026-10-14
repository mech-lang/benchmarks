"""Qualify all twenty retained Kotlin Support classes; never admit benchmark mains."""
import argparse
from contextlib import contextmanager
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
PREPARATION = BASE/'additive-compile-owners-v1/preparation-result.json'
PREPARATION_SHA = '2ab7206a97782975827c743453bfdfee1c4a9f4c95c926a55b157fc07200db8a'
SUPPORT_SOURCE_SHA = '3d8c5d6be74d4745b830ac77b05793a2cf5a32544d5314fda8b1dda874da5c66'
SUPPORT_CLASS_SHA = 'fae4ac33b4834dfca46c9dd6ad49cab97d5fddf0a5140b3ae586af3970671ec7'
STDLIB_SHA = 'bd8250210584cb659847dce9cda660f8e9906e5def7fbebcea93dc6dcb6a88a3'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def load_module(path, pins):
    path = Path(path).resolve()
    raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
    require(str(path) not in pins or pins[str(path)] == digest, 'Controller module changed')
    pins[str(path)] = digest
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


@contextmanager
def atomic():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try: yield previous
    finally: signal.pthread_sigmask(signal.SIG_SETMASK, previous)


class BSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]
    _fields_ += [('comm',ctypes.c_char*16),('name',ctypes.c_char*32)]
    _fields_ += [(name,ctypes.c_uint32) for name in ('nfiles','pgid','jobc','tdev','tpgid')]
    _fields_ += [('nice',ctypes.c_int32),('birth_seconds',ctypes.c_uint64),('birth_microseconds',ctypes.c_uint64)]


class Kernel:
    """Kernel identity/group reads avoid a second native process in timeout cleanup."""
    def __init__(self):
        self.library = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        self.library.proc_pidinfo.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        self.library.proc_pidinfo.restype = ctypes.c_int
        self.library.proc_listallpids.argtypes = [ctypes.c_void_p,ctypes.c_int]
        self.library.proc_listallpids.restype = ctypes.c_int
        require(ctypes.sizeof(BSDInfo) == 136, 'Unexpected kernel identity layout')

    def identity(self, pid):
        info = BSDInfo()
        # XNU's PROC_PIDTBSDINFO searches unreaped zombies only with arg != 0.
        # Keep their identity visible until this owner explicitly calls wait.
        if self.library.proc_pidinfo(pid,3,1,ctypes.byref(info),ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        require(info.pid == pid and info.birth_seconds > 0, 'Invalid kernel identity')
        return {name:getattr(info,name) for name in
                ('pid','ppid','pgid','status','birth_seconds','birth_microseconds')}

    def group(self, pgid):
        capacity = self.library.proc_listallpids(None,0)+256
        require(capacity > 256, 'Process inventory failed')
        buffer = (ctypes.c_int*capacity)()
        count = self.library.proc_listallpids(buffer,ctypes.sizeof(buffer))
        require(0 <= count < capacity, 'Process inventory overflow or failure')
        return [row for pid in buffer[:count] if pid > 0 and (row := self.identity(pid))
                and row['pgid'] == pgid and row['status'] != 5]


def pump(process, payload, output, deadline):
    """Real pipes in both directions, with partial stdout persisted as it arrives."""
    offset = 0
    with selectors.DefaultSelector() as selector:
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ)
        if payload:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE)
        else:
            process.stdin.close()
        while selector.get_map():
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, 30)
            for key, mask in selector.select(min(0.1, remaining)):
                if key.fileobj is process.stdout:
                    data = os.read(process.stdout.fileno(), 65536)
                    if data:
                        output.write(data); output.flush()
                    else:
                        selector.unregister(process.stdout); process.stdout.close()
                else:
                    try:
                        offset += os.write(process.stdin.fileno(), payload[offset:offset+65536])
                    except BrokenPipeError:
                        selector.unregister(process.stdin); process.stdin.close()
                        require(offset == len(payload), 'Child closed stdin before complete payload')
                    else:
                        if offset == len(payload):
                            selector.unregister(process.stdin); process.stdin.close()


def verify_lock(lock):
    opened, named = os.fstat(lock.fileno()), LOCK.stat()
    require((opened.st_dev,opened.st_ino) == (named.st_dev,named.st_ino)
            and opened.st_ino == LOCK_INODE, 'Common mutex changed')


def retain_pipe(stream, path, deadline):
    """Drain output buffered at failure after killing the owned group."""
    if stream.closed:
        return
    os.set_blocking(stream.fileno(),False)
    with path.open('r+b') as output, selectors.DefaultSelector() as selector:
        output.seek(0,os.SEEK_END)
        selector.register(stream,selectors.EVENT_READ)
        while True:
            remaining = deadline-time.monotonic()
            require(remaining > 0, 'Output pipe did not close within cleanup deadline')
            if not selector.select(min(0.1,remaining)):
                continue
            data = os.read(stream.fileno(),65536)
            if not data:
                return
            output.write(data); output.flush()


def observe(command, environment, directory, payload, expected_stdout, lock,
            *, kernel=None, launch=subprocess.Popen, transfer=pump, drain=retain_pipe):
    kernel = kernel if kernel is not None else Kernel()
    record = dict(status='starting', command=command, environment=environment, cwd=str(directory),
        started_at=datetime.now(timezone.utc).isoformat(), process_timeout_seconds=30,
        cleanup_timeout_seconds=5, inherited_common_mutex=True, common_mutex_inode=LOCK_INODE,
        benchmark_samples=0, subject_main_executions=0, stop_signals=[], cleanup_errors=[],
        stdin_bytes=len(payload), stdin_sha256=hashlib.sha256(payload).hexdigest(),
        stdout_transport='OS pipe, drained to exclusive artifact', stderr_transport='exclusive artifact')
    process = None; reaped = False
    save(directory/'start.json', record)
    try:
        verify_lock(lock)
        with (directory/'stdout.bin').open('xb') as stdout, (directory/'stderr.bin').open('xb') as stderr:
            deadline = time.monotonic()+30
            with atomic() as mask:
                def child_setup():
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
                    resource.setrlimit(resource.RLIMIT_CORE, (0,0))
                process = launch(command, cwd=directory, env=environment, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=stderr, start_new_session=True,
                    pass_fds=(lock.fileno(),), preexec_fn=child_setup)
                record.update(status='running', pid=process.pid, pgid=process.pid,
                              identity=kernel.identity(process.pid))
            identity = record['identity']
            require(identity and identity['ppid'] == os.getpid() and identity['pgid'] == process.pid,
                    'Missing owned native identity')
            save(directory/'active.json', record)
            transfer(process, payload, stdout, deadline)
            # Do not reap the leader until its group is empty: its PID remains
            # reserved throughout any cleanup and cannot identify a foreign group.
            while (identity := kernel.identity(process.pid)) and identity['status'] != 5:
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, 30)
                time.sleep(0.01)
            require(identity is not None, 'Owned child identity vanished before reap')
            record['remaining_process_group'] = kernel.group(process.pid)
            require(not record['remaining_process_group'], 'Native command left live descendants')
            with atomic():
                record['exit_status'] = process.wait(timeout=max(0.001, deadline-time.monotonic()))
                reaped = True
            require(record['exit_status'] == 0, 'Native command exited unsuccessfully')
        require((directory/'stderr.bin').read_bytes() == b'', 'Unexpected stderr; raw bytes retained')
        require((directory/'stdout.bin').read_bytes() == expected_stdout, 'Complete stdout differs; raw bytes retained')
        record['status'] = 'passed'
    except BaseException as error:
        record.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__,
                      timed_out=isinstance(error,subprocess.TimeoutExpired))
        if process is not None and not reaped:
            with atomic():
                deadline = time.monotonic()+5
                try:
                    # Unreaped direct-child PID ownership is stronger than a
                    # textual ps match and remains valid for a zombie leader.
                    try:
                        if kernel.group(process.pid):
                            os.killpg(process.pid, signal.SIGKILL)
                            record['stop_signals'].append(int(signal.SIGKILL))
                    except ProcessLookupError:
                        pass
                except BaseException as cleanup_error:
                    record['cleanup_errors'].append(str(cleanup_error) or type(cleanup_error).__name__)
                try:
                    drain(process.stdout,directory/'stdout.bin',deadline)
                except BaseException as cleanup_error:
                    record['cleanup_errors'].append(str(cleanup_error) or type(cleanup_error).__name__)
                try:
                    while remaining := kernel.group(process.pid):
                        record['remaining_after_cleanup'] = remaining
                        require(time.monotonic() < deadline, 'Owned group survived cleanup deadline')
                        time.sleep(0.01)
                    record['remaining_after_cleanup'] = []
                    record['exit_status'] = process.wait(timeout=max(0.001,deadline-time.monotonic()))
                    reaped = True
                except BaseException as cleanup_error:
                    record['cleanup_errors'].append(str(cleanup_error) or type(cleanup_error).__name__)
        raise
    finally:
        if process is not None:
            for stream in (process.stdin,process.stdout):
                if stream is not None:
                    try: stream.close()
                    except BaseException as error: record['cleanup_errors'].append(str(error))
        record['direct_child_reaped'] = reaped
        for name in ('stdout','stderr'):
            path = directory/(name+'.bin')
            if path.is_file():
                record[name+'_bytes'],record[name+'_sha256'] = path.stat().st_size,sha(path)
            else:
                record.setdefault('artifact_errors',[]).append('Missing '+str(path))
        record['complete_output_matches'] = (record.get('stdout_bytes'),record.get('stdout_sha256')) == (
            len(expected_stdout),hashlib.sha256(expected_stdout).hexdigest())
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        if record['cleanup_errors'] or record.get('artifact_errors'):
            record['status'] = 'failed-cleanup-or-artifacts'
        save(directory/'process.json',record)
        verify_lock(lock)
        require(not record['cleanup_errors'] and not record.get('artifact_errors'), 'Cleanup or output retention failed')
    return record


def environment(saved, directory):
    for name in ('home','tmp','config'):
        (directory/name).mkdir()
    env = dict(saved)
    require(not any(key in env for key in ('JDK_JAVA_OPTIONS','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS')), 'Injected JVM options')
    env.update(HOME=str(directory/'home'), XDG_CONFIG_HOME=str(directory/'config'), TMPDIR=str(directory/'tmp')+os.sep)
    env['JAVA_OPTS'] = ' '.join(FLAGS+[f'-Duser.home={directory}/home',f'-Djava.io.tmpdir={directory}/tmp'])
    require(all(env[key] == '' for key in ('CLASSPATH','KOTLIN_RUNNER','KOTLIN_COMPILER','KOTLIN_TOOL')),
            'Injected Kotlin/classpath options')
    return env


def class_directory(row, storage, bind):
    original = Path(row['compile_command']['command'][-1])
    selected = original
    # A whole directory relocates as a unit; partial original/retained mixtures
    # are rejected. The mapping never supplies or changes expected artifact hashes.
    if not original.is_dir():
        copies = [storage.get(item['path']) for item in row['generated_artifacts']]
        require(all(copies), 'Missing declared retained class copy')
        roots = {str(Path(copy['stored_path']).parents[len(Path(item['path']).relative_to(original).parts)-1])
                 for item,copy in zip(row['generated_artifacts'],copies)}
        require(len(roots) == 1, 'Retained class copies span directories')
        selected = ROOT/roots.pop()
    require(selected.is_dir() and not selected.is_symlink(), 'Missing selected classes directory')
    expected = {}
    for item in row['generated_artifacts']:
        relative = Path(item['path']).relative_to(original)
        path = selected/relative
        if selected != original:
            copy = storage[item['path']]
            require(copy['sha256'] == item['sha256'] and copy['bytes'] == item['bytes'] and
                    path == ROOT/copy['stored_path'], 'Retained class mapping disagrees with compiler receipt')
        bind(path,item['sha256'])
        require(path.stat().st_size == item['bytes'], 'Class artifact size changed')
        expected[str(relative)] = item['sha256']
    actual = {str(p.relative_to(selected)) for p in selected.rglob('*') if p.is_file()}
    require(actual == set(expected) and not any(p.is_symlink() for p in selected.rglob('*')), 'Class directory changed')
    require(expected['clbg/Support.class'] == SUPPORT_CLASS_SHA, 'Unexpected retained helper class')
    return original,selected.resolve()


def validate_log(text, classes, stdlib, probe_classes):
    observed = {}
    for line in text.splitlines():
        if '[class,load]' not in line:
            continue
        match = re.search(r'\[class,load\]\s+(\S+) source: (.+)$',line)
        require(match, ('Unrecognized class-load evidence',line))
        owner,source = match.groups()
        if owner.startswith('clbg.'):
            require(owner == 'clbg.Support', ('Prohibited benchmark owner loaded',owner))
        if source.startswith('file:'):
            path = Path(unquote(urlparse(source).path)).resolve()
            expected = classes if owner == 'clbg.Support' else stdlib if owner.startswith('kotlin.') else probe_classes
            require(path == expected and (owner == 'clbg.Support' or owner.startswith(('kotlin.','helperqualification.'))),
                    ('Unexpected non-platform class origin',owner,source))
        else:
            # A nested platform class's hidden lambda can log its outer nest
            # host. Require both enclosing class and host already loaded from
            # the same platform image, plus the exact hidden-lambda name shape.
            hidden_lambda = re.fullmatch(r'(.+)\$\$Lambda(?:\$\d+)?/0x[0-9a-fA-F]+',owner)
            enclosing = hidden_lambda[1] if hidden_lambda else None
            host_origin = observed.get(source,'')
            platform_lambda = enclosing is not None and (enclosing == source or enclosing.startswith(source+'$')) and \
                source.startswith(('java.','jdk.','sun.','com.sun.')) and \
                host_origin.startswith(('jrt:/','shared objects file')) and observed.get(enclosing) == host_origin
            require(source.startswith(('jrt:/','shared objects file')) or
                    source == '__JVM_LookupDefineClass__' and owner.startswith(('java.','jdk.')) or platform_lambda,
                    ('Unknown class origin',owner,source))
        observed[owner] = source
    require('clbg.Support' in observed and 'helperqualification.HelperProbe' in observed, 'Incomplete class-load log')
    return observed


def validate_summary(summary, saved, row, classes, stdlib, probe_classes, case, options, payload):
    require(summary['status'] == 'passed' and summary['benchmark_main_executions'] == 0 and
            summary['main_loaded'] is False, 'Incomplete helper probe')
    require(summary['denied_owners'] == ['clbg.'+row['benchmark']+'.MainKt','clbg.UnexpectedHelper'], 'Missing negative loader canary')
    require(summary['support_code_source'] == classes.as_uri().replace('file:///','file:/')+'/' and
            summary['support_resource'] == (classes/'clbg/Support.class').as_uri().replace('file:///','file:/'),
            'Support origin differs')
    origins = summary['non_platform_class_origins']
    require('clbg.Support' in origins and all(name == 'clbg.Support' or name.startswith('kotlin.') for name in origins),
            'Unexpected loader owner')
    for name,source in origins.items():
        expected = classes if name == 'clbg.Support' else stdlib
        require(Path(unquote(urlparse(source).path)).resolve() == expected, 'Loader origin mismatch')
    require(summary['format_vectors'] == 1536 and len(summary['format_rejected']) == 5 and
            len(summary['integer_accepted']) == 8 and len(summary['integer_rejected']) == 7 and
            len(summary['line_cases']) == 8, 'Semantic case inventory incomplete')
    require(summary['input_bytes'] == len(payload) and summary['repeated_eof'] is True and
            summary['byte_values_verified'] == 256 and summary['write_overloads_verified'] == 2, 'I/O cases incomplete')
    runtime = summary['runtime']
    for key in ('JAVA_HOME','RUNTIME_VERSION','VENDOR','OS_ARCH','VM_NAME','VM_INFO','COMPILER','PROCESSORS','MAX_HEAP'):
        require(runtime[key] == saved['actual_generic_runtime_probe'][key], ('Runtime identity changed',key))
    require(runtime['FILE_ENCODING'] == 'UTF-8' and runtime['CLASS_PATH'] == str(probe_classes) and
            runtime['USER_HOME'] == str(case/'home') and runtime['JAVA_TMPDIR'] == str(case/'tmp') and
            runtime['flags'] == options and runtime['collectors'] == saved['actual_collectors'], 'Runtime configuration changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); output = args.output.resolve()
    require(not output.exists(), 'Fresh output required; no overwrite or automatic retry')
    def interrupted(signum,frame):
        raise KeyboardInterrupt('Helper qualification interrupted: '+str(signum))
    for sig in SIGNALS: signal.signal(sig,interrupted)
    with LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB); verify_lock(lock)
        output.mkdir(parents=True)
        pins = {}; evidence = None
        report = dict(status='running',scope='twenty-retained-Kotlin-helper-classes',pins=pins,
            started_at=datetime.now(timezone.utc).isoformat(), completed_profile_ids=[],
            diagnostic_compiler_requests=0, helper_jvm_requests=0, subject_compiler_commands=0,
            subject_main_executions=0, benchmark_samples=0, helper_formatting_and_stdio_qualified=False,
            actual_subject_runtime_dependency_closure_qualified=False, source_work_qualified=False,
            subject_JIT_method_evidence_qualified=False, bounded_workload_output_qualified=False,
            canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False)
        def bind(path,expected=None):
            path = Path(path).resolve(); actual = sha(path); expected = expected or actual
            require(actual == expected, ('Pinned bytes changed',str(path)))
            require(str(path) not in pins or pins[str(path)] == expected, 'Conflicting physical pin')
            pins[str(path)] = expected; return path
        save(output/'report.json',report)
        try:
            require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and
                    sys.flags.no_site and sys.flags.dont_write_bytecode, 'Use pinned Python with -I -S -B')
            bind(PYTHON,PYTHON_SHA)
            for path in (Path(__file__),ROOT/'migration/reorganization-paths.tsv',BASE/'editorial-substitutions.json'):
                bind(path)
            resume = load_module(ROOT/'tools/qualification/kotlin_resume.py',pins)
            compiled = json.loads(bind(PREPARATION,PREPARATION_SHA).read_bytes())
            require(compiled['status'] == 'Kotlin20-classes-and-bytecode-captured-awaiting-scored-owner-and-runtime-review' and
                    compiled['total_compiled_profiles'] == 20 and compiled['retained_compiler_commands'] == 3 and
                    compiled['retained_bytecode_reader_commands'] == 2 and compiled['new_compiler_commands'] == 17 and
                    compiled['new_bytecode_reader_commands'] == 18 and compiled['subject_main_executions'] == 0,
                    'Incomplete retained compile/owner cohort')
            rows = compiled['profiles']
            storage_doc = json.loads(bind(BASE/'additive-compile-owners-v1/artifact-storage.json').read_bytes())
            require(storage_doc['schema'] == 'kotlin-retained-generated-artifacts-v1' and
                    storage_doc['original_execution_paths_unchanged'] is True, 'Unknown artifact storage mapping')
            storage = {item['execution_path']:item for item in storage_doc['artifacts']}
            require(len(storage) == len(storage_doc['artifacts']), 'Duplicate class copy mapping')
            artifact_pins = {item['path']:item for row in rows for item in row['generated_artifacts']}
            relocations = {}
            for original,copy in storage.items():
                require(original in artifact_pins and copy['sha256'] == artifact_pins[original]['sha256'] and
                        copy['bytes'] == artifact_pins[original]['bytes'], 'Storage mapping differs from compiler evidence')
                target = (ROOT/copy['stored_path']).resolve()
                require(target.is_relative_to(BASE/'additive-compile-owners-v1/retained-artifacts'), 'Retained copy escapes artifact store')
                bind(target,copy['sha256'])
                if not Path(original).is_file(): relocations[original] = target
            class HelperEvidence(resume.Evidence):
                def path(self,logical):
                    return relocations.get(str(logical)) or super().path(logical)
            evidence = HelperEvidence(ROOT,json.loads((BASE/'editorial-substitutions.json').read_bytes()))
            saved,inventory,retained = resume.preflight(evidence)
            require([r['id'] for r in rows] == [r['id'] for r in inventory], 'Cohort differs from closed inventory')
            # Replay the successful closure as an integrity check, never as native execution.
            evidence.absorb(compiled['pins'])
            specification = json.loads(bind(BASE/'source-owner-review-v1/bounded-checks.json').read_bytes())
            require(specification['schema'] == 'kotlin-bounded-qualification-specification-v1' and
                    specification['limits'] == dict(process_timeout_seconds=30,group_cleanup_timeout_seconds=5,
                        maximum_live_subject_processes=1,automatic_retries=0), 'Bounded specification changed')
            review = json.loads(bind(BASE/'source-owner-review-v1/review.json').read_bytes())
            require([r['id'] for r in review['profiles']] == [r['id'] for r in rows], 'Review cohort differs')
            selected = {}
            for row,source,reviewed in zip(rows,inventory,review['profiles']):
                require(row['physical_inputs'] == source['authored_inputs'] and row['source_to_compile_command_binding'] is True,
                        'Compile/source binding differs')
                resume.successful(row['compile_command']); resume.successful(row['bytecode_reader'])
                require(len(reviewed['source_inputs']) == 2, 'Incomplete reviewed source bundle')
                for item,checked in zip(row['physical_inputs'],reviewed['source_inputs']):
                    require(item['path'] == checked['physical_path'] and item['sha256'] == checked['recorded_sha256'],
                            'Source review binding differs')
                    bind(item['path'],item['sha256']); bind(ROOT/checked['reviewed_source'],item['sha256'])
                require(row['physical_inputs'][1]['sha256'] == SUPPORT_SOURCE_SHA, 'Unexpected helper source')
                original,classes = class_directory(row,storage,bind); selected[row['id']] = classes
                require({a['path']:a['sha256'] for a in row['generated_artifacts'] if a['path'].endswith('.class')} ==
                        {a['physical_path']:a['recorded_sha256'] for a in reviewed['class_owners']}, 'Owner review differs')
                bind(ROOT/reviewed['disassembly_path'],reviewed['recorded_disassembly_sha256'])
                report.setdefault('class_sources',[]).append(dict(id=row['id'],original_execution_directory=str(original),
                    selected_runtime_directory=str(classes),relocated=original != classes))
            java = Path(saved['runtime_environment']['JAVACMD']); javac = java.with_name('javac')
            stdlib = Path(saved['compiler']).parent.parent/'lib/kotlin-stdlib.jar'
            for path in (java,javac,stdlib):
                require(str(path) in evidence.pins, ('Runtime/compiler not closed',str(path)))
                bind(path,evidence.pins[str(path)])
            require(pins[str(stdlib.resolve())] == STDLIB_SHA, 'Unexpected Kotlin standard library')
            probe = bind(BASE/'helper-semantics/HelperProbe.java')
            generator = ROOT/'experiments/elixir/helper-semantics/generate_vectors.py'
            vectors = bind(generator.with_name('format-vectors.tsv'))
            module = load_module(generator,pins)
            expected_vectors = ''.join('\t'.join(row)+'\n' for row in module.vectors()).encode()
            require(len(expected_vectors.splitlines()) == 1536 and vectors.read_bytes() == expected_vectors,
                    'Independent format expectations changed')
            payload = bytes(range(256))*1027+b'\x00\r\n\x1bFINAL-WITHOUT-NEWLINE'
            (output/'input.bin').write_bytes(payload)
            bind(output/'input.bin',hashlib.sha256(payload).hexdigest())
            compile_case = output/'diagnostic-compile'; compile_case.mkdir()
            env = environment(saved['runtime_environment'],compile_case)
            classes = output/'probe-classes'; classes.mkdir()
            source_copy = compile_case/'HelperProbe.java'; source_copy.write_bytes(probe.read_bytes()); bind(source_copy,pins[str(probe)])
            evidence.unchanged()
            for path,digest in pins.items(): require(sha(path) == digest, ('Input changed before launch',path))
            command = [str(javac)]+['-J'+flag for flag in FLAGS]+[
                '-J-Duser.home='+str(compile_case/'home'),'-J-Djava.io.tmpdir='+str(compile_case/'tmp'),
                '--release','17','-d',str(classes),str(source_copy)]
            report['diagnostic_compiler_requests'] = 1; save(output/'report.json',report)
            observe(command,env,compile_case,b'',b'',lock)
            for path in compile_case.iterdir():
                if path.is_file(): bind(path)
            generated = {str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()}
            require(generated == {'helperqualification/HelperProbe.class','helperqualification/HelperProbe$SupportLoader.class'},
                    'Unexpected diagnostic probe class set')
            for relative in generated:
                path = bind(classes/relative); raw = path.read_bytes()
                require(raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8],'big') == 61, 'Wrong diagnostic class target')
            for row in rows:
                case = output/row['id']; case.mkdir(); env = environment(row['runtime_environment'],case)
                options = FLAGS+[f'-Duser.home={case}/home',f'-Djava.io.tmpdir={case}/tmp',
                    f'-Xlog:class+load=info:file={case}/classes.log:uptime,tags',
                    f'-Xlog:gc*=info:file={case}/gc.log:uptime,tags']
                command = [str(java)]+options+['-cp',str(classes),'helperqualification.HelperProbe',
                    str(selected[row['id']]),str(stdlib),str(vectors),str(case/'summary.json'),
                    'clbg.'+row['benchmark']+'.MainKt']
                report['helper_jvm_requests'] += 1; save(output/'report.json',report)
                observe(command,env,case,payload,payload+payload,lock)
                summary = json.loads((case/'summary.json').read_bytes())
                validate_summary(summary,saved,row,selected[row['id']],stdlib,classes,case,options,payload)
                observed = validate_log((case/'classes.log').read_text(),selected[row['id']],stdlib,classes)
                require((case/'gc.log').is_file() and 'Using G1' in (case/'gc.log').read_text(), 'Missing G1 diagnostic evidence')
                save(case/'validated.json',dict(status='passed',profile_id=row['id'],loaded_classes=observed,
                    helper_semantics_qualified=True,subject_main_executions=0,benchmark_samples=0,chart_admission=False))
                for path in case.iterdir():
                    if path.is_file(): bind(path)
                report['completed_profile_ids'].append(row['id']); save(output/'report.json',report)
                print('Validated Kotlin helper:',row['id'],flush=True)
            require(len(report['completed_profile_ids']) == 20, 'Incomplete helper cohort')
            report.update(status='twenty-retained-helper-semantics-passed',helper_formatting_and_stdio_qualified=True)
        except BaseException as error:
            report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
            raise
        finally:
            native_records = []
            for path in output.glob('*/process.json'):
                try:
                    receipt = json.loads(path.read_bytes())
                    if receipt.get('pid'):
                        native_records.append(dict(path=str(path.relative_to(output)),pid=receipt['pid'],
                            status=receipt['status'],direct_child_reaped=receipt['direct_child_reaped']))
                except BaseException as error:
                    report.setdefault('process_receipt_errors',[]).append(dict(path=str(path),error=str(error)))
            report['registered_native_commands'] = native_records
            report['diagnostic_compiler_launches'] = sum(r['path'].startswith('diagnostic-compile/') for r in native_records)
            report['helper_jvm_launches'] = len(native_records)-report['diagnostic_compiler_launches']
            if report['status'] == 'twenty-retained-helper-semantics-passed' and not (
                    report['diagnostic_compiler_launches'] == 1 and report['helper_jvm_launches'] == 20 and
                    all(r['status'] == 'passed' and r['direct_child_reaped'] for r in native_records)):
                report.setdefault('process_receipt_errors',[]).append(dict(error='Successful native command inventory incomplete'))
            integrity_errors = []
            if evidence is not None:
                report['closed_evidence_resolution'] = evidence.records
                for record in evidence.records.values():
                    try: require(sha(record['resolved_path']) == record['active_sha256'], 'Closed input changed')
                    except BaseException as error:
                        integrity_errors.append(dict(path=record['resolved_path'],error=str(error)))
            for path,digest in pins.items():
                try: require(sha(path) == digest, 'Input changed')
                except BaseException as error: integrity_errors.append(dict(path=path,error=str(error)))
            report.update(integrity_errors=integrity_errors,finished_at=datetime.now(timezone.utc).isoformat())
            if integrity_errors or report.get('process_receipt_errors'):
                report.update(status='failed-input-integrity',helper_formatting_and_stdio_qualified=False)
            save(output/'report.json',report)
            artifacts = {}; artifact_errors = []
            for path in output.rglob('*'):
                if path.is_file():
                    try: artifacts[str(path.relative_to(output))] = dict(sha256=sha(path),bytes=path.stat().st_size)
                    except BaseException as error: artifact_errors.append(dict(path=str(path),error=str(error)))
            if artifact_errors:
                report.update(status='failed-artifact-integrity',helper_formatting_and_stdio_qualified=False,artifact_errors=artifact_errors)
                save(output/'report.json',report)
                artifacts['report.json'] = dict(sha256=sha(output/'report.json'),bytes=(output/'report.json').stat().st_size)
            save(output/'terminal.json',dict(status=report['status'],report_sha256=sha(output/'report.json'),
                available_evidence=artifacts,integrity_errors=integrity_errors,artifact_errors=artifact_errors,
                common_mutex_held=True,common_mutex_inode=LOCK_INODE,subject_main_executions=0,
                benchmark_samples=0,chart_admission=False))
            require(not integrity_errors and not artifact_errors and not report.get('process_receipt_errors'),
                    'Qualification input/artifact/native-receipt integrity failed')


if __name__ == '__main__':
    main()
