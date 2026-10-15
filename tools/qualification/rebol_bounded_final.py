"""Eight unstarted corpus cases after a separately accepted quoted rejection."""
import argparse
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/qualification/rebol_bounded_continue.py'
BASE_SHA='abec5a85500ecd96bb7d1bcf7a049e3b607c4a070713ac64e0dc1b677719a1a0'
PRIOR_PACKET=ROOT/'experiments/rebol/bounded-v1/tree-continuation-v1'
BASE_REVIEW=dict(path=str(PRIOR_PACKET/'source-review-v1.json'),sha256='def0fde1199aa51024a034d88f6073aa8a279026226285920bd4da214313350e')
PRIOR=dict(path=str(PRIOR_PACKET/'failed-stage-review-v1.json'),sha256='4f896a02dc2b0d783fa9275337e66cb4e5717d0c6a32d8423fa5cdfeb9137da6')
PRIOR_REFS=dict(
    plan=dict(path=str(PRIOR_PACKET/'plan-v1.json'),sha256='e1957dbd7254fb0edc0457e28fc4eda93e7a9726c3915b01dd26e5a6ce86f85b'),
    report=dict(path=str(PRIOR_PACKET/'run-v1/report.json'),sha256='54f08350f865f06dc048b2ca0b0a0c1b3f5d0aed27b3892bf32bab07600a9b4f'),
    terminal=dict(path=str(PRIOR_PACKET/'run-v1/terminal.json'),sha256='fbaf693e61f0d83869b626a1cbd3aff2e5af2f2451ba2e4bb3fd1540a3104627'))
JOBS=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs'
PRIOR_JOB=JOBS/'rebol-bounded126-tree-v2'
PRELAUNCH_JOB=JOBS/'rebol-bounded126-tree-v1'
CHECKER=dict(path=str(ROOT/'tools/qualification/rebol_outputs_quoted.py'),sha256='68a0e0d9d5f1fd1a99253f495574568e98c6eabc1d084f633f7a6c225dcbddab')
CHECKER_REVIEW=dict(path=str(ROOT/'experiments/rebol/bounded-v1/quoted-rejection-v1/source-review-v1.json'),sha256='8d36ded2e0c0eabe7e82fd4007311466c7cc017b4e6966b5bc281359821605c5')
ACCEPTANCE=dict(path=str(ROOT/'experiments/rebol/bounded-v1/quoted-rejection-v1/retained-rejection-review-v1.json'),sha256='73952a6e5ed7c0823e573b601ff66eb444c0c2054ac5015850e6c080990e79f5')
PACKET=PRIOR_PACKET/'final8-v1'
SUCCESS='final8-output-contracts-retained-awaiting-independent-review'
FILES={str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),Path(__file__).with_name('test_rebol_bounded_final.py'),PACKET/'README.md')}

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def checked_source(r,source_ref,adapter_ref):
    raw=r.read_small(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Final8 source review changed')
    review=json.loads(raw)
    require(review['schema']=='rebol8-continuation-source-review-v1'
        and review['status']=='independent-source-review-complete-native-cases-pending'
        and review['independent_review'] is True and set(review['files'])==FILES
        and review['dependencies']=={str(BASE.relative_to(ROOT)):BASE_SHA,str(Path(CHECKER['path']).relative_to(ROOT)):CHECKER['sha256']}
        and review['base_source_review']==BASE_REVIEW and review['prior_stage_review']==PRIOR
        and review['checker_source_review']==CHECKER_REVIEW and review['retained_rejection_review']==ACCEPTANCE
        and review['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256']
        and all(review[k] is False for k in r.GATES),'Exact final8 source approval required')
    for name,expected in {**review['files'],**review['dependencies']}.items():
        require(digest(r.read_small(ROOT/name))==expected,'Reviewed final8 source changed')
    return review

@contextmanager
def extra_leases(e,inherited,review):
    with ExitStack() as stack:
        combined=list(inherited)
        for item,job in ((review['durable'],PRIOR_JOB),(review['failed_prelaunch'],PRELAUNCH_JOB)):
            lease=item['lease'];path=Path(lease['path'])
            require(item['directory']==str(job) and path==job/'owner.lock'
                and path not in [Path(x[0]) for x in combined]
                and all(type(lease[k]) is int for k in ('device','inode')),'Exact distinct prior lease required')
            stream=stack.enter_context(e.regular(path));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            combined.append((path,stream,(lease['device'],lease['inode'])))
        e.check_leases(combined)
        try:yield combined
        finally:e.check_leases(combined)

def prior_ledger(r,review,plan,report,terminal,primitive_ref):
    require(review['schema']=='rebol126-independent-failed-closure-v1'
        and review['status']=='revcomp-diagnostic-mismatch-preserved-owned-stage-closed'
        and review['independent_review'] is True
        and all(type(review[k]) is int and review[k]==v for k,v in dict(attempted_cases=118,
            successful_output_contracts=117,failed_cases=1,unstarted_cases=8,benchmark_samples=0).items())
        and review['references']==dict(PRIOR_REFS,primitive_review=primitive_ref,source_review=BASE_REVIEW)
        and all(review[k] is False for k in r.GATES),'Exact failed126 independent closure required')
    ids=[s['id'] for s in plan['schedule']]
    require(plan['schema']=='rebol126-bounded-plan-v1' and plan['repository']==str(ROOT)
        and plan['continuation_adapter']==dict(path=str(BASE),sha256=BASE_SHA) and plan['entrypoint']==str(BASE)
        and plan['source_review']==BASE_REVIEW and plan['primitive_review']==primitive_ref
        and plan['output']==str(PRIOR_PACKET/'run-v1') and len(ids)==126
        and ids[117]=='revcomp:extended-invalid-space'
        and report['schema']=='rebol126-bounded-results-v1' and terminal['schema']=='rebol126-bounded-terminal-v1'
        and report['status']==terminal['status']=='stopped-unqualified'
        and report['plan']==PRIOR_REFS['plan']['path'] and report['plan_sha256']==PRIOR_REFS['plan']['sha256']
        and report['attempts']==ids[:118] and [x['id'] for x in report['registered']]==ids[:118]
        and len({x['pid'] for x in report['registered']})==118
        and [x['id'] for x in report['captures']]==ids[:117] and report['active'] is None
        and report['error']=='Rebol user-error diagnostic differs' and report['error_type']=='ValueError'
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and report['pins']==dict(plan['pins'],**{PRIOR_REFS['plan']['path']:PRIOR_REFS['plan']['sha256']})
        and report['input_resolutions']==dict(plan['input_resolutions'],**{PRIOR_REFS['plan']['path']:PRIOR_REFS['plan']['path']})
        and terminal['report_sha256']==terminal['expected_report_sha256']==PRIOR_REFS['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==118
        and terminal['validated_cases']==117 and report['preserved_successful_cases']==terminal['preserved_successful_cases']==23
        and report['prior_bounded_stage']==plan['prior_bounded_stage']==review['prior_bounded_stage']
        and all(report[k] is terminal[k] is plan[k] is False for k in r.GATES),'Failed126 producer ledger differs')

def closed_jobs(e,review,pins,resolutions):
    current=review['durable'];job=Path(current['directory'])
    require(job==PRIOR_JOB and e.inventory(job,('owner.lock',))[0]==current['artifacts']
        and set(current['artifacts'])=={'launch.json','command-started.json','terminal.json','request.json',
            'worker-started.json','command.stdout','command.stderr','worker.log'},'Prior126 durable inventory differs')
    for name,item in current['artifacts'].items():e.pin(pins,resolutions,job/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(BASE),'--adapter-sha256',BASE_SHA,'run',
        '--plan',PRIOR_REFS['plan']['path'],'--plan-sha256',PRIOR_REFS['plan']['sha256']]
    require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
        and ended['status']=='command-failed' and type(ended['exit_code']) is int and ended['exit_code']==1
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals']==[]
        and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
        and started['command_identity']==ended['command_identity'],'Prior126 durable identity differs')
    failed=review['failed_prelaunch'];path=Path(failed['directory'])
    require(path==PRELAUNCH_JOB and failed['status']=='sandbox-ps-error-before-worker-identity-and-target-handshake'
        and failed['target_command_started'] is failed['birth_identity_recorded'] is False
        and failed['process_absence_not_claimed_without_identity'] is True
        and set(failed['artifacts'])=={'owner.lock','request.json','worker.log'}
        and e.inventory(path)[0]==failed['artifacts'],'Exact prelaunch failure provenance required')
    for name,item in failed['artifacts'].items():e.pin(pins,resolutions,path/name,item['sha256'])
    return started['command_pid'],current,dict(directory=str(path),artifacts=failed['artifacts'])

def acceptance(r,e,checker,approval,slot,capture,snapshot,review):
    require(approval['schema']=='rebol-retained-quoted-rejection-review-v1'
        and approval['status']=='exact-retained-revcomp-rejection-qualified' and approval['independent_review'] is True
        and approval['references']==dict(PRIOR_REFS,checker=CHECKER,source_review=CHECKER_REVIEW,failed_stage_review=PRIOR)
        and approval['case_id']==slot['id']=='revcomp:extended-invalid-space'
        and approval['slot']==slot and approval['case']==slot['case']
        and approval['capture_directory']==review['failed_capture']['capture_directory']
        and approval['capture_files']==snapshot==review['failed_capture']['capture_files']
        and approval['output_validation']==capture['output_validation']
        and approval['observer_status']==capture['observer_status']=='failed'
        and approval['producer_status']=='stopped-unqualified' and approval['rejection_qualified'] is True
        and all(approval[k] is False for k in r.GATES),'Exact independent retained rejection acceptance required')

def final_schedule(slots):
    require(len(slots)==126 and slots[117]['id']=='revcomp:extended-invalid-space','Original126 schedule differs')
    final=slots[118:]
    require(len(final)==8 and len({s['id'] for s in final})==8
        and sum(s['expected_exit']==1 for s in final)==6
        and [s['id'] for s in final[-2:]]==['mandelbrot:n-0','fannkuchredux:n-0']
        and all(s['expected_exit']==0 for s in final[-2:]),'Exact final8 corpus suffix required')
    return final

def attach(r,adapter_ref):
    old_held,old_build=r.held,r.build_plan
    @contextmanager
    def held(primitive_ref,source_ref):
        initial=checked_source(r,source_ref,adapter_ref)
        with old_held(primitive_ref,BASE_REVIEW) as inherited:
            p,e,transport,old_checker,inspector,common,leases,intake,extension,review,pins,resolutions=inherited
            current=e.document(source_ref,pins,resolutions);require(current==initial,'Final8 approval changed after locking')
            for name,expected in {**current['files'],**current['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,expected)
            source=e.document(CHECKER_REVIEW,pins,resolutions)
            require(source['schema']=='rebol-quoted-rejection-checker-source-review-v1'
                and source['status']=='independent-source-review-complete'
                and source['independent_review'] is True and all(source[k] is False for k in r.GATES),
                'Independent quoted checker source approval required')
            for name,expected in {**source['files'],**source['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,expected)
            for ref in source['formatting_sources']:e.pin(pins,resolutions,ref['path'],ref['sha256'])
            require(pins[CHECKER['path']]==CHECKER['sha256'],'Quoted checker approval differs')
            raw=e.read_bytes(CHECKER['path']);require(digest(raw)==CHECKER['sha256'],'Quoted checker changed')
            checker=r.load(raw,Path(CHECKER['path']),'rebol_final8_quoted_checker')
            prior=e.document(PRIOR,pins,resolutions);e.document(ACCEPTANCE,pins,resolutions)
            with extra_leases(e,leases,prior) as combined:
                yield p,e,transport,checker,inspector,common,combined,intake,extension,review,pins,resolutions

    def validate_prior(e,kb,checker,primitive_ref,pins,resolutions):
        review=e.document(PRIOR,pins,resolutions)
        plan,report,terminal=[e.document(PRIOR_REFS[name],pins,resolutions) for name in ('plan','report','terminal')]
        prior_ledger(r,review,plan,report,terminal,primitive_ref)
        for name,expected in report['pins'].items():
            e.pin(pins,resolutions,name,expected);require(resolutions[name]==report['input_resolutions'][name],'Prior named input changed')
        output=Path(plan['output']);complete=e.inventory(output)[0]
        require(complete==review['artifacts'] and len(complete)==592,'Exact failed126 output inventory required')
        for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
        parent,durable,prelaunch=closed_jobs(e,review,pins,resolutions)
        cases=r.corpus(e,pins,resolutions);spec=e.document(plan['historical_spec'],pins,resolutions)
        mapping=e.document(dict(path=str(r.ORIGINAL/'bounded-corpus-map.json'),sha256=spec['fixture_source_pins']['bounded-corpus-map.json']),pins,resolutions)
        selected=r.source_selection(e,spec,mapping,cases,pins,resolutions)
        require(selected==plan['sources'] and r.schedule(e,checker,cases,selected,plan['extension_image'],output,plan['limits'])==plan['schedule'],
            'Prior126 sources or schedule changed')
        previous=plan['prior_bounded_stage']['report_finished_at'];validated={};accepted=None
        for index,slot in enumerate(plan['schedule'][:118]):
            directory=output/slot['directory'];capture,snapshot=r.checked_case(e,kb,checker,slot,directory,parent)
            require(capture['pid']==report['registered'][index]['pid'] and r.stamp(previous)<=r.stamp(capture['started_at']),
                'Prior126 capture identity or serial order differs')
            previous=capture['finished_at']
            if index<117:
                require(capture==report['captures'][index],'Preserved successful126 output differs')
                validated.update({str(Path(slot['directory'])/name):item for name,item in snapshot.items()})
            else:
                approval=e.document(ACCEPTANCE,pins,resolutions)
                acceptance(r,e,checker,approval,slot,capture,snapshot,review);accepted=capture
        require(validated==report['validated_files'] and all(not os.path.lexists(output/s['directory']) for s in plan['schedule'][118:]),
            'Prior126 validated prefix or unstarted suffix differs')
        expected={str(Path(s['directory'])/name) for s in plan['schedule'][:118] for name in r.CAPTURE_FILES}
        require(set(e.inventory(output,('report.json','terminal.json'))[0])==expected
            and e.inventory(output,('report.json','terminal.json'))[0]==report['artifacts']
            and e.inventory(output,('terminal.json',))[0]==terminal['available_evidence']
            and e.inventory(output)[0]==complete,'Prior126 terminal artifact closure differs')
        record=dict(review=PRIOR,references=PRIOR_REFS,durable=durable,failed_prelaunch=review['failed_prelaunch'],
            original_preserved_successes=23,current_preserved_successes=117,accepted_rejection=ACCEPTANCE,
            accepted_capture=accepted,preserved_successful_cases=141,report_finished_at=report['finished_at'])
        return record,[dict(directory=str(output),artifacts=complete),prelaunch],plan

    def build_plan(p,e,transport,checker,inspector,output,primitive_ref,source_ref,intake,extension,review,pins,resolutions):
        require(output.is_relative_to(PACKET) and output!=PACKET,'Fresh final8 packet output required')
        # Keep the current126 constructor's full149 coverage assertion intact.
        value=old_build(p,e,transport,checker,inspector,output,primitive_ref,BASE_REVIEW,intake,extension,review,pins,resolutions)
        prior,closures,old_plan=r.validate_prior_continuation(e,inspector.kb,checker,primitive_ref,pins,resolutions)
        require(value['sources']==old_plan['sources'] and value['extension_image']==old_plan['extension_image']
            and value['prerequisite_artifact_closures']==old_plan['prerequisite_artifact_closures']
            and value['prior_durable_jobs']==old_plan['prior_durable_jobs']
            and value['prior_bounded_stage']==old_plan['prior_bounded_stage'],'Prior126 prerequisites changed')
        value.update(schema='rebol8-bounded-plan-v1',source_review=source_ref,continuation_source_review=BASE_REVIEW,
            final_adapter=dict(adapter_ref),entrypoint=adapter_ref['path'],quoted_checker=CHECKER,checker_source_review=CHECKER_REVIEW,
            retained_rejection_review=ACCEPTANCE,prior_continuation_stage=prior,schedule=final_schedule(value['schedule']),
            native_processes=8,success_cases=2,rejection_cases=6,preserved_successful_cases=141,
            preserved_actual_attempts=142,prior_failed_producer_attempts=2)
        value['prerequisite_artifact_closures'].extend(closures)
        value['prior_durable_jobs'].append(dict(directory=prior['durable']['directory'],artifacts=prior['durable']['artifacts']))
        value['pins']=dict(pins);value['input_resolutions']=dict(resolutions)
        return value
    r.held,r.build_plan=held,build_plan
    r.validate_prior_continuation=validate_prior;r.final_adapter=dict(adapter_ref);r.SUCCESS=SUCCESS
    r.run=lambda *args:run(r,*args);r.finish=lambda *args:finish(r,*args)
    return r

def load_controller(expected):
    before=BASE.lstat();require(stat.S_ISREG(before.st_mode) and BASE.resolve()==BASE,'Physical regular continuation required')
    with os.fdopen(os.open(BASE,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Continuation replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2 and digest(raw)==BASE_SHA,'Frozen126 continuation changed')
    base=types.ModuleType('rebol_final8_base');base.__file__=str(BASE);exec(compile(raw,str(BASE),'exec'),base.__dict__)
    r=base.load_controller(BASE_SHA);own=Path(__file__).resolve()
    require(r.read_small(BASE)==raw and digest(r.read_small(own))==expected,'Final8 adapter identity changed')
    return attach(r,dict(path=str(own),sha256=expected))

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();r=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];r.main()
    finally:sys.argv=previous

# The two small lifecycle functions below preserve the frozen observation path.

def finish(r,e,kb,report,plan,output,pins,resolutions,leases):
    errors=[];held=False;available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        ids=[s['id'] for s in plan['schedule']]
        require(len(ids)==8 and report['attempts']==ids[:len(report['attempts'])] and len(report['attempts'])<=8,'Attempt prefix differs')
        require([x['id'] for x in report['registered']]==report['attempts'][:len(report['registered'])]
            and len({x['pid'] for x in report['registered']})==len(report['registered']) and report['active'] is None,'Registered prefix differs')
        for slot in plan['schedule'][:len(report['attempts'])]:
            raw=json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration=next((x for x in report['registered'] if x['id']==slot['id']),None)
            require(raw['cleanup_errors']==[] and not raw.get('artifact_errors'),'Native cleanup failed')
            if registration:require(raw['pid']==registration['pid'] and raw['direct_child_reaped'] is True
                and raw.get('remaining_process_group',[])==raw.get('remaining_after_cleanup',[])==[],'Owned group not closed')
            else:require(raw['native_process_started'] is False,'Unregistered native process')
        require(all(available.get(name)==value for name,value in report['validated_files'].items()),'Validated artifact changed')
        if report['status']==SUCCESS:
            expected={str(Path(s['directory'])/name) for s in plan['schedule'] for name in r.CAPTURE_FILES}
            require(len(report['attempts'])==len(report['registered'])==len(report['captures'])==8
                and [x['id'] for x in report['captures']]==ids
                and sum(x['expected_rejection'] for x in report['captures'])==6
                and set(available)==set(report['validated_files'])==expected,'Complete8 evidence required')
        r.verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:report['status']='failed-integrity'
    raw=r.encoded(report);kb.save(output/'report.json',report);closure={};report_sha=None
    try:
        require(e.read_bytes(output/'report.json')==raw,'Serialized report changed')
        closure=e.inventory(output,('terminal.json',))[0]
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),'Final inventory differs')
        r.verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0]==closure,'Output changed during final input replay')
        report_sha=e.sha(output/'report.json');require(report_sha==digest(raw),'Final report changed')
        e.check_leases(leases);held=True
    except BaseException as error:errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={};report_sha=None
    terminal=dict(schema='rebol8-bounded-terminal-v1',status=report['status'],report_sha256=report_sha,
        expected_report_sha256=digest(raw),available_evidence=closure,integrity_errors=errors,artifact_errors=artifact_errors,
        common_mutex_held=held,common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_cases=len(report['captures']),preserved_successful_cases=141,
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in r.GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(r.encoded(terminal))
    require(not errors and not artifact_errors,'Final integrity failed; evidence retained')

def run(r,e,kb,checker,plan,plan_path,plan_sha,pins,resolutions,common,leases):
    output=Path(plan['output']);e.pin(pins,resolutions,plan_path,plan_sha)
    r.verify_inputs(e,plan,pins,resolutions,leases);output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):(output/name).mkdir()
    report=dict(schema='rebol8-bounded-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_files={},pins=pins,
        input_resolutions=resolutions,primitive_review=plan['primitive_review'],final_adapter=plan['final_adapter'],
        prior_continuation_stage=plan['prior_continuation_stage'],preserved_successful_cases=141,benchmark_samples=0,**{k:False for k in r.GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            r.verify_inputs(e,plan,pins,resolutions,leases)
            require(e.inventory(output,('report.json',))[0]==report['validated_files'],'Earlier artifacts changed')
            payload=e.read_bytes(r.CORPUS.parent/slot['case']['stdin']['path'])
            require(len(payload)==slot['stdin_bytes'] and digest(payload)==slot['stdin_sha256'],'Case input changed')
            directory=output/slot['directory'];directory.mkdir()
            with kb.atomic():report['attempts'].append(slot['id']);kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid));report['active']=dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT=slot['timeout_seconds'];kb.CLEANUP_TIMEOUT=5
            kb.RSS_LIMIT=slot['rss_limit_bytes'];kb.FILE_LIMIT=slot['stream_limit_bytes']
            try:kb.observe(slot['command'],slot['environment'],directory,payload,common,launched,kind=r.KIND)
            except AssertionError as error:
                if not slot['expected_exit'] or str(error)!='Native command exited unsuccessfully':raise
            with kb.atomic():
                report['active']=None
                capture,snapshot=r.checked_case(e,kb,checker,slot,directory,os.getpid())
                previous=report['captures'][-1]['finished_at'] if report['captures'] else plan['prior_continuation_stage']['report_finished_at']
                require(r.stamp(previous)<=r.stamp(capture['started_at']),'Overlapping prior or remaining cases')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):item for name,item in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        with kb.atomic():report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():r.finish(e,kb,report,plan,output,pins,resolutions,leases)

if __name__=='__main__':main()
