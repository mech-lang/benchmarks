"""Consume the actual split primitive completion for unchanged shared149.

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
PRIMITIVE_ADAPTER = ROOT/'tools/qualification/rebol_primitive_remaining.py'
PRIMITIVE_ADAPTER_SHA = 'f28c9bbb5ed9a47bf6bd2d912e031312038228b6092e451e58a4e364332a7a4b'
REGEX_MAIN = dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/main.reb'),
                  sha256='e031f15f60e0b53cd565a87a2993efec9fcecc9ea5dcde35f1a6f13576c7f650')
REGEX_REVIEW = dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/source-review-v1.json'),
                    sha256='14557b38a4b2b7ea4131b39b27646e0501d3d3515e4ebce82246a1608e5edb08')
PACKET = ROOT/'experiments/rebol/bounded-v1/remaining-intake-v1'


def require(value, message):
    if not value: raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def check_primitive_review(r, review):
    require(review['schema']=='rebol-combined-independent-primitive-review-v1'
        and review['status']=='exact-eighteen-primitive-contracts-qualified'
        and review['independent_review'] is True and review['full_primitive_fixtures_qualified'] is True
        and all(review[k] is False for k in r.GATES), 'Actual combined primitive approval required')
    counts=dict(native_attempts=21,primitive_attempts=19,diagnostic_compile_attempts=2,
                successful_captures=19,successful_primitive_contracts=18,failed_attempts=2,benchmark_samples=0)
    require(all(type(review.get(k)) is int and review[k]==v for k,v in counts.items()),
            'Actual combined primitive counts differ')
    require(set(review['references'])=={'plan','report','terminal','extension_review','source_review'}
        and set(review['prior_cohorts'])=={'first_compile_failure','linker_stage'},
        'Exact current and prior primitive references required')
    for item in (*review['references'].values(),*review['prior_cohorts'].values()):
        require(set(item)=={'path','sha256'}, 'Exact evidence reference required')
        r.ref(item['path'],item['sha256'])
    durable=review['durable'];require(set(durable)=={'directory','artifacts','lease'},
                                     'Current primitive durable closure required')
    job=Path(durable['directory']);lease=durable['lease']
    require(job.is_relative_to(ROOT/'experiments/shared/owned-jobs-v1/owned-jobs')
        and lease['path']==str(job/'owner.lock') and set(lease)=={'path','device','inode'}
        and all(type(lease[k]) is int for k in ('device','inode')), 'Primitive lease identity differs')


def prior_success_end(r, linker, current_ids, case_ids):
    captures=linker['successful_captures']
    require([row['id'] for row in captures]==['compile-io-interposer','arithmetic','formatting']
        and [row['id'] for row in captures]+current_ids==['compile-io-interposer',*case_ids]
        and len(current_ids)==16 and len(set(current_ids))==16,
        'Preserved and new captures do not cover the exact eighteen contracts')
    previous=None
    for row in captures:
        started,finished=r.stamp(row['started_at']),r.stamp(row['finished_at'])
        require(started<=finished and (previous is None or previous<=started),
                'Preserved successful captures overlap')
        previous=finished
    return previous


def select_sources(r, original, e, spec, mapping, cases, pins, resolutions):
    selected=original(e,spec,mapping,cases,pins,resolutions)
    review=e.document(REGEX_REVIEW,pins,resolutions)
    require(review['schema']=='rebol-regex-literals-independent-source-review-v1'
        and review['status']=='independent-source-review-complete-native-validation-pending'
        and review['independent_review'] is True
        and {k:review['files']['main.reb'][k] for k in ('path','sha256')}==REGEX_MAIN
        and all(review[k] is False for k in r.GATES), 'Exact corrected regex source approval required')
    old=selected['regexredux'];prior=review['original_sources']['original_main']
    require(old['path']==old['historical_path']==prior['path']
        and old['sha256']==old['historical_sha256']==prior['sha256']
        and old['substitution'] is None, 'Original regex source association differs')
    e.pin(pins,resolutions,REGEX_MAIN['path'],REGEX_MAIN['sha256'])
    helpers=[item for item in review['relative_helper_paths'] if item['source']=='main.reb']
    expected={str(ROOT/'archive/languages/rebol/20261013/drafts/private-v1/support'/name)
              for name in ('clbg_io.reb','clbg_regex.reb')}
    require(len(helpers)==2 and {item['target']['path'] for item in helpers}==expected,
            'Corrected regex helper membership differs')
    for item in helpers:
        target=item['target']
        require(item['file_literal'].startswith('%')
            and (Path(REGEX_MAIN['path']).parent/item['file_literal'][1:]).resolve(strict=True)==Path(target['path']),
            'Corrected regex helper resolution differs')
        e.pin(pins,resolutions,target['path'],target['sha256'])
    selected['regexredux']=dict(old,**REGEX_MAIN,substitution='literal-regex-source')
    return selected


def check_prerequisites(plan, prior, closures, jobs, image, p, intake, failure, failure_closure, linker, linker_closure):
    missing = str(Path(intake['include_roots']['macos_sdk'])/'usr/include/mach-o/dyld-interposing.h')
    header_closure = dict(directory=str(p.HEADER_ROOT), artifacts={
        'mach-o/dyld-interposing.h': dict(bytes=2368, sha256=p.HEADER_SHA)})
    require(plan['unavailable_inputs']==sorted(set(prior['unavailable_inputs'])|{missing})
        and plan['prerequisite_artifact_closures']==closures+[header_closure,failure_closure,linker_closure]
        and plan['prior_fixed19_failure']==failure and plan['prior_linker_stage']==linker
        and plan['diagnostic_header_review']==p.HEADER_REVIEW
        and plan['pins'][str(p.HEADER)]==p.HEADER_SHA
        and plan['extension_durables']==jobs and 'extension_durable' not in plan
        and len(jobs)==3 and [job['stage'] for job in jobs]==list(p.STAGES)
        and plan['extension_image']==image,
        'Primitive split jobs or diagnostic header/failure closure differs')
    return closures+[header_closure,failure_closure,linker_closure]


def attach(r, supplemental, adapter_ref, primitive_adapter_ref):
    original_build, original_source_selection = r.build_plan, r.source_selection
    files = r.FILES | {str(path.relative_to(ROOT)) for path in (
        Path(adapter_ref['path']), Path(__file__).with_name('test_rebol_bounded_remaining.py'), PACKET/'README.md', Path(REGEX_MAIN['path']))}
    dependencies = {str(PRIMITIVE.relative_to(ROOT)): PRIMITIVE_SHA,
                    str(PRIMITIVE_ADAPTER.relative_to(ROOT)): primitive_adapter_ref['sha256']}

    def bootstrap(primitive_ref, source_ref):
        raw = r.read_small(source_ref['path'])
        require(digest(raw)==source_ref['sha256'], 'Bounded intake source review changed')
        source = json.loads(raw)
        require(source['schema']=='rebol149-remaining-controller-source-review-v1'
            and source['status']=='independent-source-review-complete-native-cases-pending'
            and source['independent_review'] is True and set(source['files'])==files
            and source['dependencies']==dependencies and source['regex_source_review']==REGEX_REVIEW
            and source['files'][str(Path(REGEX_MAIN['path']).relative_to(ROOT))]==REGEX_MAIN['sha256']
            and all(source[k] is False for k in r.GATES)
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
        require(plan['schema']=='rebol-primitive-remaining-plan-v1' and plan['repository']==str(ROOT)
            and plan['controller']==str(PRIMITIVE) and plan['controller_sha256']==pins[str(PRIMITIVE)]
            and plan['intake_adapter']==p.intake_adapter and plan['linker_adapter']==p.linker_adapter
            and plan['remaining_adapter']==p.remaining_adapter==primitive_adapter_ref
            and plan['entrypoint']==primitive_adapter_ref['path']
            and plan['extension_review']==refs['extension_review'] and plan['source_review']==refs['source_review']
            and output.is_relative_to(p.PACKET) and output!=p.PACKET
            and refs['report']['path']==str(output/'report.json') and refs['terminal']['path']==str(output/'terminal.json')
            and plan['schedule']==p.schedule(e,adapter,spec,intake,image,output)
            and plan['native_processes']==16 and plan['fixture_processes']==16 and plan['diagnostic_compilations']==0
            and plan['preserved_successful_native_captures']==3
            and plan['regex_review']==REGEX_REVIEW and plan['selected_regex']==supplemental.REGEX
            and plan['reused_interposer']==supplemental.INTERPOSER
            and plan['automatic_retry'] is False and plan['extension_image']==image
            and plan['corrected_source']==extension['corrected_source'], 'Primitive source/plan identity differs')
        failure,failure_closure = p.validate_prior_failure(e,pins,resolutions)
        linker,linker_closure = p.validate_prior_linker(e,adapter,inspector,pins,resolutions)
        require(review['prior_cohorts']==dict(first_compile_failure=failure['review'],linker_stage=linker['review']),
                'Combined primitive approval names different prior cohorts')
        closures = check_prerequisites(plan,prior,closures,extension_jobs,image,p,intake,
                                       failure,failure_closure,linker,linker_closure)
        for name,expected in plan['pins'].items():
            e.pin(pins,resolutions,name,expected)
            require(resolutions[name]==plan['input_resolutions'][name], 'Primitive named input changed')
        ids=[slot['id'] for slot in plan['schedule']]
        require(report['schema']=='rebol-primitive-remaining-results-v1'
            and terminal['schema']=='rebol-primitive-remaining-terminal-v1'
            and report['status']==terminal['status']==p.SUCCESS
            and report['remaining_adapter']==primitive_adapter_ref and report['prior_linker_stage']==linker
            and report['diagnostic_compilations']==terminal['diagnostic_compilations']==0
            and report['plan']==refs['plan']['path'] and report['plan_sha256']==refs['plan']['sha256']
            and report['pins']==dict(plan['pins'],**{refs['plan']['path']:refs['plan']['sha256']})
            and report['input_resolutions']==dict(plan['input_resolutions'],**{refs['plan']['path']:refs['plan']['path']})
            and report['attempts']==ids and [row['id'] for row in report['registered']]==ids
            and [row['id'] for row in report['captures']]==ids and report['active'] is None
            and len(ids)==len({row['pid'] for row in report['registered']})==16
            and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
            and terminal['report_sha256']==terminal['expected_report_sha256']==refs['report']['sha256']
            and terminal['native_processes_started']==terminal['fixture_processes_started']==terminal['validated_captures']==16
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
        previous=prior_success_end(r,linker,ids,adapter.CASE_IDS)
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
        return plan,closures+[dict(directory=str(output),artifacts=complete)], [*extension_jobs,failure['durable'],linker['durable'],job],image

    def build_plan(*args, **kwargs):
        value=original_build(*args, **kwargs)
        value.update(intake_adapter=dict(adapter_ref), primitive_intake_adapter=dict(primitive_adapter_ref),
                     entrypoint=adapter_ref['path'], regex_source_review=REGEX_REVIEW,
                     selected_regex_main=dict(REGEX_MAIN))
        return value

    r.bootstrap,r.durable_inputs,r.primitive_inputs,r.build_plan = bootstrap,durable_inputs,primitive_inputs,build_plan
    r.check_primitive_review=lambda review:check_primitive_review(r,review)
    r.source_selection=lambda e,spec,mapping,cases,pins,resolutions:select_sources(
        r,original_source_selection,e,spec,mapping,cases,pins,resolutions)
    return r


def load_controller(expected, primitive_expected):
    require(primitive_expected==PRIMITIVE_ADAPTER_SHA, 'Exact reviewed remaining16 adapter required')
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
    supplemental=r.load(raw,PRIMITIVE_ADAPTER,'rebol_remaining16_intake')
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
