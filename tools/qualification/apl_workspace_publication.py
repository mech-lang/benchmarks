"""Pure admission of the complete APL N=21 tree cohort, with no rebasing.

The guarded caller reproduces the six observations and all source/runtime pins.
The optimized label is an explicit source and timing alias, not another run.
"""
import copy
import hashlib
import math
from pathlib import PurePosixPath
import statistics
from urllib.parse import quote

EVIDENCE_ROOT = '/private/tmp/mech-benchmark-completion'
PACKET = 'experiments/apl/binarytrees-workspace-v1/full6-v1'
AUDIT = 'apl_workspace_publication_audit'
SCHEMA = 'apl-workspace-full6-publication-candidate-v1'
SUBJECT = 'binarytrees:apl-workspace200-compact'
ALIAS = 'binarytrees:apl-workspace200-optimized'
CONTROL = 'binarytrees:apl-workspace200-full-study:mech-control'
SOURCE = 'archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl'
SOURCE_SHA = 'd1293d125d2d65940137d2d624402d4931f74d1f031bc2261165ad6663c57e74'
SETUP = 'experiments/apl/binarytrees-workspace-v1/setup.apl'
SETUP_SHA = '3adce52a2aea05cc00ee13e011655749f5a03bc81d37a4ee8eb13c14f227e58c'
RUNTIME_REF = dict(path='experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json',
    sha256='76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6')
RUNTIME_SHA = 'ac9a9e7c4521f3e871fd32143fd50661dd6ea8a7afbde9bbb388cc6786d80836'
LAUNCHER_SHA = '50c937c62df5095151dd766dcbd8bc2058e24a93ccefb6b5b601944a48cdadf4'
BUNDLE = [(SOURCE, SOURCE_SHA, 'application', 40), (SETUP, SETUP_SHA, 'runtime-setup', 1)]
FAILED = [dict(path='experiments/apl/binarytrees-workspace-v1/'+path,sha256=digest) for path,digest in (
    ('bounded-run-v1/report.json','daff19879de9ab9e7b30574a29195224340b24a9f7b3e080baa0b5f539335388'),
    ('remaining-three-v1/run-v1/report.json','98a72540c56d68d8ef45c51aa77d4b8c6054ed2513396a1504d0bd85e27b210b'))]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def safe_path(name):
    path = PurePosixPath(name)
    require(type(name) is str and name and not path.is_absolute() and '..' not in path.parts
            and '\\' not in name and str(path) == name, 'Portable exact evidence path required')
    return name


def public_ref(ref):
    name = ref['path']
    if name.startswith(EVIDENCE_ROOT + '/'):
        name = name[len(EVIDENCE_ROOT)+1:]
    safe_path(name)
    digest = ref['sha256']
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
            'Exact evidence digest required')
    return dict(path=name, sha256=digest)


def portable(value):
    if type(value) is list:
        return [portable(item) for item in value]
    if type(value) is dict:
        result = {key: portable(item) for key, item in value.items()}
        if type(value.get('path')) is str and type(value.get('sha256')) is str:
            name = value['path']
            if not name.startswith('/') or name.startswith(EVIDENCE_ROOT+'/'):
                result.update(public_ref(value))
        return result
    return value


def measured(profile):
    samples = profile['samples_seconds']
    require(len(samples) == 3 and all(positive(v) for v in samples)
            and statistics.median(samples) == profile['median_seconds']
            and math.isclose(statistics.stdev(samples),profile['sample_stdev_seconds'],rel_tol=1e-12,abs_tol=1e-12)
            and profile['native_observations'] == 3 and profile['full_workload_qualified'] is True
            and len(profile['sample_evidence']) == len(profile['sample_execution_metadata']) == 3,
            'Three distinct closed observations and their metadata are required')
    return copy.deepcopy(samples)


def build_candidate(review, sources, counts, work, runtime, refs):
    require(review['schema'] == 'apl-workspace-independent-full6-reconciliation-v1'
            and review['status'] == 'six-full-process-observations-file-verified-awaiting-publication'
            and review['file_integrity_verified'] is review['common_mutex_held'] is True
            and review['source_work_qualified'] is review['canonical_loc_qualified'] is True
            and review['actual_full_native_processes'] == 6
            and review['subject_native_observations'] == review['control_native_observations'] == 3
            and review['chart_admission'] is False, 'Independent six-observation file review required')
    require(review['source_aliases'] == [dict(key=ALIAS,variant='optimized',source_alias_of=SUBJECT,
            timing_alias_of=SUBJECT,additional_native_processes=0,optimization_claim=False)]
            and portable(review['preserved_failed_reports']) == FAILED, 'Alias or preserved failure scope differs')
    require(set(review['references']) == {'plan','report','terminal','durable'}
            and refs['native_cohort'] == portable(review['references'])
            and refs['report'] == public_ref(review['references']['report'])
            and refs['source_counts'] == public_ref(review['source_counts'])
            and refs['source_work'] == public_ref(review['source_work'])
            and counts == review['qualified_source_counts'] and work == review['qualified_source_work'],
            'Exact native cohort and independent qualification bindings required')
    profiles = review['profiles']
    require(set(profiles) == {SUBJECT, CONTROL}, 'Alias must not become a third native profile')
    subject, control = profiles[SUBJECT], profiles[CONTROL]
    row = subject['original_profile']
    require(row['key'] == SUBJECT and row['language'] == 'apl' and row['variant'] == 'compact'
            and row['source_sha256'] == SOURCE_SHA and row['loc'] == row['canonical_loc'] == row['physical_loc'] == 41
            and row['setup_inside_timer'] is True and row['maximum_workers'] == 1,
            'Exact counted source and timed setup required')
    require(counts['schema'] == 'apl-binarytrees-workspace-qualified-source-counts-v1'
            and counts['canonical_LOC_admitted'] is True and counts['canonical_loc'] == counts['physical_loc'] == 41
            and counts['formatted_loc'] is None and counts['formatted_loc_qualified'] is False
            and counts['setup_assignment_included'] is True, 'Qualified 40+1 source units required')
    expected_bundle = [dict(path=path, sha256=digest, canonical_loc=units, physical_loc=units)
                       for path, digest, _, units in BUNDLE]
    require(counts['source_bundle'] == expected_bundle
            and portable(row['source_count_review']) == refs['source_counts']
            and portable(row['required_work_review']) == refs['source_work']
            and public_ref(work['source_counts']) == refs['source_counts']
            and work['schema'] == 'apl-binarytrees-workspace-required-work-v1'
            and work['source_work_qualified'] is True and work['workload_n'] == 21
            and work['source_sha256'] == SOURCE_SHA and work['setup_sha256'] == SETUP_SHA
            and work['workspace_scale'] == 200 and work['previous_failures_preserved'] is True,
            'Independent source/count/work references differ')
    require(runtime['schema'] == 'apl-retained-runtime-publication-scope-review-v1'
            and runtime['runtime_publication_metadata_qualified'] is True
            and refs['runtime_metadata_basis'] == RUNTIME_REF
            and runtime['runtime']['sha256'] == row['runtime_binary']['sha256'] == RUNTIME_SHA
            and runtime['runtime']['path'] == row['runtime_binary']['path']
            and row['binary_sha256'] == LAUNCHER_SHA,
            'The exact previously reviewed interpreter image and launcher are required')
    require(row['command'] == [row['binary'], '--cc', '1', '-f', EVIDENCE_ROOT+'/'+SETUP,
                              '-f', row['source'], '--', '{n}'], 'Timed setup/source invocation changed')
    for path, digest in runtime['required_inherited_pins'].items():
        require(review['verified_file_pins'].get(path) == digest, 'Unverified retained runtime dependency')
    require(set(sources) == {SOURCE_SHA, SETUP_SHA}, 'Complete application and setup source required')
    files, roles = {}, {}
    for path, digest, role, units in BUNDLE:
        raw = sources[digest]
        require(sha(raw) == digest, 'Exact authored source differs')
        files[digest] = dict(path=path, archive_path=path, name=PurePosixPath(path).name,
                             sha256=digest, code=raw.decode('utf-8'))
        roles[digest] = dict(role=role, source_path=path, normalized_loc=units, physical_loc=units,
                            formatted_loc=None, source_owner_review=refs['source_counts'])
    samples, control_samples = measured(subject), measured(control)
    matched = dict(key=CONTROL, samples=control_samples, seconds=control['median_seconds'],
        timing_sd=statistics.stdev(control_samples), sample_evidence=portable(control['sample_evidence']),
        sample_execution_metadata=copy.deepcopy(control['sample_execution_metadata']),
        original_profile=copy.deepcopy(control['original_profile']), native_observations=3,
        report=refs['report'])
    base = dict(key=SUBJECT, id='apl-binarytrees-workspace200-compact', language='apl', benchmark='binarytrees',
        variant='compact', files=[SOURCE_SHA, SETUP_SHA], file_roles=roles, source_sha256=SOURCE_SHA,
        source_path=SOURCE, loc=41, canonical_loc=41, physical_loc=41, loc_metric='canonical-source-units',
        canonical_loc_qualified=True, formatted_loc=None, formatted_x=None, formatted_loc_qualified=False,
        formatted_loc_complete=False, formatted_loc_status='unavailable', loc_expansions=[],
        samples=samples, seconds=subject['median_seconds'], timing_sd=statistics.stdev(samples),
        sample_evidence=portable(subject['sample_evidence']),
        sample_execution_metadata=copy.deepcopy(subject['sample_execution_metadata']),
        report=refs['report']['path'], report_sha256=refs['report']['sha256'],
        loc_report=refs['source_counts']['path'], loc_report_sha256=refs['source_counts']['sha256'],
        source_work_evidence=refs['source_work'], source_work_qualified=True, required_work_validated=True,
        full_workload_qualified=True, native_observations=3, source_alias_of=None, timing_alias_of=None,
        aliased_sample_source=None, distinct_optimization_claimed=False, setup_inside_timer=True,
        runtime=copy.deepcopy(runtime['runtime']), runtime_arguments=copy.deepcopy(row['command']),
        runtime_environment=copy.deepcopy(row['runtime_environment']), execution_mode='interpreted',
        runtime_policy='GNU APL 2.0 · native ARM64 interpreter · serial numerical primitives on macOS',
        memory_policy=row['memory_policy'], workspace_scale=200, maximum_workers=1,
        numerical_primitive_parallelism_enabled=False, runtime_publication_metadata_qualified=True,
        runtime_metadata_basis=refs['runtime_metadata_basis'],
        runtime_metadata_scope='Identical retained image, launcher and recorded static dependencies; '
                               'the prior profile-specific approval is not extended to this new source.',
        per_process_loaded_images_qualified=False, complete_transitive_os_inventory_qualified=False,
        matched_mech_control=matched, mech_comparison=dict(scope='paired-control', control_key=CONTROL,
            seconds=matched['seconds'], samples_seconds=control_samples, time_x_mech=subject['median_seconds']/matched['seconds']),
        timing_boundary='Fresh process including startup, source parsing, workspace assignment, all N=21 work, output and shutdown.',
        eligible_for_publication_review=True, eligible_for_chart=False, chart_admission=False)
    alias = copy.deepcopy(base)
    alias.update(key=ALIAS, id='apl-binarytrees-workspace200-optimized', variant='optimized', native_observations=0,
                 source_alias_of=SUBJECT, timing_alias_of=SUBJECT, aliased_sample_source=SUBJECT)
    result = dict(schema=SCHEMA, status='validated-six-observations-awaiting-publication',
        files=files, program_inventory={SUBJECT:base, ALIAS:alias}, matched_mech_controls={'binarytrees':matched},
        source_forms=2, distinct_subject_sources=1, counted_physical_files=2, timing_aliases=1,
        subject_native_observations=3, control_native_observations=3, source_units=41,
        endpoints={'binarytrees':endpoint()}, previous_failures=portable(review['preserved_failed_reports']),
        chart_admission=False, dataset_files_changed=False, historical_reports_mutated=False,
        native_processes_started=0, **copy.deepcopy(refs))
    validate_candidate(result)
    return result


def endpoint():
    return dict(language='apl', label='APL (GNU APL)', fast=SUBJECT, small=SUBJECT,
                programs=[SUBJECT], formatted_fast=None, formatted_small=None)


def validate_candidate(candidate):
    require(candidate['schema'] == SCHEMA and candidate['status'] == 'validated-six-observations-awaiting-publication'
            and candidate['chart_admission'] is candidate['dataset_files_changed'] is candidate['historical_reports_mutated'] is False
            and candidate['native_processes_started'] == 0 and candidate['endpoints'] == {'binarytrees':endpoint()},
            'Wrong tree-only candidate disposition')
    rows = candidate['program_inventory']
    require(set(rows) == {SUBJECT, ALIAS} and set(candidate['files']) == {SOURCE_SHA, SETUP_SHA}
            and candidate['subject_native_observations'] == candidate['control_native_observations'] == 3,
            'Distinct source/control observation accounting changed')
    base = rows[SUBJECT]
    expected = copy.deepcopy(base)
    expected.update(key=ALIAS, id='apl-binarytrees-workspace200-optimized', variant='optimized', native_observations=0,
                    source_alias_of=SUBJECT, timing_alias_of=SUBJECT, aliased_sample_source=SUBJECT)
    require(rows[ALIAS] == expected and base['timing_alias_of'] is base['source_alias_of'] is None
            and base['native_observations'] == 3 and base['loc'] == base['canonical_loc'] == base['physical_loc'] == 41
            and base['setup_inside_timer'] is True and base['files'] == [SOURCE_SHA, SETUP_SHA],
            'Alias or complete source/setup accounting differs')
    for digest, source in candidate['files'].items():
        require(sha(source['code'].encode()) == source['sha256'] == digest, 'Embedded counted source differs')
    for row in rows.values():
        samples = row['samples']
        require(len(samples) == 3 and all(positive(v) for v in samples)
                and row['seconds'] == statistics.median(samples) and row['timing_sd'] == statistics.stdev(samples)
                and row['eligible_for_chart'] is row['chart_admission'] is False,
                'Three full-size samples and unadmitted rows required')
        require(row['source_work_qualified'] is row['required_work_validated'] is row['full_workload_qualified'] is
                row['canonical_loc_qualified'] is row['runtime_publication_metadata_qualified'] is True
                and row['formatted_loc'] is row['formatted_x'] is None
                and row['formatted_loc_qualified'] is False, 'Source/work/runtime/count admission is incomplete')
        require(set(row['file_roles']) == {SOURCE_SHA,SETUP_SHA}, 'Counted file role omitted')
        for path,digest,role,units in BUNDLE:
            item = row['file_roles'][digest]
            require(item['role'] == role and item['source_path'] == path
                    and item['normalized_loc'] == item['physical_loc'] == units,
                    'Counted setup/application role changed')
    require(candidate['previous_failures'] == FAILED, 'Earlier unqualified outcomes must remain preserved')


def aggregate(data, reference, kind, axis):
    values = []
    for bench in data['benchmarks']:
        if bench['key'] in reference['measured_benchmarks']:
            groups = [g for g in bench['groups'] if g['language'] == 'apl']
            require(len(groups) == 1, 'Exactly one APL endpoint per admitted workload required')
            values.append(data['programs'][groups[0][kind]][axis])
    require(len(values) == len(reference['measured_benchmarks']) and all(positive(v) for v in values),
            'Incomplete APL aggregate')
    return statistics.geometric_mean(values)


def build_publication(original, original_languages, candidate, candidate_ref):
    validate_candidate(candidate)
    require(AUDIT not in original, 'Tree cohort already admitted')
    candidate_ref = public_ref(candidate_ref)
    data, languages = copy.deepcopy(original), copy.deepcopy(original_languages)
    benches = {b['key']:b for b in data['benchmarks']}
    require(len(benches) == len(data['benchmarks']) == 10 and 'binarytrees' in benches, 'Exact ten-workload catalog required')
    previous = set(benches)-{'binarytrees'}
    entries = [e for e in data['languages'] if e['key'] == 'apl']
    references = [e for e in data['reference_summary'] if e['lang'] == 'apl']
    require(len(entries) == 1 and len(references) <= 1 and 'apl' in languages['languages']
            and set(entries[0]['timed_benchmarks']) == previous
            and all(sum(g['language'] == 'apl' for g in benches[b]['groups']) == 1 for b in previous)
            and not any(g['language'] == 'apl' for g in benches['binarytrees']['groups']),
            'Preserved nine-workload APL coverage with no existing tree endpoint required')
    if references:
        require(set(references[0]['measured_benchmarks']) == previous, 'Prior APL aggregate coverage differs')
    bench = benches['binarytrees']
    require(positive(bench['baseline_loc']) and positive(bench['baseline_seconds'])
            and 41 >= bench['baseline_loc'] and candidate['program_inventory'][SUBJECT]['seconds'] >= bench['baseline_seconds'],
            'New LOC or time minimum requires separate normalization review')
    for digest, source in candidate['files'].items():
        if digest in data['files']:
            require(data['files'][digest]['code'] == source['code'], 'Retained source collision')
        else:
            data['files'][digest] = copy.deepcopy(source)
    for key, source in candidate['program_inventory'].items():
        require(key not in data['programs'] and key not in data['program_inventory'], 'Tree source already present')
        row = copy.deepcopy(source)
        row.update(eligible_for_chart=True, chart_admission=dict(candidate=candidate_ref, source_counts_independently_reviewed=True),
            source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(SOURCE),
            source_link_label='Exact retained source and counted setup', local_adaptation=True,
            x=row['loc']/bench['baseline_loc'], y=row['seconds']/bench['baseline_seconds'])
        row['publication_record'] = copy.deepcopy(row)
        data['program_inventory'][key] = row
    data['programs'][SUBJECT] = copy.deepcopy(data['program_inventory'][SUBJECT])
    bench['groups'].append(endpoint())
    for field in ('timed_benchmarks', 'source_benchmarks'):
        entries[0][field] = [b['key'] for b in data['benchmarks'] if b['key'] in set(entries[0][field])|{'binarytrees'}]
    prior = copy.deepcopy(references[0]) if references else None
    reference = copy.deepcopy(prior) if prior else dict(lang='apl', label='APL (GNU APL)')
    reference['measured_benchmarks'] = [b['key'] for b in data['benchmarks']]
    for kind in ('fast', 'small'):
        reference[kind] = {axis:aggregate(data, reference, kind, axis) for axis in ('x', 'y')}
    if references:
        references[0].clear(); references[0].update(reference)
    else:
        data['reference_summary'].append(reference)
    languages['languages']['apl']['displayed_program_count'] = sum(r['language'] == 'apl' for r in data['programs'].values())
    audit = dict(schema='apl-workspace-tree-catalog-admission-v1', status='prepared-qualified-six-observation-cohort',
        language='apl', candidate=candidate_ref, source_forms=2, distinct_subject_sources=1, counted_physical_files=2,
        timing_aliases=1, subject_native_observations=3, control_native_observations=3, endpoints={'binarytrees':endpoint()},
        normalizations=[], aggregate_change=dict(before=prior, after=copy.deepcopy(reference)),
        native_runs=0, historical_reports_mutated=False, old_raw_measurements_changed=False,
        **{k:copy.deepcopy(candidate[k]) for k in ('report','source_counts','source_work','runtime_metadata_basis','reconciliation')})
    data[AUDIT] = audit
    paths = {candidate_ref['path'], SOURCE, SETUP}
    paths.update(candidate[k]['path'] for k in ('report','source_counts','source_work','runtime_metadata_basis','reconciliation'))
    for path in sorted(paths):
        safe_path(path)
        require(data['archive_paths'].get(path, path) == path, 'Evidence mapping collision')
        data['archive_paths'][path] = path
    for pool in ('programs','program_inventory','files'):
        require(all(data[pool][key] == row for key,row in original[pool].items()), 'Old source or measured record changed')
    require(data.get('formatted_reference_summary') == original.get('formatted_reference_summary'), 'Formatted aggregate changed')
    return data, languages, audit
