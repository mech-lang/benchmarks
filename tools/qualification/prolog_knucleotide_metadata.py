"""Review retained Prolog runtime metadata across four actual timing cohorts.

No producer, native runtime or compiler executes. Six existing leases remain
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
import signal
import stat

ROOT=Path(__file__).resolve().parents[2]
RECONCILER=Path(__file__).with_name('prolog_knucleotide_reconcile.py')
RECONCILER_SHA='9c561518ad2b8c479e2e0c4bea697cb05fb61cba23c4f317a05e4f2386b238de'
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
SCHEMA='prolog-four-cohort-recorded-runtime-metadata-v1'
runtime_context,original_profile,linear_profile=f.runtime_context,f.original_profile,f.linear_profile


def knucleotide_profile(plan,row,config,images,read,read_raw):
    """Bind the two qualified corrected inputs to retained compiler observations."""
    qualification=plan['knucleotide_qualification']
    same(plan['qualification'],dict(path=str(n.QUALIFICATION),sha256=n.QUALIFICATION_SHA),
         'Wrong independently qualified knucleotide packet')
    require(qualification['schema']=='prolog-knucleotide-linear-qualified-v1'
            and all(qualification[k] is True for k in ('bounded_outputs_qualified','compiled_inputs_qualified','source_work_qualified','canonical_LOC_admitted'))
            and qualification['full_timings_qualified'] is qualification['chart_admission'] is False,
            'Corrected knucleotide qualification is incomplete')
    matching=[value for value in qualification['profiles'] if value['id']==row['id']]
    require(len(matching)==1,'Missing corrected profile');same(matching[0],row,'Corrected profile differs')
    counts_ref=qualification['evidence']['source_counts']
    same({k:row['compiler_bound_input_inventory'][k] for k in ('path','sha256')},counts_ref,
         'Compiler input/count review differs')
    owner=read(counts_ref['path'],counts_ref['sha256'])
    require(owner['schema']=='prolog-knucleotide-linear-actual-source-owner-review-v1'
            and owner['status']=='qualified-exact-authored-compiler-inputs'
            and owner['compiled_inputs_qualified'] is owner['canonical_LOC_admitted'] is True
            and owner['full_timings_qualified'] is owner['chart_admission'] is False,
            'Corrected compiler/count disposition differs')
    variants=[v for v in owner['source_counts']['variants'] if v['variant']==row['variant']]
    require(len(variants)==1,'Missing corrected count variant');variant=variants[0]
    require(variant['canonical_loc']==row['canonical_loc']==238 and variant['physical_loc']==row['physical_loc']==154
            and variant['formatted_loc'] is row.get('formatted_loc') is None,'Corrected count totals differ')
    fields=('origin','path','sha256','normalized_loc','physical_loc')
    same([{k:v[k] for k in fields} for v in variant['source_bundle']],row['source_bundle'],'Corrected counted bundle differs')
    same({k:variant['canonical_source_projection'][k] for k in ('path','sha256')},row['canonical_source_projection'],
         'Corrected projection identity differs')
    compiled={v['compiler_input']['path']:v for v in owner['compilation']['files']}
    qlf={}
    for source in row['source_bundle']:
        item=compiled[source['path']]
        require(item['compiler_input']['sha256']==item['authored']['sha256']==source['sha256']
                and item['authored']['path']==source['origin'],'Corrected compiler source identity differs')
        artifact=item['compiled_artifact'];path=str(Path(source['path']).with_suffix('.qlf'))
        require(artifact['path']==path and plan['pins'].get(path)==artifact['sha256'],'Corrected QLF unbound')
        qlf[path]=artifact['sha256']
        if source['path']==row['measured_source']:same(artifact,row['compiled_artifact'],'Corrected primary QLF differs')
    command=[config['binary'],*f.PREFIX,'-l',str(Path(row['cwd'])/'support/clbg_io.qlf'),
        '-l',str(Path(row['cwd'])/'support/clbg_records.qlf'),'-s',row['compiled_artifact']['path'],
        '-g','clbg_io:run(clbg_knucleotide:main)']
    same(row['command'],command,'Corrected runtime loading differs')
    ref=variant['loaded_inputs'];loaded=read(ref['path'],ref['sha256'])
    require(loaded['mode']=='inspect' and loaded['target']==row['compiled_artifact']['path'],
            'Corrected preparation inspected another main')
    f.runtime_flags(loaded['runtime'],config['home'])
    require(all(s['path'] in loaded['loaded_sources'] for s in row['source_bundle'])
            and all(path in plan['pins'] for path in loaded['loaded_sources']),'Corrected loaded source unbound')
    for library in loaded['foreign_libraries']:
        require(library['resolved_path'] in images['image_pins'],'Corrected preparation native image unbound')
    work_ref=qualification['evidence']['required_work'];work=read(work_ref['path'],work_ref['sha256'])
    require(work['status']=='qualified-required-source-work' and work['source_work_qualified'] is True
            and work['full_timings_qualified'] is work['chart_admission'] is False,'Corrected source work unqualified')
    selected=[v for v in work['profiles'] if v['profile']==row['id']]
    require(len(selected)==1 and selected[0]['required_source_work_qualified'] is True
            and selected[0]['main_atom_string_calls']==1,'One-time text conversion work differs')
    for label,binding in (('compiled_qlf',row['compiled_artifact']),('loaded_inputs',ref)):
        same(str(ROOT/selected[0][label]['path']),binding['path'],'Work evidence path differs')
        same(selected[0][label]['sha256'],binding['sha256'],'Work evidence bytes differ')
    return qlf,[],loaded


def inspect(plan, stopped, prior, previous, reconciliation, outcome, read, read_raw):
    _,all_profiles,_=n.schedule(plan,stopped,prior,previous)
    require(reconciliation['schema']==l.SCHEMA
            and reconciliation['status']=='full36-plus-retained54-reconciled-awaiting-runtime-and-publication-review'
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
        elif row['benchmark']=='knucleotide':
            qlf,vendor,loaded=knucleotide_profile(plan,row,config,images,read,read_raw)
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
        original_source_outcome=previous['sealed_source_outcome'],linear_qualification=plan['linear_qualification'],knucleotide_qualification=plan['qualification'],
        limitations=['Loaded-image and GC observations are from retained probe/preparation commands, not timed processes.',
            'QLF contains application bytecode; native application AOT compilation is not claimed.',
            'Compact/optimized labels are explicit source aliases; distinct source algorithms are not claimed.',
            'Nine original regex, 31 linear-continuation, 14 preserved stopped-prefix and up to 36 new observations retain their actual cohorts and matched controls.',
            'Cancelled reverse-complement and pre-correction knucleotide attempts supply no timing or timeout result.',
            'Source-linear traversal is established separately from any empirical runtime scaling claim.'],
        remaining_gate='Explicit dataset import and website validation; failed profiles remain excluded.')


def read_regular(path):
    """Never block on a substituted FIFO or follow a replaced file symlink."""
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts,'Absolute physical input required')
    for parent in reversed(path.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode),'Nonphysical input ancestor')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Nonregular input')
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(stream.fileno())
        require(stat.S_ISREG(held.st_mode) and (held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),
                'Input replaced before read')
        raw=stream.read()
    after=path.lstat()
    require(stat.S_ISREG(after.st_mode) and (after.st_dev,after.st_ino)==(before.st_dev,before.st_ino),
            'Input replaced during read')
    return raw


def checked(path,digest):
    raw=read_regular(path)
    require(p.digest(digest) and hashlib.sha256(raw).hexdigest()==digest,'Pinned bytes differ: '+str(path))
    return raw


@contextmanager
def atomic():
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
    try:yield
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)


class OwnedResult:
    """Track exclusive output before writing; preserve any later external edit."""
    def __init__(self,path):
        self.path=Path(path);self.identity=None;self.raw=None;self.complete=False
    def write(self,value):
        self.raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        with atomic():
            with self.path.open('xb') as stream:
                info=os.fstat(stream.fileno());self.identity=(info.st_dev,info.st_ino)
                stream.write(self.raw);stream.flush();os.fsync(stream.fileno());self.complete=True
        return hashlib.sha256(self.raw).hexdigest()
    def verify(self):
        if self.identity is None:return
        info=self.path.lstat()
        require(self.complete and stat.S_ISREG(info.st_mode) and (info.st_dev,info.st_ino)==self.identity
                and read_regular(self.path)==self.raw,'Owned result changed')
        after=self.path.lstat();require((after.st_dev,after.st_ino)==self.identity,'Owned result replaced')
    def remove(self):
        if self.identity is None:return
        with atomic():
            try:info=self.path.lstat()
            except FileNotFoundError:self.identity=None;return
            require(stat.S_ISREG(info.st_mode) and (info.st_dev,info.st_ino)==self.identity,
                    'Owned result replaced; preserving changed file')
            current=read_regular(self.path)
            require(current==self.raw if self.complete else self.raw.startswith(current),
                    'Owned result changed; preserving altered bytes')
            self.path.unlink();self.identity=None


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
        same(saved,review,'Saved four-cohort reconciliation did not independently reproduce')
        for name,digest in ((RECONCILER,RECONCILER_SHA),(HELPER,HELPER_SHA),
                (Path(__file__).resolve(),hashlib.sha256(Path(__file__).read_bytes()).hexdigest())):
            files.verify(str(name),digest)
        plan=files.document(str(n.PLAN),n.PLAN_SHA)
        stopped=files.document(str(n.PREVIOUS_PLAN),n.PREVIOUS_PLAN_SHA)
        prior=files.document(str(n.PRIOR_PLAN),n.PRIOR_PLAN_SHA)
        previous=files.document(str(n.OLD_REFS['plan'][0]),n.OLD_REFS['plan'][1])
        def saved_document(name):
            return files.document(str(name),review['verified_file_pins'][str(name)])
        reader=f.m.Evidence(dict(previous,pins=plan['pins']),saved_document(previous['storage_manifest']['path']))
        outcome=reader.document(previous['sealed_source_outcome']['path'],r.OUTCOME_SHA)
        result=inspect(plan,stopped,prior,previous,review,outcome,reader.document,reader.raw)
        for name,digest in reader.read_pins.items():files.verify(name,digest)
        verified=n.merge(review['verified_file_pins'],files.verified)
        def recheck():
            for name,digest in files.verified.copy().items():files.verify(name,digest)
        result.update(status='qualified-recorded-runtime-metadata',runtime_publication_metadata_qualified=True,
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=review['plan'],reconciliation=dict(path=str(path),sha256=expected_sha),
            verified_file_pins=verified,source_outcome=previous['sealed_source_outcome'],
            new_full_native_processes=review['new_full_native_processes'],reused_qualified_samples=54,
            original_regex_samples=9,retained_linear_samples=31,retained_remaining_samples=14,
            excluded_original_attempt=10,excluded_remaining50_attempt=15,
            cohorts=copy.deepcopy(review['cohorts']),prior_producer_statuses=copy.deepcopy(review['prior_producer_statuses']))
        with f._yield_verified(result,recheck,on_exit_failure,final_consumer_check) as qualified:
            yield qualified


def save_metadata(args,target):
    owned=OwnedResult(target)
    try:
        with review_context(args.reconciliation,args.reconciliation_sha256,
                            on_exit_failure=owned.remove,final_consumer_check=owned.verify) as result:
            digest=owned.write(result)
        return result,digest
    except BaseException as error:
        try:owned.remove()
        except BaseException as cleanup:raise BaseExceptionGroup('Metadata write and cleanup failed',[error,cleanup])
        raise


def install_stop_handlers():
    def interrupted(signum,frame):raise KeyboardInterrupt('Publication review interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)


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
    install_stop_handlers()
    result,digest=save_metadata(args,output)
    print(json.dumps(dict(status=result['status'],sha256=digest,source_forms_reviewed=result['source_forms_reviewed'])),flush=True)


if __name__=='__main__':main()
