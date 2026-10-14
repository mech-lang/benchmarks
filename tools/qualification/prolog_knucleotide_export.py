"""Build a private Prolog publication candidate from independently closed evidence.

No native execution or publication. Actual file review requires the six existing
leases and reproduces the pinned metadata/reconciliation before reading sources.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
METADATA=Path(__file__).with_name('prolog_knucleotide_metadata.py')
METADATA_SHA='68b0c2fc2b9db77d270088991961eb458c890883aae41cd3cbcf33467a7b37aa'
raw=METADATA.read_bytes()
if hashlib.sha256(raw).hexdigest()!=METADATA_SHA:raise ValueError('Frozen metadata reviewer changed')
spec=importlib.util.spec_from_file_location('prolog_export_metadata',METADATA)
m=importlib.util.module_from_spec(spec);exec(compile(raw,str(METADATA),'exec'),m.__dict__)
l,r,p,require,same=m.l,m.r,m.p,m.require,m.same
SCHEMA='prolog-four-cohort-private-publication-candidate-v1'


def ref(path,digest):
    require(Path(path).is_absolute() and '..' not in Path(path).parts and p.digest(digest),'Malformed evidence reference')
    return dict(path=str(path),sha256=digest)


def retained_source(source,previous,pins):
    name,digest=source['path'],source['sha256']
    if Path(name).is_relative_to(ROOT):
        path=name
    else:
        relocation=previous['path_reconciliation'][name]
        require(relocation['historical_path']==name and relocation['storage_encoding']=='identity'
                and relocation['editorial_substitution'] is None
                and relocation['expected_sha256']==relocation['actual_content_sha256']==digest,
                'Authored source requires an exact identity relocation')
        path=relocation['resolved_path']
    require(Path(path).is_relative_to(ROOT) and '..' not in Path(path).parts
            and pins.get(path)==digest,'Unpinned public compiler input')
    return ref(path,digest)


def sample_records(measured,row,plan,review,read_raw,cohorts):
    records=[];good=[];identities=set()
    for origin in measured['sample_evidence']:
        cohort=origin['cohort'];number=origin['attempt']
        require(cohort in cohorts and p.integer(number) and number>0,'Unknown sample cohort or attempt')
        identity=(cohort,number)
        require(identity not in identities,'Repeated sample identity');identities.add(identity)
        directory={'original-full90':l.OLD/'results','linear-full81':l.PRIOR/'run-v1',
                   'linear-remaining50':l.PREVIOUS/'run-v1','knucleotide-remaining36':Path(plan['output'])}[cohort]
        expected=l.attempt_paths(directory,dict(attempt=number,id=row['id']))
        same([origin[k] for k in ('raw','supervisor','outer')],[str(path) for path in expected],
             'Sample receipt routed to another cohort or profile')
        require(cohort!='original-full90' or number<=9,'Cancelled original attempt cannot supply a sample')
        require(cohort!='linear-full81' or number<=31,'Unexecuted prior slot cannot supply a sample')
        require(cohort!='linear-remaining50' or number<=14,'Cancelled prior knucleotide attempt cannot supply a sample')
        paths={name:ref(origin[name],review['verified_file_pins'][origin[name]]) for name in ('raw','supervisor','outer')}
        raw=read_raw(paths['supervisor']['path'],paths['supervisor']['sha256'])
        require(hashlib.sha256(raw).hexdigest()==paths['supervisor']['sha256'],'Supervisor bytes changed')
        item=p.strict_json(raw)
        require(item['attempt']==number and item['key']==row['key'] and item['id']==row['id']
                and item['benchmark']==row['benchmark'] and item['round']==origin['round'],
                'Sample belongs to another profile or round')
        for field in ('qualified','seconds','stdout_bytes','stdout_sha256','validation'):
            same(item.get(field),origin[field],'Reconciled sample differs from supervisor: '+field)
        qualified=origin['qualified']
        require(type(qualified) is bool and (qualified or (cohort==measured['failed_cohort']
                and number==measured['failed_attempt'])),'Failed sample identity differs')
        if qualified:good.append(origin['seconds'])
        records.append(dict(attempt=number,attempt_cohort=cohort,round=origin['round'],qualified=qualified,
            seconds=origin['seconds'],started_at=item['started_at'],finished_at=item['finished_at'],
            stdout_bytes=origin['stdout_bytes'],stdout_sha256=origin['stdout_sha256'],validation=origin['validation'],
            error=item.get('error'),error_type=item.get('error_type'),raw_evidence=paths['raw'],
            supervisor_evidence=paths['supervisor'],outer_supervisor_evidence=paths['outer'],
            producer_plan=cohorts[cohort]['plan'],producer_report=cohorts[cohort]['report'],
            producer_terminal=cohorts[cohort]['terminal'],producer_status=cohorts[cohort]['status']))
    same(good,measured['samples_seconds'],'Sample values differ from independent reconciliation')
    same([x['attempt'] for x in records if x['attempt_cohort']=='knucleotide-remaining36'],measured['attempts'],
         'New cohort membership differs')
    same([dict(cohort=x['attempt_cohort'],attempt=x['attempt'],report=x['producer_report']['path'],
               report_sha256=x['producer_report']['sha256']) for x in records if x['attempt_cohort']!='knucleotide-remaining36'],
         measured['retained_attempts'],'Retained cohort membership differs')
    return records


def build_candidate(plan,stopped,prior,previous,review,metadata,read_raw):
    _,profiles,_=l.schedule(plan,stopped,prior,previous)
    require(review['schema']==l.SCHEMA and review['file_integrity_verified'] is True
            and review['status']=='full36-plus-retained54-reconciled-awaiting-runtime-and-publication-review'
            and review['chart_admission'] is review['runtime_publication_metadata_qualified'] is False,
            'Completed independent reconciliation required')
    require(metadata['schema']==m.SCHEMA and metadata['status']=='qualified-recorded-runtime-metadata'
            and metadata['file_integrity_verified'] is metadata['runtime_publication_metadata_qualified'] is True
            and metadata['chart_admission'] is False and p.integer(metadata['source_forms_reviewed'],20),
            'Qualified metadata for all twenty source forms required')
    same(review['plan'],metadata['plan'],'Metadata and samples name different plans')
    same(review['plan'],ref(str(l.PLAN),l.PLAN_SHA),'Wrong continuation plan')
    same(metadata['linear_qualification'],plan['linear_qualification'],'Linear qualification changed')
    same(metadata['knucleotide_qualification'],plan['qualification'],'Knucleotide qualification changed')
    require(set(review['profiles'])==set(profiles),'Reconciliation profile inventory differs')
    runtime={x['key']:x for x in metadata['profiles']}
    expected={k for k,v in profiles.items() if v['language']=='prolog' and review['profiles'][k]['full_workload_qualified']}
    require(len(runtime)==len(metadata['profiles']) and set(runtime)==expected,'Runtime profile eligibility differs')
    require(metadata['verified_file_pins'].get(str(METADATA))==METADATA_SHA,'Metadata reviewer unbound')
    for name,digest in review['verified_file_pins'].items():
        require(metadata['verified_file_pins'].get(name)==digest,'Metadata closure omitted reconciled evidence')
    cohorts=copy.deepcopy(review['cohorts'])
    same(cohorts,metadata['cohorts'],'Metadata cohort identities differ')
    require(set(cohorts)=={'original-full90','linear-full81','linear-remaining50','knucleotide-remaining36'},'Four actual cohorts required')
    same(review['prior_producer_statuses'],{'original-full90':'stopped-unqualified','linear-full81':'stopped-unqualified','linear-remaining50':'stopped-unqualified'},
         'Stopped producer statuses changed')
    for name in ('original-full90','linear-full81','linear-remaining50'):
        require(cohorts[name]['status']=='stopped-unqualified','Stopped report falsely completed')
    require(p.integer(review['reused_qualified_samples'],54) and p.integer(review['original_regex_samples'],9)
            and p.integer(review['retained_linear_samples'],31) and p.integer(review['retained_remaining_samples'],14)
            and p.integer(review['excluded_remaining50_attempt'],15),'Preserved cohort counts differ')
    require(p.integer(cohorts['linear-remaining50']['actual_native_processes'],15)
            and cohorts['linear-remaining50']['excluded_attempts']==[15]
            and p.integer(cohorts['linear-remaining50']['preserved_qualified_samples'],14),
            'Stopped fifty-slot cohort must retain its actual fifteen attempts')
    inventory={};controls={};files={};endpoints={};excluded=[]
    for bench in r.BENCHES:
        control_key=bench+':prolog-full-study:mech-control'
        control_row=profiles[control_key];control=copy.deepcopy(review['profiles'][control_key])
        control['sample_execution_metadata']=sample_records(control,control_row,plan,review,read_raw,cohorts)
        control['source_evidence']=ref(control_row['source'],control_row['source_sha256'])
        controls[bench]=control;candidates=[]
        for row in plan['manifests'][bench]['profiles'][:2]:
            measured=review['profiles'][row['key']];roles={};file_ids=[]
            if measured['full_workload_qualified']:
                for field in ('source','source_sha256','source_bundle','binary','binary_sha256','command','runtime_environment'):
                    same(runtime[row['key']][field],row[field],'Runtime/source identity differs')
                same(runtime[row['key']]['timing'],measured,'Runtime metadata binds different timing')
            for source in row['source_bundle']:
                retained=retained_source(source,previous,plan['pins']);digest=source['sha256']
                raw=read_raw(retained['path'],digest)
                require(hashlib.sha256(raw).hexdigest()==digest,'Compiler input bytes differ')
                code=raw.decode('utf-8');public=Path(retained['path']).relative_to(ROOT).as_posix()
                require(digest not in roles,'Repeated source content within one authored bundle')
                if digest in files:require(files[digest]['code']==code,'Source hash collision')
                else:files[digest]=dict(sha256=digest,name=Path(source['path']).name,code=code,archive_path=public)
                role='application' if source['path']==row['measured_source'] else 'application-helper'
                roles[digest]=dict(role=role,source_path=public,retained_source=retained,
                    original_source=ref(source['origin'],digest),normalized_loc=source['normalized_loc'],
                    physical_loc=source['physical_loc'],formatted_loc=None)
                file_ids.append(digest)
            require(sum(v['role']=='application' for v in roles.values())==1,'One counted main required')
            require(sum(v['normalized_loc'] for v in roles.values())==row['canonical_loc']
                    and sum(v['physical_loc'] for v in roles.values())==row['physical_loc'],'Counted bundle total differs')
            success=measured['full_workload_qualified'];control_ok=control['full_workload_qualified'];eligible=success and control_ok
            if success:
                median,sd=p.three_statistics(measured['samples_seconds'])
                require(measured['median_seconds']==median and
                    math.isclose(measured['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Timing statistics differ')
            else:require(measured['median_seconds'] is measured['sample_stdev_seconds'] is measured['time_x_mech'] is None,
                         'Failed subject has an admitted timing')
            ratio=measured['median_seconds']/control['median_seconds'] if eligible else None
            same(measured['time_x_mech'],ratio,'Matched control ratio differs')
            counts=row.get('source_count_review',previous['sealed_source_outcome'])
            work=row.get('required_work_review',previous['sealed_source_outcome'])
            entry=dict(key=row['key'],receipt_key=row['key'],id=row['id'],benchmark=bench,variant=row['variant'],language='prolog',
                loc=row['canonical_loc'],canonical_loc=row['canonical_loc'],physical_loc=row['physical_loc'],formatted_loc=None,
                loc_metric='statement-normalized',files=file_ids,file_roles=roles,seconds=measured['median_seconds'],
                samples=copy.deepcopy(measured['samples_seconds']),timing_sd=measured['sample_stdev_seconds'],
                measurement_status='measured' if success else 'failed-full-workload',source_work_qualified=True,
                canonical_loc_qualified=True,formatted_loc_qualified=False,full_workload_qualified=success,
                matched_control_qualified=control_ok,eligible_for_publication_review=eligible,chart_admission=False,
                source_alias_of=row['source_alias_of'],optimization_claim=row['optimization_claim'],distinct_optimization_claimed=False,
                timing_alias_of=None,command=row['command'],runtime_environment=row['runtime_environment'],cwd=row['cwd'],
                source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],execution_mode='interpreted',
                canonical_source_evidence=copy.deepcopy(counts),required_work_evidence=copy.deepcopy(work),
                compiler_bound_input_inventory=copy.deepcopy(row['compiler_bound_input_inventory']),
                sample_execution_metadata=sample_records(measured,row,plan,review,read_raw,cohorts),
                matched_mech_control_key=control_key,time_ratio_to_matched_mech=ratio,failed_attempt=measured['failed_attempt'],
                attempt_cohorts=list(dict.fromkeys(x['cohort'] for x in measured['sample_evidence'])),
                failed_cohort=measured['failed_cohort'],
                exclusion_reason=None if eligible else ('subject-full-workload-failed' if not success else 'matched-Mech-control-failed'))
            inventory[row['key']]=entry
            if eligible:candidates.append(entry)
            else:excluded.append(row['id'])
        if candidates:
            fast=min(candidates,key=lambda x:(x['seconds'],x['loc'],x['key']))
            small=min(candidates,key=lambda x:(x['loc'],x['seconds'],x['key']))
            endpoints[bench]=dict(fast=fast['key'],small=small['key'],programs=list(dict.fromkeys([small['key'],fast['key']])),chart_admission=False)
        else:endpoints[bench]=dict(fast=None,small=None,programs=[],chart_admission=False)
    language=dict(key='prolog',label='Prolog',family='prolog',platform='runtime',runtime='SWI-Prolog 10.0.2',
        execution=['interpreted'],typing='dynamic',style=['logic'],memory=['gc'],
        note='SWI-Prolog executes precompiled QLF virtual-machine instructions; explicit source aliases retain independent samples.',
        sources=['https://www.swi-prolog.org/pldoc/man?section=qlf','https://www.swi-prolog.org/pldoc/man?section=gc'],
        runtime_policy='SWI-Prolog 10.0.2 arm64 bytecode VM; -q -O -f none --stack-limit=8g; one compute worker',
        memory_policy=metadata['memory_policy'],evidence_scope=metadata['limitations'],
        runtime_publication_metadata_qualified=True,runtime_gc_configuration_observed=True,
        observed_in_each_timed_process=False,gc_numeric_defaults_claimed=False,chart_admission=False)
    return dict(schema=SCHEMA,status='validated-evidence-candidate-awaiting-explicit-publication-review',
        chart_admission=False,dataset_files_changed=False,native_processes_started=0,language_metadata=language,
        program_inventory=inventory,matched_mech_controls=controls,files=files,endpoint_proposals=endpoints,
        excluded_profiles=excluded,failed_profiles=review['failed_profiles'],skipped_slots=review['skipped_slots'],
        actual_full_native_processes=review['actual_full_native_processes'],new_full_native_processes=review['new_full_native_processes'],
        qualified_samples=review['qualified_samples'],reused_qualified_samples=54,original_regex_samples=9,retained_linear_samples=31,retained_remaining_samples=14,
        total_native_processes_including_cancelled=review['total_native_processes_including_cancelled'],excluded_remaining50_attempt=15,
        excluded_original_attempt=10,prior_producer_statuses=copy.deepcopy(review['prior_producer_statuses']),
        cohorts=cohorts,cohort_policy=review['cohort_policy'],plan=review['plan'],report=review['report'],terminal=review['terminal'],
        original_producer_flags_unchanged=True)


def checked(path,digest):
    raw=m.read_regular(path);require(p.digest(digest) and hashlib.sha256(raw).hexdigest()==digest,'Pinned bytes differ: '+str(path))
    return raw


def reproduced_candidate(plan,stopped,prior,previous,review,metadata,read_raw,reconciliation_ref,metadata_ref):
    result=build_candidate(plan,stopped,prior,previous,review,metadata,read_raw)
    result.update(reconciliation=reconciliation_ref,runtime_metadata=metadata_ref,
        export_controller=ref(str(Path(__file__).resolve()),hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    return result


def save_candidate(args,output):
    owned=m.OwnedResult(output);controller=Path(__file__).resolve()
    supplemental={str(args.reconciliation):args.reconciliation_sha256,str(args.metadata):args.metadata_sha256,
                  str(controller):hashlib.sha256(controller.read_bytes()).hexdigest(),str(METADATA):METADATA_SHA}
    def cleanup():owned.remove()
    def check():
        for path,digest in supplemental.items():checked(path,digest)
        owned.verify()
    try:
        with m.review_context(args.reconciliation,args.reconciliation_sha256,
                              on_exit_failure=cleanup,final_consumer_check=check) as fresh:
            same(p.strict_json(checked(args.metadata,args.metadata_sha256)),fresh,'Saved runtime metadata did not reproduce')
            review=p.strict_json(checked(args.reconciliation,args.reconciliation_sha256))
            plan=p.strict_json(checked(l.PLAN,l.PLAN_SHA))
            stopped=p.strict_json(checked(l.PREVIOUS_PLAN,l.PREVIOUS_PLAN_SHA))
            prior=p.strict_json(checked(l.PRIOR_PLAN,l.PRIOR_PLAN_SHA))
            previous=p.strict_json(checked(*l.OLD_REFS['plan']))
            def read_raw(path,digest):
                require(fresh['verified_file_pins'].get(path)==digest,'Unverified candidate input')
                return checked(path,digest)
            result=reproduced_candidate(plan,stopped,prior,previous,review,fresh,read_raw,
                ref(str(args.reconciliation.resolve()),args.reconciliation_sha256),ref(str(args.metadata.resolve()),args.metadata_sha256))
            check();owned_sha=owned.write(result)
        return result,owned_sha
    except BaseException as error:
        try:cleanup()
        except BaseException as cleanup_error:raise BaseExceptionGroup('Candidate failure and cleanup conflict',[error,cleanup_error])
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reconciliation','metadata'):
        parser.add_argument('--'+name,type=Path,required=True);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B')
    output=args.output.resolve()
    require(output.is_relative_to(l.PACKET) and not output.is_relative_to(l.PACKET/'run-v1')
            and not output.exists() and output.parent.is_dir(),'Fresh additive candidate output required')
    m.install_stop_handlers()
    result,digest=save_candidate(args,output)
    print(json.dumps(dict(status=result['status'],sha256=digest,programs=len(result['program_inventory']))),flush=True)


if __name__=='__main__':main()
