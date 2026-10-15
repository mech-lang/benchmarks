"""Remaining 126 shared-corpus captures after the preserved tree-leaf failure.

The original 23 successful captures remain separate evidence. This entrypoint
changes tree source selection and the continuation ledger, not native policy.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/qualification/rebol_bounded_remaining.py'
BASE_SHA='4b620fdd96d789ba02b119a700c7028fa1f8b84cc2bd83dcd1d88ff494db40f4'
PRIMITIVE_SHA='f28c9bbb5ed9a47bf6bd2d912e031312038228b6092e451e58a4e364332a7a4b'
BASE_PACKET=ROOT/'experiments/rebol/bounded-v1/remaining-intake-v1'
BASE_REVIEW=dict(path=str(BASE_PACKET/'source-review-v1.json'),sha256='5714e8949018b6fb725c3c2326f3dd90179bfb5734660b149484c0402010e9a1')
PRIOR=dict(path=str(BASE_PACKET/'failed-stage-review-v1.json'),sha256='1dcf3e89ebf098d4702c654c4e8d155c0208aabf1010587f0ee31e519a284e60')
PRIOR_REFS=dict(
    plan=dict(path=str(BASE_PACKET/'plan-v1.json'),sha256='b954c0590470a03c188e7addd44568a2df319a30212568d628b1f35d54577dff'),
    report=dict(path=str(BASE_PACKET/'run-v1/report.json'),sha256='e5721c895f5539923c52a87aa5160293ce6d1368a866b1244de5e7e6f73f0a1c'),
    terminal=dict(path=str(BASE_PACKET/'run-v1/terminal.json'),sha256='1980b4ba564115ba83f85993fbd486372a64a0a44016ce711c97a0ab7df2070c'))
PRIOR_JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-bounded149-remaining-v1'
TREE=dict(path=str(ROOT/'experiments/rebol/tree-leaves-v1/main.reb'),sha256='128df2a9e4c9d5d5be798b07d8ff0ab967c5969ee38746de9c7ee635502574ef')
TREE_REVIEW=dict(path=str(ROOT/'experiments/rebol/tree-leaves-v1/source-review-v1.json'),sha256='6e29eb3605990bf09b26ccc92fe0c65e1917aa265e6d4d2ea0a5af1108c7a9ce')
PACKET=ROOT/'experiments/rebol/bounded-v1/tree-continuation-v1'
SUCCESS='remaining126-output-contracts-retained-awaiting-independent-review'
SOURCE_FILES={str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),
    Path(__file__).with_name('test_rebol_bounded_continue.py'),PACKET/'README.md',Path(TREE['path']),Path(TREE_REVIEW['path']))}

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def checked_source_review(r,source_ref,adapter_ref):
    raw=r.read_small(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Continuation source review changed')
    value=json.loads(raw)
    require(value['schema']=='rebol126-continuation-source-review-v1'
        and value['status']=='independent-source-review-complete-native-cases-pending'
        and value['independent_review'] is True and set(value['files'])==SOURCE_FILES
        and value['dependencies']=={str(BASE.relative_to(ROOT)):BASE_SHA}
        and value['base_source_review']==BASE_REVIEW and value['prior_stage_review']==PRIOR
        and value['tree_source_review']==TREE_REVIEW and all(value[k] is False for k in r.GATES)
        and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256']
        and value['files'][str(Path(TREE['path']).relative_to(ROOT))]==TREE['sha256']
        and value['files'][str(Path(TREE_REVIEW['path']).relative_to(ROOT))]==TREE_REVIEW['sha256'],
        'Exact continuation source approval required')
    for name,expected in {**value['files'],**value['dependencies']}.items():
        require(digest(r.read_small(ROOT/name))==expected,'Continuation source dependency changed: '+name)
    return value

def select_tree(r,original,e,spec,mapping,cases,pins,resolutions):
    selected=original(e,spec,mapping,cases,pins,resolutions)
    review=e.document(TREE_REVIEW,pins,resolutions)
    require(review['schema']=='rebol-tree-leaves-independent-source-review-v1'
        and review['status']=='independent-source-review-complete-native-validation-pending'
        and review['independent_review'] is True
        and {k:review['files']['main.reb'][k] for k in ('path','sha256')}==TREE
        and {k:review['retained_failure']['review'][k] for k in ('path','sha256')}==PRIOR
        and all(review[k] is False for k in r.GATES),'Exact corrected tree source review required')
    old=selected['binarytrees'];prior=review['original_sources']['original_main']
    require(old['path']==old['historical_path']==prior['path']
        and old['sha256']==old['historical_sha256']==prior['sha256'] and old['substitution'] is None,
        'Original tree source association differs')
    e.pin(pins,resolutions,TREE['path'],TREE['sha256'])
    helpers=[x for x in review['relative_helper_paths'] if x['source']=='main.reb']
    target=ROOT/'archive/languages/rebol/20261013/drafts/private-v1/support/clbg_io.reb'
    require(len(helpers)==1 and helpers[0]['target']['path']==str(target)
        and helpers[0]['file_literal'].startswith('%')
        and (Path(TREE['path']).parent/helpers[0]['file_literal'][1:]).resolve(strict=True)==target,
        'Corrected tree IO helper differs')
    e.pin(pins,resolutions,target,helpers[0]['target']['sha256'])
    selected['binarytrees']=dict(old,**TREE,substitution='evaluated-none-tree-leaves')
    return selected

def remaining_schedule(original,*args):
    slots=original(*args)
    require(len(slots)==149 and len({s['id'] for s in slots})==149
        and slots[23]['id']=='binarytrees:n-0' and all(s['expected_exit']==0 for s in slots[:23]),
        'Original shared149 prefix differs')
    remaining=slots[23:]
    require(len(remaining)==126 and sum(s['expected_exit']==0 for s in remaining)==119
        and sum(s['expected_exit']==1 for s in remaining)==7,'Exact remaining126 cases required')
    return remaining

def durable_inputs(e,review,pins,resolutions):
    durable=review['durable'];job=Path(durable['directory'])
    require(job==PRIOR_JOB and durable['lease']['path']==str(job/'owner.lock'),'Exact prior bounded job required')
    artifacts=e.inventory(job,('owner.lock',))[0]
    require(artifacts==durable['artifacts'] and set(artifacts)=={
        'launch.json','command-started.json','terminal.json','request.json','worker-started.json',
        'command.stdout','command.stderr','worker.log'},'Prior bounded durable inventory differs')
    for name,item in artifacts.items():e.pin(pins,resolutions,job/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(BASE),'--adapter-sha256',BASE_SHA,
        '--primitive-adapter-sha256',PRIMITIVE_SHA,'run','--plan',PRIOR_REFS['plan']['path'],
        '--plan-sha256',PRIOR_REFS['plan']['sha256']]
    require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
        and ended['status']=='command-failed' and type(ended['exit_code']) is int and ended['exit_code']==1
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals']==[]
        and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
        and started['command_identity']==ended['command_identity'],'Prior bounded durable identity differs')
    return started['command_pid'],durable

def prior_ledger(r,review,plan,report,terminal,primitive_ref):
    counts=dict(attempted_cases=24,successful_output_contracts=23,failed_cases=1,unstarted_cases=125,benchmark_samples=0)
    require(review['schema']=='rebol149-remaining-independent-failed-closure-v1'
        and review['status']=='binarytrees-main-failure-preserved-owned-stage-closed'
        and review['independent_review'] is True and all(type(review[k]) is int and review[k]==v for k,v in counts.items())
        and all(review[k] is False for k in r.GATES),'Exact failed shared149 closure required')
    require(review['references']==dict(PRIOR_REFS,primitive_review=primitive_ref,source_review=BASE_REVIEW)
        and plan['schema']=='rebol149-bounded-plan-v1' and plan['repository']==str(ROOT)
        and plan['controller']==str(Path(r.__file__)) and plan['controller_sha256']==r.digest(r.read_small(r.__file__))
        and plan['intake_adapter']==dict(path=str(BASE),sha256=BASE_SHA)
        and plan['primitive_intake_adapter']==dict(path=str(ROOT/'tools/qualification/rebol_primitive_remaining.py'),sha256=PRIMITIVE_SHA)
        and plan['entrypoint']==str(BASE) and plan['source_review']==BASE_REVIEW and plan['primitive_review']==primitive_ref
        and plan['output']==str(BASE_PACKET/'run-v1'),'Prior bounded plan identity differs')
    ids=[s['id'] for s in plan['schedule']]
    require(len(ids)==149 and ids[23]=='binarytrees:n-0'
        and report['schema']=='rebol149-bounded-results-v1' and terminal['schema']=='rebol149-bounded-terminal-v1'
        and report['status']==terminal['status']=='stopped-unqualified'
        and report['plan']==PRIOR_REFS['plan']['path'] and report['plan_sha256']==PRIOR_REFS['plan']['sha256']
        and report['attempts']==ids[:24] and [x['id'] for x in report['registered']]==ids[:24]
        and len({x['pid'] for x in report['registered']})==24
        and [x['id'] for x in report['captures']]==ids[:23] and report['active'] is None
        and report['error']=='Native command exited unsuccessfully' and report['error_type']=='AssertionError'
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==PRIOR_REFS['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==24 and terminal['validated_cases']==23
        and all(report[k] is terminal[k] is plan[k] is False for k in r.GATES)
        and report['pins']==dict(plan['pins'],**{PRIOR_REFS['plan']['path']:PRIOR_REFS['plan']['sha256']})
        and report['input_resolutions']==dict(plan['input_resolutions'],**{PRIOR_REFS['plan']['path']:PRIOR_REFS['plan']['path']}),
        'Prior bounded failure ledger differs')

@contextmanager
def extra_lease(e,inherited,review):
    lease=review['durable']['lease'];path=Path(lease['path'])
    require(Path(review['durable']['directory'])==PRIOR_JOB and path==PRIOR_JOB/'owner.lock'
        and path not in [Path(x[0]) for x in inherited]
        and all(type(lease[k]) is int for k in ('device','inode')),'Distinct prior bounded lease required')
    with e.regular(path) as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        combined=inherited+[(path,stream,(lease['device'],lease['inode']))]
        e.check_leases(combined)
        try:yield combined
        finally:e.check_leases(combined)

def attach(r,adapter_ref):
    old_held,old_build,old_source,old_schedule=r.held,r.build_plan,r.source_selection,r.schedule
    @contextmanager
    def held(primitive_ref,source_ref):
        initial=checked_source_review(r,source_ref,adapter_ref)
        with old_held(primitive_ref,BASE_REVIEW) as inherited:
            p,e,transport,checker,inspector,common,leases,intake,extension,review,pins,resolutions=inherited
            current=e.document(source_ref,pins,resolutions);require(current==initial,'Continuation approval changed after lock acquisition')
            for name,expected in {**current['files'],**current['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,expected)
            prior=e.document(PRIOR,pins,resolutions)
            with extra_lease(e,leases,prior) as combined:
                yield p,e,transport,checker,inspector,common,combined,intake,extension,review,pins,resolutions
    def validate_prior(e,kb,checker,primitive_ref,pins,resolutions):
        review=e.document(PRIOR,pins,resolutions)
        plan,report,terminal=[e.document(PRIOR_REFS[name],pins,resolutions) for name in ('plan','report','terminal')]
        prior_ledger(r,review,plan,report,terminal,primitive_ref)
        for name,expected in report['pins'].items():
            e.pin(pins,resolutions,name,expected)
            require(resolutions[name]==report['input_resolutions'][name],'Prior bounded named input changed')
        output=Path(plan['output']);complete=e.inventory(output)[0]
        require(complete==review['artifacts'] and len(complete)==122,'Prior bounded complete inventory differs')
        for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
        parent,durable=durable_inputs(e,review,pins,resolutions)
        cases=r.corpus(e,pins,resolutions);spec=e.document(plan['historical_spec'],pins,resolutions)
        mapping=e.document(dict(path=str(r.ORIGINAL/'bounded-corpus-map.json'),sha256=spec['fixture_source_pins']['bounded-corpus-map.json']),pins,resolutions)
        selected=old_source(e,spec,mapping,cases,pins,resolutions)
        require(selected==plan['sources'] and plan['schedule']==old_schedule(e,checker,cases,selected,plan['extension_image'],output,plan['limits']),
            'Prior bounded source selection or schedule differs')
        previous=None;validated={}
        for index,slot in enumerate(plan['schedule'][:24]):
            directory=output/slot['directory']
            if index<23:
                capture,snapshot=r.checked_case(e,kb,checker,slot,directory,parent)
                require(capture==report['captures'][index],'Preserved successful output contract differs')
                validated.update({str(Path(slot['directory'])/name):item for name,item in snapshot.items()})
                final=json.loads(e.read_bytes(directory/'process.json'))
                saved=review['successful_captures'][index]
            else:
                require(slot['expected_exit']==0,'Original failed tree was not a planned success')
                final,streams,snapshot=r.native_capture(e,kb,dict(slot,expected_exit=1),directory,parent)
                require(streams[0]==b'' and len(streams[1])==345
                    and digest(streams[1])=='d7bb1700b0fa18ab1d2ed28923f76fbcadff31f1d61c2c51dec2fe5559665b78',
                    'Original tree word-leaf failure differs')
                saved=review['failed_capture']
            require(saved==dict(id=slot['id'],pid=final['pid'],exit_status=final['exit_status'],
                started_at=final['started_at'],finished_at=final['finished_at'],identity=final['identity'],
                capture_directory=str(directory),capture_files=snapshot,output_contract_passed=index<23)
                and final['pid']==report['registered'][index]['pid'],'Prior independent capture join differs')
            if previous is not None:require(previous<=r.stamp(final['started_at']),'Prior bounded cases overlap')
            previous=r.stamp(final['finished_at'])
        require(len(review['successful_captures'])==23 and validated==report['validated_files']
            and all(not os.path.lexists(output/slot['directory']) for slot in plan['schedule'][24:]),
            'Prior validated prefix or unstarted suffix differs')
        expected={str(Path(slot['directory'])/name) for slot in plan['schedule'][:24] for name in r.CAPTURE_FILES}
        artifacts=e.inventory(output,('report.json','terminal.json'))[0]
        require(set(artifacts)==expected and artifacts==report['artifacts']
            and e.inventory(output,('terminal.json',))[0]==terminal['available_evidence']
            and e.inventory(output)[0]==complete,'Prior bounded report/artifact closure differs')
        record=dict(review=PRIOR,references=PRIOR_REFS,durable=durable,successful_captures=report['captures'],
            failed_case='binarytrees:n-0',attempted_cases=24,successful_output_contracts=23,unstarted_cases=125,
            report_finished_at=report['finished_at'])
        return record,dict(directory=str(output),artifacts=complete),plan
    def build_plan(p,e,transport,checker,inspector,output,primitive_ref,source_ref,intake,extension,review,pins,resolutions):
        require(output.is_relative_to(PACKET) and output!=PACKET,'Fresh output must be inside continuation packet')
        prior,closure,prior_plan=validate_prior(e,inspector.kb,checker,primitive_ref,pins,resolutions)
        value=old_build(p,e,transport,checker,inspector,output,primitive_ref,source_ref,intake,extension,review,pins,resolutions)
        require(value['prerequisite_artifact_closures']==prior_plan['prerequisite_artifact_closures']
            and value['prior_durable_jobs']==prior_plan['prior_durable_jobs']
            and value['extension_image']==prior_plan['extension_image'],'Bounded prerequisite closure changed')
        require([x['id'] for x in prior['successful_captures']]+[s['id'] for s in value['schedule']]
            ==[s['id'] for s in prior_plan['schedule']],'Preserved and remaining cases do not cover shared149 exactly')
        value.update(schema='rebol126-bounded-plan-v1',continuation_adapter=dict(adapter_ref),entrypoint=adapter_ref['path'],
            prior_bounded_stage=prior,tree_source_review=TREE_REVIEW,selected_tree_main=TREE,
            native_processes=126,success_cases=119,rejection_cases=7,preserved_successful_cases=23,
            prior_attempted_cases=24,prior_failed_cases=1)
        value['prerequisite_artifact_closures'].append(closure)
        value['prior_durable_jobs'].append(dict(directory=prior['durable']['directory'],artifacts=prior['durable']['artifacts']))
        value['pins']=dict(pins);value['input_resolutions']=dict(resolutions)
        return value
    r.held,r.build_plan=held,build_plan
    r.source_selection=lambda *args:select_tree(r,old_source,*args)
    r.schedule=lambda *args:remaining_schedule(old_schedule,*args)
    r.validate_prior_bounded=validate_prior;r.continuation_adapter=dict(adapter_ref);r.SUCCESS=SUCCESS
    r.run=lambda *args:run(r,*args)
    r.finish=lambda *args:finish(r,*args)
    return r

def load_controller(expected):
    before=BASE.lstat();require(stat.S_ISREG(before.st_mode) and BASE.resolve()==BASE,'Physical regular bounded intake required')
    with os.fdopen(os.open(BASE,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno())
        require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Bounded intake replaced')
        raw=stream.read(2*1024**2+1)
        require(len(raw)<=2*1024**2 and digest(raw)==BASE_SHA,'Frozen bounded intake changed')
    base=types.ModuleType('rebol_continuation_base');base.__file__=str(BASE)
    exec(compile(raw,str(BASE),'exec'),base.__dict__)
    r=base.load_controller(BASE_SHA,PRIMITIVE_SHA)
    own=Path(__file__).resolve();require(digest(r.read_small(own))==expected,'Continuation adapter changed')
    require(r.read_small(BASE)==raw,'Frozen bounded intake identity changed')
    return attach(r,dict(path=str(own),sha256=expected))

def finish(r,e,kb,report,plan,output,pins,resolutions,leases):
    errors=[];held=False;available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        ids=[s['id'] for s in plan['schedule']]
        require(len(ids)==126 and report['attempts']==ids[:len(report['attempts'])] and len(report['attempts'])<=126,'Attempt prefix differs')
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
            require(len(report['attempts'])==len(report['registered'])==len(report['captures'])==126
                and [x['id'] for x in report['captures']]==ids
                and sum(x['expected_rejection'] for x in report['captures'])==7
                and set(available)==set(report['validated_files'])==expected,'Complete126 evidence required')
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
    terminal=dict(schema='rebol126-bounded-terminal-v1',status=report['status'],report_sha256=report_sha,
        expected_report_sha256=digest(raw),available_evidence=closure,integrity_errors=errors,artifact_errors=artifact_errors,
        common_mutex_held=held,common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_cases=len(report['captures']),preserved_successful_cases=23,
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in r.GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(r.encoded(terminal))
    require(not errors and not artifact_errors,'Final integrity failed; evidence retained')

def run(r,e,kb,checker,plan,plan_path,plan_sha,pins,resolutions,common,leases):
    output=Path(plan['output']);e.pin(pins,resolutions,plan_path,plan_sha)
    r.verify_inputs(e,plan,pins,resolutions,leases);output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):(output/name).mkdir()
    report=dict(schema='rebol126-bounded-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_files={},pins=pins,
        input_resolutions=resolutions,primitive_review=plan['primitive_review'],continuation_adapter=plan['continuation_adapter'],
        prior_bounded_stage=plan['prior_bounded_stage'],preserved_successful_cases=23,benchmark_samples=0,**{k:False for k in r.GATES})
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
                previous=report['captures'][-1]['finished_at'] if report['captures'] else plan['prior_bounded_stage']['report_finished_at']
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

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();controller=load_controller(args.adapter_sha256)
    previous=sys.argv
    try:sys.argv=[previous[0],*remaining];controller.main()
    finally:sys.argv=previous

if __name__=='__main__':main()
