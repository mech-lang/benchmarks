"""One complete-map observation, preserving the closed tree/Pi observations."""
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
BASE=ROOT/'tools/qualification/rebol_work_final.py'
BASE_SHA='f9d3361d8082b3c356fc8381c53416befe8cd8e59e2f87a5025d096058b4ee11'
PRIOR_PACKET=ROOT/'experiments/rebol/work-observations-v1/remaining-intake-v1/final-bounded-v1'
PACKET=PRIOR_PACKET/'map-only-v1'
MAP_PACKET=ROOT/'experiments/rebol/work-observations-v1/complete-maps-v1'
BASE_REVIEW=dict(path=str(PRIOR_PACKET/'source-review-v1.json'),sha256='42009d444cc819088fee9347ec0bc1c0d4aef002a8e64f0d2b6dacdeedc9c679')
PRIOR=dict(path=str(PRIOR_PACKET/'failed-stage-review-v1.json'),sha256='4449440e8f46c83669b9e4300801c2b1f7dac7f2d43639bd6e72d35a7193e064')
MAP_REVIEW=dict(path=str(MAP_PACKET/'independent-source-review-v1.json'),sha256='7c04a472f9db65d8785c1c607c1a3b6734ca3a85e79cb3404e089350eb5dbc98')
MAP_SOURCE=dict(path=str(MAP_PACKET/'knucleotide.reb'),sha256='e934a2ccd8283661b45dfb4fd0a9255592d0a2a05043f66eaf6463c9fec0e805')
MAP_CONSUMER=dict(path=str(MAP_PACKET/'map_contract.py'),sha256='d7069fce1ebeb0c37e10f44e7bd11de7f87e7462cb9eef9c0d0ee23682de6346')
REFS=dict(
    plan=dict(path=str(PRIOR_PACKET/'plan-v1.json'),sha256='7c32526a6caf8b779731b166f5ae9843ad2532b7547e220c9765310f43771fba'),
    report=dict(path=str(PRIOR_PACKET/'run-v1/report.json'),sha256='8bee715a365a55b2181f0ab624c611e8f8b91ada07a2d247529e9f72f0d26032'),
    terminal=dict(path=str(PRIOR_PACKET/'run-v1/terminal.json'),sha256='bc8ccc04abb0b71805c51c33c81ce2a6bbf4238655771ec8fca43f11635d9cf6'))
JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-work3-final-v1'
IDS=('knucleotide-arbitrary-widths',)
SUCCESS='single-map-observation-retained-awaiting-independent-review'
KIND='rebol-bounded-work-observation'
GATES=('benchmark_correctness_qualified','runtime_source_equivalence_proven','source_work_qualified',
       'canonical_source_count_qualified','full_timing_qualified','chart_admission')
CAPTURE_FILES={'start.json','active.json','process.json','stdout.bin','stderr.bin'}


def require(value,message):
    if not value:raise AssertionError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,indent=2)+'\n').encode()


def pin_review_references(e,refs,pins,resolutions):
    for ref in refs.values():
        target=e.pin(pins,resolutions,ref['path'],ref['sha256'])
        raw=e.read_bytes(target)
        require(digest(raw)==ref['sha256'] and len(raw)==ref['bytes'], 'Source review reference bytes changed')


def read_small(path):
    path=Path(path);before=path.lstat()
    require(path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'Physical regular source required')
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Source replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2,'Source exceeds intake bound')
        after=path.lstat();require(stat.S_ISREG(after.st_mode) and (after.st_dev,after.st_ino)==(current.st_dev,current.st_ino),'Source replaced during read')
    return raw


@contextmanager
def prior_lease(e,inherited,review):
    durable=review['durable'];lease=durable['lease'];path=Path(lease['path'])
    require(durable['directory']==str(JOB) and path==JOB/'owner.lock'
        and path not in [Path(x[0]) for x in inherited]
        and all(type(lease[k]) is int for k in ('device','inode')),'Distinct prior work lease required')
    with e.regular(path) as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        leases=[*inherited,(path,stream,(lease['device'],lease['inode']))]
        e.check_leases(leases)
        try:yield leases
        finally:e.check_leases(leases)


def prior_ledger(review,plan,report,terminal,primitive_ref,bounded_ref):
    require(review['schema']=='rebol-three-work-observations-independent-failed-closure-v1'
        and review['status']=='map-rss-limit-failure-preserved-owned-stage-closed' and review['independent_review'] is True
        and review['references']==dict(REFS,primitive_review=primitive_ref,bounded_source_review=bounded_ref,source_review=BASE_REVIEW)
        and review['native_processes_started']==3 and review['completed_observations']==2
        and review['failed_observations']==1 and review['unstarted_observations']==0
        and all(review[k] is False for k in GATES),'Exact failed work3 independent review required')
    ids=['binarytrees-n4','pidigits-n27',IDS[0]]
    require(plan['schema']=='rebol-three-work-observations-plan-v1' and plan['repository']==str(ROOT)
        and plan['final_intake_adapter']==dict(path=str(BASE),sha256=BASE_SHA) and plan['entrypoint']==str(BASE)
        and plan['source_review']==BASE_REVIEW and plan['primitive_review']==primitive_ref and plan['bounded_source_review']==bounded_ref
        and plan['output']==str(PRIOR_PACKET/'run-v1') and [s['id'] for s in plan['schedule']]==ids
        and report['schema']=='rebol-three-work-observations-results-v1'
        and terminal['schema']=='rebol-three-work-observations-terminal-v1'
        and report['status']==terminal['status']=='stopped-unqualified'
        and report['error']=='Bounded process group exceeded RSS limit' and report['error_type']=='AssertionError'
        and report['plan']==REFS['plan']['path'] and report['plan_sha256']==REFS['plan']['sha256']
        and report['active'] is None and report['attempts']==[x['id'] for x in report['registered']]==ids
        and len({x['pid'] for x in report['registered']})==3
        and [x['id'] for x in report['captures']]==ids[:2]
        and [x['capture'] for x in review['successful_captures']]==report['captures']
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==REFS['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==3 and terminal['validated_observations']==2
        and report['pins']==dict(plan['pins'],**{REFS['plan']['path']:REFS['plan']['sha256']})
        and report['input_resolutions']==dict(plan['input_resolutions'],**{REFS['plan']['path']:REFS['plan']['path']})
        and all(plan[k] is report[k] is terminal[k] is False for k in GATES),'Failed work3 producer ledger differs')


def validate_prior(w,e,primitive_ref,bounded_ref,pins,resolutions):
    review=e.document(PRIOR,pins,resolutions)
    plan,report,terminal=[e.document(REFS[name],pins,resolutions) for name in ('plan','report','terminal')]
    prior_ledger(review,plan,report,terminal,primitive_ref,bounded_ref)
    for name,expected in report['pins'].items():
        e.pin(pins,resolutions,name,expected);require(resolutions[name]==report['input_resolutions'][name],'Prior named input changed')
    output=Path(plan['output']);complete=e.inventory(output)[0]
    require(complete==review['artifacts'] and len(complete)==19,'Exact failed work3 artifact inventory required')
    for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
    validated={}
    for index,item in enumerate(review['successful_captures']):
        slot=plan['schedule'][index];directory=output/slot['directory'];capture=item['capture']
        require(item['id']==slot['id'] and item['capture_directory']==str(directory)
            and item['bounded_observation_contract_satisfied'] is True and item['native_process_verified'] is True
            and capture['pid']==report['registered'][index]['pid']
            and e.inventory(directory)[0]==item['capture_files'],'Retained tree/Pi capture differs')
        validated.update({str(Path(slot['directory'])/name):v for name,v in item['capture_files'].items()})
    failed=review['failed_capture'];slot=plan['schedule'][2];directory=output/slot['directory']
    raw=json.loads(e.read_bytes(directory/'process.json'))
    require(failed['id']==slot['id']==IDS[0] and failed['capture_directory']==str(directory)
        and e.inventory(directory)[0]==failed['capture_files'] and raw==failed['process']
        and raw['pid']==report['registered'][2]['pid'] and raw['status']=='failed'
        and raw['error']=='Bounded process group exceeded RSS limit' and raw['exit_status']==-9
        and raw['observed_peak_process_group_rss_bytes']>raw['maximum_process_group_rss_bytes']==slot['rss_limit_bytes']
        and raw['direct_child_reaped'] is True and raw['remaining_after_cleanup']==raw['cleanup_errors']==[]
        and failed['observation_contract_satisfied'] is False and failed['sidecar_present'] is False
        and not os.path.lexists(slot['sidecar']),'Original map resource failure changed')
    require(validated==report['validated_files'] and e.inventory(output,('report.json','terminal.json'))[0]==report['artifacts']
        and e.inventory(output,('terminal.json',))[0]==terminal['available_evidence']
        and e.inventory(output)[0]==complete,'Failed work3 report/terminal inventory differs')
    durable=review['durable']
    require(durable['directory']==str(JOB) and e.inventory(JOB,('owner.lock',))[0]==durable['artifacts']
        and set(durable['artifacts'])=={'launch.json','command-started.json','terminal.json','request.json',
            'worker-started.json','command.stdout','command.stderr','worker.log'},'Failed work3 durable inventory differs')
    for name,item in durable['artifacts'].items():e.pin(pins,resolutions,JOB/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(JOB/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(BASE),'--adapter-sha256',BASE_SHA,
          'run','--plan',REFS['plan']['path'],'--plan-sha256',REFS['plan']['sha256']]
    require(launch['command']==started['command']==review['actual_command']==argv
        and launch['cwd']==started['cwd']==str(ROOT) and ended['status']=='command-failed'
        and type(ended['exit_code']) is int and ended['exit_code']==1
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals']==[]
        and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
        and started['command_identity']==ended['command_identity']
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid'],
        'Failed work3 durable launch or identity differs')
    record=dict(review=PRIOR,references=review['references'],durable=durable,
        retained_observations=review['successful_captures'],failed_capture=failed,
        actual_native_processes=3,preserved_observations=2,failed_observations=1)
    return plan,record,dict(directory=str(output),artifacts=complete)


def map_schedule(slots):
    require(len(slots)==3 and [s['id'] for s in slots]==['binarytrees-n4','pidigits-n27',IDS[0]],'Original three observation slots required')
    value=dict(slots[2]);value['command']=list(value['command'])
    require(value['consumer']=='map' and value['expected_observer_stderr_failure'] is True,'Original map observation policy changed')
    value['command'][3]=MAP_SOURCE['path'];value['expected_observer_stderr_failure']=False
    return [value]


def attach(w,base_review,map_review,adapter_ref):
    old_held,old_build=w.held,w.build_plan
    files=set(base_review['files'])|set(map_review['files'])|{str(p.relative_to(ROOT)) for p in (
        Path(__file__).resolve(),Path(__file__).with_name('test_rebol_work_map.py'),PACKET/'README.md')}
    def source_review(value):
        require(value['schema']=='rebol-single-map-work-source-review-v1'
            and value['status']=='independent-source-review-complete-native-observation-pending'
            and value['independent_review'] is True and set(value['files'])==files
            and all(value['files'][name]==sha for name,sha in {**base_review['files'],**map_review['files']}.items())
            and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256']
            and value['dependencies']==base_review['dependencies'] and value['base_source_review']==BASE_REVIEW
            and value['map_source_review']==MAP_REVIEW and value['prior_stage_review']==PRIOR
            and all(value[k] is False for k in GATES),'Exact single-map source approval required')
    @contextmanager
    def held(primitive_ref,bounded_ref,source_ref):
        with old_held(primitive_ref,bounded_ref,source_ref) as inherited:
            r,p,e,adapter,consumers,inspector,common,leases,intake,extension,review,pins,resolutions=inherited
            require(e.document(BASE_REVIEW,pins,resolutions)==base_review
                and e.document(MAP_REVIEW,pins,resolutions)==map_review,'Inherited source approval changed')
            for name,expected in map_review['dependencies'].items():e.pin(pins,resolutions,ROOT/name,expected)
            pin_review_references(e,map_review['references'],pins,resolutions)
            prior=e.document(PRIOR,pins,resolutions)
            raw=e.read_bytes(MAP_CONSUMER['path']);require(digest(raw)==MAP_CONSUMER['sha256'],'Complete-map consumer changed')
            consumers=dict(consumers,map=w.load(raw,Path(MAP_CONSUMER['path']),'rebol_complete_maps_consumer'))
            with prior_lease(e,leases,prior) as combined:
                yield r,p,e,adapter,consumers,inspector,common,combined,intake,extension,review,pins,resolutions
    def build_plan(r,p,e,adapter,consumers,inspector,output,primitive_ref,bounded_ref,source_ref,
                   intake,extension,review,pins,resolutions):
        require(output.is_relative_to(PACKET) and output!=PACKET,'Fresh single-map output inside its packet required')
        value=old_build(r,p,e,adapter,consumers,inspector,output,primitive_ref,bounded_ref,source_ref,
                        intake,extension,review,pins,resolutions)
        prior,record,closure=validate_prior(w,e,primitive_ref,bounded_ref,pins,resolutions)
        for key in ('extension_image','corrected_source','unavailable_inputs','prerequisite_artifact_closures',
                    'prior_durable_jobs','bounded_correctness','selected_tree_diagnostic','tree_source_review'):
            require(value[key]==prior[key],'Prior work prerequisite changed: '+key)
        value.update(schema='rebol-single-map-work-plan-v1',schedule=map_schedule(value['schedule']),native_processes=1,
            map_intake_adapter=adapter_ref,entrypoint=adapter_ref['path'],map_source_review=MAP_REVIEW,
            selected_map_diagnostic=MAP_SOURCE,selected_map_consumer=MAP_CONSUMER,prior_work_stage=record,
            preserved_observations=2,preserved_native_processes=3,preserved_failed_observations=1)
        value['prerequisite_artifact_closures'].append(closure)
        value['prior_durable_jobs'].append(dict(directory=record['durable']['directory'],artifacts=record['durable']['artifacts']))
        value['pins']=dict(pins);value['input_resolutions']=dict(resolutions)
        return value
    w.source_review,w.held,w.build_plan=source_review,held,build_plan
    w.run=lambda *args:run(w,*args);w.finish=lambda *args:finish(*args);w.SUCCESS=SUCCESS
    w.validate_prior_work=lambda *args:validate_prior(w,*args)
    return w


def load_controller(expected):
    raw=read_small(BASE);require(digest(raw)==BASE_SHA,'Frozen work-final adapter changed')
    base=types.ModuleType('rebol_single_map_base');base.__file__=str(BASE);exec(compile(raw,str(BASE),'exec'),base.__dict__)
    w=base.load_controller(BASE_SHA);own=Path(__file__).resolve()
    require(digest(read_small(own))==expected,'Single-map adapter changed')
    reviews=[]
    for ref in (BASE_REVIEW,MAP_REVIEW):
        raw=read_small(ref['path']);require(digest(raw)==ref['sha256'],'Reviewed source disposition changed')
        reviews.append(json.loads(raw))
    map_review=reviews[1]
    require(map_review['schema']=='rebol-complete-map-observation-source-review-v1'
        and map_review['status']=='independent-source-review-complete' and map_review['independent_review'] is True
        and map_review['files'][str(Path(MAP_SOURCE['path']).relative_to(ROOT))]==MAP_SOURCE['sha256']
        and map_review['files'][str(Path(MAP_CONSUMER['path']).relative_to(ROOT))]==MAP_CONSUMER['sha256']
        and all(map_review[k] is False for k in ('native_execution','metadata_prepared','runtime_qualified',
            'runtime_source_equivalence_proven','required_work_qualified','source_work_qualified',
            'full_size_work_qualified','full_timing_qualified','chart_admission')),
        'Independent complete-map source approval required')
    return attach(w,*reviews,dict(path=str(own),sha256=expected))


def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();w=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];w.main()
    finally:sys.argv=previous


# Only explicit single-process accounting/schema differs below; native observation is unchanged.
def finish(r,e,kb,report,plan,output,pins,resolutions,leases):
    errors = []
    lock_confirmed = False
    available,artifact_errors = e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        require(report['preserved_observations'] == plan['preserved_observations'] == 2
                and report['prior_work_stage'] == plan['prior_work_stage'], 'Preserved work disposition changed')
        require(report['attempts'] == list(IDS[:len(report['attempts'])]) and len(report['attempts']) <= 1,
                'Attempt prefix differs')
        require([item['id'] for item in report['registered']] == report['attempts'][:len(report['registered'])]
                and len({item['pid'] for item in report['registered']}) == len(report['registered'])
                and [item['id'] for item in report['captures']] == report['attempts'][:len(report['captures'])]
                and report['active'] is None, 'Registered/validated prefix differs')
        for slot in plan['schedule'][:len(report['attempts'])]:
            raw = json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration = next((item for item in report['registered'] if item['id'] == slot['id']),None)
            require(raw['cleanup_errors'] == [] and not raw.get('artifact_errors'), 'Native cleanup failed')
            if registration:
                require(raw['pid'] == registration['pid'] and raw['direct_child_reaped'] is True
                        and raw.get('remaining_process_group',[]) == raw.get('remaining_after_cleanup',[]) == [],
                        'Registered process group not closed')
            else:
                require(raw['native_process_started'] is False, 'Unregistered process started')
        require(all(available.get(name) == value for name,value in report['validated_files'].items()),
                'Validated artifact changed')
        if report['status'] == SUCCESS:
            expected = {str(Path(slot['directory'])/name) for slot in plan['schedule']
                        for name in CAPTURE_FILES | {Path(slot['sidecar']).name}}
            require(len(report['attempts']) == len(report['registered']) == len(report['captures']) == 1
                    and set(available) == set(report['validated_files']) == expected, 'One complete map capture required')
        r.verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:
        report['status'] = 'failed-integrity'
    raw = encoded(report)
    kb.save(output/'report.json',report)
    closure = {}
    report_sha = None
    try:
        require(e.read_bytes(output/'report.json') == raw, 'Serialized report changed')
        closure = e.inventory(output,('terminal.json',))[0]
        require(closure == dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),
                'Final inventory differs')
        r.verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0] == closure, 'Evidence changed during final input replay')
        report_sha = e.sha(output/'report.json')
        require(report_sha == digest(raw), 'Final report changed')
        e.check_leases(leases)
        lock_confirmed = True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
        report['status'] = 'failed-integrity'
        closure = {}
        report_sha = None
    terminal = dict(schema='rebol-single-map-work-terminal-v1',status=report['status'],
        report_sha256=report_sha,expected_report_sha256=digest(raw),available_evidence=closure,
        integrity_errors=errors,artifact_errors=artifact_errors,common_mutex_held=lock_confirmed,
        common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_observations=len(report['captures']),preserved_observations=2,producer_success_is_not_qualification=True,
        benchmark_samples=0,**{key:False for key in GATES})
    with (output/'terminal.json').open('xb') as stream:
        stream.write(encoded(terminal))
    require(not errors and not artifact_errors, 'Final integrity failed; evidence retained')


def run(w,r,e,adapter,consumers,kb,plan,plan_path,plan_sha,pins,resolutions,common,leases):
    output = Path(plan['output'])
    e.pin(pins,resolutions,plan_path,plan_sha)
    r.verify_inputs(e,plan,pins,resolutions,leases)
    output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):
        (output/name).mkdir()
    report = dict(schema='rebol-single-map-work-results-v1',status='running',plan=str(plan_path),
        plan_sha256=plan_sha,started_at=e.now(),active=None,attempts=[],registered=[],captures=[],
        validated_files={},pins=pins,input_resolutions=resolutions,primitive_review=plan['primitive_review'],
        benchmark_samples=0,prior_work_stage=plan['prior_work_stage'],preserved_observations=2,**{key:False for key in GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            r.verify_inputs(e,plan,pins,resolutions,leases)
            require(e.inventory(output,('report.json',))[0] == report['validated_files'], 'Earlier observations changed')
            payload = e.read_bytes(r.CORPUS.parent/slot['case']['stdin']['path'])
            require(len(payload) == slot['stdin_bytes'] and digest(payload) == slot['stdin_sha256'], 'Input changed')
            directory = output/slot['directory']
            directory.mkdir()
            with kb.atomic():
                report['attempts'].append(slot['id'])
                kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid))
                report['active'] = dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT = slot['timeout_seconds']
            kb.RSS_LIMIT = slot['rss_limit_bytes']
            kb.FILE_LIMIT = slot['native_file_limit_bytes']
            kb.CLEANUP_TIMEOUT = 5
            try:
                kb.observe(slot['command'],slot['environment'],directory,payload,common,launched,kind=KIND)
            except AssertionError as error:
                if not slot['expected_observer_stderr_failure'] or str(error) != 'Unexpected stderr; raw bytes retained':
                    raise
            with kb.atomic():
                report['active'] = None
                capture,snapshot = w.checked_case(r,e,adapter,consumers,kb,slot,directory,os.getpid())
                if report['captures']:
                    require(r.stamp(report['captures'][-1]['finished_at']) <= r.stamp(capture['started_at']),
                            'Overlapping observations')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):value for name,value in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status'] = SUCCESS
    except BaseException as error:
        with kb.atomic():
            report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():
            finish(r,e,kb,report,plan,output,pins,resolutions,leases)



if __name__ == '__main__':main()
