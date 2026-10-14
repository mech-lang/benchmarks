"""Prepare a Lua-only candidate from the eighteen retained pi-digit records."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/lua/retained-pidigits-v1'
RECONCILER_SHA='7f18cb6870b084e9aa96ec0eb9874f550e831b6d93eceeb24939143ea7ab319b'
WRITER_SHA='f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'
REPORT='archive/comparisons/lua-pidigits-comparison/20261012/results/full-study.json'


def require(condition,message):
    if not condition:raise ValueError(message)


def ref(path,digest):return dict(path=path,sha256=digest)


def module(name,filename,digest):
    path=Path(__file__).with_name(filename);raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'Reviewed consumer source changed: '+filename)
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),value.__dict__);return value


def build_candidate(review,sources,r):
    require(review['schema']=='lua-retained-pidigits-reconciliation-v1'
            and review['status']=='eighteen-saved-observations-file-verified-awaiting-publication-review'
            and review['physical_file_integrity_verified'] is review['common_mutex_held'] is True
            and review['source_work_qualified'] is review['canonical_loc_qualified'] is True
            and review['total_observations']==18 and review['subject_observations']==12
            and review['matched_control_observations']==6 and review['native_processes_started']==0
            and review['luajit_mutated'] is review['chart_admission'] is False,
            'Complete Lua-only physical reconciliation required')
    counts=review['canonical_counts'];require(set(sources)==set(counts['files']),'Five counted source files required')
    files={};inventory={};controls={}
    for digest,raw in sources.items():
        c=counts['files'][digest]
        require(hashlib.sha256(raw).hexdigest()==digest==c['sha256'],'Counted source bytes differ')
        files[digest]=dict(path=c['path'],archive_path=c['path'],name=Path(c['path']).name,
                           sha256=digest,code=raw.decode('utf-8'))
    for identity in r.CONTROLS:
        row=review['profiles'][identity];samples=row['samples_seconds']
        require(row['language']=='mech' and len(samples)==3
                and statistics.median(samples)==row['median_seconds']
                and statistics.stdev(samples)==row['sample_stdev_seconds'],'Matched control statistics differ')
        controls[identity]=dict(key=row['key'],source=row['source'],source_sha256=row['source_sha256'],
            command=copy.deepcopy(row['command']),samples=copy.deepcopy(samples),
            seconds=row['median_seconds'],timing_sd=row['sample_stdev_seconds'],
            report=ref(REPORT,r.REPORT_SHA),attempt_numbers=[a['attempt'] for a in row['sample_execution_metadata']])
    fast_control=controls['mech-fast-control']
    for identity in r.IDS:
        row=review['profiles'][identity];bundle=counts['profiles'][identity];digest=row['source_sha256'];samples=row['samples_seconds']
        require(bundle['files']==[digest,r.HELPER_SHA] and len(samples)==3
                and statistics.median(samples)==row['median_seconds']
                and statistics.stdev(samples)==row['sample_stdev_seconds'],'Measured source, bundle or samples differ')
        require(bundle['canonical_loc']==sum(counts['files'][d]['canonical_loc'] for d in bundle['files'])
                and bundle['physical_loc']==sum(counts['files'][d]['physical_loc'] for d in bundle['files']),
                'Complete counted bundle differs')
        roles={d:dict(role=counts['files'][d]['role'],source_path=counts['files'][d]['path'],
            normalized_loc=counts['files'][d]['canonical_loc'],physical_loc=counts['files'][d]['physical_loc'],
            formatted_loc=None,source_owner_review=copy.deepcopy(review['source_counts'])) for d in bundle['files']}
        key=row['key'];inventory[key]=dict(key=key,id=identity,benchmark='pidigits',language='lua',
            variant=review['algorithm_forms'][identity],loc=bundle['canonical_loc'],canonical_loc=bundle['canonical_loc'],
            physical_loc=bundle['physical_loc'],loc_metric='canonical-source-units',canonical_loc_qualified=True,
            formatted_loc=None,formatted_loc_qualified=False,formatted_loc_complete=False,
            formatted_loc_status='unavailable',formatted_x=None,files=copy.deepcopy(bundle['files']),
            source_sha256=digest,file_roles=roles,samples=copy.deepcopy(samples),seconds=row['median_seconds'],
            timing_sd=row['sample_stdev_seconds'],full_output_validation=copy.deepcopy(row['sample_validation']),
            report=REPORT,report_sha256=r.REPORT_SHA,source_report=review['source_manifest']['path'],
            source_manifest_sha256=review['source_manifest']['sha256'],
            original_manifest_sha256=r.MANIFEST_SHA,loc_report=review['source_counts']['path'],
            loc_expansions=[],original_producer_loc=row['loc'],original_producer_physical_loc=row['physical_loc'],
            original_helper_counted=False,helper_counted=True,
            algorithm=copy.deepcopy(row['algorithm']),required_work_validated=True,source_work_qualified=True,
            full_workload_qualified=True,eligible_for_publication_review=True,eligible_for_chart=False,
            chart_admission=False,timing_alias_of=None,native_observations=3,distinct_source_form=True,
            source_provenance='Retained listed Lua source with formatting-only normalization and a general GMP compatibility module.',
            upstream_source_url=row['source_url'],upstream_source_sha256=row['upstream_sha256'],
            adaptations=copy.deepcopy(row['adaptations']),
            sample_evidence=dict(kind='original-completed-study-and-per-attempt-receipts',
                report=ref(REPORT,r.REPORT_SHA),attempt_numbers=[a['attempt'] for a in row['sample_execution_metadata']],
                receipts=[dict(attempt=a['attempt'],path='archive/comparisons/'+r.COHORT+'/full-study/attempts/'+
                    Path(a['result_path']).name) for a in row['sample_execution_metadata']]),
            sample_execution_metadata=copy.deepcopy(row['sample_execution_metadata']),
            timing_boundary=review['timing_boundary'],timing_measurement=dict(kind='full-process-wall',samples=3,
                includes=['startup','source loading','computation','complete output','shutdown','supervisor notification']),
            runtime_policy=review['runtime_policy'],execution_mode='interpreted',runtime=copy.deepcopy(row['runtime']),
            runtime_arguments=copy.deepcopy(row['command']),runtime_environment=copy.deepcopy(row['runtime_environment']),
            maximum_workers=1,general_native_library=copy.deepcopy(review['library']),
            matched_mech_control=copy.deepcopy(fast_control),additional_matched_mech_control=copy.deepcopy(controls['mech-small-control']),
            mech_comparison=dict(scope='paired-control',control_key=fast_control['key'],seconds=fast_control['seconds'],
                samples_seconds=copy.deepcopy(fast_control['samples']),time_x_mech=row['median_seconds']/fast_control['seconds']),
            provenance_limitations=copy.deepcopy(review['limitations']))
    rows=list(inventory.values());fast=min(rows,key=lambda x:(x['seconds'],x['loc'],x['key']))
    small=min(rows,key=lambda x:(x['loc'],x['seconds'],x['key']))
    endpoints={'pidigits':dict(language='lua',label='Lua (interpreted)',fast=fast['key'],small=small['key'],
        programs=list(dict.fromkeys([fast['key'],small['key']])),formatted_fast=None,formatted_small=None)}
    return dict(schema='lua-retained-pidigits-publication-candidate-v1',
        status='validated-retained-observations-awaiting-publication-review',program_inventory=inventory,
        files=files,matched_mech_controls=controls,endpoints=endpoints,source_forms=4,subject_samples=12,
        matched_control_samples=6,native_processes_started=0,report=ref(REPORT,r.REPORT_SHA),
        source_counts=copy.deepcopy(review['source_counts']),source_manifest=copy.deepcopy(review['source_manifest']),
        original_manifest_sha256=r.MANIFEST_SHA,historical_reports_mutated=False,luajit_mutated=False,
        chart_admission=False,dataset_files_changed=False)


def export(args):
    r=module('lua_retained_closed_consumer','lua_pidigits_reconcile.py',RECONCILER_SHA)
    writer=module('lua_retained_owned_writer','import_uiua_fann.py',WRITER_SHA)
    own=Path(__file__).resolve();digest=hashlib.sha256(own.read_bytes()).hexdigest()
    require(digest==args.tool_sha256,'Explicit exporter source digest differs')
    output=args.output.resolve()
    require(output.is_relative_to(PACKET.resolve()) and not output.exists(),'Fresh packet output directory required')
    owner=writer.OwnedFiles()
    with r.review_context(RECONCILER_SHA,args.source_counts,args.source_counts_sha256,
            on_exit_failure=owner.remove_all,final_consumer_check=owner.final_check) as (review,files,sources):
        files.verify(own,digest);files.verify(own.with_name('import_uiua_fann.py'),WRITER_SHA)
        candidate=build_candidate(review,sources,r);output.mkdir(parents=True)
        review_raw=writer.encoded(review);owner.write(output/'reconciliation.json',review_raw)
        candidate['reconciliation']=ref((output/'reconciliation.json').relative_to(ROOT).as_posix(),hashlib.sha256(review_raw).hexdigest())
        candidate['exporter']=ref(own.relative_to(ROOT).as_posix(),digest)
        raw=writer.encoded(candidate);owner.write(output/'candidate.json',raw)
    print(json.dumps(dict(status=candidate['status'],candidate=str(output/'candidate.json'),
        candidate_sha256=hashlib.sha256(raw).hexdigest(),native_processes_started=0)))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tool-sha256',required=True)
    p.add_argument('--source-counts',type=Path,required=True);p.add_argument('--source-counts-sha256',required=True)
    p.add_argument('--output',type=Path,required=True);export(p.parse_args())


if __name__=='__main__':main()
