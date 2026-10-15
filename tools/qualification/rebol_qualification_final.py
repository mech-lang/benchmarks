"""Join final Rebol source counts, split correctness and bounded work evidence.

This file-only adapter preserves the original qualification context and its
exit checks. It accepts one publication form per workload and no timing result.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'tools/qualification/rebol_qualification.py'
ORIGINAL_SHA='42c8ef4f7fe452c2fd072901237e1a1f6e244267cfd049cc338a45f3d1b548aa'
WORK=ROOT/'tools/qualification/rebol_work_map.py'
WORK_SHA='cdd426e5beb45c0e2714d6f6e49d8097fa350ff7fa186f1692f8a7880f37a395'
FINAL=ROOT/'tools/qualification/rebol_bounded_final.py'
FINAL_SHA='ba354558de43f830953e8a17f85115ec07213b0ff91e3860cfbcaa85ed9f4db4'
BINDING=ROOT/'tools/qualification/rebol_tree_reviewed_count_ledger.py'
BINDING_SHA='ffb0c13df72e419b1c1da452a1b8ff6f37608cd77bf6c0c9616bd214bf7cb5e2'
PACKET=ROOT/'experiments/rebol/qualification-v1/final-intake-v1'
WORK_PACKET=ROOT/'experiments/rebol/work-observations-v1/remaining-intake-v1/final-bounded-v1/map-only-v1'
JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-map-work-v1'


def reference(path,sha):return dict(path=str(path),sha256=sha)


BINDING_REVIEW=reference(ROOT/'experiments/rebol/tree-leaves-v1/source-counts-v1/binding-source-review-v1.json',
    'f6a571822bf07b0e351d71d1ff7ddf1189c12269ed70b87758266c9b915f6c48')
COUNTS=reference(ROOT/'experiments/rebol/tree-leaves-v1/source-counts-v1/count-review-v1.json',
    'bc71e89e685feb84b17b00579d168d3936b83c247d627d441e15beb43bf88575')
BOUNDED=reference(ROOT/'experiments/rebol/bounded-v1/tree-continuation-v1/final8-v1/combined-bounded-review-v1.json',
    'e0514bb96b47a5420ffc300dff0aeac898b5547ece3e4b1d17384c90120c9e5c')
OBSERVATIONS=reference(WORK_PACKET/'combined-bounded-work-review-v1.json',
    '3996ceb8569fcbbf813d229ef0fff6b63f5c08ebe6407d2f5b0bd1fec6db9a1f')
CLOSURE=reference(WORK_PACKET/'independent-closure-v1.json',
    '06969ae19f9f6314743f0983f4b22b7d67d996f0a01b9b0e3795f65972c3b624')
WORK_SOURCE=reference(WORK_PACKET/'source-review-v1.json',
    'b08eee3064e5127d45cbe7f327b9d87c28eaf7092384132c6cd6f4fc956a27a0')
POLICY=reference(ROOT/'experiments/rebol/full60-v1/POLICY.md',
    'ced3456b5e189b737ec750b2c7b23b3a9aa884be2480c7fa0b726c05b3bba91b')
STAGE={name:reference(WORK_PACKET/path,sha) for name,path,sha in (
    ('plan','plan-v1.json','b7c777cd1cf83622ccbf8fbb58a19ae8f07cc6875dcda5c9a612d7e012c66cbe'),
    ('report','run-v1/report.json','1a99502315f8b3f29d1d5ccb75ad8d31e61e20f705cb9a6eedcc0dd862141ad0'),
    ('terminal','run-v1/terminal.json','08ba6aa2f1629e6d979b695cf2b3672c367c6370488f3996f12485beda6a905d'))}
UNOBSERVED=('backing_series_capacity_observed','backing_series_identity_observed','full_pointer_identity_observed',
    'hash_bucket_capacities_observed','capacity_growth_trajectory_observed','machine_division_count_established',
    'per_tree_frees_observed','memory_usage_qualified','full_size_work_qualified')


def require(value,message):
    if not value:raise AssertionError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()
def durable_ref(value):return {k:value[k] for k in ('directory','artifacts','lease')}


@contextmanager
def map_lease(e,inherited,durable):
    lease=durable['lease'];path=Path(lease['path'])
    require(durable['directory']==str(JOB) and path==JOB/'owner.lock'
        and path not in [Path(item[0]) for item in inherited]
        and all(type(lease[k]) is int for k in ('device','inode')),'Distinct current-map lease required')
    with e.regular(path) as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        leases=[*inherited,(path,stream,(lease['device'],lease['inode']))]
        e.check_leases(leases)
        try:yield leases
        finally:e.check_leases(leases)


def check_observations(w,review,closure,prior,refs):
    expected=dict(STAGE,source_review=WORK_SOURCE,map_source_review=refs['map_source_review'],
        primitive_review=refs['primitive_review'],bounded_source_review=refs['bounded_source_review'])
    require(review['schema']=='rebol-combined-independent-bounded-work-review-v1'
        and review['status']=='three-bounded-observation-contracts-verified' and review['independent_review'] is True
        and review['references']==expected and review['current_closure']==CLOSURE
        and review['prior_work_stage_review']==prior['review']
        and review['actual_native_processes']==4 and review['accepted_observations']==3
        and review['preserved_failed_observations']==1 and review['unstarted_observations']==0
        and review['bounded_observation_contracts_qualified'] is True
        and all(review[k] is False for k in (*w.GATES,*UNOBSERVED)), 'Exact split bounded-work approval required')
    require(closure['schema']=='rebol-single-map-independent-closure-v1'
        and closure['status']=='complete-map-observation-verified-owned-stage-closed'
        and closure['independent_review'] is True and closure['references']==expected
        and closure['native_processes_started']==closure['completed_observations']==1
        and closure['failed_observations']==closure['unstarted_observations']==0
        and closure['preserved_observations']==2 and closure['preserved_failed_observations']==1
        and closure['prior_work_stage']==prior and len(closure['successful_captures'])==1
        and all(closure[k] is False for k in w.GATES),'Exact single-map independent closure required')
    require(review['observations']==prior['retained_observations']+closure['successful_captures']
        and [x['id'] for x in review['observations']]==['binarytrees-n4','pidigits-n27','knucleotide-arbitrary-widths']
        and review['preserved_failed_capture']==prior['failed_capture']
        and review['prior_durable']==prior['durable'] and review['durable']==closure['durable']
        and review['cohort_references']==dict(prior_work3=prior['references'],current_map=expected)
        and all(x['native_process_verified'] is x['bounded_observation_contract_satisfied'] is True
                for x in review['observations']), 'Split observation identity or failure preservation differs')


def closed_map(q,w,r,e,adapter,consumers,inspector,review,closure,prior,expected,pins,resolutions):
    """Replay one current capture; retain the independently closed tree/Pi pair."""
    plan,report,terminal=[e.document(STAGE[key],pins,resolutions) for key in ('plan','report','terminal')]
    output=e.physical(Path(plan['output']))
    require(output==WORK_PACKET/'run-v1' and plan['schema']=='rebol-single-map-work-plan-v1'
        and plan['repository']==str(ROOT) and plan['controller']==w.__file__
        and plan['controller_sha256']==pins[w.__file__]
        and plan['map_intake_adapter']==reference(WORK,WORK_SHA) and plan['entrypoint']==str(WORK)
        and all(plan.get(k)==v for k,v in expected.items())
        and plan['automatic_retry'] is False and plan['benchmark_samples']==0
        and plan['native_processes']==1 and plan['preserved_observations']==2
        and plan['preserved_native_processes']==3 and plan['preserved_failed_observations']==1
        and plan['prior_work_stage']==prior and all(plan[k] is False for k in w.GATES), 'Current map plan differs')
    require(set(plan['pins'])==set(plan['input_resolutions']), 'Current map named closure differs')
    for name,sha in plan['pins'].items():
        e.pin(pins,resolutions,name,sha)
        require(resolutions[name]==plan['input_resolutions'][name], 'Current map input resolution changed')
    ids=[slot['id'] for slot in plan['schedule']]
    require(ids==['knucleotide-arbitrary-widths'] and report['schema']=='rebol-single-map-work-results-v1'
        and terminal['schema']=='rebol-single-map-work-terminal-v1' and report['status']==terminal['status']==w.SUCCESS
        and report['plan']==STAGE['plan']['path'] and report['plan_sha256']==STAGE['plan']['sha256']
        and report['pins']==dict(plan['pins'],**{STAGE['plan']['path']:STAGE['plan']['sha256']})
        and report['input_resolutions']==dict(plan['input_resolutions'],**{STAGE['plan']['path']:STAGE['plan']['path']})
        and report['active'] is None and report['attempts']==[x['id'] for x in report['registered']]==ids
        and [x['id'] for x in report['captures']]==ids and len(report['captures'])==1
        and report['prior_work_stage']==prior and report['preserved_observations']==terminal['preserved_observations']==2
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['report_sha256']==terminal['expected_report_sha256']==STAGE['report']['sha256']
        and terminal['native_processes_started']==terminal['validated_observations']==1
        and terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==plan['common_mutex_inode']==79859134
        and report['benchmark_samples']==terminal['benchmark_samples']==0
        and all(report[k] is terminal[k] is False for k in w.GATES), 'Current map producer ledger differs')
    complete=e.inventory(output)[0]
    require(complete==closure['artifacts'] and len(complete)==8
        and e.inventory(output,('report.json','terminal.json'))[0]==report['artifacts']==report['validated_files']
        and e.inventory(output,('terminal.json',))[0]==terminal['available_evidence'], 'Current map artifact membership differs')
    for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
    durable=review['durable'];require(e.inventory(JOB,('owner.lock',))[0]==durable['artifacts']
        and len(durable['artifacts'])==8,'Current map durable inventory differs')
    for name,item in durable['artifacts'].items():e.pin(pins,resolutions,JOB/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(JOB/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(WORK),'--adapter-sha256',WORK_SHA,
          'run','--plan',STAGE['plan']['path'],'--plan-sha256',STAGE['plan']['sha256']]
    require(launch['command']==started['command']==closure['actual_command']==argv
        and launch['cwd']==started['cwd']==str(ROOT) and ended['status']=='command-exited-zero-awaiting-report-review'
        and type(ended['exit_code']) is int and ended['exit_code']==0
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals']==[]
        and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
        and started['command_identity']==ended['command_identity']
        and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid'],
        'Current map durable command or identity differs')
    slot=plan['schedule'][0];directory=output/slot['directory']
    capture,snapshot=w.checked_case(r,e,adapter,consumers,inspector.kb,slot,directory,started['command_pid'])
    item=closure['successful_captures'][0]
    require(capture==report['captures'][0]==item['capture'] and capture['pid']==report['registered'][0]['pid']
        and snapshot==item['capture_files'] and item['capture_directory']==str(directory)
        and e.inventory(output)[0]==complete,'Actual complete-map capture differs')
    return plan,dict(directory=str(output),artifacts=complete),dict(directory=str(JOB),artifacts=durable['artifacts'])


def attach(q,map_module,adapter_ref):
    old_load,old_bootstrap,old_contract,old_counts,old_pinned,old_bases=q.load,q.bootstrap,q.manifest_contract,q.counts,q.pinned_module,q.make_bases
    dependencies={str(WORK):WORK_SHA,str(FINAL):FINAL_SHA,str(BINDING):BINDING_SHA,
        BINDING_REVIEW['path']:BINDING_REVIEW['sha256'],POLICY['path']:POLICY['sha256']}
    q.FILES|={str(p.relative_to(ROOT)) for p in (Path(adapter_ref['path']),
        Path(__file__).with_name('test_rebol_qualification_final.py'),PACKET/'README.md')}
    q.DEPENDENCIES|={str(Path(p).relative_to(ROOT)) for p in dependencies}
    q.LIMITATIONS=q.clone(q.LIMITATIONS)
    q.LIMITATIONS['maps'].update(final_backing_capacity_observed=False,backing_series_identity_observed=False)
    def manifest_contract(value):
        extra=dict(bounded_review=BOUNDED,observation_review=OBSERVATIONS,timing_policy=POLICY)
        require(all(value['references'].get(k)==v for k,v in extra.items()),'Final bounded/work/policy references required')
        original=q.clone(value);original['references']={k:v for k,v in value['references'].items() if k not in extra}
        old_contract(original)
        require(value['references']['count_review']==COUNTS and value['references']['work_source_review']==WORK_SOURCE,
            'Final count and single-map source approvals required')
    def load(raw,path,name):
        if Path(path)==q.WORK:return map_module.load_controller(WORK_SHA)
        return old_load(raw,path,name)
    def bootstrap(manifest_ref):
        manifest,source,w=old_bootstrap(manifest_ref)
        require(source['files'][str(ORIGINAL.relative_to(ROOT))]==ORIGINAL_SHA
            and source['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256']
            and all(source['dependencies'][str(Path(p).relative_to(ROOT))]==sha for p,sha in dependencies.items()),
            'Final qualifier source identities differ')
        return manifest,source,w
    def counts(e,review_ref,source,pins,resolutions,sources,extension):
        require(review_ref==COUNTS,'Exact final tree/regex counts required')
        review=e.document(review_ref,pins,resolutions);approval=e.document(BINDING_REVIEW,pins,resolutions)
        require(approval['schema']=='rebol-corrected-tree-count-binding-source-review-v1'
            and approval['status']=='independent-source-review-complete' and approval['independent_review'] is True
            and approval['files'][str(BINDING.relative_to(ROOT))]['sha256']==BINDING_SHA
            and approval['native_execution'] is approval['chart_admission'] is False,'Count binding source approval differs')
        binding=old_pinned(e,BINDING,BINDING_SHA,pins,resolutions,'rebol_final_count_binding')
        proposal=e.document(review['references']['proposal'],pins,resolutions)
        for key,expected in (('corrected_regex_substitution',binding.REGEX_SUBSTITUTION),('corrected_tree_substitution',binding.TREE_SUBSTITUTION)):
            require(proposal[key]==review[key]==expected,'Final counted source substitution differs')
        def pinned(e,path,expected,pins,resolutions,name):
            module=old_pinned(e,path,expected,pins,resolutions,name)
            return binding.bind_ledger(module,review) if Path(path)==q.LEDGER else module
        require(q.pinned_module is old_pinned,'Count module loader already replaced')
        q.pinned_module=pinned
        try:return old_counts(e,review_ref,source,pins,resolutions,sources,extension)
        finally:q.pinned_module=old_pinned
    def make_bases(*args):
        bases=old_bases(*args)
        for base in bases:base['alias_policy']['publication_forms']=['compact']
        return bases
    q.load,q.bootstrap,q.manifest_contract,q.counts,q.make_bases=load,bootstrap,manifest_contract,counts,make_bases
    q._held_review=lambda *args,**kwargs:held_review(q,map_module,*args,**kwargs)
    q.intake_adapter=adapter_ref
    return q


def source_work(q,e,manifest,pins,resolutions,sources,identities,runtime,image):
    review=e.document(manifest['references']['work_review'],pins,resolutions)
    require(review['schema']=='rebol-final-independent-source-work-review-v1'
        and review['status']=='qualified-exact-sources-and-bounded-evidence' and review['independent_review'] is True
        and review['bounded_output_qualified'] is review['required_work_qualified'] is True
        and all(review[k] is False for k in q.FALSE_SCOPE)
        and review['references']==dict(bounded_review=BOUNDED,observation_review=OBSERVATIONS,count_review=COUNTS,timing_policy=POLICY)
        and review['runtime']==runtime and review['extension_image']==image
        and review['sources']=={i:{k:v[k] for k in ('path','sha256')} for i,v in identities.items()}
        and review['limitations']==q.LIMITATIONS and set(review['source_work'])==set(sources),
        'Independent ten-source bounded-work disposition required')
    for bench,item in review['source_work'].items():
        require(item['main']=={k:sources[bench][k] for k in ('path','sha256')}
            and item['required_work_qualified'] is True and item['scope']=='exact-source-and-bounded-evidence'
            and type(item['evidence']) is list and item['evidence'],'Exact source-specific work approval required')
        for ref in item['evidence']:q.ref(ref);e.pin(pins,resolutions,ref['path'],ref['sha256'])
    ref=q.ref(review['map_growth_source_review']);e.pin(pins,resolutions,ref['path'],ref['sha256'])
    return review


@contextmanager
def held_review(q,map_module,manifest_path,manifest_sha,on_exit_failure=None,final_consumer_check=None):
    manifest_ref=q.ref(reference(manifest_path,manifest_sha))
    initial,source,w=q.bootstrap(manifest_ref);refs=initial['references']
    with w.held(refs['primitive_review'],refs['bounded_source_review'],refs['work_source_review']) as inherited:
        r,p,e,adapter,consumers,inspector,common,leases,intake,extension,primitive,pins,resolutions=inherited
        manifest=e.document(manifest_ref,pins,resolutions)
        require(manifest==initial and e.document(refs['source_review'],pins,resolutions)==source,'Qualifier review changed after locking')
        for name,sha in {**source['files'],**source['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,sha)
        observations=e.document(OBSERVATIONS,pins,resolutions);closure=e.document(CLOSURE,pins,resolutions)
        with map_lease(e,leases,observations['durable']) as combined:
            try:
                final=q.pinned_module(e,FINAL,FINAL_SHA,pins,resolutions,'rebol_qualification_final_bounded')
                bounded_plan,closures,jobs,bounded=w.bounded_inputs(r,e,inspector.kb,final,refs['primitive_review'],pins,resolutions)
                prior_plan,prior,prior_closure=w.validate_prior_work(e,refs['primitive_review'],refs['bounded_source_review'],pins,resolutions)
                check_observations(w,observations,closure,prior,dict(refs,map_source_review=map_module.MAP_REVIEW))
                require(prior_plan['bounded_correctness']==bounded and observations['unchanged_bounded_correctness']==bounded
                    and prior_plan['prerequisite_artifact_closures']==closures and prior_plan['prior_durable_jobs']==jobs,
                    'Retained work and bounded prerequisites differ')
                require(manifest['stages']['bounded']==dict({k:bounded['references'][k] for k in ('plan','report','terminal')},
                        durable=durable_ref(bounded['durable']))
                    and manifest['stages']['work']==dict(STAGE,durable=durable_ref(observations['durable'])),
                    'Manifest actual split stage references differ')
                closures=closures+[prior_closure];jobs=jobs+[dict(directory=prior['durable']['directory'],artifacts=prior['durable']['artifacts'])]
                image=bounded_plan['extension_image'];sources=bounded_plan['sources']
                cases=r.corpus(e,pins,resolutions);by_id={(c['benchmark'],c['case']):c for c in cases}
                slots=map_module.map_schedule(w.schedule(e,[by_id[i] for i in w.CASES],image,WORK_PACKET/'run-v1'))
                expected=dict(source_review=WORK_SOURCE,primitive_review=refs['primitive_review'],bounded_source_review=refs['bounded_source_review'],
                    extension_image=image,corrected_source=extension['corrected_source'],bounded_correctness=bounded,
                    unavailable_inputs=bounded_plan['unavailable_inputs'],prerequisite_artifact_closures=closures,prior_durable_jobs=jobs,
                    selected_map_diagnostic=map_module.MAP_SOURCE,selected_map_consumer=map_module.MAP_CONSUMER,
                    map_source_review=map_module.MAP_REVIEW,schedule=slots)
                plan,current_closure,current_job=closed_map(q,w,r,e,adapter,consumers,inspector,observations,closure,prior,expected,pins,resolutions)
                closures=closures+[current_closure];jobs=jobs+[current_job]
                bundles,identities,_=q.counts(e,COUNTS,source,pins,resolutions,sources,extension)
                runtime=reference(e.RUNTIME,pins[str(e.RUNTIME)])
                source_work(q,e,manifest,pins,resolutions,sources,identities,runtime,image)
                profiles=e.document(reference(q.PROFILES,pins[str(q.PROFILES)]),pins,resolutions)
                bases=q.make_bases(e,r,profiles,sources,bundles,image,pins)
                checker=q.pinned_module(e,Path(final.CHECKER['path']),final.CHECKER['sha256'],pins,resolutions,'rebol_final_qualification_outputs')
                admission=dict(schema='rebol-pre-timing-admission-v1',manifest=manifest_ref,bases=bases,
                    runtime=dict(binary=runtime,toolchain_intake=extension['references']['toolchain_intake'],
                        extension_review=primitive['references']['extension_review'],declared_image_closure=extension['declared_image_closure'],
                        actual_layout_and_load_refs=extension['references'],interpreter_loaded_images_observed=False,runtime_source_equivalence_proven=False),
                    extension_image=image,references=q.clone(dict(refs,stages=manifest['stages'])),
                    unavailable_inputs=plan['unavailable_inputs'],artifact_closures=closures,durable_jobs=jobs,
                    lease_identities=[dict(path=str(path),device=identity[0],inode=identity[1]) for path,_,identity in combined],
                    scope=dict(manifest['scope'],limitations=q.clone(q.LIMITATIONS)))
                recheck=q.guarded_recheck(e,pins,resolutions,admission,combined,plan['unavailable_inputs'],closures,jobs)
                held=types.SimpleNamespace(pins=pins,resolutions=resolutions,common=common,leases=tuple(combined),evidence=e,checker=checker,recheck=recheck)
                recheck()
                with q._yield_verified(admission,held,on_exit_failure,final_consumer_check) as value:yield value
            finally:e.check_leases(combined)


def load_controller(expected):
    before=ORIGINAL.lstat()
    require(ORIGINAL.resolve()==ORIGINAL and stat.S_ISREG(before.st_mode),'Physical original qualifier required')
    with os.fdopen(os.open(ORIGINAL,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Qualifier replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2 and digest(raw)==ORIGINAL_SHA,'Frozen qualifier changed')
    q=types.ModuleType('rebol_final_original_qualification');q.__file__=str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),q.__dict__)
    own=Path(__file__).resolve();require(digest(q.read_small(own))==expected,'Final qualifier adapter changed')
    raw=q.read_small(WORK);require(digest(raw)==WORK_SHA,'Single-map work adapter changed')
    return attach(q,q.load(raw,WORK,'rebol_final_map_loader'),q.ref(reference(own,expected)))


def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();q=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];q.main()
    finally:sys.argv=previous


if __name__=='__main__':main()
