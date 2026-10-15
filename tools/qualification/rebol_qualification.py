"""Replay actual Rebol bounded evidence and exact authored counts before timing.

This consumer starts no native process. It requires separate actual independent
dispositions; successful producer captures and count proposals remain unchanged.
"""
from contextlib import contextmanager, ExitStack
from datetime import datetime
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/qualification-v1'
WORK = ROOT/'tools/qualification/rebol_work_observations.py'
COUNTER = ROOT/'tools/qualification/rebol_source_units.py'
LEDGER = ROOT/'experiments/rebol/source-counts-v1/owner_ledger.py'
RULE = ROOT/'archive/validation/loc-normalization/20261012/PLAN.md'
PROFILES = ROOT/'archive/languages/rebol/20261013/drafts/private-v1/profiles.json'
FILES = {str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),
    Path(__file__).with_name('test_rebol_qualification.py'), PACKET/'README.md')}
DEPENDENCIES = {str(p.relative_to(ROOT)) for p in (WORK, COUNTER, LEDGER, PROFILES)}
TRUE_SCOPE = ('required_work_qualified','canonical_source_count_qualified','bounded_output_qualified',
              'extension_abi_qualified','full_primitive_fixtures_qualified')
FALSE_SCOPE = ('runtime_source_equivalence_proven','full_timing_qualified','chart_admission')
ROLES = dict(io='application-helper', big='application-helper', regex='application-helper',
             loader='application-launcher', extension='general-library-helper')
LIMITATIONS = {
    'tree': dict(extra_root_alias_disclosed=True, per_tree_frees_observed=False,
                 full_size_observed=False),
    'pi': dict(instrumented_forwarding_trace=True, uninstrumented_full_size_trace=False,
               negative_n27_operands_claimed=False),
    'maps': dict(final_backing_capacity_observed=True, capacity_growth_trajectory_observed=False,
                 hash_bucket_capacity_observed=False, full_pointer_identity_observed=False),
}


def require(value, message):
    if not value: raise AssertionError(message)


def encoded(value): return (json.dumps(value,indent=2)+'\n').encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def clone(value): return json.loads(json.dumps(value))
def stamp(value): return datetime.fromisoformat(value).timestamp()


def ref(value):
    require(type(value) is dict and set(value)=={'path','sha256'}, 'Exact path/SHA reference required')
    path=Path(value['path'])
    require(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts
            and re.fullmatch(r'[0-9a-f]{64}',value['sha256']) is not None,
            'Evidence must retain its original repository path and digest')
    return value


def read_small(path):
    path=Path(path)
    require(path.resolve(strict=True)==path, 'Physical original evidence path required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode), 'Regular evidence required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd)
        require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino), 'Evidence replaced before read')
        raw=stream.read(2*1024**2+1);after=path.lstat()
        require(len(raw)<=2*1024**2 and stat.S_ISREG(after.st_mode)
                and (held.st_dev,held.st_ino)==(after.st_dev,after.st_ino), 'Evidence changed or exceeded bound')
    return raw


def load(raw,path,name):
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def manifest_contract(value):
    require(value['schema']=='rebol-exact-bounded-source-qualification-v1'
            and value['status']=='independently-qualified-exact-inputs-for-full-timing'
            and value['independent_review'] is True
            and set(value['scope'])==set(TRUE_SCOPE+FALSE_SCOPE)
            and all(value['scope'][k] is True for k in TRUE_SCOPE)
            and all(value['scope'][k] is False for k in FALSE_SCOPE), 'Actual scoped independent admission required')
    require(set(value['references'])=={'source_review','primitive_review','bounded_source_review',
            'work_source_review','count_review','work_review'}, 'Qualification references differ')
    for item in value['references'].values():ref(item)
    require(set(value['stages'])=={'bounded','work'}, 'Both actual completed stages required')
    for stage in value['stages'].values():
        require(set(stage)=={'plan','report','terminal','durable'}, 'Exact stage evidence required')
        for key in ('plan','report','terminal'):ref(stage[key])
        durable=stage['durable'];require(set(durable)=={'directory','artifacts','lease'}, 'Durable inventory required')
        directory=Path(durable['directory']);lease=durable['lease']
        require(directory.is_absolute() and '..' not in directory.parts
                and directory.is_relative_to(ROOT/'experiments/shared/owned-jobs-v1/owned-jobs')
                and set(lease)=={'path','device','inode'} and lease['path']==str(directory/'owner.lock')
                and all(type(lease[k]) is int for k in ('device','inode')), 'Durable lease binding differs')


def bootstrap(manifest_ref):
    raw=read_small(manifest_ref['path']);require(digest(raw)==manifest_ref['sha256'], 'Manifest changed')
    manifest=json.loads(raw);manifest_contract(manifest)
    source_ref=manifest['references']['source_review'];raw=read_small(source_ref['path'])
    require(digest(raw)==source_ref['sha256'], 'Consumer source review changed')
    source=json.loads(raw)
    require(source['schema']=='rebol-qualification-consumer-source-review-v1'
            and source['status']=='independent-source-review-complete-actual-replay-pending'
            and source['independent_review'] is True and set(source['files'])==FILES
            and set(source['dependencies'])==DEPENDENCIES
            and source['native_execution'] is False and source['chart_admission'] is False,
            'Exact consumer source review required')
    for path in (Path(__file__),WORK):
        raw=read_small(path)
        pins=source['files'] if path==Path(__file__) else source['dependencies']
        require(digest(raw)==pins[str(path.relative_to(ROOT))], 'Consumer or dependency source changed')
        if path==WORK:w=load(raw,path,'rebol_qualification_work')
    require(w.ROOT==ROOT and Path(w.__file__)==WORK, 'Original work consumer location changed')
    return manifest,source,w


def pinned_module(e,path,expected,pins,resolutions,name):
    e.physical(path);e.pin(pins,resolutions,path,expected);raw=e.read_bytes(path)
    require(digest(raw)==expected, 'Source changed before module load')
    module=load(raw,path,name)
    require(Path(module.__file__)==path, 'Loaded module location differs')
    return module


def durable_inputs(e,stage,controller,pins,resolutions):
    durable=stage['durable'];job=e.physical(Path(durable['directory']))
    artifacts=e.inventory(job,('owner.lock',))[0]
    require(artifacts==durable['artifacts'] and {'launch.json','command-started.json','terminal.json'}<=set(artifacts),
            'Closed durable inventory differs')
    for name,item in artifacts.items():e.pin(pins,resolutions,job/name,item['sha256'])
    launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
    argv=[str(e.PYTHON),'-I','-S','-B',str(controller),'run','--plan',stage['plan']['path'],
          '--plan-sha256',stage['plan']['sha256']]
    require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
            and ended['status']=='command-exited-zero-awaiting-report-review'
            and type(ended['exit_code']) is int and ended['exit_code']==0
            and ended['actual_command_started'] is True and ended['automatic_retry'] is False
            and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False
            and type(started['command_pid']) is int and started['command_pid']>0
            and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
            and started['command_identity']==ended['command_identity'], 'Durable controller identity differs')
    return started['command_pid'],dict(directory=str(job),artifacts=artifacts)


def closed_stage(e,module,stage,expected,checker,pins,resolutions):
    """Only fixed149/work3 routing; reuse each existing independent capture check."""
    kind=expected.pop('_kind');count=149 if kind=='bounded' else 3
    schema='rebol149-bounded' if kind=='bounded' else 'rebol-three-work-observations'
    plan=e.document(stage['plan'],pins,resolutions);report=e.document(stage['report'],pins,resolutions)
    terminal=e.document(stage['terminal'],pins,resolutions);output=e.physical(Path(plan['output']))
    require(output.is_relative_to(module.PACKET) and output!=module.PACKET
            and stage['report']['path']==str(output/'report.json') and stage['terminal']['path']==str(output/'terminal.json'),
            'Closed output references differ')
    require(plan['schema']==schema+'-plan-v1' and plan['repository']==str(ROOT)
            and plan['controller']==module.__file__ and plan['controller_sha256']==pins[module.__file__]
            and plan['automatic_retry'] is False and plan['benchmark_samples']==0
            and plan['common_mutex_inode']==79859134 and plan['cleanup_timeout_seconds']==5
            and all(plan[k] is False for k in module.GATES)
            and all(plan.get(k)==v for k,v in expected.items()), 'Closed stage plan differs')
    require(set(plan['pins'])==set(plan['input_resolutions']), 'Plan named input closure differs')
    for name,sha in plan['pins'].items():
        e.pin(pins,resolutions,name,sha)
        require(resolutions[name]==plan['input_resolutions'][name], 'Original named input changed')
    ids=[slot['id'] for slot in plan['schedule']]
    require(len(ids)==len(set(ids))==count
            and report['schema']==schema+'-results-v1' and terminal['schema']==schema+'-terminal-v1'
            and report['status']==terminal['status']==module.SUCCESS
            and report['plan']==stage['plan']['path'] and report['plan_sha256']==stage['plan']['sha256']
            and report['pins']==dict(plan['pins'],**{stage['plan']['path']:stage['plan']['sha256']})
            and report['input_resolutions']==dict(plan['input_resolutions'],**{stage['plan']['path']:stage['plan']['path']})
            and report['attempts']==ids and [x['id'] for x in report['registered']]==ids
            and [x['id'] for x in report['captures']]==ids and report['active'] is None
            and len({x['pid'] for x in report['registered']})==count
            and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
            and terminal['report_sha256']==terminal['expected_report_sha256']==stage['report']['sha256']
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==79859134
            and terminal['native_processes_started']==count
            and terminal['validated_cases' if kind=='bounded' else 'validated_observations']==count
            and terminal['benchmark_samples']==report['benchmark_samples']==0
            and all(report[k] is terminal[k] is False for k in module.GATES), 'Closed producer evidence differs')
    artifacts=e.inventory(output,('report.json','terminal.json'))[0]
    names={str(Path(slot['directory'])/name) for slot in plan['schedule']
           for name in module.CAPTURE_FILES|({Path(slot['sidecar']).name} if kind=='work' else set())}
    require(set(artifacts)==names and artifacts==report['validated_files']==report['artifacts'], 'Exact stage artifact set differs')
    available=dict(artifacts,**{'report.json':dict(bytes=len(e.read_bytes(output/'report.json')),sha256=stage['report']['sha256'])})
    require(terminal['available_evidence']==available, 'Terminal artifact inventory differs')
    complete=dict(available,**{'terminal.json':dict(bytes=len(e.read_bytes(output/'terminal.json')),sha256=stage['terminal']['sha256'])})
    for name,item in complete.items():e.pin(pins,resolutions,output/name,item['sha256'])
    parent,job=durable_inputs(e,stage,Path(module.__file__),pins,resolutions)
    previous=None;observations=[]
    for slot,registered,capture in zip(plan['schedule'],report['registered'],report['captures']):
        observed,snapshot=checker(slot,output/slot['directory'],parent)
        require(observed==capture and observed['pid']==registered['pid'], 'Replayed capture differs')
        prefix=slot['directory']+'/'
        require(snapshot=={n[len(prefix):]:v for n,v in artifacts.items() if n.startswith(prefix)}, 'Capture snapshot differs')
        if previous is not None:require(previous<=stamp(observed['started_at']), 'Stage processes overlap')
        previous=stamp(observed['finished_at']);observations.append(observed)
    require(e.inventory(output)[0]==complete, 'Closed stage changed during replay')
    return plan,observations,dict(directory=str(output),artifacts=complete),job


def counts(e,review_ref,source,pins,resolutions,sources,extension):
    review=e.document(review_ref,pins,resolutions)
    require(review['schema']=='rebol15-independent-source-count-review-v1'
            and review['status']=='qualified-exact-fifteen-source-owner-counts'
            and review['independent_review'] is True and review['canonical_LOC_admitted'] is True
            and review['full_timing_qualified'] is review['chart_admission'] is False,
            'Actual independent owner/count admission required')
    require(set(review['references'])=={'proposal','rule'} and review['references']['rule']['path']==str(RULE), 'Count authority differs')
    for item in review['references'].values():ref(item)
    e.pin(pins,resolutions,RULE,review['references']['rule']['sha256'])
    proposal=e.document(review['references']['proposal'],pins,resolutions)
    units=pinned_module(e,COUNTER,source['dependencies'][str(COUNTER.relative_to(ROOT))],pins,resolutions,'rebol_qualified_units')
    ledger=pinned_module(e,LEDGER,source['dependencies'][str(LEDGER.relative_to(ROOT))],pins,resolutions,'rebol_qualified_ledger')
    require(units.ROOT==ROOT and units.LEDGER==LEDGER and len(ledger.SOURCES)==15
            and len({v['path'] for v in ledger.SOURCES.values()})==15 and len(ledger.BUNDLES)==10,
            'Finite count identities differ')
    require(proposal['schema']=='rebol-fifteen-source-count-proposal-v1' and proposal['status']=='unreviewed-projection'
            and proposal['rule_version']==review['rule_version']==ledger.RULE
            and proposal['source_files']==15 and proposal['workloads']==10
            and proposal['four_file_bundles']==8 and proposal['five_file_bundles']==2
            and proposal['decisions']==ledger.DECISIONS
            and proposal['source_identity_reviewed'] is False
            and proposal['canonical_LOC_admitted'] is proposal['native_execution'] is proposal['compiler_input_qualified']
            is proposal['required_work_qualified'] is proposal['full_timing_qualified'] is proposal['chart_admission'] is False
            and set(proposal['sources'])==set(review['sources'])==set(ledger.SOURCES)
            and set(proposal['bundles'])==set(review['bundles'])==set(sources)==set(ledger.BUNDLES), 'Count proposal scope differs')
    expected_substitutions={'corrected_c_substitution':dict(original=ledger.ORIGINAL_C,counted=ledger.CORRECTED_C,
        original_modified=False,count_both_revisions=False),'corrected_fannkuch_substitution':dict(original=ledger.ORIGINAL_FANN,
        counted=ledger.CORRECTED_FANN,original_modified=False,count_both_revisions=False)}
    require(all(proposal[k]==v for k,v in expected_substitutions.items()), 'Counted source substitutions differ')
    projections={};identities={}
    for identity,spec in ledger.SOURCES.items():
        path=ROOT/spec['path'];e.physical(path);e.pin(pins,resolutions,path,spec['reviewed_source_sha256'])
        result=units.count_source(e.read_bytes(path),identity,ledger)
        # The original proposal remains unreviewed; compare its complete exact
        # owners to the independently frozen projection without rewriting it.
        original=dict(result,source_identity_reviewed=False)
        require(original==proposal['sources'][identity], 'Complete source-owner projection differs')
        summary=dict(path=str(path),sha256=result['source_sha256'],canonical_loc=result['canonical_loc'],physical_loc=result['physical_loc'])
        require(review['sources'][identity]==summary and result['formatted_loc'] is None, 'Reviewed source count differs')
        projections[identity]=result;identities[identity]=summary
    require(identities['extension']['path']==extension['corrected_source']['path']
            and identities['extension']['sha256']==extension['corrected_source']['sha256'], 'Counted C differs from actual built extension')
    for identity in ('io','loader','big','regex'):
        require(extension['unchanged_facades'][identities[identity]['path']]==identities[identity]['sha256'], 'Counted facade differs from executed input')
    bundles={}
    for bench,members in ledger.BUNDLES.items():
        expected=(bench,'io','loader','extension')+(('big',) if bench=='pidigits' else ('regex',) if bench=='regexredux' else ())
        require(tuple(members)==expected and len(set(members))==len(members), 'Counted bundle roles differ')
        require({k:identities[bench][k] for k in ('path','sha256')}=={k:sources[bench][k] for k in ('path','sha256')}, 'Measured main differs from counted main')
        files=[dict(identity=i,path=ledger.SOURCES[i]['path'],sha256=identities[i]['sha256'],
                    canonical_loc=identities[i]['canonical_loc'],physical_loc=identities[i]['physical_loc']) for i in members]
        canonical=sum(x['canonical_loc'] for x in files);physical=sum(x['physical_loc'] for x in files)
        require(proposal['bundles'][bench]==dict(files=files,canonical_loc=canonical,physical_loc=physical,
                source_forms=1,native_samples=0,canonical_LOC_admitted=False)
                and review['bundles'][bench]==dict(members=list(members),canonical_loc=canonical,physical_loc=physical),
                'Exact bundle totals differ')
        bundles[bench]=dict(physical_inputs=[dict(identities[i],role=ROLES.get(i,'application'),counted=True) for i in members],
                           canonical_loc=canonical,physical_loc=physical,formatted_loc=None)
    return bundles,identities,review


def work_approval(e,manifest,pins,resolutions,sources,identities,runtime,image,bounded,work):
    review=e.document(manifest['references']['work_review'],pins,resolutions)
    require(review['schema']=='rebol-independent-bounded-work-review-v1'
            and review['status']=='qualified-exact-bounded-outputs-and-source-work'
            and review['independent_review'] is True
            and review['bounded_output_qualified'] is review['required_work_qualified'] is True
            and all(review[k] is False for k in FALSE_SCOPE), 'Actual independent bounded/work disposition required')
    refs={key:{name:manifest['stages'][key][name] for name in ('plan','report','terminal')} for key in ('bounded','work')}
    require(review['stages']==refs and review['runtime']==runtime and review['extension_image']==image
            and review['sources']=={i:{k:v[k] for k in ('path','sha256')} for i,v in identities.items()}
            and review['bounded_validations']==bounded and review['work_observations']==work
            and review['limitations']==LIMITATIONS, 'Reviewed actual output/work/source joins differ')
    require(set(review['source_work'])==set(sources), 'All ten source-work dispositions required')
    for bench,item in review['source_work'].items():
        require(item['main']=={k:sources[bench][k] for k in ('path','sha256')}
                and item['required_work_qualified'] is True and item['scope']=='exact-source-and-bounded-evidence',
                'Source-specific work approval differs')
        require(type(item['evidence']) is list and item['evidence'], 'Source-work evidence references required')
        for evidence in item['evidence']:
            ref(evidence);e.pin(pins,resolutions,evidence['path'],evidence['sha256'])
    growth=review['map_growth_source_review'];ref(growth);e.pin(pins,resolutions,growth['path'],growth['sha256'])
    return review


def make_bases(e,r,profiles,sources,bundles,image,pins):
    rows=profiles['profiles'];require(len(rows)==10 and len({row['benchmark'] for row in rows})==10
            and {row['benchmark'] for row in rows}==set(r.BENCHES), 'Original ten profiles differ')
    by_bench={row['benchmark']:row for row in rows};bases=[]
    dynamic=('HOME','REBOL_HOME','TMPDIR')
    fixed={k:v for k,v in e.environment(PACKET).items() if k not in dynamic}
    for bench in r.BENCHES:
        row=by_bench[bench];require(row['maximum_workers']==1 and type(row['stdin']) is bool, 'Original worker/input policy differs')
        main={k:sources[bench][k] for k in ('path','sha256')}
        require(str(PROFILES.parent/row['source'])==sources[bench]['historical_path'], 'Original profile source differs')
        bases.append(dict(original_profile_id=row['id'],benchmark=bench,language='rebol3',main=main,
            command_prefix=[str(e.RUNTIME),'-q','-s',main['path']],input_kind='stdin' if row['stdin'] else 'integer-argument',
            cwd=str(ROOT),maximum_workers=1,runtime_environment_policy=dict(fixed=fixed,
                fresh_directories={'HOME':'home','REBOL_HOME':'home','TMPDIR':'tmp'},
                extension_variable='MECH_CLBG_REBOL_PRIMITIVES',ambient_loader_overrides=False,diagnostic_flags=[]),
            **bundles[bench],corrections=dict(main=sources[bench]['substitution'],
                historical_main=dict(path=sources[bench]['historical_path'],sha256=sources[bench]['historical_sha256']),
                extension_source='exact corrected C bound to independently approved image'),
            alias_policy=dict(authored_source_forms=1,publication_forms=['compact','optimized'],
                              distinct_optimization_claim=False,copied_timing_allowed=False)))
    return bases


@contextmanager
def _yield_verified(admission,held,on_exit_failure=None,final_consumer_check=None):
    errors=[]
    try:yield admission,held
    except BaseException as error:errors.append(error)
    try:
        held.recheck()
        if final_consumer_check is not None:final_consumer_check()
    except BaseException as error:errors.append(error)
    if errors and on_exit_failure is not None:
        try:on_exit_failure()
        except BaseException as error:errors.append(error)
    if len(errors)==1:raise errors[0]
    if errors:raise BaseExceptionGroup('Qualification body/closure/cleanup failed',errors)


def guarded_recheck(e,pins,resolutions,admission,leases,absent,closures,jobs):
    fixed_pins=dict(pins);fixed_resolutions=dict(resolutions);fixed_admission=encoded(admission)
    absent=clone(absent);closures=clone(closures);jobs=clone(jobs);leases=tuple(leases)
    def check():
        require(all(pins.get(k)==v for k,v in fixed_pins.items())
                and all(resolutions.get(k)==v for k,v in fixed_resolutions.items()), 'Qualification-owned input pin removed or rebound')
        require(encoded(admission)==fixed_admission, 'Yielded qualification content changed')
        e.verify(pins,resolutions,absent,closures)
        for job in jobs:require(e.inventory(Path(job['directory']),('owner.lock',))[0]==job['artifacts'], 'Closed durable artifact changed')
        e.check_leases(leases)
    return check


@contextmanager
def _held_review(manifest_path,manifest_sha,on_exit_failure=None,final_consumer_check=None):
    manifest_ref=ref(dict(path=str(manifest_path),sha256=manifest_sha))
    initial,source,w=bootstrap(manifest_ref);refs=initial['references']
    with w.held(refs['primitive_review'],refs['bounded_source_review'],refs['work_source_review']) as inherited:
        r,p,e,adapter,consumers,inspector,common,leases,intake,extension,primitive,pins,resolutions=inherited
        manifest=e.document(manifest_ref,pins,resolutions)
        require(manifest==initial and e.document(refs['source_review'],pins,resolutions)==source, 'Qualification review changed after locking')
        for name,sha in {**source['files'],**source['dependencies']}.items():e.pin(pins,resolutions,ROOT/name,sha)
        with ExitStack() as stack:
            combined=list(leases)
            for key in ('bounded','work'):
                lease=manifest['stages'][key]['durable']['lease'];path=Path(lease['path'])
                require(path not in [Path(item[0]) for item in combined], 'Repeated closed-stage lease')
                stream=stack.enter_context(e.regular(path));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                combined.append((path,stream,(lease['device'],lease['inode'])))
            e.check_leases(combined)
            try:
                prior,closures,jobs,image=r.primitive_inputs(p,e,adapter,inspector,primitive,intake,extension,pins,resolutions)
                cases=r.corpus(e,pins,resolutions)
                spec=e.document(dict(path=str(r.ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),pins,resolutions)
                mapping=e.document(dict(path=str(r.ORIGINAL/'bounded-corpus-map.json'),
                    sha256=spec['fixture_source_pins']['bounded-corpus-map.json']),pins,resolutions)
                sources=r.source_selection(e,spec,mapping,cases,pins,resolutions)
                checker=pinned_module(e,r.CHECKER,pins[str(r.CHECKER)],pins,resolutions,'rebol_qualification_outputs')
                common_plan=dict(primitive_review=refs['primitive_review'],extension_image=image,corrected_source=extension['corrected_source'],
                    unavailable_inputs=prior['unavailable_inputs'],prerequisite_artifact_closures=closures,prior_durable_jobs=jobs,
                    historical_sources_preserved=True)
                bounded_stage=manifest['stages']['bounded'];out=Path(e.document(bounded_stage['plan'],pins,resolutions)['output'])
                expected=dict(common_plan,_kind='bounded',source_review=refs['bounded_source_review'],sources=sources,
                    corpus=dict(path=str(r.CORPUS),sha256=r.CORPUS_SHA),limits=spec['limits'],
                    historical_spec=dict(path=str(r.ORIGINAL/'spec.json'),sha256=p.SPEC_SHA),
                    schedule=r.schedule(e,checker,cases,sources,image,out,spec['limits']),native_processes=149,
                    success_cases=142,rejection_cases=7,compilations=0,matched_controls=0)
                bounded_plan,bounded,closure,job=closed_stage(e,r,bounded_stage,expected,
                    lambda slot,directory,parent:r.checked_case(e,inspector.kb,checker,slot,directory,parent),pins,resolutions)
                bounded_closure,bounded_job=closure,job
                work_stage=manifest['stages']['work'];out=Path(e.document(work_stage['plan'],pins,resolutions)['output'])
                by_id={(c['benchmark'],c['case']):c for c in cases};selected=[by_id[i] for i in w.CASES]
                expected=dict(common_plan,_kind='work',source_review=refs['work_source_review'],bounded_source_review=refs['bounded_source_review'],
                    schedule=w.schedule(e,selected,image,out),native_processes=3,compilations=0,matched_controls=0)
                work_plan,work,closure,job=closed_stage(e,w,work_stage,expected,
                    lambda slot,directory,parent:w.checked_case(r,e,adapter,consumers,inspector.kb,slot,directory,parent),pins,resolutions)
                closures=closures+[bounded_closure,closure];jobs=jobs+[bounded_job,job]
                bundles,identities,count_review=counts(e,refs['count_review'],source,pins,resolutions,sources,extension)
                runtime=dict(path=str(e.RUNTIME),sha256=pins[str(e.RUNTIME)])
                approval=work_approval(e,manifest,pins,resolutions,sources,identities,runtime,image,bounded,work)
                # This original source proposal supplies IDs and input/worker
                # policy only. Its historical false admission flags stay false.
                require(str(PROFILES) in pins, 'Original profile document lacks inherited pin')
                profiles=e.document(dict(path=str(PROFILES),sha256=pins[str(PROFILES)]),pins,resolutions)
                bases=make_bases(e,r,profiles,sources,bundles,image,pins)
                admission=dict(schema='rebol-pre-timing-admission-v1',manifest=manifest_ref,bases=bases,
                    runtime=dict(binary=runtime,toolchain_intake=extension['references']['toolchain_intake'],
                        extension_review=primitive['references']['extension_review'],
                        declared_image_closure=extension['declared_image_closure'],
                        actual_layout_and_load_refs=extension['references'],interpreter_loaded_images_observed=False,
                        runtime_source_equivalence_proven=False),extension_image=image,
                    references=clone(dict(refs,stages=manifest['stages'])),unavailable_inputs=prior['unavailable_inputs'],
                    artifact_closures=closures,durable_jobs=jobs,
                    lease_identities=[dict(path=str(path),device=identity[0],inode=identity[1]) for path,_,identity in combined],
                    scope=dict(manifest['scope'],limitations=clone(LIMITATIONS)))
                recheck=guarded_recheck(e,pins,resolutions,admission,combined,prior['unavailable_inputs'],closures,jobs)
                held=types.SimpleNamespace(pins=pins,resolutions=resolutions,common=common,leases=tuple(combined),
                                           evidence=e,checker=checker,recheck=recheck)
                recheck()
                with _yield_verified(admission,held,on_exit_failure,final_consumer_check) as value:yield value
            finally:e.check_leases(combined)


@contextmanager
def review_context(manifest_path,manifest_sha,on_exit_failure=None,final_consumer_check=None):
    """Late inherited-helper exit errors also reach the failure callback.

    Normal body/check failures call cleanup before releasing any lease. An
    inherited context's own final check can fail while that context unwinds;
    the failure callback must then inspect its retained common stream and must
    not claim the mutex is held after that stream has closed.
    """
    cleaned=False
    def cleanup():
        nonlocal cleaned
        cleaned=True
        if on_exit_failure is not None:on_exit_failure()
    try:
        with _held_review(manifest_path,manifest_sha,cleanup,final_consumer_check) as value:yield value
    except BaseException as error:
        if not cleaned and on_exit_failure is not None:
            try:cleanup()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup('Qualification exit and cleanup failed',[error,cleanup_error])
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args()
    with review_context(args.manifest,args.manifest_sha256) as (admission,held):
        result=encoded(admission)
    print(result.decode(),end='')


if __name__=='__main__':main()
