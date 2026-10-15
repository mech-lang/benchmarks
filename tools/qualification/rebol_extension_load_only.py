"""One bounded load continuation; preserve the failed four-stage producer."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/extension-api-v2'
TYPED = ROOT/'tools/qualification/rebol_extension_typed_images.py'
TYPED_SHA = 'bec9d1e020cfd2449ecdd5e1dced224f6ccbf050785fd9390e3d07931d499124'
OLD_PLAN = PACKET/'plan-v1.json'
OLD_PLAN_SHA = '5bde9601a330af587834edee0a304a49239b2d970444ae1d2d2596a03fa87247'
OLD_REPORT_SHA = '085cba324d9047441a79b16387520e569f3a8069b5ecabae38782ddb10ecae65'
OLD_TERMINAL_SHA = 'df16b01164361913d71bf3f0ba776fa840c913421a61c45f12dec502892c0aad'
OLD_STDERR_SHA = '629ea1796f694bffd09311c79ec43399297fb9a5d767ed1ff24a4abc886b7d1e'
OLD_JOB = ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-extension4-v1'
OLD_LEASE = (16777232,82419599)
REUSE_REVIEW = Path('/private/tmp/mech-history-candidate-validation/rebol-extension4-independent-closure-v1.json')
REUSE_SHA = 'f45dfefcb3c6acb6ac3918b4647fe973b6fc3bb3f6f4d4100661acb05d78aa89'
ID = 'load-nine-commands-scoped-reads'
SUCCESS = 'one-load-capture-retained-awaiting-combined-independent-review'
CAPTURE_FILES = {'start.json','active.json','process.json','stdout.bin','stderr.bin'}


def require(value, message):
    if not value: raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def load_helper():
    raw=TYPED.read_bytes();require(digest(raw)==TYPED_SHA,'Typed adapter changed')
    typed=types.ModuleType('rebol_load_typed_helper');typed.__file__=str(TYPED)
    exec(compile(raw,str(TYPED),'exec'),typed.__dict__)
    return typed.load_controller(TYPED_SHA)


def secure_code(e):
    # SECURE's matcher is a case-sensitive path-prefix matcher. These are
    # read-only exceptions spelled with the two exact pinned input filenames;
    # this is not an OS sandbox or a claim of exact-filename ACL semantics.
    return 'secure ['+' '.join('%'+str(p)+' [allow read]' for p in
        (e.FIXTURES/'common.reb',e.SUPPORT/'clbg_primitives.reb'))+']'


def corrected_slot(e, old, output):
    original=old['schedule'][3]
    require(original['command']==[str(e.RUNTIME),'--quiet','--no-color',str(e.PACKET/'load-smoke.reb')]
        and original['stdin_hex']=='0080ff' and original['timeout_seconds']==30,
        'Original smoke invocation differs')
    env=e.environment(output,load=True)
    env['MECH_CLBG_REBOL_PRIMITIVES']=str(Path(old['output'])/'build/clbg_primitives.dylib')
    return dict(id=ID,directory='00-'+ID,command=original['command'][:3]+
        ['--do',secure_code(e),original['command'][3]],environment=env,
        stdin_hex=original['stdin_hex'],timeout_seconds=30)


def check_prior_metadata(e, old, report, terminal, launch, started, ended):
    require(old['controller']==str(e.ROOT/'tools/qualification/rebol_extension.py')
        and old['controller_sha256']=='8bfd7b7def7562ca810ce633dc5b92455fb29df66fc3a727641ffcc62b516493'
        and old['typed_image_adapter']==dict(path=str(TYPED),sha256=TYPED_SHA)
        and old['entrypoint']==str(TYPED),'Original implementation/adapter identity differs')
    require(report['schema']=='rebol-extension-build-layout-load-results-v1'
        and terminal['schema']=='rebol-extension-build-layout-load-terminal-v1'
        and report['status']==terminal['status']=='stopped-unqualified'
        and report['plan']==str(OLD_PLAN) and report['plan_sha256']==OLD_PLAN_SHA
        and report['attempts']==e.IDS and [r['id'] for r in report['registered']]==e.IDS
        and len({r['pid'] for r in report['registered']})==4
        and [r['id'] for r in report['captures']]==e.IDS[:3] and report['active'] is None
        and report['error']=='Native command exited unsuccessfully' and report['error_type']=='AssertionError'
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==OLD_REPORT_SHA
        and terminal['native_processes_started']==4 and terminal['validated_captures']==3
        and terminal['common_mutex_held'] is True
        and all(report[k] is terminal[k] is False for k in e.GATES),
        'Exact stopped four-stage history required')
    argv=[str(e.PYTHON),'-I','-S','-B',str(TYPED),'--adapter-sha256',TYPED_SHA,
          'run','--plan',str(OLD_PLAN),'--plan-sha256',OLD_PLAN_SHA]
    require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
        and ended['status']=='command-failed' and type(ended['exit_code']) is int and ended['exit_code']==1
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False
        and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
        and started['command_identity_observation_missing'] is False
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
        and started['command_identity']==ended['command_identity'],'Original durable failed command differs')
    return started['command_pid']


def prior_evidence(e, inspector, old, pins, resolutions):
    output=Path(old['output']);require(output==PACKET/'run-v1','Original output path differs')
    refs=dict(plan=dict(path=str(OLD_PLAN),sha256=OLD_PLAN_SHA),
        report=dict(path=str(output/'report.json'),sha256=OLD_REPORT_SHA),
        terminal=dict(path=str(output/'terminal.json'),sha256=OLD_TERMINAL_SHA))
    report=e.document(refs['report'],pins,resolutions);terminal=e.document(refs['terminal'],pins,resolutions)
    job_artifacts=e.inventory(OLD_JOB,('owner.lock',))[0]
    for name,item in job_artifacts.items():e.pin(pins,resolutions,OLD_JOB/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(OLD_JOB/name)) for name in
                         ('launch.json','command-started.json','terminal.json')]
    parent=check_prior_metadata(e,old,report,terminal,launch,started,ended)
    available=e.inventory(output,('terminal.json',))[0]
    require(available==terminal['available_evidence'],'Original terminal inventory changed')
    complete=dict(available,**{'terminal.json':dict(bytes=len(e.read_bytes(output/'terminal.json')),sha256=OLD_TERMINAL_SHA)})
    for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
    build=e.build_inventory(output,2)
    require(build==report['validated_build_artifacts'],'Successful build artifacts changed')
    reuse=e.document(dict(path=str(REUSE_REVIEW),sha256=REUSE_SHA),pins,resolutions)
    require(reuse['schema']=='rebol-extension4-independent-closure-and-prefix-review-v1'
        and reuse['status']=='closed-failed-stage-first-three-captures-reusable'
        and all(reuse[k]==v for k,v in refs.items())
        and reuse['retained_build_artifacts']==build
        and [r['id'] for r in reuse['reusable_completed_captures']]==e.IDS[:3]
        and reuse['durable_directory']==str(OLD_JOB),'Independent retained-prefix review differs')
    intake=e.document(old['toolchain_intake'],pins,resolutions)
    for index,(slot,capture) in enumerate(zip(old['schedule'][:3],report['captures'])):
        actual,snapshot=e.checked_capture(slot,output/slot['directory'],parent,inspector.kb)
        require(all(capture.get(k)==v for k,v in actual.items())
            and snapshot==report['validated_artifacts'][slot['directory']]
            and snapshot==reuse['reusable_completed_captures'][index]['capture']
            and actual['pid']==report['registered'][index]['pid'],'Original successful capture differs')
        stdout=e.read_bytes(output/slot['directory']/'stdout.bin')
        if index<2:
            stem='extension' if index==0 else 'layout'
            source=PACKET/('clbg_primitives.c' if index==0 else 'layout-probe.c')
            require(stdout==b'' and capture['actual_compiler_inputs']==
                e.validate_compile_inputs(output,stem,source,pins,resolutions),'Compiler inputs differ')
            images=[output/'build/clbg_primitives.dylib']
            if index==1:images.append(output/'build/layout-probe')
            require(capture['built_declared_image_closure']==e.built_image_closure(images,intake,inspector,pins),
                    'Compiled image closure differs')
        else:
            require(capture['native_layout_and_images']==e.validate_layout(stdout,output,intake,inspector,pins,resolutions),
                    'Retained layout/image observation differs')
    failed=json.loads(e.read_bytes(output/old['schedule'][3]['directory']/'process.json'))
    require(failed['status']=='failed' and type(failed['exit_status']) is int and failed['exit_status']==1
        and failed['error']=='Native command exited unsuccessfully' and failed['error_type']=='AssertionError'
        and failed['pid']==report['registered'][3]['pid'] and failed['identity']['ppid']==parent
        and failed['direct_child_reaped'] is True and failed['remaining_process_group']==failed.get('remaining_after_cleanup',[])==[]
        and failed['stop_signals']==failed['cleanup_errors']==[] and not failed.get('artifact_errors')
        and failed['stdout_bytes']==0 and failed['stderr_bytes']==321 and failed['stderr_sha256']==OLD_STDERR_SHA,
        'Original security failure/owned closure differs')
    require(e.sha(output/old['schedule'][3]['directory']/'stderr.bin')==OLD_STDERR_SHA,
            'Original security failure bytes changed')
    closures=old['prerequisite_artifact_closures']+[dict(directory=str(output),artifacts=complete)]
    return dict(references=refs,independent_reuse_review=dict(path=str(REUSE_REVIEW),sha256=REUSE_SHA),
        successful_capture_ids=e.IDS[:3],failed_capture_preserved=e.IDS[3],
        build_artifacts=build,durable=dict(directory=str(OLD_JOB),artifacts=job_artifacts,
            lease=dict(path=str(OLD_JOB/'owner.lock'),device=OLD_LEASE[0],inode=OLD_LEASE[1]))),closures


@contextmanager
def held(e, own_sha):
    raw=e.read_bytes(OLD_PLAN);require(digest(raw)==OLD_PLAN_SHA,'Original plan changed')
    old=json.loads(raw)
    with e.held_inputs(old['toolchain_intake']) as (common,leases,intake,pins,resolutions):
        with e.regular(OLD_JOB/'owner.lock') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            combined=leases+[(OLD_JOB/'owner.lock',stream,OLD_LEASE)]
            e.check_leases(combined)
            e.pin(pins,resolutions,OLD_PLAN,OLD_PLAN_SHA)
            for name,expected in old['pins'].items():
                e.pin(pins,resolutions,name,expected)
                require(resolutions[name]==old['input_resolutions'][name],'Original input resolution changed')
            e.pin(pins,resolutions,__file__,own_sha)
            inspector=e.load_support(pins,resolutions)
            try:yield old,common,combined,intake,pins,resolutions,inspector
            finally:e.check_leases(combined)


def build_plan(e, old, output, pins, resolutions, inspector):
    e.physical(output);require(output.is_relative_to(PACKET) and output!=PACKET
        and not os.path.lexists(output),'Fresh continuation directory required')
    prior,closures=prior_evidence(e,inspector,old,pins,resolutions)
    return dict(schema='rebol-extension-load-only-plan-v1',status='prepared-awaiting-independent-review',
        repository=str(ROOT),controller=str(Path(__file__).resolve()),controller_sha256=pins[str(Path(__file__).resolve())],
        typed_image_adapter=dict(path=str(TYPED),sha256=TYPED_SHA),output=str(output),
        toolchain_intake=old['toolchain_intake'],source_review=old['source_review'],prior=prior,
        schedule=[corrected_slot(e,old,output)],pins=dict(pins),input_resolutions=dict(resolutions),
        unavailable_inputs=old['unavailable_inputs'],prerequisite_artifact_closures=closures,
        native_processes=1,compilations=0,benchmark_samples=0,automatic_retry=False,
        process_group_rss_limit_bytes=2*1024**3,stream_limit_bytes=e.FILE_LIMIT,cleanup_timeout_seconds=5,
        common_mutex_inode=79859134,original_failed_stage_preserved=True,
        security_scope='Process-local read exceptions using the runtime path-prefix matcher for two exact pinned filename spellings; other policies unchanged.',
        **{k:False for k in e.GATES})


def verify(e, plan, pins, resolutions, leases):
    e.verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures'])
    require(e.inventory(OLD_JOB,('owner.lock',))[0]==plan['prior']['durable']['artifacts'],'Original durable inventory changed')
    e.check_leases(leases)


def finish(e, report, plan, output, pins, resolutions, kb, leases):
    errors=[];held_now=False
    available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        require(not artifact_errors and report['active'] is None,'Unclosed or unreadable continuation')
        require(report['attempts'] in ([],[ID]) and [r['id'] for r in report['registered']]==report['attempts'][:len(report['registered'])],
                'Continuation attempt/registration differs')
        if report['attempts']:
            record=json.loads(e.read_bytes(output/plan['schedule'][0]['directory']/'process.json'))
            require(record['cleanup_errors']==[] and not record.get('artifact_errors'),'Native cleanup failed')
            if report['registered']:
                require(record['pid']==report['registered'][0]['pid'] and record['direct_child_reaped'] is True
                    and record.get('remaining_process_group',[])==record.get('remaining_after_cleanup',[])==[],
                    'Continuation child/group remains')
            else:require(record['native_process_started'] is False,'Unregistered continuation child')
        for name,item in report['validated_artifacts'].items():require(available.get(name)==item,'Validated continuation capture changed')
        if report['status']==SUCCESS:
            require(len(report['captures'])==len(report['registered'])==1
                and set(available)=={str(Path(plan['schedule'][0]['directory'])/n) for n in CAPTURE_FILES},
                'Incomplete or unexpected load-only capture')
        verify(e,plan,pins,resolutions,leases)
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:report['status']='failed-integrity'
    raw=e.encoded(report);expected=e.digest(raw);kb.save(output/'report.json',report);closure={}
    try:
        closure=e.inventory(output,('terminal.json',))[0]
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=expected)}),'Initial report/capture inventory changed')
        verify(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0]==closure and e.read_bytes(output/'report.json')==raw,
                'Report/captures changed during input replay')
        e.check_leases(leases);held_now=True
    except BaseException as error:errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={}
    terminal=dict(schema='rebol-extension-load-only-terminal-v1',status=report['status'],report_sha256=expected,
        expected_report_sha256=expected,available_evidence=closure,integrity_errors=errors,artifact_errors=artifact_errors,
        common_mutex_held=held_now,common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_captures=len(report['captures']),original_failed_stage_preserved=True,
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in e.GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(e.encoded(terminal))
    require(not errors and not artifact_errors,'Continuation integrity failed; original/new failure evidence retained')


def run(e, plan, plan_path, plan_sha, pins, resolutions, inspector, common, leases):
    kb=inspector.kb;output=Path(plan['output']);slot=plan['schedule'][0]
    e.pin(pins,resolutions,plan_path,plan_sha);verify(e,plan,pins,resolutions,leases)
    output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):(output/name).mkdir()
    report=dict(schema='rebol-extension-load-only-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_artifacts={},
        original_failed_stage_preserved=True,benchmark_samples=0,**{k:False for k in e.GATES})
    kb.save(output/'report.json',report)
    try:
        directory=output/slot['directory'];directory.mkdir()
        with kb.atomic():report['attempts'].append(ID);kb.save(output/'report.json',report)
        def launched(pid):
            report['registered'].append(dict(id=ID,pid=pid));report['active']=dict(id=ID,pid=pid)
            kb.save(output/'report.json',report)
        kb.TIMEOUT=30
        kb.observe(slot['command'],slot['environment'],directory,bytes.fromhex(slot['stdin_hex']),common,launched,kind=e.KIND)
        with kb.atomic():
            report['active']=None
            capture,snapshot=e.checked_capture(slot,directory,os.getpid(),kb)
            require(e.read_bytes(directory/'stdout.bin')==e.LOAD_OUTPUT,'Nine-command smoke output differs')
            report['captures'].append(capture)
            report['validated_artifacts']={str(Path(slot['directory'])/n):v for n,v in snapshot.items()}
            report['status']=SUCCESS;kb.save(output/'report.json',report)
    except BaseException as error:
        with kb.atomic():report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():finish(e,report,plan,output,pins,resolutions,kb,leases)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--controller-sha256',required=True)
    sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    execute=sub.add_parser('run');execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();e=load_helper()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
        and Path(sys.executable).resolve()==e.PYTHON.resolve(),'Use retained Python -I -S -B')
    def stop(signum,frame):raise KeyboardInterrupt('Load-only continuation interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,stop)
    saved=None
    if args.mode=='run':
        raw=e.read_bytes(args.plan);require(e.digest(raw)==args.plan_sha256,'Continuation plan changed')
        saved=json.loads(raw);output=Path(saved['output'])
    else:output=args.output
    with held(e,args.controller_sha256) as (old,common,leases,intake,pins,resolutions,inspector):
        plan=build_plan(e,old,output,pins,resolutions,inspector);verify(e,plan,pins,resolutions,leases)
        if args.mode=='prepare':
            e.physical(args.plan);require(args.plan.is_relative_to(PACKET) and not args.plan.is_relative_to(output),'Separate packet plan required')
            raw=e.encoded(plan)
            with inspector.kb.atomic():
                with args.plan.open('xb') as stream:stream.write(raw)
                verify(e,plan,pins,resolutions,leases);require(e.read_bytes(args.plan)==raw,'Prepared plan changed')
            print(json.dumps(dict(plan=str(args.plan),sha256=e.digest(raw),native_processes_started=0)))
        else:
            require(saved==plan,'Continuation plan does not replay exactly')
            run(e,plan,args.plan,args.plan_sha256,pins,resolutions,inspector,common,leases)


if __name__=='__main__':main()
