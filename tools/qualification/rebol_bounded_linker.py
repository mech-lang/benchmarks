"""Consume the linker continuation and actual primitive evidence for shared149.

The frozen bounded controller still owns scheduling, observation, output
validation and finalization. This additive intake records all prerequisite jobs
and both entrypoints without rewriting any earlier plan or failed receipt.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT/'tools/qualification/rebol_bounded.py'
ORIGINAL_SHA = '7a308c92f20c54a039bba87490fa3bbedec332333e106041acb128e4e4ade3b9'
PRIMITIVE = ROOT/'tools/qualification/rebol_primitive_fixtures.py'
PRIMITIVE_SHA = '3c9c7367be14d02573fd5feec42881d9e59f2c4d2e301e4ae36f19327815216c'
PRIMITIVE_ADAPTER = ROOT/'tools/qualification/rebol_primitive_fixtures_linker.py'
PACKET = ROOT/'experiments/rebol/bounded-v1/linker-intake-v1'


def require(value, message):
    if not value: raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def check_prerequisites(plan, prior, closures, jobs, image, supplemental, intake, failure, failure_closure):
    missing = str(Path(intake['include_roots']['macos_sdk'])/'usr/include/mach-o/dyld-interposing.h')
    header_closure = dict(directory=str(supplemental.HEADER_ROOT), artifacts={
        'mach-o/dyld-interposing.h': dict(bytes=2368, sha256=supplemental.HEADER_SHA)})
    require(plan['unavailable_inputs']==sorted(set(prior['unavailable_inputs'])|{missing})
        and plan['prerequisite_artifact_closures']==closures+[header_closure,failure_closure]
        and plan['prior_fixed19_failure']==failure
        and plan['diagnostic_header_review']==supplemental.HEADER_REVIEW
        and plan['pins'][str(supplemental.HEADER)]==supplemental.HEADER_SHA
        and plan['extension_durables']==jobs and 'extension_durable' not in plan
        and len(jobs)==3 and [job['stage'] for job in jobs]==list(supplemental.STAGES)
        and plan['extension_image']==image,
        'Primitive split jobs or diagnostic header closure differs')
    return closures+[header_closure,failure_closure]


def attach(r, supplemental, adapter_ref, primitive_adapter_ref):
    original_build = r.build_plan
    files = r.FILES | {str(path.relative_to(ROOT)) for path in (
        Path(adapter_ref['path']), Path(__file__).with_name('test_rebol_bounded_linker.py'), PACKET/'README.md')}
    dependencies = {str(PRIMITIVE.relative_to(ROOT)): PRIMITIVE_SHA,
                    str(PRIMITIVE_ADAPTER.relative_to(ROOT)): primitive_adapter_ref['sha256']}

    def bootstrap(primitive_ref, source_ref):
        raw = r.read_small(source_ref['path'])
        require(digest(raw)==source_ref['sha256'], 'Bounded intake source review changed')
        source = json.loads(raw)
        require(source['schema']=='rebol149-combined-controller-source-review-v1'
            and source['status']=='independent-source-review-complete-native-cases-pending'
            and source['independent_review'] is True and set(source['files'])==files
            and source['dependencies']==dependencies and all(source[k] is False for k in r.GATES)
            and source['files'][str(ORIGINAL.relative_to(ROOT))]==ORIGINAL_SHA
            and source['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256'],
            'Exact additive bounded source review required')
        for name, expected in {**source['files'], **source['dependencies']}.items():
            require(digest(r.read_small(ROOT/name))==expected, 'Bounded source dependency changed: '+name)
        p = supplemental.load_controller(primitive_adapter_ref['sha256'])
        require(p.ROOT==ROOT and Path(p.__file__)==PRIMITIVE, 'Original primitive controller identity differs')
        raw = r.read_small(primitive_ref['path'])
        require(digest(raw)==primitive_ref['sha256'], 'Primitive approval changed')
        primitive = json.loads(raw)
        r.check_primitive_review(primitive)
        return p, primitive, source

    def durable_inputs(e, review, plan_ref, pins, resolutions):
        durable = review['durable']; job = e.physical(Path(durable['directory']))
        artifacts = e.inventory(job, ('owner.lock',))[0]
        require(artifacts==durable['artifacts'] and {'launch.json','command-started.json','terminal.json'}<=set(artifacts),
                'Primitive durable inventory differs')
        for name, item in artifacts.items(): e.pin(pins,resolutions,job/name,item['sha256'])
        launch, started, ended = [json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
        argv = [str(e.PYTHON),'-I','-S','-B',primitive_adapter_ref['path'],
                '--adapter-sha256',primitive_adapter_ref['sha256'],'run',
                '--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256']]
        require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
            and ended['status']=='command-exited-zero-awaiting-report-review' and type(ended['exit_code']) is int and ended['exit_code']==0
            and ended['actual_command_started'] is True and ended['automatic_retry'] is False
            and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False
            and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
            and started['command_identity']==ended['command_identity'], 'Primitive durable ownership differs')
        return started['command_pid'], dict(directory=str(job), artifacts=artifacts)

    def primitive_inputs(p,e,adapter,inspector,review,intake,extension,pins,resolutions):
        refs=review['references']
        plan=e.document(refs['plan'],pins,resolutions);report=e.document(refs['report'],pins,resolutions)
        terminal=e.document(refs['terminal'],pins,resolutions)
        prior,closures,extension_jobs,image=p.extension_inputs(e,inspector,extension,intake,pins,resolutions)
        output=e.physical(Path(plan['output']))
        spec=e.document(dict(path=str(r.ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),pins,resolutions)
        require(plan['schema']=='rebol-primitive-fixtures-plan-v2' and plan['repository']==str(ROOT)
            and plan['controller']==str(PRIMITIVE) and plan['controller_sha256']==pins[str(PRIMITIVE)]
            and plan['intake_adapter']==supplemental.BASE_INTAKE_ADAPTER
            and plan['linker_adapter']==primitive_adapter_ref and plan['entrypoint']==primitive_adapter_ref['path']
            and plan['extension_review']==refs['extension_review'] and plan['source_review']==refs['source_review']
            and output.is_relative_to(p.PACKET) and output!=p.PACKET
            and refs['report']['path']==str(output/'report.json') and refs['terminal']['path']==str(output/'terminal.json')
            and plan['schedule']==p.schedule(e,adapter,spec,intake,image,output)
            and plan['native_processes']==19 and plan['fixture_processes']==18 and plan['diagnostic_compilations']==1
            and plan['automatic_retry'] is False and plan['extension_image']==image
            and plan['corrected_source']==extension['corrected_source'], 'Primitive source/plan identity differs')
        failure,failure_closure = p.validate_prior_failure(e,pins,resolutions)
        closures = check_prerequisites(plan,prior,closures,extension_jobs,image,supplemental,intake,failure,failure_closure)
        for name,expected in plan['pins'].items():
            e.pin(pins,resolutions,name,expected)
            require(resolutions[name]==plan['input_resolutions'][name], 'Primitive named input changed')
        ids=[slot['id'] for slot in plan['schedule']]
        require(report['schema']=='rebol-primitive-fixtures-results-v2'
            and terminal['schema']=='rebol-primitive-fixtures-terminal-v2'
            and report['status']==terminal['status']==p.SUCCESS
            and report['plan']==refs['plan']['path'] and report['plan_sha256']==refs['plan']['sha256']
            and report['pins']==dict(plan['pins'],**{refs['plan']['path']:refs['plan']['sha256']})
            and report['input_resolutions']==dict(plan['input_resolutions'],**{refs['plan']['path']:refs['plan']['path']})
            and report['attempts']==ids and [row['id'] for row in report['registered']]==ids
            and [row['id'] for row in report['captures']]==ids and report['active'] is None
            and len({row['pid'] for row in report['registered']})==19
            and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
            and terminal['report_sha256']==terminal['expected_report_sha256']==refs['report']['sha256']
            and terminal['native_processes_started']==terminal['validated_captures']==19
            and terminal['common_mutex_held'] is True
            and all(report[k] is terminal[k] is False for k in p.GATES), 'Primitive producer is not closed successfully')
        artifacts=e.inventory(output,('report.json','terminal.json'))[0]
        require(artifacts==report['validated_files']==report['artifacts'] and set(artifacts)==p.expected_files(plan),
                'Primitive validated artifact membership differs')
        available=dict(artifacts,**{'report.json':dict(bytes=len(e.read_bytes(output/'report.json')),sha256=refs['report']['sha256'])})
        require(terminal['available_evidence']==available, 'Primitive terminal inventory differs')
        complete=dict(available,**{'terminal.json':dict(bytes=len(e.read_bytes(output/'terminal.json')),sha256=refs['terminal']['sha256'])})
        for name,item in complete.items(): e.pin(pins,resolutions,output/name,item['sha256'])
        parent,job=durable_inputs(e,review,refs['plan'],pins,resolutions)
        previous=None
        for slot,registration,capture in zip(plan['schedule'],report['registered'],report['captures']):
            directory=output/slot['directory'];prefix=slot['directory']+'/'
            extra={name[len(prefix):]:item for name,item in artifacts.items() if name.startswith(prefix) and name[len(prefix):] not in r.CAPTURE_FILES}
            observed,snapshot=p.checked_capture(e,slot,directory,parent,inspector.kb,extra)
            require(observed['pid']==registration['pid'] and all(capture.get(k)==v for k,v in observed.items()), 'Primitive capture join differs')
            if previous is not None: require(previous<=r.stamp(observed['started_at']), 'Primitive commands overlap')
            previous=r.stamp(observed['finished_at'])
            if 'case' in slot:
                case=slot['case'];sidecars={key:e.read_bytes(path) for key,path in slot['sidecars'].items()}
                decoded=adapter.check_case(case,e.read_bytes(directory/'stdout.bin'),e.read_bytes(directory/'stderr.bin'),0,**sidecars)
                require(decoded==capture['fixture_observations'], 'Primitive output review differs')
        require(e.inventory(output,('terminal.json',))[0]==available, 'Primitive evidence changed during replay')
        return plan,closures+[dict(directory=str(output),artifacts=complete)], [*extension_jobs,failure['durable'],job],image

    def build_plan(*args, **kwargs):
        value=original_build(*args, **kwargs)
        value.update(intake_adapter=dict(adapter_ref), primitive_intake_adapter=dict(primitive_adapter_ref),
                     entrypoint=adapter_ref['path'])
        return value

    r.bootstrap,r.durable_inputs,r.primitive_inputs,r.build_plan = bootstrap,durable_inputs,primitive_inputs,build_plan
    return r


def load_controller(expected, primitive_expected):
    before=ORIGINAL.lstat()
    require(stat.S_ISREG(before.st_mode) and ORIGINAL.resolve()==ORIGINAL, 'Physical regular controller required')
    with os.fdopen(os.open(ORIGINAL,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno())
        require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino), 'Controller replaced')
        raw=stream.read(2*1024**2+1)
        require(len(raw)<=2*1024**2 and digest(raw)==ORIGINAL_SHA, 'Frozen bounded controller changed')
    r=types.ModuleType('rebol_original_shared149');r.__file__=str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),r.__dict__)
    own=Path(__file__).resolve()
    adapter_ref=r.ref(str(own),expected); primitive_ref=r.ref(str(PRIMITIVE_ADAPTER),primitive_expected)
    require(digest(r.read_small(own))==expected, 'Bounded intake adapter changed')
    raw=r.read_small(PRIMITIVE_ADAPTER)
    require(digest(raw)==primitive_expected, 'Primitive intake adapter changed')
    supplemental=r.load(raw,PRIMITIVE_ADAPTER,'rebol_combined_fixed19')
    return attach(r,supplemental,adapter_ref,primitive_ref)


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--adapter-sha256',required=True)
    parser.add_argument('--primitive-adapter-sha256',required=True)
    args,remaining=parser.parse_known_args()
    controller=load_controller(args.adapter_sha256,args.primitive_adapter_sha256)
    sys.argv=[str(ORIGINAL),*remaining]
    controller.main()


if __name__=='__main__': main()
