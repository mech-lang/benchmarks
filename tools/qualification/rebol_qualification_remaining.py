"""Replay split primitive evidence and corrected source counts before timing.

The original qualification consumer retains all workload, work-observation,
count-owner and held-lease checks. This adapter binds the additive entrypoints
and the approved copied count ledger without altering earlier evidence.
"""
import argparse
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
WORK=ROOT/'tools/qualification/rebol_work_remaining.py'
BOUNDED=ROOT/'tools/qualification/rebol_bounded_remaining.py'
PRIMITIVE=ROOT/'tools/qualification/rebol_primitive_remaining.py'
BINDING=ROOT/'tools/qualification/rebol_regex_reviewed_count_ledger.py'
BINDING_SHA='601da9225a7976dd70843eeb042ee04fd94b8af31cb34b9ac3f27eb597628743'
BINDING_REVIEW=dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/source-counts-v1/binding-source-review-v1.json'),
    sha256='cfd993fbd1575cf2674e4a25a39df2ea6a6ef609831a73998380551fbaf68080')
COUNTS=dict(path=str(ROOT/'experiments/rebol/regex-literals-v1/source-counts-v1/count-review-v1.json'),
    sha256='21178b501437f2cda34fd261641960061bca56a94575a9e883bb407ac587562a')
PACKET=ROOT/'experiments/rebol/qualification-v1/remaining-intake-v1'


def require(value,message):
    if not value:raise AssertionError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def command_for(e,controller,plan_ref,refs):
    """Bind the actual reviewed adapter argv, retaining original controller IDs."""
    if Path(controller)==ROOT/'tools/qualification/rebol_bounded.py':
        entry=refs['bounded'];options=['--primitive-adapter-sha256',refs['primitive']['sha256']]
    elif Path(controller)==ROOT/'tools/qualification/rebol_work_observations.py':
        entry=refs['work'];options=['--bounded-adapter-sha256',refs['bounded']['sha256'],
            '--primitive-adapter-sha256',refs['primitive']['sha256']]
    else:raise AssertionError('Only bounded and work producer entrypoints are allowed')
    return [str(e.PYTHON),'-I','-S','-B',entry['path'],'--adapter-sha256',entry['sha256'],*options,
            'run','--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256']]


def check_stage_adapter(plan,kind,refs):
    entry=refs[kind]
    require(plan['intake_adapter']==entry and plan['entrypoint']==entry['path']
        and plan['primitive_intake_adapter']==refs['primitive'],'Closed stage adapter identity differs')
    if kind=='work':require(plan['bounded_intake_adapter']==refs['bounded'],'Work bounded intake differs')


def attach(q,supplemental,refs):
    old_load,old_bootstrap,old_closed,old_counts,old_pinned=q.load,q.bootstrap,q.closed_stage,q.counts,q.pinned_module
    q.FILES |= {str(p.relative_to(ROOT)) for p in (Path(refs['qualification']['path']),
        Path(__file__).with_name('test_rebol_qualification_remaining.py'),PACKET/'README.md')}
    dependencies={str(ROOT/name):None for name in q.DEPENDENCIES}
    dependencies.update({v['path']:v['sha256'] for k,v in refs.items() if k!='qualification'})
    dependencies.update({str(BINDING):BINDING_SHA,BINDING_REVIEW['path']:BINDING_REVIEW['sha256']})
    q.DEPENDENCIES={str(Path(p).relative_to(ROOT)) for p in dependencies}

    def load(raw,path,name):
        if Path(path)==q.WORK:
            return supplemental.load_controller(refs['work']['sha256'],refs['bounded']['sha256'],refs['primitive']['sha256'])
        return old_load(raw,path,name)

    def bootstrap(manifest_ref):
        manifest,source,w=old_bootstrap(manifest_ref)
        require(source['files'][str(ORIGINAL.relative_to(ROOT))]==ORIGINAL_SHA
            and source['files'][str(Path(refs['qualification']['path']).relative_to(ROOT))]==refs['qualification']['sha256'],
            'Exact original and additive qualification sources required')
        require(all(source['dependencies'][str(Path(p).relative_to(ROOT))]==sha
            for p,sha in dependencies.items() if sha is not None),'Qualification dependency identity differs')
        require(manifest['references']['count_review']==COUNTS,'Corrected regex source-count admission required')
        return manifest,source,w

    def durable_inputs(e,stage,controller,pins,resolutions):
        durable=stage['durable'];job=e.physical(Path(durable['directory']))
        artifacts=e.inventory(job,('owner.lock',))[0]
        require(artifacts==durable['artifacts'] and {'launch.json','command-started.json','terminal.json'}<=set(artifacts),
            'Closed durable inventory differs')
        for name,item in artifacts.items():e.pin(pins,resolutions,job/name,item['sha256'])
        launch,started,ended=[json.loads(e.read_bytes(job/name)) for name in ('launch.json','command-started.json','terminal.json')]
        argv=command_for(e,controller,stage['plan'],refs)
        require(launch['command']==started['command']==argv and launch['cwd']==started['cwd']==str(ROOT)
            and ended['status']=='command-exited-zero-awaiting-report-review'
            and type(ended['exit_code']) is int and ended['exit_code']==0
            and ended['actual_command_started'] is True and ended['automatic_retry'] is False
            and ended['stop_signals']==[] and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False
            and type(started['command_pid']) is int and started['command_pid']>0
            and started['command_pid']==ended['command_pid']==started['command_identity']['pid']==ended['command_identity']['pid']
            and started['command_identity']==ended['command_identity'],'Durable adapter ownership differs')
        return started['command_pid'],dict(directory=str(job),artifacts=artifacts)

    def closed_stage(e,module,stage,expected,checker,pins,resolutions):
        plan=e.document(stage['plan'],pins,resolutions)
        check_stage_adapter(plan,expected['_kind'],refs)
        return old_closed(e,module,stage,expected,checker,pins,resolutions)

    def counts(e,review_ref,source,pins,resolutions,sources,extension):
        require(review_ref==COUNTS,'Only the exact corrected-source count review is admitted')
        review=e.document(review_ref,pins,resolutions)
        approval=e.document(BINDING_REVIEW,pins,resolutions)
        require(approval['schema']=='rebol-corrected-regex-count-binding-source-review-v1'
            and approval['status']=='independent-source-review-complete' and approval['independent_review'] is True
            and approval['files'][str(BINDING.relative_to(ROOT))]['sha256']==BINDING_SHA
            and approval['native_execution'] is approval['chart_admission'] is False,'Count binding source review differs')
        binding=old_pinned(e,BINDING,BINDING_SHA,pins,resolutions,'rebol_corrected_count_binding')
        proposal=e.document(review['references']['proposal'],pins,resolutions)
        require(proposal['corrected_regex_substitution']==review['corrected_regex_substitution']==binding.REGEX_SUBSTITUTION,
            'Corrected regex count substitution differs')
        def pinned_module(e,path,expected,pins,resolutions,name):
            module=old_pinned(e,path,expected,pins,resolutions,name)
            return binding.bind_ledger(module,review) if Path(path)==q.LEDGER else module
        require(q.pinned_module is old_pinned,'Count replay cannot nest or replace another module loader')
        q.pinned_module=pinned_module
        try:return old_counts(e,review_ref,source,pins,resolutions,sources,extension)
        finally:q.pinned_module=old_pinned

    q.load,q.bootstrap,q.durable_inputs,q.closed_stage,q.counts=load,bootstrap,durable_inputs,closed_stage,counts
    q.intake_adapters=refs
    return q


def load_controller(expected,work_expected,bounded_expected,primitive_expected):
    # Bootstrap the original physical-file reader before executing it.
    before=ORIGINAL.lstat()
    require(ORIGINAL.resolve()==ORIGINAL and stat.S_ISREG(before.st_mode),
        'Physical original qualification consumer required')
    with os.fdopen(os.open(ORIGINAL,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno())
        require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Qualification consumer replaced')
        raw=stream.read(2*1024**2+1)
        require(len(raw)<=2*1024**2 and digest(raw)==ORIGINAL_SHA,'Frozen qualification consumer changed')
    q=types.ModuleType('rebol_original_remaining_qualification');q.__file__=str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),q.__dict__)
    refs={key:q.ref(dict(path=str(path),sha256=sha)) for key,path,sha in (
        ('qualification',Path(__file__).resolve(),expected),('work',WORK,work_expected),
        ('bounded',BOUNDED,bounded_expected),('primitive',PRIMITIVE,primitive_expected))}
    verified={}
    for key,ref in refs.items():
        raw=q.read_small(ref['path'])
        require(digest(raw)==ref['sha256'],'Qualification adapter changed')
        verified[key]=raw
    supplemental=q.load(verified['work'],WORK,'rebol_remaining_work_loader')
    return attach(q,supplemental,refs)


def main():
    parser=argparse.ArgumentParser(add_help=False)
    for name in ('adapter','work-adapter','bounded-adapter','primitive-adapter'):parser.add_argument('--'+name+'-sha256',required=True)
    args,remaining=parser.parse_known_args()
    q=load_controller(args.adapter_sha256,args.work_adapter_sha256,args.bounded_adapter_sha256,args.primitive_adapter_sha256)
    sys.argv=[str(ORIGINAL),*remaining];q.main()


if __name__=='__main__':main()
