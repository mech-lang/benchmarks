"""Sixteen fixture-only captures after the preserved linker-stage regex failure."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/qualification/rebol_primitive_fixtures_linker.py'
BASE_SHA='8e236a2e84869ac7c67ced7ac1341d0c06383a5d3da2f38353d9a15f4fec26d8'
BASE_REVIEW=dict(path=str(ROOT/'experiments/rebol/primitive-fixtures-v2/linker-invocation-v1/source-review-v1.json'),sha256='236206775ed4797a58ddc48479bb2f9cc00952020ac1ff5e99c4685b73e99a5e')
PRIOR=dict(path=str(ROOT/'experiments/rebol/primitive-fixtures-v2/linker-invocation-v1/failed-stage-review-v1.json'),sha256='631984b01ef4a492700095f1d49fc11662b117ac4155abc7b472f57a0bccf9ec')
REGEX_REVIEW=dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/source-review-v1.json'),sha256='14557b38a4b2b7ea4131b39b27646e0501d3d3515e4ebce82246a1608e5edb08')
REGEX=dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/regex.reb'),sha256='0cb030cb93f6fe521e9e4fa33635c65c8200beb62d9faa6d1007ba2237b925eb')
INTERPOSER=dict(path=str(ROOT/'experiments/rebol/primitive-fixtures-v2/linker-invocation-v1/run-v1/build/io-faults.dylib'),sha256='a5db2b9d4a6d0e99e861ac53387ac26bb2e0c09457b6a4c82ddbb63066907b73')
PACKET=ROOT/'experiments/rebol/primitive-fixtures-v2/remaining16-v1'
SUCCESS='sixteen-fixture-captures-retained-awaiting-independent-primitive-review'
SOURCE_FILES={str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),Path(__file__).with_name('test_rebol_primitive_remaining.py'),PACKET/'README.md')}

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,indent=2)+'\n').encode()

def remaining_schedule(original,e,transport,spec,intake,image,output):
    slots=original(e,transport,spec,intake,image,output)
    require(len(slots)==19 and [s['id'] for s in slots[:4]]==['compile-io-interposer','arithmetic','formatting','regex']
        and slots[-1]['id']=='pipe-injected-short-io','Exact original fixed19 order required')
    slots=slots[3:]
    require(slots[0]['command']==[str(e.RUNTIME),'-q','-s',str(ROOT/'experiments/rebol/primitive-fixtures-v1/regex.reb')],
        'Original regex invocation differs')
    slots[0]['command'][3]=REGEX['path']
    require(slots[-1]['environment']['DYLD_INSERT_LIBRARIES']==str(output/'build/io-faults.dylib'),
        'Original injected image path differs')
    slots[-1]['environment']['DYLD_INSERT_LIBRARIES']=INTERPOSER['path']
    return slots

def expected_files(f,plan):
    result=set()
    for slot in plan['schedule']:
        result.update(str(Path(slot['directory'])/name) for name in f.CAPTURE_FILES|{'transport.json'})
        result.add(str(Path(slot['input_path']).relative_to(plan['output'])))
        result.update(str(Path(path).relative_to(plan['output'])) for path in slot['sidecars'].values())
    return result

def attach(f,adapter_ref):
    old_bootstrap,old_held,old_build,old_verify,original_schedule=f.bootstrap,f.held,f.build_plan,f.verify_inputs,f.schedule
    def source_review(source_ref):
        raw=f.bootstrap_read(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Remaining source review changed');value=json.loads(raw)
        require(value['schema']=='rebol-primitive-remaining-source-review-v1'
            and value['status']=='independent-source-review-complete-native-fixtures-pending'
            and value['independent_review'] is True and set(value['files'])==SOURCE_FILES
            and value['dependencies']=={str(BASE.relative_to(ROOT)):BASE_SHA} and value['base_source_review']==BASE_REVIEW
            and value['prior_stage_review']==PRIOR and value['regex_review']==REGEX_REVIEW
            and all(value[k] is False for k in f.GATES)
            and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256'],
            'Exact remaining fixture source review required')
        return value
    def bootstrap(extension_ref,source_ref):
        review=source_review(source_ref);e,extension,_=old_bootstrap(extension_ref,BASE_REVIEW)
        return e,extension,review
    @contextmanager
    def held(extension_ref,source_ref):
        initial=source_review(source_ref)
        with old_held(extension_ref,BASE_REVIEW) as inherited:
            e,transport,inspector,common,leases,intake,extension,pins,resolutions=inherited
            current=e.document(source_ref,pins,resolutions);require(current==initial,'Remaining review changed after acquisition')
            for name,expected in current['files'].items():e.pin(pins,resolutions,ROOT/name,expected)
            prior=e.document(PRIOR,pins,resolutions);lease=prior['durable']['lease'];path=Path(lease['path'])
            require(path==Path(prior['durable']['directory'])/'owner.lock' and path not in [x[0] for x in leases],
                'Distinct closed linker-stage lease required')
            with e.regular(path) as stream:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);combined=leases+[(path,stream,(lease['device'],lease['inode']))]
                e.check_leases(combined)
                try:yield e,transport,inspector,common,combined,intake,extension,pins,resolutions
                finally:e.check_leases(combined)
    def validate_prior_linker(e,transport,inspector,pins,resolutions):
        review=e.document(PRIOR,pins,resolutions)
        require(review['schema']=='rebol-fixed19-linker-independent-failed-closure-v1'
            and review['status']=='regex-fixture-failure-preserved-owned-stage-closed'
            and review['native_attempts']==4 and review['validated_captures']==3 and review['successful_fixture_processes']==2
            and review['unstarted_fixture_processes']==15,'Exact closed linker failure required')
        plan=e.document(review['plan'],pins,resolutions);report=e.document(review['report'],pins,resolutions);terminal=e.document(review['terminal'],pins,resolutions)
        ids=['compile-io-interposer','arithmetic','formatting','regex']
        require(plan['linker_adapter']==dict(path=str(BASE),sha256=BASE_SHA) and plan['source_review']==BASE_REVIEW
            and plan['entrypoint']==str(BASE) and report['plan']==review['plan']['path'] and report['plan_sha256']==review['plan']['sha256']
            and report['status']==terminal['status']=='stopped-unqualified' and report['attempts']==ids
            and [x['id'] for x in report['registered']]==ids and [x['id'] for x in report['captures']]==ids[:3]
            and report['active'] is None and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
            and terminal['report_sha256']==terminal['expected_report_sha256']==review['report']['sha256']
            and terminal['common_mutex_held'] is True and terminal['native_processes_started']==4 and terminal['validated_captures']==3
            and all(report[k] is terminal[k] is False for k in f.GATES),'Prior linker ledger changed')
        for name,expected in report['pins'].items():
            e.pin(pins,resolutions,name,expected);require(resolutions[name]==report['input_resolutions'][name],'Prior linker named input changed')
        output=Path(plan['output']);durable=review['durable'];job=Path(durable['directory'])
        require(e.inventory(output)[0]==review['artifacts'] and e.inventory(job,('owner.lock',))[0]==durable['artifacts'],
            'Prior linker artifacts changed')
        for directory,items in ((output,review['artifacts']),(job,durable['artifacts'])):
            for name,item in items.items():e.pin(pins,resolutions,directory/name,item['sha256'])
        launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
        command=[str(e.PYTHON),'-I','-S','-B',str(BASE),'--adapter-sha256',BASE_SHA,'run','--plan',review['plan']['path'],'--plan-sha256',review['plan']['sha256']]
        require(launch['command']==started['command']==command and launch['cwd']==started['cwd']==str(ROOT)
            and ended['status']=='command-failed' and type(ended['exit_code']) is int and ended['exit_code']==1
            and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals']==[]
            and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
            and started['command_pid']==ended['command_pid']==started['command_identity']['pid']
            and started['command_identity']==ended['command_identity'],'Prior linker durable identity differs')
        spec=e.document(plan['historical_spec'],pins,resolutions);intake=e.document(plan['toolchain_intake'],pins,resolutions)
        require(plan['schedule']==original_schedule(e,transport,spec,intake,plan['extension_image'],output),
            'Prior linker schedule differs')
        for index,slot in enumerate(plan['schedule'][:3]):
            directory=output/slot['directory'];extra={}
            if index:extra={'transport.json':review['artifacts'][slot['directory']+'/transport.json']}
            observed,snapshot=f.checked_capture(e,slot,directory,started['command_pid'],inspector.kb,extra)
            saved=report['captures'][index]
            require(all(saved.get(k)==v for k,v in observed.items()) and observed['pid']==report['registered'][index]['pid'],
                'Preserved successful capture differs')
            if index:
                result=transport.check_case(slot['case'],e.read_bytes(directory/'stdout.bin'),e.read_bytes(directory/'stderr.bin'),0)
                require(result==saved['fixture_observations'],'Preserved fixture output differs')
            else:require(e.read_bytes(directory/'stdout.bin')==b'','Preserved compiler stdout differs')
        require(review['reusable_build_files']==e.inventory(output/'build')[0]
            and review['reusable_build_files']['io-faults.dylib']['sha256']==INTERPOSER['sha256']
            and INTERPOSER['path']==str(output/'build/io-faults.dylib'),'Preserved interposer differs')
        e.pin(pins,resolutions,INTERPOSER['path'],INTERPOSER['sha256'])
        failure=json.loads(e.read_bytes(output/plan['schedule'][3]['directory']/'process.json'))
        require(failure['exit_status']==1 and failure['status']=='failed' and failure['direct_child_reaped'] is True
            and failure['remaining_process_group']==failure['cleanup_errors']==[]
            and e.read_bytes(output/plan['schedule'][3]['directory']/'stderr.bin')==b'\n** User error: "Fixture mismatch: LF multiline boundary"\n\n',
            'Original regex failure differs')
        record=dict(review=PRIOR,**{k:review[k] for k in ('plan','report','terminal')},durable=durable,
            successful_stages=review['successful_stages'],successful_captures=report['captures'],interposer=INTERPOSER,
            reusable_build_files=review['reusable_build_files'])
        return record,dict(directory=str(output),artifacts=review['artifacts'])
    def schedule(e,transport,spec,intake,image,output):
        return remaining_schedule(original_schedule,e,transport,spec,intake,image,output)
    def build_plan(e,transport,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions):
        require(output.is_relative_to(PACKET) and output!=PACKET,'Remaining output must be inside its additive packet')
        prior,closure=validate_prior_linker(e,transport,inspector,pins,resolutions)
        review=e.document(REGEX_REVIEW,pins,resolutions)
        require(review['schema']=='rebol-regex-literals-independent-source-review-v1'
            and review['status']=='independent-source-review-complete-native-validation-pending' and review['independent_review'] is True
            and {k:review['files']['regex.reb'][k] for k in ('path','sha256')}==REGEX
            and all(review[k] is False for k in f.GATES),'Reviewed corrected regex fixture required')
        e.pin(pins,resolutions,REGEX['path'],REGEX['sha256'])
        helper=next(x for x in review['relative_helper_paths'] if x['source']=='regex.reb')
        require(Path(REGEX['path']).parent.joinpath(helper['file_literal'][1:]).resolve()==Path(helper['target']['path']),
            'Corrected regex common helper resolution differs')
        e.pin(pins,resolutions,helper['target']['path'],helper['target']['sha256'])
        value=old_build(e,transport,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions)
        require(len(value['schedule'])==16 and all('case' in x for x in value['schedule']),'Exactly sixteen fixture-only slots required')
        value.update(schema='rebol-primitive-remaining-plan-v1',remaining_adapter=dict(adapter_ref),entrypoint=adapter_ref['path'],
            prior_linker_stage=prior,regex_review=REGEX_REVIEW,selected_regex=REGEX,reused_interposer=INTERPOSER,
            native_processes=16,fixture_processes=16,diagnostic_compilations=0,preserved_successful_native_captures=3)
        value['prerequisite_artifact_closures'].append(closure)
        value['pins']=dict(pins);value['input_resolutions']=dict(resolutions)
        return value
    def verify_inputs(e,plan,pins,resolutions,leases):
        old_verify(e,plan,pins,resolutions,leases)
        durable=plan['prior_linker_stage']['durable']
        require(e.inventory(Path(durable['directory']),('owner.lock',))[0]==durable['artifacts'],'Prior linker durable inventory changed')
        e.check_leases(leases)
    f.bootstrap,f.held,f.schedule,f.build_plan,f.verify_inputs=bootstrap,held,schedule,build_plan,verify_inputs
    f.validate_prior_linker=validate_prior_linker;f.remaining_adapter=dict(adapter_ref);f.SUCCESS=SUCCESS
    f.expected_files=lambda plan:expected_files(f,plan)
    f.run=lambda *args:run(f,*args)
    f.finish=lambda *args:finish(f,*args)
    return f

def load_controller(expected):
    before=BASE.lstat();require(stat.S_ISREG(before.st_mode) and BASE.resolve()==BASE,'Physical regular linker controller required')
    with os.fdopen(os.open(BASE,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Linker controller replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2 and digest(raw)==BASE_SHA,'Frozen linker controller changed')
    base=types.ModuleType('remaining_linker');base.__file__=str(BASE);exec(compile(raw,str(BASE),'exec'),base.__dict__)
    f=base.load_controller(BASE_SHA);own=Path(__file__).resolve();require(digest(f.bootstrap_read(own))==expected,'Remaining adapter changed')
    return attach(f,dict(path=str(own),sha256=expected))

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();module=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];module.main()
    finally:sys.argv=previous


def finish(f, e, report, plan, output, pins, resolutions, kb, leases):
    errors=[];held=False
    available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        ids=[slot['id'] for slot in plan['schedule']]
        require(report['attempts']==ids[:len(report['attempts'])] and len(report['attempts'])<=len(ids),'Attempt prefix differs')
        require([r['id'] for r in report['registered']]==report['attempts'][:len(report['registered'])]
            and len({r['pid'] for r in report['registered']})==len(report['registered']),'Native registration differs')
        require(report['active'] is None and not artifact_errors,'Open native/artifact failure')
        for slot in plan['schedule'][:len(report['attempts'])]:
            record=json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration=next((r for r in report['registered'] if r['id']==slot['id']),None)
            require(record['cleanup_errors']==[] and not record.get('artifact_errors'),'Native cleanup failed')
            if registration:
                require(record['pid']==registration['pid'] and record['direct_child_reaped'] is True
                    and record.get('remaining_process_group',[])==record.get('remaining_after_cleanup',[])==[],'Owned child/group not closed')
            else:require(record['native_process_started'] is False,'Unregistered native process')
        require(all(available.get(name)==snapshot for name,snapshot in report['validated_files'].items()),
                'Previously validated artifact changed or disappeared')
        if report['status']==SUCCESS:
            require(len(report['attempts'])==len(report['registered'])==len(report['captures'])==len(ids)
                and set(available)==set(report['validated_files'])==expected_files(f,plan),'Incomplete fixture-only continuation')
        f.verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:report['status']='failed-integrity'
    raw=encoded(report);kb.save(output/'report.json',report);closure={}
    try:
        require(e.read_bytes(output/'report.json')==raw,'Serialized report changed')
        closure=e.inventory(output,('terminal.json',))[0]
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),'Final artifact/report inventory differs')
        f.verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0]==closure,'Output changed during final input replay')
        report_sha=e.sha(output/'report.json');require(report_sha==digest(raw),'Final report digest differs')
        e.check_leases(leases);held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={};report_sha=None
    terminal=dict(schema='rebol-primitive-remaining-terminal-v1',status=report['status'],
        report_sha256=report_sha,expected_report_sha256=digest(raw),available_evidence=closure,
        integrity_errors=errors,artifact_errors=artifact_errors,common_mutex_held=held,common_mutex_inode=79859134,
        native_processes_started=len(report['registered']),fixture_processes_started=len(report['registered']),diagnostic_compilations=0,validated_captures=len(report['captures']),
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in f.GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(encoded(terminal))
    require(not errors and not artifact_errors,'Final integrity failed; failure evidence retained')


def run(f, e, adapter, inspector, plan, plan_path, plan_sha, intake, pins, resolutions, common, leases):
    output=Path(plan['output']);kb=inspector.kb;e.pin(pins,resolutions,plan_path,plan_sha)
    f.verify_inputs(e,plan,pins,resolutions,leases);output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp','inputs'):(output/name).mkdir()
    report=dict(schema='rebol-primitive-remaining-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_files={},
        pins=pins,input_resolutions=resolutions,extension_review=plan['extension_review'],remaining_adapter=plan['remaining_adapter'],prior_linker_stage=plan['prior_linker_stage'],diagnostic_compilations=0,
        failed_sdk_producer_preserved=True,benchmark_samples=0,**{k:False for k in f.GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            payload,_=adapter.case_bytes(slot['case']);path=Path(slot['input_path'])
            with path.open('xb') as stream:stream.write(payload)
            raw,snapshot=f.exact_snapshot(e,path)
            require(raw==payload and snapshot==dict(bytes=slot['stdin_bytes'],sha256=slot['stdin_sha256']),'Prepared stdin changed')
            report['validated_files'][str(path.relative_to(output))]=snapshot
        for index,slot in enumerate(plan['schedule']):
            f.verify_inputs(e,plan,pins,resolutions,leases)
            current=e.inventory(output,('report.json',))[0]
            require(current==report['validated_files'],'Earlier artifact membership/bytes changed before next process')
            directory=output/slot['directory'];directory.mkdir()
            with kb.atomic():report['attempts'].append(slot['id']);kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid));report['active']=dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT=slot['timeout_seconds'];kb.RSS_LIMIT=slot['rss_limit_bytes'];kb.FILE_LIMIT=slot['stream_limit_bytes']
            kb.CLEANUP_TIMEOUT=5
            decoded,extra=f.observe_case(e,adapter,kb,slot,output,common,launched)
            with kb.atomic():
                report['active']=None
                capture,snapshot=f.checked_capture(e,slot,directory,os.getpid(),kb,extra)
                capture['fixture_observations']=decoded
                if report['captures']:
                    require(datetime.fromisoformat(report['captures'][-1]['finished_at'])<=datetime.fromisoformat(capture['started_at']),
                            'Native commands overlapped')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):value for name,value in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        with kb.atomic():report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():f.finish(e,report,plan,output,pins,resolutions,kb,leases)


if __name__=='__main__':main()
