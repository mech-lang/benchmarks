"""Prepare a fresh vendor SDK copy, then run only the retained pre-make route.

No Builder, download, compiler, extension load, primitive test or benchmark is
repeated here. Generation remains an unscored SDK observation pending review.
"""
import argparse
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import traceback
import types

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/rebol/sdk-generation-v1'
CHECK=ROOT/'archive/qualification/rebol/checks/rebol-builder-spec-only-closed-review-v1'
ARCHIVE=ROOT/'archive/languages/rebol/20261013'
HOST=Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
OLD=HOST/'rebol-comparison/20261013'
ORIGINAL=OLD/'.build/saved-runtime-source-intake-v1/source-original'
RUNTIME=OLD/'.build/runtime-v1/runtime/rebol3'
RUNTIME_SHA='27e255625d4d9928f5d726d3f2546fa64ff82a09a2b971cbc3a236a0bbed08a2'
ROOT_SHA='2573872ee1076a173ebb225f320e9a38389d7ed0addcdaf2120ef686f06aa542'
INTAKE_SHA='7973ca054bf8b93d4513cdd60fa2466079c416653e1a259bf70018fac6c1e4e2'
PYTHON=Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA='ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK=Path('/tmp/mech-clbg-timing.lock')
SUPERVISOR=ROOT/'tools/qualification/rebol_sdk_supervisor.py'
HEADER_NAMES='gen-funcs gen-funcargs gen-strings gen-evaltypes gen-maketypes gen-comptypes reb-types ext-types gen-exttypes gen-bootdefs gen-sysobj reb-dialect reb-evtypes gen-errnums gen-portmodes gen-sysctx gen-boot gen-config host-init host-ext-window host-lib reb-lib reb-lib-lib'.split()
GENERATED={f'src/include/{name}.h' for name in HEADER_NAMES}|{
    'src/generated/gen-symbols.reb','src/generated/gen-natives.reb','src/generated/gen-host-init.reb',
    'src/mezz/base-collected.reb','src/core/b-boot.c','reb-lib-doc.txt'}


@contextmanager
def regular_stream(path):
    path=Path(path); before=path.lstat()
    assert stat.S_ISREG(before.st_mode),('Regular file required',str(path))
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        opened=os.fstat(stream.fileno())
        assert stat.S_ISREG(opened.st_mode) and (opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino)
        yield stream
        named=path.lstat()
        assert stat.S_ISREG(named.st_mode) and (opened.st_dev,opened.st_ino)==(named.st_dev,named.st_ino)


def file_bytes(path):
    with regular_stream(path) as stream:return stream.read()


def sha(path):
    with regular_stream(path) as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def new_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,indent=2)+'\n').encode()
    with path.open('xb') as stream:
        opened=os.fstat(stream.fileno());stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return raw,(opened.st_dev,opened.st_ino)


def bind(path,expected,pins):
    path=Path(path)
    assert sha(path)==expected,('Pinned bytes changed',str(path))
    assert str(path) not in pins or pins[str(path)]==expected
    pins[str(path)]=expected
    return path


def read(path,expected,pins):
    path=bind(path,expected,pins);raw=file_bytes(path)
    assert hashlib.sha256(raw).hexdigest()==expected
    return json.loads(raw)


def cold(path,expected,name,pins):
    path=bind(path,expected,pins);raw=file_bytes(path);assert hashlib.sha256(raw).hexdigest()==expected
    assert name not in sys.modules
    module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


@contextmanager
def common():
    with regular_stream(LOCK) as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        opened,named=os.fstat(stream.fileno()),LOCK.stat()
        assert (opened.st_dev,opened.st_ino)==(named.st_dev,named.st_ino) and opened.st_ino==79859134
        identity=(opened.st_dev,opened.st_ino)
        try:yield stream
        finally:verify_leases([(LOCK,stream,identity)])


def verify_leases(leases):
    for path,stream,expected in leases:
        opened,named=os.fstat(stream.fileno()),Path(path).lstat()
        assert stat.S_ISREG(opened.st_mode) and stat.S_ISREG(named.st_mode)
        assert (opened.st_dev,opened.st_ino)==(named.st_dev,named.st_ino)==expected,('Lease identity changed',str(path))


def checked_runtime():
    assert sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
    assert Path(sys.executable).resolve()==PYTHON.resolve() and sha(PYTHON.resolve())==PYTHON_SHA


def retained(pins):
    root=read(CHECK/'receipt.json',ROOT_SHA,pins)
    assert root['status']=='closed-actual-Rebol-spec-only-native0-and-898-preserved'
    assert root['original898_files_preserved'] is root['common_mutex_held'] is True
    assert root['durable_exit_code']==root['owned_native_exit']==0 and root['owned_spec_commands']==1
    assert root['header_generation_executed'] is root['extension_build_executed'] is root['chart_admission'] is False
    for original,record in root['copies'].items():
        suffix=record['path'].split('/rebol-builder-spec-only-closed-review-v1/',1)[1]
        bind(CHECK/suffix,record['sha256'],pins)
    terminal=read(CHECK/'durable/terminal.json',root['durable_terminal_sha256'],pins)
    request=read(CHECK/'durable/request.json',root['request_sha256'],pins)
    start=json.loads(file_bytes(CHECK/'durable/command-started.json'))
    worker=json.loads(file_bytes(CHECK/'durable/worker-started.json'))
    assert request['command']==start['command']==worker['command']
    assert terminal['exit_code']==0 and terminal['stop_signals']==[] and terminal['actual_command_started'] is True
    assert terminal['command_pid']==start['command_pid']==root['command_pid']==35504
    assert terminal['worker_identity']==worker['worker_identity'] and terminal['worker_identity']['pid']==35498
    assert not any(terminal.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure'))
    report=read(CHECK/'evidence/report.json',root['report_sha256'],pins)
    body=read(CHECK/'evidence/terminal-pin.json',root['body_terminal_sha256'],pins)
    assert report['terminal_evidence_complete'] is True and report['pins']==body['partial_evidence_pins']
    assert body['report_sha256']==root['report_sha256']
    actual=read(CHECK/'evidence/spec-only.json',root['native_command_receipt_sha256'],pins)
    startup=json.loads(file_bytes(CHECK/'evidence/spec-only-startup.json'))
    assert actual['pid']==startup['pid']==root['owned_native_pid']==35514
    assert actual['exit_status']==actual['final_exit_status']==0 and actual['inherited_common_mutex'] is True
    assert not any(actual.get(k) for k in ('error','cleanup_errors'))
    intake=read(ARCHIVE/'sdk-qualification/builder-intake-v1/intake.json',INTAKE_SHA,pins)
    assert intake['source_copy_count']==len(intake['source_copy_files'])==898
    assert len({r['original'] for r in intake['source_copy_files']})==898
    source_pins={}
    for entry in intake['source_copy_files']:
        original=Path(entry['original']);assert original.is_relative_to(ORIGINAL)
        assert report['pins'][str(original)]==entry['sha256']
        bind(original,entry['sha256'],source_pins)
    assert set(source_pins)=={str(p) for p in ORIGINAL.rglob('*') if p.is_file()}
    assert not any(p.is_symlink() for p in ORIGINAL.rglob('*'))
    pins.update(source_pins)
    bind(RUNTIME,RUNTIME_SHA,pins)
    # Preserve the historical ownership evidence without executing old services
    # or reopening old intake entry points. Generation uses the bounded local
    # supervisor pinned into the new plan.
    for path,expected in report['pins'].items():
        if path.endswith('.py') and Path(path).is_relative_to(HOST):bind(path,expected,pins)
    fixture=HOST/'c3-comparison/20261012/proposal-seals/private-v1/ownership-fixtures.json'
    fixture_command=read(fixture,report['pins'][str(fixture)],pins)
    assert fixture_command['exit_status']==fixture_command['final_exit_status']==0
    assert fixture_command['inherited_common_mutex'] is True
    inventory=fixture.with_name('ownership-fixtures-inventory.json')
    assert fixture_command['command'][-2:]==['--receipt',str(inventory)]
    observed=read(inventory,report['pins'][str(inventory)],pins)
    assert observed['status']=='passed' and observed['successful'] is True and observed['tests_run']==11
    assert set(observed['actual_test_ids'])==set(observed['expected_test_ids']) and len(set(observed['actual_test_ids']))==11
    assert all(observed[k]==[] for k in ('failures','errors','skipped','expected_failures','unexpected_successes'))
    return root,report,source_pins


def prepare(args):
    checked_runtime()
    assert not any(os.path.lexists(p) for p in (args.plan,args.work,args.output))
    with common():
        pins={};root,report,source_pins=retained(pins)
        specmod=cold(ROOT/'tools/qualification/rebol_spec.py',sha(ROOT/'tools/qualification/rebol_spec.py'),'sdk_saved_spec_reader',pins)
        raw=file_bytes(bind(CHECK/'raw-spec/spec.reb',specmod.SPEC_SHA,pins))
        review=specmod.review(raw)
        expected_review=read(PACKET/'spec-source-review.json',sha(PACKET/'spec-source-review.json'),pins)
        assert review==expected_review
        for values in review['arrays'].values():
            for name in values:
                if name.endswith('/'):
                    assert (ORIGINAL/name).is_dir()
                else:
                    # The vendor spec also names outputs produced by pre-make.
                    # Their exact membership and bytes are validated after generation.
                    assert str(ORIGINAL/name) in source_pins or name in GENERATED,('Spec input outside retained source closure',name)
        # Existing vendor source and Builder copy are never written. Only this
        # fresh copy can receive generated boot files and complete SDK headers.
        args.work.mkdir(parents=True)
        copy=args.work.resolve()/'source';copy.mkdir()
        copy_pins={}
        for path,expected in source_pins.items():
            target=copy/Path(path).relative_to(ORIGINAL);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(file_bytes(path))
            target.chmod(0o644)
            bind(target,expected,copy_pins)
        assert len(copy_pins)==898 and not (copy/'.git').exists()
        for name in ('home','data'): (args.work/name).mkdir()
        environment=dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',HOME=str(args.work.resolve()/'home'),
            REBOL_HOME=str(args.work.resolve()/'data'),CI='true',LANG='C',LC_ALL='C')
        # These are the only written selected vendor shell routes. A missing
        # ldd remains a real attempted/missing query, never a fabricated result.
        os_inputs={}
        for path in ('/bin/sh','/bin/ps','/usr/bin/sw_vers','/System/Library/CoreServices/SystemVersion.plist'):
            bind(path,sha(path),pins);os_inputs[path]=pins[path]
        assert not any((Path(folder)/'ldd').exists() for folder in environment['PATH'].split(':'))
        for path in (Path(__file__).resolve(),ROOT/'tools/qualification/rebol_sdk_exec.py',SUPERVISOR,PACKET/'generate.reb',PYTHON.resolve()):
            bind(path,sha(path),pins)
        pins.update(copy_pins)
        command=[str(RUNTIME),'-q','-s',str(PACKET/'generate.reb'),str(CHECK/'raw-spec/spec.reb'),str(copy),str(args.output.resolve())]
        plan=dict(schema='rebol-retained-spec-sdk-generation-v1',controller=str(Path(__file__).resolve()),
            controller_sha256=sha(__file__),runtime=str(RUNTIME),runtime_sha256=RUNTIME_SHA,
            raw_spec=str(CHECK/'raw-spec/spec.reb'),raw_spec_sha256=specmod.SPEC_SHA,
            generator_wrapper=str(PACKET/'generate.reb'),source_copy=str(copy),output=str(args.output.resolve()),
            command=command,environment=environment,pins=pins,source_pins=source_pins,initial_copy_pins=copy_pins,
            historical_pins=report['pins'],os_inputs=os_inputs,ldd_present_at_prepare=False,
            source_files=898,source_and_saved_spec_files=899,expected_generated_paths=sorted(GENERATED),
            retained_spec_processes=1,repeated_Builder_processes=0,repeated_runtime_queries=0,
            compiler_invocations=0,extension_build_authorized=False,runtime_configuration_admitted=False,
            source_work_qualified=False,chart_admission=False,automatic_retry=False,
            expected_shell_queries=['sw_vers -productVersion','ldd --version'],
            timeout_seconds=300,cleanup_total_timeout_seconds=5,
            supervisor=str(SUPERVISOR),supervisor_sha256=pins[str(SUPERVISOR)],
            generated_headers_require_independent_review=True)
        for path,expected in pins.items():assert sha(path)==expected,('SDK prepare pin changed',path)
        current_copy,errors=artifact_pins((copy,))
        assert not errors and current_copy==copy_pins,'SDK preparation copy changed'
        raw,_=new_json(args.plan,plan)
        for path,expected in pins.items():assert sha(path)==expected,('SDK post-write prepare pin changed',path)
        current_copy,errors=artifact_pins((copy,))
        assert not errors and current_copy==copy_pins,'SDK post-write preparation copy changed'
        assert file_bytes(args.plan)==raw,'Prepared plan bytes changed'
    print(json.dumps(dict(plan=str(args.plan),sha256=hashlib.sha256(raw).hexdigest(),native_commands=0)),flush=True)


def artifact_pins(bases):
    """Keep readable outputs and explicit failures without losing terminal data."""
    pins,errors={},[]
    def failed(path,error):
        errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
    for base in bases:
        try:
            assert stat.S_ISDIR(Path(base).lstat().st_mode),'Physical artifact directory required'
            for directory,dirs,files in os.walk(base,onerror=lambda error:failed(error.filename,error)):
                for name in list(dirs):
                    path=Path(directory)/name
                    try:assert stat.S_ISDIR(path.lstat().st_mode),'Unexpected linked or non-directory artifact'
                    except BaseException as error:
                        dirs.remove(name);failed(path,error)
                for name in files:
                    path=Path(directory)/name
                    try:
                        assert stat.S_ISREG(path.lstat().st_mode),'Unexpected nonregular artifact'
                        pins[str(path)]=sha(path)
                    except BaseException as error:failed(path,error)
        except BaseException as error:failed(base,error)
    return pins,errors


def verified_bytes(path,validated):
    raw=file_bytes(path)
    assert hashlib.sha256(raw).hexdigest()==validated[str(path)],('Validated artifact changed',str(path))
    return raw


def verify_generated(plan,specmod,validated):
    output,copy=Path(plan['output']),Path(plan['source_copy'])
    native=specmod.parse(verified_bytes(output/'native-original-spec.reb',validated))
    original_raw=file_bytes(plan['raw_spec'])
    assert hashlib.sha256(original_raw).hexdigest()==plan['raw_spec_sha256']
    original=specmod.parse(original_raw)
    assert {k:specmod.canonical(v) for k,v in native.items()}=={k:specmod.canonical(v) for k,v in original.items()}, 'Native saved spec readback differs'
    # Verify the actual native relocation across every field, not a rebuilt
    # host approximation of selected source lists or defaults.
    moved=specmod.parse(verified_bytes(output/'generation-spec.reb',validated))
    expected_text=original_raw.decode().replace(specmod.SOURCE_ROOT,str(copy)+'/')
    expected=specmod.parse(expected_text.encode())
    assert {k:specmod.canonical(v) for k,v in moved.items()}=={k:specmod.canonical(v) for k,v in expected.items()}, 'Native spec relocation changed semantics'
    assert (output/'generator-completed.reb').is_file() and (output/'os-query-events.reb').is_file()
    actual_copy,errors=artifact_pins((copy,))
    assert not errors,errors
    assert set(actual_copy)==set(plan['initial_copy_pins'])|{str(copy/name) for name in GENERATED},'SDK copy file membership changed'
    assert all(validated.get(path)==digest for path,digest in actual_copy.items()),'SDK copy changed after capture'
    generated={}
    for path,actual in actual_copy.items():
        p=Path(path);name=str(p.relative_to(copy))
        if str(p) not in plan['initial_copy_pins'] or actual!=plan['initial_copy_pins'][str(p)]:
            assert name in GENERATED,('Unexpected vendor write',name)
            generated[name]=actual
    for name in GENERATED:assert (copy/name).is_file() and (copy/name).stat().st_size>0,('Missing SDK output',name)
    # Whole headers are retained. API layout and extension compatibility are
    # later evidence gates; merely finding expected names grants no ABI claim.
    for name in ('reb-lib.h','reb-lib-lib.h','reb-host.h','host-lib.h','reb-ext.h','ext-types.h'):
        assert (copy/'src/include'/name).is_file()
    return generated


def immutable_pin_errors(pins,copy):
    errors=[]
    for path,expected in pins.items():
        relative=Path(path).relative_to(copy) if Path(path).is_relative_to(copy) else None
        if relative is not None and str(relative) in GENERATED:continue
        try:assert sha(path)==expected,('SDK prerequisite changed',path)
        except BaseException as error:errors.append(dict(path=path,error=str(error) or type(error).__name__))
    return errors


def rewrite_owned_report(path,value,raw,identity):
    assert file_bytes(path)==raw,'Report bytes changed; preserving external edit'
    fd=os.open(path,os.O_WRONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'wb') as stream:
        held=os.fstat(stream.fileno())
        assert stat.S_ISREG(held.st_mode) and (held.st_dev,held.st_ino)==identity,'Report replaced; preserving replacement'
        raw=(json.dumps(value,indent=2)+'\n').encode()
        stream.truncate(0);stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return raw


def retain_terminal(output,copy,result,pins,*,validated,check_leases):
    command_receipt=output/'header-generation.json'
    if os.path.lexists(command_receipt):
        try:
            observed=json.loads(file_bytes(command_receipt))
            result['native_commands_started']=int(type(observed.get('pid')) is int and observed['pid']>0)
        except BaseException as error:
            result['command_receipt_error']=str(error) or type(error).__name__
            result['status']='failed-command-receipt'
    if result['native_commands_started']==0:
        startup=output/'header-generation-started.json'
        if os.path.lexists(startup):
            try:
                observed=json.loads(file_bytes(startup))
                result['native_commands_started']=int(type(observed.get('pid')) is int and observed['pid']>0)
            except BaseException as error:result['command_start_receipt_error']=str(error) or type(error).__name__
    errors=immutable_pin_errors(pins,copy)
    artifacts,artifact_errors=artifact_pins((output,copy))
    for path,expected in validated.items():
        if artifacts.get(path)!=expected:
            errors.append(dict(path=path,error='Artifact differs from validated generation bytes'))
    if result['status']=='vendor-SDK-generated-awaiting-header-and-extension-ABI-review' and artifacts!=validated:
        errors.append(dict(path='validated artifacts',error='Successful generation artifact membership changed'))
    held=False
    try:check_leases();held=True
    except BaseException as error:errors.append(dict(path='held leases',error=str(error) or type(error).__name__))
    result.update(integrity_errors=errors,artifact_pins=artifacts,artifact_errors=artifact_errors,
                  validated_artifact_pins=dict(validated),common_mutex_held=held)
    if errors:result['status']='failed-terminal-integrity'
    if artifact_errors:result['status']='failed-artifact-integrity'
    report_path=output/'report.json'
    raw,identity=new_json(report_path,result)
    expected_report=hashlib.sha256(raw).hexdigest()
    expected_closure=dict(artifacts,**{str(report_path):expected_report})
    closure={};held=False
    try:
        late_errors=immutable_pin_errors(pins,copy)
        errors.extend(late_errors)
        assert not late_errors,'SDK prerequisite changed after report write'
        closure,late_artifact_errors=artifact_pins((output,copy))
        artifact_errors.extend(late_artifact_errors)
        assert not late_artifact_errors,'SDK artifact became unreadable or nonregular'
        assert closure==expected_closure,'SDK artifact/report bytes or inventory changed after validation'
        named=report_path.lstat()
        assert (named.st_dev,named.st_ino)==identity and stat.S_ISREG(named.st_mode),'Report identity changed'
        check_leases();held=True
    except BaseException as error:
        errors.append(dict(path='final closure',error=str(error) or type(error).__name__))
        result.update(status='failed-terminal-integrity',common_mutex_held=False)
        closure={}
        try:raw=rewrite_owned_report(report_path,result,raw,identity)
        except BaseException as rewrite_error:
            errors.append(dict(path=str(report_path),error=str(rewrite_error) or type(rewrite_error).__name__))
    report_sha=expected_report
    if not closure:
        try:report_sha=sha(report_path)
        except BaseException as error:
            report_sha=None;errors.append(dict(path=str(report_path),error=str(error) or type(error).__name__))
            result['status']='failed-terminal-integrity'
    # These descriptors remain held until the terminal is written. The final
    # pathname check follows report/artifact hashing, not merely native exit.
    held=False
    try:check_leases();held=True
    except BaseException as error:
        errors.append(dict(path='held leases',error=str(error) or type(error).__name__))
        result.update(status='failed-terminal-integrity',common_mutex_held=False)
        try:
            raw=rewrite_owned_report(report_path,result,raw,identity)
            report_sha=hashlib.sha256(raw).hexdigest()
        except BaseException as rewrite_error:
            errors.append(dict(path=str(report_path),error=str(rewrite_error) or type(rewrite_error).__name__))
        closure={}
    new_json(output/'terminal.json',dict(status=result['status'],report_sha256=report_sha,
        expected_initial_report_sha256=expected_report,available_evidence_pins=closure,
        prerequisites=pins,integrity_errors=errors,artifact_errors=artifact_errors,
        command_receipt_error=result.get('command_receipt_error'),common_mutex_held=held,chart_admission=False,
        actual_command_receipt=str(command_receipt),original_source_files_preserved=not errors))
    return errors,artifact_errors


def generate(args):
    checked_runtime();raw=file_bytes(args.plan);assert hashlib.sha256(raw).hexdigest()==args.plan_sha256
    plan=json.loads(raw)
    assert plan['schema']=='rebol-retained-spec-sdk-generation-v1' and plan['controller_sha256']==sha(__file__)
    assert plan['extension_build_authorized'] is plan['chart_admission'] is plan['automatic_retry'] is False
    output=Path(plan['output']);assert not os.path.lexists(output)
    with common() as lock,ExitStack() as leases:
        opened=os.fstat(lock.fileno());held_leases=[(LOCK,lock,(opened.st_dev,opened.st_ino))]
        # Keep the original completed owners closed throughout SDK generation.
        for name in ('rebol-builder-spec-only-v1','rebol-builder-intake-v1','rebol-saved-runtime-source-intake-v1'):
            path=HOST/'continuation/owned-jobs'/name/'owner.lock'
            lease=leases.enter_context(regular_stream(path));fcntl.flock(lease,fcntl.LOCK_SH|fcntl.LOCK_NB)
            opened=os.fstat(lease.fileno());held_leases.append((path,lease,(opened.st_dev,opened.st_ino)))
        check_leases=lambda:verify_leases(held_leases)
        check_leases()
        pins=dict(plan['pins']);bind(args.plan.resolve(),args.plan_sha256,pins)
        for path,expected in pins.items():assert sha(path)==expected,('SDK preflight pin changed',path)
        copy=Path(plan['source_copy'])
        current_copy,copy_errors=artifact_pins((copy,))
        assert not copy_errors and current_copy==plan['initial_copy_pins'], 'SDK copy gained unreviewed files'
        assert not (copy/'.git').exists()
        output.mkdir(parents=True)
        result=dict(status='running-vendor-SDK-generation',native_commands_started=0,chart_admission=False,
            extension_build_executed=False,runtime_configuration_admitted=False,source_work_qualified=False,
            repeated_Builder_processes=0,repeated_runtime_queries=0,benchmark_runs=0,common_mutex_held=True)
        failure=None;validated={}
        try:
            assert plan['supervisor']==str(SUPERVISOR) and plan['timeout_seconds']==300
            assert plan['cleanup_total_timeout_seconds']==5
            supervisor=cold(SUPERVISOR,plan['supervisor_sha256'],'rebol_sdk_owned_supervisor',pins)
            command=[str(PYTHON),'-I','-S','-B','-u',str(ROOT/'tools/qualification/rebol_sdk_exec.py'),
                '--plan',str(args.plan.resolve()),'--plan-sha256',args.plan_sha256,'--common-fd',str(lock.fileno())]
            assert not any((Path(folder)/'ldd').exists() for folder in plan['environment']['PATH'].split(':'))
            result['native_commands_requested']=1
            actual=supervisor.owned_command(command,plan['environment'],output,lock.fileno(),300,
                'header-generation',copy/'make')
            validated,artifact_errors=artifact_pins((output,copy))
            assert not artifact_errors,artifact_errors
            assert json.loads(verified_bytes(output/'header-generation.json',validated))==actual['detail'], 'Owned command receipt changed'
            started=json.loads(verified_bytes(output/'generator-startup.json',validated))
            assert started['pid']==actual['detail']['pid'] and started['command']==plan['command']
            assert started['actual_cwd']==str(Path(plan['source_copy'])/'make')
            assert actual['detail']['exit_status']==actual['detail']['final_exit_status']==0
            assert not any(actual['detail'].get(k) for k in ('error','cleanup_errors'))
            reader=cold(ROOT/'tools/qualification/rebol_spec.py',pins[str(ROOT/'tools/qualification/rebol_spec.py')],'sdk_post_generation_reader',pins)
            result['generated_files']=verify_generated(plan,reader,validated)
            result.update(status='vendor-SDK-generated-awaiting-header-and-extension-ABI-review',
                native_spec_readback_verified=True,root_relocation_verified=True,
                generator_stages_completed=6,generated_headers_qualified=False,
                native_child_count_independently_observed=False)
        except BaseException as error:
            failure=error;result.update(status='stopped-unqualified',error=str(error),error_type=type(error).__name__)
            try:(output/'error.log').write_text(traceback.format_exc())
            except BaseException as logging:result['error_log_write_failure']=str(logging) or type(logging).__name__
        finally:
            previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
            try:errors,artifact_errors=retain_terminal(output,copy,result,pins,validated=validated,check_leases=check_leases)
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
        if failure is not None:raise failure
        assert not errors and not artifact_errors and not result.get('command_receipt_error'),'SDK terminal integrity failed'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_subparsers(dest='mode',required=True)
    prep=modes.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True)
    prep.add_argument('--work',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    gen=modes.add_parser('generate');gen.add_argument('--plan',type=Path,required=True);gen.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('SDK generation interrupted: '+str(signum))
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,interrupted)
    (prepare if args.mode=='prepare' else generate)(args)


if __name__=='__main__':main()
