#!/usr/bin/env python3
"""Own 149 serial Scala correctness cases using closed, retained class files.

The frozen observer's seven expected exit-1 failure receipts remain unchanged.
Only their exact normal-exit envelope plus the Scala output contract can pass.
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
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/scala/bounded-v1'
COMPILE = ROOT/'tools/qualification/scala_compile.py'
COMPILE_SHA = '02005f096518ffe8c9397808735435c5aa911e9857bb9142f51aa26901e629ce'
CHECKER = ROOT/'tools/qualification/scala_typescript_outputs.py'
CHECKER_SHA = '88efb309f9ef6054b4541bd1605d98c323711acf2a62ce7c0080cc3bbcd08d0d'
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
BUILD = CORPUS.parent.parent/'build.py'
BUILD_SHA = 'ebe804f81cfc9df83083fe548f9c09e302f261984a0a96fbd14782d6e65c06c0'
SUCCESS = 'all149-bounded-output-contracts-passed-awaiting-required-work-review'
COMPILED = 'ten-applications-compiled-and-inspected-awaiting-native-conformance'


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def module(path, expected):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Frozen dependency changed: '+str(path))
    spec = importlib.util.spec_from_file_location(path.stem+'_scala_bounded',path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),value.__dict__)
    return value


c = module(COMPILE,COMPILE_SHA)
check = module(CHECKER,CHECKER_SHA)
helper = c.load_helper()
kb = helper.load_observer()


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
    """Read only retained metadata/artifacts; complete pin hashing is a separate locked step."""
    path = Path(path); physical(path); output = path.parent
    require(path.name=='report.json' and output.is_relative_to(c.PACKET) and output!=c.PACKET,
            'Closed Scala compilation report required')
    report = document(path,report_sha,pins)
    terminal = document(output/'terminal.json',terminal_sha,pins)
    require(report['schema']=='scala-ten-applications-compile-v1' and report['status']==terminal['status']==COMPILED
            and terminal['report_sha256']==report_sha and report['integrity_errors']==[] and report['active'] is None
            and report['native_processes_started']==terminal['native_processes_started']==20
            and report['compiler_processes_started']==report['bytecode_reader_processes_started']==10
            and report['subject_main_executions']==terminal['subject_main_executions']==0
            and report['benchmark_samples']==terminal['benchmark_samples']==0
            and report['bounded_outputs_qualified'] is report['source_work_qualified'] is report['full_timings_qualified'] is False
            and report['chart_admission'] is terminal['chart_admission'] is False
            and report['canonical_loc'] is report['formatted_loc'] is None,
            'Compilation is incomplete or claims unrelated qualification')
    for name,digest in report['pins'].items(): bind(pins,name,digest)
    for name,digest in ((COMPILE,COMPILE_SHA),(c.HELPER,c.HELPER_SHA),(c.TOOLCHAIN,c.TOOLCHAIN_SHA),
            (c.SOURCES,c.SOURCES_SHA),(Path(kb.__file__),helper.OBSERVER_SHA),
            (Path(kb.kh.__file__),kb.HELPER_CONTROLLER_SHA),(Path(kb.eb.__file__),kb.REFERENCE_CONTROLLER_SHA),
            (kb.kh.PYTHON,kb.kh.PYTHON_SHA)):
        require(report['pins'].get(str(name))==digest, 'Compilation omitted a required source/runtime pin')
    toolchain = document(c.TOOLCHAIN,c.TOOLCHAIN_SHA,pins)
    require(toolchain['status']=='versions-and-readers-compiled-awaiting-parser-execution'
            and toolchain['native_processes_started']==4 and toolchain['integrity_errors']==[], 'Wrong compiled toolchain')
    require(all(report['pins'].get(name)==digest for name,digest in toolchain['pins'].items()), 'Compilation omitted toolchain closure')
    sources = c.source_rows(document(c.SOURCES,c.SOURCES_SHA,pins))
    libraries = [str(p) for p in c.runtime_jars(toolchain['compiler_dependencies'])]
    require(report['runtime_libraries']==libraries and all(name in pins for name in libraries), 'Runtime library identity differs')
    java = toolchain['java']; javap = str(Path(java).with_name('javap'))
    require(java in pins and javap in pins, 'JDK entrypoints unbound')
    require(len(report['profiles'])==10 and [r['id'] for r in report['profiles']]==[r['id'] for r in sources], 'Compiled profile order differs')
    closure = inventory(output,('report.json','terminal.json'))
    require(closure==report['artifacts'], 'Compiled native artifact closure differs')
    require({name for name in closure if Path(name).name=='process.json'} ==
            {row['benchmark']+'/'+stage+'/process.json' for row in sources for stage in ('compile','bytecode')},
            'Compiled native process receipt inventory differs')
    for name,item in closure.items(): bind(pins,output/name,item['sha256'])
    profiles=[]; parent=None; seen=[]; previous=stamp(report['started_at'])
    for profile,row in zip(report['profiles'],sources):
        bench=row['benchmark']; directory=output/bench; source=directory/'Main.scala'; authored=ROOT/row['sources'][0]['path']
        digest=row['sources'][0]['sha256']; cp=str(directory/'classes')+os.pathsep+os.pathsep.join(libraries)
        require(profile['benchmark']==bench and profile['source']==str(source) and profile['original_source']==str(authored.relative_to(ROOT))
                and profile['source_sha256']==digest and profile['main_owner']=='Main' and profile['runtime_classpath']==cp
                and profile['source_work_qualified'] is profile['chart_admission'] is False
                and report['pins'].get(str(source))==report['pins'].get(str(authored))==digest
                and sha(source)==sha(authored)==digest, 'Authored/compiled Scala profile differs')
        artifacts=c.class_inventory(directory/'classes')
        require(artifacts==profile['artifacts'] and all(report['pins'].get(a['path'])==a['sha256'] for a in artifacts), 'Class inventory changed')
        env=dict(PATH='/usr/bin:/bin',HOME=str(directory/'home'),TMPDIR=str(directory/'tmp')+'/',
                 JAVA_HOME=str(Path(java).parent.parent),LC_ALL='C',LANG='C',TZ='UTC')
        compile_command=[java]+c.FLAGS+['-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
            '-cp',toolchain['compiler_classpath'],'dotty.tools.dotc.Main','-classpath',os.pathsep.join(libraries),
            '-encoding','UTF-8','-color:never','-d',str(directory/'classes'),str(source)]
        require(profile['compile_command']==compile_command, 'Compilation command changed')
        for stage in ('compile','bytecode'):
            where=directory/stage
            owners=[a['relative_path'][:-6].replace('/','.') for a in artifacts if a['relative_path'].endswith('.class')]
            command=compile_command if stage=='compile' else [javap,'-J-XX:ActiveProcessorCount=8','-J-Xms64m','-J-Xmx1g',
                '-J-XX:+UseG1GC','-p','-c','-s','-l','-verbose','-classpath',cp]+owners
            ref=profile[stage+'_process']
            require(ref['path']==str(where/'process.json') and ref['sha256']==sha(where/'process.json'), 'Compiler receipt binding differs')
            raw=json.loads((where/'process.json').read_bytes())
            if parent is None:parent=raw['identity']['ppid']
            receipt,stdout,stderr=native_receipt(where,command,env,b'',parent,'diagnostic-compile' if stage=='compile' else 'bytecode-inspection')
            require(stderr==b'' and (stdout==b'' if stage=='compile' else
                    b'public static void main(java.lang.String[]);' in stdout and b'descriptor: ([Ljava/lang/String;)V' in stdout),
                    'Compile/bytecode stream or direct main evidence differs')
            require(previous<=stamp(receipt['started_at'])<=stamp(receipt['finished_at']), 'Overlapping compiler schedule')
            previous=stamp(receipt['finished_at']);seen.append(receipt['pid'])
        profiles.append(dict(id=row['id'],benchmark=bench,source=str(authored),source_sha256=digest,
            compiled_source=str(source),classes=str(directory/'classes'),artifacts=artifacts,runtime_classpath=cp,main_owner='Main'))
    require(len(set(seen))==20 and previous<=stamp(report['finished_at']), 'Incomplete compiled lifecycle schedule')
    require(inventory(output,('report.json','terminal.json'))==closure, 'Compilation artifacts changed during validation')
    return dict(report=str(path),report_sha256=report_sha,terminal=str(output/'terminal.json'),terminal_sha256=terminal_sha,
                artifacts=closure,java=java,runtime_libraries=libraries,profiles=profiles)


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
        schedule.append(dict(slot=index,id='scala-'+case['benchmark']+'-jvm-v1',case=case,
                             directory=f'{index:03d}-{case["benchmark"]}-{case["case"]}'))
    require(sum(s['case']['expected_exit']=='nonzero' for s in schedule)==7, 'Wrong rejection count')
    return schedule


def build_plan(output, compiled_report, report_sha, terminal_sha):
    physical(output);require(output.is_relative_to(PACKET) and output!=PACKET and not output.exists(), 'Fresh bounded output required')
    pins={};compiled=compiled_prerequisite(compiled_report,report_sha,terminal_sha,pins);schedule=corpus(pins)
    for path,digest in ((COMPILE,COMPILE_SHA),(CHECKER,CHECKER_SHA),(Path(__file__).resolve(),sha(__file__)),
            (Path(__file__).with_name('test_scala_bounded.py'),sha(Path(__file__).with_name('test_scala_bounded.py'))),
            (PACKET/'README.md',sha(PACKET/'README.md'))):bind(pins,path,digest)
    return dict(schema='scala149-bounded-plan-v1',status='prepared-awaiting-independent-review',output=str(output),
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),compiled=compiled,pins=pins,schedule=schedule,
        runtime_flags=list(c.FLAGS),native_processes=149,successful_cases=142,rejection_cases=7,maximum_workers=8,
        timeout_seconds=30,cleanup_seconds=5,maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        common_mutex_inode=79859134,no_automatic_retry=True,compiler_invocations=0,
        bounded_outputs_qualified=False,source_work_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,benchmark_samples=0,chart_admission=False)


def environment(directory,java):
    return dict(PATH='/usr/bin:/bin',HOME=str(directory/'home'),TMPDIR=str(directory/'tmp')+'/',
                JAVA_HOME=str(Path(java).parent.parent),LC_ALL='C',LANG='C',TZ='UTC')


def command_for(plan,profile,case,directory):
    env=environment(directory,plan['compiled']['java'])
    command=[plan['compiled']['java']]+c.FLAGS+['-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
                '-cp',profile['runtime_classpath'],'Main']
    if case['input_kind']=='integer-argument':command.append(str(case['n']))
    return command,env


def checked_case(plan,slot,directory,parent):
    case=slot['case'];profile=next(r for r in plan['compiled']['profiles'] if r['id']==slot['id'])
    command,env=command_for(plan,profile,case,directory)
    payload=(CORPUS.parent/case['stdin']['path']).read_bytes()
    require(len(payload)==case['stdin']['bytes'] and hashlib.sha256(payload).hexdigest()==case['stdin']['sha256'], 'Case input changed')
    code=1 if case['expected_exit']=='nonzero' else 0
    receipt,stdout,stderr=native_receipt(directory,command,env,payload,parent,'scala-bounded-main',code)
    expected=None if code else (CORPUS.parent/case['expected']['path']).read_bytes()
    validation=check.validate(case,'scala',stdout,stderr,receipt['exit_status'],expected)
    return dict(slot=slot['slot'],id=slot['id'],case=case['case'],benchmark=case['benchmark'],pid=receipt['pid'],
        process=dict(path=str(directory/'process.json'),sha256=sha(directory/'process.json')),
        observer_status=receipt['status'],expected_rejection=bool(code),output_validation=validation,
        native_lifetime_verified=True,source_work_qualified=False,chart_admission=False)


def execution_inputs(plan):
    pins=plan['pins'];compiled=plan['compiled']
    for profile in compiled['profiles']:
        require(c.class_inventory(Path(profile['classes']))==profile['artifacts'], 'Executable class inventory changed')
        for name in (profile['source'],profile['compiled_source']):require(sha(name)==pins[name], 'Application source changed')
    for name in (compiled['java'],*compiled['runtime_libraries'],str(CHECKER)):
        require(sha(name)==pins[name], 'Execution dependency changed')


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
    terminal=dict(schema='scala149-bounded-terminal-v1',status=report['status'],report_sha256=sha(output/'report.json'),
        available_evidence=available,integrity_errors=errors,process_receipt_errors=report['process_receipt_errors'],
        native_processes_started=report['native_processes_started'],qualified_cases=report['qualified_cases'],
        bounded_outputs_qualified=report['bounded_outputs_qualified'],common_mutex_held=held,common_mutex_inode=79859134,
        source_work_qualified=False,canonical_loc=None,formatted_loc=None,full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
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
        for path in plan['compiled']['runtime_libraries']:
            with zipfile.ZipFile(path) as jar:require('Class-Path:' not in jar.read('META-INF/MANIFEST.MF').decode(), 'Transitive runtime jar classpath')
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
        report=dict(schema='scala149-bounded-results-v1',status='running',plan=str(args.plan),plan_sha256=args.plan_sha256,pins=pins,
            started_at=datetime.now(timezone.utc).isoformat(),active=None,native_processes_started=0,registered_commands=[],
            cases=[],qualified_cases=0,successful_cases=0,rejected_cases=0,validated_case_artifacts={},
            bounded_outputs_qualified=False,source_work_qualified=False,canonical_loc=None,formatted_loc=None,
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
                try:kb.observe(command,env,directory,payload,lock,launched,kind='scala-bounded-main')
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
    def interrupted(signum,frame):raise KeyboardInterrupt('Scala bounded stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    return prepare(args) if args.mode=='prepare' else run(args)


if __name__=='__main__':raise SystemExit(main())
