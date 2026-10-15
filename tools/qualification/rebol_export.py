"""Export an independently reconciled Rebol full90 private candidate.

No module import performs evidence intake. No producer, runtime or compiler is
executed. Actual closed reconciliation and separately reviewed publication
metadata are required; raw failures and separately timed source aliases remain
explicit. This module has no catalog apply mode.
"""
import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import statistics
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/rebol/full90-v1'
RECONCILER=Path(__file__).with_name('rebol_reconcile.py')
PYTHON=Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
FILES=(Path(__file__).resolve(),Path(__file__).with_name('test_rebol_export.py'),PACKET/'EXPORT.md')
BENCHES=('regexredux','revcomp','pidigits','spectralnorm','mandelbrot','fasta',
         'knucleotide','binarytrees','nbody','fannkuchredux')
FORMS=('compact','optimized')
ROLES=('application','application-helper','application-launcher','general-library-helper')


def require(value,message):
    if not value:raise AssertionError(message)


def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def clone(value):return copy.deepcopy(value)


def ref(path,sha):
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts and type(sha) is str and re.fullmatch('[0-9a-f]{64}',sha),
            'Exact absolute evidence reference required')
    return dict(path=str(path),sha256=sha)


def read_bytes(path):
    path=Path(path);before=path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True)==path,'Physical regular metadata required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd)
        require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Metadata replaced before open')
        raw=stream.read(32*1024**2+1);require(len(raw)<=32*1024**2,'Metadata intake limit exceeded')
        after=path.lstat()
        require(stat.S_ISREG(after.st_mode) and (held.st_dev,held.st_ino)==(after.st_dev,after.st_ino),
                'Metadata replaced during read')
    return raw


def checked(path,expected):
    raw=read_bytes(path);require(digest(raw)==expected,'Evidence bytes changed: '+str(path));return raw


def load_reconciler(expected):
    raw=checked(RECONCILER,expected)
    module=types.ModuleType('rebol_export_independent_reconciler');module.__file__=str(RECONCILER)
    exec(compile(raw,str(RECONCILER),'exec'),module.__dict__)
    require(module.ROOT==ROOT,'Independent evidence root changed')
    return module


def source_intake(binding):
    review=json.loads(checked(binding['path'],binding['sha256']))
    require(review['schema']=='rebol-export-source-review-v1'
        and review['status']=='independent-source-review-complete-actual-export-pending'
        and review['independent_review'] is True and review['native_execution'] is review['chart_admission'] is False
        and set(review['files'])=={str(path.relative_to(ROOT)) for path in FILES}
        and set(review['dependencies'])=={str(RECONCILER.relative_to(ROOT))},'Actual export source review required')
    pins={str(ROOT/name):sha for name,sha in {**review['files'],**review['dependencies']}.items()}
    for path,sha in pins.items():ref(path,sha);checked(path,sha)
    pins[binding['path']]=binding['sha256']
    return load_reconciler(pins[str(RECONCILER)]),pins


def positive(value):return type(value) in (int,float) and math.isfinite(value) and value>0
def close(left,right):return type(right) in (int,float) and math.isfinite(right) and math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-12)


def statistics_check(measured):
    success=measured['full_workload_qualified'];require(type(success) is bool,'Nonboolean qualification')
    samples=measured['samples_seconds']
    require(type(samples) is list and len(samples)<=3 and all(positive(value) for value in samples),'Invalid actual samples')
    if success:
        require(len(samples)==3 and measured['failed_attempt'] is None
            and measured['median_seconds']==statistics.median(samples)
            and close(statistics.stdev(samples),measured['sample_stdev_seconds']),'Three-sample statistics differ')
    else:
        require(len(samples)<3 and type(measured['failed_attempt']) is int and measured['failed_attempt']>0
            and measured['median_seconds'] is measured['sample_stdev_seconds'] is measured['time_x_mech'] is None,
            'Failed profile cannot acquire a median or ratio')
    return success


def sample_records(measured,row,plan,review,read_raw):
    result,good=[],[]
    for number in measured['attempts']:
        require(type(number) is int and number>0,'Invalid attempt identity')
        stem=f'{number:03d}-{row["id"]}'
        raw_path=plan['output']+'/attempts/'+stem+'.json'
        supervised=plan['output']+'/attempts/'+stem+'.supervisor.json'
        outer=plan['output']+'/outer-supervisor/'+stem+'.json'
        bindings=[ref(path,review['verified_file_pins'][path]) for path in (raw_path,supervised,outer)]
        item=json.loads(read_raw(supervised,bindings[1]['sha256']))
        # The independent reader already checks all three exact receipts. Read
        # every referenced byte here too so the candidate cannot name stale data.
        read_raw(raw_path,bindings[0]['sha256']);read_raw(outer,bindings[2]['sha256'])
        qualified=number!=measured['failed_attempt']
        require(item['attempt']==number and item['key']==row['key'] and item['id']==row['id']
            and item['benchmark']==row['benchmark'] and type(item['qualified']) is bool
            and item['qualified']==qualified,'Sample belongs to another row or disposition')
        if qualified:good.append(item['seconds'])
        result.append(dict(attempt=number,round=item['round'],qualified=qualified,seconds=item.get('seconds'),
            started_at=item['started_at'],finished_at=item['finished_at'],
            stdout_bytes=item['stdout_bytes'] if qualified else item.get('stdout_bytes'),
            stdout_sha256=item['stdout_sha256'] if qualified else item.get('stdout_sha256'),
            validation=item.get('validation'),error=item.get('error'),error_type=item.get('error_type'),
            raw_evidence=bindings[0],supervisor_evidence=bindings[1],outer_supervisor_evidence=bindings[2]))
    require(good==measured['samples_seconds'] and len({row['attempt'] for row in result})==len(result),
            'Sample values or unique ownership differ')
    require([row['attempt'] for row in result if not row['qualified']]==
            ([] if measured['full_workload_qualified'] else [measured['failed_attempt']]),'Failure receipt missing')
    return result


def validate_metadata(metadata,admission,read_raw):
    require(metadata['schema']=='rebol-publication-runtime-metadata-v1'
        and metadata['status']=='independently-reviewed-runtime-and-publication-metadata'
        and metadata['independent_review'] is True and metadata['key']=='rebol3'
        and metadata['runtime_publication_metadata_qualified'] is True and metadata['chart_admission'] is False,
        'Actual independent publication metadata required')
    require(metadata['qualification_manifest']==admission['manifest']
        and metadata['qualified_runtime']==admission['runtime']
        and metadata['extension_image']==admission['extension_image'], 'Runtime/source association differs')
    for key in ('runtime_source_equivalence_proven','observed_in_each_timed_process',
                'actual_loaded_image_inventory_observed','runtime_gc_configuration_observed','gc_numeric_defaults_claimed'):
        require(metadata[key] is False,'Runtime evidence scope was promoted: '+key)
    require(metadata['runtime_evidence_scope']==admission['scope']['limitations'], 'Runtime/work limits differ')
    require(metadata['execution']==['interpreted'] and metadata['typing']=='dynamic'
        and type(metadata['runtime']) is str and metadata['runtime']
        and all(key in metadata for key in ('label','family','platform','style','memory','note','sources')),
        'Reviewed language metadata incomplete')
    require(type(metadata['evidence']) is dict and metadata['evidence'],'Classification/version evidence missing')
    for binding in metadata['evidence'].values():
        ref(binding['path'],binding['sha256']);read_raw(binding['path'],binding['sha256'])


def validate_prerequisites(r,plan,review,metadata,read_raw):
    slots,profiles=r.schedule(plan)
    require(len(slots)==90 and len(profiles)==30 and set(review['profiles'])==set(profiles), 'Full90 inventory differs')
    require(review['schema']=='rebol-independent-full90-reconciliation-v1'
        and review['status']=='full90-reconciled-awaiting-runtime-and-publication-review'
        and review['file_integrity_verified'] is review['common_mutex_held'] is True
        and type(review['common_mutex_inode']) is int and review['common_mutex_inode']==79859134
        and review['runtime_publication_metadata_qualified'] is False and review['chart_admission'] is False,
        'Held independent full90 reconciliation required')
    require(review['verified_file_pins'].get(review['plan']['path'])==review['plan']['sha256']
        and all(review['verified_file_pins'].get(path)==sha for path,sha in plan['pins'].items()),
        'Reconciliation omitted prerequisite pins')
    admission=review['qualification']
    require(admission==plan['qualification'] and admission['manifest']==plan['qualification_manifest'],
            'Reproduced qualification differs')
    validate_metadata(metadata,admission,read_raw)
    bases={row['benchmark']:row for row in admission['bases']}
    require(len(admission['bases'])==len(bases)==10 and set(bases)==set(BENCHES),'Ten exact counted base bundles required')
    for bench in BENCHES:
        base=bases[bench]
        for form in FORMS:
            row=profiles[f'rebol-{bench}-{form}']
            require(row['physical_inputs']==base['physical_inputs'] and row['original_profile_id']==base['original_profile_id']
                and row['source']==base['main']['path'] and row['source_sha256']==base['main']['sha256']
                and row['binary']==admission['runtime']['binary']['path']
                and row['binary_sha256']==admission['runtime']['binary']['sha256']
                and row['canonical_loc']==base['canonical_loc'] and row['physical_loc']==base['physical_loc']
                and row['formatted_loc'] is base['formatted_loc'] is None
                and row['source_work_qualified'] is row['canonical_loc_qualified'] is True
                and row['formatted_loc_qualified'] is False and 'timing_alias_of' not in row
                and row['alias_policy']==base['alias_policy'] and row['separate_fresh_samples_required'] is True
                and row['optimization_claim'] is False,'Counted separately timed source identity differs')
    return profiles,bases


def build_candidate(r,plan,review,metadata,read_raw):
    profiles,bases=validate_prerequisites(r,plan,review,metadata,read_raw)
    inventory,controls,files,endpoints,excluded,physical={},{},{},{},[],set()
    for bench in BENCHES:
        control_key=bench+':rebol-full-study:mech-control'
        control_row,measured_control=profiles[control_key],review['profiles'][control_key]
        for field in ('id','language','benchmark','source','source_sha256','binary_sha256'):
            require(measured_control[field]==control_row[field],'Measured control identity differs: '+field)
        control_ok=statistics_check(measured_control)
        control=clone(measured_control)
        control.update(source_evidence=ref(control_row['source'],control_row['source_sha256']),
                       sample_execution_metadata=sample_records(measured_control,control_row,plan,review,read_raw))
        controls[bench]=control;eligible_rows=[]
        for form in FORMS:
            identity=f'rebol-{bench}-{form}';row=profiles[identity];measured=review['profiles'][identity]
            for field in ('id','language','benchmark','source','source_sha256','binary_sha256'):
                require(measured[field]==row[field],'Measured identity differs: '+field)
            successful=statistics_check(measured);eligible=successful and control_ok
            require(measured['matched_control_qualified'] is control_ok and measured['endpoint_eligible'] is eligible,
                    'Independent comparative admission differs')
            ratio=measured['median_seconds']/measured_control['median_seconds'] if eligible else None
            require(measured['time_x_mech']==ratio,'Matched-control ratio differs')
            file_ids,roles=[],{}
            for source in row['physical_inputs']:
                path,sha=source['path'],source['sha256'];physical.add(path)
                require(plan['pins'].get(path)==sha and source['counted'] is True
                    and source['role'] in ROLES and all(type(source[key]) is int and source[key]>0
                    for key in ('canonical_loc','physical_loc')),'Counted source pin or owner differs')
                raw=read_raw(path,sha);require(digest(raw)==sha,'Source content digest differs')
                public=str(Path(path).relative_to(ROOT));code=raw.decode('utf-8')
                if sha not in files:
                    files[sha]=dict(sha256=sha,name=Path(path).name,code=code,archive_path=public,source_paths=[])
                require(files[sha]['code']==code and sha not in roles,'Hash collision or duplicate role content')
                if public not in files[sha]['source_paths']:files[sha]['source_paths'].append(public)
                file_ids.append(sha)
                roles[sha]=dict(role=source['role'],source_path=public,original_source=ref(path,sha),
                    retained_source=ref(path,sha),normalized_loc=source['canonical_loc'],physical_loc=source['physical_loc'],
                    formatted_loc=None,canonical_count_evidence=clone(review['qualification']['references']['count_review']))
            require(len(file_ids)==(5 if bench in ('pidigits','regexredux') else 4)
                and set(role['role'] for role in roles.values())==set(ROLES)
                and row['canonical_loc']==sum(value['normalized_loc'] for value in roles.values())
                and row['physical_loc']==sum(value['physical_loc'] for value in roles.values()),'Full authored bundle differs')
            key=bench+':'+identity
            entry=dict(key=key,receipt_key=identity,id=identity,benchmark=bench,variant=form,language='rebol3',
                loc=row['canonical_loc'],canonical_loc=row['canonical_loc'],physical_loc=row['physical_loc'],formatted_loc=None,
                loc_metric='statement-normalized',files=file_ids,file_roles=roles,seconds=measured['median_seconds'],
                samples=clone(measured['samples_seconds']),timing_sd=measured['sample_stdev_seconds'],
                measurement_status='measured' if successful else 'failed-full-workload',source_work_qualified=True,
                canonical_loc_qualified=True,formatted_loc_qualified=False,full_workload_qualified=successful,
                matched_control_qualified=control_ok,eligible_for_publication_review=eligible,chart_admission=False,
                source_alias_group=row['original_profile_id'],source_alias_of=None if form=='compact' else f'rebol-{bench}-compact',
                source_alias_note='Equivalent authored bundle; independently timed forms; no distinct optimization claim.',
                distinct_optimization_claimed=False,timing_alias_of=None,separate_fresh_samples_required=True,
                command=clone(row['command']),runtime_environment=clone(row['runtime_environment']),cwd=row['cwd'],
                source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],execution_mode='interpreted',
                extension_image=clone(review['qualification']['extension_image']),corrections=clone(row['corrections']),
                runtime_source_equivalence_proven=False,sample_execution_metadata=sample_records(measured,row,plan,review,read_raw),
                matched_mech_control_key=control_key,time_ratio_to_matched_mech=ratio,failed_attempt=measured['failed_attempt'],
                evidence=clone(review['source_evidence']),exclusion_reason=None if eligible else
                ('subject-full-workload-failed' if not successful else 'matched-Mech-control-failed'))
            inventory[key]=entry
            if eligible:eligible_rows.append(entry)
            else:excluded.append(identity)
        fast=min(eligible_rows,key=lambda row:(row['seconds'],row['canonical_loc'],row['key'])) if eligible_rows else None
        small=min(eligible_rows,key=lambda row:(row['canonical_loc'],row['seconds'],row['key'])) if eligible_rows else None
        endpoints[bench]=dict(fast=fast['key'] if fast else None,small=small['key'] if small else None,
            programs=list(dict.fromkeys([small['key'],fast['key']])) if fast else [],chart_admission=False)
    require(len(inventory)==20 and len(controls)==len(endpoints)==10 and len(physical)==15,'Incomplete full90 source inventory')
    for source in files.values():source['source_paths'].sort()
    return dict(schema='rebol-full90-publication-candidate-v1',status='validated-evidence-candidate-awaiting-publication-review',
        chart_admission=False,dataset_files_changed=False,native_processes_started=0,language_metadata=clone(metadata),
        program_inventory=inventory,files=files,matched_mech_controls=controls,endpoint_proposals=endpoints,
        excluded_profiles=excluded,plan=clone(review['plan']),report=clone(review['report']),terminal=clone(review['terminal']),
        qualification_manifest=clone(plan['qualification_manifest']),qualified_runtime=clone(review['qualification']['runtime']),
        actual_full_native_processes=review['actual_full_native_processes'],qualified_samples=review['qualified_samples'],
        planned_rebol_samples=60,planned_matched_mech_samples=30,distinct_subject_bundles=10,
        counted_physical_sources=15,source_forms=20,timing_aliases=0,formatted_loc_qualified=False,
        skipped_slots=clone(review['skipped_slots']),failed_profiles=clone(review['failed_profiles']),
        complete_stdout_retained=False,full_output_evidence=review['full_output_evidence'],resource_evidence=review['resource_evidence'],
        publication_requirements=['candidate review','dataset/catalog/site validation'])


def verify_owned(path,owned):
    if not owned:return
    before=Path(path).lstat()
    require(stat.S_ISREG(before.st_mode) and (before.st_dev,before.st_ino)==owned['identity']
        and read_bytes(path)==owned['raw'],'Owned candidate changed')
    after=Path(path).lstat()
    require((after.st_dev,after.st_ino)==owned['identity'],'Owned candidate replaced during check')


def remove_owned(path,owned):
    if not owned or not os.path.lexists(path):return
    identity=Path(path).lstat()
    require(stat.S_ISREG(identity.st_mode) and (identity.st_dev,identity.st_ino)==owned['identity'],
            'Candidate replacement preserved')
    raw=read_bytes(path)
    require(raw==owned['raw'] if owned.get('complete') else len(raw)<=len(owned['raw']) and owned['raw'].startswith(raw),
            'Changed candidate bytes preserved')
    again=Path(path).lstat()
    require((again.st_dev,again.st_ino)==owned['identity'],'Candidate replacement preserved before cleanup')
    Path(path).unlink();owned.clear()


@contextmanager
def deferred_stops():
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
    try:yield
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)


@contextmanager
def stop_handlers():
    previous={number:signal.getsignal(number) for number in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    def stop(number,frame):raise InterruptedError('Export stopped by signal '+str(number))
    try:
        with deferred_stops():
            for number in previous:signal.signal(number,stop)
        yield
    finally:
        with deferred_stops():
            for number,handler in previous.items():signal.signal(number,handler)


def write_new(path,value,owned):
    raw=encoded(value)
    # Deliver a stop only after the exclusive file has a persistent ownership
    # record. The caller's failure guard can then remove its unchanged bytes.
    with deferred_stops():
        with Path(path).open('xb') as stream:
            st=os.fstat(stream.fileno())
            owned.update(identity=(st.st_dev,st.st_ino),raw=raw,complete=False)
            stream.write(raw);stream.flush();os.fsync(stream.fileno());owned['complete']=True
    return digest(raw)


@contextmanager
def preserve_failure_cleanup(cleanup):
    try:yield
    except BaseException as error:
        try:cleanup()
        except BaseException as cleanup_error:
            raise BaseExceptionGroup('Candidate failed; cleanup preserved changed evidence',[error,cleanup_error])
        raise


def export_context(args, *, final_consumer_check=None, on_exit_failure=None):
    """Return the actual reader context; expose this narrow call to importers."""
    source_ref=ref(args.source_review,args.source_review_sha256)
    r,pins=source_intake(source_ref)
    return r,pins,r.review_context(args.plan,args.plan_sha256,args.durable_directory,pins[str(RECONCILER)],
        final_consumer_check=final_consumer_check,on_exit_failure=on_exit_failure)


def save_candidate(args):
    target=Path(args.output).absolute();plan_path=Path(args.plan).absolute()
    saved_plan=json.loads(checked(plan_path,args.plan_sha256))
    require(target.parent.resolve(strict=True)==target.parent and not os.path.lexists(target)
        and not target.is_relative_to(Path(saved_plan['output']))
        and not any(target.is_relative_to(ROOT/name) for name in ('data','site')),
        'Fresh private candidate outside timing and publication paths required')
    own_source=ref(Path(args.source_review).absolute(),args.source_review_sha256)
    reconciliation=ref(Path(args.reconciliation).absolute(),args.reconciliation_sha256)
    metadata_ref=ref(Path(args.metadata).absolute(),args.metadata_sha256)
    metadata=json.loads(checked(metadata_ref['path'],metadata_ref['sha256']))
    owned={};extra={reconciliation['path']:reconciliation['sha256'],metadata_ref['path']:metadata_ref['sha256']}
    for binding in metadata['evidence'].values():
        ref(binding['path'],binding['sha256'])
        require(binding['path'] not in extra or extra[binding['path']]==binding['sha256'],'Conflicting metadata evidence')
        extra[binding['path']]=binding['sha256']
    def check():
        for path,sha in extra.items():checked(path,sha)
        verify_owned(target,owned)
    def cleanup():remove_owned(target,owned)
    r,source_pins,context=export_context(args,final_consumer_check=check,on_exit_failure=cleanup)
    for path,sha in source_pins.items():
        require(path not in extra or extra[path]==sha,'Conflicting source review pin');extra[path]=sha
    with preserve_failure_cleanup(cleanup):
        with context as review:
            check()
            require(json.loads(checked(reconciliation['path'],reconciliation['sha256']))==review,
                    'Saved independent reconciliation differs from actual replay')
            require(checked(plan_path,args.plan_sha256)==encoded(saved_plan),'Plan must retain its exact serialized bytes')
            def read_raw(path,sha):
                require(review['verified_file_pins'].get(path)==sha or extra.get(path)==sha,
                        'Export reads only reviewed evidence')
                return checked(path,sha)
            result=build_candidate(r,saved_plan,review,metadata,read_raw)
            result.update(reconciliation=reconciliation,metadata_review=metadata_ref,export_source_review=own_source,
                export_controller=ref(Path(__file__).resolve(),source_pins[str(Path(__file__).resolve())]))
            write_new(target,result,owned)
            check()
    return result,digest(owned['raw'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','reconciliation','metadata','source-review'):
        parser.add_argument('--'+name,type=Path,required=True)
        parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--durable-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
        and Path(sys.executable).resolve()==PYTHON.resolve(),'Use retained Python -I -S -B')
    with stop_handlers():result,sha=save_candidate(args)
    print(json.dumps(dict(output=str(args.output.absolute()),sha256=sha,inventory_forms=20,
        excluded_profiles=result['excluded_profiles'],dataset_files_changed=False,chart_admission=False)),flush=True)


if __name__=='__main__':main()
