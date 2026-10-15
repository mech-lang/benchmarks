"""Exact linker-option continuation around the frozen combined fixed19 intake."""
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
BASE=ROOT/'tools/qualification/rebol_primitive_fixtures_combined.py'
BASE_SHA='95e3b713c5d0adbec6db1ab03d1251a8e49f5aaae9056d36906bcc0927b41742'
BASE_INTAKE_ADAPTER=dict(path=str(BASE),sha256=BASE_SHA)
HEADER_ROOT=ROOT/'experiments/rebol/primitive-fixtures-v2/diagnostic-headers-v1/include'
HEADER=HEADER_ROOT/'mach-o/dyld-interposing.h'
HEADER_SHA='763eeb269c19216b7963345567b9d20ca6591c73249571019a8763f8fcdc0e71'
HEADER_REVIEW=dict(path=str(HEADER_ROOT.parent/'source-review.json'),sha256='bdddfbb718f1a18550a3cbfad09f2cf1c7641615d55d5074388dd62291284204')
STAGES=('original_build','scoped_load_failure','rebx_load')
BASE_REVIEW=dict(path=str(ROOT/'experiments/rebol/primitive-fixtures-v2/combined-intake-v1/source-review-v1.json'),sha256='a88e3f5040bb60d820cd70ec34ecd75024410b18f03be44cb84055554e59372f')
FAILURE=dict(path=str(ROOT/'experiments/rebol/primitive-fixtures-v2/combined-intake-v1/failed-stage-review-v1.json'),sha256='8e6a1c4b588e01646cfe3cd250d3624384da636dd969a8427c28ef0756fde907')
PACKET=ROOT/'experiments/rebol/primitive-fixtures-v2/linker-invocation-v1'
SOURCE_FILES={str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),Path(__file__).with_name('test_rebol_primitive_fixtures_linker.py'),PACKET/'README.md')}

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def validate_prior_failure(e,pins,resolutions):
    review=e.document(FAILURE,pins,resolutions)
    require(review['schema']=='rebol-fixed19-independent-failed-closure-v1'
        and review['status']=='diagnostic-compiler-failure-preserved-owned-stage-closed'
        and review['native_attempts']==1 and review['validated_captures']==review['rebol_fixture_processes']==0
        and review['compiler_exit_status']==1 and review['compiler_outputs']==[],'Exact failed first diagnostic compile required')
    plan=e.document(review['plan'],pins,resolutions);report=e.document(review['report'],pins,resolutions);terminal=e.document(review['terminal'],pins,resolutions)
    require(plan['intake_adapter']==dict(path=str(BASE),sha256=BASE_SHA) and plan['source_review']==BASE_REVIEW
        and report['status']==terminal['status']=='stopped-unqualified' and report['captures']==[]
        and report['attempts']==['compile-io-interposer'] and report['active'] is None
        and report['integrity_errors']==report['artifact_errors']==terminal['integrity_errors']==terminal['artifact_errors']==[]
        and terminal['common_mutex_held'] is True and terminal['native_processes_started']==1 and terminal['validated_captures']==0
        and terminal['report_sha256']==terminal['expected_report_sha256']==review['report']['sha256'],'Prior failed producer changed')
    for name,expected in report['pins'].items():
        e.pin(pins,resolutions,name,expected);require(resolutions[name]==report['input_resolutions'][name],'Prior failed named input changed')
    output=Path(plan['output']);durable=review['durable'];job=Path(durable['directory'])
    require(e.inventory(output)[0]==review['artifacts'] and e.inventory(job,('owner.lock',))[0]==durable['artifacts'],'Prior failed artifacts changed')
    for directory,items in ((output,review['artifacts']),(job,durable['artifacts'])):
        for name,item in items.items():e.pin(pins,resolutions,directory/name,item['sha256'])
    return dict(review=FAILURE,**{k:review[k] for k in ('plan','report','terminal')},durable=durable),dict(directory=str(output),artifacts=review['artifacts'])

def attach(f,adapter_ref):
    old_bootstrap,old_held,old_compile,old_build,old_verify=f.bootstrap,f.held,f.compile_slot,f.build_plan,f.verify_inputs
    def source_review(source_ref):
        raw=f.bootstrap_read(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Linker source review changed');value=json.loads(raw)
        require(value['schema']=='rebol-fixed19-linker-source-review-v1'
            and value['status']=='independent-source-review-complete-native-fixtures-pending'
            and value['independent_review'] is True and set(value['files'])==SOURCE_FILES
            and value['dependencies']=={str(BASE.relative_to(ROOT)):BASE_SHA} and value['base_source_review']==BASE_REVIEW
            and all(value[k] is False for k in f.GATES)
            and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))]==adapter_ref['sha256'],'Exact additive linker source review required')
        return value
    def bootstrap(extension_ref,source_ref):
        value=source_review(source_ref);e,extension,_=old_bootstrap(extension_ref,BASE_REVIEW)
        return e,extension,value
    @contextmanager
    def held(extension_ref,source_ref):
        initial=source_review(source_ref)
        with old_held(extension_ref,BASE_REVIEW) as inherited:
            e,transport,inspector,common,leases,intake,extension,pins,resolutions=inherited
            current=e.document(source_ref,pins,resolutions);require(current==initial,'Linker review changed after acquisition')
            for name,expected in current['files'].items():e.pin(pins,resolutions,ROOT/name,expected)
            failed=e.document(FAILURE,pins,resolutions);lease=failed['durable']['lease'];path=Path(lease['path'])
            require(path==Path(failed['durable']['directory'])/'owner.lock' and path not in [x[0] for x in leases],'Distinct failed-stage lease required')
            with e.regular(path) as stream:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);combined=leases+[(path,stream,(lease['device'],lease['inode']))]
                e.check_leases(combined)
                try:yield e,transport,inspector,common,combined,intake,extension,pins,resolutions
                finally:e.check_leases(combined)
    def compile_slot(e,intake,output):
        value=old_compile(e,intake,output);before='-fuse-ld='+intake['tools']['linker']['path']
        require(value['command'].count(before)==1 and not any(x.startswith('--ld-path=') for x in value['command']),'Exact original linker option required')
        value['command'][value['command'].index(before)]='--ld-path='+intake['tools']['linker']['path']
        return value
    def build_plan(e,transport,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions):
        failure,closure=validate_prior_failure(e,pins,resolutions)
        value=old_build(e,transport,inspector,output,extension_ref,source_ref,intake,extension,pins,resolutions)
        value['prior_fixed19_failure']=failure;value['prerequisite_artifact_closures'].append(closure)
        value['linker_adapter']=dict(adapter_ref);value['entrypoint']=adapter_ref['path']
        return value
    def verify_inputs(e,plan,pins,resolutions,leases):
        old_verify(e,plan,pins,resolutions,leases)
        prior=plan['prior_fixed19_failure']['durable']
        require(e.inventory(Path(prior['directory']),('owner.lock',))[0]==prior['artifacts'],'Failed-stage durable inventory changed')
        e.check_leases(leases)
    f.bootstrap,f.held,f.compile_slot,f.build_plan,f.verify_inputs=bootstrap,held,compile_slot,build_plan,verify_inputs
    f.validate_prior_failure=validate_prior_failure
    f.linker_adapter=dict(adapter_ref);f.intake_adapter=dict(BASE_INTAKE_ADAPTER)
    for name in ('HEADER_ROOT','HEADER','HEADER_SHA','HEADER_REVIEW','STAGES'):setattr(f,name,globals()[name])
    return f

def load_controller(expected):
    before=BASE.lstat();require(stat.S_ISREG(before.st_mode) and BASE.resolve()==BASE,'Physical regular base controller required')
    with os.fdopen(os.open(BASE,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Base controller replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2 and digest(raw)==BASE_SHA,'Frozen combined adapter changed')
    base=types.ModuleType('linker_combined_intake');base.__file__=str(BASE);exec(compile(raw,str(BASE),'exec'),base.__dict__)
    require(all(getattr(base,name)==globals()[name] for name in ('HEADER_ROOT','HEADER','HEADER_SHA','HEADER_REVIEW','STAGES')),'Diagnostic constants differ from frozen base')
    f=base.load_controller(BASE_SHA);own=Path(__file__).resolve();require(digest(f.bootstrap_read(own))==expected,'Linker adapter changed')
    return attach(f,dict(path=str(own),sha256=expected))

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--adapter-sha256',required=True)
    args,remaining=parser.parse_known_args();module=load_controller(args.adapter_sha256);previous=sys.argv
    try:sys.argv=[previous[0],*remaining];module.main()
    finally:sys.argv=previous

if __name__=='__main__':main()
