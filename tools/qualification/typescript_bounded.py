#!/usr/bin/env python3
"""Own 149 serial TypeScript correctness cases using closed, emitted JavaScript.

The frozen observer's seven expected exit-1 failure receipts remain unchanged.
Only their exact normal-exit envelope plus the TypeScript output contract can pass.
This stage admits bounded outputs, never required work, source counts or timings.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/typescript/bounded-v1'
COMPILE = ROOT/'tools/qualification/typescript_native_stage.py'
COMPILE_SHA = '4a6cc2484c2e967bd84496958e0b22ac205600a403e0ca41310505c3fc998175'
CHECKER = ROOT/'tools/qualification/scala_typescript_outputs.py'
CHECKER_SHA = '88efb309f9ef6054b4541bd1605d98c323711acf2a62ce7c0080cc3bbcd08d0d'
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
BUILD = CORPUS.parent.parent/'build.py'
BUILD_SHA = 'ebe804f81cfc9df83083fe548f9c09e302f261984a0a96fbd14782d6e65c06c0'
SUCCESS = 'all149-bounded-output-contracts-passed-awaiting-required-work-review'
COMPILED = 'compile-and-AST-captures-recorded-awaiting-independent-review'
COMPILED_REPORT_SHA = 'ec6fb9979e5de31cd8496f01e338fef80f322f118def9923d61b8c3b5ca9e83b'
COMPILED_TERMINAL_SHA = '2abf7814b6063b15561af165bed377d77f6616597d555ec7f4d967c421372038'
COMPILED_PLAN_SHA = '520b14aea813379f036053ce7bc6e7b21ad016775407536ee3195703444412c4'
REVIEW = ROOT/'experiments/typescript/native-stage-v1/independent-native-review-v1.json'
REVIEW_SHA = 'f5c253d1abe24c3c0f409a3ca1668b1662f9377742976160c7e26392c6dcffd5'


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def module(path, expected):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Frozen dependency changed: '+str(path))
    spec = importlib.util.spec_from_file_location(path.stem+'_typescript_bounded',path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),value.__dict__)
    return value


c = module(COMPILE,COMPILE_SHA)
check = module(CHECKER,CHECKER_SHA)
kb = c.kb


def bind(pins, path, digest):
    path = str(path)
    require(Path(path).is_absolute() and Path(path).resolve() == Path(path), 'Physical absolute input required')
    require(type(digest) is str and len(digest)==64 and all(x in '0123456789abcdef' for x in digest), 'Invalid SHA-256')
    require(path not in pins or pins[path] == digest, 'Conflicting input pin: '+path)
    pins[path] = digest


def document(path, digest, pins):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Changed metadata: '+str(path))
    bind(pins,path,digest)
    return json.loads(raw)


def verify(pins):
    for path,digest in pins.items(): require(sha(path)==digest,'Pinned file changed: '+path)


def physical(path):
    require(path.is_absolute() and path.resolve()==path, 'Physical absolute path required')


def inventory(output, exclude=()):
    require(output.is_dir() and not output.is_symlink(), 'Missing or linked output directory')
    result = {}; total = 0
    for path in sorted(output.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), 'Linked or nonregular artifact')
        relative = str(path.relative_to(output))
        if path.is_file() and relative not in exclude:
            size = path.stat().st_size; total += size
            require(size <= kb.FILE_LIMIT+kb.PIPE_CHUNK or relative.endswith('.json'), 'Oversized native artifact')
            result[relative] = dict(bytes=size,sha256=sha(path))
    require(len(result)<=2500 and total<=512*1024*1024, 'Artifact inventory exceeds bounded stage limits')
    return result


def stamp(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.tzinfo is not None, 'Naive lifecycle timestamp')
    return parsed


def native_receipt(directory, command, environment, payload, parent, kind, expected_exit=0):
    """Require exact ownership/resource closure, retaining the exit-1 producer failure."""
    start,active,final = [json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start,active,final):
        require(record['command']==command and record['environment']==environment and record['cwd']==str(directory)
                and record['kind']==kind and record['started_at']==start['started_at']
                and type(record['stdin_bytes']) is int and record['stdin_bytes']==len(payload)
                and record['stdin_sha256']==hashlib.sha256(payload).hexdigest()
                and record['inherited_common_mutex'] is True and record['common_mutex_inode']==79859134
                and record['process_timeout_seconds']==30 and record['cleanup_timeout_seconds']==5
                and record['maximum_process_group_rss_bytes']==kb.RSS_LIMIT
                and record['native_file_limit_bytes']==kb.FILE_LIMIT
                and record['stdout_capture_limit_bytes']==kb.FILE_LIMIT+kb.PIPE_CHUNK
                and record['stdout_transport']=='OS pipe, retained as received'
                and record['stderr_transport']=='exclusive artifact'
                and record['benchmark_samples']==0 and record['source_work_qualified'] is record['chart_admission'] is False,
                'Native launch/input/resource policy differs')
    identity = final['identity']; leader = final['leader_identity_before_reap']
    require(start['status']=='starting' and start['native_process_started'] is False
            and active['status']=='running' and active['native_process_started'] is True
            and active['identity']==identity and final['native_process_started'] is True
            and type(parent) is int and parent>0 and identity['ppid']==parent,
            'Missing or unowned native start/active identity')
    for field in ('pid','pgid','ppid','birth_seconds','birth_microseconds'):
        require(type(identity[field]) is int and identity[field]==leader[field], 'Native birth identity changed')
    pid = final['pid']
    require(type(pid) is int and pid>0 and active['pid']==active['pgid']==pid==final['pgid']==identity['pid']==identity['pgid']
            and leader['status']==5 and final['direct_child_reaped'] is True
            and final['remaining_process_group']==[] and final.get('remaining_after_cleanup',[])==[]
            and final['stop_signals']==final['cleanup_errors']==[] and not final.get('artifact_errors')
            and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
            and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples']>0
            and 0<final['observed_peak_process_group_rss_bytes']<=kb.RSS_LIMIT
            and stamp(start['started_at'])<=stamp(final['finished_at'])
            and type(final['exit_status']) is int and final['exit_status']==expected_exit,
            'Native process failed normal owned closure')
    if expected_exit==1:
        require(final['status']=='failed' and final.get('error_type')=='AssertionError'
                and final.get('error')=='Native command exited unsuccessfully', 'Unrelated failure cannot be an expected rejection')
    else:
        require(expected_exit==0 and final['status']=='native-passed'
                and not final.get('error') and not final.get('error_type'), 'Successful native receipt required')
    streams = []
    for name in ('stdout','stderr'):
        raw = (directory/(name+'.bin')).read_bytes()
        require(len(raw)==final[name+'_bytes'] and hashlib.sha256(raw).hexdigest()==final[name+'_sha256'], 'Native raw stream differs')
        streams.append(raw)
    return final,streams[0],streams[1]


def compiled_prerequisite(path, report_sha, terminal_sha, pins):
    """Replay the exact closed compile/AST packet; runtime pin hashing stays locked."""
    path=Path(path);physical(path);output=path.parent
    require(path==c.HERE/'run-v1/report.json' and report_sha==COMPILED_REPORT_SHA
            and terminal_sha==COMPILED_TERMINAL_SHA, 'Exact independently reviewed TypeScript compilation required')
    report=document(path,report_sha,pins);terminal=document(output/'terminal.json',terminal_sha,pins)
    plan_path=c.HERE/'plan-v1.json';plan=document(plan_path,COMPILED_PLAN_SHA,pins)
    review=document(REVIEW,REVIEW_SHA,pins)
    require(review['status']=='actual-compile-and-AST-artifact-replay-passed'
            and review['report']['sha256']==report_sha and review['terminal']['sha256']==terminal_sha
            and review['source_plan']['sha256']==COMPILED_PLAN_SHA, 'Independent compilation review differs')
    require(report['schema']=='typescript-compile-and-reader-results-v1'
            and terminal['schema']=='typescript-compile-and-reader-terminal-v1'
            and report['status']==terminal['status']==COMPILED and terminal['report_sha256']==report_sha
            and report['integrity_errors']==report['process_receipt_errors']==terminal['integrity_errors']==terminal['process_receipt_errors']==[]
            and report['active'] is None and report['api_child_start_unconfirmed'] is False
            and report['owned_commands_started']==terminal['owned_commands_started']==2
            and report['subject_main_invocations']==report['benchmark_samples']==terminal['benchmark_samples']==0
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==79859134
            and report['native_transport_verified'] is report['conformance_qualified'] is report['required_work_qualified'] is False
            and report['runtime_dependency_closure_qualified'] is report['chart_admission'] is terminal['chart_admission'] is False
            and report['canonical_loc'] is report['formatted_loc'] is terminal['canonical_loc'] is terminal['formatted_loc'] is None,
            'Incomplete compilation or unrelated qualification')
    require(plan['status']=='prepared-awaiting-independent-review' and plan['pins_verified'] is True
            and plan['controller']==str(COMPILE) and plan['controller_sha256']==COMPILE_SHA
            and plan['output']==str(output) and report['plan']==str(plan_path) and report['plan_sha256']==COMPILED_PLAN_SHA
            and report['pins']==dict(plan['pins'],**{str(plan_path):COMPILED_PLAN_SHA}), 'Compiled plan/pin identity differs')
    for name,digest in report['pins'].items():bind(pins,name,digest)
    for name,digest in {**c.PINS,COMPILE:COMPILE_SHA,c.OBSERVER:c.OBSERVER_SHA,
            Path(kb.kh.__file__):kb.HELPER_CONTROLLER_SHA,Path(kb.eb.__file__):kb.REFERENCE_CONTROLLER_SHA,
            kb.kh.PYTHON:kb.kh.PYTHON_SHA,c.NODE:c.NODE_SHA,c.ORIGINAL_READER:c.ORIGINAL_READER_SHA}.items():
        require(report['pins'].get(str(name))==digest,'Compilation omitted a required source/runtime pin')
    require(plan['node']==str(c.NODE) and plan['node_sha256']==c.NODE_SHA, 'Retained Node identity differs')
    closure=inventory(output,('report.json','terminal.json'))
    require(closure==report['artifacts'] and terminal['available_evidence']==dict(closure,
            **{'report.json':dict(bytes=path.stat().st_size,sha256=report_sha)}), 'Compiled terminal artifact inventory differs')
    require({name for name in closure if Path(name).name=='process.json'}=={'compile/process.json','reader/process.json'},
            'Compiled process inventory differs')
    c.check_snapshot(report,output,closure)
    require(c.process_closure(report,output)==[], 'Compiled process closure failed')
    for name,item in closure.items():bind(pins,output/name,item['sha256'])
    for name,digest in report['generated_input_pins'].items():
        bind(pins,name,digest);require(sha(name)==digest,'Generated reader input changed')
    parent=None;previous=stamp(report['started_at']);seen=[];receipts=[]
    for stage in ('compile','reader'):
        directory=output/stage;raw=json.loads((directory/'process.json').read_bytes())
        if parent is None:parent=raw['identity']['ppid']
        command=plan['compiler_command'] if stage=='compile' else [plan['node'],plan['reader'],
            str(output/'reader-plan.json'),sha(output/'reader-plan.json')]
        receipt,stdout,stderr=native_receipt(directory,command,c.environment(directory),b'',parent,'typescript-'+stage)
        require(stderr==b'' and (stage!='reader' or stdout==b''), 'Unexpected compile/reader diagnostics')
        require(previous<=stamp(receipt['started_at'])<=stamp(receipt['finished_at']), 'Overlapping compilation stages')
        previous=stamp(receipt['finished_at']);seen.append(receipt['pid']);receipts.append(receipt)
        if stage=='compile':require(c.validate_compile(plan,directory,stdout)==report['stages']['compile'], 'Compiled output replay differs')
    require(len(set(seen))==2 and previous<=stamp(report['finished_at']) and report['registered_commands']==
            [dict(stage=s,pid=p,pgid=p) for s,p in zip(('compile','reader'),seen)], 'Incomplete compilation schedule')
    child=json.loads((output/'reader/evidence/compiler-child-start.json').read_bytes())
    child_terminal=json.loads((output/'reader/evidence/compiler-child-terminal.json').read_bytes())
    c.validate_child(child,child_terminal,receipts[1],plan)
    require(report['observed_api_children']==terminal['observed_api_children']==[child], 'API child ledger differs')
    rows=report['stages']['compile']['profiles'];profiles=[]
    require([r['id'] for r in rows]==['typescript-'+b+'-v1' for b in c.BENCHES], 'Compiled profile order differs')
    for bench,row in zip(c.BENCHES,rows):
        authored=c.SOURCES/(bench+'.ts');staged=output/'compile/project'/(bench+'.ts')
        script=output/'compile/project/emitted'/(bench+'.js');mapping=script.with_suffix('.js.map')
        require(row['source_sha256']==pins[str(authored)]==sha(staged)==sha(authored)
                and row['javascript']==dict(path=str(script),sha256=sha(script))
                and row['source_map']==dict(path=str(mapping),sha256=sha(mapping)), 'Source/emitted binding differs')
        profiles.append(dict(id=row['id'],benchmark=bench,source=str(authored),source_sha256=row['source_sha256'],
            compiled_source=str(staged),javascript=row['javascript'],source_map=row['source_map']))
    require(inventory(output,('report.json','terminal.json'))==closure, 'Compilation artifacts changed during replay')
    return dict(report=str(path),report_sha256=report_sha,terminal=str(output/'terminal.json'),terminal_sha256=terminal_sha,
        artifacts=closure,node=plan['node'],profiles=profiles,source_plan=str(plan_path),source_plan_sha256=COMPILED_PLAN_SHA,
        independent_review=str(REVIEW),independent_review_sha256=REVIEW_SHA,packages=plan['packages'])


def corpus(pins):
    bind(pins,BUILD,BUILD_SHA)
    data=document(CORPUS,CORPUS_SHA,pins)
    require(data['schema']=='shared-bounded-workload-corpus-v1' and data['generator_sha256']==BUILD_SHA
            and data['case_count']==len(data['cases'])==149 and data['success_cases']==142 and data['rejection_cases']==7
            and data['subject_output_qualified'] is data['source_work_qualified'] is data['chart_admission'] is False,
            'Changed corpus policy')
    for name,digest in data['reference_pins'].items(): bind(pins,ROOT/name,digest)
    identities=set();schedule=[]
    for index,case in enumerate(data['cases'],1):
        identity=(case['benchmark'],case['case'])
        require(identity not in identities and case['benchmark'] in c.BENCHES, 'Duplicate/unknown corpus case')
        identities.add(identity)
        require(case['input_kind'] in ('stdin','integer-argument') and type(case['n']) is int and case['n']>=0,
                'Invalid corpus input')
        for field in ('stdin','expected'):
            if field not in case: continue
            item=case[field]; path=CORPUS.parent/item['path']
            require(path.resolve().is_relative_to(CORPUS.parent) and '..' not in Path(item['path']).parts
                    and type(item['bytes']) is int and item['bytes']>=0, 'Escaping or invalid corpus artifact')
            bind(pins,path,item['sha256'])
            require(path.stat().st_size==item['bytes'] and sha(path)==item['sha256'], 'Changed corpus bytes')
        negative=case['expected_exit']=='nonzero'
        require((negative and case['benchmark']=='revcomp' and case['validation']=='language-specific-invalid-iupac' and 'expected' not in case)
                or (type(case['expected_exit']) is int and case['expected_exit']==0 and 'expected' in case), 'Wrong output contract')
        require(case['input_kind']!='integer-argument' or case['stdin']['bytes']==0, 'Numeric case carries stdin')
        schedule.append(dict(slot=index,id='typescript-'+case['benchmark']+'-v1',case=case,
                             directory=f'{index:03d}-{case["benchmark"]}-{case["case"]}'))
    require(sum(s['case']['expected_exit']=='nonzero' for s in schedule)==7, 'Wrong rejection count')
    return schedule


def build_plan(output, compiled_report, report_sha, terminal_sha):
    physical(output);require(output.is_relative_to(PACKET) and output!=PACKET and not output.exists(), 'Fresh bounded output required')
    pins={};compiled=compiled_prerequisite(compiled_report,report_sha,terminal_sha,pins);schedule=corpus(pins)
    for path,digest in ((COMPILE,COMPILE_SHA),(CHECKER,CHECKER_SHA),(Path(__file__).resolve(),sha(__file__)),
            (Path(__file__).with_name('test_typescript_bounded.py'),sha(Path(__file__).with_name('test_typescript_bounded.py'))),
            (PACKET/'README.md',sha(PACKET/'README.md'))):bind(pins,path,digest)
    return dict(schema='typescript149-bounded-plan-v1',status='prepared-awaiting-independent-review',output=str(output),
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),compiled=compiled,pins=pins,schedule=schedule,
        runtime_flags=[],native_processes=149,successful_cases=142,rejection_cases=7,authored_computation_threads=1,
        timeout_seconds=30,cleanup_seconds=5,maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        common_mutex_inode=79859134,no_automatic_retry=True,compiler_invocations=0,
        bounded_outputs_qualified=False,source_work_qualified=False,runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,benchmark_samples=0,chart_admission=False)


def environment(directory):
    return dict(PATH='/usr/bin:/bin',HOME=str(directory/'home'),TMPDIR=str(directory/'tmp')+'/',
                LC_ALL='C',LANG='C',TZ='UTC',UV_THREADPOOL_SIZE='8')


def command_for(plan,profile,case,directory):
    command=[plan['compiled']['node'],profile['javascript']['path']]
    if case['input_kind']=='integer-argument':command.append(str(case['n']))
    return command,environment(directory)


def checked_case(plan,slot,directory,parent):
    case=slot['case'];profile=next(r for r in plan['compiled']['profiles'] if r['id']==slot['id'])
    command,env=command_for(plan,profile,case,directory)
    payload=(CORPUS.parent/case['stdin']['path']).read_bytes()
    require(len(payload)==case['stdin']['bytes'] and hashlib.sha256(payload).hexdigest()==case['stdin']['sha256'], 'Case input changed')
    code=1 if case['expected_exit']=='nonzero' else 0
    receipt,stdout,stderr=native_receipt(directory,command,env,payload,parent,'typescript-bounded-main',code)
    expected=None if code else (CORPUS.parent/case['expected']['path']).read_bytes()
    validation=check.validate(case,'typescript',stdout,stderr,receipt['exit_status'],expected)
    return dict(slot=slot['slot'],id=slot['id'],case=case['case'],benchmark=case['benchmark'],pid=receipt['pid'],
        process=dict(path=str(directory/'process.json'),sha256=sha(directory/'process.json')),
        observer_status=receipt['status'],expected_rejection=bool(code),output_validation=validation,
        native_lifetime_verified=True,source_work_qualified=False,chart_admission=False)


def execution_inputs(plan):
    pins=plan['pins'];compiled=plan['compiled']
    emitted=Path(compiled['report']).parent/'compile/project/emitted'
    expected={bench+suffix for bench in c.BENCHES for suffix in ('.js','.js.map')}
    require(emitted.is_dir() and not emitted.is_symlink() and {p.name for p in emitted.iterdir()}==expected
            and all(p.is_file() and not p.is_symlink() for p in emitted.iterdir()), 'Emitted executable inventory changed')
    for profile in compiled['profiles']:
        for name in (profile['source'],profile['compiled_source'],profile['javascript']['path'],profile['source_map']['path']):
            require(sha(name)==pins[name], 'Authored/emitted input changed')
    for name in (compiled['node'],str(CHECKER),str(emitted.parent/'package.json')):
        require(sha(name)==pins[name], 'Node execution dependency changed')


def process_closure(report,plan,output):
    errors=[]
    try:
        registrations=report['registered_commands'];count=report['native_processes_started']
        require(len(registrations)==count<=149 and len({x['pid'] for x in registrations})==count,
                'Repeated or missing registered process')
        require({str(p.parent.relative_to(output)) for p in output.rglob('process.json')}=={r['directory'] for r in registrations},
                'Native receipt inventory differs')
        for index,record in enumerate(registrations):
            slot=plan['schedule'][index]
            require(record['slot']==slot['slot'] and record['directory']==slot['directory'], 'Native schedule changed')
            receipt=json.loads((output/record['directory']/'process.json').read_bytes())
            require(type(record['pid']) is int and record['pid']>0 and receipt['pid']==receipt['pgid']==record['pid']
                    and receipt['native_process_started'] is receipt['direct_child_reaped'] is True
                    and receipt.get('remaining_process_group',[])==receipt.get('remaining_after_cleanup',[])==[]
                    and receipt['cleanup_errors']==[], 'Native group/reaping closure incomplete')
        if report['status']==SUCCESS:
            require(count==len(report['cases'])==149 and report['qualified_cases']==149
                    and report['successful_cases']==142 and report['rejected_cases']==7,
                    'Successful corpus incomplete')
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    return errors


def final_snapshot(report,artifacts):
    for directory,snapshot in report['validated_case_artifacts'].items():
        prefix=directory+'/'
        require({n[len(prefix):]:v for n,v in artifacts.items() if n.startswith(prefix)}==snapshot,
                'Validated case differs from final artifact inventory: '+directory)


def finish(report,plan,output,pins,lock):
    errors=[];held=False
    report['process_receipt_errors']=process_closure(report,plan,output)
    if report['process_receipt_errors']:errors.append(dict(path='<process-closure>',error='Incomplete native closure'))
    try:
        require(not (output/'terminal.json').exists(), 'Terminal already exists')
        report['artifacts']=inventory(output,('report.json',));final_snapshot(report,report['artifacts'])
    except BaseException as error:errors.append(dict(path='<artifact-inventory>',error=str(error)))
    report['integrity_errors']=errors;report['active']=None
    if errors:report['status']='failed-integrity'
    report['finished_at']=datetime.now(timezone.utc).isoformat();kb.save(output/'report.json',report)
    try:
        available=inventory(output)
        require({n:v for n,v in available.items() if n!='report.json'}==report['artifacts'], 'Artifacts changed during final closure')
        final_snapshot(report,available)
        require(available['report.json']['sha256']==sha(output/'report.json'), 'Final report differs')
    except BaseException as error:errors.append(dict(path='<terminal-inventory>',error=str(error)));available={}
    for path,digest in pins.items():
        try:require(sha(path)==digest,'Pinned input changed after final inventory')
        except BaseException as error:errors.append(dict(path=path,error=str(error)))
    try:execution_inputs(plan)
    except BaseException as error:errors.append(dict(path='<execution-inputs>',error=str(error)))
    try:
        compiled=plan['compiled'];require(inventory(Path(compiled['report']).parent,('report.json','terminal.json'))==compiled['artifacts'],
                                          'Compiled artifact inventory changed')
    except BaseException as error:errors.append(dict(path='<compiled-closure>',error=str(error)))
    try:kb.kh.verify_lock(lock);held=True
    except BaseException as error:errors.append(dict(path='<common-mutex>',error=str(error)))
    if errors:
        report['status']='failed-integrity';report['bounded_outputs_qualified']=False;kb.save(output/'report.json',report)
        available={'report.json':dict(bytes=(output/'report.json').stat().st_size,sha256=sha(output/'report.json'))}
    terminal=dict(schema='typescript149-bounded-terminal-v1',status=report['status'],report_sha256=sha(output/'report.json'),
        available_evidence=available,integrity_errors=errors,process_receipt_errors=report['process_receipt_errors'],
        native_processes_started=report['native_processes_started'],qualified_cases=report['qualified_cases'],
        bounded_outputs_qualified=report['bounded_outputs_qualified'],common_mutex_held=held,common_mutex_inode=79859134,
        source_work_qualified=False,runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
    with (output/'terminal.json').open('x') as stream:json.dump(terminal,stream,indent=2);stream.write('\n')


def checked_python():
    require(Path(sys.executable).resolve()==kb.kh.PYTHON.resolve() and sha(sys.executable)==kb.kh.PYTHON_SHA
            and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Use retained Python -I -S -B without -O')


def prepare(args):
    physical(args.plan);physical(args.output)
    require(not args.plan.exists() and not args.plan.is_relative_to(args.output), 'Fresh plan outside output required')
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock);checked_python()
        plan=build_plan(args.output,args.compiled_report,args.compiled_report_sha256,args.compiled_terminal_sha256)
        verify(plan['pins'])
        c.package_inventory(plan['compiled']['packages']);execution_inputs(plan)
        kb.kh.verify_lock(lock);args.plan.parent.mkdir(parents=True,exist_ok=True)
        with args.plan.open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes=0)))


def run(args):
    physical(args.plan)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock);checked_python()
        pins={};plan=document(args.plan,args.plan_sha256,pins);compiled=plan['compiled'];output=Path(plan['output'])
        expected=build_plan(output,compiled['report'],compiled['report_sha256'],compiled['terminal_sha256'])
        require(plan==expected,'Plan differs from exact compiled inputs/corpus/policy')
        for path,digest in plan['pins'].items():bind(pins,path,digest)
        verify(pins);output.mkdir(parents=True,exist_ok=False)
        report=dict(schema='typescript149-bounded-results-v1',status='running',plan=str(args.plan),plan_sha256=args.plan_sha256,pins=pins,
            started_at=datetime.now(timezone.utc).isoformat(),active=None,native_processes_started=0,registered_commands=[],
            cases=[],qualified_cases=0,successful_cases=0,rejected_cases=0,validated_case_artifacts={},
            bounded_outputs_qualified=False,source_work_qualified=False,runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
            full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
        kb.save(output/'report.json',report)
        try:
            for slot in plan['schedule']:
                execution_inputs(plan);kb.kh.verify_lock(lock)
                directory=output/slot['directory'];directory.mkdir()
                for name in ('home','tmp'):(directory/name).mkdir()
                case=slot['case'];profile=next(r for r in compiled['profiles'] if r['id']==slot['id'])
                command,env=command_for(plan,profile,case,directory);payload=(CORPUS.parent/case['stdin']['path']).read_bytes()
                require(len(payload)==case['stdin']['bytes'] and hashlib.sha256(payload).hexdigest()==case['stdin']['sha256'], 'Input changed before launch')
                def launched(pid):
                    report['native_processes_started']+=1
                    report['registered_commands'].append(dict(slot=slot['slot'],directory=slot['directory'],pid=pid))
                    report['active']=dict(slot=slot['slot'],pid=pid);kb.save(output/'report.json',report)
                try:kb.observe(command,env,directory,payload,lock,launched,kind='typescript-bounded-main')
                except AssertionError as error:
                    require(case['expected_exit']=='nonzero' and str(error)=='Native command exited unsuccessfully',
                            'Observer failure is not the specified normal rejection')
                snapshot=inventory(directory)
                result=checked_case(plan,slot,directory,os.getpid())
                require(inventory(directory)==snapshot,'Native case artifact changed during validation')
                report['cases'].append(result);report['qualified_cases']+=1
                report['rejected_cases' if result['expected_rejection'] else 'successful_cases']+=1
                report['validated_case_artifacts'][slot['directory']]=snapshot;report['active']=None
                kb.save(output/'report.json',report)
            require((report['qualified_cases'],report['successful_cases'],report['rejected_cases'])==(149,142,7), 'Incomplete bounded corpus')
            report.update(status=SUCCESS,bounded_outputs_qualified=True)
        except BaseException as error:report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        finally:
            with kb.atomic():finish(report,plan,output,pins,lock)
        print(json.dumps(dict(status=report['status'],qualified_cases=report['qualified_cases'],report_sha256=sha(output/'report.json'))))
        return 0 if report['status']==SUCCESS else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    prep.add_argument('--compiled-report',type=Path,required=True);prep.add_argument('--compiled-report-sha256',required=True)
    prep.add_argument('--compiled-terminal-sha256',required=True)
    execute=sub.add_parser('run');execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('TypeScript bounded stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    return prepare(args) if args.mode=='prepare' else run(args)


if __name__=='__main__':raise SystemExit(main())
