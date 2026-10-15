"""Serial shared149 Rebol main captures after actual primitive qualification.

No import performs evidence intake or launches a process. The fixed19 helper
and frozen observer remain unchanged. Normal expected rejections retain their
original failed observer receipts; only the separate Rebol output checker can
accept their complete streams. This producer grants no admission gate.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/bounded-v1'
HELPER = ROOT/'tools/qualification/rebol_primitive_fixtures.py'
CHECKER = ROOT/'tools/qualification/rebol_outputs.py'
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
BUILD = CORPUS.parent.parent/'build.py'
BUILD_SHA = 'ebe804f81cfc9df83083fe548f9c09e302f261984a0a96fbd14782d6e65c06c0'
ORIGINAL = ROOT/'experiments/rebol/primitive-fixtures-v1'
FANN = ROOT/'experiments/rebol/fannkuch-zero-v1/main.reb'
BENCHES = ('binarytrees','fannkuchredux','fasta','knucleotide','mandelbrot','nbody',
           'pidigits','regexredux','revcomp','spectralnorm')
FILES = {str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),
    Path(__file__).with_name('test_rebol_bounded.py'), CHECKER,
    CHECKER.with_name('test_rebol_outputs.py'), FANN, PACKET/'README.md')}
GATES = ('benchmark_correctness_qualified','runtime_source_equivalence_proven',
         'source_work_qualified','canonical_source_count_qualified',
         'full_timing_qualified','chart_admission')
SUCCESS = 'all149-output-contracts-retained-awaiting-independent-review'
KIND = 'rebol-bounded-main'
CAPTURE_FILES = {'start.json','active.json','process.json','stdout.bin','stderr.bin'}


def require(value, message):
    if not value: raise AssertionError(message)


def encoded(value): return (json.dumps(value,indent=2)+'\n').encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_small(path, limit=2*1024**2):
    path=Path(path)
    require(path.is_absolute() and path.resolve(strict=True)==path,'Physical absolute metadata required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Regular metadata required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd);require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Metadata replaced')
        raw=stream.read(limit+1);require(len(raw)<=limit,'Metadata exceeds intake bound')
        after=path.lstat();require(stat.S_ISREG(after.st_mode) and
            (after.st_dev,after.st_ino)==(held.st_dev,held.st_ino),'Metadata changed during read')
    return raw


def ref(path, sha):
    require(Path(path).is_absolute() and type(sha) is str and re.fullmatch('[0-9a-f]{64}',sha),
            'Absolute path and exact SHA256 required')
    return dict(path=str(path),sha256=sha)


def load(raw, path, name):
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def bootstrap(primitive_ref, source_ref):
    raw=read_small(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Source review changed')
    source=json.loads(raw)
    require(source['schema']=='rebol149-controller-source-review-v1'
        and source['status']=='independent-source-review-complete-native-cases-pending'
        and source['independent_review'] is True and set(source['files'])==FILES
        and set(source['dependencies'])=={str(HELPER.relative_to(ROOT))}
        and all(source[k] is False for k in GATES),'Exact independent bounded source review required')
    helper=read_small(HELPER)
    require(digest(helper)==source['dependencies'][str(HELPER.relative_to(ROOT))],'Fixed19 helper changed')
    p=load(helper,HELPER,'rebol149_fixed19_helper');require(p.ROOT==ROOT,'Original helper root changed')
    raw=read_small(primitive_ref['path']);require(digest(raw)==primitive_ref['sha256'],'Primitive approval changed')
    primitive=json.loads(raw);check_primitive_review(primitive)
    return p,primitive,source


def check_primitive_review(review):
    require(review['schema']=='rebol19-independent-primitive-review-v1'
        and review['status']=='exact-eighteen-primitive-contracts-qualified'
        and review['independent_review'] is True and review['full_primitive_fixtures_qualified'] is True
        and all(review[k] is False for k in GATES)
        and type(review['native_processes']) is int and review['native_processes']==19
        and type(review['fixture_processes']) is int and review['fixture_processes']==18
        and type(review['benchmark_samples']) is int and review['benchmark_samples']==0,
        'Actual independent primitive19 approval required')
    require(set(review['references'])=={'plan','report','terminal','extension_review','source_review'},
            'Exact primitive evidence references required')
    for item in review['references'].values():ref(item['path'],item['sha256'])
    durable=review['durable'];require(set(durable)=={'directory','artifacts','lease'},'Primitive durable closure required')
    job=Path(durable['directory']);lease=durable['lease']
    require(job.is_relative_to(ROOT/'experiments/shared/owned-jobs-v1/owned-jobs')
        and lease['path']==str(job/'owner.lock') and set(lease)=={'path','device','inode'}
        and all(type(lease[k]) is int for k in ('device','inode')),'Primitive lease identity differs')


@contextmanager
def held(primitive_ref, source_ref):
    p,initial,initial_source=bootstrap(primitive_ref,source_ref)
    refs=initial['references']
    with p.held(refs['extension_review'],refs['source_review']) as inherited:
        e,adapter,inspector,common,leases,intake,extension,pins,resolutions=inherited
        review=e.document(primitive_ref,pins,resolutions);source=e.document(source_ref,pins,resolutions)
        require(review==initial and source==initial_source,'Review changed after lock acquisition')
        for name,expected in {**source['files'],**source['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,expected)
        raw=e.read_bytes(CHECKER);require(digest(raw)==source['files'][str(CHECKER.relative_to(ROOT))],'Output checker changed')
        checker=load(raw,CHECKER,'rebol149_output_checker')
        lease=review['durable']['lease'];path=Path(lease['path'])
        require(path not in [Path(item[0]) for item in leases],'Duplicate primitive lease')
        with e.regular(path) as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            combined=leases+[(path,stream,(lease['device'],lease['inode']))]
            e.check_leases(combined)
            try:yield p,e,adapter,checker,inspector,common,combined,intake,extension,review,pins,resolutions
            finally:e.check_leases(combined)


def durable_inputs(e, review, plan_ref, pins, resolutions):
    durable=review['durable'];job=e.physical(Path(durable['directory']))
    artifacts=e.inventory(job,('owner.lock',))[0]
    require(artifacts==durable['artifacts'] and {'launch.json','command-started.json','terminal.json'}<=set(artifacts),
            'Primitive durable inventory differs')
    for name,item in artifacts.items():e.pin(pins,resolutions,job/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(HELPER),'run','--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256']]
    require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
        and ended['status']=='command-exited-zero-awaiting-report-review' and type(ended['exit_code']) is int and ended['exit_code']==0
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False
        and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
        and started['command_identity_observation_missing'] is False
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
        and started['command_identity']==ended['command_identity'],'Primitive durable ownership differs')
    return started['command_pid'],dict(directory=str(job),artifacts=artifacts)


def primitive_inputs(p,e,adapter,inspector,review,intake,extension,pins,resolutions):
    refs=review['references']
    plan=e.document(refs['plan'],pins,resolutions);report=e.document(refs['report'],pins,resolutions)
    terminal=e.document(refs['terminal'],pins,resolutions)
    prior,closures,extension_job,image=p.extension_inputs(e,inspector,extension,intake,pins,resolutions)
    output=e.physical(Path(plan['output']))
    spec=e.document(dict(path=str(ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),pins,resolutions)
    require(plan['schema']=='rebol-primitive-fixtures-plan-v2' and plan['repository']==str(ROOT)
        and plan['controller']==str(HELPER) and plan['controller_sha256']==pins[str(HELPER)]
        and plan['extension_review']==refs['extension_review'] and plan['source_review']==refs['source_review']
        and output.is_relative_to(p.PACKET) and output!=p.PACKET
        and refs['report']['path']==str(output/'report.json') and refs['terminal']['path']==str(output/'terminal.json')
        and plan['schedule']==p.schedule(e,adapter,spec,intake,image,output)
        and plan['native_processes']==19 and plan['fixture_processes']==18 and plan['diagnostic_compilations']==1
        and plan['automatic_retry'] is False and plan['extension_image']==image
        and plan['corrected_source']==extension['corrected_source']
        and plan['unavailable_inputs']==prior['unavailable_inputs']
        and plan['prerequisite_artifact_closures']==closures
        and plan['extension_durable']==extension_job,'Primitive source/plan identity differs')
    for name,expected in plan['pins'].items():
        e.pin(pins,resolutions,name,expected)
        require(resolutions[name]==plan['input_resolutions'][name],'Primitive named input changed')
    ids=[slot['id'] for slot in plan['schedule']]
    require(report['schema']=='rebol-primitive-fixtures-results-v2'
        and terminal['schema']=='rebol-primitive-fixtures-terminal-v2'
        and report['status']==terminal['status']==p.SUCCESS
        and report['plan']==refs['plan']['path'] and report['plan_sha256']==refs['plan']['sha256']
        and report['pins']==dict(plan['pins'],**{refs['plan']['path']:refs['plan']['sha256']})
        and report['input_resolutions']==dict(plan['input_resolutions'],**{refs['plan']['path']:refs['plan']['path']})
        and report['attempts']==ids and [r['id'] for r in report['registered']]==ids
        and [r['id'] for r in report['captures']]==ids and report['active'] is None
        and len({r['pid'] for r in report['registered']})==19
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==refs['report']['sha256']
        and terminal['native_processes_started']==terminal['validated_captures']==19
        and terminal['common_mutex_held'] is True
        and all(report[k] is terminal[k] is False for k in p.GATES),'Primitive producer is not closed successfully')
    artifacts=e.inventory(output,('report.json','terminal.json'))[0]
    require(artifacts==report['validated_files']==report['artifacts'] and set(artifacts)==p.expected_files(plan),
            'Primitive validated artifact membership differs')
    available=dict(artifacts,**{'report.json':dict(bytes=len(e.read_bytes(output/'report.json')),sha256=refs['report']['sha256'])})
    require(terminal['available_evidence']==available,'Primitive terminal inventory differs')
    complete=dict(available,**{'terminal.json':dict(bytes=len(e.read_bytes(output/'terminal.json')),sha256=refs['terminal']['sha256'])})
    for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
    parent,job=durable_inputs(e,review,refs['plan'],pins,resolutions)
    previous=None
    for slot,registration,capture in zip(plan['schedule'],report['registered'],report['captures']):
        directory=output/slot['directory'];prefix=slot['directory']+'/'
        extra={name[len(prefix):]:item for name,item in artifacts.items() if name.startswith(prefix) and name[len(prefix):] not in CAPTURE_FILES}
        observed,snapshot=p.checked_capture(e,slot,directory,parent,inspector.kb,extra)
        require(observed['pid']==registration['pid'] and all(capture.get(k)==v for k,v in observed.items()),'Primitive capture join differs')
        if previous is not None:require(previous<=stamp(observed['started_at']),'Primitive commands overlap')
        previous=stamp(observed['finished_at'])
        if 'case' in slot:
            case=slot['case'];sidecars={key:e.read_bytes(path) for key,path in slot['sidecars'].items()}
            decoded=adapter.check_case(case,e.read_bytes(directory/'stdout.bin'),e.read_bytes(directory/'stderr.bin'),0,**sidecars)
            require(decoded==capture['fixture_observations'],'Primitive output review differs')
    require(e.inventory(output,('terminal.json',))[0]==available,'Primitive evidence changed during replay')
    return plan,closures+[dict(directory=str(output),artifacts=complete)], [extension_job,job],image


def stamp(value):
    parsed=datetime.fromisoformat(value);require(parsed.tzinfo is not None,'Timezone-aware timestamp required');return parsed


def corpus(e,pins,resolutions):
    data=e.document(dict(path=str(CORPUS),sha256=CORPUS_SHA),pins,resolutions)
    e.pin(pins,resolutions,BUILD,BUILD_SHA)
    require(data['schema']=='shared-bounded-workload-corpus-v1' and data['generator_sha256']==BUILD_SHA
        and data['case_count']==len(data['cases'])==149 and data['success_cases']==142 and data['rejection_cases']==7
        and data['subject_output_qualified'] is data['source_work_qualified'] is data['chart_admission'] is False,
        'Exact shared149 corpus required')
    for name,expected in data['reference_pins'].items():e.pin(pins,resolutions,ROOT/name,expected)
    identities=set()
    for case in data['cases']:
        identity=(case['benchmark'],case['case'])
        require(identity not in identities and case['benchmark'] in BENCHES,'Duplicate or unknown corpus case')
        identities.add(identity)
        require(case['input_kind'] in ('stdin','integer-argument') and type(case['n']) is int and case['n']>=0,'Invalid case input')
        negative=case['expected_exit']=='nonzero'
        require((negative and case['benchmark']=='revcomp' and case['validation']=='language-specific-invalid-iupac' and 'expected' not in case)
            or (type(case['expected_exit']) is int and case['expected_exit']==0 and 'expected' in case),'Unexpected output contract')
        for key in ('stdin','expected'):
            if key not in case:continue
            item=case[key];relative=Path(item['path']);path=CORPUS.parent/relative
            require(not relative.is_absolute() and '..' not in relative.parts and type(item['bytes']) is int and item['bytes']>=0,
                    'Escaping or invalid corpus file')
            e.physical(path);e.pin(pins,resolutions,path,item['sha256'])
            require(path.stat().st_size==item['bytes'],'Corpus file length differs')
        require(case['input_kind']!='integer-argument' or case['stdin']['bytes']==0,'Numeric case acquired stdin')
    require(sum(c['expected_exit']=='nonzero' for c in data['cases'])==7,'Wrong rejection count')
    return data['cases']


def source_selection(e,spec,mapping,cases,pins,resolutions):
    require(mapping['schema']=='rebol-ten-source-bounded-corpus-map-v1' and mapping['status']=='source-map-only'
        and mapping['corpus_sha256']==CORPUS_SHA and mapping['case_count']==149 and mapping['qualification'] is False
        and [row['benchmark'] for row in mapping['rows']]==list(BENCHES),'Original ten-main map differs')
    result={}
    for row in mapping['rows']:
        bench=row['benchmark'];old=ROOT/row['source'];expected=spec['immutable_source_pins'][row['source']]
        require(row['source_sha256']==expected and set(row['case_ids'])=={c['case'] for c in cases if c['benchmark']==bench},
                'Original source/case mapping differs')
        e.pin(pins,resolutions,old,expected)
        selected=FANN if bench=='fannkuchredux' else old
        require(str(selected) in pins,'Selected source lacks independent source-review pin')
        result[bench]=dict(path=str(selected),sha256=pins[str(selected)],historical_path=str(old),historical_sha256=expected,
                           substitution='zero-size-fannkuch-source' if bench=='fannkuchredux' else None)
    return result


def schedule(e,checker,cases,sources,image,output,limits):
    require(type(checker.NEGATIVE_EXIT_STATUS) is int and 0<checker.NEGATIVE_EXIT_STATUS<128,'Reviewed normal Rebol rejection exit required')
    result=[]
    for index,case in enumerate(cases):
        directory=f'{index:03d}-{case["benchmark"]}-{case["case"]}'
        argv=[str(e.RUNTIME),'-q','-s',sources[case['benchmark']]['path']]
        if case['input_kind']=='integer-argument':argv.append(str(case['n']))
        environment=e.environment(output);environment['MECH_CLBG_REBOL_PRIMITIVES']=image['path']
        require(all(key not in environment for key in ('DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH','MECH_REBOL_IO_FAULT_REPORT')),
                'Benchmark acquired diagnostic interposer settings')
        result.append(dict(id=case['benchmark']+':'+case['case'],directory=directory,command=argv,environment=environment,
            case=case,source=sources[case['benchmark']],expected_exit=checker.NEGATIVE_EXIT_STATUS if case['expected_exit']=='nonzero' else 0,
            timeout_seconds=limits['per_process_seconds'],rss_limit_bytes=limits['per_process_rss_bytes'],
            stream_limit_bytes=limits['stdout_limit_bytes'],stdin_bytes=case['stdin']['bytes'],stdin_sha256=case['stdin']['sha256']))
    return result


def build_plan(p,e,adapter,checker,inspector,output,primitive_ref,source_ref,intake,extension,review,pins,resolutions):
    e.physical(output);require(output.is_relative_to(PACKET) and output!=PACKET and not os.path.lexists(output),'Fresh bounded output required')
    prior,closures,jobs,image=primitive_inputs(p,e,adapter,inspector,review,intake,extension,pins,resolutions)
    spec=e.document(dict(path=str(ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),pins,resolutions)
    limits=spec['limits'];require(limits==dict(per_process_seconds=180,per_process_rss_bytes=536870912,
        stdout_limit_bytes=1048576,stderr_limit_bytes=1048576,automatic_retry=False),'Retained Rebol bounded policy differs')
    for name,expected in spec['immutable_source_pins'].items():e.pin(pins,resolutions,ROOT/name,expected)
    mapping=e.document(dict(path=str(ORIGINAL/'bounded-corpus-map.json'),sha256=spec['fixture_source_pins']['bounded-corpus-map.json']),pins,resolutions)
    cases=corpus(e,pins,resolutions);sources=source_selection(e,spec,mapping,cases,pins,resolutions)
    return dict(schema='rebol149-bounded-plan-v1',status='prepared-awaiting-independent-review',repository=str(ROOT),
        controller=str(Path(__file__).resolve()),controller_sha256=e.sha(__file__),output=str(output),
        primitive_review=primitive_ref,source_review=source_ref,schedule=schedule(e,checker,cases,sources,image,output,limits),
        sources=sources,extension_image=image,corrected_source=extension['corrected_source'],
        historical_spec=dict(path=str(ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),historical_sources_preserved=True,
        corpus=dict(path=str(CORPUS),sha256=CORPUS_SHA),limits=limits,cleanup_timeout_seconds=5,
        pins=dict(pins),input_resolutions=dict(resolutions),unavailable_inputs=prior['unavailable_inputs'],
        prerequisite_artifact_closures=closures,prior_durable_jobs=jobs,common_mutex_inode=79859134,
        native_processes=149,success_cases=142,rejection_cases=7,compilations=0,matched_controls=0,
        automatic_retry=False,benchmark_samples=0,**{k:False for k in GATES})


def verify_inputs(e,plan,pins,resolutions,leases):
    e.verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures'])
    for job in plan['prior_durable_jobs']:
        require(e.inventory(Path(job['directory']),('owner.lock',))[0]==job['artifacts'],'Prior durable inventory changed')
    e.check_leases(leases)


def native_capture(e,kb,slot,directory,parent):
    snapshots=e.inventory(directory)[0];require(set(snapshots)==CAPTURE_FILES,'Native capture file set differs')
    start,active,final=[json.loads(e.read_bytes(directory/(name+'.json'))) for name in ('start','active','process')]
    for record in (start,active,final):
        require(record['command']==slot['command'] and record['environment']==slot['environment']
            and record['cwd']==str(directory) and record['kind']==KIND and record['started_at']==start['started_at']
            and record['process_timeout_seconds']==slot['timeout_seconds'] and record['cleanup_timeout_seconds']==5
            and record['maximum_process_group_rss_bytes']==slot['rss_limit_bytes']
            and record['native_file_limit_bytes']==slot['stream_limit_bytes']
            and record['stdout_capture_limit_bytes']==slot['stream_limit_bytes']+kb.PIPE_CHUNK
            and record['stdout_transport']=='OS pipe, retained as received' and record['stderr_transport']=='exclusive artifact'
            and record['stdin_bytes']==slot['stdin_bytes'] and record['stdin_sha256']==slot['stdin_sha256']
            and record['inherited_common_mutex'] is True and record['common_mutex_inode']==79859134
            and type(record['benchmark_samples']) is int and record['benchmark_samples']==0
            and record['source_work_qualified'] is record['chart_admission'] is False,'Native launch/policy differs')
    identity,leader,pid=final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status']=='starting' and start['native_process_started'] is False
        and active['status']=='running' and active['native_process_started'] is final['native_process_started'] is True
        and active['identity']==identity and identity['ppid']==parent
        and all(type(identity[k]) is int and identity[k]==leader[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and type(pid) is int and pid>0 and active['pid']==active['pgid']==pid==final['pgid']==identity['pid']==identity['pgid']
        and leader['status']==5 and final['direct_child_reaped'] is True
        and final['remaining_process_group']==final.get('remaining_after_cleanup',[])==[]
        and final['stop_signals']==final['cleanup_errors']==[] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples']>0
        and type(final['exit_status']) is int and final['exit_status']==slot['expected_exit']
        and stamp(start['started_at'])<=stamp(final['finished_at']),'Normal owned native closure required')
    if slot['expected_exit']:
        require(final['status']=='failed' and final.get('error_type')=='AssertionError'
            and final.get('error')=='Native command exited unsuccessfully','Unrelated failure is not an expected rejection')
    else:require(final['status']=='native-passed' and not final.get('error') and not final.get('error_type'),'Successful native receipt required')
    peak=final['observed_peak_process_group_rss_bytes']
    require(type(peak) is int and 0<=peak<=slot['rss_limit_bytes'],'Invalid RSS observation')
    if peak==0:require(identity['status']==5 and not final.get('live_rss_observation_obtained',False),'Zero RSS lacks initial owned zombie')
    streams=[]
    for name in ('stdout','stderr'):
        raw=e.read_bytes(directory/(name+'.bin'));entry=dict(bytes=len(raw),sha256=digest(raw))
        require(entry==snapshots[name+'.bin']==dict(bytes=final[name+'_bytes'],sha256=final[name+'_sha256'])
            and len(raw)<=slot['stream_limit_bytes'],'Native stream changed or exceeded bound')
        streams.append(raw)
    require(e.inventory(directory)[0]==snapshots,'Capture changed during validation')
    return final,streams,snapshots


def checked_case(e,kb,checker,slot,directory,parent):
    final,streams,snapshots=native_capture(e,kb,slot,directory,parent)
    case=slot['case'];expected=None if slot['expected_exit'] else e.read_bytes(CORPUS.parent/case['expected']['path'])
    result=checker.validate(case,*streams,final['exit_status'],expected)
    require(e.inventory(directory)[0]==snapshots,'Validated output changed before adoption')
    return dict(id=slot['id'],pid=final['pid'],started_at=final['started_at'],finished_at=final['finished_at'],
        observer_status=final['status'],expected_rejection=bool(slot['expected_exit']),output_validation=result,
        observed_peak_process_group_rss_bytes=final['observed_peak_process_group_rss_bytes'] or None,
        rss_observation_complete=False,memory_usage_qualified=False),snapshots


def finish(e,kb,report,plan,output,pins,resolutions,leases):
    errors=[];held=False;available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        ids=[s['id'] for s in plan['schedule']]
        require(report['attempts']==ids[:len(report['attempts'])] and len(report['attempts'])<=149,'Attempt prefix differs')
        require([r['id'] for r in report['registered']]==report['attempts'][:len(report['registered'])]
            and len({r['pid'] for r in report['registered']})==len(report['registered']) and report['active'] is None,
            'Registered prefix differs')
        for slot in plan['schedule'][:len(report['attempts'])]:
            raw=json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration=next((r for r in report['registered'] if r['id']==slot['id']),None)
            require(raw['cleanup_errors']==[] and not raw.get('artifact_errors'),'Native cleanup failed')
            if registration:require(raw['pid']==registration['pid'] and raw['direct_child_reaped'] is True
                and raw.get('remaining_process_group',[])==raw.get('remaining_after_cleanup',[])==[],'Owned group not closed')
            else:require(raw['native_process_started'] is False,'Unregistered native process')
        require(all(available.get(name)==value for name,value in report['validated_files'].items()),'Validated artifact changed')
        if report['status']==SUCCESS:
            expected={str(Path(s['directory'])/name) for s in plan['schedule'] for name in CAPTURE_FILES}
            require(len(report['attempts'])==len(report['registered'])==len(report['captures'])==149
                and sum(r['expected_rejection'] for r in report['captures'])==7
                and set(available)==set(report['validated_files'])==expected,'Complete149 evidence required')
        verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:report['status']='failed-integrity'
    raw=encoded(report);kb.save(output/'report.json',report);closure={};report_sha=None
    try:
        require(e.read_bytes(output/'report.json')==raw,'Serialized report changed')
        closure=e.inventory(output,('terminal.json',))[0]
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),'Final inventory differs')
        verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0]==closure,'Output changed during final input replay')
        report_sha=e.sha(output/'report.json');require(report_sha==digest(raw),'Final report changed')
        e.check_leases(leases);held=True
    except BaseException as error:errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={};report_sha=None
    terminal=dict(schema='rebol149-bounded-terminal-v1',status=report['status'],report_sha256=report_sha,
        expected_report_sha256=digest(raw),available_evidence=closure,integrity_errors=errors,artifact_errors=artifact_errors,
        common_mutex_held=held,common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_cases=len(report['captures']),producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(encoded(terminal))
    require(not errors and not artifact_errors,'Final integrity failed; evidence retained')


def run(e,kb,checker,plan,plan_path,plan_sha,pins,resolutions,common,leases):
    output=Path(plan['output']);e.pin(pins,resolutions,plan_path,plan_sha)
    verify_inputs(e,plan,pins,resolutions,leases);output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):(output/name).mkdir()
    report=dict(schema='rebol149-bounded-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_files={},pins=pins,
        input_resolutions=resolutions,primitive_review=plan['primitive_review'],benchmark_samples=0,**{k:False for k in GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            verify_inputs(e,plan,pins,resolutions,leases)
            require(e.inventory(output,('report.json',))[0]==report['validated_files'],'Earlier artifacts changed')
            payload=e.read_bytes(CORPUS.parent/slot['case']['stdin']['path'])
            require(len(payload)==slot['stdin_bytes'] and digest(payload)==slot['stdin_sha256'],'Case input changed')
            directory=output/slot['directory'];directory.mkdir()
            with kb.atomic():report['attempts'].append(slot['id']);kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid));report['active']=dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT=slot['timeout_seconds'];kb.CLEANUP_TIMEOUT=5
            kb.RSS_LIMIT=slot['rss_limit_bytes'];kb.FILE_LIMIT=slot['stream_limit_bytes']
            try:kb.observe(slot['command'],slot['environment'],directory,payload,common,launched,kind=KIND)
            except AssertionError as error:
                # Never rewrite the frozen producer failure. Only its exact
                # normal-nonzero envelope plus the separate output contract
                # may establish an expected rejection below.
                if not slot['expected_exit'] or str(error)!='Native command exited unsuccessfully':raise
            with kb.atomic():
                report['active']=None
                capture,snapshot=checked_case(e,kb,checker,slot,directory,os.getpid())
                if report['captures']:require(stamp(report['captures'][-1]['finished_at'])<=stamp(capture['started_at']),'Overlapping cases')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):item for name,item in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        with kb.atomic():report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():finish(e,kb,report,plan,output,pins,resolutions,leases)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prepare=sub.add_parser('prepare');prepare.add_argument('--plan',type=Path,required=True);prepare.add_argument('--output',type=Path,required=True)
    for name in ('primitive-review','source-review'):
        prepare.add_argument('--'+name,type=Path,required=True);prepare.add_argument('--'+name+'-sha256',required=True)
    execute=sub.add_parser('run');execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,'Use retained Python -I -S -B')
    def stop(signum,frame):raise KeyboardInterrupt('Rebol bounded stage stopped: '+str(signum))
    for signum in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(signum,stop)
    if args.mode=='prepare':
        primitive_ref=ref(args.primitive_review,args.primitive_review_sha256);source_ref=ref(args.source_review,args.source_review_sha256)
        output=args.output;saved=None
    else:
        raw=read_small(args.plan,64*1024**2);require(digest(raw)==args.plan_sha256,'Prepared plan changed')
        saved=json.loads(raw);primitive_ref=saved['primitive_review'];source_ref=saved['source_review'];output=Path(saved['output'])
    with held(primitive_ref,source_ref) as context:
        p,e,adapter,checker,inspector,common,leases,intake,extension,review,pins,resolutions=context
        require(Path(sys.executable).resolve()==e.PYTHON.resolve(),'Retained Python required')
        plan=build_plan(p,e,adapter,checker,inspector,output,primitive_ref,source_ref,intake,extension,review,pins,resolutions)
        verify_inputs(e,plan,pins,resolutions,leases)
        if args.mode=='prepare':
            e.physical(args.plan);require(args.plan.is_relative_to(PACKET) and not args.plan.is_relative_to(output),'Separate packet plan required')
            args.plan.parent.mkdir(parents=True,exist_ok=True);raw=encoded(plan)
            with inspector.kb.atomic():
                with args.plan.open('xb') as stream:stream.write(raw)
                verify_inputs(e,plan,pins,resolutions,leases);require(e.read_bytes(args.plan)==raw,'Prepared plan changed');e.check_leases(leases)
            result=dict(plan=str(args.plan),sha256=digest(raw),native_processes_started=0)
        else:
            require(saved==plan,'Prepared149 stage does not replay exactly')
            run(e,inspector.kb,checker,plan,args.plan,args.plan_sha256,pins,resolutions,common,leases)
            result=dict(status=SUCCESS,output=str(output),qualified=False)
    print(json.dumps(result))


if __name__=='__main__':main()
