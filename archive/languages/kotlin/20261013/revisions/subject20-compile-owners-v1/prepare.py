"""Compile the twenty retained Kotlin inputs; save all generated class owners."""
import argparse
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
SAVED = H/'revisions/saved-runtime-probe-v1'
SAVED_SHA = '98a1ccc423e3bc1ff32a0cae1fa6fa528032e3b410b881a333a911e5334a0e59'
SAVED_NOTE_SHA = '642c17c7b7909ecab20015af8cbd7c146062ef3f8059ac7c3d0f26fa740fbe8e'
ROOT = C/'continuation/jobs/kotlin-saved-probe-closed-review-v1/receipt.json'
ROOT_SHA = '0d0c8d6ac6bc18577f5b71979408e86ce3c557b63387f2c7ddd0598cdac0260b'
OWNER = C/'continuation/owned-jobs/kotlin-saved-runtime-probe-v1'
RESULT = SAVED/'jobs/saved-runtime-probe-v1/intake-result.json'
RESULT_SHA = '2feb46e6dd49649372c803c1d6ed2dc7df33b5ae8480889ac3e2c2b17bbc87f9'
BODY_SHA = 'a79c088703e7036da6187d5621c11d21e959c4008fe8dd61d4f7f99071689b08'
DURABLE_SHA = 'f76f7d18032ae8db8f8fdcb7735a03e3a5adeb3fac7835eb995bba86e99110f7'
REQUEST_SHA = 'b3300896754d8fc82a64511e5e163cb3a86d34fe1e28cf0003220329d7ee47e2'
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
LOCK = Path('/tmp/mech-clbg-timing.lock')
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
STATUS = 'Kotlin20-classes-and-bytecode-captured-awaiting-scored-owner-and-runtime-review'


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def cold_saved(pins):
    path = SAVED/'resume.py'
    assert not path.stat().st_mode & 0o222 and sha(path) == SAVED_SHA
    assert not (SAVED/'REVIEW.md').stat().st_mode & 0o222 and sha(SAVED/'REVIEW.md') == SAVED_NOTE_SHA
    name = 'kotlin_subject20_saved_runtime_helpers'; assert name not in sys.modules
    saved = types.ModuleType(name); saved.__file__ = str(path); sys.modules[name] = saved
    exec(compile(path.read_bytes(), str(path), 'exec'), saved.__dict__)
    base = saved.load_original(pins)
    base.bind(path, SAVED_SHA, pins); base.bind(SAVED/'REVIEW.md', SAVED_NOTE_SHA, pins)
    return saved, base


def retained(saved, base, pins):
    root = base.read(ROOT, ROOT_SHA, pins)
    assert root['status'] == 'closed-Kotlin-saved-generic-runtime-probe-passed-no-subject-execution'
    assert (root['worker_pid'], root['command_pid'], root['native_pid'], root['verified_pins']) == (39194,39200,39204,5460)
    assert root['common_mutex_held'] is True and root['common_mutex_inode'] == 79859134
    assert root['new_native_tool_commands'] == 1 and root['successful_native_commands_reused'] == 2
    assert root['subject_compiler_commands'] == root['native_benchmarks'] == root['old_tool_fixture_reexecutions'] == 0
    assert root['source_forms'] == 20 and root['counted_main_and_helper_inputs'] == 40 and root['chart_admission'] is False
    for path, digest in root['pins'].items(): base.bind(path,digest,pins)
    expected = [str(PYTHON),'-I','-S','-B','-u',str(SAVED/'resume.py'),'--revision','saved-runtime-probe-v1',
        '--worker-sha256',SAVED_SHA,'--review-sha256',SAVED_NOTE_SHA]
    ended = base.read(OWNER/'terminal.json',DURABLE_SHA,pins)
    request = base.read(OWNER/'request.json',REQUEST_SHA,pins)
    start, worker, launch = [base.read(OWNER/name,root['pins'][str(OWNER/name)],pins)
        for name in ('command-started.json','worker-started.json','launch.json')]
    assert all(item['command'] == expected and item['cwd'] == str(C.parent.parent) for item in (request,start,worker,launch))
    assert ended['status'] == 'command-exited-zero-awaiting-report-review' and type(ended['exit_code']) is int and ended['exit_code'] == 0
    assert ended['actual_command_started'] is True and ended['stop_signals'] == []
    assert request['qualification_granted'] is request['automatic_retry'] is ended['qualification_granted'] is ended['automatic_retry'] is False
    assert request['common_mutex_owned_by_target_command'] is worker['common_mutex_owned_by_target_command'] is True
    assert worker['inherited_private_lease'] is worker['detached_session'] is True
    assert start['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
    assert start['command_identity'] == ended['command_identity'] and start['command_pid'] == ended['command_pid'] == 39200
    assert worker['worker_identity'] == ended['worker_identity'] and worker['worker_identity']['pid'] == launch['worker_identity']['pid'] == 39194
    actual = ended['command_identity']['listing'].split(None,7)
    assert actual[:2] == ['39200','39194'] and actual[7].split() == expected
    assert not any(ended.get(key) for key in ('error','error_type','exception_cleanup','error_log_write_failure'))
    result = base.read(RESULT,RESULT_SHA,pins)
    outcome = base.read(RESULT.with_name('outcome.json'),BODY_SHA,pins)
    assert result['status'] == outcome['status'] == 'saved-Kotlin-compiler-and-generic-JVM-probe-passed-awaiting-subject-review'
    assert not any(outcome.get(key) for key in ('error','error_type','integrity_errors','available_bytes_not_fully_pinned'))
    for mapping in (outcome['prerequisite_pins'],outcome['available_evidence_pins'],result['pins']):
        for path,digest in mapping.items(): base.bind(path,digest,pins)
    assert result['actual_jvm_flags'] == root['actual_jvm_flags'] and result['actual_collectors'] == root['actual_collectors']
    assert result['actual_generic_runtime_probe'] == root['actual_generic_runtime_probe']
    assert result['subject_compiler_commands'] == result['native_benchmarks'] == result['fixture_reexecutions'] == 0
    assert result['authored_forms'] == result['counted_main_inputs'] == result['counted_support_inputs'] == 20
    _, compiler, _, inventory, _ = saved.saved_intake(base,pins)
    assert result['compiler'] == str(compiler/'bin/kotlinc')
    assert result['retained_source_inventory'] == dict(path=str(saved.OLD_OUT/'source-input-inventory.json'),
        sha256=pins[str(saved.OLD_OUT/'source-input-inventory.json')])
    return result,compiler,inventory


def service_closure(base,pins):
    service = base.cold(base.SERVICE,'kotlin_subject20_original_owned_service',pins)
    guard = base.cold(service.GUARD,'kotlin_subject20_original_guard',pins)
    previous = importlib.machinery.SourceFileLoader.get_code
    def checked(loader,fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(HOST/'benchmarks/clbg'):
            assert path.suffix == '.py' and str(path) in pins
            return compile(base.bind(path,pins[str(path)],pins).read_bytes(),str(path),'exec')
        return previous(loader,fullname)
    importlib.machinery.SourceFileLoader.get_code = checked
    try: harness = guard.load_harness()
    finally: importlib.machinery.SourceFileLoader.get_code = previous
    for module in list(sys.modules.values()):
        filename = getattr(module,'__file__',None)
        if filename and Path(filename).is_relative_to(HOST/'benchmarks/clbg'):
            path = Path(filename).absolute(); assert str(path) in pins; base.bind(path,pins[str(path)],pins)
    assert not list(service.HERE.glob('*.class')) and not (service.HERE/'.java').exists()
    return service,guard,harness


def run(saved,base,output,build,pins,fd,progress):
    prior,compiler,inventory = retained(saved,base,pins)
    service,guard,harness = service_closure(base,pins)
    rows = inventory['forms']; assert len(rows) == len({row['id'] for row in rows}) == 20
    stdlib = compiler/'lib/kotlin-stdlib.jar'; base.bind(stdlib,pins[str(stdlib)],pins)
    completed = []
    base.save(output/'contract.json',dict(status='twenty-independent-compiles-and-whole-class-owner-dumps',
        source_inventory=prior['retained_source_inventory'],saved_probe=dict(path=str(RESULT),sha256=RESULT_SHA),
        compiler_commands=20,bytecode_reader_commands=20,passed_tool_or_fixture_reexecutions=0,
        subject_main_executions=0,counted_roles=['application','application-helper'],authored_scored_launcher_inputs=0,
        unknown_compiler_diagnostic_policy='retain-and-stop-without-retry',chart_admission=False))
    for row in rows:
        case=output/row['id'];case.mkdir(); folder=build/row['id'];folder.mkdir()
        classes=folder/'classes';classes.mkdir()
        for name in ('home','config','tmp'): (folder/name).mkdir()
        environment=dict(prior['runtime_environment'])
        assert all(key not in environment for key in saved.EMPTY_OPTIONS)
        flags=base.FLAGS+['-Duser.home='+str(folder/'home'),'-Djava.io.tmpdir='+str(folder/'tmp')]
        environment.update(HOME=str(folder/'home'),XDG_CONFIG_HOME=str(folder/'config'),TMPDIR=str(folder/'tmp')+os.sep,JAVA_OPTS=' '.join(flags))
        main,support=[Path(item['path']) for item in row['authored_inputs']]
        assert [item['role'] for item in row['authored_inputs']] == ['application','application-helper']
        assert main.read_text().startswith('package clbg.'+row['benchmark']+'\n') and support.read_text().startswith('package clbg\n')
        expected=list(row['compile_command_proposed']); assert expected == [str(compiler/'bin/kotlinc'),str(support),str(main),'-jvm-target','17','-no-reflect','-d',str(main.parent/'classes')]
        command=expected[:-1]+[str(classes)]
        base.verify(pins)
        progress['compiler_commands_requested']+=1
        compiled=service.owned_command(guard,harness,command,environment,case/'compile',fd,180,'compile')
        base.owned(compiled['detail']);progress['compiler_commands_completed']+=1
        assert compiled['stdout'] == compiled['stderr'] == b'', 'Unexpected compiler diagnostics retained; no generic waiver'
        artifacts=[]; owners=[]
        for path in sorted(classes.rglob('*')):
            assert not path.is_symlink()
            if not path.is_file():continue
            relative=path.relative_to(classes)
            assert path.suffix == '.class' or relative == Path('META-INF/main.kotlin_module')
            if path.suffix == '.class':
                raw=path.read_bytes();assert raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8],'big') == 61
                assert relative.parts[0] == 'clbg' and (relative.parts[1] == row['benchmark'] or relative.as_posix().startswith('clbg/Support'))
                owners.append(relative.with_suffix('').as_posix().replace('/','.'))
            digest=base.sha(path);base.bind(path,digest,pins);path.chmod(path.stat().st_mode&~0o222)
            artifacts.append(dict(path=str(path),sha256=digest,bytes=path.stat().st_size))
        assert artifacts and 'clbg.Support' in owners and 'clbg.'+row['benchmark']+'.MainKt' in owners
        classpath=os.pathsep.join((str(classes),str(stdlib)))
        javap=base.JDK/'bin/javap';base.bind(javap,pins[str(javap)],pins)
        read_command=[str(javap),*['-J'+flag for flag in flags],'-classpath',classpath,'-p','-c','-s','-v',*owners]
        base.verify(pins);progress['reader_commands_requested']+=1
        decoded=service.owned_command(guard,harness,read_command,environment,case/'owners',fd,120,'javap')
        base.owned(decoded['detail']);progress['reader_commands_completed']+=1
        assert decoded['stderr'] == b'' and decoded['stdout']
        for path in (main.parent/'classes',):assert not any(path.iterdir())
        record=dict(id=row['id'],benchmark=row['benchmark'],variant=row['variant'],alias_of=row['alias_of'],
            physical_inputs=row['authored_inputs'],compile_command=compiled['detail'],generated_artifacts=artifacts,
            class_owner_names=owners,classfile_target_major=61,bytecode_reader=decoded['detail'],
            runtime_command=[str(base.JDK/'bin/java'),*flags,'-cp',classpath,'clbg.'+row['benchmark']+'.MainKt','{n}'],
            runtime_environment=environment,runtime_classpath_candidates=[dict(path=str(stdlib),sha256=pins[str(stdlib)])],
            source_to_compile_command_binding=True,bytecode_semantic_owner_review_qualified=False,
            actual_subject_runtime_dependency_closure_qualified=False,raw_stdio_qualified=False,source_work_qualified=False,
            subject_JIT_method_evidence_qualified=False,canonical_loc=None,formatted_loc=None,chart_admission=False)
        base.save(case/'result.json',record);completed.append(record);progress['completed_profile_ids'].append(row['id'])
        print('COMPLETED Kotlin compile+class artifacts:',row['id'],flush=True)
    assert len(completed) == 20 and progress['compiler_commands_completed'] == progress['reader_commands_completed'] == 20
    base.verify(pins)
    base.save(output/'preparation-result.json',dict(status=STATUS,profiles=completed,source_inventory=prior['retained_source_inventory'],
        total_compiled_profiles=20,compiler_commands=20,bytecode_reader_commands=20,passed_tool_fixture_reexecutions=0,
        subject_main_executions=0,raw_stdio_qualified=False,helper_semantics_qualified=False,source_work_qualified=False,
        compiler_native_dependency_execution_qualified=False,subject_JIT_method_evidence_qualified=False,
        canonical_loc=None,formatted_loc=None,chart_admission=False,pins=dict(pins)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('revision','worker-sha256','review-sha256'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();assert args.revision == 'subject20-compile-owners-v1'
    assert sys.dont_write_bytecode and Path(sys.executable).resolve() == PYTHON.resolve()
    assert all(re.fullmatch('[a-f0-9]{64}',v) for k,v in vars(args).items() if k.endswith('_sha256'))
    def interrupted(signum,frame):raise KeyboardInterrupt('Kotlin subjects interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP,signal.SIGALRM):signal.signal(sig,interrupted)
    with ExitStack() as leases:
        for path in (OWNER/'owner.lock',SAVED/'owner.lock',C/'continuation/owned-jobs/kotlin-official-compiler-retained-jdk-v1/owner.lock',
            HOST/'benchmarks/clbg/continuation/owned-jobs/clojure-publication-metadata-v1/owner.lock'):
            held=leases.enter_context(path.open('rb'));fcntl.flock(held,fcntl.LOCK_SH|fcntl.LOCK_NB)
            a,b=os.fstat(held.fileno()),path.stat();assert (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino)
        path=P/'owner.lock';held=leases.enter_context(path.open('a+'));fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
        a,b=os.fstat(held.fileno()),path.stat();assert (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino)
        print('WAIT common mutex: twenty Kotlin subject compiles and class-owner captures',flush=True)
        with LOCK.open('r+') as common:
            fcntl.flock(common,fcntl.LOCK_EX)
            a,b=os.fstat(common.fileno()),LOCK.stat();assert (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino) and a.st_ino == 79859134
            output,build=P/'jobs'/args.revision,H/'.build'/args.revision
            assert not output.exists() and not build.exists()
            assert not any(path.is_symlink() for path in (P,H,output.parent,build.parent))
            output.mkdir(parents=True);build.mkdir(parents=True)
            pins,errors={},[]
            progress=dict(status='failed-Kotlin-subject20-preparation',compiler_commands_requested=0,compiler_commands_completed=0,
                reader_commands_requested=0,reader_commands_completed=0,completed_profile_ids=[],subject_main_executions=0,
                passed_tool_fixture_reexecutions=0,chart_admission=False)
            signal.alarm(6600)
            try:
                for path,digest in ((P/'prepare.py',args.worker_sha256),(P/'REVIEW.md',args.review_sha256),(PYTHON.resolve(),PYTHON_SHA)):
                    assert sha(path) == digest
                    if path.suffix in ('.py','.md'):assert not path.stat().st_mode&0o222
                    pins[str(path)]=digest
                saved,base=cold_saved(pins);run(saved,base,output,build,pins,common.fileno(),progress);progress['status']=STATUS
            except BaseException as error:
                progress.update(error=str(error) or type(error).__name__,error_type=type(error).__name__)
                with (output/'error.log').open('x') as stream:stream.write(traceback.format_exc())
                raise
            finally:
                signal.alarm(0);available={}
                try:
                    a,b=os.fstat(common.fileno()),LOCK.stat();assert (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino) and a.st_ino == 79859134
                except BaseException as error:errors.append(dict(path=str(LOCK),error=str(error) or type(error).__name__))
                for path,digest in pins.items():
                    try:assert sha(path) == digest
                    except BaseException as error:errors.append(dict(path=path,error=str(error) or type(error).__name__))
                for root in (output,build):
                    for path in root.rglob('*'):
                        if path.is_file() and not any(part in ('home','config','tmp') for part in path.relative_to(root).parts):
                            try:available[str(path)]=sha(path)
                            except BaseException as error:errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
                if errors:progress.update(status='failed-terminal-integrity',integrity_errors=errors)
                progress.update(finished_at=datetime.now(timezone.utc).isoformat(),prerequisite_pins=pins,available_evidence_pins=available,
                    common_mutex_held=True,common_mutex_inode=79859134,original_host_inputs_preserved=True,private_startup_paths_excluded=True)
                with (output/'outcome.json').open('x') as stream:json.dump(progress,stream,indent=2);stream.write('\n')
                if errors:raise RuntimeError('Kotlin preparation terminal integrity failed; partial output preserved')


if __name__ == '__main__':main()
