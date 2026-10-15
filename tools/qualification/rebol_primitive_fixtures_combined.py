"""Explicit combined-extension intake for the unchanged fixed nineteen fixtures."""
import argparse
from contextlib import contextmanager,ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'tools/qualification/rebol_primitive_fixtures.py'
PACKET=ROOT/'experiments/rebol/primitive-fixtures-v2/combined-intake-v1'
COMBINED=ROOT/'experiments/rebol/extension-api-v2/extension-import-v1/combined-extension-review-v1.json'
COMBINED_SHA='8b8a45736f0bb6cdc60a07d22b19759dc6dfa658ebb7bb77f40007d4c29242d5'
HEADER_ROOT=ROOT/'experiments/rebol/primitive-fixtures-v2/diagnostic-headers-v1/include'
HEADER=HEADER_ROOT/'mach-o/dyld-interposing.h'
HEADER_SHA='763eeb269c19216b7963345567b9d20ca6591c73249571019a8763f8fcdc0e71'
HEADER_REVIEW=dict(path=str(HEADER_ROOT.parent/'source-review.json'),sha256='bdddfbb718f1a18550a3cbfad09f2cf1c7641615d55d5074388dd62291284204')
DEPENDENCIES={
 'tools/qualification/rebol_primitive_fixtures.py':'3c9c7367be14d02573fd5feec42881d9e59f2c4d2e301e4ae36f19327815216c',
 'tools/qualification/test_rebol_primitive_fixtures.py':'fa4c41aabf1efeb3b771fd9bd97754c8b22aa91a5027b9b383cdae043ac72b76',
 'experiments/rebol/primitive-fixtures-v2/adapter.py':'650dfd32506af6694cff2b42714e8dc2d5e40774cdf9b1b4028c30e47f74e2d5',
 'experiments/rebol/primitive-fixtures-v2/test_adapter.py':'271dd168c8c58fae9b99ab47e3a9ec153d3d3a602c064a40976e85c37ec1b5b9',
 'experiments/rebol/primitive-fixtures-v2/README.md':'1d3adb851313e0d03d78ed6e70e1bdcdbda1dd0c5ff11a57bb403a04a24ba5e8',
 'tools/qualification/rebol_extension_rebx_load.py':'a9d69c8c07ba7fb592f34563114506715053d5195fbc63d7b646888b60554961',
 'tools/qualification/rebol_extension_load_only.py':'54fc9c69dba361cb49dc8c5cb20872c6a280f986bec6dbc8d7c5745216fd631f',
 'tools/qualification/rebol_extension_typed_images.py':'bec9d1e020cfd2449ecdd5e1dced224f6ccbf050785fd9390e3d07931d499124',
 'tools/qualification/rebol_extension.py':'8bfd7b7def7562ca810ce633dc5b92455fb29df66fc3a727641ffcc62b516493'}
SOURCE_FILES={str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),Path(__file__).with_name('test_rebol_primitive_fixtures_combined.py'),PACKET/'README.md')}
STAGES=('original_build','scoped_load_failure','rebx_load')
GATES=('full_primitive_fixtures_qualified','benchmark_correctness_qualified','runtime_source_equivalence_proven','source_work_qualified','canonical_source_count_qualified','full_timing_qualified','chart_admission')

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def compiled(path,expected,reader):
    raw=reader(path);require(digest(raw)==expected,'Frozen dependency changed: '+str(path))
    module=types.ModuleType(path.stem+'_combined_intake');module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__);return module

def check_disposition(value):
    require(value['schema']=='rebol-extension-combined-build-layout-load-review-v1'
        and value['status']=='qualified-exact-combined-extension-build-layout-load'
        and value['independent_review'] is value['extension_abi_qualified'] is True
        and all(value[k] is False for k in GATES),'Actual combined ABI-only disposition required')
    require((value['native_processes'],value['native_attempts'],value['successful_logical_stages'],value['compilations'],value['failed_loads'],value['benchmark_samples'])==(6,6,4,2,2,0)
        and value['failed_sdk_producer_preserved'] is value['original_failed_stage_preserved'] is value['failed_scoped_load_preserved'] is True,'Actual successes and failures must remain distinct')
    require(set(value['references'])=={'toolchain_intake','source_review',*STAGES}
        and [x['stage'] for x in value['durables']]==list(STAGES)
        and [x['exit_code'] for x in value['durables']]==[1,1,0]
        and [x['stage'] for x in value['successful_stages']]==['original_build']*3+['rebx_load']
        and [x['id'] for x in value['successful_stages']]==['build-extension','build-layout-probe','layout-and-exports','load-nine-commands-rebx']
        and len(value['retained_failed_loads'])==2,'Exact three-job/four-success/two-failure join required')
    require(value['built_image']==value['image_copy']['alias'] and value['original_built_image']==value['image_copy']['original']
        and value['built_image']['sha256']==value['original_built_image']['sha256']
        and value['image_copy']['byte_identical'] is True and value['image_copy']['binary_rebuilt'] is False,'Approved byte-identical image required')

def check_success(f,e,load,plan,refs,durable,pins,resolutions,inspector):
    report=e.document(refs['report'],pins,resolutions);terminal=e.document(refs['terminal'],pins,resolutions)
    out=Path(plan['output']);slot=plan['schedule'][0]
    require(refs['report']['path']==str(out/'report.json') and refs['terminal']['path']==str(out/'terminal.json')
        and report['status']==terminal['status']==load.SUCCESS
        and report['plan']==refs['plan']['path'] and report['plan_sha256']==refs['plan']['sha256']
        and report['attempts']==[load.ID] and report['active'] is None
        and len(report['registered'])==len(report['captures'])==1
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==refs['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==terminal['validated_captures']==1
        and all(report[k] is terminal[k] is False for k in e.GATES),'Successful load receipt differs')
    job=Path(durable['directory']);launch,started,ended=[json.loads(e.read_bytes(job/n)) for n in ('launch.json','command-started.json','terminal.json')]
    expected=[str(e.PYTHON),'-I','-S','-B',refs['entrypoint']['path'],'--adapter-sha256',refs['entrypoint']['sha256'],'run','--plan',refs['plan']['path'],'--plan-sha256',refs['plan']['sha256']]
    f.check_durable_controller(launch,started,ended,expected)
    observed,snapshot=e.checked_capture(slot,out/slot['directory'],started['command_pid'],inspector.kb)
    require(observed==report['captures'][0] and observed['pid']==report['registered'][0]['pid']
        and e.read_bytes(out/slot['directory']/'stdout.bin')==e.LOAD_OUTPUT
        and report['validated_artifacts']==report['artifacts']=={str(Path(slot['directory'])/n):v for n,v in snapshot.items()},'Exact successful smoke output/capture changed')
    require(e.inventory(out,('terminal.json',))[0]==terminal['available_evidence'],'Successful load inventory changed')
    complete=e.inventory(out)[0]
    for name,item in complete.items():e.pin(pins,resolutions,out/name,item['sha256'])
    return dict(directory=str(out),artifacts=complete)

def attach(f,adapter_ref,rebx):
    load=rebx.load_controller(DEPENDENCIES['tools/qualification/rebol_extension_rebx_load.py'])
    original_compile=f.compile_slot
    def bootstrap(extension_ref,source_ref):
        require(extension_ref==dict(path=str(COMBINED),sha256=COMBINED_SHA),'Exact completed extension disposition required')
        raw=f.bootstrap_read(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Source review changed');review=json.loads(raw)
        require(review['schema']=='rebol-combined-primitive-controller-source-review-v1'
            and review['status']=='independent-source-review-complete-native-fixtures-pending'
            and review['independent_review'] is True and set(review['files'])==SOURCE_FILES
            and review['dependencies']==DEPENDENCIES and all(review[k] is False for k in GATES)
            and review['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256'],'Exact additive source review required')
        for name,expected in {**review['files'],**review['dependencies']}.items():require(digest(f.bootstrap_read(ROOT/name))==expected,'Source dependency changed')
        raw=f.bootstrap_read(extension_ref['path']);require(digest(raw)==extension_ref['sha256'],'Combined disposition changed')
        extension=json.loads(raw);check_disposition(extension);e=load.load_helper()
        require(e.ROOT==ROOT and Path(e.__file__)==f.HELPER,'Original extension helper identity differs')
        return e,extension,review
    @contextmanager
    def held(extension_ref,source_ref):
        e,initial_extension,initial_source=bootstrap(extension_ref,source_ref)
        with e.held_inputs(initial_extension['references']['toolchain_intake']) as (common,leases,intake,pins,resolutions):
            extension=e.document(extension_ref,pins,resolutions);review=e.document(source_ref,pins,resolutions)
            require(extension==initial_extension and review==initial_source,'Review changed after acquisition')
            for name,expected in {**review['files'],**review['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,expected)
            with ExitStack() as stack:
                combined=list(leases)
                for durable in extension['durables']:
                    lease=durable['lease'];path=Path(lease['path'])
                    require(path==Path(durable['directory'])/'owner.lock' and path not in [x[0] for x in combined],'Distinct original stage lease required')
                    stream=stack.enter_context(e.regular(path));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    combined.append((path,stream,(lease['device'],lease['inode'])))
                e.check_leases(combined)
                transport=compiled(f.ADAPTER,DEPENDENCIES[str(f.ADAPTER.relative_to(ROOT))],e.read_bytes)
                inspector=e.load_support(pins,resolutions)
                try:yield e,transport,inspector,common,combined,intake,extension,pins,resolutions
                finally:e.check_leases(combined)
    def extension_inputs(e,inspector,extension,intake,pins,resolutions):
        check_disposition(extension);refs=extension['references'];base_refs=refs['original_build']
        old=e.document(base_refs['plan'],pins,resolutions);new=e.document(refs['rebx_load']['plan'],pins,resolutions)
        require(old['toolchain_intake']==new['toolchain_intake']==refs['toolchain_intake']
            and old['source_review']==new['source_review']==refs['source_review'],'Common source/intake join differs')
        source=e.document(refs['source_review'],pins,resolutions);e.validate_intake(intake,source,refs['source_review'],pins,resolutions)
        for plan in (old,new):
            for name,expected in plan['pins'].items():
                e.pin(pins,resolutions,name,expected);require(resolutions[name]==plan['input_resolutions'][name],'Prior input resolution changed')
        prior,closures=load.prior_evidence(e,inspector,old,pins,resolutions)
        failure,failure_closure=rebx.prior_failure(e,pins,resolutions)
        require(prior==new['prior'] and failure==new['prior_load_failure'],'Frozen continuation joins differ')
        require({k:base_refs[k] for k in ('plan','report','terminal')}==prior['references']
            and base_refs['independent_closure']==prior['independent_reuse_review']
            and {k:refs['scoped_load_failure'][k] for k in ('plan','report','terminal')}=={k:failure[k] for k in ('plan','report','terminal')}
            and refs['scoped_load_failure']['independent_closure']==failure['review'],'Independent failure references differ')
        closed=e.document(refs['rebx_load']['independent_closure'],pins,resolutions)
        require(closed['status']=='successful-load-retained-owned-stage-closed' and closed['native_exit_status']==0
            and closed['plan']==refs['rebx_load']['plan'] and closed['report']==refs['rebx_load']['report'] and closed['terminal']==refs['rebx_load']['terminal'],
            'Independent successful closure differs')
        require(new['rebx_adapter']==refs['rebx_load']['entrypoint'] and new['entrypoint']==refs['rebx_load']['entrypoint']['path']
            and dict(path=new['controller'],sha256=new['controller_sha256'])==refs['rebx_load']['controller'],'Actual continuation identity differs')
        snapshots=[]
        for durable,expected in zip(extension['durables'],(prior['durable'],failure['durable'],closed['durable'])):
            require(all(durable[k]==expected[k] for k in ('directory','artifacts','lease')),'Actual durable closure differs')
            job=Path(durable['directory']);actual=e.inventory(job,('owner.lock',))[0];require(actual==durable['artifacts'],'Prior durable inventory changed')
            for name,item in actual.items():e.pin(pins,resolutions,job/name,item['sha256'])
            snapshots.append(dict(directory=str(job),artifacts=actual,lease=durable['lease'],stage=durable['stage']))
        success=check_success(f,e,load,new,refs['rebx_load'],extension['durables'][2],pins,resolutions,inspector)
        image=rebx.image_alias(e,inspector,pins,resolutions,False)
        require(image==extension['image_copy'] and image['alias']==extension['built_image'] and image['original']==extension['original_built_image'],'Selected image association differs')
        declared=e.built_image_closure([Path(image['alias']['path'])],intake,inspector,pins)
        original_report=e.document(prior['references']['report'],pins,resolutions)
        require(declared==extension['selected_image_closure']==new['rebx_image']['declared_image_closure']
            and original_report['captures'][2]['native_layout_and_images']['declared_image_closure']==extension['declared_image_closure'],'Static image scope differs')
        generated,sdk_closures=e.retained_sdk(pins,resolutions)
        require(generated==old['generated_outputs'] and extension['sdk_output_reuse']==dict(path=str(e.REUSE),sha256=e.REUSE_SHA)
            and extension['corrected_source']==dict(path=str(e.PACKET/'clbg_primitives.c'),sha256=pins[str(e.PACKET/'clbg_primitives.c')]),'Compiled source/SDK association differs')
        return old,closures+[failure_closure,success],snapshots,image['alias']
    def compile_slot(e,intake,output):
        value=original_compile(e,intake,output)
        position=value['command'].index('-MD')
        value['command'][position:position]=['-isystem',str(HEADER_ROOT)]
        return value
    def build_plan(e,transport,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions):
        e.physical(output);require(output.is_relative_to(f.PACKET) and output!=f.PACKET and not os.path.lexists(output),'Fresh fixture output required')
        prior,closures,durables,image=extension_inputs(e,inspector,extension,intake,pins,resolutions)
        spec=e.document(dict(path=str(f.ORIGINAL/'spec.json'),sha256=f.SPEC_SHA),pins,resolutions)
        review=e.document(extension['fixture_source_review'],pins,resolutions)
        require(review['schema']=='rebol-general-primitive-fixtures-source-review-v1'
            and review['status']=='independent-source-review-complete-native-gates-pending'
            and review['source_review']['independent'] is True,'Original fixture review required')
        for name,expected in spec['fixture_source_pins'].items():
            require(review['files'].get(str((f.ORIGINAL/name).relative_to(ROOT)))==expected,'Original fixture source review differs')
            e.pin(pins,resolutions,f.ORIGINAL/name,expected)
        require(review['files'][str((f.ORIGINAL/'spec.json').relative_to(ROOT))]==f.SPEC_SHA,'Original fixture spec identity differs')
        for name,expected in spec['immutable_source_pins'].items():e.pin(pins,resolutions,ROOT/name,expected)
        facades={str(e.SUPPORT/name):spec['immutable_source_pins'][str((e.SUPPORT/name).relative_to(ROOT))]
            for name in ('clbg_io.reb','clbg_primitives.reb','clbg_big.reb','clbg_regex.reb')}
        require(extension['unchanged_facades']==facades,'Exact retained loader/facades required')
        header=e.document(HEADER_REVIEW,pins,resolutions);missing=str(Path(intake['include_roots']['macos_sdk'])/'usr/include/mach-o/dyld-interposing.h')
        require(header['schema']=='rebol-diagnostic-interposer-header-intake-v1' and header['header_review']['independent_source_review'] is True
            and header['retained_header']==dict(path=str(HEADER),bytes=2368,sha256=HEADER_SHA)
            and header['selected_sdk']==intake['include_roots']['macos_sdk'] and header['selected_sdk_header_present'] is False
            and not os.path.lexists(missing),'Official supplemental diagnostic header review required')
        e.pin(pins,resolutions,HEADER,HEADER_SHA)
        header_files=e.inventory(HEADER_ROOT)[0]
        require(header_files=={'mach-o/dyld-interposing.h':dict(bytes=2368,sha256=HEADER_SHA)},'Supplemental include root changed')
        require(spec['limits']==dict(per_process_seconds=180,per_process_rss_bytes=536870912,stdout_limit_bytes=1048576,stderr_limit_bytes=1048576,automatic_retry=False),'Original bounded policy differs')
        return dict(schema='rebol-primitive-fixtures-plan-v2',status='prepared-awaiting-independent-review',repository=str(ROOT),
            controller=str(ORIGINAL),controller_sha256=DEPENDENCIES[str(ORIGINAL.relative_to(ROOT))],intake_adapter=dict(adapter_ref),entrypoint=adapter_ref['path'],
            output=str(output),extension_review=extension_ref,source_review=source_ref,toolchain_intake=extension['references']['toolchain_intake'],
            schedule=f.schedule(e,transport,spec,intake,image,output),pins=dict(pins),input_resolutions=dict(resolutions),
            unavailable_inputs=sorted(set(prior['unavailable_inputs'])|{missing}),
            prerequisite_artifact_closures=closures+[dict(directory=str(HEADER_ROOT),artifacts=header_files)],
            extension_durables=durables,extension_image=image,corrected_source=extension['corrected_source'],diagnostic_header_review=HEADER_REVIEW,
            historical_spec=dict(path=str(f.ORIGINAL/'spec.json'),sha256=f.SPEC_SHA),historical_old_c_preserved=True,failed_sdk_producer_preserved=True,
            native_processes=19,fixture_processes=18,diagnostic_compilations=1,benchmark_samples=0,automatic_retry=False,
            cleanup_timeout_seconds=5,common_mutex_inode=79859134,**{k:False for k in GATES})
    def verify_inputs(e,plan,pins,resolutions,leases):
        e.verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures'])
        require([v['stage'] for v in plan['extension_durables']]==list(STAGES),'All three original durable jobs required')
        for durable in plan['extension_durables']:
            require(e.inventory(Path(durable['directory']),('owner.lock',))[0]==durable['artifacts'],'Prior durable inventory changed')
        e.check_leases(leases)
    f.bootstrap,f.check_disposition,f.held,f.extension_inputs=bootstrap,check_disposition,held,extension_inputs
    f.build_plan,f.verify_inputs,f.compile_slot=build_plan,verify_inputs,compile_slot
    return f

def load_controller(expected):
    # The regular-only reader is taken from the exact frozen fixture module.
    before=ORIGINAL.lstat();require(stat.S_ISREG(before.st_mode) and ORIGINAL.resolve()==ORIGINAL,'Physical regular controller required')
    with os.fdopen(os.open(ORIGINAL,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Controller replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2,'Bounded controller source required')
    require(digest(raw)==DEPENDENCIES[str(ORIGINAL.relative_to(ROOT))],'Frozen fixture controller changed')
    f=types.ModuleType('rebol_original_fixed19');f.__file__=str(ORIGINAL);exec(compile(raw,str(ORIGINAL),'exec'),f.__dict__)
    own=Path(__file__).resolve();require(digest(f.bootstrap_read(own))==expected,'Intake adapter changed')
    path=ROOT/'tools/qualification/rebol_extension_rebx_load.py';rebx=compiled(path,DEPENDENCIES[str(path.relative_to(ROOT))],f.bootstrap_read)
    return attach(f,dict(path=str(own),sha256=expected),rebx)

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();module=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];module.main()
    finally:sys.argv=previous

if __name__=='__main__':main()
