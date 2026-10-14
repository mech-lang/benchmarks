#!/usr/bin/env python3
"""Reconcile the closed first Kotlin capture, then capture only the other three.

The failed first attempt is immutable. Its exact VM warning is retained and
separately identified; its complete subject bytes and saved machine code are
replayed. prepare/run require the existing continuous timing mutex.
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
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/single-entry-remaining-v1'
ORIGINAL = ROOT/'experiments/kotlin/single-entry-work-v1'
CAPTURE_SHA = 'baeb42da62b8bb4020fe019a2c0c22e47f4bb401852339d6c383b93ad76fd7a4'
FIRST_PLAN_SHA = '363f5a7af8a10e0dc93b88e3da3d371872ae0737e91d8f2a4591889d8885e88d'
FIRST_REPORT_SHA = '5918aed5d40abb86e1c647dcad9e3664062be762f47a63d1e4d59d0730c52aea'
FIRST_TERMINAL_SHA = 'e69e7f55f8ae63dfd6f516b82256625fd13cd8c53e9e359d5cef943266260097'
DURABLE = ROOT/'experiments/kotlin/dispatch-v1/owned-jobs/single-entry-four-v1/terminal.json'
DURABLE_SHA = 'e550b132232a4fdb5cf87c46516a2444f267ff8faeb40dc8f7f8e52cf39a6814'
FIRST_ID = 'kotlin-binarytrees-compact'
IDS = ['kotlin-binarytrees-optimized','kotlin-pidigits-compact','kotlin-pidigits-optimized']
FIRST_WARNING = b'[0.023s][warning][os] Loading hsdis library failed\n'
COMPLETE = 'all3-additional-native-captures-awaiting-instruction-review'


def require(value, message):
    if not value: raise AssertionError(message)


def load_capture():
    path = ROOT/'tools/qualification/kotlin_single_entry_capture.py'; raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CAPTURE_SHA, 'Reviewed capture replay changed')
    spec = importlib.util.spec_from_file_location('remaining_kotlin_capture',path)
    module = importlib.util.module_from_spec(spec); exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


capture = load_capture()
base = capture.stage
kb = base.kb
sha, save, bind, read = base.sha, base.save, base.bind, base.read


def options(benchmark, directory):
    return base.options(benchmark,directory)+[
        '-Xlog:all=warning,os=off:stdout:uptime,level,tags',
        f'-Xlog:os=warning:file={directory}/os.log:uptime,level,tags']


def validate_first_stdout(raw, expected):
    require(raw == FIRST_WARNING+expected,
            'First stdout is not the exact recorded VM warning plus complete prescribed subject bytes')
    return raw[len(FIRST_WARNING):]


def validate_saved_receipt(receipt, directory, command, environment, parent_pid):
    require(receipt['status'] == 'native-passed' and receipt['kind'] == 'single-entry-work' and
            receipt['native_process_started'] is True and receipt['direct_child_reaped'] is True and
            receipt['exit_status'] == 0 and receipt['command'] == command and receipt['environment'] == environment and
            receipt['cwd'] == str(directory) and receipt['pid'] == receipt['pgid'] and
            type(receipt['pid']) is int and receipt['pid'] > 0 and
            receipt['inherited_common_mutex'] is True and receipt['common_mutex_inode'] == kb.LOCK_INODE and
            receipt['stdin_bytes'] == 0 and receipt['stdin_sha256'] == hashlib.sha256(b'').hexdigest(),
            'Closed native receipt identity differs')
    require(not any(receipt.get(k) for k in ('error','error_type','stop_signals','cleanup_errors','artifact_errors',
                'remaining_process_group','remaining_after_cleanup','timed_out')), 'Native cleanup was not clean')
    before,after = receipt['identity'],receipt['leader_identity_before_reap']
    require(all(before[k] == after[k] for k in ('pid','pgid','ppid','birth_seconds','birth_microseconds')) and
            before['pid'] == before['pgid'] == receipt['pid'] and before['ppid'] == parent_pid and after['status'] == 5,
            'Native birth/parent/reaping proof differs')
    for key,value in [('process_timeout_seconds',kb.TIMEOUT),('cleanup_timeout_seconds',kb.CLEANUP_TIMEOUT),
                      ('maximum_process_group_rss_bytes',kb.RSS_LIMIT),('native_file_limit_bytes',kb.FILE_LIMIT),
                      ('stdout_capture_limit_bytes',kb.FILE_LIMIT+kb.PIPE_CHUNK)]:
        require(receipt[key] == value, 'Native bound differs: '+key)
    require(receipt['kernel_monitor_samples'] > 0 and 0 <= receipt['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT,
            'Native RSS observation missing/outside policy')
    for stream in ('stdout','stderr'):
        path = directory/(stream+'.bin')
        require(receipt[stream+'_bytes'] == path.stat().st_size and receipt[stream+'_sha256'] == sha(path),
                'Retained stream receipt differs')
    require(receipt['stderr_bytes'] == 0, 'Unexpected native stderr')


def reconcile_first(pins, verify_artifact_closure):
    plan = read(ORIGINAL/'plan-v1.json',FIRST_PLAN_SHA,pins)
    report = read(ORIGINAL/'run-v1/report.json',FIRST_REPORT_SHA,pins)
    terminal = read(ORIGINAL/'run-v1/terminal.json',FIRST_TERMINAL_SHA,pins)
    durable = read(DURABLE,DURABLE_SHA,pins)
    require(plan['controller_sha256'] == capture.CONTROLLER_SHA and plan['ids'] == [FIRST_ID]+IDS and
            report['plan_sha256'] == FIRST_PLAN_SHA and report['status'] == terminal['status'] == 'failed' and
            report['error'] == 'Prescribed complete stdout differs' and report['error_type'] == 'AssertionError' and
            report['active'] is None and report['profiles'] == [] and report['validated_command_artifacts'] == {} and
            report['native_processes_started'] == terminal['native_processes_started'] == 1 and
            report['registered_native_commands'] == terminal['registered_native_commands'] ==
            [dict(id=FIRST_ID,pid=23661,pgid=23661)] and terminal['report_sha256'] == FIRST_REPORT_SHA and
            terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == kb.LOCK_INODE,
            'Exact closed first attempt differs')
    require(all(report[k] == terminal[k] == [] for k in ('process_receipt_errors','integrity_errors')) and
            terminal['artifact_errors'] == [] and report['source_work_qualified'] is False and
            report['benchmark_samples'] == 0 and set(report['commands']) == {FIRST_ID}, 'First attempt integrity differs')
    require(durable['status'] == 'command-failed' and durable['actual_command_started'] is True and
            durable['exit_code'] == 1 and durable['command_pid'] == durable['command_identity']['pid'] == 23659 and
            durable['qualification_granted'] is False and durable['automatic_retry'] is False and
            durable['stop_signals'] == [] and not durable['command_identity_observation_missing'] and
            str(ORIGINAL/'plan-v1.json') in durable['command_identity']['listing'] and
            FIRST_PLAN_SHA in durable['command_identity']['listing'], 'First durable terminal differs')
    if verify_artifact_closure:
        for path,digest in report['pins'].items(): bind(path,digest,pins)
        base.closed_artifacts(ORIGINAL/'run-v1',terminal,pins)
    row = plan['profiles'][0]; directory = (ORIGINAL/'run-v1'/FIRST_ID).resolve()
    command = [plan['java']]+base.options('binarytrees',directory)+[
        '-cp',row['classes']+os.pathsep+plan['stdlib'],row['main_owner'],'21']
    require(row['id'] == FIRST_ID and report['commands'][FIRST_ID]['argv'] == command, 'First direct-main command differs')
    receipt = json.loads((directory/'process.json').read_bytes())
    validate_saved_receipt(receipt,directory,command,report['commands'][FIRST_ID]['environment'],23659)
    for name in ('start.json','active.json'):
        saved = json.loads((directory/name).read_bytes())
        require(all(saved[k] == receipt[k] for k in ('kind','command','environment','cwd','started_at')),
                'First native start/final linkage differs')
        if name == 'active.json': require(saved['identity'] == receipt['identity'], 'First active birth differs')
    expected = base.expected_output('binarytrees'); raw = (directory/'stdout.bin').read_bytes()
    validate_first_stdout(raw,expected)
    require((directory/'expected.stdout').read_bytes() == expected,'First retained output reference differs')
    base.validate_vm_identity(directory/'hotspot.xml',row,plan,directory,receipt)
    loaded = base.validate_classes((directory/'classes.log').read_text(),row,plan['stdlib'])
    require('Using G1' in (directory/'gc.log').read_text(), 'First G1 evidence missing')
    index = capture.capture_index(directory/'hotspot.xml','binarytrees')
    require(not any(n['installed_nmethod'] for n in index['node_allocation_eliminations']),
            'First saved code contains an installed Node elimination')
    proof = dict(schema='kotlin-first-single-entry-additive-reconciliation-v1',id=FIRST_ID,
        original_status='failed',original_error=report['error'],original_plan_sha256=FIRST_PLAN_SHA,
        original_report_sha256=FIRST_REPORT_SHA,original_terminal_sha256=FIRST_TERMINAL_SHA,
        durable_terminal_sha256=DURABLE_SHA,pid=23661,controller_pid=23659,
        raw_stdout_sha256=receipt['stdout_sha256'],raw_stdout_bytes=len(raw),
        retained_vm_diagnostic=FIRST_WARNING.decode('ascii'),vm_diagnostic_bytes=len(FIRST_WARNING),
        complete_subject_output_bytes=len(expected),complete_subject_output_sha256=hashlib.sha256(expected).hexdigest(),
        complete_subject_output_match=True,actual_loaded_classes=loaded,native_capture=index,
        observed_peak_process_group_rss_bytes=receipt['observed_peak_process_group_rss_bytes'],
        native_commands_reexecuted=0,source_work_qualified=False,benchmark_samples=0,chart_admission=False)
    return plan,proof


def prepare(args):
    require(not args.plan.exists() and not args.output.exists() and
            not args.plan.resolve().is_relative_to(args.output.resolve()), 'Fresh plan/output required')
    pins = {}; prior,proof = reconcile_first(pins,True)
    rows = [r for r in prior['profiles'] if r['id'] in IDS]
    require([r['id'] for r in rows] == IDS, 'Remaining retained cohort differs')
    for path in (Path(__file__).resolve(),ROOT/'tools/qualification/kotlin_single_entry_capture.py',
                 PACKET/'README.md',PACKET/'first-capture-reconciliation.md',kb.kh.PYTHON): bind(path,sha(path),pins)
    require(pins[str(kb.kh.PYTHON)] == kb.kh.PYTHON_SHA, 'Interpreter differs')
    plan = dict(schema='kotlin-single-entry-remaining-plan-v1',controller_sha256=sha(__file__),capture_sha256=CAPTURE_SHA,
        status='prepared-awaiting-three-additional-captures',pins=pins,ids=IDS,excluded_id=FIRST_ID,
        first_capture_reconciliation=proof,profiles=rows,java=prior['java'],stdlib=prior['stdlib'],
        runtime_expected=prior['runtime_expected'],prescribed_inputs=base.INPUTS,output=str(args.output.resolve()),
        planned_native_commands=3,prior_native_commands_reused=1,automatic_retries=0,
        process_timeout_seconds=kb.TIMEOUT,cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=kb.FILE_LIMIT,
        subject_recompilations=0,diagnostic_compilations=0,benchmark_samples=0,
        source_work_qualified=False,full_timings_qualified=False,chart_admission=False)
    args.plan.parent.mkdir(parents=True,exist_ok=True); require(not args.plan.exists(),'Plan appeared during prepare')
    save(args.plan,plan)
    print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_executions=0,reused_native_commands=1)),flush=True)


def validate_vm_identity(path,row,plan,directory,receipt):
    root = ET.parse(path).getroot(); args = root.find('vm_arguments')
    require(root.get('process') == str(receipt['pid']) and args is not None and
            args.findtext('args','').strip().split() == options(row['benchmark'],directory) and
            args.findtext('command','').strip() == row['main_owner']+' '+str(base.INPUTS[row['benchmark']]) and
            args.findtext('launcher','').strip() == 'SUN_STANDARD','Actual remaining JVM command differs')
    properties = dict(line.split('=',1) for line in args.findtext('properties','').strip().splitlines() if '=' in line)
    expected = {'java.home':str(Path(plan['java']).parent.parent),
        'java.class.path':row['classes']+os.pathsep+plan['stdlib'],
        'java.vm.version':plan['runtime_expected']['RUNTIME_VERSION'],'java.vm.name':plan['runtime_expected']['VM_NAME'],
        'java.vm.vendor':plan['runtime_expected']['VENDOR'],'user.home':str(directory/'home'),
        'java.io.tmpdir':str(directory/'tmp')}
    require(all(properties.get(k) == v for k,v in expected.items()) and
            'for bsd-'+plan['runtime_expected']['OS_ARCH']+' ' in root.findtext('vm_version/info',''),
            'Actual remaining JVM identity differs')


def validate_os_log(raw):
    lines = raw.decode('ascii').splitlines()
    require(len(lines) <= 1 and all(re.fullmatch(r'\[[0-9]+\.[0-9]+s\]\[warning\]\[os\] Loading hsdis library failed',s)
                                  for s in lines), 'Unexpected OS diagnostic; retained without filtering')
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),lines=lines)


def finish(report,plan,pins,output,lock):
    # The reused finalizer always reconciles registered PIDs, reaping, validated
    # snapshots, all pins and the complete artifact inventory. Its special
    # four-case success branch is deliberately not used; validate these three
    # cases explicitly before passing our distinct status to it.
    errors = []
    if report['status'] == COMPLETE:
        try:
            require([p['id'] for p in report['profiles']] == IDS and report['native_processes_started'] == 3 and
                    set(report['commands']) == set(report['validated_command_artifacts']) == set(IDS) and
                    [r['id'] for r in report['registered_native_commands']] == IDS and
                    len({r['pid'] for r in report['registered_native_commands']}) == 3 and report['active'] is None,
                    'Successful remaining-three inventory differs')
            require(json.loads((output/'first-capture-reconciliation.json').read_bytes()) ==
                    report['first_capture_reconciliation'] == plan['first_capture_reconciliation'],
                    'Saved first-capture reconciliation differs')
            require({str(p.parent.relative_to(output)) for p in output.rglob('process.json')} == set(IDS),
                    'Unexpected or omitted remaining native receipt')
            for identity in IDS:
                directory = output/identity; row = next(p for p in report['profiles'] if p['id'] == identity)
                require(json.loads((directory/'validated.json').read_bytes()) == row, 'Saved/report profile differs')
                validate_saved_receipt(json.loads((directory/'process.json').read_bytes()),directory,
                    report['commands'][identity]['argv'],report['commands'][identity]['environment'],os.getpid())
        except BaseException as error: errors.append(str(error) or type(error).__name__)
    report['remaining_receipt_errors'] = errors
    if errors: report['status'] = 'failed-remaining-native-reconciliation'
    base.finish(report,plan,pins,output,lock)
    require(not errors,'Remaining native reconciliation failed')


def run(args,lock):
    pins = {}; plan = read(args.plan,args.plan_sha256,pins)
    require(plan['schema'] == 'kotlin-single-entry-remaining-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['capture_sha256'] == CAPTURE_SHA and plan['ids'] == IDS and plan['excluded_id'] == FIRST_ID and
            [r['id'] for r in plan['profiles']] == IDS and plan['planned_native_commands'] == 3 and
            plan['prior_native_commands_reused'] == 1 and plan['prescribed_inputs'] == base.INPUTS and
            plan['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and plan['process_timeout_seconds'] == kb.TIMEOUT and
            plan['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT and plan['native_file_limit_bytes'] == kb.FILE_LIMIT and
            plan['automatic_retries'] == 0 and plan['source_work_qualified'] is False and
            plan['full_timings_qualified'] is False and plan['chart_admission'] is False and
            plan['subject_recompilations'] == plan['diagnostic_compilations'] == plan['benchmark_samples'] == 0,
            'Wrong remaining plan')
    pins.update(plan['pins'])
    for path,digest in pins.items(): require(sha(path) == digest,'Preflight input changed: '+path)
    prior,proof = reconcile_first(pins,False)
    require(proof == plan['first_capture_reconciliation'] and
            plan['profiles'] == [r for r in prior['profiles'] if r['id'] in IDS] and
            all(plan[k] == prior[k] for k in ('java','stdlib','runtime_expected')), 'First capture or remaining inputs differ')
    output = Path(plan['output']); require(not output.exists(),'Fresh output required; no retry'); output.mkdir(parents=True)
    report = dict(schema='kotlin-single-entry-remaining-results-v1',status='running',plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256,pins=pins,started_at=datetime.now(timezone.utc).isoformat(),
        first_capture_reconciliation=proof,prior_native_commands_reused=1,profiles=[],active=None,
        native_processes_started=0,registered_native_commands=[],commands={},validated_command_artifacts={},
        subject_recompilations=0,diagnostic_compilations=0,benchmark_samples=0,source_work_qualified=False,
        optimized_main_allocation_and_lifetime_proved=False,runtime_pi_division_counts_proved=False,
        full_timings_qualified=False,chart_admission=False)
    save(output/'first-capture-reconciliation.json',proof); save(output/'report.json',report)
    try:
        for row in plan['profiles']:
            kb.kh.verify_lock(lock); identity = row['id']; benchmark = row['benchmark']; classes = Path(row['classes'])
            require(identity in IDS and identity != FIRST_ID,'First subject must not rerun')
            require({str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()} ==
                    {a['relative_path'] for a in row['class_artifacts']} and
                    not any(p.is_symlink() for p in classes.rglob('*')),'Retained class inventory changed')
            for item in row['physical_inputs']+row['class_artifacts']:
                require(sha(item['path']) == item['sha256'],'Active source/class changed')
            directory = output/identity; directory.mkdir(); environment = kb.kh.environment(row['runtime_environment'],directory)
            expected = base.expected_output(benchmark); (directory/'expected.stdout').write_bytes(expected)
            command = [plan['java']]+options(benchmark,directory)+['-cp',row['classes']+os.pathsep+plan['stdlib'],
                row['main_owner'],str(base.INPUTS[benchmark])]
            report['commands'][identity] = dict(argv=command,environment=environment)
            report['active'] = dict(id=identity,receipt=str(directory/'process.json'),pid=None); save(output/'report.json',report)
            def launched(pid):
                report['native_processes_started'] += 1
                report['registered_native_commands'].append(dict(id=identity,pid=pid,pgid=pid))
                report['active']['pid'] = pid; save(output/'report.json',report)
            receipt = kb.observe(command,environment,directory,b'',lock,launched,kind='single-entry-work')
            validate_saved_receipt(receipt,directory,command,environment,os.getpid())
            require((directory/'stdout.bin').read_bytes() == expected,'Prescribed complete stdout differs')
            os_log = validate_os_log((directory/'os.log').read_bytes())
            validate_vm_identity(directory/'hotspot.xml',row,plan,directory,receipt)
            loaded = base.validate_classes((directory/'classes.log').read_text(),row,plan['stdlib'])
            require('Using G1' in (directory/'gc.log').read_text(),'Actual G1 evidence missing')
            index = capture.capture_index(directory/'hotspot.xml',benchmark); save(directory/'capture-index.json',index)
            require(not any(n['installed_nmethod'] for n in index['node_allocation_eliminations']),
                    'Installed native code eliminates required Node allocation; retain for entry-reachability review')
            result = dict(id=identity,n=base.INPUTS[benchmark],status=index['status'],complete_output_match=True,
                actual_loaded_classes=loaded,os_diagnostics=os_log,capture=index,source_work_qualified=False,
                main_entry='direct JVM launcher; one main call inferred from pinned launch/source, not a probe counter')
            save(directory/'validated.json',result); report['validated_command_artifacts'][identity] = base.snapshot(directory)
            report['profiles'].append(result); report['active'] = None; save(output/'report.json',report)
            print('Captured additional Kotlin single-entry code: '+identity,flush=True)
        report['status'] = COMPLETE
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__); raise
    finally:
        with kb.atomic(): finish(report,plan,pins,output,lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='action',required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--plan',type=Path,required=True); prep.add_argument('--output',type=Path,required=True)
    execute = commands.add_parser('run'); execute.add_argument('--plan',type=Path,required=True); execute.add_argument('--plan-sha256',required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use retained Python with -I -S -B')
    def interrupted(signum,frame): raise KeyboardInterrupt('Remaining capture interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA,'Interpreter changed')
        if args.action == 'prepare': prepare(args)
        else: run(args,lock)


if __name__ == '__main__': main()
