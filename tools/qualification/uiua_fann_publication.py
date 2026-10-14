"""Pure additive Uiua fannkuch v5 catalog preparation and LOC normalization.

The file-phase caller must reproduce the retained-study reconciliation while
holding its common lease. This module never opens a catalog or launches work.
Only the newly established fannkuch minimum changes old chart coordinates;
original source counts, timings, samples and evidence remain byte-equivalent
as JSON values after removing the explicitly audited derived x coordinates.
"""
import copy
import hashlib
import math
from pathlib import Path
import statistics
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = 'fannkuchredux'
ARCHIVE = 'archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5'
REPORT = ARCHIVE+'/full-study/report.json'
REPORT_SHA = 'f5ab40f30c8add188c4e7a0ac87dc7fd18475ff28c5bba8838dc08b10ff71a6c'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive(value):
    return type(value) in (int,float) and math.isfinite(value) and value > 0


def public_ref(ref):
    path = Path(ref['path'])
    require(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts and
            path.resolve().is_relative_to(ROOT.resolve()),
            'Evidence reference is not retained in the repository')
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=ref['sha256'])


def build_candidate(review, source_bytes):
    require(review['schema'] == 'uiua-fann-v5-retained-reconciliation-v1' and
            review['status'] == 'nine-retained-observations-reconciled-awaiting-publication-review' and
            review['file_integrity_verified'] is review['common_mutex_held'] is True and
            review['native_observations'] == 9 and review['native_processes_started'] == 0 and
            review['chart_admission'] is review['dataset_files_changed'] is False and
            review['source_work_qualified'] is review['canonical_loc_qualified'] is True,
            'Closed independently reproduced retained study required')
    require(set(source_bytes) == {'compact','fast'}, 'Exact authored source pair required')
    files, programs = {}, {}
    control = copy.deepcopy(review['matched_control'])
    for attempt in control['sample_execution_metadata']:
        attempt['retained_raw_receipt'] = ARCHIVE+'/full-study/attempts/'+Path(attempt['result_path']).name
        attempt['retained_supervisor_report'] = REPORT
        attempt['retained_supervisor_report_sha256'] = REPORT_SHA
    for variant in ('compact','fast'):
        source = source_bytes[variant]
        count = review['source_counts'][variant]
        row = review['rows']['uiua-'+variant]
        original = review['source_programs'][variant]
        digest = hashlib.sha256(source).hexdigest()
        require(digest == count['source_sha256'] == row['source_sha256'] and
                count['canonical_loc'] == (20 if variant == 'compact' else 21),
                'Independently counted source bytes differ')
        path = ARCHIVE+'/sources/'+variant+'.ua'
        files[digest] = dict(path=path,archive_path=path,name=variant+'.ua',sha256=digest,code=source.decode('utf-8'))
        key = row['key']
        observations = copy.deepcopy(row['sample_execution_metadata'])
        for attempt in observations:
            attempt['retained_raw_receipt'] = ARCHIVE+'/full-study/attempts/'+Path(attempt['result_path']).name
            attempt['retained_supervisor_report'] = REPORT
            attempt['retained_supervisor_report_sha256'] = REPORT_SHA
        programs[key] = dict(key=key,id=key.split(':',1)[1],benchmark=BENCHMARK,language='uiua',
            variant=variant,loc=count['canonical_loc'],canonical_loc=count['canonical_loc'],
            physical_loc=count['original_physical_loc'],loc_metric='canonical-source-units',
            formatted_loc=None,formatted_loc_qualified=False,formatted_loc_complete=False,
            formatted_loc_status='unavailable',formatted_x=None,
            files=[digest],source_sha256=digest,
            file_roles={digest:dict(role='application',source_path=path,
                normalized_loc=count['canonical_loc'],physical_loc=count['original_physical_loc'],
                formatted_loc=None,source_owner_review=public_ref(review['source_owner_review']))},
            samples=copy.deepcopy(row['samples_seconds']),seconds=row['median_seconds'],
            timing_sd=row['sample_stdev_seconds'],sample_execution_metadata=observations,
            full_output_validation=copy.deepcopy(row['sample_validation']),
            report=REPORT,report_sha256=REPORT_SHA,
            source_report=public_ref(review['source_owner_review'])['path'],
            loc_report=public_ref(review['source_owner_review'])['path'],loc_expansions=[],
            algorithm=copy.deepcopy(original['algorithm']),required_work_validated=True,
            source_work_qualified=True,canonical_loc_qualified=True,full_workload_qualified=True,
            eligible_for_publication_review=True,eligible_for_chart=False,chart_admission=False,
            timing_alias_of=None,distinct_optimization_claimed=False,
            source_provenance=original['provenance'],adaptations=copy.deepcopy(original['adaptations']),
            timing_boundary=review['timing_boundary'],
            timing_measurement=dict(kind='full-process-wall',samples=len(row['samples_seconds']),
                includes=['startup','source compilation','workers','computation','output','shutdown']),
            runtime_policy='Uiua 0.19.1 · official native ARM64 interpreter',
            runtime=copy.deepcopy(review['runtime']),runtime_arguments=copy.deepcopy(row['command']),
            runtime_environment=copy.deepcopy(row['runtime_environment']),maximum_workers=8,
            matched_mech_control=copy.deepcopy(control),
            mech_comparison=dict(scope='paired-control',seconds=control['median_seconds'],
                control_key=control['key'],control_loc=59,source=control['source'],source_sha256=control['source_sha256'],
                samples_seconds=copy.deepcopy(control['samples_seconds']),report=REPORT,
                sample_execution_metadata=copy.deepcopy(control['sample_execution_metadata']),
                time_x_mech=row['median_seconds']/control['median_seconds'],control_loc_x_mech=count['canonical_loc']/59))
    return dict(schema='uiua-fann-v5-private-publication-candidate-v1',
        status='validated-retained-study-awaiting-publication-review',
        chart_admission=False,dataset_files_changed=False,native_processes_started=0,
        retained_subject_samples=6,retained_control_samples=3,
        original_report_status='complete',files=files,program_inventory=programs,
        source_counts=copy.deepcopy(review['source_counts']),
        report=public_ref(review['report']),manifest=public_ref(review['manifest']),
        independent_source_approval=public_ref(review['independent_source_approval']),
        prior_independent_reconciliation=public_ref(review['prior_independent_reconciliation']),
        source_owner_review=public_ref(review['source_owner_review']),
        source_candidate_archive=dict(public_ref(review['source_candidate_archive']),
            original_sealed_sha256=review['source_candidate_archive']['original_sealed_sha256'],
            documentation_only_changed_fields=copy.deepcopy(review['source_candidate_archive']['documentation_only_changed_fields']),
            measurement_fields_changed=False),
        canonical_baseline_proposal=dict(benchmark=BENCHMARK,before=31,after=20,
            reason='New independently qualified canonical source minimum; maintain x-best chart semantics.'),
        historical_reports_mutated=False)


def without_derived_x(row):
    result = copy.deepcopy(row)
    result.pop('x',None)
    if type(result.get('publication_record')) is dict:
        result['publication_record'].pop('x',None)
    return result


def normalize_fann_loc(data, before_baseline):
    """Change only canonical x coordinates and affected aggregate x values."""
    bench = next(b for b in data['benchmarks'] if b['key'] == BENCHMARK)
    require(bench['baseline_loc'] == before_baseline == 31, 'Unexpected original fannkuch LOC baseline')
    eligible = [data['programs'][key] for group in bench['groups'] for key in group['programs']
                if data['programs'][key].get('eligible_for_chart') is not False]
    require(eligible and min(p['loc'] for p in eligible) == 20, 'Qualified canonical minimum is not 20')
    bench['baseline_loc'] = 20
    changed = []
    for pool in ('programs','program_inventory'):
        for key,row in data[pool].items():
            if row['benchmark'] != BENCHMARK or not positive(row.get('x')):
                continue
            require(positive(row.get('loc')), 'Positive chart coordinate has no canonical count')
            old = row['x']
            row['x'] = row['loc']/20
            if type(row.get('publication_record')) is dict:
                require(row['publication_record'].get('loc') == row['loc'], 'Publication source count differs')
                row['publication_record']['x'] = row['x']
            changed.append(dict(pool=pool,key=key,before=old,after=row['x']))
    affected = {g['language'] for g in bench['groups']}
    references = []
    for reference in data['reference_summary']:
        language = reference['lang']
        if language not in affected:
            continue
        inputs = []
        selected = reference.get('measured_benchmarks')
        for workload in data['benchmarks']:
            if selected is not None and workload['key'] not in selected:
                continue
            groups = [g for g in workload['groups'] if g['language'] == language]
            require(len(groups) <= 1, 'Duplicate language workload group')
            if groups:
                inputs.append(groups[0])
        require(inputs, 'Aggregate has no retained endpoint inputs')
        for kind in ('fast','small'):
            values = [data['programs'][g[kind]]['x'] for g in inputs]
            require(all(positive(x) for x in values), 'Aggregate input is not a valid coordinate')
            old = reference[kind]['x']
            reference[kind]['x'] = statistics.geometric_mean(values)
            references.append(dict(language=language,kind=kind,before=old,after=reference[kind]['x']))
    return dict(benchmark=BENCHMARK,axis='canonical-loc',before=31,after=20,
        changed_program_coordinates=changed,changed_aggregate_coordinates=references,
        timing_baseline_changed=False,formatted_baselines_changed=False,
        raw_source_counts_changed=False,timing_samples_changed=False,source_or_receipt_bytes_changed=False)


def build_publication(original, original_languages, candidate, candidate_ref):
    """Pure preview; the caller independently reproduces candidate before use."""
    require(candidate['schema'] == 'uiua-fann-v5-private-publication-candidate-v1' and
            candidate['chart_admission'] is candidate['dataset_files_changed'] is False and
            candidate['native_processes_started'] == 0 and candidate['retained_subject_samples'] == 6 and
            candidate['retained_control_samples'] == 3, 'Publication candidate scope differs')
    data, languages = copy.deepcopy(original), copy.deepcopy(original_languages)
    require('uiua_fann_v5_publication_audit' not in data, 'This retained study is already admitted')
    require(set(candidate['program_inventory']) == {
        'fannkuchredux:parallel-study:uiua-compact','fannkuchredux:parallel-study:uiua-fast'},
        'Exact two source identities required')
    benchmark = next(b for b in data['benchmarks'] if b['key'] == BENCHMARK)
    require(not any(g['language'] == 'uiua' for g in benchmark['groups']),
            'Existing Uiua fannkuch endpoints require a separately reviewed selection merge')
    require(benchmark['baseline_loc'] == 31 and positive(benchmark['baseline_seconds']),
            'Expected pre-admission baselines differ')
    for digest,source in candidate['files'].items():
        require(hashlib.sha256(source['code'].encode()).hexdigest() == digest == source['sha256'],
                'Candidate source bytes differ')
        if digest in data['files']:
            require(data['files'][digest]['code'] == source['code'], 'Existing source collision')
        else:
            data['files'][digest] = copy.deepcopy(source)
        data['archive_paths'].setdefault(source['path'],source['path'])
    rows = []
    for key,source in candidate['program_inventory'].items():
        require(key not in data['programs'] and key not in data['program_inventory'], 'Program identity already exists')
        row = copy.deepcopy(source)
        require(row['language'] == 'uiua' and row['benchmark'] == BENCHMARK and row['key'] == key and
                row['canonical_loc'] == row['loc'] == row['physical_loc'] and row['loc'] in (20,21) and
                len(row['samples']) == 3 and all(positive(x) for x in row['samples']) and
                row['seconds'] == statistics.median(row['samples']) and
                row['timing_sd'] == statistics.stdev(row['samples']), 'Candidate count/sample identity differs')
        require(row['seconds'] >= benchmark['baseline_seconds'], 'This change does not authorize a time rebase')
        row.update(eligible_for_chart=True,chart_admission=dict(candidate=candidate_ref,
            retained_samples_reused=True,source_counts_independently_reviewed=True),
            source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(candidate['files'][row['files'][0]]['path']),
            source_link_label='Exact retained source',local_adaptation=True,
            x=row['loc']/benchmark['baseline_loc'],y=row['seconds']/benchmark['baseline_seconds'])
        row['publication_record'] = copy.deepcopy(row)
        data['programs'][key] = row
        data['program_inventory'][key] = copy.deepcopy(row)
        rows.append(row)
    fast = min(rows,key=lambda r:(r['seconds'],r['loc'],r['key']))
    small = min(rows,key=lambda r:(r['loc'],r['seconds'],r['key']))
    endpoint = dict(language='uiua',label='Uiua',programs=list(dict.fromkeys([fast['key'],small['key']])),
        fast=fast['key'],small=small['key'],formatted_fast=None,formatted_small=None)
    benchmark['groups'].append(endpoint)
    normalization = normalize_fann_loc(data,31)
    uiua = next(x for x in data['languages'] if x['key'] == 'uiua')
    for field in ('timed_benchmarks','source_benchmarks'):
        values = set(uiua[field]) | {BENCHMARK}
        uiua[field] = [b['key'] for b in data['benchmarks'] if b['key'] in values]
    inputs = [g for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'uiua']
    require(not any(x['lang'] == 'uiua' for x in data['reference_summary']),
            'Existing Uiua aggregate requires explicit preservation review')
    reference = dict(lang='uiua',label='Uiua',measured_benchmarks=copy.deepcopy(uiua['timed_benchmarks']))
    for kind in ('fast','small'):
        reference[kind] = {axis:statistics.geometric_mean(data['programs'][g[kind]][axis] for g in inputs) for axis in ('x','y')}
    data['reference_summary'].append(reference)
    languages['languages']['uiua']['displayed_program_count'] = sum(p['language'] == 'uiua' for p in data['programs'].values())
    evidence_paths = [candidate_ref['path']]
    for name in ('report','manifest','independent_source_approval','prior_independent_reconciliation','source_owner_review','source_candidate_archive'):
        evidence_paths.append(candidate[name]['path'])
    if 'reconciliation' in candidate:
        evidence_paths.append(candidate['reconciliation']['path'])
    for row in rows:
        evidence_paths.extend(a['retained_raw_receipt'] for a in row['sample_execution_metadata'])
        evidence_paths.extend(a['retained_raw_receipt'] for a in row['matched_mech_control']['sample_execution_metadata'])
    for path in evidence_paths:
        require(not Path(path).is_absolute() and '..' not in Path(path).parts,'Unsafe retained evidence path')
        data['archive_paths'].setdefault(path,path)
    audit = dict(schema='uiua-fann-v5-catalog-admission-v1',status='prepared-qualified-retained-study',
        candidate=candidate_ref,report=candidate['report'],manifest=candidate['manifest'],
        independent_source_approval=candidate['independent_source_approval'],
        prior_independent_reconciliation=candidate['prior_independent_reconciliation'],
        source_owner_review=candidate['source_owner_review'],
        source_candidate_archive=candidate['source_candidate_archive'],
        imported_subject_samples=6,reused_matched_control_samples=3,native_runs=0,
        source_forms=2,aliases=0,endpoint=endpoint,normalization=normalization,
        historical_reports_mutated=False,old_raw_measurements_changed=False)
    data['uiua_fann_v5_publication_audit'] = audit
    for key,row in original['programs'].items():
        require(without_derived_x(data['programs'][key]) == without_derived_x(row), 'Old selected source measurement changed')
        if row['benchmark'] != BENCHMARK:
            require(data['programs'][key] == row,'Unrelated selected program coordinate changed')
    for key,row in original['program_inventory'].items():
        require(without_derived_x(data['program_inventory'][key]) == without_derived_x(row), 'Old inventory measurement changed')
        if row['benchmark'] != BENCHMARK:
            require(data['program_inventory'][key] == row,'Unrelated inventory coordinate changed')
    for key,row in original['files'].items():
        require(data['files'][key] == row, 'Old source bytes/metadata changed')
    for old,new in zip(original['benchmarks'],data['benchmarks']):
        if old['key'] == BENCHMARK:
            require(dict(new,baseline_loc=31,groups=new['groups'][:-1]) == old, 'Unauthorised workload change')
        else:
            require(new == old, 'Unrelated workload changed')
    require(data.get('formatted_reference_summary') == original.get('formatted_reference_summary'), 'Formatted summaries changed')
    require(len(data['languages']) == len(original['languages']),'Language inventory changed')
    for old,new in zip(original['languages'],data['languages']):
        expected = copy.deepcopy(old)
        if old['key'] == 'uiua':
            for field in ('timed_benchmarks','source_benchmarks'):
                expected[field] = uiua[field]
        require(new == expected,'Unrelated language metadata changed')
    expected_languages = copy.deepcopy(original_languages)
    expected_languages['languages']['uiua']['displayed_program_count'] = languages['languages']['uiua']['displayed_program_count']
    require(languages == expected_languages,'Unrelated language catalog metadata changed')
    require(len(data['reference_summary']) == len(original['reference_summary'])+1,'Aggregate inventory changed')
    for old,new in zip(original['reference_summary'],data['reference_summary']):
        expected = copy.deepcopy(old)
        for kind in ('fast','small'):
            expected[kind]['x'] = new[kind]['x']
        require(new == expected,'Existing aggregate timing or metadata changed')
    for key,value in original['archive_paths'].items():
        require(data['archive_paths'][key] == value,'Existing retained evidence mapping changed')
    allowed = {'programs','program_inventory','files','archive_paths','benchmarks','languages','reference_summary'}
    for key in set(original)-allowed:
        require(data[key] == original[key], 'Unrelated catalog field changed: '+key)
    return data,languages,audit
