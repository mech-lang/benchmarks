"""Fixed diagnostic compile plus eighteen unchanged Rebol primitive captures.

No benchmark is executed. Preparation requires an independently reviewed actual
extension build/layout/load disposition, not the earlier source proposal. The
original failed SDK generation and original fixture specification stay intact.
"""
import argparse
from contextlib import contextmanager, ExitStack, nullcontext
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
PACKET = ROOT/'experiments/rebol/primitive-fixtures-v2'
ORIGINAL = ROOT/'experiments/rebol/primitive-fixtures-v1'
HELPER = ROOT/'tools/qualification/rebol_extension.py'
ADAPTER = PACKET/'adapter.py'
SPEC_SHA = '3962c9c0782f4b8fae81555821e5ad5573ea4aa36b55a2d3396e570fa5bb2a79'
KIND = 'rebol-general-primitive-fixtures'
SUCCESS = 'nineteen-captures-retained-awaiting-independent-primitive-review'
CAPTURE_FILES = {'start.json','active.json','process.json','stdout.bin','stderr.bin'}
BUILD_FILES = {'io-faults.dylib','interposer.d','interposer.map'}
SOURCE_FILES = {str(p.relative_to(ROOT)) for p in (
    Path(__file__).resolve(), Path(__file__).with_name('test_rebol_primitive_fixtures.py'),
    ADAPTER, PACKET/'test_adapter.py', PACKET/'README.md')}
GATES = ('full_primitive_fixtures_qualified','benchmark_correctness_qualified',
         'runtime_source_equivalence_proven','source_work_qualified',
         'canonical_source_count_qualified','full_timing_qualified','chart_admission')


def require(value, message):
    if not value: raise AssertionError(message)


def encoded(value): return (json.dumps(value,indent=2)+'\n').encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()


def bootstrap_read(path, limit=2*1024**2):
    """Only the small, explicitly pinned review/helper intake precedes leases."""
    path=Path(path)
    require(path.is_absolute() and path.resolve(strict=True)==path,'Physical intake path required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Regular intake file required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd);require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Intake replaced')
        raw=stream.read(limit+1);require(len(raw)<=limit,'Bounded review/helper intake required')
        after=path.lstat();require(stat.S_ISREG(after.st_mode) and
            (after.st_dev,after.st_ino)==(held.st_dev,held.st_ino),'Intake replaced during read')
    return raw


def ref(path, sha):
    require(type(sha) is str and re.fullmatch('[0-9a-f]{64}',sha),'Exact SHA256 required')
    path=Path(path);require(path.is_absolute(),'Absolute evidence reference required')
    return dict(path=str(path),sha256=sha)


def bootstrap(extension_ref, source_ref):
    source_raw=bootstrap_read(source_ref['path']);require(digest(source_raw)==source_ref['sha256'],'Source review changed')
    review=json.loads(source_raw)
    require(review['schema']=='rebol-primitive-fixture-controller-source-review-v1'
        and review['status']=='independent-source-review-complete-native-fixtures-pending'
        and review['independent_review'] is True and set(review['files'])==SOURCE_FILES
        and set(review['dependencies'])=={str(HELPER.relative_to(ROOT))}
        and all(review[k] is False for k in GATES),'Independent fixed-stage source review required')
    helper_raw=bootstrap_read(HELPER)
    require(digest(helper_raw)==review['dependencies'][str(HELPER.relative_to(ROOT))],'Reviewed extension helper changed')
    e=types.ModuleType('rebol_fixture_extension_helper');e.__file__=str(HELPER)
    exec(compile(helper_raw,str(HELPER),'exec'),e.__dict__)
    require(e.ROOT==ROOT and Path(e.__file__)==HELPER,'Original helper root must remain unchanged')
    extension_raw=bootstrap_read(extension_ref['path'])
    require(digest(extension_raw)==extension_ref['sha256'],'Extension review changed')
    extension=json.loads(extension_raw)
    check_disposition(extension)
    return e,extension,review


def check_disposition(value):
    require(value['schema']=='rebol-extension-actual-build-layout-load-review-v1'
        and value['status']=='qualified-exact-extension-build-layout-load'
        and value['independent_review'] is True and value['extension_abi_qualified'] is True
        and all(value[k] is False for k in GATES)
        and value['failed_sdk_producer_preserved'] is True
        and value['native_processes']==4 and value['benchmark_samples']==0,
        'Actual independently reviewed four-command extension disposition required')
    require(set(value['references'])=={'plan','report','terminal','toolchain_intake','source_review'},
            'Exact extension evidence references required')
    for item in value['references'].values(): ref(item['path'],item['sha256'])
    require(set(value['durable'])=={'directory','artifacts','lease'},'Closed extension durable inventory required')
    job=Path(value['durable']['directory'])
    require(job.is_relative_to(ROOT/'experiments/shared/owned-jobs-v1/owned-jobs')
        and Path(value['durable']['lease']['path'])==job/'owner.lock','Extension lease/job join differs')
    require(set(value['durable']['lease'])=={'path','device','inode'}
        and all(type(value['durable']['lease'][k]) is int for k in ('device','inode')),'Exact extension lease identity required')


@contextmanager
def held(extension_ref, source_ref):
    e,initial_extension,initial_source=bootstrap(extension_ref,source_ref)
    intake_ref=initial_extension['references']['toolchain_intake']
    with e.held_inputs(intake_ref) as (common,leases,intake,pins,resolutions):
        source=e.document(source_ref,pins,resolutions)
        extension=e.document(extension_ref,pins,resolutions)
        require(source==initial_source and extension==initial_extension,'Review changed after lock acquisition')
        for name,expected in {**source['files'],**source['dependencies']}.items():
            e.pin(pins,resolutions,ROOT/name,expected)
        check_disposition(extension)
        lease=extension['durable']['lease'];path=Path(lease['path'])
        require(path not in e.LEASE_PATHS and path!=e.LOCK,'Duplicate inherited lease')
        with e.regular(path) as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            # The outer helper owns its original list and checks it after this
            # inner stream closes. Never append a shorter-lived stream to it.
            combined=leases+[(path,stream,(lease['device'],lease['inode']))]
            e.check_leases(combined)
            adapter_raw=e.read_bytes(ADAPTER)
            require(digest(adapter_raw)==source['files'][str(ADAPTER.relative_to(ROOT))],'Adapter source changed')
            adapter=types.ModuleType('rebol_fixture_transport');adapter.__file__=str(ADAPTER)
            exec(compile(adapter_raw,str(ADAPTER),'exec'),adapter.__dict__)
            inspector=e.load_support(pins,resolutions)
            try: yield e,adapter,inspector,common,combined,intake,extension,pins,resolutions
            finally: e.check_leases(combined)


def exact_snapshot(e, path):
    raw=e.read_bytes(path)
    return raw,dict(bytes=len(raw),sha256=digest(raw))


def extension_inputs(e, inspector, extension, intake, pins, resolutions):
    """Replay immutable evidence; independent disposition scopes native ABI only."""
    refs=extension['references']
    plan=e.document(refs['plan'],pins,resolutions)
    report=e.document(refs['report'],pins,resolutions)
    terminal=e.document(refs['terminal'],pins,resolutions)
    source=e.document(refs['source_review'],pins,resolutions)
    e.validate_intake(intake,source,refs['source_review'],pins,resolutions)
    require(plan['schema']=='rebol-extension-build-layout-load-plan-v1'
        and plan['repository']==str(ROOT) and plan['controller']==str(HELPER)
        and plan['controller_sha256']==pins[str(HELPER)]
        and plan['source_review']==refs['source_review'] and plan['toolchain_intake']==refs['toolchain_intake']
        and plan['schedule']==e.schedule(intake,Path(plan['output']))
        and plan['native_processes']==4 and plan['automatic_retry'] is False,
        'Reviewed original extension plan differs')
    output=e.physical(Path(plan['output']))
    require(output.is_relative_to(e.PACKET) and refs['report']['path']==str(output/'report.json')
        and refs['terminal']['path']==str(output/'terminal.json'),'Original extension output references differ')
    require(report['schema']=='rebol-extension-build-layout-load-results-v1'
        and terminal['schema']=='rebol-extension-build-layout-load-terminal-v1'
        and report['status']==terminal['status']==e.SUCCESS
        and report['plan']==refs['plan']['path'] and report['plan_sha256']==refs['plan']['sha256']
        and report['attempts']==e.IDS and [x['id'] for x in report['captures']]==e.IDS
        and [x['id'] for x in report['registered']]==e.IDS and report['active'] is None
        and len({x['pid'] for x in report['registered']})==4
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==refs['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==4
        and terminal['validated_captures']==4
        and all(report[k] is terminal[k] is False for k in e.GATES),'Extension native stage is not closed successfully')
    for name,expected in plan['pins'].items():
        e.pin(pins,resolutions,name,expected)
        require(resolutions[name]==plan['input_resolutions'][name],'Original extension named input changed')
    generated,sdk_closures=e.retained_sdk(pins,resolutions)
    require(generated==plan['generated_outputs'] and extension['sdk_output_reuse']==dict(path=str(e.REUSE),sha256=e.REUSE_SHA),
            'Failed SDK/output-reuse identity differs')
    require(extension['corrected_source']==dict(path=str(e.PACKET/'clbg_primitives.c'),
        sha256=pins[str(e.PACKET/'clbg_primitives.c')]),'Corrected C source differs')
    image=extension['built_image'];require(image['path']==str(output/'build/clbg_primitives.dylib'), 'Wrong extension image')
    e.pin(pins,resolutions,image['path'],image['sha256'])
    require(report['validated_build_artifacts']['build/clbg_primitives.dylib']['sha256']==image['sha256'],
            'Actual built extension is not the approved image')
    require(extension['declared_image_closure']==report['captures'][2]['native_layout_and_images']['declared_image_closure'],
            'Approved static image scope differs')
    available=e.inventory(output,('terminal.json',))[0]
    require(available==terminal['available_evidence'],'Closed extension artifact inventory changed')
    complete=dict(available,**{'terminal.json':dict(bytes=len(e.read_bytes(output/'terminal.json')),sha256=refs['terminal']['sha256'])})
    for name,item in complete.items(): e.pin(pins,resolutions,output/name,item['sha256'])
    durable=extension['durable'];job=e.physical(Path(durable['directory']))
    actual=e.inventory(job,('owner.lock',))[0]
    require(actual==durable['artifacts'],'Closed extension durable inventory changed')
    require({'command-started.json','terminal.json','launch.json'}<=set(actual),'Incomplete extension durable receipts')
    for name,item in actual.items():e.pin(pins,resolutions,job/name,item['sha256'])
    started=json.loads(e.read_bytes(job/'command-started.json'))
    ended=json.loads(e.read_bytes(job/'terminal.json'));launch=json.loads(e.read_bytes(job/'launch.json'))
    expected=[str(e.PYTHON),'-I','-S','-B',str(HELPER),'run','--plan',refs['plan']['path'],'--plan-sha256',refs['plan']['sha256']]
    check_durable_controller(launch,started,ended,expected)
    for slot,registration,capture in zip(plan['schedule'],report['registered'],report['captures']):
        observed,snapshot=e.checked_capture(slot,output/slot['directory'],started['command_pid'],inspector.kb)
        require(all(capture.get(k)==v for k,v in observed.items()) and observed['pid']==registration['pid']
            and snapshot==report['validated_artifacts'][slot['directory']], 'Original four capture identities differ')
    closures=sdk_closures+[dict(directory=str(output),artifacts=complete)]
    # Durable lock files are held by inode and deliberately not file-hashed.
    return plan,closures,dict(directory=str(job),artifacts=actual),image


def check_durable_controller(launch,started,ended,expected):
    """Zero exit retains the launcher's awaiting-report-review disposition."""
    require(started['command']==launch['command']==expected and started['cwd']==launch['cwd']==str(ROOT)
        and ended['status']=='command-exited-zero-awaiting-report-review'
        and type(ended['exit_code']) is int and ended['exit_code']==0
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False
        and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
        and started['command_identity_observation_missing'] is False
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
        and started['command_identity']==ended['command_identity'],'Closed extension durable command differs')


def compile_slot(e, intake, output):
    roots=intake['include_roots'];tools=intake['tools'];build=output/'build'
    argv=[tools['clang']['path'],'--no-default-config','-target',intake['target'],
        '-std=c11','-O2','-Wall','-Wextra','-Werror','-D_DARWIN_C_SOURCE','-fno-modules','-nostdinc',
        '-isysroot',roots['macos_sdk'],'-resource-dir',str(Path(roots['clang_resource']).parent),
        '-fuse-ld='+tools['linker']['path'],'-isystem',roots['clang_resource'],
        '-isystem',str(Path(roots['macos_sdk'])/'usr/include'),'-MD','-MT','dependencies',
        '-MF',str(build/'interposer.d'),'-dynamiclib',str(ORIGINAL/'io-faults.c'),
        '-Wl,-install_name,@rpath/io-faults.dylib','-Wl,-map,'+str(build/'interposer.map'),
        '-o',str(build/'io-faults.dylib')]
    return dict(id='compile-io-interposer',directory='00-compile-io-interposer',command=argv,
        environment=e.environment(output),timeout_seconds=300,rss_limit_bytes=2*1024**3,
        stream_limit_bytes=64*1024**2,stdin_bytes=0,stdin_sha256=digest(b''),sidecars={})


def schedule(e, adapter, spec, intake, image, output):
    require(spec['schema']=='rebol-general-primitive-fixtures-source-v1' and spec['case_count']==18
        and tuple(c['id'] for c in spec['cases'])==adapter.CASE_IDS,'Exact original eighteen-case order required')
    slots=[compile_slot(e,intake,output)]
    for index,case in enumerate(spec['cases'],1):
        directory=f'{index:02d}-'+case['id'];destination=output/directory
        substitution=dict(runtime=intake['tools']['runtime']['path'],fixture_root=str(ORIGINAL),
            output=str(destination),qualified_io_fault_interposer=str(output/'build/io-faults.dylib'))
        argv=[arg.format(**substitution) for arg in case['argv']]
        require(argv[:3]==[str(e.RUNTIME),'-q','-s'],'Original fixture invocation changed')
        payload,expected=adapter.case_bytes(case)
        environment=e.environment(output)
        environment.update(MECH_CLBG_REBOL_PRIMITIVES=image['path'],MECH_REBOL_FIXTURE_SUPPORT=str(e.SUPPORT))
        if case['id']=='pipe-injected-short-io':
            require(set(case['environment_additions'])=={'DYLD_INSERT_LIBRARIES','MECH_REBOL_IO_FAULT_REPORT'},'Fault environment differs')
            environment.update({k:v.format(**substitution) for k,v in case['environment_additions'].items()})
        else:
            require('environment_additions' not in case and all(k not in environment for k in spec['absent_environment_for_ordinary_cases']),
                    'Ordinary case acquired an interposer/environment override')
        sidecars={k:case[k]['path'].format(**substitution) for k in ('sidecar','fault_sidecar') if k in case}
        require(all(Path(path).parent==destination for path in sidecars.values()),'Sidecar escaped owned case directory')
        slots.append(dict(id=case['id'],directory=directory,command=argv,environment=environment,
            timeout_seconds=180,rss_limit_bytes=512*1024**2,stream_limit_bytes=1024**2,
            stdin_bytes=len(payload),stdin_sha256=digest(payload),input_path=str(output/'inputs'/(case['id']+'.bin')),
            expected_stdout_bytes=len(expected),expected_stdout_sha256=digest(expected),
            sidecars=sidecars,case=case))
    return slots


def build_plan(e, adapter, inspector, output, extension_ref, source_ref, intake, extension, pins, resolutions):
    e.physical(output);require(output.is_relative_to(PACKET) and output!=PACKET and not os.path.lexists(output),'Fresh fixture output required')
    prior,closures,durable,image=extension_inputs(e,inspector,extension,intake,pins,resolutions)
    spec=e.document(dict(path=str(ORIGINAL/'spec.json'),sha256=SPEC_SHA),pins,resolutions)
    review=e.document(extension['fixture_source_review'],pins,resolutions)
    require(review['schema']=='rebol-general-primitive-fixtures-source-review-v1'
        and review['status']=='independent-source-review-complete-native-gates-pending'
        and review['source_review']['independent'] is True,'Original fixture review required')
    for name,expected in spec['fixture_source_pins'].items():
        require(review['files'].get(str((ORIGINAL/name).relative_to(ROOT)))==expected,'Original fixture source review differs')
        e.pin(pins,resolutions,ORIGINAL/name,expected)
    require(review['files'][str((ORIGINAL/'spec.json').relative_to(ROOT))]==SPEC_SHA,'Original fixture spec identity differs')
    # Preserve every old source pin, including the old C revision as historical
    # input. Only the explicitly approved actual image selects corrected C.
    for name,expected in spec['immutable_source_pins'].items():e.pin(pins,resolutions,ROOT/name,expected)
    facades={str(e.SUPPORT/name):spec['immutable_source_pins'][str((e.SUPPORT/name).relative_to(ROOT))]
        for name in ('clbg_io.reb','clbg_primitives.reb','clbg_big.reb','clbg_regex.reb')}
    require(extension['unchanged_facades']==facades,'Exact retained loader/facades missing from disposition')
    header=str(Path(intake['include_roots']['macos_sdk'])/'usr/include/mach-o/dyld-interposing.h')
    require(header in intake['input_pins'] and pins.get(header)==intake['input_pins'][header],
            'Selected official dyld interposition header must be in reviewed intake')
    require(spec['limits']==dict(per_process_seconds=180,per_process_rss_bytes=536870912,
        stdout_limit_bytes=1048576,stderr_limit_bytes=1048576,automatic_retry=False),'Original bounded policy differs')
    return dict(schema='rebol-primitive-fixtures-plan-v2',status='prepared-awaiting-independent-review',
        repository=str(ROOT),controller=str(Path(__file__).resolve()),controller_sha256=e.sha(__file__),
        output=str(output),extension_review=extension_ref,source_review=source_ref,
        toolchain_intake=extension['references']['toolchain_intake'],
        schedule=schedule(e,adapter,spec,intake,image,output),pins=dict(pins),input_resolutions=dict(resolutions),
        unavailable_inputs=prior['unavailable_inputs'],prerequisite_artifact_closures=closures,
        extension_durable=durable,extension_image=image,corrected_source=extension['corrected_source'],
        historical_spec=dict(path=str(ORIGINAL/'spec.json'),sha256=SPEC_SHA),
        historical_old_c_preserved=True,failed_sdk_producer_preserved=True,
        native_processes=19,fixture_processes=18,diagnostic_compilations=1,benchmark_samples=0,
        automatic_retry=False,cleanup_timeout_seconds=5,common_mutex_inode=79859134,
        **{k:False for k in GATES})


def verify_inputs(e, plan, pins, resolutions, leases):
    e.verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures'])
    durable=plan['extension_durable']
    require(e.inventory(Path(durable['directory']),('owner.lock',))[0]==durable['artifacts'],
            'Closed extension durable membership changed')
    e.check_leases(leases)


def checked_capture(e, slot, directory, parent, kb, extra):
    snapshot=e.inventory(directory)[0]
    require(set(snapshot)==CAPTURE_FILES|set(extra),'Unexpected/missing native capture artifact')
    require(all(snapshot.get(name)==value for name,value in extra.items()),'Validated sidecar/transport bytes changed')
    start,active,final=[json.loads(e.read_bytes(directory/(name+'.json'))) for name in ('start','active','process')]
    for value in (start,active,final):
        require(value['command']==slot['command'] and value['environment']==slot['environment']
            and value['cwd']==str(directory) and value['kind']==KIND and value['started_at']==start['started_at']
            and value['process_timeout_seconds']==slot['timeout_seconds'] and value['cleanup_timeout_seconds']==5
            and value['maximum_process_group_rss_bytes']==slot['rss_limit_bytes']
            and value['native_file_limit_bytes']==slot['stream_limit_bytes']
            and value['stdout_capture_limit_bytes']==slot['stream_limit_bytes']+kb.PIPE_CHUNK
            and value['stdout_transport']=='OS pipe, retained as received' and value['stderr_transport']=='exclusive artifact'
            and value['stdin_bytes']==slot['stdin_bytes'] and value['stdin_sha256']==slot['stdin_sha256']
            and value['inherited_common_mutex'] is True and value['common_mutex_inode']==79859134
            and value['source_work_qualified'] is value['chart_admission'] is False,'Native capture contract differs')
    identity,leader,pid=final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status']=='starting' and start['native_process_started'] is False
        and active['status']=='running' and active['native_process_started'] is final['native_process_started'] is True
        and active['identity']==identity and identity['ppid']==parent
        and all(type(identity[k]) is int and identity[k]==leader[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and active['pid']==active['pgid']==pid==final['pgid']==identity['pid']==identity['pgid']
        and leader['status']==5 and final['direct_child_reaped'] is True
        and final['remaining_process_group']==final.get('remaining_after_cleanup',[])==[]
        and final['stop_signals']==final['cleanup_errors']==[] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and not final.get('error') and not final.get('error_type')
        and final.get('timed_out',False) is False and final['status']=='native-passed'
        and type(final['exit_status']) is int and final['exit_status']==0
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples']>0,
        'Native ownership/exit/cleanup differs')
    peak=final['observed_peak_process_group_rss_bytes']
    require(type(peak) is int and 0<=peak<=slot['rss_limit_bytes'],'Invalid RSS observation')
    if peak==0:require(identity['status']==5 and not final.get('live_rss_observation_obtained',False),'Zero RSS lacks initial owned zombie proof')
    require(datetime.fromisoformat(start['started_at'])<=datetime.fromisoformat(final['finished_at']),'Inverted capture interval')
    for name in ('stdout','stderr'):
        require(snapshot[name+'.bin']==dict(bytes=final[name+'_bytes'],sha256=final[name+'_sha256'])
            and final[name+'_bytes']<=slot['stream_limit_bytes'],'Stream changed or exceeded acceptance limit')
    require(final['stderr_bytes']==0,'Unknown stderr')
    require(e.inventory(directory)[0]==snapshot,'Capture changed during independent check')
    return dict(id=slot['id'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        observed_peak_process_group_rss_bytes=peak or None,rss_observation_complete=False,memory_usage_qualified=False),snapshot


def observe_case(e, adapter, kb, slot, output, common, launched):
    case=slot['case'];payload,_=adapter.case_bytes(case);directory=output/slot['directory']
    handle=adapter.regular_input(Path(slot['input_path']),payload) if case['stdin'].get('transport')=='regular-file' else nullcontext(None)
    transport=None;observed={};retention_errors=[]
    try:
        with handle as regular:
            transport=adapter.Transport(case,regular=regular)
            kb.observe(slot['command'],slot['environment'],directory,payload,common,launched,
                kind=KIND,launch=transport.launch,transfer=transport.transfer)
    finally:
        # Sidecars remain in their original owned location even when decoding or
        # observation fails. Snapshot every readable one before any check_case.
        with kb.atomic():
            if transport is not None:
                try:
                    raw=encoded(transport.record);kb.save(directory/'transport.json',transport.record)
                    require(e.read_bytes(directory/'transport.json')==raw,'Transport record changed at save')
                    observed['transport.json']=dict(bytes=len(raw),sha256=digest(raw))
                except BaseException as error:
                    retention_errors.append(dict(path=str(directory/'transport.json'),error=str(error) or type(error).__name__))
            for name in slot['sidecars'].values():
                path=Path(name)
                if os.path.lexists(path):
                    try: observed[path.name]=exact_snapshot(e,path)[1]
                    except BaseException as error:retention_errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
            if retention_errors:kb.save(directory/'sidecar-retention-errors.json',retention_errors)
    require(transport is not None,'Missing transport registration')
    record=transport.record
    require(record['spawn_hook_called'] is True and record['transfer_completed'] is True
        and record['stdout_eof'] is True and record['parent_epipe'] is False
        and record['parent_read_bytes']==slot['expected_stdout_bytes'],'Incomplete observed transport')
    if record['requested_transport']=='pipe':
        require(record['stdin_closed'] is True and record['parent_write_bytes']==len(payload),'Incomplete pipe input')
    else:
        require(record['spawn_stdin_descriptor']['type']=='regular-file' and record['parent_write_bytes']==0,
                'Regular file was silently pumped through a pipe')
    require(not retention_errors,'Sidecar retention failed')
    sidecars={}
    for key,path in slot['sidecars'].items():
        raw,snapshot=exact_snapshot(e,Path(path));require(observed.get(Path(path).name)==snapshot,'Sidecar changed before decode')
        sidecars[key]=raw
    stdout,stdout_snapshot=exact_snapshot(e,directory/'stdout.bin')
    stderr,stderr_snapshot=exact_snapshot(e,directory/'stderr.bin')
    process=json.loads(e.read_bytes(directory/'process.json'))
    result=adapter.check_case(case,stdout,stderr,process['exit_status'],**sidecars)
    require(stdout_snapshot==dict(bytes=slot['expected_stdout_bytes'],sha256=slot['expected_stdout_sha256']),
            'Fixture oracle digest differs')
    return result,observed


def expected_files(plan):
    result={'build/'+name for name in BUILD_FILES}
    for slot in plan['schedule']:
        result.update(str(Path(slot['directory'])/name) for name in CAPTURE_FILES)
        if 'case' in slot:
            result.add(str(Path(slot['input_path']).relative_to(plan['output'])))
            result.add(str(Path(slot['directory'])/'transport.json'))
            result.update(str(Path(path).relative_to(plan['output'])) for path in slot['sidecars'].values())
    return result


def finish(e, report, plan, output, pins, resolutions, kb, leases):
    errors=[];held=False
    available,artifact_errors=e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        ids=[slot['id'] for slot in plan['schedule']]
        require(report['attempts']==ids[:len(report['attempts'])] and len(report['attempts'])<=19,'Attempt prefix differs')
        require([r['id'] for r in report['registered']]==report['attempts'][:len(report['registered'])]
            and len({r['pid'] for r in report['registered']})==len(report['registered']),'Native registration differs')
        require(report['active'] is None and not artifact_errors,'Open native/artifact failure')
        for slot in plan['schedule'][:len(report['attempts'])]:
            record=json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration=next((r for r in report['registered'] if r['id']==slot['id']),None)
            require(record['cleanup_errors']==[] and not record.get('artifact_errors'),'Native cleanup failed')
            if registration:
                require(record['pid']==registration['pid'] and record['direct_child_reaped'] is True
                    and record.get('remaining_process_group',[])==record.get('remaining_after_cleanup',[])==[],'Owned child/group not closed')
            else:require(record['native_process_started'] is False,'Unregistered native process')
        require(all(available.get(name)==snapshot for name,snapshot in report['validated_files'].items()),
                'Previously validated artifact changed or disappeared')
        if report['status']==SUCCESS:
            require(len(report['attempts'])==len(report['registered'])==len(report['captures'])==19
                and set(available)==set(report['validated_files'])==expected_files(plan),'Incomplete fixed nineteen-process stage')
        verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:report['status']='failed-integrity'
    raw=encoded(report);kb.save(output/'report.json',report);closure={}
    try:
        require(e.read_bytes(output/'report.json')==raw,'Serialized report changed')
        closure=e.inventory(output,('terminal.json',))[0]
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),'Final artifact/report inventory differs')
        verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0]==closure,'Output changed during final input replay')
        report_sha=e.sha(output/'report.json');require(report_sha==digest(raw),'Final report digest differs')
        e.check_leases(leases);held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);report['status']='failed-integrity';closure={};report_sha=None
    terminal=dict(schema='rebol-primitive-fixtures-terminal-v2',status=report['status'],
        report_sha256=report_sha,expected_report_sha256=digest(raw),available_evidence=closure,
        integrity_errors=errors,artifact_errors=artifact_errors,common_mutex_held=held,common_mutex_inode=79859134,
        native_processes_started=len(report['registered']),validated_captures=len(report['captures']),
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in GATES})
    with (output/'terminal.json').open('xb') as stream:stream.write(encoded(terminal))
    require(not errors and not artifact_errors,'Final integrity failed; failure evidence retained')


def run(e, adapter, inspector, plan, plan_path, plan_sha, intake, pins, resolutions, common, leases):
    output=Path(plan['output']);kb=inspector.kb;e.pin(pins,resolutions,plan_path,plan_sha)
    verify_inputs(e,plan,pins,resolutions,leases);output.mkdir(parents=True,exist_ok=False)
    for name in ('build','home','tmp','inputs'):(output/name).mkdir()
    report=dict(schema='rebol-primitive-fixtures-results-v2',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=e.now(),active=None,attempts=[],registered=[],captures=[],validated_files={},
        pins=pins,input_resolutions=resolutions,extension_review=plan['extension_review'],
        failed_sdk_producer_preserved=True,benchmark_samples=0,**{k:False for k in GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule'][1:]:
            payload,_=adapter.case_bytes(slot['case']);path=Path(slot['input_path'])
            with path.open('xb') as stream:stream.write(payload)
            raw,snapshot=exact_snapshot(e,path)
            require(raw==payload and snapshot==dict(bytes=slot['stdin_bytes'],sha256=slot['stdin_sha256']),'Prepared stdin changed')
            report['validated_files'][str(path.relative_to(output))]=snapshot
        for index,slot in enumerate(plan['schedule']):
            verify_inputs(e,plan,pins,resolutions,leases)
            current=e.inventory(output,('report.json',))[0]
            require(current==report['validated_files'],'Earlier artifact membership/bytes changed before next process')
            directory=output/slot['directory'];directory.mkdir()
            with kb.atomic():report['attempts'].append(slot['id']);kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid));report['active']=dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT=slot['timeout_seconds'];kb.RSS_LIMIT=slot['rss_limit_bytes'];kb.FILE_LIMIT=slot['stream_limit_bytes']
            kb.CLEANUP_TIMEOUT=5
            if index==0:
                kb.observe(slot['command'],slot['environment'],directory,b'',common,launched,kind=KIND)
                decoded=None;extra={}
            else:decoded,extra=observe_case(e,adapter,kb,slot,output,common,launched)
            with kb.atomic():
                report['active']=None
                capture,snapshot=checked_capture(e,slot,directory,os.getpid(),kb,extra)
                if index==0:
                    require(e.read_bytes(directory/'stdout.bin')==b'','Compiler stdout differs')
                    capture['actual_compiler_inputs']=e.validate_compile_inputs(output,'interposer',ORIGINAL/'io-faults.c',pins,resolutions)
                    image=output/'build/io-faults.dylib'
                    closure=e.built_image_closure([image],intake,inspector,pins)
                    require(set(closure['images'])=={str(image)},'Diagnostic interposer acquired non-OS dependencies')
                    capture['built_declared_image_closure']=closure
                    build=e.inventory(output/'build')[0]
                    require(set(build)==BUILD_FILES and all(v['bytes']>0 for v in build.values()),'Missing/unexpected interposer outputs')
                    report['validated_files'].update({str(Path('build')/name):value for name,value in build.items()})
                else:capture['fixture_observations']=decoded
                if report['captures']:
                    require(datetime.fromisoformat(report['captures'][-1]['finished_at'])<=datetime.fromisoformat(capture['started_at']),
                            'Native commands overlapped')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):value for name,value in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        with kb.atomic():report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():finish(e,report,plan,output,pins,resolutions,kb,leases)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prepare=sub.add_parser('prepare');prepare.add_argument('--plan',type=Path,required=True);prepare.add_argument('--output',type=Path,required=True)
    for name in ('extension-review','source-review'):
        prepare.add_argument('--'+name,type=Path,required=True);prepare.add_argument('--'+name+'-sha256',required=True)
    execute=sub.add_parser('run');execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,'Use retained Python -I -S -B')
    def stop(signum,frame):raise KeyboardInterrupt('Primitive fixture stage stopped: '+str(signum))
    for value in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(value,stop)
    if args.mode=='prepare':
        extension_ref=ref(args.extension_review,args.extension_review_sha256);source_ref=ref(args.source_review,args.source_review_sha256)
        output=args.output;saved=None
    else:
        raw=bootstrap_read(args.plan,64*1024**2);require(digest(raw)==args.plan_sha256,'Prepared plan changed')
        saved=json.loads(raw);extension_ref=saved['extension_review'];source_ref=saved['source_review'];output=Path(saved['output'])
    with held(extension_ref,source_ref) as (e,adapter,inspector,common,leases,intake,extension,pins,resolutions):
        require(Path(sys.executable).resolve()==e.PYTHON.resolve(),'Retained Python required')
        plan=build_plan(e,adapter,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions)
        verify_inputs(e,plan,pins,resolutions,leases)
        if args.mode=='prepare':
            e.physical(args.plan);require(args.plan.is_relative_to(PACKET) and not args.plan.is_relative_to(output),'Plan must be separate inside packet')
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            raw=encoded(plan)
            with inspector.kb.atomic():
                with args.plan.open('xb') as stream:stream.write(raw)
                verify_inputs(e,plan,pins,resolutions,leases)
                require(e.read_bytes(args.plan)==raw,'Prepared plan changed before closure');e.check_leases(leases)
            result=dict(plan=str(args.plan),sha256=digest(raw),native_processes_started=0)
        else:
            require(saved==plan,'Prepared fixed stage does not replay exactly')
            run(e,adapter,inspector,plan,args.plan,args.plan_sha256,intake,pins,resolutions,common,leases)
            result=dict(status='captures-closed-awaiting-independent-review',output=str(output),qualified=False)
    print(json.dumps(result))


if __name__=='__main__':main()
