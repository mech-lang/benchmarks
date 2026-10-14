"""Two scope-isolated APL ownership diagnostics; no subject timings or admission."""
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
PACKET=ORIGINAL/'scope-isolated-v1'
PRIOR=ROOT/'tools/qualification/apl_workspace_remaining.py'
PRIOR_SHA='4c91295dac29ecdbf586e49270f3f72356252572e968490ede2974a2c7e50fc1'
FAILED_PACKET=ORIGINAL/'remaining-three-v1'
FAILED_RUN=FAILED_PACKET/'run-v1'
FAILED_JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/apl-workspace-remaining3-v1'
FAILED_FIXED={
    FAILED_PACKET/'plan-v1.json':'bfab7d2e1ad45b5482c6531f03a6aa072ce818e4de9e6f6bd1f6ddb8f1620a70',
    FAILED_RUN/'report.json':'98a72540c56d68d8ef45c51aa77d4b8c6054ed2513396a1504d0bd85e27b210b',
    FAILED_RUN/'terminal.json':'ad1903c45720afb638a81db57bf5917711818465c0e80418520acf9387397be0',
    FAILED_PACKET/'actual-closure-v1.json':'846ecf32bbe84cec09670b418d12b1fc8f8f21dd012a6fea5185bb7a645669c6',
    FAILED_JOB/'terminal.json':'30a452504b742f3d562473043efc50f0f64a1320d68cd866b3a2a57dfe7fddf1',
}
SOURCE_PINS={
    'allocation.apl':'2248159002ddacb173726426e66d1751c84d8b872116b4ee343f826d34a3773b',
    'zero-allocation-control.apl':'a714403553dda1299e19f252e460d86cd948ffa4c7988cd26cd0de40bdfe0e5c',
    'test_source_contract.py':'c59606e230fe97bd4b929b07686e37c355189070bb7c96674fd6e5dea102959d',
    'README.md':'491b3a5f937e55ae7e7d8be3d78c5e86693366d88c02a81c54c09143be0b87d3',
    'source-review.json':'c6010b5aadec7f376e0603dbd057c0938c30138ae232cd02f570fbac17e718d9',
    'independent-source-review-v1.json':'62560ceb8e549d4cdb8447102ea30ef50c0132707edd2a90f60a1add1fe522ae',
}
IDS=('zero-allocation-control','scope-isolated-allocation')
FILES=('zero-allocation-control.apl','allocation.apl')
EXPECTED=('control_deltas=0,0,0,0,0,0\nchecks=1,1,7\n',
          'live_deltas=1,2,9,2,1,0\nchecks=1,1,7\n')
SUCCESS='two-scope-isolated-captures-awaiting-independent-ownership-review'


def require(value,message):
    if not value:raise AssertionError(message)


raw=PRIOR.read_bytes()
require(hashlib.sha256(raw).hexdigest()==PRIOR_SHA,'Frozen prior controller changed')
spec=importlib.util.spec_from_file_location('apl_scoped_private_prior',PRIOR)
r=importlib.util.module_from_spec(spec);exec(compile(raw,str(PRIOR),'exec'),r.__dict__)
b,kb=r.b,r.kb
sha,physical,pin,document=r.sha,r.physical,r.pin,r.document
inventory,stamp=r.inventory,r.stamp
WARNING=r.WARNING
FALSE_GATES=b.FALSE_GATES+('native_syntax_qualified','allocation_ownership_qualified')
_failure_lease=None
_base_lock_identity=b.lock_identity


def check_output(slot,stdout,stderr,pattern):
    require(slot['id'] in IDS,'Only the two scope-isolated diagnostics are registered')
    require(len(stdout)<=b.FILE_LIMIT and len(stderr)<=b.FILE_LIMIT,'Stream exceeded 1MiB bound')
    require(slot['expected_stdout_utf8']==EXPECTED[IDS.index(slot['id'])],'Diagnostic oracle changed')
    require(stderr==WARNING,'Unexpected APL stderr; exact shutdown diagnostic required')
    require(stdout==slot['expected_stdout_utf8'].encode(),'Exact scope-isolated output mismatch')
    return dict(exact_output=True,exact_shutdown_diagnostic=True,
        stderr_bytes=len(stderr),stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        diagnostic_review=dict(path=str(r.DIAGNOSTIC),sha256=r.DIAGNOSTIC_SHA),
        source_review=dict(path=str(PACKET/'source-review.json'),sha256=SOURCE_PINS['source-review.json']))


def lock_identity(lock):
    inherited=_base_lock_identity(lock)
    for held,path,inode in ((r._prior_lease,r.OLD_JOB/'owner.lock',82370343),
                            (_failure_lease,FAILED_JOB/'owner.lock',82374025)):
        if held is not None:
            fd,named=os.fstat(held.fileno()),path.stat()
            require((fd.st_dev,fd.st_ino)==(named.st_dev,named.st_ino) and fd.st_ino==inode,
                    'Retained durable lease changed: '+str(path))
    return inherited


# Private instances only: preserve all native supervision and capture code.
b.check_output=check_output
b.lock_identity=lock_identity
observe,checked_capture=b.observe,b.checked_capture


@contextmanager
def held_mutex():
    global _failure_lease
    require(_failure_lease is None,'Nested retained lease ownership')
    with r.held_mutex() as lock,(FAILED_JOB/'owner.lock').open('rb') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        _failure_lease=lease
        try:
            lock_identity(lock)
            yield lock
        finally:
            try:lock_identity(lock)
            finally:_failure_lease=None


def verify(pins,resolutions,absent,lock):
    require(r._prior_lease is not None and _failure_lease is not None,'Both retained leases required')
    r.verify(pins,resolutions,absent,lock)
    terminal=json.loads((FAILED_RUN/'terminal.json').read_bytes())
    require(inventory(FAILED_RUN,('terminal.json',))==terminal['available_evidence'],
            'Failed allocation evidence inventory changed')
    expected={str(Path(path).relative_to(FAILED_JOB)) for path in pins if Path(path).is_relative_to(FAILED_JOB)}
    require(set(inventory(FAILED_JOB))==expected,'Failed allocation durable inventory changed')
    lock_identity(lock)


def retained_allocation_failure(pins):
    values={path:document(path,digest,pins) for path,digest in FAILED_FIXED.items()}
    old=values[FAILED_PACKET/'plan-v1.json'];report=values[FAILED_RUN/'report.json']
    terminal=values[FAILED_RUN/'terminal.json'];closure=values[FAILED_PACKET/'actual-closure-v1.json']
    durable=values[FAILED_JOB/'terminal.json']
    require(report['status']==terminal['status']=='failed' and
        report['error']=='Exact bounded APL output mismatch' and report['error_type']=='AssertionError' and
        report['native_processes_started']==1 and report['captures']==[] and report['validated_artifacts']=={} and
        report['attempted_commands']==['02-allocation-ownership'] and
        report['registered_commands']==[dict(directory='02-allocation-ownership',pid=22296)] and
        report['integrity_errors']==terminal['integrity_errors']==[],'Retained failed allocation result changed')
    require(terminal['report_sha256']==FAILED_FIXED[FAILED_RUN/'report.json'] and
        terminal['native_processes_started']==1 and terminal['capture_count']==0 and
        terminal['common_mutex_held'] is True,'Retained failed terminal changed')
    require(closure['status']=='closed-failed-allocation-release-count-mismatch' and
        closure['plan_sha256']==FAILED_FIXED[FAILED_PACKET/'plan-v1.json'] and
        closure['report_sha256']==FAILED_FIXED[FAILED_RUN/'report.json'] and
        closure['terminal_sha256']==FAILED_FIXED[FAILED_RUN/'terminal.json'] and
        closure['durable_terminal_sha256']==FAILED_FIXED[FAILED_JOB/'terminal.json'] and
        closure['remaining_commands_unstarted']==['whole-subject-n4','whole-subject-n10'] and
        closure['new_capture_qualified'] is False,'Retained failed closure changed')
    require(durable['status']=='command-failed' and durable['exit_code']==1 and durable['command_pid']==22294 and
        durable['actual_command_started'] is True and durable['stop_signals']==[] and
        durable['automatic_retry'] is durable['qualification_granted'] is False,'Retained durable outcome changed')
    require(inventory(FAILED_RUN,('terminal.json',))==terminal['available_evidence'],'Failed allocation artifacts changed')
    for name,entry in terminal['available_evidence'].items():pin(pins,FAILED_RUN/name,entry['sha256'])
    for name,entry in inventory(FAILED_JOB).items():pin(pins,FAILED_JOB/name,entry['sha256'])
    require(report['pins']==dict(old['pins'],**{str(FAILED_PACKET/'plan-v1.json'):FAILED_FIXED[FAILED_PACKET/'plan-v1.json']}),
            'Failed allocation prerequisites changed')
    for path,digest in report['pins'].items():pin(pins,path,digest)
    directory=FAILED_RUN/'02-allocation-ownership';process=json.loads((directory/'process.json').read_bytes())
    require(process['status']=='failed' and process['exit_status']==0 and process['direct_child_reaped'] is True and
        process['remaining_process_group']==process.get('remaining_after_cleanup',[])==[] and
        process['cleanup_errors']==process['stop_signals']==[] and process.get('output_validation') is None and
        process['error']==report['error'] and process['error_type']=='AssertionError',
        'Retained failed process disposition changed')
    stdout=(directory/'stdout.bin').read_bytes();stderr=(directory/'stderr.bin').read_bytes()
    require(stdout==b'checks=1,1,7\nlive_deltas=1,2,9,4,2,1\n' and stderr==WARNING,
            'Retained failure raw bytes changed')
    for name,data in (('stdout',stdout),('stderr',stderr)):
        require(process[name+'_bytes']==len(data) and process[name+'_sha256']==hashlib.sha256(data).hexdigest(),
                'Retained failure stream binding changed')
    return dict(original_producer_status='failed',original_error=report['error'],qualified=False,
        report=dict(path=str(FAILED_RUN/'report.json'),sha256=FAILED_FIXED[FAILED_RUN/'report.json']),
        terminal=dict(path=str(FAILED_RUN/'terminal.json'),sha256=FAILED_FIXED[FAILED_RUN/'terminal.json']),
        closure=dict(path=str(FAILED_PACKET/'actual-closure-v1.json'),sha256=FAILED_FIXED[FAILED_PACKET/'actual-closure-v1.json']),
        retained_native_observations=1,whole_subject_n4_n10_unstarted=True)


def build_plan(output):
    require(output.is_relative_to(PACKET) and output!=PACKET and not output.exists(),'Fresh scope-isolated output required')
    plan=b.build_plan(output);pins=plan['pins'];pin(pins,PRIOR,PRIOR_SHA);pin(pins,r.BASE,r.BASE_SHA)
    prefix=dict(configuration_and_readback=r.retained_prefix(pins),failed_allocation=retained_allocation_failure(pins))
    diagnostic=document(r.DIAGNOSTIC,r.DIAGNOSTIC_SHA,pins)
    require(diagnostic['exact_stderr_utf8'].encode()==WARNING and diagnostic['original_failure_preserved'] is True,
            'Shutdown diagnostic review changed')
    for ref in diagnostic['retained_runtime_source_evidence']:pin(pins,ref['path'],ref['sha256'])
    for name,digest in SOURCE_PINS.items():pin(pins,PACKET/name,digest)
    proof=document(PACKET/'source-review.json',SOURCE_PINS['source-review.json'],pins)
    require(proof['expected_stdout']==dict(zip(FILES,EXPECTED)) and proof['new_native_processes']==0,
            'Scope-isolated source oracle changed')
    for ref in proof['retained_runtime_source_evidence']:pin(pins,ref['path'],ref['sha256'])
    for path in (Path(__file__).resolve(),Path(__file__).with_name('test_apl_workspace_scoped.py'),PACKET/'controller-README.md'):
        pin(pins,path)
    template=plan['schedule'][2]
    schedule=[]
    for index,(identity,name,stdout) in enumerate(zip(IDS,FILES,EXPECTED)):
        slot=dict(template,id=identity,directory=f'{index:02}-'+identity,expected_stdout_utf8=stdout)
        slot['argv']=template['argv'][:-1]+[str(PACKET/name)]
        require(slot['argv'][-2]=='-f' and slot['timeout_seconds']==30,'Diagnostic launch template changed')
        schedule.append(slot)
    plan.update(schema='apl-workspace-scope-isolated-plan-v1',controller=str(Path(__file__).resolve()),
        controller_sha256=sha(__file__),retained_prefix=prefix,schedule=schedule,native_commands=2,
        retained_native_observations=3,retained_config_readback_observations=2,retained_failed_allocation_observations=1,
        diagnostic_review=dict(path=str(r.DIAGNOSTIC),sha256=r.DIAGNOSTIC_SHA),
        whole_subject_n4_n10_scheduled=False,**{k:False for k in FALSE_GATES})
    absent={name for name in plan['absent_inputs'] if not Path(name).is_relative_to(output)}
    source_spec=json.loads(Path(plan['specification']['path']).read_bytes())
    prefix_path=Path(source_spec['runtime_binary']['path']).resolve().parent.parent
    for path in b.preference_paths(prefix_path,[output/s['directory'] for s in schedule]):
        if path.is_file():pin(pins,path)
        else:
            require(not os.path.lexists(path),'Nonregular or dangling APL preference path')
            absent.add(str(path))
    plan['absent_inputs']=sorted(absent)
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
    terminal=dict(schema='apl-workspace-scope-isolated-terminal-v1',status=report['status'],
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
    report=dict(schema='apl-workspace-scope-isolated-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        controller_sha256=sha(__file__),retained_prefix=plan['retained_prefix'],retained_native_observations=3,pins=pins,input_resolutions=resolutions,absent_inputs=plan['absent_inputs'],
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
    args=parser.parse_args();physical(args.plan);require(args.plan.is_relative_to(PACKET),'Plan outside scope-isolated packet')
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
