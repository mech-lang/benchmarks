"""Two retained small binary-tree cases after exact scoped diagnostics pass."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'experiments/apl/binarytrees-workspace-v1'
PACKET=ORIGINAL/'whole-subject-v1'
PRIOR=ROOT/'tools/qualification/apl_workspace_scoped.py'
PRIOR_SHA='0596f2969057ca5a2040a17902335c24c3f01e38ca9ea0fd15cb523e6bc096db'
SCOPED=ORIGINAL/'scope-isolated-v1'
SCOPED_RUN=SCOPED/'run-v1'
SCOPED_JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/apl-scope-isolated2-v1'
OWNERSHIP_REVIEW=SCOPED/'actual-ownership-review-v1.json'
OWNERSHIP_REVIEW_SHA='1fb964c7d73c174e540b71ada594b8b435d9466dc2d9ecc55ba6a3db88059f76'
SCOPED_FIXED={
    SCOPED/'plan-v1.json':'265b9094746431b27a3fbfd18b7d841916f0f7aaf35177e782502e88421f81b6',
    SCOPED_RUN/'report.json':'8f3a8405726f694f38654b5c42e7b892cfe72ef35528c17510f8cda53935a59b',
    SCOPED_RUN/'terminal.json':'a0c9643659bc45eeba3999536f85d80b24cd6c3cd3cc6cb450d1bcb3a2677b97',
    SCOPED/'actual-closure-v1.json':'36f0075e14eac29ff224ab74af3c4315b2c2f4523cc5307682c9dfe71551fb98',
    SCOPED_JOB/'terminal.json':'249f735cfcdd5c4e4b8bf73138dc8b5d677fc8c5786b614effc3014841bd3eac',
}
IDS=('whole-subject-n4','whole-subject-n10')
SUCCESS='two-small-subject-captures-awaiting-independent-work-review'


def require(value,message):
    if not value:raise AssertionError(message)


raw=PRIOR.read_bytes()
require(hashlib.sha256(raw).hexdigest()==PRIOR_SHA,'Frozen scoped controller changed')
spec=importlib.util.spec_from_file_location('apl_subject_private_scoped',PRIOR)
s=importlib.util.module_from_spec(spec);exec(compile(raw,str(PRIOR),'exec'),s.__dict__)
r,b,kb=s.r,s.b,s.kb
sha,physical,pin,document=s.sha,s.physical,s.pin,s.document
inventory,stamp=s.inventory,s.stamp
WARNING=s.WARNING
FALSE_GATES=s.FALSE_GATES
_scoped_lease=None
_prior_lock_identity=s.lock_identity
source_spec_raw=b.SPEC.read_bytes()
require(hashlib.sha256(source_spec_raw).hexdigest()==b.SPEC_SHA,'Original bounded specification changed')
SUBJECT_ROWS=json.loads(source_spec_raw)['commands'][3:]
require(tuple(row['id'] for row in SUBJECT_ROWS)==IDS,'Original small-case schedule changed')


def check_output(slot,stdout,stderr,pattern):
    if slot['id'] in s.IDS:
        # Only retained capture replay uses these slots; the new schedule is N4/N10.
        return s.check_output(slot,stdout,stderr,pattern)
    require(slot['id'] in IDS,'Only retained small subject cases are registered')
    expected=SUBJECT_ROWS[IDS.index(slot['id'])]['expected_stdout_utf8']
    require(slot['expected_stdout_utf8']==expected,'Retained subject oracle changed')
    return r.check_output(slot,stdout,stderr,pattern)


def lock_identity(lock):
    inherited=_prior_lock_identity(lock)
    if _scoped_lease is not None:
        held,named=os.fstat(_scoped_lease.fileno()),(SCOPED_JOB/'owner.lock').stat()
        require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino) and held.st_ino==82382998,
                'Scoped diagnostic durable lease changed')
    return inherited


b.check_output=check_output
b.lock_identity=lock_identity
observe,checked_capture=b.observe,b.checked_capture


@contextmanager
def held_mutex():
    global _scoped_lease
    require(_scoped_lease is None,'Nested scoped lease ownership')
    with s.held_mutex() as lock,(SCOPED_JOB/'owner.lock').open('rb') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        _scoped_lease=lease
        try:
            lock_identity(lock)
            yield lock
        finally:
            try:lock_identity(lock)
            finally:_scoped_lease=None


def verify(pins,resolutions,absent,lock):
    require(_scoped_lease is not None,'Scoped diagnostic lease required')
    s.verify(pins,resolutions,absent,lock)
    terminal=json.loads((SCOPED_RUN/'terminal.json').read_bytes())
    require(inventory(SCOPED_RUN,('terminal.json',))==terminal['available_evidence'],
            'Scoped diagnostic artifact inventory changed')
    expected={str(Path(path).relative_to(SCOPED_JOB)) for path in pins if Path(path).is_relative_to(SCOPED_JOB)}
    require(set(inventory(SCOPED_JOB))==expected,'Scoped durable artifact inventory changed')
    lock_identity(lock)


def retained_scoped_success(pins):
    values={path:document(path,digest,pins) for path,digest in SCOPED_FIXED.items()}
    plan=values[SCOPED/'plan-v1.json'];report=values[SCOPED_RUN/'report.json']
    terminal=values[SCOPED_RUN/'terminal.json'];closure=values[SCOPED/'actual-closure-v1.json']
    durable=values[SCOPED_JOB/'terminal.json']
    review=document(OWNERSHIP_REVIEW,OWNERSHIP_REVIEW_SHA,pins)
    require(review['status']=='two-actual-diagnostics-independently-reviewed' and
        review['native_diagnostic_syntax_qualified'] is review['bounded_allocation_ownership_qualified'] is True and
        review['control_deltas']==[0,0,0,0,0,0] and review['allocation_deltas']==[1,2,9,2,1,0] and
        review['checks']==[1,1,7] and review['whole_subject_n4_n10_unstarted'] is True and
        all(review[k] is False for k in ('source_work_qualified','canonical_source_count_qualified',
                                       'full_timing_qualified','chart_admission','memory_usage_qualified')),
        'Independent bounded ownership disposition changed')
    for name,digest in review['inputs'].items():
        path=Path(name)
        require(not path.is_absolute() and '..' not in path.parts,'Invalid ownership review input path')
        pin(pins,ROOT/path,digest)
    for capture in review['captures']:
        pin(pins,ROOT/capture['source']['path'],capture['source']['sha256'])
    require(report['status']==terminal['status']==s.SUCCESS and
        report['native_processes_started']==terminal['native_processes_started']==terminal['capture_count']==2 and
        report['integrity_errors']==terminal['integrity_errors']==[] and
        report['attempted_commands']==[slot['directory'] for slot in plan['schedule']] and
        tuple(slot['id'] for slot in plan['schedule'])==s.IDS and len(report['captures'])==2 and
        all(report[k] is terminal[k] is False for k in FALSE_GATES),'Both scoped captures must have passed')
    require(terminal['report_sha256']==SCOPED_FIXED[SCOPED_RUN/'report.json'] and terminal['common_mutex_held'] is True,
            'Scoped terminal binding changed')
    require(closure['status']=='closed-two-passed-diagnostic-captures-awaiting-independent-review' and
        closure['plan_sha256']==SCOPED_FIXED[SCOPED/'plan-v1.json'] and
        closure['report_sha256']==SCOPED_FIXED[SCOPED_RUN/'report.json'] and
        closure['terminal_sha256']==SCOPED_FIXED[SCOPED_RUN/'terminal.json'] and
        closure['durable_terminal_sha256']==SCOPED_FIXED[SCOPED_JOB/'terminal.json'] and
        closure['whole_subject_n4_n10_unstarted'] is True,'Scoped closure changed')
    require(durable['status']=='command-exited-zero-awaiting-report-review' and durable['exit_code']==0 and
        durable['command_pid']==29825 and durable['actual_command_started'] is True and durable['stop_signals']==[] and
        durable['automatic_retry'] is durable['qualification_granted'] is False,'Scoped durable closure changed')
    require(inventory(SCOPED_RUN,('terminal.json',))==terminal['available_evidence'],'Scoped raw artifacts changed')
    for name,entry in terminal['available_evidence'].items():pin(pins,SCOPED_RUN/name,entry['sha256'])
    for name,entry in inventory(SCOPED_JOB).items():pin(pins,SCOPED_JOB/name,entry['sha256'])
    require(report['pins']==dict(plan['pins'],**{str(SCOPED/'plan-v1.json'):SCOPED_FIXED[SCOPED/'plan-v1.json']}),
            'Scoped prerequisite closure changed')
    for path,digest in report['pins'].items():pin(pins,path,digest)
    captures=[]
    for slot,saved in zip(plan['schedule'],report['captures']):
        current,snapshot=checked_capture(slot,SCOPED_RUN/slot['directory'],durable['command_pid'],
                                        report['inherited_lock_descriptor'],plan['configuration_pattern'])
        require(current==saved and snapshot==report['validated_artifacts'][slot['directory']],
                'Scoped capture disposition changed')
        captures.append(current)
    require(report['registered_commands']==[dict(directory=c['directory'],pid=c['pid']) for c in captures] and
        stamp(captures[0]['finished_at'])<=stamp(captures[1]['started_at']) and
        stamp(captures[1]['finished_at'])<=stamp(report['finished_at'])<=stamp(durable['finished_at']),
        'Scoped process ledger or nonoverlap changed')
    return dict(report=dict(path=str(SCOPED_RUN/'report.json'),sha256=SCOPED_FIXED[SCOPED_RUN/'report.json']),
        terminal=dict(path=str(SCOPED_RUN/'terminal.json'),sha256=SCOPED_FIXED[SCOPED_RUN/'terminal.json']),
        closure=dict(path=str(SCOPED/'actual-closure-v1.json'),sha256=SCOPED_FIXED[SCOPED/'actual-closure-v1.json']),
        bounded_ownership_review=dict(path=str(OWNERSHIP_REVIEW),sha256=OWNERSHIP_REVIEW_SHA),
        captures=captures,exact_bounded_outputs_verified=True,retained_native_observations=2,
        **{k:False for k in FALSE_GATES})


def build_plan(output):
    require(output.is_relative_to(PACKET) and output!=PACKET and not output.exists(),'Fresh small-subject output required')
    plan=b.build_plan(output);pins=plan['pins']
    for path,digest in ((PRIOR,PRIOR_SHA),(s.PRIOR,s.PRIOR_SHA),(r.BASE,r.BASE_SHA)):pin(pins,path,digest)
    prefix=dict(configuration_and_readback=r.retained_prefix(pins),failed_allocation=s.retained_allocation_failure(pins),
                scoped_diagnostics=retained_scoped_success(pins))
    for path in (Path(__file__).resolve(),Path(__file__).with_name('test_apl_workspace_subject.py'),PACKET/'README.md'):
        pin(pins,path)
    schedule=plan['schedule'][3:]
    require(tuple(slot['id'] for slot in schedule)==IDS and
        [slot['timeout_seconds'] for slot in schedule]==[30,60],'Only original N4/N10 slots are allowed')
    plan.update(schema='apl-workspace-small-subject-plan-v1',controller=str(Path(__file__).resolve()),
        controller_sha256=sha(__file__),retained_prefix=prefix,schedule=schedule,native_commands=2,
        retained_native_observations=5,full_size_timing_scheduled=False,
        **{k:False for k in FALSE_GATES})
    # Original slot directory names are indexed; only their future HOME paths disappear.
    unused=[str(output/name)+'/' for name in ('00-configuration','01-workspace-readback','02-allocation-ownership')]
    plan['absent_inputs']=[name for name in plan['absent_inputs'] if not any(name.startswith(p) for p in unused)]
    plan['input_resolutions']={name:str(Path(name).resolve()) for name in pins}
    return plan


def finish(report, plan, output, pins, resolutions, lock):
    errors=[];available={};held=False
    try:
        verify(pins,resolutions,plan['absent_inputs'],lock);held=True
        entries,attempts=report['registered_commands'],report['attempted_commands']
        require(attempts == [s['directory'] for s in plan['schedule'][:len(attempts)]] and len(attempts) <= 2,
                'Attempt sequence contains a retry, omission or extra command')
        require(len(entries) == report['native_processes_started'] <= len(attempts) and
                [e['directory'] for e in entries] == attempts[:len(entries)] and
                len({e['pid'] for e in entries}) == len(entries),'Native registration differs')
        receipts={str(p.relative_to(output)) for p in output.glob('*/process.json')}
        require(receipts == {d+'/process.json' for d in attempts},'Native receipt inventory differs')
        for directory in attempts:
            record=json.loads((output/directory/'process.json').read_bytes())
            expected=next((e for e in entries if e['directory'] == directory),None)
            require(record['cleanup_errors'] == [] and not record.get('artifact_errors'),'Native cleanup/artifact failure')
            if expected:
                require(record['native_process_started'] is True and record['pid'] == expected['pid'] and
                        record['direct_child_reaped'] is True and record.get('remaining_process_group',[]) ==
                        record.get('remaining_after_cleanup',[]) == [],'Owned native not reaped or group survived')
            else:require(record['native_process_started'] is False and not record.get('pid'),'Unregistered native process')
        for slot,capture in zip(plan['schedule'],report['captures']):
            current,snapshot=checked_capture(slot,output/slot['directory'],os.getpid(),report['inherited_lock_descriptor'],plan['configuration_pattern'])
            require(current == capture and snapshot == report['validated_artifacts'][slot['directory']],'Validated capture changed')
        require(len(report['captures']) == len(report['validated_artifacts']),'Capture snapshot inventory differs')
        for previous,current in zip(report['captures'],report['captures'][1:]):
            require(stamp(previous['finished_at']) <= stamp(current['started_at']),'Bounded native commands overlapped')
        if report['status'] == SUCCESS:
            require(len(report['captures']) == len(entries) == len(attempts) == 2,'Incomplete two-command stage')
        available=inventory(output,('report.json','terminal.json'))
        for directory,snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')} == snapshot,
                    'Final inventory adopted changed validated bytes')
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,artifacts=available)
    if errors:report['status']='failed-integrity'
    expected_report=(json.dumps(report,indent=2)+'\n').encode('utf-8')
    kb.save(output/'report.json',report)
    try:
        closure=inventory(output,('terminal.json',))
        require({n:v for n,v in closure.items() if n != 'report.json'} == available,'Final artifact closure changed')
        require(closure['report.json'] == dict(bytes=len(expected_report),sha256=hashlib.sha256(expected_report).hexdigest()),
                'Final report differs from validated ledger bytes')
        held=False;verify(pins,resolutions,plan['absent_inputs'],lock);held=True
        require(inventory(output,('terminal.json',)) == closure,'Artifact/report changed during final input replay')
        held=False;lock_identity(lock);held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={}
        kb.save(output/'report.json',report)
    terminal=dict(schema='apl-workspace-small-subject-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),available_evidence=closure,integrity_errors=errors,
        native_processes_started=report['native_processes_started'],capture_count=len(report['captures']),
        common_mutex_held=held,inherited_lock_descriptor=report['inherited_lock_descriptor'],
        common_mutex_inode=kb.LOCK_INODE,sampler_processes=0,benchmark_samples=0,
        **{k:False for k in FALSE_GATES})
    with (output/'terminal.json').open('x') as stream:stream.write(json.dumps(terminal,indent=2)+'\n')


def run_plan(plan, plan_path, plan_sha, lock):
    output=Path(plan['output']);pins=dict(plan['pins']);pin(pins,plan_path,plan_sha)
    resolutions=dict(plan['input_resolutions'],**{str(plan_path):str(plan_path.resolve())})
    inherited=lock_identity(lock);verify(pins,resolutions,plan['absent_inputs'],lock)
    output.mkdir(parents=True,exist_ok=False)
    report=dict(schema='apl-workspace-small-subject-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        controller_sha256=sha(__file__),retained_prefix=plan['retained_prefix'],retained_native_observations=5,pins=pins,input_resolutions=resolutions,absent_inputs=plan['absent_inputs'],
        inherited_lock_descriptor=inherited,started_at=datetime.now(timezone.utc).isoformat(),active=None,
        attempted_commands=[],registered_commands=[],native_processes_started=0,captures=[],validated_artifacts={},
        sampler_processes=0,benchmark_samples=0,**{k:False for k in FALSE_GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            verify(pins,resolutions,plan['absent_inputs'],lock)
            directory=output/slot['directory'];directory.mkdir()
            for name in ('home','tmp'):(directory/name).mkdir()
            with kb.atomic():
                report['attempted_commands'].append(slot['directory']);kb.save(output/'report.json',report)
            def launched(pid):
                report['native_processes_started']+=1
                report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
                report['active']=dict(directory=slot['directory'],pid=pid);kb.save(output/'report.json',report)
            observe(slot,directory,lock,launched,plan['configuration_pattern'])
            capture,snapshot=checked_capture(slot,directory,os.getpid(),inherited,plan['configuration_pattern'])
            with kb.atomic():
                report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
                report['active']=None;kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
    finally:
        with kb.atomic():finish(report,plan,output,pins,resolutions,lock)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run');run.add_argument('--plan',type=Path,required=True);run.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();physical(args.plan);require(args.plan.is_relative_to(PACKET),'Plan outside small-subject packet')
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize and
            Path(sys.executable).resolve() == kb.kh.PYTHON.resolve(),'Use exact retained Python -I -S -B without -O')
    def interrupted(signum,frame):raise KeyboardInterrupt('APL bounded stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    with held_mutex() as lock:
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA,'Retained Python changed')
        if args.mode == 'prepare':
            require(not args.plan.exists() and not args.plan.is_relative_to(args.output),'Fresh external plan required')
            plan=build_plan(args.output);verify(plan['pins'],plan['input_resolutions'],plan['absent_inputs'],lock)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('x') as stream:stream.write(json.dumps(plan,indent=2)+'\n')
            print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes_started=0)));return 0
        plan=document(args.plan,args.plan_sha256,{})
        require(plan == build_plan(Path(plan['output'])),'Concrete prepared plan differs')
        report=run_plan(plan,args.plan,args.plan_sha256,lock)
    print(json.dumps(dict(status=report['status'],captures=len(report['captures']),report_sha256=sha(Path(plan['output'])/'report.json'))))
    return 0 if report['status'] == SUCCESS else 1


if __name__ == '__main__':raise SystemExit(main())
