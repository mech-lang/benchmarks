"""Reuse the saved Kotlin intake; run only its missing generic JVM probe."""
import argparse
import base64
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import signal
import sys
import traceback
import types

P = Path(__file__).resolve().parent
H = P.parents[1]
C = H.parents[1]
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OLD = HOST/'benchmarks/clbg/kotlin-comparison/20261013'
ORIGINAL = OLD/'revisions/retained-jdk-intake-v1'
ORIGINAL_SHA = '834b139966b990660c3255cb7881db3e17ef6e306dcf73dd692e71bb3ed53c46'
OLD_OUT = OLD/'jobs/official-compiler-retained-jdk-v1'
OLD_BUILD = OLD/'.build/official-compiler-retained-jdk-v1'
OWNER = C/'continuation/owned-jobs/kotlin-official-compiler-retained-jdk-v1'
ROOT = C/'continuation/jobs/kotlin-first-intake-closed-review-v1/receipt.json'
ROOT_SHA = '3326693e1bbfc09bfa8af8cfbd8a176e93f44e3ed13f56cca2f4b4c1fb381eb1'
TERMINAL_SHA = 'b6ecc9d44d65d93f2f3a628e99cb05d3bf976744ba0625e4896e16a54ceac326'
REQUEST_SHA = 'e1c7607ec42dcef46adf7de57584f8e890ebbf27b70c5bbe83a14991c897a0aa'
OUTCOME_SHA = '2756d53c5344bb8818539200fa234c8bbf2fdf531150ca6b19dd47d13487d8d4'
PACKET = C/'continuation/jobs/kotlin-retained-jdk-release-v1/frozen-inputs.json'
PACKET_SHA = '8e7a6eeefdc2999effc9afcbd4241426ae750eb021263dcaca14ea1a181e41d9'
RUNTIME_REVIEW_SHA = 'e53c574cc22c13a880dd9d76725a90204cbbd9d2e799b81c9eec18797856b3ac'
VERSION_SHA = '2c5334cb57c41d3044d3e0f50c42dcc8599d4087c37f0eba3be34afee470653c'
COMPILE_SHA = '4b8a36012016be5476ca8f918dcf1603ce1d6bf2a8abdfcf9465d2db9fa923a0'
CLASS_SHA = 'bfd1d0628409b4326c7d17be359ddd0b9ec384a9f457f8f828250054a863451c'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK = Path('/tmp/mech-clbg-timing.lock')
EMPTY_OPTIONS = ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS')


def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_original(pins):
    raw = (ORIGINAL/'intake.py').read_bytes()
    assert not (ORIGINAL/'intake.py').stat().st_mode & 0o222
    assert hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA
    name = 'kotlin_saved_intake_original_helpers'; assert name not in sys.modules
    original = types.ModuleType(name); original.__file__ = str(ORIGINAL/'intake.py')
    sys.modules[name] = original
    exec(compile(raw, original.__file__, 'exec'), original.__dict__)
    original.bind(ORIGINAL/'intake.py', ORIGINAL_SHA, pins)
    return original


def saved_intake(original, pins):
    root = original.read(ROOT, ROOT_SHA, pins)
    assert root['status'] == 'closed-Kotlin-intake-empty-option-diagnostic-failure-with-two-native-successes'
    assert (root['worker_pid'], root['command_pid'], root['verified_pins']) == (16569, 16575, 5422)
    assert root['runtime_probe_executed'] is root['chart_admission'] is False
    assert root['subject_compiler_commands'] == root['native_benchmarks'] == 0
    assert root['original_host_paths_preserved'] is root['common_mutex_held'] is True and root['common_mutex_inode'] == 79859134
    for stem, path, sha in (('durable_terminal', OWNER/'terminal.json', TERMINAL_SHA),
                           ('request', OWNER/'request.json', REQUEST_SHA), ('outcome', OLD_OUT/'outcome.json', OUTCOME_SHA)):
        assert root[stem+'_path'] == str(path) and root[stem+'_sha256'] == sha
    expected = [str(PYTHON), '-I', '-S', '-B', '-u', str(ORIGINAL/'intake.py'), '--revision',
        'official-compiler-retained-jdk-v1', '--packet', str(PACKET), '--packet-sha256', PACKET_SHA,
        '--runtime-review-sha256', RUNTIME_REVIEW_SHA]
    ended = original.read(OWNER/'terminal.json', TERMINAL_SHA, pins)
    request = original.read(OWNER/'request.json', REQUEST_SHA, pins)
    started, worker, launch = [original.read(OWNER/name, digest(OWNER/name), pins)
        for name in ('command-started.json', 'worker-started.json', 'launch.json')]
    assert all(record['command'] == expected and record['cwd'] == str(HOST) for record in (request, started, worker, launch))
    assert ended['status'] == 'command-failed' and type(ended['exit_code']) is int and ended['exit_code'] == 1
    assert ended['actual_command_started'] is True and ended['stop_signals'] == []
    assert ended['qualification_granted'] is ended['automatic_retry'] is request['qualification_granted'] is request['automatic_retry'] is False
    assert request['common_mutex_owned_by_target_command'] is worker['common_mutex_owned_by_target_command'] is True
    assert worker['inherited_private_lease'] is worker['detached_session'] is True
    assert worker['worker_identity'] == ended['worker_identity'] and ended['worker_identity']['pid'] == launch['worker_identity']['pid'] == 16569
    assert started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
    assert started['command_identity'] == ended['command_identity'] and started['command_pid'] == ended['command_pid'] == 16575
    listing = ended['command_identity']['listing'].split(None, 7)
    assert listing[:2] == ['16575', '16569'] and listing[7].split() == expected
    assert not any(ended.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
    outcome = original.read(OLD_OUT/'outcome.json', OUTCOME_SHA, pins)
    assert outcome['status'] == 'failed-Kotlin-toolchain-intake' and outcome['error'] == outcome['error_type'] == 'AssertionError'
    assert outcome['exclusive_common_mutex_held'] is True and outcome['common_mutex_inode'] == 79859134
    assert outcome['original_JDK_and_sources_preserved'] is True
    assert not any(outcome.get(key) for key in ('integrity_errors', 'available_bytes_not_fully_pinned'))
    assert not (OLD_OUT/'probe').exists() and not (OLD_OUT/'intake-result.json').exists()
    for mapping in (outcome['prerequisite_pins'], outcome['available_evidence_pins']):
        for path, sha in mapping.items(): original.bind(path, sha, pins)
    packet = original.read(PACKET, PACKET_SHA, pins)
    assert packet['schema'] == 'frozen-kotlin-retained-jdk-intake-v1'
    assert set(packet['pins']) == {str(path) for path in original.INPUTS} | {str(ORIGINAL/name) for name in original.FILES} | {str(PYTHON.resolve())}
    for path, sha in packet['pins'].items(): original.bind(path, sha, pins)
    runtime = original.retained_jdk(argparse.Namespace(runtime_review_sha256=RUNTIME_REVIEW_SHA), pins)
    compiler = OLD_BUILD/'compiler/kotlinc'
    publisher = original.read(OLD_OUT/'publisher-intake.json', outcome['available_evidence_pins'][str(OLD_OUT/'publisher-intake.json')], pins)
    assert publisher['extracted_root'] == str(compiler) and publisher['payload_sha256'] == original.PAYLOAD_SHA
    assert publisher['checksum_sha256'] == original.CHECKSUM_SHA
    for path, sha in publisher['complete_compiler_jars'].items(): original.bind(path, sha, pins)
    assert publisher['wrapper'] == str(compiler/'bin/kotlinc') and publisher['wrapper_sha256'] == pins[str(compiler/'bin/kotlinc')]
    inventory_path = OLD_OUT/'source-input-inventory.json'
    inventory = original.read(inventory_path, outcome['available_evidence_pins'][str(inventory_path)], pins)
    assert inventory['status'] == 'exact20-full-inputs-materialized-not-compiled'
    assert (inventory['distinct_main_inputs'], inventory['counted_helper_inputs'], inventory['authored_launcher_inputs']) == (20,20,0)
    rows = inventory['forms']; assert len(rows) == len({row['id'] for row in rows}) == 20
    assert {(row['benchmark'], row['variant']) for row in rows} == {(b, v) for b in original.BENCHES for v in ('compact', 'optimized')}
    for row in rows:
        folder = OLD_BUILD/'forms'/row['id']
        assert row['id'] == 'kotlin-'+row['benchmark']+'-'+row['variant'] and row['alias_of'] == 'kotlin-'+row['benchmark']+'-baseline-v1'
        files = row['authored_inputs']; assert len(files) == 2 and [item['role'] for item in files] == ['application', 'application-helper']
        for item, name in zip(files, ('Main.kt', 'Support.kt')):
            assert item['path'] == str(folder/name) and item['counted'] is True
            original.bind(item['path'], item['sha256'], pins); original.bind(item['origin'], item['sha256'], pins)
        assert row['authored_launcher_count'] == 0 and row['subject_compiler_executed'] is row['chart_admission'] is False
        assert row['canonical_loc'] is row['formatted_loc'] is None and not any((folder/'classes').iterdir())
    classes = OLD_BUILD/'probe-classes'
    class_path = original.bind(classes/'RuntimeProbe.class', CLASS_SHA, pins)
    assert root['retained_probe_class'] == dict(path=str(class_path), sha256=CLASS_SHA, bytes=3175)
    assert {path.name for path in classes.iterdir()} == {'RuntimeProbe.class'}
    assert class_path.stat().st_size == 3175 and class_path.read_bytes()[:4] == b'\xca\xfe\xba\xbe'
    old_flags = original.FLAGS + ['-Duser.home='+str(OLD_BUILD/'home'), '-Djava.io.tmpdir='+str(OLD_BUILD/'tmp')]
    receipts = [(OLD_OUT/'version/compiler-version.json', VERSION_SHA, 16617, [str(compiler/'bin/kotlinc'), '-version']),
        (OLD_OUT/'probe-build/metadata-probe-compile.json', COMPILE_SHA, 16633,
         [str(original.JDK/'bin/javac'), *['-J'+flag for flag in old_flags], '-encoding', 'UTF-8', '-d', str(classes), str(ORIGINAL/'RuntimeProbe.java')])]
    assert root['successful_native_commands'] == [dict(path=str(path), sha256=sha, pid=pid, command=argv) for path,sha,pid,argv in receipts]
    for path, sha, pid, argv in receipts:
        receipt = original.read(path, sha, pins); original.owned(receipt)
        assert receipt['command'] == argv and receipt['pid'] == pid
        assert receipt['preparation_only'] is receipt['never_chart_eligible'] is True
    compile_stderr = OLD_OUT/'probe-build/metadata-probe-compile.stderr'
    assert original.bind(compile_stderr, outcome['available_evidence_pins'][str(compile_stderr)], pins).read_bytes() == b'Picked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \n'
    compile_stdout = OLD_OUT/'probe-build/metadata-probe-compile.stdout'
    assert original.bind(compile_stdout, outcome['available_evidence_pins'][str(compile_stdout)], pins).read_bytes() == b''
    version_text = b''.join(original.bind(OLD_OUT/'version'/('compiler-version.'+suffix),
        outcome['available_evidence_pins'][str(OLD_OUT/'version'/('compiler-version.'+suffix))], pins).read_bytes() for suffix in ('stdout', 'stderr')).decode('utf-8')
    assert version_text == 'NOTE: Picked up JDK_JAVA_OPTIONS: \nPicked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \ninfo: kotlinc-jvm 2.4.21 (JRE 25.0.4.1+1-LTS)\n'
    assert len(root['new_repository_copies']) == 12
    for path, sha in root['new_repository_copies'].items():
        copy = Path(path); assert copy.is_relative_to(H/'jobs/official-compiler-retained-jdk-v1')
        prior = OLD_OUT/copy.relative_to(H/'jobs/official-compiler-retained-jdk-v1')
        assert sha == (OUTCOME_SHA if prior.name == 'outcome.json' else outcome['available_evidence_pins'][str(prior)])
        original.bind(copy, sha, pins)
    return runtime, compiler, classes, inventory, version_text


def run(args, output, build, pins, fd, original):
    runtime, compiler, classes, inventory, version_text = saved_intake(original, pins)
    for name, sha in (('resume.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
        assert not (P/name).stat().st_mode & 0o222; original.bind(P/name, sha, pins)
    for name in ('home', 'config', 'tmp'): (build/name).mkdir()
    flags = original.FLAGS + ['-Duser.home='+str(build/'home'), '-Djava.io.tmpdir='+str(build/'tmp')]
    environment = dict(PATH=str(original.JDK/'bin')+':/usr/bin:/bin:/usr/sbin:/sbin', JAVA_HOME=str(original.JDK), JAVACMD=str(original.JDK/'bin/java'),
        JAVA_OPTS=' '.join(flags), CLASSPATH='', KOTLIN_RUNNER='', KOTLIN_COMPILER='', KOTLIN_TOOL='', LC_ALL='C', LANG='C',
        HOME=str(build/'home'), XDG_CONFIG_HOME=str(build/'config'), TMPDIR=str(build/'tmp')+os.sep,
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
    assert not any(key in environment for key in EMPTY_OPTIONS)
    original.bind(original.SERVICE, original.SERVICE_SHA, pins)
    service = original.cold(original.SERVICE, 'kotlin_saved_probe_original_owned_service', pins)
    original.bind(service.GUARD, pins[str(service.GUARD)], pins)
    guard = original.cold(service.GUARD, 'kotlin_saved_probe_original_guard', pins)
    original_get_code = importlib.machinery.SourceFileLoader.get_code
    def checked_code(loader, fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(HOST/'benchmarks/clbg'):
            assert path.suffix == '.py' and str(path) in pins
            raw = original.bind(path, pins[str(path)], pins).read_bytes()
            return compile(raw, str(path), 'exec')
        return original_get_code(loader, fullname)
    importlib.machinery.SourceFileLoader.get_code = checked_code
    try:
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = original_get_code
    for module in (harness, harness.compact, harness.compact.common):
        path = Path(module.__file__).resolve(); original.bind(path, pins[str(path)], pins)
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_relative_to(HOST/'benchmarks/clbg'):
            path = Path(filename).absolute(); assert str(path) in pins
            original.bind(path, pins[str(path)], pins)
    assert not list(service.HERE.glob('*.class')) and not (service.HERE/'.java').exists()
    argv = [str(original.JDK/'bin/java'), *flags, '-cp', str(classes), 'RuntimeProbe']
    original.save(output/'contract.json', dict(status='reuse-two-successful-tools-run-missing-generic-JVM-probe-once',
        original_failure=dict(path=str(OLD_OUT/'outcome.json'), sha256=OUTCOME_SHA), original_class=dict(path=str(classes/'RuntimeProbe.class'), sha256=CLASS_SHA),
        compiler_version_reexecutions=0, javac_reexecutions=0, subject_compiler_commands=0,
        removed_empty_environment_keys=list(EMPTY_OPTIONS), changed_private_paths=['HOME','XDG_CONFIG_HOME','TMPDIR','-Duser.home','-Djava.io.tmpdir'],
        runtime_environment=environment, exact_command=argv, original_host_paths_preserved=True, chart_admission=False))
    original.verify(pins)
    result = service.owned_command(guard, harness, argv, environment, output/'probe', fd, 120, 'runtime-configuration')
    original.owned(result['detail']); assert result['stderr'] == b''
    values, actual_flags, collectors = {}, [], []
    for line in result['stdout'].decode('ascii').splitlines():
        key, encoded = line.split('=', 1); value = base64.b64decode(encoded, validate=True).decode('utf-8')
        if key == 'JVM_ARG': actual_flags.append(value)
        elif key == 'COLLECTOR': collectors.append(value)
        else: assert key not in values; values[key] = value
    required = dict(JAVA_HOME=str(original.JDK), RUNTIME_VERSION='25.0.4.1+1-LTS', VENDOR='Eclipse Adoptium', OS_ARCH='aarch64',
        CLASS_PATH=str(classes), PROCESSORS='8', USER_HOME=str(build/'home'), JAVA_TMPDIR=str(build/'tmp'))
    assert all(values[key] == value for key,value in required.items()) and actual_flags == flags
    assert set(values) == set(required) | {'VM_NAME','VM_INFO','COMPILER','MAX_HEAP','FILE_ENCODING'}
    assert '64-Bit' in values['VM_NAME'] and 'mixed mode' in values['VM_INFO'] and 'Tiered' in values['COMPILER']
    assert 0 < int(values['MAX_HEAP']) <= 8*1024**3 and collectors == ['G1 Young Generation','G1 Concurrent GC','G1 Old Generation']
    for row in inventory['forms']: assert not any((OLD_BUILD/'forms'/row['id']/'classes').iterdir())
    original.verify(pins)
    original.save(output/'intake-result.json', dict(status='saved-Kotlin-compiler-and-generic-JVM-probe-passed-awaiting-subject-review',
        compiler=str(compiler/'bin/kotlinc'), compiler_version_stdout_stderr=version_text, retained_JDK_lineage=runtime,
        retained_probe_class=dict(path=str(classes/'RuntimeProbe.class'), sha256=CLASS_SHA), actual_generic_runtime_probe=values,
        actual_jvm_flags=actual_flags, actual_collectors=collectors, runtime_environment=environment,
        retained_source_inventory=dict(path=str(OLD_OUT/'source-input-inventory.json'), sha256=pins[str(OLD_OUT/'source-input-inventory.json')]),
        authored_forms=20, counted_main_inputs=20, counted_support_inputs=20, authored_workload_launcher_inputs=0,
        reused_successful_tool_commands=2, new_owned_tool_commands=1, compiler_version_reexecutions=0, javac_reexecutions=0,
        original_ownership_fixtures_reused=11, fixture_reexecutions=0, publisher_downloads=0, extractions=0,
        subject_compiler_commands=0, native_benchmarks=0, raw_stdio_qualified=False, compiler_native_dependency_execution_qualified=False,
        subject_JIT_method_evidence_qualified=False, source_work_qualified=False, canonical_loc=None, formatted_loc=None,
        runtime_configuration_admitted=False, chart_admission=False, pins=dict(pins)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('revision', 'worker-sha256', 'review-sha256'): parser.add_argument('--'+name, required=True)
    args = parser.parse_args(); assert args.revision == 'saved-runtime-probe-v1'
    assert sys.dont_write_bytecode and Path(sys.executable).resolve() == PYTHON.resolve()
    assert all(re.fullmatch('[a-f0-9]{64}', value) for key,value in vars(args).items() if key.endswith('_sha256'))
    def interrupted(signum, frame): raise KeyboardInterrupt('Kotlin saved probe interrupted: '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM): signal.signal(sig, interrupted)
    with ExitStack() as leases:
        for path in (OWNER/'owner.lock', HOST/'benchmarks/clbg/continuation/owned-jobs/clojure-publication-metadata-v1/owner.lock'):
            held = leases.enter_context(path.open('rb')); fcntl.flock(held, fcntl.LOCK_SH|fcntl.LOCK_NB)
            opened, named = os.fstat(held.fileno()), path.stat(); assert (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
        owner_path = P/'owner.lock'
        held = leases.enter_context(owner_path.open('a+')); fcntl.flock(held, fcntl.LOCK_EX|fcntl.LOCK_NB)
        opened, named = os.fstat(held.fileno()), owner_path.stat()
        assert (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
        print('WAIT common mutex: one missing Kotlin generic JVM probe', flush=True)
        with LOCK.open('r+') as common:
            fcntl.flock(common, fcntl.LOCK_EX); opened, named = os.fstat(common.fileno()), LOCK.stat()
            assert (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino) and opened.st_ino == 79859134
            output, build = P/'jobs'/args.revision, H/'.build'/args.revision
            assert not output.exists() and not build.exists()
            assert not any(path.is_symlink() for path in (P, H, output.parent, build.parent))
            output.mkdir(parents=True); build.mkdir(parents=True)
            pins, failures = {}, []
            outcome = dict(status='failed-Kotlin-saved-runtime-probe', subject_compiler_commands=0, native_benchmarks=0,
                compiler_version_reexecutions=0, javac_reexecutions=0, fixture_reexecutions=0, chart_admission=False)
            signal.alarm(420)
            try:
                for path, sha in ((P/'resume.py', args.worker_sha256), (P/'REVIEW.md', args.review_sha256), (PYTHON.resolve(), PYTHON_SHA)):
                    if path.suffix in ('.py', '.md'): assert not path.stat().st_mode & 0o222
                    assert digest(path) == sha; pins[str(path)] = sha
                original = load_original(pins); run(args, output, build, pins, common.fileno(), original)
                outcome['status'] = 'saved-Kotlin-compiler-and-generic-JVM-probe-passed-awaiting-subject-review'
            except BaseException as error:
                outcome.update(error=str(error) or type(error).__name__, error_type=type(error).__name__)
                with (output/'error.log').open('x') as stream: stream.write(traceback.format_exc())
                raise
            finally:
                signal.alarm(0); available = {}
                try:
                    opened, named = os.fstat(common.fileno()), LOCK.stat()
                    assert (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino) and opened.st_ino == 79859134
                except BaseException as error:
                    failures.append(dict(path=str(LOCK), error=str(error) or type(error).__name__))
                for path, sha in pins.items():
                    try: assert digest(path) == sha
                    except BaseException as error: failures.append(dict(path=path, error=str(error) or type(error).__name__))
                for path in output.rglob('*'):
                    if path.is_file():
                        try: available[str(path)] = digest(path)
                        except BaseException as error: failures.append(dict(path=str(path), error=str(error) or type(error).__name__))
                if failures: outcome.update(status='failed-terminal-integrity', integrity_errors=failures)
                outcome.update(finished_at=datetime.now(timezone.utc).isoformat(), prerequisite_pins=pins, available_evidence_pins=available,
                    common_mutex_held=True, common_mutex_inode=79859134, original_host_paths_preserved=True,
                    private_startup_directories_not_evidence_artifacts=True)
                with (output/'outcome.json').open('x') as stream: json.dump(outcome, stream, indent=2); stream.write('\n')
                if failures: raise RuntimeError('Kotlin saved probe terminal integrity failed; partial evidence retained')


if __name__ == '__main__': main()
