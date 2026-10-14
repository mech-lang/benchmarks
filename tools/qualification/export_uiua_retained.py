"""Export exact retained Uiua n-body/tree sources and measurements for review.

The exporter reproduces the independent native provenance under the common
mutex. It writes a fresh private candidate and changes no catalog or baseline.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/uiua/retained-native-v1'
RECONCILER=ROOT/'tools/qualification/uiua_retained_reconcile.py'
RECONCILER_SHA='6ffbc98941b3e4e60ac63a899f0e8e4e0cb10def2d3d66ba60c61d25ad3a5523'
REVIEW=PACKET/'independent-source-review-v2.json'
REVIEW_SHA='399451293e8161ea3c32224fb9d0eb945782db0d2d342d1caad860d9040231f2'


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def public_ref(ref):
    path=Path(ref['path'])
    require(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve().is_relative_to(ROOT.resolve()),
            'Retained repository evidence reference required')
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=ref['sha256'])


def load_reconciler():
    raw=RECONCILER.read_bytes();require(sha(raw)==RECONCILER_SHA,'Reviewed reconciler changed')
    spec=importlib.util.spec_from_file_location('uiua_retained_export_review',RECONCILER)
    result=importlib.util.module_from_spec(spec);exec(compile(raw,str(RECONCILER),'exec'),result.__dict__)
    return result


def build_candidate(review,sources):
    require(review['schema']=='uiua-retained-nbody-trees-independent-reconciliation-v1' and
            review['status']=='fifteen-retained-observations-file-verified-awaiting-publication' and
            review['file_integrity_verified'] is review['common_mutex_held'] is True and
            review['canonical_loc_qualified'] is review['source_work_qualified'] is True and
            review['chart_admission'] is review['dataset_files_changed'] is False and
            review['native_processes_started']==0 and review['accepted_native_observations']==15 and
            review['subject_native_observations']==9 and review['control_native_observations']==6 and
            review['preserved_excluded_native_observations']==1 and review['timing_aliases']==1,
            'Exact independently verified retained cohort required')
    profiles=review['profiles']
    subjects={key:p for key,p in profiles.items() if p['language']=='uiua'}
    controls={p['benchmark']:p for p in profiles.values() if p['language']=='mech'}
    require(len(subjects)==4 and set(sources)==set(subjects) and set(controls)=={'nbody','binarytrees'},
            'Four source forms and two matched controls required')
    files={};inventory={}
    report=public_ref(review['report']);audit=public_ref(review['source_audit']);counts=public_ref(review['count_approval'])
    for key,profile in sorted(subjects.items()):
        original=profile['original_profile'];count=profile['canonical_source_count'];source=sources[key]
        digest=sha(source)
        require(digest==profile['source_sha256']==original['source_sha256']==count['source_sha256'] and
                count['canonical_loc']==(15 if profile['benchmark']=='binarytrees' else 21),
                'Measured source and independent canonical count differ')
        source_path='archive/comparisons/'+str(Path(original['source']).relative_to(
            Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')))
        source_path=Path(source_path).as_posix()
        if digest not in files:
            files[digest]=dict(path=source_path,archive_path=source_path,name=Path(source_path).name,
                sha256=digest,code=source.decode('utf-8'),source_paths=[source_path])
        else:
            require(files[digest]['code']==source.decode('utf-8'),'Source digest collision')
            files[digest]['source_paths'].append(source_path)
        control=controls[profile['benchmark']];control_source=control['original_profile']
        alias=profile['timing_alias_of']
        require(profile['native_observations']==(0 if alias else 3),'Alias duplicated native observations')
        if alias:
            require(alias in subjects and subjects[alias]['timing_alias_of'] is None and
                    profile['source_sha256']==subjects[alias]['source_sha256'] and
                    profile['samples_seconds']==subjects[alias]['samples_seconds'] and
                    profile['sample_evidence']==subjects[alias]['sample_evidence'],
                    'Alias source/timing ownership differs')
        inventory[key]=dict(key=key,id=original['id'],benchmark=profile['benchmark'],language='uiua',
            variant=original['variant'],profile=original.get('profile'),source_profile=original.get('source_profile'),
            loc=count['canonical_loc'],canonical_loc=count['canonical_loc'],physical_loc=count['original_physical_loc'],
            loc_metric='canonical-source-units',formatted_loc=None,formatted_loc_qualified=False,
            formatted_loc_complete=False,formatted_loc_status='unavailable',formatted_x=None,
            source_sha256=digest,source_path=source_path,files=[digest],
            file_roles={digest:dict(role='application',source_path=source_path,normalized_loc=count['canonical_loc'],
                physical_loc=count['original_physical_loc'],formatted_loc=None,canonical_owner_receipt=counts)},
            samples=copy.deepcopy(profile['samples_seconds']),seconds=profile['median_seconds'],
            timing_sd=profile['sample_stdev_seconds'],sample_execution_metadata=copy.deepcopy(profile['sample_execution_metadata']),
            sample_evidence=copy.deepcopy(profile['sample_evidence']),
            full_output_validation=copy.deepcopy(original['sample_validation']),report=report['path'],report_sha256=report['sha256'],
            source_report=audit['path'],loc_report=counts['path'],loc_report_sha256=counts['sha256'],loc_expansions=[],
            algorithm=copy.deepcopy(original['algorithm']),source_work_qualified=True,canonical_loc_qualified=True,
            required_work_validated=True,full_workload_qualified=True,
            eligible_for_publication_review=True,eligible_for_chart=False,chart_admission=False,
            timing_alias_of=alias,aliased_sample_source=original.get('aliased_sample_source'),
            native_observations=profile['native_observations'],distinct_optimization_claimed=False,
            runtime=copy.deepcopy(original['runtime']),runtime_policy='Uiua 0.19.1 · official native ARM64 interpreter',
            runtime_arguments=copy.deepcopy(original['command']),runtime_environment=copy.deepcopy(original['runtime_environment']),
            maximum_workers=original['maximum_workers'],execution_fingerprint=original.get('execution_fingerprint'),
            timing_boundary=review['timing_scope'],timing_measurement=dict(kind='full-process-wall',samples=3,
                includes=['startup','source compilation','computation','complete output','shutdown']),
            provenance=copy.deepcopy(original.get('provenance')),adaptations=copy.deepcopy(original.get('adaptations')),
            matched_mech_control=copy.deepcopy(control),
            mech_comparison=dict(scope='paired-control',seconds=control['median_seconds'],control_key=control['key'],
                control_loc=control_source['loc'],source=control_source['source'],source_sha256=control['source_sha256'],
                samples_seconds=copy.deepcopy(control['samples_seconds']),report=report['path'],
                sample_execution_metadata=copy.deepcopy(control['sample_execution_metadata']),
                time_x_mech=profile['median_seconds']/control['median_seconds'],
                control_loc_x_mech=count['canonical_loc']/control_source['loc']))
    return dict(schema='uiua-retained-nbody-trees-publication-candidate-v1',
        status='validated-retained-observations-awaiting-publication-review',
        files=files,program_inventory=inventory,source_forms=4,distinct_subject_sources=3,timing_aliases=1,
        retained_subject_native_observations=9,retained_control_native_observations=6,
        report=report,source_audit=audit,count_approval=counts,
        source_counts={key:copy.deepcopy(p['canonical_source_count']) for key,p in subjects.items()},
        preserved_environmental_exclusion=copy.deepcopy(review['excluded_attempt']),
        guard_revisions=copy.deepcopy(review['guard_revisions']),guard=copy.deepcopy(review['guard']),
        required_work=dict(binarytrees=copy.deepcopy(review['tree_work_scope']),nbody=copy.deepcopy(review['nbody_work'])),
        limitations=[review['environment_limitation'],review['resource_observation_limitation'],
            'The original report-only runner did not write separate sampler or supervisor receipts.',
            'The tree alias contributes no additional native observations. Formatted LOC remains unavailable.'],
        proposed_coordinate_policy=dict(nbody='Preserve the existing independently qualified minimum unless the concrete catalog requires an explicit rebase.',
            binarytrees='The new independently qualified 15-unit minimum requires an audited x-best rebase if the current baseline is still 16.'),
        chart_admission=False,dataset_files_changed=False,historical_reports_mutated=False,native_processes_started=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();own=Path(__file__).resolve();output=args.output.resolve()
    require(sha(own.read_bytes())==args.tool_sha256,'Explicit reviewed exporter SHA-256 required')
    require(output.is_relative_to(PACKET.resolve()) and not output.exists(),'Fresh candidate directory required')
    r=load_reconciler();writer=r.load_modules()['writer'];owner=writer.OwnedFiles()
    with r.review_context(RECONCILER_SHA,on_exit_failure=owner.remove_all,final_consumer_check=owner.final_check) as (review,files):
        files.verify(own,args.tool_sha256);files.verify(REVIEW,REVIEW_SHA)
        sources={key:files.read(Path(review['profiles'][key]['original_profile']['source']),
            review['profiles'][key]['source_sha256']) for key in r.COUNTS}
        candidate=build_candidate(review,sources)
        output.mkdir(parents=True)
        review_raw=writer.encoded(review)
        candidate['reconciliation']=dict(path=(output/'reconciliation.json').relative_to(ROOT).as_posix(),sha256=sha(review_raw))
        candidate['independent_source_review']=dict(path=REVIEW.relative_to(ROOT).as_posix(),sha256=REVIEW_SHA)
        candidate['consumer_sources']=dict(exporter=dict(path=own.relative_to(ROOT).as_posix(),sha256=args.tool_sha256),
            reconciler=dict(path=RECONCILER.relative_to(ROOT).as_posix(),sha256=RECONCILER_SHA))
        candidate_raw=writer.encoded(candidate)
        owner.write(output/'reconciliation.json',review_raw);owner.write(output/'candidate.json',candidate_raw)
        success=dict(status='candidate-exported',candidate_sha256=sha(candidate_raw),reconciliation_sha256=sha(review_raw),
            retained_subject_native_observations=9,retained_control_native_observations=6,native_processes_started=0,
            catalog_changed=False)
        owner.write(output/'SUCCESS.json',writer.encoded(success))
    print(json.dumps(success,indent=2))


if __name__=='__main__':main()
