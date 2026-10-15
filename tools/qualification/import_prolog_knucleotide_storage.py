"""Prepare or explicitly apply a reproduced Prolog publication candidate.

This additive importer supports declared gzip evidence and current target traits.
The default writes a private three-file candidate with exact original backups.
No native program executes. All actual evidence hashing and optional publication
remain inside the metadata review's six continuously held leases.
"""
import argparse
import copy
from contextlib import contextmanager
from datetime import datetime,timezone
import hashlib
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import statistics
import stat
import sys
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[2]
EXPORTER=Path(__file__).with_name('prolog_knucleotide_export.py')
EXPORTER_SHA='9cba58451b6b456caf7574b8b051bffb4705319fac4543d88ec0f8cf5f218e34'
RELEASE=ROOT/'experiments/prolog/full81-linear-v1/release-metadata-v1.json'
RELEASE_SHA='cd66bfd19d6709566b33af0a481b66e5a9efde6cb1e51ed98b70f9928337fde9'
TRAITS=ROOT/'site/src/traits.mjs'
TRAITS_SHA='c0e82551949568f0247aa289b7d8e39ac7c9497368c9e6f7321b9dd94a0af87f'
TARGETS=('data/benchmarks.json','data/languages.json','site/src/languages.mjs')
META_FIELDS=('platform','runtime','execution','typing','style','memory','note','sources')
raw=EXPORTER.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPORTER_SHA:raise ValueError('Frozen Prolog exporter changed')
spec=importlib.util.spec_from_file_location('prolog_import_exporter',EXPORTER)
e=importlib.util.module_from_spec(spec);exec(compile(raw,str(EXPORTER),'exec'),e.__dict__)
m,l,r,p,require,same=e.m,e.l,e.r,e.p,e.require,e.same


TARGET_HELPER=Path(__file__).with_name('import_prolog_publication_target.py')
TARGET_HELPER_SHA='0ac16c8c401f5fc279e5fd09f8c42457002b789a1b9946baf1427d57e18be849'
h=m.module(TARGET_HELPER,TARGET_HELPER_SHA)
PACKET_REL='experiments/prolog/full36-knucleotide-v1'
IMPORTER_REL='tools/qualification/import_prolog_knucleotide_storage.py'
ORIGINAL_IMPORTER=ROOT/'tools/qualification/import_prolog_knucleotide.py'
ORIGINAL_IMPORTER_SHA='16af22803d6ac8d2399549bcc88be59b5b0dba14dc5e31fffe1fa0a5c526dee1'
STORAGE_REL='experiments/prolog/qualified-original22-v2/storage-manifest.json'
STORAGE_SHA='3538de1dfd61b923970c81db881342cf8ff15cb45c691817ce73433a7c9c1340'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def positive(value):return type(value) in (int,float) and math.isfinite(value) and value>0


def public_ref(binding,root=ROOT):
    path=Path(binding['path'])
    require(path.is_absolute() and '..' not in path.parts and p.digest(binding['sha256'])
            and path.is_relative_to(root) and path.resolve().is_relative_to(root),'Unretained public evidence reference')
    relative=path.relative_to(root).as_posix()
    item=storage_entries().get(relative)
    if item is not None:
        require(binding['sha256']==item['original_sha256'],'Logical evidence identity differs')
        return dict(path=item['stored_path'],sha256=item['stored_sha256'],storage_encoding='gzip',
            logical_path=relative,original_sha256=item['original_sha256'],original_bytes=item['original_bytes'],
            stored_bytes=item['stored_bytes'],storage_manifest=dict(path=STORAGE_REL,sha256=STORAGE_SHA))
    return dict(path=relative,sha256=binding['sha256'])


def public_refs(value,root=ROOT):
    if type(value) is list:return [public_refs(x,root) for x in value]
    if type(value) is dict:
        result={k:public_refs(v,root) for k,v in value.items()}
        if type(value.get('path')) is str and p.digest(value.get('sha256')):
            path=Path(value['path'])
            if path.is_absolute() and path.is_relative_to(root):result.update(public_ref(value,root))
        return result
    return value


def validate_candidate(candidate):
    require(candidate['schema']==e.SCHEMA
            and candidate['status']=='validated-evidence-candidate-awaiting-explicit-publication-review'
            and candidate['chart_admission'] is candidate['dataset_files_changed'] is False
            and p.integer(candidate['native_processes_started'],0)
            and p.integer(candidate['reused_qualified_samples'],54)
            and p.integer(candidate['original_regex_samples'],9) and p.integer(candidate['retained_linear_samples'],31)
            and p.integer(candidate['excluded_original_attempt'],10)
            and p.integer(candidate['retained_remaining_samples'],14)
            and p.integer(candidate['excluded_remaining50_attempt'],15),'Candidate scope differs')
    meta=candidate['language_metadata']
    require(meta['key']==meta['family']=='prolog' and meta['label']=='Prolog' and meta['platform']=='runtime'
            and meta['execution']==['interpreted'] and meta['typing']=='dynamic' and meta['style']==['logic']
            and meta['memory']==['gc'] and meta['runtime_publication_metadata_qualified'] is True
            and meta['chart_admission'] is False and meta['observed_in_each_timed_process'] is False
            and meta['gc_numeric_defaults_claimed'] is False,'Reviewed SWI bytecode taxonomy required')
    expected={b+':prolog-'+b+('-linear' if b=='revcomp' else '')+'-'+v for b in r.BENCHES for v in ('compact','optimized')}
    require(set(candidate['program_inventory'])==expected
            and set(candidate['matched_mech_controls'])==set(candidate['endpoint_proposals'])==set(r.BENCHES),
            'Exact twenty source profiles and ten controls required')
    same(candidate['prior_producer_statuses'],{'original-full90':'stopped-unqualified','linear-full81':'stopped-unqualified','linear-remaining50':'stopped-unqualified'},
         'Stopped producer statuses changed')
    require(set(candidate['cohorts'])=={'original-full90','linear-full81','linear-remaining50','knucleotide-remaining36'},'Four actual cohort identities required')
    excluded=[];samples=[]
    for key,row in candidate['program_inventory'].items():
        require(row['key']==row['receipt_key']==key==row['benchmark']+':'+row['id'] and row['language']=='prolog'
                and row['chart_admission'] is False and row['distinct_optimization_claimed'] is False
                and row['timing_alias_of'] is None,'Profile identity or alias policy differs')
        require(row['source_work_qualified'] is row['canonical_loc_qualified'] is True
                and row['formatted_loc_qualified'] is False and row['formatted_loc'] is None,
                'Source work/canonical-only gates differ')
        roles=row['file_roles']
        require(len(row['files'])==len(set(row['files']))==len(roles) and set(row['files'])==set(roles)
                and sum(v['role']=='application' for v in roles.values())==1
                and all(v['role'] in ('application','application-helper') for v in roles.values()),'Authored bundle differs')
        for field,role_field in (('loc','normalized_loc'),('physical_loc','physical_loc')):
            values=[v[role_field] for v in roles.values()]
            require(all(type(v) is int and v>0 for v in values) and row[field]==sum(values),'Authored count total differs')
        require(row['canonical_loc']==row['loc'] and all(v['formatted_loc'] is None for v in roles.values()),'Count metric differs')
        alias=row['source_alias_of']
        if row['variant']=='optimized':
            base=row['id'].removesuffix('-optimized')+'-compact'
            require(alias==base and candidate['program_inventory'][row['benchmark']+':'+base]['source_sha256']==row['source_sha256'],
                    'Alias source identity differs')
        else:require(row['variant']=='compact' and alias is None,'Unknown source form')
        control=candidate['matched_mech_controls'][row['benchmark']]
        require(control['key']==row['matched_mech_control_key']==row['benchmark']+':prolog-full-study:mech-control'
                and control['language']=='mech','Matched control identity differs')
        success,control_ok=row['full_workload_qualified'],control['full_workload_qualified']
        require(type(success) is type(control_ok) is bool and row['matched_control_qualified'] is control_ok
                and row['eligible_for_publication_review'] is (success and control_ok),'Eligibility differs')
        if success:
            median,sd=p.three_statistics(row['samples'])
            require(row['seconds']==median and math.isclose(row['timing_sd'],sd,rel_tol=1e-12,abs_tol=1e-12),
                    'Subject timing statistics differ')
        else:require(row['seconds'] is row['timing_sd'] is row['time_ratio_to_matched_mech'] is None
                     and row['failed_attempt'] is not None,'Failed subject promoted')
        if success and control_ok:
            median,_=p.three_statistics(control['samples_seconds'])
            require(control['median_seconds']==median and row['time_ratio_to_matched_mech']==row['seconds']/median,
                    'Matched-control statistics differ')
        else:
            require(row['time_ratio_to_matched_mech'] is None,'Failed control/subject has a ratio');excluded.append(row['id'])
        observations=row['sample_execution_metadata'];samples.extend(observations)
        same(row['attempt_cohorts'],list(dict.fromkeys(x['attempt_cohort'] for x in observations)),
             'Profile cohort inventory differs')
        same([x['seconds'] for x in observations if x['qualified']],row['samples'],'Sample values differ')
        same([x['attempt'] for x in observations if not x['qualified']],[] if success else [row['failed_attempt']],
             'Failure sample evidence differs')
    same(sorted(excluded),sorted(candidate['excluded_profiles']),'Excluded profile inventory differs')
    for control in candidate['matched_mech_controls'].values():
        observations=control['sample_execution_metadata'];samples.extend(observations)
        same([x['seconds'] for x in observations if x['qualified']],control['samples_seconds'],'Control samples differ')
    identities=[(x['attempt_cohort'],x['attempt']) for x in samples]
    require(len(set(identities))==len(identities)==candidate['actual_full_native_processes']
            and sum(x['qualified'] for x in samples)==candidate['qualified_samples'],'Sample/cohort accounting differs')
    require(sum(cohort=='original-full90' for cohort,_ in identities)==9
            and sum(cohort=='linear-full81' for cohort,_ in identities)==31
            and sum(cohort=='linear-remaining50' for cohort,_ in identities)==14
            and sum(cohort=='knucleotide-remaining36' for cohort,_ in identities)==candidate['new_full_native_processes']
            and candidate['actual_full_native_processes']==candidate['new_full_native_processes']+54
            and candidate['total_native_processes_including_cancelled']==candidate['actual_full_native_processes']+2,
            'Preserved/new sample counts differ')
    require({number for cohort,number in identities if cohort=='original-full90'}==set(range(1,10))
            and {number for cohort,number in identities if cohort=='linear-full81'}==set(range(1,32))
            and {number for cohort,number in identities if cohort=='linear-remaining50'}==set(range(1,15))
            and {number for cohort,number in identities if cohort=='knucleotide-remaining36'}==set(range(1,candidate['new_full_native_processes']+1)),
            'Actual attempt inventory differs')
    for sample in samples:
        cohort=candidate['cohorts'][sample['attempt_cohort']]
        for name in ('plan','report','terminal'):same(sample['producer_'+name],cohort[name],'Sample producer provenance differs')
        require(sample['producer_status']==cohort['status'],'Actual producer status differs')
        if sample['attempt_cohort']!='knucleotide-remaining36':
            require(cohort['status']=='stopped-unqualified' and sample['qualified'] is True,'Stopped producer or retained qualification changed')
    require(candidate['cohorts']['linear-remaining50']['actual_native_processes']==15
            and candidate['cohorts']['linear-remaining50']['excluded_attempts']==[15]
            and candidate['cohorts']['linear-remaining50']['preserved_qualified_samples']==14,
            'Cancelled prior attempt must remain recorded and excluded')
    used={digest for row in candidate['program_inventory'].values() for digest in row['files']}
    require(used==set(candidate['files']),'Unowned authored source')
    for digest,source in candidate['files'].items():
        require(source['sha256']==digest==sha(source['code'].encode('utf-8')),'Source bytes differ')


def build_publication(originals,candidate,release,refs,plan,root=ROOT):
    validate_candidate(candidate)
    require(release['schema']=='prolog-publication-release-metadata-v1' and release['language']=='prolog'
            and p.integer(release['release_year'],1972) and release['chart_admission'] is False,'Reviewed language-origin record required')
    data,languages=(p.strict_json(originals[name]) for name in TARGETS[:2])
    match=re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',originals[TARGETS[2]].decode('utf-8'),re.S)
    require(match is not None,'Unexpected taxonomy module syntax');module=p.strict_json(match[2]);before=copy.deepcopy(data)
    require('prolog' not in {x['key'] for x in data['languages']} and 'prolog' not in languages['languages']
            and 'prolog' not in module and 'prolog_audit' not in data,'Prolog already admitted')
    require(not any(x['language']=='prolog' for pool in ('programs','program_inventory') for x in data[pool].values()),
            'Prolog programs already present')
    require({b['key'] for b in data['benchmarks']}==set(r.BENCHES),'Workload cohort differs')
    public=public_refs(candidate,root);meta=public['language_metadata']
    for digest,source in public['files'].items():
        source['path']=source['archive_path'];path=Path(source['path'])
        require(not path.is_absolute() and '..' not in path.parts and (root/path).resolve().is_relative_to(root),'Unsafe source path')
        if digest in data['files']:same(data['files'][digest]['code'],source['code'],'Source hash collision')
        else:data['files'][digest]=source
        data['archive_paths'].setdefault(source['path'],source['archive_path'])
    links=[*refs.values(),*(cohort[name] for cohort in public['cohorts'].values() for name in ('plan','report','terminal'))]
    for binding in links:
        name=binding['path'];require(not Path(name).is_absolute() and '..' not in Path(name).parts,'Nonportable review link')
        require(data['archive_paths'].get(name,name)==name,'Archive mapping conflicts');data['archive_paths'][name]=name
    endpoints={};admitted=[]
    for bench in data['benchmarks']:
        name=bench['key'];rows=[];control=public['matched_mech_controls'][name]
        for variant in ('compact','optimized'):
            key=name+':prolog-'+name+('-linear' if name=='revcomp' else '')+'-'+variant
            row=copy.deepcopy(public['program_inventory'][key]);eligible=row['eligible_for_publication_review']
            require(key not in data['program_inventory'] and key not in data['programs'],'Existing program identity')
            require(positive(bench['baseline_loc']) and positive(bench['baseline_seconds']),'Invalid existing baseline')
            if eligible:require(row['loc']>=bench['baseline_loc'] and row['seconds']>=bench['baseline_seconds'],
                                'New Prolog minimum requires a separately reviewed baseline update: '+key)
            main=next(v for v in row['file_roles'].values() if v['role']=='application')['retained_source']
            producer=dict(report=refs['reconciliation'])
            row.update(eligible_for_chart=eligible,required_work_validated=True,
                chart_admission=dict(independent_candidate=refs['candidate'],reconciliation=refs['reconciliation'],
                    runtime_metadata=refs['metadata'],historical_reports_unchanged=True) if eligible else False,
                original_admission_policy=dict(candidate_chart_admission=False,program_chart_admission=False,
                    runtime_chart_admission=False,eligible_for_publication_review=eligible),
                report=producer['report']['path'],report_sha256=producer['report']['sha256'],
                sample_producer_cohorts={cohort:copy.deepcopy(public['cohorts'][cohort]) for cohort in row['attempt_cohorts']},
                loc_report=row['canonical_source_evidence']['path'],source_report=row['canonical_source_evidence']['path'],
                loc_expansions=[],formatted_loc_status='not-qualified',formatted_loc_complete=False,
                formatted_loc_evidence=None,runtime_policy=meta['runtime_policy'],memory_policy=meta['memory_policy'],
                runtime_support='SWI library(pcre), bundled PCRE2 10.40, jit(false)' if name=='regexredux' else 'Retained SWI-Prolog runtime',
                runtime_evidence=copy.deepcopy(meta),runtime_evidence_scope=meta['evidence_scope'],
                runtime_gc_configuration_observed=True,gc_numeric_defaults_claimed=False,timing_boundary=plan['timing_policy'],
                timing_summary='Median of three qualified full fresh-process samples, including startup, QLF loading, input, work, output and shutdown. Failed forms retain no median.',
                source_provenance='Exact retained compiler input and all authored helpers; source work and canonical owners independently qualified.',
                source_provenance_record=dict(source_evidence=main,canonical_source_evidence=row['canonical_source_evidence'],
                    required_work_evidence=row['required_work_evidence'],authored_roles=copy.deepcopy(row['file_roles'])),
                source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(main['path']),
                source_link_label='Exact retained source',local_adaptation=True,matched_mech_control=copy.deepcopy(control),
                full_output_validation=[x['validation'] for x in row['sample_execution_metadata']],
                x=row['loc']/bench['baseline_loc'] if eligible else None,y=row['seconds']/bench['baseline_seconds'] if eligible else None,
                formatted_x=None,measured_backend=dict(key='swi-native-bytecode-vm',execution='interpreted',
                    label=meta['runtime_policy'],verified=True,evidence=dict(verified=True,report=producer['report']['path'],
                        report_sha256=producer['report']['sha256'],command=row['command'],source_sha256=row['files'],
                        runtime_receipt=dict(verified=True,report=refs['metadata']['path'],report_sha256=refs['metadata']['sha256'],
                            field='/application_execution',value='bytecode/QLF',value_encoding='literal-saved-string'))))
            row['publication_record']=copy.deepcopy(row);data['program_inventory'][key]=row
            if eligible:rows.append(row)
        proposal=candidate['endpoint_proposals'][name]
        if not rows:
            same(proposal,dict(fast=None,small=None,programs=[],chart_admission=False),'Excluded endpoint proposal differs')
            endpoints[name]=dict(fast=None,small=None,formatted_fast=None,formatted_small=None,programs=[]);continue
        fast=min(rows,key=lambda x:(x['seconds'],x['loc'],x['key']));small=min(rows,key=lambda x:(x['loc'],x['seconds'],x['key']))
        same(proposal,dict(fast=fast['key'],small=small['key'],programs=list(dict.fromkeys([small['key'],fast['key']])),chart_admission=False),
             'Endpoint proposal differs')
        selected=list(dict.fromkeys([fast['key'],small['key']]))
        data['programs'].update({key:data['program_inventory'][key] for key in selected})
        endpoint=dict(fast=fast['key'],small=small['key'],formatted_fast=None,formatted_small=None,programs=selected)
        bench['groups'].append(dict(language='prolog',label='Prolog',**endpoint));endpoints[name]=endpoint;admitted.append(name)
    language=dict(meta,**{key:release[key] for key in ('release_year','release_name','release_source','release_note')})
    module['prolog']={key:copy.deepcopy(language[key]) for key in META_FIELDS}
    data['languages'].append(dict(key='prolog',label='Prolog',family='prolog',color='#c97052',
        **{key:release[key] for key in ('release_year','release_name','release_source','release_note')},
        timed_benchmarks=admitted,source_benchmarks=[b['key'] for b in data['benchmarks']],
        formatted_timed_benchmarks=[],formatted_source_benchmarks=[],runtime_family='runtime',runtime=meta['runtime'],
        execution_modes=['interpreted'],typing='dynamic',execution='Interpreted',line_style='solid',runtime_policy=meta['runtime_policy'],
        paradigms=['logic'],memory_models=['gc'],classification_note=meta['note'],
        coverage_note=f'{len(admitted)}/10 workloads admitted; canonical-only source counts; failed forms/controls have no chart coordinates.'))
    displayed=sum(x['language']=='prolog' for x in data['programs'].values())
    languages['languages']['prolog']=dict(language,displayed_program_count=displayed,measurement_basis=[dict(refs['candidate'],status='independently-reproduced-publication-candidate')])
    languages['audited_on']=datetime.now(timezone.utc).date().isoformat();languages['scope']=str(len(data['languages']))+' measured variants; all classifications explicit.'
    if admitted:
        reference=dict(lang='prolog',label='Prolog',measured_benchmarks=admitted)
        for kind in ('fast','small'):
            rows=[data['program_inventory'][endpoints[name][kind]] for name in admitted]
            reference[kind]={axis:statistics.geometric_mean(x[axis] for x in rows) for axis in ('x','y')}
        data['reference_summary'].append(reference)
    data['protocol']['prolog']=(meta['runtime_policy']+'. Canonical LOC includes every authored compiler input. '
        'Nine original regex, 31 linear-continuation, 14 preserved stopped-prefix and remaining36 observations retain each actual report, attempt index and matched control. '
        'Cancelled reverse-complement and pre-correction knucleotide attempts supply no timing. Identical source aliases retain independent samples. '
        'Runtime observations come from separate probes/preparation. Formatted LOC is unavailable.')
    for group in data['language_groups']:
        if group['key'] in ('interpreted','dynamic','logic'):
            require('prolog' not in group['languages'],'Duplicate filter membership');group['languages'].append('prolog')
    if not any(group['key']=='logic' for group in data['language_groups']):
        data['language_groups'].append(dict(key='logic',label='Logic',languages=['prolog']))
    audit=dict(schema='prolog-four-cohort-publication-import-v1',status='qualified-saved-cohort-prepared',**refs,
        cohorts=public['cohorts'],endpoints=endpoints,imported_program_inventory=20,imported_endpoint_programs=displayed,
        admitted_workloads=admitted,excluded_profiles=candidate['excluded_profiles'],failed_profiles=candidate['failed_profiles'],
        skipped_slots=candidate['skipped_slots'],actual_full_native_processes=candidate['actual_full_native_processes'],
        new_full_native_processes=candidate['new_full_native_processes'],reused_qualified_samples=54,original_regex_samples=9,retained_linear_samples=31,retained_remaining_samples=14,
        excluded_original_attempt=10,excluded_remaining50_attempt=15,
        total_native_processes_including_cancelled=candidate['total_native_processes_including_cancelled'],
        qualified_samples=candidate['qualified_samples'],baseline_changed=False,historical_reports_mutated=False,
        original_producer_chart_flags_preserved=True,native_commands=0,benchmark_runs=0)
    data['prolog_audit']=audit
    for field in ('programs','program_inventory','files','archive_paths'):
        same({key:data[field][key] for key in before[field]},before[field],'Existing '+field+' changed')
    for old,new in zip(before['benchmarks'],data['benchmarks']):
        same(dict(new,groups=[x for x in new['groups'] if x['language']!='prolog']),old,'Existing workload or baseline changed')
    for field in ('languages','reference_summary','formatted_reference_summary'):
        same(data[field][:len(before[field])],before[field],'Existing '+field+' changed')
    same(data['formatted_reference_summary'],before['formatted_reference_summary'],'Canonical-only import changed formatted summary')
    allowed={'programs','program_inventory','files','archive_paths','benchmarks','languages','reference_summary','protocol','language_groups'}
    for key in set(before)-allowed:same(data[key],before[key],'Unrelated dataset value changed')
    require(set(module)==set(languages['languages'])=={x['key'] for x in data['languages']},'Taxonomy keys differ')
    encoded={TARGETS[0]:(json.dumps(data,indent=2,allow_nan=False)+'\n').encode(),
             TARGETS[1]:(json.dumps(languages,indent=2,allow_nan=False)+'\n').encode(),
             TARGETS[2]:(match[1]+json.dumps(module,indent=2,allow_nan=False)+match[3]).encode()}
    return encoded,audit


@contextmanager
def atomic_publication():
    mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
    try:yield
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,mask)


def replace_bytes(path,raw,suffix):
    temporary=path.with_name(path.name+suffix)
    owned=None
    try:
        with temporary.open('xb') as stream:
            info=os.fstat(stream.fileno());owned=(info.st_dev,info.st_ino)
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if owned is not None:
            try:
                info=temporary.lstat()
                if (info.st_dev,info.st_ino)==owned:temporary.unlink()
            except FileNotFoundError:pass


def restore_prepared(root,prepared,originals,journal):
    """Restore every still-owned target before leases close; preserve unrelated edits."""
    errors=[]
    with atomic_publication():
        for name in reversed(journal[:]):
            try:
                current=m.read_regular(h.physical(root/name,root))
                require(current in (prepared[name],originals[name]),'Publication target changed before restoration: '+name)
                if current!=originals[name]:replace_bytes(root/name,originals[name],'.prolog-remaining-restore.tmp')
                journal.remove(name)
            except BaseException as error:errors.append(error)
    if errors:raise BaseExceptionGroup('Publication restoration conflicts',errors)


def verify_written(root,prepared,journal):
    for name in journal:
        require(m.read_regular(h.physical(root/name,root))==prepared[name],'Prepared publication target changed: '+name)


def apply_prepared(root,prepared,originals,pins,verify,journal):
    try:
        for name in TARGETS:
            verify();verify_written(root,prepared,journal);e.checked(root/name,pins[name])
            with atomic_publication():
                journal.append(name)
                replace_bytes(root/name,prepared[name],'.prolog-knucleotide-import.tmp')
        verify();verify_written(root,prepared,journal)
        require(journal==list(TARGETS),'Incomplete publication replacement inventory')
    except BaseException as apply_error:
        try:restore_prepared(root,prepared,originals,journal)
        except BaseException as restoration_error:
            raise BaseExceptionGroup('Publication replacement and restoration both failed',[apply_error,restoration_error])
        raise



def storage_entries():
    raw=h.checked(ROOT/STORAGE_REL,STORAGE_SHA,ROOT)
    manifest=p.strict_json(raw)
    require(manifest['schema']=='declared-exact-gzip-storage-v1'
            and manifest['historical_receipts_unchanged'] is True
            and manifest['original_content_unchanged'] is True,'Declared lossless storage required')
    entries={}
    for item in manifest['artifacts']:
        for field in ('logical_path','stored_path'):
            path=Path(item[field])
            require(not path.is_absolute() and '..' not in path.parts and path.as_posix()==item[field],
                    'Unsafe declared storage path')
        require(item['storage_encoding']=='gzip' and p.digest(item['original_sha256'])
                and p.digest(item['stored_sha256']) and type(item['original_bytes']) is int
                and type(item['stored_bytes']) is int and item['original_bytes']>=0 and item['stored_bytes']>0,
                'Invalid declared storage identity')
        require(item['logical_path'] not in entries,'Duplicate logical storage path')
        entries[item['logical_path']]=item
    return entries


def publication_links(candidate,refs,evidence):
    original=h.collect_publication_links(candidate,refs,evidence)
    entries=storage_entries();result={}
    for name,expected in original.items():
        item=entries.get(name)
        if item is not None:
            require(expected==item['original_sha256'],'Logical publication reference changed')
            name,expected=item['stored_path'],item['stored_sha256']
        require(name not in result or result[name]==expected,'Conflicting stored reference')
        result[name]=expected
    result[STORAGE_REL]=STORAGE_SHA
    result[ORIGINAL_IMPORTER.relative_to(evidence).as_posix()]=ORIGINAL_IMPORTER_SHA
    return result


def checked_physical(path,expected,root):
    raw=m.read_regular(h.physical(path,root))
    require(p.digest(expected) and sha(raw)==expected,'Pinned publication bytes differ')
    return raw


def verify_public_links(links,evidence,publication):
    for relative,expected in links.items():
        require(checked_physical(evidence/relative,expected,evidence)==
                checked_physical(publication/relative,expected,publication),'Public evidence copy differs')
    for item in storage_entries().values():
        if item['stored_path'] in links:
            raw=checked_physical(publication/item['stored_path'],item['stored_sha256'],publication)
            require(len(raw)==item['stored_bytes'],'Stored evidence length differs')
            decoded=gzip.decompress(raw)
            require(len(decoded)==item['original_bytes'] and sha(decoded)==item['original_sha256'],
                    'Decoded evidence identity differs')


class OwnedOutput(h.OwnedOutput):
    def verify(self):
        for path,identity in self.directories.items():
            info=path.lstat()
            require(stat.S_ISDIR(info.st_mode) and (info.st_dev,info.st_ino)==identity,'Private output directory changed')
        for path,(identity,raw,complete) in self.files.items():
            info=path.lstat()
            require(complete and stat.S_ISREG(info.st_mode) and (info.st_dev,info.st_ino)==identity
                    and m.read_regular(path)==raw,'Private output bytes or identity changed')
    def restore(self):
        errors=[]
        with self.atomic():
            for path,(identity,raw,complete) in reversed(list(self.files.items())):
                try:
                    for parent in path.parents:
                        if parent in self.directories:
                            info=parent.lstat()
                            require(stat.S_ISDIR(info.st_mode) and (info.st_dev,info.st_ino)==self.directories[parent],
                                    'Private output ancestor replaced; preserving')
                    info=path.lstat()
                    require(stat.S_ISREG(info.st_mode) and (info.st_dev,info.st_ino)==identity,
                            'Private output replaced; preserving')
                    current=m.read_regular(path)
                    require(current==raw if complete else raw.startswith(current),'Private output edited; preserving')
                    path.unlink();del self.files[path]
                except FileNotFoundError:self.files.pop(path,None)
                except BaseException as error:errors.append(error)
            for path,identity in reversed(list(self.directories.items())):
                try:
                    info=path.lstat()
                    require(stat.S_ISDIR(info.st_mode) and (info.st_dev,info.st_ino)==identity,
                            'Private directory replaced; preserving')
                    path.rmdir();del self.directories[path]
                except FileNotFoundError:self.directories.pop(path,None)
                except BaseException as error:errors.append(error)
        if errors:raise BaseExceptionGroup('Private output restoration conflicts',errors)


def publish(args):
    evidence, publication = h.roots(args.evidence_root, args.publication_root)
    adapter = evidence / IMPORTER_REL
    require(Path(__file__).resolve()==adapter and ROOT==evidence, 'Launch the unchanged consumer from its original evidence root')
    checked_physical(adapter, args.importer_sha256, evidence)
    output = Path(args.output)
    require(output.is_absolute() and '..' not in output.parts and not output.exists()
            and not output.is_symlink() and not output.is_relative_to(evidence)
            and not output.is_relative_to(publication), 'Fresh private output outside both checkouts required')
    h.physical(output.parent, output.parent, directory=True)
    refs = {}
    supplemental = {adapter: args.importer_sha256, TARGET_HELPER: TARGET_HELPER_SHA,
                    EXPORTER: EXPORTER_SHA, RELEASE: RELEASE_SHA,
                    TRAITS: TRAITS_SHA, ORIGINAL_IMPORTER: ORIGINAL_IMPORTER_SHA,
                    evidence/STORAGE_REL: STORAGE_SHA}
    for name in ('candidate', 'metadata', 'reconciliation'):
        path = Path(getattr(args, name))
        require(path.is_relative_to(evidence / PACKET_REL) and not path.is_relative_to(evidence / PACKET_REL / 'run-v1'),
                'Publication evidence outside original additive packet')
        expected = getattr(args, name + '_sha256')
        checked_physical(path, expected, evidence)
        supplemental[path] = expected
        refs[name] = public_ref(e.ref(str(path), expected), evidence)
    refs.update(release=public_ref(e.ref(str(RELEASE), RELEASE_SHA), evidence),
                import_controller=dict(path=IMPORTER_REL, sha256=args.importer_sha256),
                measurement_importer=dict(path=IMPORTER_REL, sha256=args.importer_sha256))
    target_traits=publication/'site/src/traits.mjs'
    checked_physical(target_traits,args.traits_sha256,publication)
    pins = dict(zip(TARGETS, (args.benchmarks_sha256, args.languages_sha256, args.module_sha256)))
    originals, prepared, journal, links, names = {}, {}, [], {}, {}
    owned = OwnedOutput(output, atomic_publication)

    def restore():
        errors = []
        for operation in (lambda: restore_prepared(publication, prepared, originals, journal), owned.restore):
            try:
                operation()
            except BaseException as error:
                errors.append(error)
        if errors:
            raise BaseExceptionGroup('Publication restoration failed', errors)

    def verify():
        checked_physical(target_traits,args.traits_sha256,publication)
        for path, expected in supplemental.items():
            checked_physical(path, expected, evidence)
        for path, identity in names.items():
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity,
                    'Held lease pathname changed')
        verify_public_links(links,evidence,publication)
        verify_written(publication, prepared, journal)
        for name in TARGETS:
            checked_physical(publication / name, sha(prepared[name]) if name in journal else pins[name], publication)
        owned.verify()

    with m.review_context(args.reconciliation, args.reconciliation_sha256,
                             on_exit_failure=restore, final_consumer_check=verify) as fresh:
        try:
            leases = (l.JOB/'owner.lock',l.PREVIOUS_JOB/'owner.lock',l.q.PRIOR_JOB/'owner.lock',
                      l.OLD/'owned-jobs/full90/owner.lock', evidence/'experiments/prolog/prolog-full90.owner.lock', r.LOCK)
            names.update({path: (path.stat().st_dev, path.stat().st_ino) for path in leases})
            document = lambda path, expected: p.strict_json(checked_physical(path, expected, evidence))
            same(document(args.metadata, args.metadata_sha256), fresh, 'Saved metadata did not reproduce')
            review = document(args.reconciliation, args.reconciliation_sha256)
            plan = document(l.PLAN, l.PLAN_SHA)
            stopped = document(l.PREVIOUS_PLAN,l.PREVIOUS_PLAN_SHA)
            prior = document(l.PRIOR_PLAN, l.PRIOR_PLAN_SHA)
            previous = document(*l.OLD_REFS['plan'])
            def read_raw(path, expected):
                require(fresh['verified_file_pins'].get(path) == expected, 'Unverified publication input')
                return e.checked(path, expected)
            candidate = document(args.candidate, args.candidate_sha256)
            rebuilt = e.reproduced_candidate(plan, stopped, prior, previous, review, fresh, read_raw,
                e.ref(str(args.reconciliation), args.reconciliation_sha256),
                e.ref(str(args.metadata), args.metadata_sha256))
            same(candidate, rebuilt, 'Pinned candidate is not the exact independent export')
            release = document(RELEASE, RELEASE_SHA)
            originals.update({name: checked_physical(publication/name, expected, publication) for name, expected in pins.items()})
            values, audit = build_publication(originals, candidate, release, refs, plan, root=evidence)
            prepared.update(values)
            links.update(publication_links(candidate, refs, evidence))
            verify()
            for name, raw in prepared.items():
                owned.write(name, raw)
                owned.write('originals/' + name, originals[name])
            if args.apply:
                apply_prepared(publication, prepared, originals, pins, verify, journal)
            verify()
            receipt = dict(audit, applied=args.apply, evidence_root=str(evidence), publication_root=str(publication),
                adapter=dict(path=IMPORTER_REL, sha256=args.importer_sha256),
                guarded_output_helper=dict(path=str(TARGET_HELPER.relative_to(evidence)),sha256=TARGET_HELPER_SHA),
                supplemental_evidence_pins={str(path): expected for path, expected in supplemental.items()},
                copied_publication_links=links, inputs=pins,
                target_traits=dict(path='site/src/traits.mjs',sha256=args.traits_sha256),
                evidence_storage_manifest=dict(path=STORAGE_REL,sha256=STORAGE_SHA),
                outputs={name: sha(raw) for name, raw in prepared.items()},
                verified_artifact_count=len(fresh['verified_file_pins']),
                evidence_roots_changed=False, historical_receipts_changed=False)
            if args.apply:
                receipt['status'] = 'qualified-saved-cohort-imported'
            owned.write('import-receipt.json', (json.dumps(receipt, indent=2, allow_nan=False)+'\n').encode())
        except BaseException as body_error:
            try:
                restore()
            except BaseException as restoration_error:
                raise BaseExceptionGroup('Publication body and restoration both failed', [body_error, restoration_error])
            raise
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--publication-root', type=Path, required=True)
    for name in ('candidate', 'metadata', 'reconciliation'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    for name in ('importer', 'benchmarks', 'languages', 'module', 'traits'):
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Publication interrupted: ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    receipt = publish(args)
    print(json.dumps({name: receipt[name] for name in ('status', 'applied', 'evidence_root', 'publication_root')}), flush=True)


if __name__ == '__main__':
    main()
