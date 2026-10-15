"""Explicit .rebx image continuation around the frozen one-load controller."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/rebol/extension-api-v2'
ORIGINAL=ROOT/'tools/qualification/rebol_extension_load_only.py'
ORIGINAL_SHA='54fc9c69dba361cb49dc8c5cb20872c6a280f986bec6dbc8d7c5745216fd631f'
TYPED=ROOT/'tools/qualification/rebol_extension_typed_images.py'
TYPED_SHA='bec9d1e020cfd2449ecdd5e1dced224f6ccbf050785fd9390e3d07931d499124'
OLD_IMAGE=PACKET/'run-v1/build/clbg_primitives.dylib'
IMAGE_SHA='245e6834c1719e15f888af5ac073854f917bd685ae0ca2dee0eff095028a8539'
ALIAS=PACKET/'rebx-image-v1/clbg_primitives.rebx'
PRIOR_PLAN=PACKET/'load-only-plan-v1.json'
PRIOR_PLAN_SHA='cce6b33e17a683e9778fb47b76a0496c99db0d7057a4506af516dfb140cd2eb6'
PRIOR_OUTPUT=PACKET/'load-only-run-v1'
PRIOR_JOB=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-extension-load1-v1'
PRIOR_LEASE=(16777232,82420479)
REVIEW=Path('/private/tmp/mech-history-candidate-validation/rebol-load-only-independent-closure-v1.json')
REVIEW_SHA='1e0f36d4803ab7fea65cfe3ed3b6f0ad610b1badcb4505a09521eeb168146c7c'
DIAGNOSIS=PACKET/'extension-import-v1/source-diagnosis.json'
DIAGNOSIS_SHA='0ca8494f5e4328cf24227c333d137b6814de2cb612f20054fdfb5fe81a9594fd'


def require(value,message):
    if not value:raise AssertionError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def image_alias(e,inspector,pins,resolutions,create):
    e.pin(pins,resolutions,OLD_IMAGE,IMAGE_SHA)
    raw=e.read_bytes(OLD_IMAGE);require(digest(raw)==IMAGE_SHA,'Original image changed')
    e.physical(ALIAS)
    if not os.path.lexists(ALIAS):
        require(create,'Prepared .rebx image is missing')
        ALIAS.parent.mkdir(parents=True,exist_ok=True)
        with inspector.kb.atomic():
            with ALIAS.open('xb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
    require(e.read_bytes(ALIAS)==raw,'The .rebx copy must preserve every image byte')
    e.pin(pins,resolutions,ALIAS,IMAGE_SHA)
    return dict(original=dict(path=str(OLD_IMAGE),sha256=IMAGE_SHA),
        alias=dict(path=str(ALIAS),sha256=IMAGE_SHA),bytes=len(raw),byte_identical=True,
        binary_rebuilt=False,original_install_name_unchanged=True)


def prior_failure(e,pins,resolutions):
    ref=dict(path=str(REVIEW),sha256=REVIEW_SHA);review=e.document(ref,pins,resolutions)
    require(review['schema']=='rebol-load-only-independent-failed-closure-v1'
        and review['status']=='failed-load-retained-owned-stage-closed'
        and review['plan']==dict(path=str(PRIOR_PLAN),sha256=PRIOR_PLAN_SHA)
        and review['native_exit_status']==1 and review['producer_status']=='stopped-unqualified'
        and review['durable_status']=='command-failed' and review['new_successful_captures']==0
        and review['original_three_successes_and_failed_fourth_preserved'] is True
        and review['extension_load_qualified'] is False,'Exact failed load disposition required')
    plan=e.document(review['plan'],pins,resolutions)
    require(plan['controller']==str(ORIGINAL) and plan['controller_sha256']==ORIGINAL_SHA
        and plan['output']==str(PRIOR_OUTPUT),'Prior continuation identity differs')
    for name,expected in plan['pins'].items():
        e.pin(pins,resolutions,name,expected)
        require(resolutions[name]==plan['input_resolutions'][name],'Prior named input changed')
    report=e.document(review['report'],pins,resolutions);terminal=e.document(review['terminal'],pins,resolutions)
    require(report['status']==terminal['status']=='stopped-unqualified' and report['captures']==[]
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==1
        and terminal['validated_captures']==0 and terminal['report_sha256']==terminal['expected_report_sha256']==review['report']['sha256'],
        'Prior load failure was not closed')
    artifacts=e.inventory(PRIOR_OUTPUT)[0]
    require(artifacts==review['artifacts'],'Prior failed capture membership/bytes changed')
    durable=e.inventory(PRIOR_JOB,('owner.lock',))[0]
    require(review['durable']==dict(directory=str(PRIOR_JOB),artifacts=durable),'Prior durable capture changed')
    for directory,values in ((PRIOR_OUTPUT,artifacts),(PRIOR_JOB,durable)):
        for name,item in values.items():e.pin(pins,resolutions,directory/name,item['sha256'])
    return dict(review=ref,plan=review['plan'],report=review['report'],terminal=review['terminal'],
        durable=dict(directory=str(PRIOR_JOB),artifacts=durable,
            lease=dict(path=str(PRIOR_JOB/'owner.lock'),device=PRIOR_LEASE[0],inode=PRIOR_LEASE[1]))),dict(directory=str(PRIOR_OUTPUT),artifacts=artifacts)


def attach(module,adapter_ref,create):
    old_held,old_plan,old_verify,old_slot=module.held,module.build_plan,module.verify,module.corrected_slot
    @contextmanager
    def held(e,own_sha):
        with old_held(e,own_sha) as (old,common,leases,intake,pins,resolutions,inspector):
            with e.regular(PRIOR_JOB/'owner.lock') as stream:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                combined=leases+[(PRIOR_JOB/'owner.lock',stream,PRIOR_LEASE)]
                e.check_leases(combined)
                e.pin(pins,resolutions,adapter_ref['path'],adapter_ref['sha256'])
                e.pin(pins,resolutions,DIAGNOSIS,DIAGNOSIS_SHA)
                module.REBX_ALIAS=image_alias(e,inspector,pins,resolutions,create)
                try:yield old,common,combined,intake,pins,resolutions,inspector
                finally:e.check_leases(combined)
    def slot(e,old,output):
        value=old_slot(e,old,output)
        value['environment']['MECH_CLBG_REBOL_PRIMITIVES']=str(ALIAS)
        return value
    def plan(e,old,output,pins,resolutions,inspector):
        previous,closure=prior_failure(e,pins,resolutions)
        intake=e.document(old['toolchain_intake'],pins,resolutions)
        declared=e.built_image_closure([ALIAS],intake,inspector,pins)
        value=old_plan(e,old,output,pins,resolutions,inspector)
        value['prior_load_failure']=previous
        value['prerequisite_artifact_closures'].append(closure)
        value['rebx_image']=dict(module.REBX_ALIAS,declared_image_closure=declared)
        value['rebx_adapter']=dict(adapter_ref);value['entrypoint']=adapter_ref['path']
        value['suffix_dispatch_source_review']=dict(path=str(DIAGNOSIS),sha256=DIAGNOSIS_SHA)
        return value
    def verify(e,plan,pins,resolutions,leases):
        old_verify(e,plan,pins,resolutions,leases)
        previous=plan['prior_load_failure']['durable']
        require(e.inventory(PRIOR_JOB,('owner.lock',))[0]==previous['artifacts'],'Prior load durable inventory changed')
        require(e.read_bytes(ALIAS)==e.read_bytes(OLD_IMAGE),'Prepared alias changed')
        e.check_leases(leases)
    module.held,module.corrected_slot,module.build_plan,module.verify=held,slot,plan,verify
    return module


def load_controller(expected,create=False):
    raw=TYPED.read_bytes();require(digest(raw)==TYPED_SHA,'Frozen typed adapter changed')
    typed=types.ModuleType('rebx_typed_source');typed.__file__=str(TYPED)
    exec(compile(raw,str(TYPED),'exec'),typed.__dict__)
    source=Path(__file__).resolve();typed.checked(source,expected)
    raw=typed.checked(ORIGINAL,ORIGINAL_SHA)
    module=types.ModuleType('rebx_original_load_only');module.__file__=str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),module.__dict__)
    return attach(module,dict(path=str(source),sha256=expected),create)


def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args()
    require(remaining and remaining[0] in ('prepare','run'),'Prepare or run required')
    module=load_controller(args.adapter_sha256,remaining[0]=='prepare')
    previous=sys.argv
    try:
        sys.argv=[previous[0],'--controller-sha256',ORIGINAL_SHA,*remaining]
        module.main()
    finally:sys.argv=previous


if __name__=='__main__':main()
