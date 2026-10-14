"""Prepare a candidate from five independently reconciled GNU APL workloads.

The file phase replays saved evidence under the common timing mutex. No native
subject is executed; catalog import and derived coordinates remain separate.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/apl/retained-native-v1'
RECONCILER_SHA='3abf092426f9febb692a049907fb9ea12822e78f672a949c28efc82ea3a4942c'
WRITER_SHA='f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'


def require(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def module(name,filename,digest):
    path=Path(__file__).with_name(filename);raw=path.read_bytes()
    require(sha(raw)==digest,'Reviewed source changed: '+filename)
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),value.__dict__);return value


def public_ref(ref):return dict(path=ref['path'],sha256=ref['sha256'])


def sample_evidence(profile,index,report):
    output=[]
    for n in profile['native_attempts']:
        a=report['attempts'][n-1]
        require(a['attempt_number']==n and a['key']==profile['source_profile']['key'],'Native evidence source differs')
        row=dict(attempt=n,seconds=a['seconds'],validation=copy.deepcopy(a['validation']),
            started_at=a['started_at'],finished_at=a['finished_at'],
            report=public_ref(index['documents']['report']),recorded_command=copy.deepcopy(a['command']),
            runtime_environment=copy.deepcopy(a['runtime_environment']),execution_fingerprint=a['execution_fingerprint'])
        if n==44:
            row.update(provenance='original-report-only',raw=None,supervisor=None,
                lifecycle_scope='Recorded native exit and process-group/monitor disposition; no separate supervisor receipt')
        else:
            pair=index['receipts'][str(n)]
            require(pair['raw']['recorded_path']==a['result_path'] and pair['supervisor']['recorded_path']==a['supervisor_result_path'],
                'Original raw/supervisor route differs')
            row.update(provenance='kernel-exit-recovery' if n==84 else 'original-guarded-receipts',
                raw=public_ref(pair['raw']),supervisor=public_ref(pair['supervisor']),
                lifecycle_scope='Literal Darwin kernel exit recovery' if n==84 else 'Original PGID registration, sampler exit status and cleanup')
            if n==84:row['recovery_admission']=public_ref(index['documents']['admission'])
        output.append(row)
    return output


def build_candidate(review,sources,index,counts,report):
    require(review['schema']=='apl-retained-five-native-reconciliation-v1'
        and review['status']=='five-completed-workloads-reconciled-awaiting-publication-review'
        and review['file_integrity_verified'] is review['common_mutex_held'] is True
        and review['source_work_qualified'] is review['canonical_loc_qualified'] is True
        and review['accepted_native_observations']==42 and review['apl_native_observations']==27
        and review['matched_control_observations']==15 and review['selected_source_identities']==9
        and review['selected_source_labels']==11 and review['timing_alias_labels']==2
        and review['chart_admission'] is review['full_suite_qualified'] is False and review['new_native_processes']==0,
        'Exact physically reconciled five-workload cohort required')
    require(report['status']==review['original_report_status']=='partial' and len(report['attempts'])==87
        and review['recovery_owner_status']=='complete','Original partial producer status changed')
    require(counts['canonical_loc_qualified'] is True and counts['formatted_loc_qualified'] is False
        and len(counts['sources'])==len(sources)==9 and len(counts['profiles'])==11,'Exact independently qualified counts required')
    counted={r['key']:r for r in counts['profiles']};profiles=review['profiles']
    subjects={k:r for k,r in profiles.items() if r['language']=='apl'}
    controls={r['benchmark']:r for r in profiles.values() if r['language']=='mech'}
    require(set(subjects)==set(counted) and set(controls)=={'nbody','mandelbrot','knucleotide','fannkuchredux','fasta'},'Subject/control inventory changed')
    report_ref=public_ref(index['documents']['report']);audit_ref=public_ref(index['documents']['audit']);count_ref=public_ref(index['documents']['counts'])
    files,inventory,matched,endpoints={},{},{},{}
    for bench,p in controls.items():
        require(len(p['native_attempts'])==3 and len(p['samples_seconds'])==3,'Matched control is incomplete')
        matched[bench]=dict(key=p['source_profile']['key'],source=p['source'],source_sha256=p['source_sha256'],
            command=copy.deepcopy(p['source_profile']['command']),samples=copy.deepcopy(p['samples_seconds']),
            seconds=p['median_seconds'],timing_sd=p['sample_stdev_seconds'],report=report_ref,
            sample_evidence=sample_evidence(p,index,report),native_observations=3)
    for key,p in subjects.items():
        original=p['source_profile'];count=counted[key];raw=sources[count['source_identity']];digest=sha(raw)
        require(original==report['programs'][key] and digest==p['source_sha256']==count['source']['sha256']
            and count['canonical_loc']==p['canonical_loc'] and count['formatted_loc'] is None,'Source/count/report identity differs')
        require(p['source_work_qualified'] is p['canonical_loc_qualified'] is True
            and p['source_work_evidence']['qualified'] is True,'Source work not qualified')
        path=count['source']['path'];files.setdefault(digest,dict(path=path,archive_path=path,name=Path(path).name,
            sha256=digest,code=raw.decode('utf-8')))
        alias=p['timing_alias_of'];owner=subjects[alias] if alias else p
        require(alias is None or owner['timing_alias_of'] is None,'Unflattened execution alias')
        require(len(p['native_attempts'])==(0 if alias else 3),'Alias gained independent native observations')
        require(p['samples_seconds']==owner['samples_seconds'] and p['source_sha256']==owner['source_sha256'],'Alias source or samples differ')
        samples=copy.deepcopy(p['samples_seconds'])
        require(len(samples)==3 and all(type(x) in (int,float) and x>0 for x in samples)
            and statistics.median(samples)==p['median_seconds'] and statistics.stdev(samples)==p['sample_stdev_seconds'],'Invalid sample statistics')
        bench=p['benchmark'];control=matched[bench]
        inventory[key]=dict(key=key,id=original['id'],benchmark=bench,language='apl',variant=original['variant'],
            profile=original.get('profile'),role=original.get('role'),files=[digest],source_sha256=digest,source_path=path,
            loc=p['canonical_loc'],canonical_loc=p['canonical_loc'],canonical_loc_qualified=True,physical_loc=count['physical_loc'],
            loc_metric='canonical-source-units',formatted_loc=None,formatted_loc_qualified=False,formatted_loc_complete=False,
            formatted_loc_status='unavailable',formatted_x=None,loc_expansions=[],original_producer_loc=original['loc'],
            original_producer_physical_loc=original.get('physical_loc'),
            file_roles={digest:dict(role='application',source_path=path,normalized_loc=p['canonical_loc'],
                physical_loc=count['physical_loc'],formatted_loc=None,canonical_owner_receipt=count_ref)},
            samples=samples,seconds=p['median_seconds'],timing_sd=p['sample_stdev_seconds'],
            report=report_ref['path'],report_sha256=report_ref['sha256'],source_report=audit_ref['path'],
            loc_report=count_ref['path'],loc_report_sha256=count_ref['sha256'],
            sample_evidence=sample_evidence(owner,index,report),native_observations=len(p['native_attempts']),
            full_output_validation=copy.deepcopy(original['sample_validation']),
            timing_alias_of=alias,aliased_sample_source=alias,distinct_optimization_claimed=False,
            source_work_qualified=True,required_work_validated=True,full_workload_qualified=True,
            source_work_evidence=copy.deepcopy(p['source_work_evidence']),algorithm=copy.deepcopy(original['algorithm']),
            small_validation=copy.deepcopy(original['small_validation']),adversarial_validation=copy.deepcopy(original['adversarial_validation']),
            eligible_for_publication_review=True,eligible_for_chart=False,chart_admission=False,
            runtime=copy.deepcopy(original['runtime']),runtime_policy='GNU APL 2.0 · native ARM64 interpreter · serial numerical primitives on macOS',
            execution_mode='interpreted',runtime_arguments=copy.deepcopy(original['command']),
            runtime_environment=copy.deepcopy(original['runtime_environment']),
            maximum_workers=p['source_work_evidence']['requested_worker_ceiling'],
            numerical_primitive_parallelism_enabled=False,runtime_publication_metadata_qualified=False,
            runtime_dependency_scope=review['runtime_dependency_scope'],
            source_provenance=copy.deepcopy(original['source_provenance']),upstream_source_url=original.get('source_url'),
            adaptations=copy.deepcopy(original['adaptations']),
            timing_boundary=review['timing_scope'],timing_measurement=dict(kind='full-process-wall',samples=3,
                includes=['startup','runtime/source preparation','input','computation','complete output','shutdown']),
            matched_mech_control=copy.deepcopy(control),mech_comparison=dict(scope='paired-control',control_key=control['key'],
                seconds=control['seconds'],samples_seconds=copy.deepcopy(control['samples']),time_x_mech=p['median_seconds']/control['seconds']),
            provenance_limitations=[review['native_receipt_scope'],review['environment_scope'],review['runtime_dependency_scope']])
    require(len(files)==9 and sum(v['native_observations'] for v in inventory.values())==27,'Source or native observations were duplicated')
    for bench in controls:
        rows=[r for r in inventory.values() if r['benchmark']==bench]
        fast=min(rows,key=lambda r:(r['seconds'],r['loc'],r['key']))
        small=min(rows,key=lambda r:(r['loc'],r['seconds'],r['key']))
        endpoints[bench]=dict(language='apl',label='APL (GNU APL)',fast=fast['key'],small=small['key'],
            programs=list(dict.fromkeys([fast['key'],small['key']])),formatted_fast=None,formatted_small=None)
    failed={}
    for n in (58,75):
        a=report['attempts'][n-1];require(a['qualified'] is False and a['error_type']=='OutputValidationError','Preserved failure changed disposition')
        failed[str(n)]=dict(original_attempt=copy.deepcopy(a),raw=public_ref(index['receipts'][str(n)]['raw']),
            supervisor=public_ref(index['receipts'][str(n)]['supervisor']))
    return dict(schema='apl-retained-five-workload-publication-candidate-v1',status='validated-retained-observations-awaiting-publication-review',
        files=files,program_inventory=inventory,matched_mech_controls=matched,endpoints=endpoints,
        source_forms=11,distinct_subject_sources=9,timing_aliases=2,retained_subject_native_observations=27,
        retained_control_native_observations=15,report=report_ref,source_audit=audit_ref,source_counts=count_ref,
        original_report_status='partial',recovery_owner_status='complete',preserved_failed_attempts=failed,
        recovered_original_attempt=84,recovery_admission=public_ref(index['documents']['admission']),
        binarytrees_qualified=False,complete_suite_qualified=False,runtime_publication_metadata_qualified=False,
        chart_admission=False,dataset_files_changed=False,historical_reports_mutated=False,native_processes_started=0)


def export(args):
    r=module('apl_retained_closed_consumer','apl_retained_reconcile.py',RECONCILER_SHA)
    writer=module('apl_retained_owned_writer','import_uiua_fann.py',WRITER_SHA)
    own=Path(__file__).resolve();require(sha(own.read_bytes())==args.tool_sha256,'Explicit exporter source digest required')
    output=args.output.resolve();require(output.is_relative_to(PACKET.resolve()) and not output.exists(),'Fresh packet output directory required')
    owner=writer.OwnedFiles()
    with r.review_context(RECONCILER_SHA,on_exit_failure=owner.remove_all,final_consumer_check=owner.final_check) as (review,files):
        files.verify(own,args.tool_sha256);files.verify(own.with_name('import_uiua_fann.py'),WRITER_SHA)
        index,d,_,sources=r.metadata()
        candidate=build_candidate(review,sources,index,d['counts'],d['report'])
        output.mkdir(parents=True)
        review_raw=writer.encoded(review);owner.write(output/'reconciliation.json',review_raw)
        candidate['reconciliation']=dict(path=(output/'reconciliation.json').relative_to(ROOT).as_posix(),sha256=sha(review_raw))
        candidate['exporter']=dict(path=own.relative_to(ROOT).as_posix(),sha256=args.tool_sha256)
        raw=writer.encoded(candidate);owner.write(output/'candidate.json',raw)
    print(json.dumps(dict(status=candidate['status'],candidate=str(output/'candidate.json'),candidate_sha256=sha(raw),native_runs=0)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    export(parser.parse_args())


if __name__=='__main__':main()
