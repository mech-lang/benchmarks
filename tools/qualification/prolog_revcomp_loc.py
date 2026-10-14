#!/usr/bin/env python3
"""Run nine bounded source readers after the linear candidate's 542 checks.

Preparation and execution retain the common mutex. This stage observes no
candidate main and performs no compilation; canonical admission stays false
until the actual candidate owners receive independent review.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys
from types import FunctionType, SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/prolog/revcomp-linear-v1/source-counts-v1'
BOUNDED_SHA='642e0f761aa873023eb24e8a66e9a6837d57f1eb9568e80fe1478a263e95bda9'
ADAPTER_SHA='e50907c378879e81ab74e6b1aee48e844548e472e576d0009bb412f3f85d840c'
METADATA_SHA='ce4fba632cad12e8ab181c8530e25ebf3c41d0dc9eba2930eff8c882198bfee4'
FIXTURES_SHA='72bcd84c9cea5b25be5691e5cfd9a7161d9fc15e1ab98ebe6491b623dc45c3a2'
LEGACY_REPORT=ROOT/'archive/validation/loc-normalization/20261013/prolog-proposal-v5/jobs/reader31-v1/fixture-receipt.json'
LEGACY_REPORT_SHA='1f3f96d2888ffac3180d75ec7652a762fb3be0fa09278e3e6e3a410354c02700'
LEGACY_TERMINAL=LEGACY_REPORT.with_name('terminal-pin.json')
LEGACY_TERMINAL_SHA='c4e2d74e97d514d2dc1d9fd29e50fe152d88e857c7dd0bfa9f553fcfb2d5f089'
COMPLETE='nine-native-source-readers-complete-awaiting-candidate-owner-review'


def require(value,message):
    if not value:raise AssertionError(message)


def load(path,digest,name):
    raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==digest,'Frozen source changed: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__);return module


b=load(ROOT/'tools/qualification/prolog_revcomp_bounded.py',BOUNDED_SHA,'linear_loc_bounded')
units=load(ROOT/'tools/qualification/prolog_revcomp_source_units.py',ADAPTER_SHA,'linear_loc_units')
kb=b.kb
sha,save,bind=b.sha,b.save,b.bind


def read(path,digest,pins):
    path=Path(bind(pins,path,digest));raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'JSON changed during read')
    return json.loads(raw)


def saved_receipt(directory,command,environment,payload,pid,parent_pid,**outcome):
    require(type(parent_pid) is int and parent_pid>0,'Invalid recorded controller PID')
    # Clone the frozen validator's globals solely to supply the already-bound
    # historical parent identity. Neither the frozen function nor global os is
    # mutated; every byte/policy/ownership check remains the original code.
    validator=FunctionType(b.check_receipt.__code__,dict(b.check_receipt.__globals__,
        os=SimpleNamespace(getpid=lambda:parent_pid)),b.check_receipt.__name__,b.check_receipt.__defaults__)
    return validator(directory,command,environment,payload,pid,**outcome)


def closed_artifacts(directory,terminal,pins):
    actual=b.inventory(directory)
    require('terminal.json' in actual,'Missing closed terminal')
    del actual['terminal.json']
    require(actual==terminal['available_evidence'],'Closed bounded artifact inventory differs')
    for name,item in actual.items():bind(pins,directory/name,item['sha256'])


def validate_legacy_reader(report,terminal,pins):
    status='passed-awaiting-original-source-review'
    require(report['status']==terminal['status']==status and terminal['receipt_sha256']==LEGACY_REPORT_SHA and
            report['tests_run']==31 and len(report['expected_ids'])==len(set(report['expected_ids']))==31 and
            set(report['expected_ids'])==set(report['started_ids'])==set(report['discovered_ids']),
            'Historical reader fixture cohort differs')
    require(all(report[key]==0 for key in ('failures','errors','skipped','expected_failures','unexpected_successes')) and
            report['pin_reconciliation_passed'] is True and report['terminal_artifact_errors']==[] and
            report['available_bytes_not_fully_pinned'] is terminal['available_bytes_not_fully_pinned'] is False and
            terminal['integrity_errors']==[] and report['shared_timing_mutex_held'] is True and
            report['mutex_inode']==kb.LOCK_INODE,'Historical reader fixtures are not closed and passed')
    require(pins.get(str(LEGACY_REPORT))==LEGACY_REPORT_SHA and
            pins.get(str(LEGACY_TERMINAL))==LEGACY_TERMINAL_SHA,'Reader proof absent from bounded closure')
    grammar={Path(path).name:digest for path,digest in report['input_pins'].items()
             if '/prolog-proposal-v5/' in path}
    require(grammar['foreign_prolog.py']==units.COUNTER_SHA and grammar['scan_source.pl']==units.READER_SHA,
            'Historical fixtures selected another grammar')


def bounded_prerequisite(args,pins):
    report_path=args.bounded_report.resolve();directory=report_path.parent
    report=read(report_path,args.bounded_report_sha256,pins)
    terminal_path=directory/'terminal.json'
    terminal=read(terminal_path,args.bounded_terminal_sha256,pins)
    durable=read(args.bounded_durable,args.bounded_durable_sha256,pins)
    status='bounded-conformance-passed-awaiting-work-and-source-count-review'
    require(report['schema']=='prolog-revcomp-linear-bounded-report-v1' and
            report['status']==terminal['status']==status and terminal['report_sha256']==args.bounded_report_sha256 and
            report['bounded_conformance_qualified'] is terminal['bounded_conformance_qualified'] is True and
            report['active'] is None and len(report['commands'])==542 and
            report['native_processes_started']==terminal['native_processes_started']==542 and
            report['qualified_cases']==terminal['qualified_cases']==540 and
            report['successful_cases']==470 and report['rejected_cases']==70,'Incomplete bounded prerequisite')
    require(report['integrity_errors']==terminal['integrity_errors']==[] and
            report['artifact_errors']==terminal['artifact_errors']==[] and
            terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==kb.LOCK_INODE and
            report['benchmark_samples']==0 and report['canonical_loc'] is report['formatted_loc'] is None and
            all(report[key] is terminal[key] is False for key in
                ('source_work_qualified','full_timings_qualified','chart_admission')),'Wrong bounded closure or scope')
    require(durable['status']=='command-exited-zero-awaiting-report-review' and durable['actual_command_started'] is True and
            durable['exit_code']==0 and durable['qualification_granted'] is False and durable['automatic_retry'] is False and
            durable['stop_signals']==[] and durable['command_identity_observation_missing'] is False,
            'Bounded durable owner did not close successfully')
    parent=durable['command_pid']
    require(type(parent) is int and parent>0 and durable['command_identity']['pid']==parent,'Wrong bounded durable PID')
    expected=[str(kb.kh.PYTHON),'-I','-S','-B',str(ROOT/'tools/qualification/prolog_revcomp_bounded.py'),
              'run','--plan',report['plan'],'--plan-sha256',report['plan_sha256']]
    require(durable['command_identity']['listing'].endswith(' '.join(expected)), 'Wrong bounded durable command')
    for path,digest in report['pins'].items():bind(pins,path,digest)
    plan=read(report['plan'],report['plan_sha256'],pins);b.validate_plan(plan)
    require(plan['output']==str(directory) and all(report['pins'].get(path)==digest for path,digest in plan['pins'].items()),
            'Bounded plan/output pin linkage differs')
    closed_artifacts(directory,terminal,pins)
    source=directory/'authored/candidate.pl';compiled=source.with_suffix('.qlf')
    require(report['compiler_bound_source']==dict(path=str(source),sha256=units.CANDIDATE_SHA,counted=True) and
            sha(source)==units.CANDIDATE_SHA,'Bounded compiler source differs')
    require(report['compiled_artifact']==dict(path=str(compiled),sha256=sha(compiled),bytes=compiled.stat().st_size) and
            compiled.stat().st_size>0,'Bounded compiled QLF differs')
    expected_ids=['compile','inspect']+[row['id'] for row in plan['schedule']]
    require([row['id'] for row in report['commands']]==expected_ids and
            len({row['pid'] for row in report['commands']})==542,'Bounded registered native ledger differs')
    require({str(p.parent.relative_to(directory)) for p in directory.rglob('process.json')}==set(expected_ids),
            'Extra/missing bounded process receipt')
    for index,entry in enumerate(report['commands']):
        case_dir=directory/entry['id'];preparation=index<2
        if preparation:
            target=source if index==0 else compiled
            command=b.preparation_command(plan['binary'],entry['id'],target,case_dir,source.parent);payload=b''
            require(entry['status']=='native-lifetime-verified','Bounded compiler entry unverified')
        else:
            row=plan['schedule'][index-2];case=row['case']
            payload=(Path(plan['fixtures'])/case['stdin']).read_bytes()
            require(len(payload)==case['input_bytes'] and hashlib.sha256(payload).hexdigest()==case['input_sha256'],
                    'Bounded fixture input differs')
            command=b.candidate_command(plan['binary'],compiled,row['capacity'])
            require(entry['status']=='qualified-case' and entry['fixture']==case['id'] and entry['capacity']==row['capacity'],
                    'Bounded case result linkage differs')
        failure=not preparation and case['expected_status']=='invalid-iupac'
        require(entry['command']==command and entry['environment']==plan['environment'] and entry['cwd']==str(case_dir) and
                entry['expected_failure'] is failure and entry['compiler_warning'] is preparation and
                entry['stdin_bytes']==len(payload) and entry['stdin_sha256']==hashlib.sha256(payload).hexdigest() and
                entry['process_sha256']==sha(case_dir/'process.json'),'Bounded registered command differs')
        receipt=saved_receipt(case_dir,command,plan['environment'],payload,entry['pid'],parent,
                              expected_failure=failure,compiler_warning=preparation)
        require(all(entry[key]==receipt[key] for key in ('stdout_sha256','stderr_sha256')),'Bounded stream linkage differs')
        stdout=(case_dir/'stdout.bin').read_bytes();stderr=(case_dir/'stderr.bin').read_bytes()
        if preparation:
            require(stdout==b'' and stderr==b.COMPILE_WARNING,'Bounded compiler diagnostic differs')
            b.check_compiler_metadata(case_dir,entry['id'],target,source.parent,plan)
        else:require(entry['result']==b.check_case(case,stdout,stderr),'Bounded expected result differs')
    legacy_report=read(LEGACY_REPORT,LEGACY_REPORT_SHA,pins)
    legacy_terminal=read(LEGACY_TERMINAL,LEGACY_TERMINAL_SHA,pins)
    validate_legacy_reader(legacy_report,legacy_terminal,pins)
    return dict(report=str(report_path),report_sha256=args.bounded_report_sha256,
        terminal=str(terminal_path),terminal_sha256=args.bounded_terminal_sha256,
        durable=str(args.bounded_durable.resolve()),durable_sha256=args.bounded_durable_sha256,
        controller_pid=parent,native_processes_reused=542,compiler_source=str(source),
        compiler_source_sha256=units.CANDIDATE_SHA,compiled_qlf=report['compiled_artifact'],
        inspected_wam=str(directory/'inspect/candidate.wam'),inspected_wam_sha256=sha(directory/'inspect/candidate.wam'),
        binary=plan['binary'],environment=plan['environment'])


def own_pins():
    return {str(path.resolve()):digest for path,digest in [
        (ROOT/'tools/qualification/prolog_revcomp_bounded.py',BOUNDED_SHA),
        (ROOT/'tools/qualification/prolog_revcomp_source_units.py',ADAPTER_SHA),
        (units.GRAMMAR/'foreign_prolog.py',units.COUNTER_SHA),(units.GRAMMAR/'scan_source.pl',units.READER_SHA),
        (PACKET/'inspect_targets.pl',METADATA_SHA),(PACKET/'fixtures-v1/manifest.json',FIXTURES_SHA),
        (PACKET.parent/'candidate.pl',units.CANDIDATE_SHA),(kb.kh.PYTHON,kb.kh.PYTHON_SHA),
        (Path(__file__),sha(__file__))]}


def source_schedule(binary,pins):
    manifest=read(PACKET/'fixtures-v1/manifest.json',FIXTURES_SHA,pins)
    require(manifest['native_executions']==0 and manifest['fixtures_qualified'] is False and
            len(manifest['fixtures'])==7,'Fixture source manifest scope differs')
    rows=[dict(id='builtin-metadata',kind='metadata',argv=units.metadata_command(binary))]
    for actual,expected in zip(manifest['fixtures'],units.fixtures()):
        require(all(actual[key]==value for key,value in expected.items()),'Source fixture contract differs')
        source=PACKET/'fixtures-v1'/(expected['id']+'.pl');raw=expected['source_text'].encode('utf8')
        digest=hashlib.sha256(raw).hexdigest()
        require(actual['source']==str(source) and actual['source_sha256']==digest,'Fixture source binding differs')
        bind(pins,source,digest)
        rows.append(dict(id='fixture-'+actual['id'],kind='fixture',argv=units.reader_command(binary,source),
            source=str(source),source_sha256=digest,expected_canonical_loc=actual['expected_canonical_loc'],
            expected_diagnostic_kinds=actual['expected_diagnostic_kinds']))
    source=PACKET.parent/'candidate.pl';bind(pins,source,units.CANDIDATE_SHA)
    rows.append(dict(id='candidate-original-source',kind='candidate',source=str(source),
        source_sha256=units.CANDIDATE_SHA,argv=units.reader_command(binary,source)))
    require(len(rows)==len({row['id'] for row in rows})==9,'Reader inventory differs')
    return rows


def prepare(args):
    plan_path=args.plan.resolve();output=args.output.resolve()
    require(not plan_path.exists() and not output.exists() and plan_path.is_relative_to(PACKET) and
            output.is_relative_to(PACKET) and not plan_path.is_relative_to(output),'Fresh separate packet paths required')
    pins={};prior=bounded_prerequisite(args,pins)
    for path,digest in own_pins().items():bind(pins,path,digest)
    rows=source_schedule(prior['binary'],pins)
    plan=dict(schema='prolog-linear-source-count-plan-v1',controller_sha256=sha(__file__),
        status='prepared-awaiting-nine-native-readers',pins=pins,prerequisite=prior,schedule=rows,output=str(output),
        process_timeout_seconds=kb.TIMEOUT,cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=kb.FILE_LIMIT,
        planned_native_processes=9,subject_main_executions=0,subject_compilations=0,automatic_retries=0,
        benchmark_samples=0,canonical_LOC_admitted=False,source_work_qualified=False,chart_admission=False)
    plan_path.parent.mkdir(parents=True,exist_ok=True)
    require(not plan_path.exists(),'Reader plan appeared during preparation')
    save(plan_path,plan)
    print(json.dumps(dict(plan=str(plan_path),sha256=sha(plan_path),native_executions=0)),flush=True)


def validate_plan(plan):
    expected=dict(schema='prolog-linear-source-count-plan-v1',controller_sha256=sha(__file__),
        status='prepared-awaiting-nine-native-readers',process_timeout_seconds=kb.TIMEOUT,
        cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        native_file_limit_bytes=kb.FILE_LIMIT,planned_native_processes=9,subject_main_executions=0,
        subject_compilations=0,automatic_retries=0,benchmark_samples=0,canonical_LOC_admitted=False,
        source_work_qualified=False,chart_admission=False)
    for key,value in expected.items():
        require(type(plan.get(key)) is type(value) and plan[key]==value,'Reader plan policy differs: '+key)
    require(all(plan['pins'].get(path)==digest for path,digest in own_pins().items()),'Required reader pin missing/changed')
    output=Path(plan['output']);require(output.is_absolute() and output.resolve()==output and output.is_relative_to(PACKET),
                                     'Reader output escapes packet')
    pins={};rows=source_schedule(plan['prerequisite']['binary'],pins)
    require(rows==plan['schedule'] and all(plan['pins'].get(path)==digest for path,digest in pins.items()),
            'Reader schedule/input pins differ')


def validate_projection(row,packet,metadata,prior):
    raw=Path(row['source']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==row['source_sha256'] and packet['source']==row['source'] and
            packet['source_text'].encode('utf8')==raw,'Reader packet does not contain exact scheduled source')
    if row['kind']=='candidate':
        result=units.project_candidate(raw,Path(prior['compiler_source']).read_bytes(),packet,metadata,
            prior['environment']['SWI_HOME_DIR'],Path(prior['inspected_wam']).read_text())
        require(result['projection']['diagnostics']==[] and type(result['projection']['normalized_loc']) is int,
                'Candidate source ownership unresolved')
    else:
        result=units.project(raw,packet,metadata,prior['environment']['SWI_HOME_DIR'])
        metric=result['projection']
        require(metric['normalized_loc']==row['expected_canonical_loc'] and
                [issue['kind'] for issue in metric['diagnostics']]==row['expected_diagnostic_kinds'],
                'New source fixture expectation differs')
        if row['id']=='fixture-local-definition':
            calls=[event for event in metric['canonical_events'] if event['kind']=='call']
            require(len(calls)==1 and tuple(calls[0]['resolved_target'])==('m','string_codes/2'),
                    'Local definition no longer shadows builtin')
    require(all(result[key] is False for key in ('canonical_LOC_admitted','source_work_qualified','chart_admission')),
            'Projection granted unsupported admission')
    return result


def finish(report,plan,pins,output,snapshots,lock):
    errors=[];registered=[]
    for entry in report['commands']:
        directory=output/entry['id']
        try:
            receipt=saved_receipt(directory,entry['argv'],plan['prerequisite']['environment'],b'',entry['pid'],os.getpid())
            registered.append(entry['id'])
            require(entry['process_sha256']==sha(directory/'process.json'),'Registered reader receipt changed')
        except BaseException as error:errors.append(dict(id=entry['id'],error=str(error) or type(error).__name__))
    if {str(p.parent.relative_to(output)) for p in output.rglob('process.json')}!={e['id'] for e in report['commands']}:
        errors.append(dict(error='Unexpected or missing reader process receipt'))
    if report['status']==COMPLETE:
        if (registered!=[row['id'] for row in plan['schedule']] or report['native_processes_started']!=9 or
            len({entry['pid'] for entry in report['commands']})!=9 or len(report['projections'])!=8 or
            [entry['id'] for entry in report['projections']]!=[row['id'] for row in plan['schedule'][1:]] or
            set(snapshots)!=set(registered) or report['active'] is not None):
            errors.append(dict(error='Incomplete successful reader ledger'))
        for entry in report['projections']:
            try:require(sha(output/entry['id']/'projection.json')==entry['projection_sha256'],
                        'Projection report/artifact linkage changed')
            except BaseException as error:errors.append(dict(id=entry['id'],error=str(error) or type(error).__name__))
    for name,expected in snapshots.items():
        try:require(b.inventory(output/name)==expected,'Validated reader artifacts changed')
        except BaseException as error:errors.append(dict(id=name,error=str(error) or type(error).__name__))
    integrity=b.verify_pins(pins)
    if errors or integrity:report['status']='failed-reader-integrity-or-closure'
    report.update(native_receipt_errors=errors,integrity_errors=integrity,finished_at=datetime.now(timezone.utc).isoformat())
    kb.kh.verify_lock(lock);save(output/'report.json',report)
    artifact_errors=[]
    try:artifacts=b.inventory(output)
    except BaseException as error:
        artifact_errors.append(dict(error=str(error) or type(error).__name__))
        report.update(status='failed-reader-artifact-retention',artifact_errors=artifact_errors)
        save(output/'report.json',report)
        artifacts={'report.json':dict(bytes=(output/'report.json').stat().st_size,sha256=sha(output/'report.json'))}
    require(not (output/'terminal.json').exists(),'Reader terminal already exists')
    save(output/'terminal.json',dict(schema='prolog-linear-source-count-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),available_evidence=artifacts,native_processes_started=report['native_processes_started'],
        native_receipt_errors=errors,integrity_errors=integrity,artifact_errors=artifact_errors,
        common_mutex_held=True,common_mutex_inode=kb.LOCK_INODE,
        canonical_LOC_admitted=False,source_work_qualified=False,chart_admission=False,subject_main_executions=0,
        subject_compilations=0,benchmark_samples=0))
    require(not errors and not integrity and not artifact_errors,'Reader artifact or native closure failed')


def run(args,lock):
    pins={};plan=read(args.plan,args.plan_sha256,pins);validate_plan(plan)
    for path,digest in plan['pins'].items():bind(pins,path,digest)
    prior=plan['prerequisite']
    prior_args=SimpleNamespace(bounded_report=Path(prior['report']),bounded_report_sha256=prior['report_sha256'],
        bounded_terminal_sha256=prior['terminal_sha256'],bounded_durable=Path(prior['durable']),
        bounded_durable_sha256=prior['durable_sha256'])
    require(bounded_prerequisite(prior_args,pins)==prior,'Bounded prerequisite changed after preparation')
    output=Path(plan['output']);output.mkdir(parents=True,exist_ok=False)
    report=dict(schema='prolog-linear-source-count-results-v1',status='running',started_at=datetime.now(timezone.utc).isoformat(),
        plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,pins=pins,prerequisite=prior,commands=[],projections=[],
        native_processes_started=0,active=None,canonical_LOC_admitted=False,source_work_qualified=False,chart_admission=False,
        subject_main_executions=0,subject_compilations=0,benchmark_samples=0)
    snapshots={};metadata=None;save(output/'report.json',report)
    try:
        for row in plan['schedule']:
            kb.kh.verify_lock(lock);directory=output/row['id'];directory.mkdir()
            entry=dict(id=row['id'],argv=row['argv'],pid=None,status='starting')
            report['commands'].append(entry);report['active']=row['id'];save(output/'report.json',report)
            def launched(pid):
                entry['pid']=pid;report['native_processes_started']+=1;save(output/'report.json',report)
            kb.observe(row['argv'],prior['environment'],directory,b'',lock,launched,kind='prolog-revcomp-bounded')
            saved_receipt(directory,row['argv'],prior['environment'],b'',entry['pid'],os.getpid())
            require((directory/'stderr.bin').read_bytes()==b'','Unexpected reader stderr')
            packet=json.loads((directory/'stdout.bin').read_bytes())
            if row['kind']=='metadata':
                units.validate_builtin_metadata(packet,prior['environment']['SWI_HOME_DIR']);metadata=packet
                save(directory/'validated.json',packet)
            else:
                require(metadata is not None,'Metadata reader must precede projection')
                result=validate_projection(row,packet,metadata,prior);save(directory/'projection.json',result)
                report['projections'].append(dict(id=row['id'],projection_sha256=sha(directory/'projection.json'),
                    canonical_loc=result['projection']['normalized_loc'],physical_loc=result['projection']['physical_loc'],
                    diagnostics=result['projection']['diagnostics'],canonical_LOC_admitted=False))
            entry.update(status='reader-validated',process_sha256=sha(directory/'process.json'))
            snapshots[row['id']]=b.inventory(directory);report['active']=None;save(output/'report.json',report)
            print('Read linear Prolog source: '+row['id'],flush=True)
        report['status']=COMPLETE
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__);raise
    finally:
        with kb.atomic():finish(report,plan,pins,output,snapshots,lock)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare');p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bounded-report',type=Path,required=True);p.add_argument('--bounded-report-sha256',required=True)
    p.add_argument('--bounded-terminal-sha256',required=True);p.add_argument('--bounded-durable',type=Path,required=True)
    p.add_argument('--bounded-durable-sha256',required=True)
    p=sub.add_parser('run');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    require(Path(sys.executable).resolve()==kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use retained Python with -I -S -B')
    def interrupted(signum,frame):raise KeyboardInterrupt('Prolog source-count stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON)==kb.kh.PYTHON_SHA,'Reader controller interpreter changed')
        prepare(args) if args.action=='prepare' else run(args,lock)


if __name__=='__main__':main()
