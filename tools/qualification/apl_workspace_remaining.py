"""Three remaining GNU APL checks, retaining the two original observations.

The frozen observer is loaded privately. Only its exact output contract changes;
all process ownership, limits, high-FD mutex and raw stream retention remain.
"""
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
PACKET=ORIGINAL/'remaining-three-v1'
OLD_RUN=ORIGINAL/'bounded-run-v1'
OLD_JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/apl-workspace-bounded5-v1'
BASE=ROOT/'tools/qualification/apl_workspace_bounded.py'
BASE_SHA='21a134b4c6076c0ce3418b773cd40ad246998c6928972d8e6f9c066c04a07be0'
DIAGNOSTIC=PACKET/'shutdown-diagnostic-review-v1.json'
DIAGNOSTIC_SHA='7fd4ddbf576db0b76da43e03ec5a1c571597e8e3e2bd0ce1efa684d30360237b'
FIXED={ORIGINAL/'plan-v1.json':'c3866a8255d53f63336aed8f2e6407e723ebb7a0483b4ddc760277af13e146a1',
 OLD_RUN/'report.json':'daff19879de9ab9e7b30574a29195224340b24a9f7b3e080baa0b5f539335388',
 OLD_RUN/'terminal.json':'01c3dba06b9ea287b1e5b63ea58ff787405ed1498732bf0535f2274a6d70223d',
 ORIGINAL/'actual-closure-v1.json':'de4992290f1eb11adadde7ad325a6f3f6e6b4d4ae912f714ef4b83b953bde33c',
 OLD_JOB/'terminal.json':'312c460d1ceb91976bfbd80982efb3e9e7ff21517718760e29f51451c7874ab8'}
WARNING=b'\nWARNING: File pipe-to_client still open - closing it\n'
SUCCESS='three-remaining-bounded-captures-plus-two-retained-awaiting-work-review'
IDS=('allocation-ownership','whole-subject-n4','whole-subject-n10')


def require(value,message):
    if not value:raise AssertionError(message)


raw=BASE.read_bytes()
require(hashlib.sha256(raw).hexdigest()==BASE_SHA,'Frozen observer/controller changed')
spec=importlib.util.spec_from_file_location('apl_frozen_private_observer',BASE)
b=importlib.util.module_from_spec(spec);exec(compile(raw,str(BASE),'exec'),b.__dict__)
kb=b.kb
sha,physical,pin,document=b.sha,b.physical,b.pin,b.document
inventory,stamp=b.inventory,b.stamp
_prior_lease=None
FALSE_GATES=b.FALSE_GATES
_original_output=b.check_output


def check_output(slot,stdout,stderr,pattern):
    if slot['id']=='configuration':return _original_output(slot,stdout,stderr,pattern)
    require(slot['id'] in ('workspace-readback',)+IDS,'Unregistered shutdown diagnostic context')
    require(len(stdout)<=b.FILE_LIMIT and len(stderr)<=b.FILE_LIMIT,'Stream exceeded 1MiB bound')
    require(stderr==WARNING,'Unexpected APL stderr; exact shutdown diagnostic required')
    require(stdout==slot['expected_stdout_utf8'].encode(),'Exact bounded APL output mismatch')
    return dict(exact_output=True,exact_shutdown_diagnostic=True,
        stderr_bytes=len(stderr),stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        diagnostic_review=dict(path=str(DIAGNOSTIC),sha256=DIAGNOSTIC_SHA))


# This private module's functions resolve the new exact output policy. No source
# or shared module instance is modified; all observer/lifecycle code is frozen.
b.check_output=check_output
observe,checked_capture=b.observe,b.checked_capture


def lock_identity(lock):
    inherited=b.lock_identity(lock)
    if _prior_lease is not None:
        held,named=os.fstat(_prior_lease.fileno()),(OLD_JOB/'owner.lock').stat()
        require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino) and held.st_ino==82370343,
                'Original durable lease changed')
    return inherited


@contextmanager
def held_mutex():
    global _prior_lease
    require(_prior_lease is None,'Nested retained lease ownership')
    with b.held_mutex() as lock, (OLD_JOB/'owner.lock').open('rb') as prior:
        fcntl.flock(prior,fcntl.LOCK_EX|fcntl.LOCK_NB)
        _prior_lease=prior
        try:
            lock_identity(lock)
            yield lock
        finally:
            try:lock_identity(lock)
            finally:_prior_lease=None


def verify(pins,resolutions,absent,lock):
    lock_identity(lock)
    b.verify(pins,resolutions,absent,lock)
    lock_identity(lock)
    old=json.loads((OLD_RUN/'terminal.json').read_bytes())
    require(inventory(OLD_RUN,('terminal.json',))==old['available_evidence'],'Original failed evidence inventory changed')
    expected={str(Path(path).relative_to(OLD_JOB)) for path in pins if Path(path).is_relative_to(OLD_JOB)}
    require(set(inventory(OLD_JOB))==expected,'Original durable artifact inventory changed')
    lock_identity(lock)


def retained_prefix(pins):
    values={path:document(path,digest,pins) for path,digest in FIXED.items()}
    old=values[ORIGINAL/'plan-v1.json'];report=values[OLD_RUN/'report.json'];terminal=values[OLD_RUN/'terminal.json']
    closure=values[ORIGINAL/'actual-closure-v1.json'];durable=values[OLD_JOB/'terminal.json']
    require(report['status']==terminal['status']=='failed' and report['error']=='Unknown APL stderr; complete raw bytes retained'
        and report['error_type']=='AssertionError' and report['native_processes_started']==2 and len(report['captures'])==1
        and report['integrity_errors']==terminal['integrity_errors']==[],'Original failed result differs')
    require(terminal['report_sha256']==FIXED[OLD_RUN/'report.json'] and terminal['native_processes_started']==2
        and terminal['capture_count']==1 and terminal['common_mutex_held'] is True,'Original terminal differs')
    require(closure['status']=='closed-failed-readback-shutdown-diagnostic' and closure['remaining_commands_unstarted']==3
        and closure['plan_sha256']==FIXED[ORIGINAL/'plan-v1.json'] and closure['report_sha256']==FIXED[OLD_RUN/'report.json']
        and closure['terminal_sha256']==FIXED[OLD_RUN/'terminal.json']
        and closure['durable_terminal_sha256']==FIXED[OLD_JOB/'terminal.json'],'Original closure differs')
    require(durable['status']=='command-failed' and type(durable['exit_code']) is int and durable['exit_code']==1
        and durable['actual_command_started'] is True and durable['stop_signals']==[]
        and durable['automatic_retry'] is durable['qualification_granted'] is False,'Original durable exit differs')
    require(report['attempted_commands']==[s['directory'] for s in old['schedule'][:2]]
        and [r['directory'] for r in report['registered_commands']]==report['attempted_commands'],'Original attempted prefix differs')
    require(inventory(OLD_RUN,('terminal.json',))==terminal['available_evidence'],'Original terminal artifacts changed')
    for name,entry in terminal['available_evidence'].items():pin(pins,OLD_RUN/name,entry['sha256'])
    for name,entry in inventory(OLD_JOB).items():pin(pins,OLD_JOB/name,entry['sha256'])
    for path,digest in report['pins'].items():pin(pins,path,digest)
    require(report['pins']==dict(old['pins'],**{str(ORIGINAL/'plan-v1.json'):FIXED[ORIGINAL/'plan-v1.json']}),
        'Original prerequisite closure differs')
    captures=[]
    for slot in old['schedule'][:2]:
        captures.append(retained_capture(slot,OLD_RUN/slot['directory'],durable['command_pid'],
                                        report['inherited_lock_descriptor'],old['configuration_pattern'])[0])
    require([c['pid'] for c in captures]==[e['pid'] for e in report['registered_commands']],'Original PID ledger differs')
    require(stamp(captures[0]['finished_at'])<=stamp(captures[1]['started_at'])<=stamp(captures[1]['finished_at'])
            <=stamp(durable['finished_at']),'Original processes overlapped or durable closure preceded exit')
    return dict(original_status='failed',original_report=dict(path=str(OLD_RUN/'report.json'),sha256=FIXED[OLD_RUN/'report.json']),
        original_terminal=dict(path=str(OLD_RUN/'terminal.json'),sha256=FIXED[OLD_RUN/'terminal.json']),
        closure=dict(path=str(ORIGINAL/'actual-closure-v1.json'),sha256=FIXED[ORIGINAL/'actual-closure-v1.json']),
        retained_native_observations=2,captures=captures,original_producer_failure_preserved=True,
        diagnostic_review=dict(path=str(DIAGNOSTIC),sha256=DIAGNOSTIC_SHA),**{k:False for k in FALSE_GATES})


def build_plan(output):
    require(output.is_relative_to(PACKET) and output!=PACKET and not output.exists(),'Fresh continuation output required')
    plan=b.build_plan(output);pins=plan['pins'];pin(pins,BASE,BASE_SHA);prefix=retained_prefix(pins)
    diagnostic=document(DIAGNOSTIC,DIAGNOSTIC_SHA,pins)
    require(diagnostic['exact_stderr_utf8'].encode()==WARNING and diagnostic['original_failure_preserved'] is True,
            'Exact diagnostic disposition differs')
    for ref in diagnostic['retained_runtime_source_evidence']:pin(pins,ref['path'],ref['sha256'])
    for path in (Path(__file__).resolve(),Path(__file__).with_name('test_apl_workspace_remaining.py'),PACKET/'README.md'):pin(pins,path)
    plan.update(schema='apl-workspace-three-remaining-plan-v1',controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),
        retained_prefix=prefix,schedule=plan['schedule'][2:],native_commands=3,retained_native_observations=2,
        diagnostic_review=dict(path=str(DIAGNOSTIC),sha256=DIAGNOSTIC_SHA))
    require(tuple(s['id'] for s in plan['schedule'])==IDS,'Wrong remaining command scope')
    # Preserve static missing-library candidates and only the three new HOME trees.
    unused=[str(output/('00-configuration'))+'/',str(output/('01-workspace-readback'))+'/']
    plan['absent_inputs']=[p for p in plan['absent_inputs'] if not any(p.startswith(x) for x in unused)]
    plan['input_resolutions']={name:str(Path(name).resolve()) for name in pins}
    return plan


def retained_capture(slot, directory, parent, inherited, pattern):
    start,active,final=[json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start,active,final):
        require(record['command'] == slot['argv'] and record['environment'] == b.environment(directory) and
            record['cwd'] == slot['cwd'] and record['artifact_directory'] == str(directory) and
            record['kind'] == b.KIND and record['started_at'] == start['started_at'] and
            record['stdin_bytes'] == 0 and record['stdin_sha256'] == b.EMPTY_SHA and record['stdin_transport'] == 'DEVNULL' and
            record['inherited_common_mutex'] is True and record['inherited_lock_descriptor'] == inherited and
            type(inherited['fd']) is int and inherited['fd'] >= 64 and inherited['inode'] == kb.LOCK_INODE and
            record['common_mutex_inode'] == kb.LOCK_INODE and record['sampler_processes'] == 0 and
            record['process_timeout_seconds'] == slot['timeout_seconds'] and record['cleanup_timeout_seconds'] == 5 and
            record['maximum_process_group_rss_bytes'] == b.RSS_LIMIT and record['native_file_limit_bytes'] == b.FILE_LIMIT and
            record['stdout_capture_limit_bytes'] == b.FILE_LIMIT+kb.PIPE_CHUNK and
            record['stdout_transport'] == 'OS pipe, retained as received' and record['stderr_transport'] == 'exclusive artifact' and
            record['benchmark_samples'] == 0 and record['source_work_qualified'] is record['chart_admission'] is False,
            'Native launch contract differs')
    identity,leader,pid=final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status'] == 'starting' and start['native_process_started'] is False and
        active['status'] == 'running' and active['native_process_started'] is active['child_setup_verified'] is True and
        final['native_process_started'] is final['child_setup_verified'] is True and active['identity'] == identity and
        type(parent) is int and parent > 0 and identity['ppid'] == parent and
        all(type(identity[k]) is int and identity[k] == leader[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds')) and
        type(pid) is int and pid > 0 and active['pid'] == active['pgid'] == pid == final['pgid'] == identity['pid'] == identity['pgid'] and
        leader['status'] == 5 and final['direct_child_reaped'] is True and
        final['remaining_process_group'] == final.get('remaining_after_cleanup',[]) == [] and
        final['stop_signals'] == final['cleanup_errors'] == [] and not final.get('artifact_errors') and
        not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False and
        final['status'] == ('failed' if slot['id']=='workspace-readback' else 'native-passed') and type(final['exit_status']) is int and final['exit_status'] == 0 and
        (final.get('error') == 'Unknown APL stderr; complete raw bytes retained' and final.get('error_type') == 'AssertionError' if slot['id']=='workspace-readback' else not final.get('error') and not final.get('error_type')) and
        type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples'] > 0 and
        stamp(start['started_at']) <= stamp(final['finished_at']), 'Native ownership or normal exit differs')
    peak=final['observed_peak_process_group_rss_bytes']
    require(final['rss_observation_complete'] is final['memory_usage_qualified'] is False and
            final['rss_monitoring_scope'] == 'Sampled live group RSS only; unobserved peaks are not proven below the guard.' and
            ((peak is None and final['live_rss_observation_obtained'] is False) or
             (type(peak) is int and 0 < peak <= b.RSS_LIMIT and final['live_rss_observation_obtained'] is True)),
            'RSS observation availability or scope differs')
    raw={}
    for name in ('stdout','stderr'):
        path=directory/(name+'.bin');raw[name]=path.read_bytes()
        require(len(raw[name]) == final[name+'_bytes'] and hashlib.sha256(raw[name]).hexdigest() == final[name+'_sha256'],
                'Captured stream changed')
    validation=check_output(slot,raw['stdout'],raw['stderr'],pattern)
    require((final.get('output_validation') is None if slot['id']=='workspace-readback' else final['output_validation']==validation),'Original output validation disposition differs')
    snapshot=inventory(directory)
    require(set(snapshot) == {'start.json','active.json','process.json','stdout.bin','stderr.bin'},'Unexpected native artifacts')
    return dict(id=slot['id'],directory=slot['directory'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        output_validation=validation,original_producer_status=final['status'],original_error=final.get('error'),process_sha256=snapshot['process.json']['sha256'],
        observed_peak_process_group_rss_bytes=peak,live_rss_observation_obtained=final['live_rss_observation_obtained'],
        rss_observation_complete=False,memory_usage_qualified=False,
        **{k:False for k in FALSE_GATES}),snapshot


def finish(report, plan, output, pins, resolutions, lock):
    errors=[];available={};held=False
    try:
        verify(pins,resolutions,plan['absent_inputs'],lock);held=True
        entries,attempts=report['registered_commands'],report['attempted_commands']
        require(attempts == [s['directory'] for s in plan['schedule'][:len(attempts)]] and len(attempts) <= 3,
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
            require(len(report['captures']) == len(entries) == len(attempts) == 3,'Incomplete three-command stage')
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
    terminal=dict(schema='apl-workspace-three-remaining-terminal-v1',status=report['status'],
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
    report=dict(schema='apl-workspace-three-remaining-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        controller_sha256=sha(__file__),retained_prefix=plan['retained_prefix'],retained_native_observations=2,pins=pins,input_resolutions=resolutions,absent_inputs=plan['absent_inputs'],
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
    args=parser.parse_args();physical(args.plan);require(args.plan.is_relative_to(PACKET),'Plan outside continuation packet')
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
