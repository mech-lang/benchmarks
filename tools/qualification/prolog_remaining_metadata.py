"""Review retained Prolog runtime metadata across three actual timing cohorts.

No producer, native runtime or compiler executes. Five existing leases remain
held through metadata, candidate construction, optional import and final checks.
Stopped reports keep their original statuses and receipt identities.
"""
import argparse
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
RECONCILER=Path(__file__).with_name('prolog_remaining_reconcile.py')
RECONCILER_SHA='74a6b1cdaeffa370619cd8099b57e7127d98ae38a6cf0ccecaeb1901f416621e'
HELPER=Path(__file__).with_name('prolog_linear_metadata.py')
HELPER_SHA='501d15188c55599712c2cd6480b8568ad1029657dfcedd89a5a66594ab8d758f'


def module(path,expected):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Frozen independent reviewer changed: '+str(path))
    spec=importlib.util.spec_from_file_location(path.stem+'_remaining_publication',path)
    result=importlib.util.module_from_spec(spec);exec(compile(raw,str(path),'exec'),result.__dict__)
    return result


n=module(RECONCILER,RECONCILER_SHA)
f=module(HELPER,HELPER_SHA)
l,r,p,require,same=n,n.r,n.p,n.require,n.same
SCHEMA='prolog-three-cohort-recorded-runtime-metadata-v1'
runtime_context,original_profile,linear_profile=f.runtime_context,f.original_profile,f.linear_profile


def inspect(plan, prior, previous, reconciliation, outcome, read, read_raw):
    _,all_profiles,_=n.schedule(plan,prior,previous)
    require(reconciliation['schema']==l.SCHEMA
            and reconciliation['status']=='full50-plus-retained40-reconciled-awaiting-runtime-and-publication-review'
            and reconciliation['file_integrity_verified'] is True
            and reconciliation['runtime_publication_metadata_qualified'] is False
            and reconciliation['full_timings_qualified'] is reconciliation['chart_admission'] is False,
            'Completed independent continuation reconciliation required')
    same(reconciliation['plan'],dict(path=str(l.PLAN),sha256=l.PLAN_SHA),'Wrong continuation plan')
    for path,digest in {**plan['pins'],str(RECONCILER):RECONCILER_SHA,str(n.HELPER):n.HELPER_SHA,str(r.HELPER):r.HELPER_SHA}.items():
        require(reconciliation['verified_file_pins'].get(path)==digest,'Reconciliation omitted a prerequisite')
    require(outcome['status']=='qualified-original-Prolog20-work-and-LOC-awaiting-full90'
            and outcome['source_work_qualified'] is outcome['canonical_LOC_admitted'] is True
            and outcome['chart_admission'] is False and p.integer(outcome['profiles'],20),
            'Original source-work/LOC seal incomplete')
    config,feature,images,os_images=runtime_context(plan,read,read_raw)
    rows=[row for row in all_profiles.values() if row['language']=='prolog']
    by_id={row['id']:row for row in rows};eligible=[];excluded=[]
    for row in rows:
        same(row['runtime_environment'],config['environment'],'Profile runtime environment differs')
        require(row['binary']==config['binary'] and row['binary_sha256']==config['binary_sha256']
                and p.integer(row['maximum_workers'],1),'Runtime or worker policy differs')
        if row['benchmark']=='revcomp':
            qlf,vendor,loaded=linear_profile(plan,row,config,images,read,read_raw)
        else:
            qlf,vendor,loaded=original_profile(plan,outcome,row,config,images,read)
        alias=row['source_alias_of']
        if row['variant']=='optimized':
            require(alias==row['id'].removesuffix('-optimized')+'-compact'
                    and by_id[alias]['source_sha256']==row['source_sha256'],'Source alias differs')
        else:require(row['variant']=='compact' and alias is None,'Unknown source form')
        observed=reconciliation['profiles'][row['key']]
        for field in ('key','id','language','benchmark','source','source_sha256','binary_sha256'):
            same(observed[field],row[field],'Reconciled source/runtime differs: '+field)
        if observed['full_workload_qualified'] is not True:
            require(row['key'] in reconciliation['failed_profiles'],'Unexplained failed profile')
            excluded.append(dict(key=row['key'],reason='failed-full-workload',failed_attempt=observed['failed_attempt'],
                                 failed_cohort=observed['failed_cohort']))
            continue
        require(row['key'] not in reconciliation['failed_profiles'] and len(observed['samples_seconds'])==3,
                'Failed or incomplete profile offered for publication')
        eligible.append(dict(key=row['key'],id=row['id'],benchmark=row['benchmark'],variant=row['variant'],
            source_alias_of=alias,optimization_claim=row['optimization_claim'],source=row['source'],
            source_sha256=row['source_sha256'],source_bundle=row['source_bundle'],binary=row['binary'],
            binary_sha256=row['binary_sha256'],qlf_artifact_pins=qlf,command=row['command'],cwd=row['cwd'],
            runtime_environment=row['runtime_environment'],canonical_loc=row['canonical_loc'],physical_loc=row['physical_loc'],
            execution_mode='swi-native-bytecode-vm',maximum_compute_workers=1,declared_vendor_libraries=vendor,
            preparation_foreign_libraries=loaded['foreign_libraries'],runtime_flags_observed_during_preparation=loaded['runtime'],
            timing=observed,chart_admission=False))
    return dict(schema=SCHEMA,status='recorded-runtime-metadata-reviewed-awaiting-file-verification',
        runtime_publication_metadata_qualified=False,file_integrity_verified=False,chart_admission=False,
        profiles=eligible,excluded_profiles=excluded,source_forms_reviewed=20,
        runtime_version='SWI-Prolog 10.0.2',native_architecture='arm64',application_execution='bytecode/QLF',
        memory_policy='SWI term, atom and clause garbage collection; retained preparation observed gc=true and bounded=false.',
        stack_limit_bytes=8589934592,maximum_compute_workers=1,probe_runtime_flags=feature['runtime'],
        probe_native_image_pins=images['image_pins'],os_install_names_not_file_hashed=sorted(os_images),
        pcre_version=config['pcre_version'],regex_policy='SWI library(pcre) calls bundled PCRE2 10.40; authored calls request jit(false).',
        arbitrary_integer_policy='Unbounded integers; bundled GMP image retained in the native runtime dependency closure.',
        timing_boundary=plan['timing_policy'],runtime_and_qlf_loading_inside_timer=True,compilation_outside_timer=True,
        new_native_probes=0,compiler_invocations=0,benchmark_samples=0,cohort_policy=reconciliation['cohort_policy'],
        original_source_outcome=previous['sealed_source_outcome'],linear_qualification=plan['linear_qualification'],
        limitations=['Loaded-image and GC observations are from retained probe/preparation commands, not timed processes.',
            'QLF contains application bytecode; native application AOT compilation is not claimed.',
            'Compact/optimized labels are explicit source aliases; distinct source algorithms are not claimed.',
            'Nine original regex samples, 31 preserved continuation samples and up to 50 new samples retain each actual cohort and matched control.',
            'The cancelled original reverse-complement attempt supplies no timing or timeout result.',
            'Source-linear traversal is established separately from any empirical runtime scaling claim.'],
        remaining_gate='Explicit dataset import and website validation; failed profiles remain excluded.')


def checked(path,digest):
    raw=Path(path).read_bytes()
    require(p.digest(digest) and hashlib.sha256(raw).hexdigest()==digest,'Pinned bytes differ: '+str(path))
    return raw


def write_new(path,value):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();identity=None
    try:
        with path.open('xb') as stream:
            stat=os.fstat(stream.fileno());identity=(stat.st_dev,stat.st_ino)
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    except BaseException:
        if identity is not None and path.is_file() and not path.is_symlink():
            stat=path.stat()
            if (stat.st_dev,stat.st_ino)==identity:
                current=path.read_bytes()
                if len(current)<=len(raw) and raw.startswith(current):path.unlink()
        raise
    return hashlib.sha256(raw).hexdigest()


def remove_owned(path,expected_sha):
    if expected_sha is not None and path.is_file():
        require(hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,'Owned output changed; preserving altered bytes')
        path.unlink()


@contextmanager
def review_context(reconciliation_path,expected_sha,*,on_exit_failure=None,final_consumer_check=None):
    path=Path(reconciliation_path).resolve()
    require(path.is_relative_to(n.PACKET) and not path.is_relative_to(n.PACKET/'run-v1')
            and p.digest(expected_sha),'Wrong additive reconciliation location')
    files=r.Files()
    def consumer_closure():
        # Run again after the independent reconciler's final full-file pass,
        # while every lease is still held. Publication-only pins are not in it.
        for name,digest in files.verified.copy().items():files.verify(name,digest)
        if final_consumer_check is not None:final_consumer_check()
    with n.review_context(on_exit_failure=on_exit_failure,final_consumer_check=consumer_closure) as review:
        saved=files.document(str(path),expected_sha)
        same(saved,review,'Saved three-cohort reconciliation did not independently reproduce')
        for name,digest in ((RECONCILER,RECONCILER_SHA),(HELPER,HELPER_SHA),
                (Path(__file__).resolve(),hashlib.sha256(Path(__file__).read_bytes()).hexdigest())):
            files.verify(str(name),digest)
        plan=files.document(str(n.PLAN),n.PLAN_SHA)
        prior=files.document(str(n.PRIOR/'plan-v1.json'),n.PRIOR_PLAN_SHA)
        previous=files.document(str(n.l.OLD_REFS['plan'][0]),n.l.OLD_REFS['plan'][1])
        def saved_document(name):
            return files.document(str(name),review['verified_file_pins'][str(name)])
        reader=f.m.Evidence(dict(previous,pins=plan['pins']),saved_document(previous['storage_manifest']['path']))
        outcome=reader.document(previous['sealed_source_outcome']['path'],r.OUTCOME_SHA)
        result=inspect(plan,prior,previous,review,outcome,reader.document,reader.raw)
        for name,digest in reader.read_pins.items():files.verify(name,digest)
        verified=n.merge(review['verified_file_pins'],files.verified)
        def recheck():
            for name,digest in files.verified.copy().items():files.verify(name,digest)
        result.update(status='qualified-recorded-runtime-metadata',runtime_publication_metadata_qualified=True,
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=review['plan'],reconciliation=dict(path=str(path),sha256=expected_sha),
            verified_file_pins=verified,source_outcome=previous['sealed_source_outcome'],
            new_full_native_processes=review['new_full_native_processes'],reused_qualified_samples=40,
            original_regex_samples=9,retained_linear_samples=31,excluded_original_attempt=10,
            cohorts=copy.deepcopy(review['cohorts']),prior_producer_statuses=copy.deepcopy(review['prior_producer_statuses']))
        with f._yield_verified(result,recheck,on_exit_failure,final_consumer_check) as qualified:
            yield qualified


def save_metadata(args,target):
    owned_sha=None
    def cleanup():remove_owned(target,owned_sha)
    try:
        with review_context(args.reconciliation,args.reconciliation_sha256,on_exit_failure=cleanup) as result:
            owned_sha=write_new(target,result)
        return result,owned_sha
    except BaseException:
        cleanup();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconciliation',type=Path,required=True)
    parser.add_argument('--reconciliation-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B')
    output=args.output.resolve()
    require(output.is_relative_to(n.PACKET) and not output.is_relative_to(n.PACKET/'run-v1')
            and not output.exists() and output.parent.is_dir(),'Fresh additive metadata output required')
    result,digest=save_metadata(args,output)
    print(json.dumps(dict(status=result['status'],sha256=digest,source_forms_reviewed=result['source_forms_reviewed'])),flush=True)


if __name__=='__main__':main()
