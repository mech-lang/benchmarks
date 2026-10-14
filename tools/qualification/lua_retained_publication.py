"""Admit the exact retained Lua pi cohort with an optional prior aggregate.

The nine measured workload groups are required. A missing partial-suite
aggregate is preserved as absence; the complete ten-workload aggregate is
created from the qualified endpoint coordinates. No native work is performed.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
from urllib.parse import quote


ORIGINAL = Path(__file__).with_name('retained_catalog_publication.py')
ORIGINAL_SHA = '219f4ab8bd4c3784b203c6e8654ab5f2e79aaf2fededecdcd3625ddc767be56c'
raw = ORIGINAL.read_bytes()
if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
    raise ValueError('Original retained publication source changed')
spec = importlib.util.spec_from_file_location('lua_original_retained_publication', ORIGINAL)
p = importlib.util.module_from_spec(spec)
exec(compile(raw, str(ORIGINAL), 'exec'), p.__dict__)
require = p.require


def build_publication(original, original_languages, candidate, candidate_ref, runtime_scope_ref=None):
    scope, endpoints = p.validate_candidate(candidate)
    require(scope['language'] == 'lua' and runtime_scope_ref is None, 'Only the retained Lua cohort is supported')
    p.safe_path(candidate_ref['path'])
    audit_key = scope['audit_key']
    require(audit_key not in original, 'Retained cohort already admitted')
    data, languages = copy.deepcopy(original), copy.deepcopy(original_languages)
    benches = {b['key']: b for b in data['benchmarks']}
    entries = [v for v in data['languages'] if v['key'] == 'lua']
    refs = [v for v in data['reference_summary'] if v['lang'] == 'lua']
    previous = set(benches) - {'pidigits'}
    require(len(benches) == len(data['benchmarks']) == 10 and 'pidigits' in benches
            and len(entries) == 1 and len(refs) <= 1 and 'lua' in languages['languages']
            and len(entries[0]['timed_benchmarks']) == 9
            and set(entries[0]['timed_benchmarks']) == previous
            and all(sum(g['language'] == 'lua' for g in benches[b]['groups']) == 1 for b in previous)
            and all(g['language'] != 'lua' for g in benches['pidigits']['groups']),
            'Lua admission requires exactly nine measured workloads before pi')
    if refs:
        require(len(refs[0]['measured_benchmarks']) == 9 and set(refs[0]['measured_benchmarks']) == previous,
                'Existing Lua aggregate coverage differs')
    prior = copy.deepcopy(refs[0]) if refs else None
    for digest, source in candidate['files'].items():
        if digest in data['files']:
            require(data['files'][digest]['code'] == source['code'], 'Source content collision')
        else:
            data['files'][digest] = copy.deepcopy(source)
    paths = {candidate_ref['path']}
    for field in ('report', 'source_manifest', 'source_counts', 'reconciliation'):
        if field in candidate:
            paths.add(p.safe_path(candidate[field]['path']))
    for source in candidate['files'].values():
        paths.update([source['path'], *source.get('source_paths', [])])
    for path in sorted(paths):
        p.safe_path(path)
        require(data['archive_paths'].get(path, path) == path, 'Retained evidence mapping conflict')
        data['archive_paths'][path] = path
    bench = benches['pidigits']
    for key, source in candidate['program_inventory'].items():
        require(key not in data['programs'] and key not in data['program_inventory'], 'Source identity already present')
        require(p.positive(bench['baseline_loc']) and p.positive(bench['baseline_seconds'])
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
    bench['groups'].append(copy.deepcopy(endpoints['pidigits']))
    for key in endpoints['pidigits']['programs']:
        data['programs'][key] = copy.deepcopy(data['program_inventory'][key])
    low = min(data['programs'][key]['loc'] for g in bench['groups'] for key in g['programs']
              if data['programs'][key].get('eligible_for_chart') is not False)
    require(low == bench['baseline_loc'], 'Lua canonical minimum change requires separate review')
    entry = entries[0]
    for field in ('timed_benchmarks', 'source_benchmarks'):
        selected = set(entry[field]) | {'pidigits'}
        entry[field] = [b['key'] for b in data['benchmarks'] if b['key'] in selected]
    reference = copy.deepcopy(prior) if prior else dict(lang='lua', label=scope['label'])
    reference['measured_benchmarks'] = copy.deepcopy(entry['timed_benchmarks'])
    for kind in ('fast', 'small'):
        reference[kind] = {axis: p.aggregate(data, reference, kind, axis) for axis in ('x', 'y')}
    if refs:
        refs[0].clear()
        refs[0].update(reference)
    else:
        data['reference_summary'].append(reference)
    languages['languages']['lua']['displayed_program_count'] = sum(
        row['language'] == 'lua' for row in data['programs'].values())
    audit = dict(schema='retained-language-catalog-admission-v1', status='prepared-qualified-retained-cohort',
        language='lua', candidate=copy.deepcopy(candidate_ref), report=copy.deepcopy(candidate['report']),
        source_counts=copy.deepcopy(candidate['source_counts']), source_forms=4, distinct_subject_sources=4,
        timing_aliases=0, subject_native_observations=12, control_native_observations=6,
        imported_program_inventory=4, imported_endpoint_programs=len(endpoints['pidigits']['programs']),
        endpoints=copy.deepcopy(endpoints), normalizations=[],
        aggregate_change=dict(before=prior, after=copy.deepcopy(reference)),
        native_runs=0, historical_reports_mutated=False, old_raw_measurements_changed=False,
        source_manifest=copy.deepcopy(candidate['source_manifest']), counted_physical_files=5,
        counted_files_per_profile=2, matched_control_ids=list(candidate['matched_mech_controls']),
        luajit_mutated=False)
    data[audit_key] = audit
    for pool in ('programs', 'program_inventory', 'files'):
        for key, value in original[pool].items():
            require(data[pool][key] == value, 'Existing source or timing record changed')
    require(data.get('formatted_reference_summary') == original.get('formatted_reference_summary'),
            'Formatted aggregate changed')
    return data, languages, audit
