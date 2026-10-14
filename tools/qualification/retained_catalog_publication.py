"""Pure catalog admission of already reconciled R, GNU APL, Uiua and Lua samples.

The guarded caller must reproduce the exported candidate from saved evidence.
This module does not read catalogs, execute runtimes or create observations.
Only selected endpoints enter programs; every measured form stays in inventory.
"""
import copy
import hashlib
import math
from pathlib import PurePosixPath
import statistics
from urllib.parse import quote


APL_RUNTIME_REVIEW = dict(
    path='experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json',
    sha256='76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6')


SCOPES = {
    'r-retained-three-workload-publication-candidate-v1': dict(
        language='r', label='R', audit_key='r_retained_publication_audit',
        workloads=('nbody', 'binarytrees', 'fannkuchredux'), forms=6, sources=6, aliases=0,
        subjects=18, controls=9, counts='source_counts'),
    'apl-retained-five-workload-publication-candidate-v1': dict(
        language='apl', label='APL (GNU APL)', audit_key='apl_retained_publication_audit',
        workloads=('nbody', 'mandelbrot', 'knucleotide', 'fannkuchredux', 'fasta'),
        forms=11, sources=9, aliases=2, subjects=27, controls=15, counts='source_counts'),
    'uiua-retained-nbody-trees-publication-candidate-v1': dict(
        language='uiua', label='Uiua', audit_key='uiua_retained_publication_audit',
        workloads=('nbody', 'binarytrees'), forms=4, sources=3, aliases=1,
        subjects=9, controls=6, counts='count_approval'),
    'lua-retained-pidigits-publication-candidate-v1': dict(
        language='lua', label='Lua (interpreted)', audit_key='lua_retained_publication_audit',
        workloads=('pidigits',), forms=4, sources=5, subject_sources=4, aliases=0,
        subjects=12, controls=6, counts='source_counts', source_evidence='source_manifest'),
}

LUA_PACKET = 'experiments/lua/retained-pidigits-v1'
LUA_COUNTS = dict(path=LUA_PACKET+'/qualified-source-counts-v1.json',
    sha256='8725633b2ffc195953368d38286d35bf327e54256648b7e32abc8cd37df642bf')
LUA_HELPER = 'ae50244bd96f7961201a40780c2dfeab4bb193fc0e2da2184c37753469ef4e6c'
LUA_APPLICATIONS = {
    1: ('e2e0139198ef7b00dd616fdd82d756e079a96db64702c72c4f9bed0a2d9d1e82', 62),
    5: ('00734d693c0968a606b8aef2cfeffa15da58e7f4ac81731c19fb7f1dde7a0c36', 77),
    6: ('ce34fae5e45f842c8b414b18fa368e90809165fda0781b8a00da2bc29d50d930', 63),
    7: ('cca5f009f82162b0bdd50d839add97ef21859b5d8ddd047b3db9f286973c9c2c', 57),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def safe_path(value):
    require(isinstance(value, str) and value and '\\' not in value, 'Invalid retained path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == value,
            'Unsafe retained path')
    return value


def raw_row(row):
    result = copy.deepcopy(row)
    result.pop('x', None)
    if type(result.get('publication_record')) is dict:
        result['publication_record'].pop('x', None)
    return result


def aggregate(data, reference, kind, axis):
    selected = reference.get('measured_benchmarks')
    values = []
    for bench in data['benchmarks']:
        if selected is not None and bench['key'] not in selected:
            continue
        groups = [g for g in bench['groups'] if g['language'] == reference['lang']]
        require(len(groups) <= 1, 'Duplicate language endpoint')
        if groups:
            values.append(data['programs'][groups[0][kind]][axis])
    require(values and all(positive(v) for v in values), 'Invalid aggregate inputs')
    return statistics.geometric_mean(values)


def endpoint(rows, scope):
    require(rows, 'Missing retained workload')
    fast = min(rows, key=lambda r: (r['seconds'], r['loc'], r['key']))
    small = min(rows, key=lambda r: (r['loc'], r['seconds'], r['key']))
    return dict(language=scope['language'], label=scope['label'], fast=fast['key'], small=small['key'],
                programs=list(dict.fromkeys([fast['key'], small['key']])),
                formatted_fast=None, formatted_small=None)


def validate_lua_bundle(candidate):
    """This reviewed two-file cohort does not relax other languages' bundles."""
    inventory = candidate['program_inventory']
    require(set(inventory) == {f'pidigits:lua-interpreted-gmp-listed-{v}' for v in LUA_APPLICATIONS}
            and candidate['source_counts'] == LUA_COUNTS and candidate['luajit_mutated'] is False
            and candidate['subject_samples'] == 12 and candidate['matched_control_samples'] == 6,
            'Exact four-form Lua cohort required')
    controls = candidate['matched_mech_controls']
    require(set(controls) == {'mech-fast-control', 'mech-small-control'}, 'Both matched Mech controls required')
    for identity, control in controls.items():
        samples = control['samples']
        require(control['key'] == 'pidigits:lua-study:'+identity and len(samples) == 3
                and all(positive(v) for v in samples) and control['seconds'] == statistics.median(samples)
                and control['timing_sd'] == statistics.stdev(samples), 'Lua matched control statistics differ')
    for variant, (digest, count) in LUA_APPLICATIONS.items():
        row = inventory[f'pidigits:lua-interpreted-gmp-listed-{variant}']
        require(row['id'] == f'lua-listed-{variant}' and row['source_sha256'] == digest
                and row['files'] == [digest, LUA_HELPER] and set(row['file_roles']) == {digest, LUA_HELPER}
                and row['loc'] == count + 218 and row['physical_loc'] == count + 119
                and row['helper_counted'] is True and row['original_helper_counted'] is False,
                'Complete Lua application and general helper bundle required')
        for source, role, path, units, physical in (
                (digest, 'application', f'{LUA_PACKET}/sources/pidigits-lua-{variant}-normalized.lua', count, count),
                (LUA_HELPER, 'general-library-helper', LUA_PACKET+'/support/gmp.c', 218, 119)):
            item = row['file_roles'][source]
            require(item['role'] == role and item['source_path'] == candidate['files'][source]['path'] == path
                    and item['normalized_loc'] == units and item['physical_loc'] == physical
                    and item['formatted_loc'] is None and item['source_owner_review'] == LUA_COUNTS,
                    'Lua counted source role differs')
        require(row['matched_mech_control'] == controls['mech-fast-control']
                and row['additional_matched_mech_control'] == controls['mech-small-control']
                and row['mech_comparison']['control_key'] == controls['mech-fast-control']['key']
                and row['mech_comparison']['samples_seconds'] == controls['mech-fast-control']['samples']
                and row['mech_comparison']['seconds'] == controls['mech-fast-control']['seconds'],
                'Lua matched controls were dropped or rebound')


def validate_candidate(candidate):
    require(candidate.get('schema') in SCOPES, 'Unreviewed retained candidate schema')
    scope = SCOPES[candidate['schema']]
    require(candidate['status'] == 'validated-retained-observations-awaiting-publication-review'
            and candidate['chart_admission'] is candidate['dataset_files_changed'] is False
            and candidate['historical_reports_mutated'] is False and candidate['native_processes_started'] == 0,
            'Retained candidate disposition differs')
    inventory, files = candidate['program_inventory'], candidate['files']
    require(len(inventory) == candidate['source_forms'] == scope['forms']
            and len(files) == scope['sources'], 'Candidate source inventory differs')
    require({r['benchmark'] for r in inventory.values()} == set(scope['workloads']), 'Workload set differs')
    if scope['language'] == 'lua':
        validate_lua_bundle(candidate)
    aliases = 0
    for key, row in inventory.items():
        require(row['key'] == key and row['language'] == scope['language']
                and row['eligible_for_chart'] is row['chart_admission'] is False,
                'Candidate row identity or disposition differs')
        require(all(row[flag] is True for flag in ('eligible_for_publication_review',
                'required_work_validated', 'source_work_qualified', 'canonical_loc_qualified',
                'full_workload_qualified')), 'Incomplete source/work/sample qualification')
        require(type(row['loc']) is int and row['loc'] > 0 and row['loc'] == row['canonical_loc']
                and row['formatted_loc'] is None and row['formatted_x'] is None
                and row['formatted_loc_qualified'] is False, 'Canonical/formatted count scope differs')
        if scope['language'] != 'lua':
            require(len(row['files']) == 1 and row['files'][0] == row['source_sha256']
                    and set(row['file_roles']) == set(row['files']), 'Counted source bundle differs')
            role = row['file_roles'][row['source_sha256']]
            require(role['normalized_loc'] == row['loc'] and role['physical_loc'] == row['physical_loc']
                    and role['role'] == 'application', 'Authored source count differs')
        require(len(row['samples']) == 3 and all(positive(v) for v in row['samples'])
                and row['seconds'] == statistics.median(row['samples'])
                and row['timing_sd'] == statistics.stdev(row['samples']), 'Saved sample statistics differ')
        control = row['mech_comparison']
        require(control['scope'] == 'paired-control' and positive(control['seconds'])
                and len(control['samples_seconds']) == 3 and all(positive(v) for v in control['samples_seconds'])
                and control['seconds'] == statistics.median(control['samples_seconds'])
                and control['time_x_mech'] == row['seconds'] / control['seconds'], 'Matched control differs')
        alias = row['timing_alias_of']
        if alias:
            require(alias in inventory and inventory[alias]['timing_alias_of'] is None
                    and inventory[alias]['samples'] == row['samples']
                    and inventory[alias]['source_sha256'] == row['source_sha256']
                    and row['native_observations'] == 0, 'Alias invented native observations')
            aliases += 1
        else:
            require(row.get('native_observations', 3) == 3, 'Native observation count differs')
    require(aliases == scope['aliases'] and (len(inventory) - aliases) * 3 == scope['subjects'],
            'Native sample ownership differs')
    require({f for row in inventory.values() for f in row['files']} == set(files), 'Unowned source content')
    for digest, source in files.items():
        require(digest == source['sha256'] == hashlib.sha256(source['code'].encode('utf-8')).hexdigest(),
                'Retained source bytes differ')
        safe_path(source['path'])
    endpoints = {b: endpoint([r for r in inventory.values() if r['benchmark'] == b], scope)
                 for b in scope['workloads']}
    if 'endpoints' in candidate:
        require(candidate['endpoints'] == endpoints, 'Exported endpoint proposal differs')
    return scope, endpoints


def normalize_loc(data, workload, new_base):
    bench = next(b for b in data['benchmarks'] if b['key'] == workload)
    old_base = bench['baseline_loc']
    require((workload, old_base, new_base) in (('nbody', 20, 19), ('binarytrees', 16, 15)),
            'Unreviewed retained minimum change')
    bench['baseline_loc'] = new_base
    changed = []
    for pool in ('programs', 'program_inventory'):
        for key, row in data[pool].items():
            if row['benchmark'] != workload or not positive(row.get('x')):
                continue
            require(positive(row.get('loc')) and math.isclose(row['x'], row['loc'] / old_base, rel_tol=1e-12),
                    'Existing canonical coordinate differs')
            old = row['x']
            row['x'] = row['loc'] / new_base
            if type(row.get('publication_record')) is dict:
                require(row['publication_record']['loc'] == row['loc']
                        and row['publication_record']['x'] == old, 'Publication coordinate differs')
                row['publication_record']['x'] = row['x']
            changed.append(dict(pool=pool, key=key, before=old, after=row['x']))
    affected = {g['language'] for g in bench['groups']}
    references = []
    for ref in data['reference_summary']:
        if ref['lang'] not in affected:
            continue
        for kind in ('fast', 'small'):
            old = ref[kind]['x']
            ref[kind]['x'] = aggregate(data, ref, kind, 'x')
            references.append(dict(language=ref['lang'], kind=kind, before=old, after=ref[kind]['x']))
    return dict(benchmark=workload, axis='canonical-loc', before=old_base, after=new_base,
                changed_program_coordinates=changed, changed_aggregate_coordinates=references,
                timing_baseline_changed=False, formatted_baselines_changed=False,
                raw_source_counts_changed=False, timing_samples_changed=False, source_or_receipt_bytes_changed=False)


def build_publication(original, original_languages, candidate, candidate_ref, runtime_scope_ref=None):
    scope, endpoints = validate_candidate(candidate)
    language, audit_key = scope['language'], scope['audit_key']
    require(runtime_scope_ref == (APL_RUNTIME_REVIEW if language == 'apl' else None),
            'Separate reviewed APL runtime scope required; unrelated overrides are unsupported')
    safe_path(candidate_ref['path'])
    require(audit_key not in original, 'Retained cohort already admitted')
    data, languages = copy.deepcopy(original), copy.deepcopy(original_languages)
    benches = {b['key']: b for b in data['benchmarks']}
    require(len(benches) == len(data['benchmarks']) and set(scope['workloads']) <= set(benches),
            'Catalog workload inventory differs')
    for b in scope['workloads']:
        require(not any(g['language'] == language for g in benches[b]['groups']),
                'Existing language endpoint requires explicit selection merge')
    if language == 'lua':
        prior_entries = [v for v in data['languages'] if v['key'] == 'lua']
        prior_refs = [v for v in data['reference_summary'] if v['lang'] == 'lua']
        previous = set(benches) - {'pidigits'}
        require(len(benches) == 10 and len(prior_entries) == len(prior_refs) == 1
                and len(prior_entries[0]['timed_benchmarks']) == len(prior_refs[0]['measured_benchmarks']) == 9
                and set(prior_entries[0]['timed_benchmarks']) == previous
                and set(prior_refs[0]['measured_benchmarks']) == previous
                and all(sum(g['language'] == 'lua' for g in benches[b]['groups']) == 1 for b in previous),
                'Lua admission requires the reviewed nine-to-ten workload expansion')
    for digest, source in candidate['files'].items():
        if digest in data['files']:
            require(data['files'][digest]['code'] == source['code'], 'Source content collision')
        else:
            data['files'][digest] = copy.deepcopy(source)
    paths = {candidate_ref['path']}
    if runtime_scope_ref is not None:
        paths.add(runtime_scope_ref['path'])
    source_evidence = scope.get('source_evidence', 'source_audit')
    for field in ('report', source_evidence, scope['counts'], 'reconciliation'):
        if field in candidate:
            paths.add(safe_path(candidate[field]['path']))
    for source in candidate['files'].values():
        paths.update([source['path'], *source.get('source_paths', [])])
    for path in paths:
        safe_path(path)
        require(data['archive_paths'].get(path, path) == path, 'Retained evidence mapping conflict')
        data['archive_paths'][path] = path
    for key, source in candidate['program_inventory'].items():
        require(key not in data['programs'] and key not in data['program_inventory'], 'Source identity already present')
        bench = benches[source['benchmark']]
        require(positive(bench['baseline_loc']) and positive(bench['baseline_seconds'])
                and source['seconds'] >= bench['baseline_seconds'], 'New time minimum requires separate review')
        row = copy.deepcopy(source)
        row.update(eligible_for_chart=True,
            chart_admission=dict(candidate=copy.deepcopy(candidate_ref), retained_samples_reused=True,
                                 source_counts_independently_reviewed=True),
            source_url=data['repository']['url'].rstrip('/') + '/blob/main/' +
                       quote(candidate['files'][row['source_sha256']]['path']),
            source_link_label='Exact retained source', local_adaptation=True,
            x=row['loc'] / bench['baseline_loc'], y=row['seconds'] / bench['baseline_seconds'])
        row['publication_record'] = copy.deepcopy(row)
        data['program_inventory'][key] = row
    for b, group in endpoints.items():
        benches[b]['groups'].append(copy.deepcopy(group))
        for key in group['programs']:
            data['programs'][key] = copy.deepcopy(data['program_inventory'][key])
    normalizations = []
    for b in scope['workloads']:
        bench = benches[b]
        low = min(data['programs'][key]['loc'] for g in bench['groups'] for key in g['programs']
                  if data['programs'][key].get('eligible_for_chart') is not False)
        require(low <= bench['baseline_loc'], 'Qualified current canonical minimum is absent')
        if low < bench['baseline_loc']:
            require(language != 'lua', 'Lua canonical minimum change requires separate review')
            normalizations.append(normalize_loc(data, b, low))
    entries = [v for v in data['languages'] if v['key'] == language]
    require(len(entries) == 1 and language in languages['languages'], 'Existing language metadata missing')
    entry = entries[0]
    for field in ('timed_benchmarks', 'source_benchmarks'):
        selected = set(entry[field]) | set(scope['workloads'])
        entry[field] = [b['key'] for b in data['benchmarks'] if b['key'] in selected]
    existing = [r for r in data['reference_summary'] if r['lang'] == language]
    require(len(existing) <= 1, 'Duplicate language aggregate')
    # The pre-expansion aggregate is captured after sequential LOC rebases.
    prior = copy.deepcopy(existing[0]) if existing else None
    reference = copy.deepcopy(prior) if prior else dict(lang=language, label=scope['label'])
    reference['measured_benchmarks'] = copy.deepcopy(entry['timed_benchmarks'])
    for kind in ('fast', 'small'):
        reference[kind] = {axis: aggregate(data, reference, kind, axis) for axis in ('x', 'y')}
    if existing:
        existing[0].clear()
        existing[0].update(reference)
    else:
        data['reference_summary'].append(reference)
    languages['languages'][language]['displayed_program_count'] = sum(
        row['language'] == language for row in data['programs'].values())
    audit = dict(schema='retained-language-catalog-admission-v1', status='prepared-qualified-retained-cohort',
        language=language, candidate=copy.deepcopy(candidate_ref), report=copy.deepcopy(candidate['report']),
        source_counts=copy.deepcopy(candidate[scope['counts']]),
        source_forms=scope['forms'], distinct_subject_sources=scope.get('subject_sources', scope['sources']),
        timing_aliases=scope['aliases'],
        subject_native_observations=scope['subjects'], control_native_observations=scope['controls'],
        imported_program_inventory=len(candidate['program_inventory']),
        imported_endpoint_programs=sum(len(g['programs']) for g in endpoints.values()),
        endpoints=copy.deepcopy(endpoints), normalizations=normalizations,
        aggregate_change=dict(before=prior, after=copy.deepcopy(reference)),
        native_runs=0, historical_reports_mutated=False, old_raw_measurements_changed=False)
    audit[source_evidence] = copy.deepcopy(candidate[source_evidence])
    if language == 'lua':
        audit.update(counted_physical_files=5, counted_files_per_profile=2,
                     matched_control_ids=list(candidate['matched_mech_controls']), luajit_mutated=False)
    if runtime_scope_ref is not None:
        audit['runtime_publication_scope_review'] = copy.deepcopy(runtime_scope_ref)
    data[audit_key] = audit
    changed_benches = {n['benchmark'] for n in normalizations}
    for pool in ('programs', 'program_inventory'):
        for key, row in original[pool].items():
            require(raw_row(data[pool][key]) == raw_row(row), 'Old raw source/timing record changed')
            if row['benchmark'] not in changed_benches:
                require(data[pool][key] == row, 'Unrelated coordinate changed')
    for key, source in original['files'].items():
        require(data['files'][key] == source, 'Old source bytes/metadata changed')
    require(data.get('formatted_reference_summary') == original.get('formatted_reference_summary'),
            'Formatted aggregate changed')
    return data, languages, audit
