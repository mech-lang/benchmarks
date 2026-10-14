"""Capture only the missing unchanged pi main; raw diagnostics are not work admission."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import types

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'tools/qualification/typescript_single_entry.py'
BASE_SHA = '5d0e03c560fa0c55a3fcf31419a9748af5a27b1cb513e8115f8d9b1816c064b3'
raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA: raise AssertionError('Frozen capture controller changed')
s = types.ModuleType('typescript_original_capture'); s.__file__ = str(BASE)
exec(compile(raw, str(BASE), 'exec'), s.__dict__)
b, kb, require, sha, save, atomic = s.b, s.kb, s.require, s.sha, s.save, s.atomic
PACKET = s.PACKET
PRIOR_PINS = {
 'plan-v1.json':'6e5d6b72f86dcb46e2e759b70b9dd0e3a11f898472686bd9e33dccbd7e10f4ca',
 'run-v1/report.json':'4c23b5feb3d79812659d7e6d0c212467cd970294bf2264880de13bfd1a6dbf12',
 'run-v1/terminal.json':'d8fa860d2c1bb2e4a8d7788dc4197355b7755f727da0d1cc6443abddc799d8a1',
}
SUCCESS = 'missing-pi-raw-capture-retained-awaiting-output-and-work-review'
SLOT = dict(kind='subject', benchmark='pidigits', directory='00-pidigits')


def options():
    return s.diagnostic_options('pidigits') + ['--maglev-print-filter=calculatePi', '--no-maglev-print-feedback']


def closed_prior(pins):
    plan, report, terminal = [b.document(PACKET/n, h, pins) for n,h in PRIOR_PINS.items()]
    require(plan['controller_sha256'] == BASE_SHA and report['plan_sha256'] == PRIOR_PINS['plan-v1.json']
        and report['status'] == terminal['status'] == 'failed'
        and report['error_type'] == 'AssertionError'
        and report['error'] == 'Complete prescribed stdout absent after native diagnostics'
        and report['active'] is None and report['integrity_errors'] == terminal['integrity_errors'] == []
        and report['registered_commands'] == [{'directory':'00-capabilities','pid':174}, {'directory':'01-binarytrees','pid':175}]
        and report['native_processes_started'] == terminal['native_processes_started'] == 2
        and terminal['capture_count'] == len(report['captures']) == 1
        and terminal['report_sha256'] == PRIOR_PINS['run-v1/report.json']
        and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
        'Exact closed original diagnostic attempt required')
    for doc in (report, terminal):
        require(all(doc[k] is False for k in ('required_work_qualified','runtime_dependency_closure_qualified',
            'full_timings_qualified','chart_admission')) and doc['benchmark_samples'] == 0, 'Prior capture promoted unexpectedly')
    run = PACKET/'run-v1'
    actual = s.inventory(run, ('terminal.json',))
    require(actual == terminal['available_evidence'] and
        {n:v for n,v in actual.items() if n != 'report.json'} == report['artifacts'], 'Original raw closure changed')
    require({str(p.relative_to(run)) for p in run.glob('*/process.json')} ==
        {'00-capabilities/process.json','01-binarytrees/process.json'}, 'Original native receipt inventory differs')
    for n,rec in actual.items(): b.bind(pins,run/n,rec['sha256'])
    for path,digest in plan['pins'].items(): b.bind(pins,path,digest)
    receipts=[]
    for slot in plan['schedule'][:2]:
        directory=run/slot['directory']
        receipt,stdout,stderr=s.native_receipt(directory,s.command(plan,slot),b.environment(directory),160)
        require(stderr == b'', 'Original native stderr differs')
        receipts.append(receipt)
    require([x['pid'] for x in receipts] == [174,175] and
        b.stamp(receipts[0]['finished_at']) <= b.stamp(receipts[1]['started_at']), 'Original native order differs')
    result,parts=s.checked_capture(plan,plan['schedule'][0],run/'00-capabilities',160)
    require(result == report['captures'][0] and not parts, 'Retained capability capture differs')
    for directory,snapshot in report['validated_artifacts'].items():
        require({n[len(directory)+1:]:v for n,v in actual.items() if n.startswith(directory+'/')} == snapshot,
            'Prior validated snapshot differs')
    listing=(run/'00-capabilities/stdout.bin').read_text('utf-8')
    for flag in options():
        name=flag.split('=')[0].removeprefix('--no-').removeprefix('--')
        require(re.search(r'^  --'+re.escape(name)+r' \(',listing,re.M), 'Missing retained V8 option: '+name)
    require(re.search(r'^  --maglev-print-filter .*\n\s+type: string ',listing,re.M)
        and re.search(r'^  --maglev-print-feedback .*\n\s+type: bool ',listing,re.M), 'New diagnostic option types differ')
    return dict(plan=str(PACKET/'plan-v1.json'), plan_sha256=PRIOR_PINS['plan-v1.json'],
        report=str(run/'report.json'), report_sha256=PRIOR_PINS['run-v1/report.json'],
        terminal=str(run/'terminal.json'), terminal_sha256=PRIOR_PINS['run-v1/terminal.json'],
        preserved_native_processes=2, excluded_workloads=['binarytrees'], repeated_capability_processes=0,
        tree_native_exit_verified=True, tree_application_output_qualified=False, tree_required_work_qualified=False)


def command(plan):
    row=next(p for p in plan['compiled']['profiles'] if p['benchmark']=='pidigits')
    return [plan['compiled']['node']] + options() + [row['javascript']['path'],'10000']


def build_plan(output):
    plan=s.build_plan(output)
    pins=plan['pins']; prior=closed_prior(pins)
    for p in (Path(__file__).resolve(),Path(__file__).with_name('test_typescript_single_entry_remaining.py'),PACKET/'remaining-pi.md'):
        b.bind(pins,p,sha(p))
    b.bind(pins,BASE,BASE_SHA)
    plan.update(schema='typescript-missing-pi-raw-plan-v1', controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),
        schedule=[SLOT],diagnostic_options={'pidigits':options()},inputs={'pidigits':10000},
        native_processes=1,subject_main_invocations=1,prior_capture=prior,
        application_output_qualified=False,raw_capture_only=True,
        diagnostic_changes=['--maglev-print-filter=calculatePi','--no-maglev-print-feedback'],
        diagnostic_scheduling_effect='V8 reports concurrent Maglev disabled for tracing; this is not a timing sample')
    plan['command']=command(plan)
    return plan


def checked_capture(plan, directory, parent):
    native,stdout,stderr=s.native_receipt(directory,command(plan),b.environment(directory),parent)
    code_files=sorted(directory.glob('code-*.asm')); log_files=sorted(directory.glob('isolate-*-v8.log'))
    for p in code_files:
        require(re.fullmatch(r'code-'+str(native['pid'])+r'(?:-[0-9]+)?\.asm',p.name), 'Unowned code trace')
    for p in log_files:
        require(re.fullmatch(r'isolate-0x[0-9a-fA-F]+-'+str(native['pid'])+r'-v8\.log',p.name), 'Unowned code event log')
    return dict(directory=SLOT['directory'], benchmark='pidigits',argument=10000,pid=native['pid'],
        started_at=native['started_at'],finished_at=native['finished_at'],
        native_process_receipt_sha256=sha(directory/'process.json'),
        stdout_bytes=len(stdout),stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_bytes=len(stderr),stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        code_trace_files=[p.name for p in code_files],code_event_files=[p.name for p in log_files],
        native_exit_and_raw_streams_verified=True,application_output_qualified=False,
        runtime_work_semantics_qualified=False,diagnostic_partition_status='pending-independent-lossless-review',benchmark_samples=0)


def finish(report,plan,output,pins,lock):
    errors=[];held=False
    try:
        b.verify(pins);kb.kh.verify_lock(lock);held=True
        entries=report['registered_commands']
        require(len(entries)==report['native_processes_started']<=1 and
            all(x['directory']==SLOT['directory'] for x in entries), 'Native registration differs')
        require({str(p.relative_to(output)) for p in output.glob('*/process.json')} ==
            {x['directory']+'/process.json' for x in entries}, 'Native receipt inventory differs')
        for entry in entries:
            raw=json.loads((output/entry['directory']/'process.json').read_bytes())
            require(raw['pid']==entry['pid'] and raw['direct_child_reaped'] is True and
                raw.get('remaining_process_group',[])==raw.get('remaining_after_cleanup',[])==[] and
                raw['cleanup_errors']==[] and not raw.get('artifact_errors'), 'Unclosed owned process')
        for capture in report['captures']:
            require(checked_capture(plan,output/SLOT['directory'],os.getpid())==capture,'Raw capture changed')
        if report['status']==SUCCESS:
            require(len(report['captures'])==report['native_processes_started']==1,'Missing pi capture')
        available=s.inventory(output,('report.json','terminal.json'))
        for directory,snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')}==snapshot,
                'Validated raw artifact changed')
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);available={}
    report.update(active=None,finished_at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,artifacts=available)
    if errors:report['status']='failed-integrity'
    save(output/'report.json',report)
    try:
        closure=s.inventory(output,('terminal.json',))
        require({n:v for n,v in closure.items() if n!='report.json'}==available,'Final artifact closure changed')
        require(closure['report.json']['sha256']==sha(output/'report.json'),'Final report changed')
        b.verify(pins);held=False;kb.kh.verify_lock(lock);held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);report['status']='failed-integrity'
        save(output/'report.json',report);closure={}
    terminal=dict(schema='typescript-missing-pi-raw-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),available_evidence=closure,integrity_errors=errors,
        native_processes_started=report['native_processes_started'],capture_count=len(report['captures']),
        common_mutex_held=held,common_mutex_inode=79859134,application_output_qualified=False,required_work_qualified=False,
        runtime_dependency_closure_qualified=False,full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
    with (output/'terminal.json').open('x') as stream:json.dump(terminal,stream,indent=2);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run');run.add_argument('--plan',type=Path,required=True);run.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();b.physical(args.plan)
    def interrupted(signum,frame):raise KeyboardInterrupt('TypeScript pi capture interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock);b.checked_python()
        if args.mode=='prepare':
            require(not args.plan.exists() and not args.plan.is_relative_to(args.output),'Fresh external plan required')
            plan=build_plan(args.output);b.verify(plan['pins']);b.c.package_inventory(plan['compiled']['packages'])
            kb.kh.verify_lock(lock);args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
            print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes=0)));return 0
        pins={};plan=b.document(args.plan,args.plan_sha256,pins);output=Path(plan['output'])
        require(plan==build_plan(output),'Prepared missing-pi plan differs')
        for name,digest in plan['pins'].items():b.bind(pins,name,digest)
        b.verify(pins);output.mkdir(parents=True,exist_ok=False)
        report=dict(schema='typescript-missing-pi-raw-results-v1',status='running',plan=str(args.plan),plan_sha256=args.plan_sha256,
            pins=pins,started_at=datetime.now(timezone.utc).isoformat(),active=None,native_processes_started=0,
            registered_commands=[],captures=[],validated_artifacts={},application_output_qualified=False,
            required_work_qualified=False,runtime_dependency_closure_qualified=False,full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
        save(output/'report.json',report)
        try:
            b.verify(pins);kb.kh.verify_lock(lock)
            directory=output/SLOT['directory'];directory.mkdir()
            for name in ('home','tmp'):(directory/name).mkdir()
            def launched(pid):
                report['native_processes_started']+=1;report['registered_commands'].append(dict(directory=SLOT['directory'],pid=pid))
                report['active']=dict(directory=SLOT['directory'],pid=pid);save(output/'report.json',report)
            kb.observe(command(plan),b.environment(directory),directory,b'',lock,launched,kind='typescript-single-entry')
            capture=checked_capture(plan,directory,os.getpid());snapshot=s.inventory(directory)
            with atomic():
                report['captures'].append(capture);report['validated_artifacts'][SLOT['directory']]=snapshot
                report['active']=None;save(output/'report.json',report)
            report['status']=SUCCESS
        except BaseException as error:
            report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        finally:
            with atomic():finish(report,plan,output,pins,lock)
        print(json.dumps(dict(status=report['status'],captures=len(report['captures']),report_sha256=sha(output/'report.json'))))
        return 0 if report['status']==SUCCESS else 1


if __name__=='__main__':raise SystemExit(main())
