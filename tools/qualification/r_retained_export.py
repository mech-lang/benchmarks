"""Prepare a public candidate from independently reconciled saved R samples."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/r/retained-native-v1'
RECONCILER_SHA='8015461d228fa1d72acb1fdf76373f20bcc257b813534bf874d850df308e062b'
WRITER_SHA='f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'
REPORT='archive/comparisons/r-apl-uiua-comparison/20261011/results/timings-r.json'
AUDIT='archive/comparisons/r-apl-uiua-comparison/20261011/source-audit-r.json'
COUNT_PATH='experiments/r/retained-source-counts-v1/qualified-source-counts-v1.json'


def require(condition,message):
    if not condition:raise ValueError(message)


def module(name,filename,digest):
    path=Path(__file__).with_name(filename);raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'Reviewed consumer changed: '+filename)
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),value.__dict__)
    return value


def reference(path,digest):return dict(path=path,sha256=digest)


def build_candidate(review,sources,reconciler):
    require(review['schema']=='r-retained-three-workload-reconciliation-v1'
            and review['status']=='27-saved-observations-reconciled-awaiting-publication-review'
            and review['physical_file_integrity_verified'] is review['common_mutex_held'] is True
            and review['source_work_qualified'] is review['canonical_loc_qualified'] is True
            and review['native_observations']==27 and review['native_processes_started']==0
            and review['chart_admission'] is False,'Complete physical-file reconciliation required')
    counts=review['canonical_counts']
    require(set(sources)==set(counts) and len(counts)==6,'Six exact counted sources required')
    files,inventory,controls,endpoints={},{},{},{}
    for benchmark in reconciler.BENCHES:
        key=benchmark+':mech-control-for-r';control=review['profiles'][key]
        require(control['language']=='mech' and len(control['samples_seconds'])==3,'Matched control missing')
        controls[benchmark]=dict(key=key,source=control['source'],source_sha256=control['source_sha256'],
            command=copy.deepcopy(control['command']),samples=copy.deepcopy(control['samples_seconds']),
            seconds=statistics.median(control['samples_seconds']),timing_sd=statistics.stdev(control['samples_seconds']),
            report=reference(REPORT,reconciler.REPORT_SHA),attempt_numbers=copy.deepcopy(control['attempts']))
    for key,count in counts.items():
        original=review['profiles'][key];source=sources[key];digest=hashlib.sha256(source).hexdigest()
        require(digest==count['source']['sha256']==original['source_sha256'] and
                count['canonical_loc_qualified'] is True and count['formatted_loc'] is None,
                'Exact independently counted source changed')
        path=count['source']['path'];benchmark=original['benchmark'];control=controls[benchmark]
        files[digest]=dict(path=path,archive_path=path,name=Path(path).name,sha256=digest,code=source.decode('utf-8'))
        samples=copy.deepcopy(original['samples_seconds'])
        require(len(samples)==3 and statistics.median(samples)==original['median_seconds']
                and statistics.stdev(samples)==original['sample_stdev_seconds'],'Stored sample statistics differ')
        inventory[key]=dict(key=key,id=original['id'],benchmark=benchmark,language='r',
            variant=original['variant'],loc=count['canonical_loc'],canonical_loc=count['canonical_loc'],
            physical_loc=count['physical_loc'],loc_metric='canonical-source-units',canonical_loc_qualified=True,
            formatted_loc=None,formatted_loc_qualified=False,formatted_loc_complete=False,
            formatted_loc_status='unavailable',formatted_x=None,files=[digest],source_sha256=digest,
            file_roles={digest:dict(role='application',source_path=path,normalized_loc=count['canonical_loc'],
                physical_loc=count['physical_loc'],formatted_loc=None,
                source_owner_review=reference(COUNT_PATH,reconciler.COUNTS_SHA))},
            samples=samples,seconds=original['median_seconds'],timing_sd=original['sample_stdev_seconds'],
            full_output_validation=copy.deepcopy(original['sample_validation']),
            report=REPORT,report_sha256=reconciler.REPORT_SHA,source_report=AUDIT,loc_report=COUNT_PATH,
            loc_expansions=copy.deepcopy(count['packed_owner_lines']),
            original_producer_loc=original['loc'],original_producer_physical_loc=original['physical_loc'],
            algorithm=copy.deepcopy(original['algorithm']),required_work_validated=True,source_work_qualified=True,
            full_workload_qualified=True,eligible_for_publication_review=True,eligible_for_chart=False,chart_admission=False,
            timing_alias_of=None,distinct_optimization_claimed=False,
            source_provenance='Retained R application source with recorded upstream references and local adaptations.',
            upstream_source_url=original.get('source_url'),adaptations=copy.deepcopy(original['adaptations']),
            sample_evidence=dict(kind='original-report-attempts',attempt_numbers=copy.deepcopy(original['attempts']),
                report=reference(REPORT,reconciler.REPORT_SHA),separate_continuation_receipts=[
                    dict(attempt=n,raw='archive/comparisons/'+reconciler.COHORT+'/'+reconciler.CONTINUATION+
                        f'/attempts/{n:03d}-{original["id"]}.json',
                        supervisor='archive/comparisons/'+reconciler.COHORT+'/'+reconciler.CONTINUATION+
                        f'/attempts/{n:03d}-{original["id"]}.supervisor.json') for n in original['attempts'] if n>=88]),
            timing_boundary=review['timing_boundary'],timing_measurement=dict(kind='full-process-wall',samples=3,
                includes=['startup','runtime/source preparation','workers','computation','output','shutdown']),
            runtime_policy='GNU R 4.6.1 · ARM64 · bytecode JIT enabled',execution_mode='interpreted',
            runtime=copy.deepcopy(original['runtime']),runtime_arguments=copy.deepcopy(original['command']),
            runtime_environment=copy.deepcopy(original['runtime_environment']),maximum_workers=original['maximum_workers'],
            matched_mech_control=copy.deepcopy(control),
            mech_comparison=dict(scope='paired-control',control_key=control['key'],seconds=control['seconds'],
                samples_seconds=copy.deepcopy(control['samples']),time_x_mech=original['median_seconds']/control['seconds']),
            provenance_limitations=copy.deepcopy(review['limitations']))
    for benchmark in reconciler.BENCHES:
        rows=[row for row in inventory.values() if row['benchmark']==benchmark]
        require(len(rows)==2,'Two distinct retained source forms per workload required')
        fast=min(rows,key=lambda x:(x['seconds'],x['loc'],x['key']))
        small=min(rows,key=lambda x:(x['loc'],x['seconds'],x['key']))
        endpoints[benchmark]=dict(language='r',label='R',fast=fast['key'],small=small['key'],
            programs=list(dict.fromkeys([fast['key'],small['key']])),formatted_fast=None,formatted_small=None)
    return dict(schema='r-retained-three-workload-publication-candidate-v1',
        status='validated-retained-observations-awaiting-publication-review',
        program_inventory=inventory,files=files,matched_mech_controls=controls,endpoints=endpoints,
        source_forms=6,subject_samples=18,matched_control_samples=9,native_processes_started=0,
        report=reference(REPORT,reconciler.REPORT_SHA),source_audit=reference(AUDIT,reconciler.AUDIT_SHA),
        source_counts=reference(COUNT_PATH,reconciler.COUNTS_SHA),
        historical_reports_mutated=False,chart_admission=False,dataset_files_changed=False)


def export(args):
    r=module('r_retained_closed_consumer','r_retained_reconcile.py',RECONCILER_SHA)
    writer=module('r_retained_owned_writer','import_uiua_fann.py',WRITER_SHA)
    own=Path(__file__).resolve();digest=hashlib.sha256(own.read_bytes()).hexdigest()
    require(digest==args.tool_sha256,'Explicit exporter source digest differs')
    output=args.output.resolve()
    require(output.is_relative_to(PACKET.resolve()) and not output.exists(),'Fresh packet output directory required')
    owner=writer.OwnedFiles()
    with r.review_files(RECONCILER_SHA,on_exit_failure=owner.remove_all,
                        final_consumer_check=owner.final_check) as (review,files):
        files.verify(own,digest);files.verify(own.with_name('import_uiua_fann.py'),WRITER_SHA)
        sources={key:files.read(ROOT/c['source']['path'],c['source']['sha256']) for key,c in review['canonical_counts'].items()}
        candidate=build_candidate(review,sources,r)
        output.mkdir(parents=True)
        review_bytes=writer.encoded(review)
        owner.write(output/'reconciliation.json',review_bytes)
        candidate['reconciliation']=reference((output/'reconciliation.json').relative_to(ROOT).as_posix(),
            hashlib.sha256(review_bytes).hexdigest())
        candidate['exporter']=reference(own.relative_to(ROOT).as_posix(),digest)
        raw=writer.encoded(candidate);owner.write(output/'candidate.json',raw)
    print(json.dumps(dict(status=candidate['status'],candidate=(output/'candidate.json').as_posix(),
        candidate_sha256=hashlib.sha256(raw).hexdigest(),native_runs=0)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    export(parser.parse_args())


if __name__=='__main__':main()
