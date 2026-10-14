"""Link the retained safe-trim archive, then observe the image without running it."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys
import traceback

P = Path(__file__).resolve().parent
HERE = P.parents[1]
CLBG = HERE.parents[1]
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
OLD_CLBG = HOST/'benchmarks/clbg'
OLD = OLD_CLBG/'julia-aot-comparison/20261012'
LOCK = Path('/tmp/mech-clbg-timing.lock')
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
ROOT = CLBG/'continuation/jobs/julia-saved-archive-closed-review-v1/receipt.json'
ROOT_SHA = '0f9e8e0d4a517aec5ec974998c46a76d2b6efd5c642e79346a1a6c4734e4cbe5'
SAVED = OLD/'jobs/official-static-io-safe-archives-v1'
RESULT_SHA = 'b35a53b019538e6affd5c8c0682ec5d747da2942c38ba709482417053a0df26a'
OUTCOME_SHA = '3ae135180a968c60b677744c834bfb494626467e61bd2c5dd437e04be752d55f'
OWNER = CLBG/'continuation/owned-jobs/julia-saved-safe-archive-members-v1'
REQUEST_SHA = 'f7f805b27d348bda36ce5765ddef3d03d08fee660ef0a69a67fc05986dd345ff'
TERMINAL_SHA = '787ab7e60142bfbad285dc7dcaefdd7ffe5b0187cbff1c7061be4700f267bb70'
BASE = OLD/'revisions/static-io-safe-trim-v1/build.py'
BASE_SHA = 'ff9e3b0c8a0b803d53f9e4a893815db3daed7c6f922cd5e4bce8e3544ccb3bcd'
INSPECT = OLD/'revisions/archive-link-route-v1'
INSPECT_SHA = '4ef47097b79626a0385243c5e85f6b1ff6d889f4632b97e800a667d111acf14e'
INSPECT_NOTE_SHA = '9416ae546ee666426c292c1665fc32cbba183f05390a74f8dddfa68bb71f5f02'
DRIVER_SHA = 'b3545da9b6fd44119e1316af7c8e0783aa6c4463d12e7e6c301b65edf6e31b1c'
CLANG = Path('/opt/homebrew/Cellar/llvm@22/22.1.8/bin/clang-22')
CLANG_SHA = '012b35304481c5d5db6b57f20e144fb78f198ca9db14aa0b8db72cd2e493e12d'
NM = CLANG.with_name('llvm-nm')
NM_SHA = '333b44b478ec90b2c4aca439c7c4812b9bfca03331b447eeb4da85a8faca18ea'
AR_SHA = 'caa6baa2ba5365df10bd0facab06d40abacd974134645df8f0f628b572b1e66a'
READOBJ_SHA = '95c1d516c91ffbf9840da9fc36bc986541e18043804248c2052068566282d7a4'
REVISION = 'official-static-io-safe-link-v3'
SDK = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX14.4.sdk')
SDK_SHA = '45e88fdfde9be16796dbb0f95891d44d47549236ae51d299d535834f5abdfb35'
SDK_FAILURE = CLBG/'continuation/jobs/julia-saved-safe-archive-link-v2-closed-review/receipt.json'
SDK_FAILURE_SHA = 'ca573bb7c1f02e21117b9885ca6d3aa3e1cef5b6014efea068d77265280bf6c2'
FAILED = CLBG/'continuation/jobs/julia-saved-safe-archive-link-v1-closed-review/receipt.json'
FAILED_SHA = '8ae2486acb41edf5aff7024797e0beaa38232c7dd7f65d9514a6bd76089b4b8c'
HELPER_HISTORY = OLD_CLBG/'c3-comparison/20261012/qualification/private-v3/report.json'
HELPER_HISTORY_SHA = '7cb4a25819935f3e15b3c270595efc9df3dbc056982625892abc3b16bef2f20c'
MISSING_HELPERS = {
    str(OLD_CLBG/'r-apl-uiua-comparison/20261011/prepare.py'): '27fcf050ed21db40e747f2e8801ca6f227d82f1ea98f8592bba7b10a768109e5',
    str(OLD_CLBG/'array-comparison/all-20261009/run.py'): '8b7f1b408fb5838dc6adc2404bcfa6146e48e770e602fbe78255454f3cacb8c7',
    str(OLD_CLBG/'compact/run.py'): '6926e288a7b9b59b030c9226227df967aa1d92b3e395789467706e2241d987ae',
    str(OLD_CLBG/'nbody/run.py'): 'e907f71b3fdf8fc6f65adc76aab6dfc424811875388c14f0eb2f31e14e9cffcf',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path, digest, pins):
    path = Path(path).resolve(strict=True)
    assert re.fullmatch('[a-f0-9]{64}', digest) and sha(path) == digest, ('Changed retained input', path)
    assert str(path) not in pins or pins[str(path)] == digest, ('Conflicting pin', path)
    pins[str(path)] = digest
    return path


def read(path, digest, pins):
    return json.loads(bind(path, digest, pins).read_bytes())


def cold(path, digest, name, pins):
    path = bind(path, digest, pins)
    assert name not in sys.modules
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def prerequisites(pins):
    root = read(ROOT, ROOT_SHA, pins)
    assert root['status'] == 'closed-qualified-Julia-saved-archive-members-and-entry-observation'
    assert root['verified_pins'] == 9890 and (root['worker_pid'], root['command_pid']) == (15897, 15901)
    assert root['result_path'] == str(SAVED/'archive-result.json') and root['result_sha256'] == RESULT_SHA
    assert root['outcome_path'] == str(SAVED/'outcome.json') and root['outcome_sha256'] == OUTCOME_SHA
    assert root['request_path'] == str(OWNER/'request.json') and root['request_sha256'] == REQUEST_SHA
    assert root['durable_terminal_path'] == str(OWNER/'terminal.json') and root['durable_terminal_sha256'] == TERMINAL_SHA
    assert root['common_mutex_held'] is root['original_host_paths_preserved'] is True and root['common_mutex_inode'] == 79859134
    assert root['object_members'] == root['optimized_bitcode_members'] == 10 and root['actual_defined_native_entry_count'] == 1
    assert all(root[key] is False for key in ('bitcode_decoded', 'actual_ir_removal_qualified',
        'native_owner_qualified', 'fallback_closure_qualified', 'runtime_aot_proven', 'chart_admission'))
    assert all(type(root[key]) is int and root[key] == 0 for key in
        ('actual_julia_processes', 'successful_compile_reexecutions', 'linker_executions', 'benchmark_runs'))
    argv = [PYTHON, '-I', '-S', '-B', '-u', str(INSPECT/'inspect.py'), '--revision', 'official-static-io-safe-archives-v1',
        '--worker-sha256', INSPECT_SHA, '--driver-sha256', DRIVER_SHA, '--review-sha256', INSPECT_NOTE_SHA,
        '--ar-sha256', AR_SHA, '--nm-sha256', NM_SHA, '--readobj-sha256', READOBJ_SHA]
    done = read(OWNER/'terminal.json', TERMINAL_SHA, pins)
    request = read(OWNER/'request.json', REQUEST_SHA, pins)
    start, worker = [read(OWNER/name, sha(OWNER/name), pins) for name in ('command-started.json', 'worker-started.json')]
    assert all(item['command'] == argv and item['cwd'] == str(HOST) for item in (request, start, worker))
    assert done['status'] == 'command-exited-zero-awaiting-report-review' and type(done['exit_code']) is int and done['exit_code'] == 0
    assert done['actual_command_started'] is True and done['stop_signals'] == []
    assert done['qualification_granted'] is done['automatic_retry'] is request['qualification_granted'] is request['automatic_retry'] is False
    assert request['common_mutex_owned_by_target_command'] is worker['common_mutex_owned_by_target_command'] is True
    assert worker['inherited_private_lease'] is worker['detached_session'] is True
    assert start['command_identity_observation_missing'] is done['command_identity_observation_missing'] is False
    assert start['command_identity'] == done['command_identity'] and start['command_pid'] == done['command_pid'] == 15901
    assert worker['worker_identity'] == done['worker_identity'] and done['worker_identity']['pid'] == 15897
    listing = done['command_identity']['listing'].split(None, 7)
    assert listing[:2] == ['15901', '15897'] and listing[7].split() == argv
    assert not any(done.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
    result = read(SAVED/'archive-result.json', RESULT_SHA, pins)
    outcome = read(SAVED/'outcome.json', OUTCOME_SHA, pins)
    assert result['status'] == outcome['status'] == 'actual-archive-members-and-native-entry-observed-awaiting-root-owner-and-link-review'
    assert outcome['exclusive_common_mutex_held'] is True and outcome['common_mutex_inode'] == 79859134
    assert not any(outcome.get(key) for key in ('error', 'error_type', 'integrity_errors', 'available_bytes_not_fully_pinned'))
    for mapping in (result['pins'], outcome['prerequisite_pins'], outcome['available_evidence_pins'], root['new_repository_copies']):
        for path, digest in mapping.items(): bind(path, digest, pins)
    assert result['actual_native_inspection_commands'] == len(root['native_commands']) == 6
    assert result['object_and_bitcode_members_captured'] is True and len(result['members']) == 20
    assert len(result['object_members']) == len(result['optimized_bitcode_members']) == 10
    assert result['actual_defined_native_entry_count'] == 1
    for item in root['native_commands']:
        receipt = read(item['path'], item['sha256'], pins)
        assert receipt['command'] == item['command'] and receipt['pid'] == receipt['identity']['pid'] == item['pid']
        assert type(receipt['exit_status']) is type(receipt['final_exit_status']) is int
        assert receipt['exit_status'] == receipt['final_exit_status'] == 0 and receipt['inherited_common_mutex'] is True
        assert not any(receipt.get(key) for key in ('error', 'error_type', 'cleanup_error', 'cleanup_errors'))
    assert all(result[key] is False for key in ('bitcode_decoded', 'native_owner_qualified',
        'actual_ir_removal_qualified', 'fallback_closure_qualified', 'runtime_aot_proven', 'chart_admission'))
    assert all(type(result[key]) is int and result[key] == 0 for key in ('actual_julia_processes',
        'successful_compile_reexecutions', 'linker_executions', 'actual_workload_executions', 'fixture_reexecutions', 'benchmark_runs', 'LLDB_attempts'))
    return cold(BASE, BASE_SHA, 'julia_saved_link_original_pure_helpers', pins), result


def load_service(base, pins):
    failed = read(FAILED, FAILED_SHA, pins)
    assert failed['status'] == 'closed-preserved-Julia-link1-raw-helper-pin-rejection-before-native'
    assert (failed['worker_pid'], failed['command_pid'], failed['durable_exit_code'], failed['actual_native_commands']) == (39106, 39112, 1, 0)
    assert failed['attempted_command_names'] == failed['completed_command_names'] == []
    assert failed['original_archive_and_compile_preserved'] is True and failed['common_mutex_inode'] == 79859134
    # This original qualified C3 report is already bound by the archive pins.
    # Add only its exact four transitive harness inputs before raw loading.
    history = read(HELPER_HISTORY, HELPER_HISTORY_SHA, pins)
    assert {path: history['pins'][path] for path in MISSING_HELPERS} == MISSING_HELPERS
    for path, digest in MISSING_HELPERS.items(): bind(path, digest, pins)
    service = cold(base.PREPARATION, base.PREPARATION_SHA, 'julia_saved_link_existing_owned_service', pins)
    # Legacy factories use SourceFileLoader. Execute exact retained source,
    # never a .pyc, for their old-host guard/harness dependency closure.
    original = importlib.machinery.SourceFileLoader.get_code
    def raw_code(loader, name):
        path = Path(loader.path).resolve(strict=True)
        if path.is_relative_to(OLD_CLBG):
            assert str(path) in pins and path.suffix == '.py', ('Unpinned local helper', path)
            source = path.read_bytes()
            assert hashlib.sha256(source).hexdigest() == pins[str(path)]
            return compile(source, str(path), 'exec')
        return original(loader, name)
    importlib.machinery.SourceFileLoader.get_code = raw_code
    try:
        guard = service.load_guard()
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = original
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).resolve().is_relative_to(OLD_CLBG):
            path = Path(filename).resolve(strict=True)
            assert str(path) in pins and path.suffix == '.py'
            bind(path, pins[str(path)], pins)
    return service, guard, harness


def run(args, output, build, pins, common_fd, progress):
    base, result = prerequisites(pins)
    sdk_failure = read(SDK_FAILURE, SDK_FAILURE_SHA, pins)
    assert sdk_failure['status'] == 'closed-preserved-Julia-link2-failed-SDK-selection'
    assert (sdk_failure['actual_native_commands'], sdk_failure['owned_native_exit'], sdk_failure['image_commands']) == (1, 1, 0)
    assert sdk_failure['actual_sdk'] == dict(path=str(SDK), settings_sha256=SDK_SHA, version='14.4', canonical_name='macosx14.4')
    assert pins[str(SDK/'SDKSettings.json')] == SDK_SHA
    sdk_settings = read(SDK/'SDKSettings.json', SDK_SHA, pins)
    assert sdk_settings['Version'] == '14.4' and sdk_settings['CanonicalName'] == 'macosx14.4'
    for name, digest in (('link.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
        assert not (P/name).stat().st_mode & 0o222
        bind(P/name, digest, pins)
    bind(CLANG, CLANG_SHA, pins); bind(NM, NM_SHA, pins)
    for path, digest in ((Path('/usr/bin/lipo'), args.lipo_sha256), (Path('/usr/bin/otool'), args.otool_sha256)):
        resolved = bind(path, digest, pins)
        assert os.access(resolved, os.X_OK)
    service, guard, harness = load_service(base, pins)
    runtime = base.RUNTIME
    archive = OLD/'.build/official-static-io-safe-trim-nbody-v1/nbody-safe-o.a'
    driver = INSPECT/'direct_driver.c'
    old_binary = OLD/'.build/official-static-io-safe-link-v1/nbody-safe'
    binary = build/'nbody-safe'
    bind(driver, DRIVER_SHA, pins)
    expected = [str(CLANG), '-std=gnu11', '-fPIC', '-O3', '-g', '-I'+str(runtime/'include/julia'), str(driver),
        '-o', str(old_binary), '-Xlinker', '-force_load', str(archive), '-lm', '-L'+str(runtime/'lib'),
        '-L'+str(runtime/'lib/julia'), '-Wl,-rpath,'+str(runtime/'lib/julia'), '-Wl,-rpath,'+str(runtime/'lib'), '-ljulia', '-ljulia-internal']
    image_commands = [['/usr/bin/lipo', '-archs', str(old_binary)], ['/usr/bin/otool', '-L', str(old_binary)],
        ['/usr/bin/otool', '-l', str(old_binary)], [str(NM), '--format=just-symbols', '--defined-only', '--extern-only', str(old_binary)]]
    plan = result['planned_next_link']
    assert plan['command'] == expected and plan['next_image_observations'] == image_commands and plan['actual_execution'] is False
    assert plan['counted_fresh_glue'] == dict(path=str(driver), sha256=DRIVER_SHA)
    assert plan['PackageCompiler_initialization_api_used'] is False
    link = list(expected); link[8] = str(binary)
    link[1:1] = ['-isysroot', str(SDK)]
    images = [[str(binary) if item == str(old_binary) else item for item in command] for command in image_commands]
    environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C', OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
    save(output/'link-request.json', dict(command=link, image_commands=images, environment=environment,
        owned_command_cwd=str(service.HERE), output_relocation_only=False, explicit_existing_sdk=str(SDK),
        sdk_settings_sha256=SDK_SHA, original_plan=plan,
        source_archive_review=dict(path=str(ROOT), sha256=ROOT_SHA), runtime_aot_proven=False, chart_admission=False))
    def owned(command, name, timeout):
        base.verify(pins)
        progress['attempted_command_names'].append(name)
        actual = service.owned_command(guard, harness, command, environment, output/'commands', common_fd, timeout, name)
        detail = actual['detail']
        assert detail['command'] == command and type(detail['exit_status']) is type(detail['final_exit_status']) is int
        assert detail['exit_status'] == detail['final_exit_status'] == 0 and detail['inherited_common_mutex'] is True
        assert not any(detail.get(key) for key in ('error', 'error_type', 'cleanup_error', 'cleanup_errors'))
        progress['completed_command_names'].append(name)
        return actual
    linked = owned(link, 'link-retained-safe-archive', 180)
    assert linked['stdout'] == b''
    assert binary.is_file() and not binary.is_symlink() and os.access(binary, os.X_OK)
    with binary.open('rb') as stream: header = stream.read(32)
    assert header[:4] == b'\xcf\xfa\xed\xfe' and int.from_bytes(header[4:8], 'little') == 0x0100000c
    assert int.from_bytes(header[12:16], 'little') == 2, 'Expected thin arm64 Mach-O executable'
    binary_sha = sha(binary); bind(binary, binary_sha, pins)
    observed = [owned(command, name, 60) for command, name in zip(images,
        ('image-architecture', 'image-linked-libraries', 'image-load-commands', 'image-defined-external-symbols'))]
    assert all(item['stderr'] == b'' for item in observed)
    assert observed[0]['stdout'].decode('ascii').strip() == 'arm64'
    assert observed[1]['stdout'] and observed[2]['stdout']
    symbols = observed[3]['stdout'].decode('ascii').splitlines()
    assert symbols.count('_clbg_entry') == 1, 'Missing or ambiguous linked native entry'
    base.verify(pins)
    save(output/'link-result.json', dict(status='retained-safe-archive-linked-awaiting-runtime-owner-and-fallback-review',
        binary=dict(path=str(binary), sha256=binary_sha, bytes=binary.stat().st_size, header32=header.hex(),
            container='thin-arm64-Mach-O-executable'), actual_defined_native_entry_count=1,
        archive=dict(path=str(archive), sha256=pins[str(archive.resolve())]),
        counted_fresh_glue=dict(path=str(driver), sha256=DRIVER_SHA), original_archive_result_sha256=RESULT_SHA,
        actual_link_command=link, actual_image_commands=images, owned_receipts=str(output/'commands'),
        successful_compile_reexecutions=0, archive_inspection_reexecutions=0, linker_commands=1, image_observation_commands=4,
        actual_julia_processes=0, actual_workload_executions=0, benchmark_runs=0, fixture_reexecutions=0, LLDB_attempts=0,
        native_owner_qualified=False, actual_ir_removal_qualified=False, fallback_closure_qualified=False,
        runtime_aot_proven=False, chart_admission=False, pins=dict(pins)))


def main():
    parser = argparse.ArgumentParser()
    for name in ('revision', 'worker-sha256', 'review-sha256', 'lipo-sha256', 'otool-sha256'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    assert args.revision == REVISION and sys.dont_write_bytecode and Path(sys.executable).resolve() == Path(PYTHON).resolve()
    assert all(re.fullmatch('[a-f0-9]{64}', value) for key, value in vars(args).items() if key.endswith('_sha256'))
    def interrupted(signum, frame): raise KeyboardInterrupt('Julia saved link interrupted by signal '+str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM): signal.signal(signum, interrupted)
    with ExitStack() as leases:
        for owner in (OWNER, OLD_CLBG/'continuation/owned-jobs/julia-saved-safe-build-seal-v1',
            OLD_CLBG/'continuation/owned-jobs/julia-official-static-io-safe-trim-nbody-v1',
            CLBG/'continuation/owned-jobs/julia-saved-safe-archive-link-v1',
            CLBG/'continuation/owned-jobs/julia-saved-safe-archive-link-v2'):
            lease = leases.enter_context((owner/'owner.lock').open('rb'))
            fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
            actual, named = os.fstat(lease.fileno()), (owner/'owner.lock').stat()
            assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino)
        own_path = HERE/'saved-archive-link-v3-owner.lock'
        own = leases.enter_context(own_path.open('a+')); fcntl.flock(own, fcntl.LOCK_EX | fcntl.LOCK_NB)
        actual, named = os.fstat(own.fileno()), own_path.stat()
        assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino)
        print('WAIT common mutex: one retained Julia archive link and four image observations', flush=True)
        with LOCK.open('r+') as common:
            fcntl.flock(common, fcntl.LOCK_EX)
            actual, named = os.fstat(common.fileno()), LOCK.stat()
            assert (actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino) and actual.st_ino == 79859134
            output, build = HERE/'jobs'/REVISION, HERE/'.build'/REVISION
            assert not output.exists() and not build.exists()
            assert not any(path.is_symlink() for path in (output, build, output.parent, build.parent, HERE))
            output.mkdir(parents=True, exist_ok=False); build.mkdir(parents=True, exist_ok=False)
            pins, failures = {}, []
            progress = dict(attempted_command_names=[], completed_command_names=[])
            outcome = dict(status='failed-Julia-saved-archive-link', planned_link_commands=1, planned_image_commands=4,
                actual_julia_processes=0, successful_compile_reexecutions=0, archive_inspection_reexecutions=0,
                actual_workload_executions=0, benchmark_runs=0, fixture_reexecutions=0, LLDB_attempts=0,
                native_owner_qualified=False, actual_ir_removal_qualified=False, fallback_closure_qualified=False,
                runtime_aot_proven=False, chart_admission=False)
            signal.alarm(600)
            try:
                bind(Path(sys.executable), PYTHON_SHA, pins)
                run(args, output, build, pins, common.fileno(), progress)
                outcome['status'] = 'retained-safe-archive-linked-awaiting-runtime-owner-and-fallback-review'
            except BaseException as error:
                outcome.update(error=str(error) or type(error).__name__, error_type=type(error).__name__)
                with (output/'error.log').open('x') as stream: stream.write(traceback.format_exc())
                raise
            finally:
                signal.alarm(0)
                available, actual_receipts = {}, []
                for path, expected in pins.items():
                    try: assert sha(path) == expected
                    except BaseException as error: failures.append(dict(path=path, error=str(error) or type(error).__name__))
                for tree in (output, build):
                    for path in tree.rglob('*'):
                        if path.is_file():
                            try: available[str(path)] = sha(path)
                            except BaseException as error: failures.append(dict(path=str(path), error=str(error) or type(error).__name__))
                for name in progress['attempted_command_names']:
                    path = output/'commands'/(name+'.json')
                    if path.is_file():
                        try:
                            receipt = json.loads(path.read_bytes())
                            actual_receipts.append(dict(name=name, path=str(path), sha256=available[str(path)],
                                pid=receipt.get('pid'), exit_status=receipt.get('exit_status'), final_exit_status=receipt.get('final_exit_status')))
                        except BaseException as error: failures.append(dict(path=str(path), error=str(error) or type(error).__name__))
                if failures: outcome.update(status='failed-terminal-integrity', integrity_errors=failures)
                outcome.update(progress, actual_owned_command_receipts=actual_receipts,
                    finished_at=datetime.now(timezone.utc).isoformat(), prerequisite_pins=pins, available_evidence_pins=available,
                    exclusive_common_mutex_held=True, common_mutex_inode=79859134, original_safe_compile_and_archives_preserved=True)
                save(output/'outcome.json', outcome)
                if failures: raise RuntimeError('Julia link terminal integrity failed; partial evidence retained')


if __name__ == '__main__': main()
