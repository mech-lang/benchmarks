"""Validate saved LOC rebases and produce a preservation-only coordinate view.

No producer, runtime or benchmark is invoked. Registered admission adapters bind
new minima to exact source/count/report evidence; the generic transition checker
independently checks every old/new coordinate against retained apply snapshots.
"""
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import statistics

HISTORY = 'data/normalization-history.json'
CATALOG = 'data/benchmarks.json'
LANGUAGES = 'data/languages.json'
UIUA_AUDIT = 'uiua_fann_v5_publication_audit'
PACKET = 'experiments/uiua/fann-v5-publication-v1'
ARCHIVE = 'archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5'
UIUA_PINS = {
    'report': (ARCHIVE+'/full-study/report.json', 'f5ab40f30c8add188c4e7a0ac87dc7fd18475ff28c5bba8838dc08b10ff71a6c'),
    'manifest': (ARCHIVE+'/full-study/manifest.json', 'd8b6ad100671b3fef5ae46d90dcb36b044733b25ea8d65e3ba7a4589e5b62513'),
    'independent_source_approval': (PACKET+'/independent-source-review.json', 'c594c29d38f869a2add722d3f4d4c282117bb1ac3556a3e3c4ccb3963625c826'),
    'source_owner_review': (PACKET+'/source-owner-review.md', '1e6ec65fbb85d8ad90902683b124509e3c35820ef46b1b2f489679ec0ca11c10'),
    'prior_independent_reconciliation': ('archive/comparisons/r-apl-uiua-comparison/20261011/evidence/new-results-review-20261012/independent-study-reconciliation.json', '23e728205fdcbbe1eb974db4dbaefb26bf1b93330e65f8a561f61e3ca3bde404'),
    'source_candidate_archive': (ARCHIVE+'/manifest.json', '9d8972f3254500ad14cbbf56e0378a7a47661edaaeb7afba04b50dcad3cc6534'),
}
UIUA_SOURCES = {
    'compact': ('95f622e306aa23ce3678e6c5aba0dfec8f303bf31b294d78124c7e451ea65489', 20),
    'fast': ('b3a2563f7d6503d03d2c0bbd7edae82f9743f137f7d47b3fa561970cfa0a4a0e', 21),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def equal_number(actual, expected, label):
    # Saved arithmetic is binary floating point. Raw evidence is never compared
    # with this tolerance: only independently recomputed derived coordinates.
    require(positive(actual) and positive(expected) and
            math.isclose(actual, expected, rel_tol=1e-12, abs_tol=0), label)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: '+key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def safe_path(value):
    require(isinstance(value, str) and value and '\\' not in value, 'Invalid evidence path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == value,
            'Unsafe evidence path: '+value)
    return path


def read_bytes(root, relative):
    path = root / safe_path(relative)
    require(path.resolve().is_relative_to(root.resolve()), 'Evidence escapes repository')
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), 'Evidence is not a regular file')
    raw = path.read_bytes()
    after = path.lstat()
    require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'Evidence changed while reading')
    return raw


def checked(root, reference):
    require(type(reference) is dict and isinstance(reference.get('sha256'), str) and
            re.fullmatch('[0-9a-f]{64}', reference['sha256']), 'Invalid evidence digest')
    raw = read_bytes(root, reference['path'])
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'],
            'Evidence digest differs: '+reference['path'])
    return raw


def index(values, key, label):
    result = {}
    for value in values:
        require(value[key] not in result, 'Duplicate '+label)
        result[value[key]] = value
    return result


def raw_row(row):
    value = copy.deepcopy(row)
    value.pop('x', None)
    if type(value.get('publication_record')) is dict:
        value['publication_record'].pop('x', None)
    return value


def aggregate(data, reference, kind, axis="x"):
    selected = reference.get('measured_benchmarks')
    require(selected is None or (type(selected) is list and len(selected) == len(set(selected))),
            'Invalid aggregate workload selection')
    values = []
    for bench in data['benchmarks']:
        if selected is not None and bench['key'] not in selected:
            continue
        groups = [g for g in bench['groups'] if g['language'] == reference['lang']]
        require(len(groups) <= 1, 'Duplicate aggregate language group')
        if groups:
            values.append(data['programs'][groups[0][kind]][axis])
    require(values and all(positive(v) for v in values), 'Invalid aggregate inputs')
    return statistics.geometric_mean(values)


def minimum(data, bench):
    values = []
    for group in bench['groups']:
        for key in group['programs']:
            row = data['programs'][key]
            require(row['benchmark'] == bench['key'], 'Endpoint workload differs')
            if row.get('eligible_for_chart') is not False:
                require(positive(row.get('loc')), 'Eligible endpoint lacks canonical LOC')
                values.append(row['loc'])
    require(values, 'No qualified endpoints for normalization')
    return min(values)


def validate_new_row(data,pool,key):
    row=data[pool][key]
    bench=index(data['benchmarks'],'key','workload')[row['benchmark']]
    equal_number(row.get('x'),row['loc']/bench['baseline_loc'],'Admitted program x differs')
    equal_number(row.get('y'),row['seconds']/bench['baseline_seconds'],'Admitted program y differs')
    require(type(row.get('publication_record')) is dict and
            row['publication_record']=={field:value for field,value in row.items() if field!='publication_record'},
            'Admitted publication snapshot differs')


def validate_uiua(root, audit, before, after):
    """Bind the exact admitted Uiua sources to the frozen count/native evidence."""
    require(audit.get('schema') == 'uiua-fann-v5-catalog-admission-v1' and
            audit.get('status') == 'prepared-qualified-retained-study', 'Unknown Uiua admission')
    for key, value in {'imported_subject_samples': 6, 'reused_matched_control_samples': 3,
                       'native_runs': 0, 'source_forms': 2, 'aliases': 0,
                       'historical_reports_mutated': False, 'old_raw_measurements_changed': False}.items():
        require(audit.get(key) == value, 'Uiua admission scope differs: '+key)
    candidate = strict_json(checked(root, audit['candidate']))
    require(candidate['schema'] == 'uiua-fann-v5-private-publication-candidate-v1' and
            candidate['chart_admission'] is candidate['dataset_files_changed'] is False and
            candidate['native_processes_started'] == 0 and candidate['retained_subject_samples'] == 6 and
            candidate['retained_control_samples'] == 3, 'Uiua candidate scope differs')
    evidence = {}
    for name, (path, digest) in UIUA_PINS.items():
        ref = audit[name]
        require(ref == candidate[name] and ref['path'] == path and ref['sha256'] == digest,
                'Unapproved Uiua evidence: '+name)
        raw = checked(root, ref)
        if name != 'source_owner_review':
            evidence[name] = strict_json(raw)
    source_archive = audit['source_candidate_archive']
    require(source_archive.get('original_sealed_sha256') ==
            '41462f55b1c1f6c800d08cca9ba9ba46cb5e3c6efd7f0ff3d21cfde514b70b7c' and
            source_archive.get('documentation_only_changed_fields') == ['migration_policy'] and
            source_archive.get('measurement_fields_changed') is False,
            'Original sealed candidate distinction changed')
    report = evidence['report']
    require(report['status'] == 'complete' and report['active'] is None and
            report['pins_unchanged_at_end'] is True and len(report['attempts']) == 9,
            'Complete retained nine-observation report required')
    expected_keys = {'fannkuchredux:parallel-study:uiua-'+v for v in UIUA_SOURCES}
    require(set(candidate['program_inventory']) == expected_keys, 'Uiua identities differ')
    approval = evidence['independent_source_approval']
    require(approval['status'] == 'passed-independent-source-owner-review' and
            approval['source_owner_review'] == audit['source_owner_review'], 'Source approval differs')
    for variant, (digest, count) in UIUA_SOURCES.items():
        key = 'fannkuchredux:parallel-study:uiua-'+variant
        row = candidate['program_inventory'][key]
        source = candidate['files'][digest]
        require(hashlib.sha256(source['code'].encode('utf-8')).hexdigest() == digest ==
                source['sha256'] == row['source_sha256'], 'Exact counted source differs')
        require(approval['sources'][variant]['sha256'] == digest and
                approval['sources'][variant]['canonical_loc'] == count == row['loc'] ==
                row['canonical_loc'] == candidate['source_counts'][variant]['canonical_loc'] and
                candidate['source_counts'][variant]['source_sha256'] == digest,
                'Reviewed canonical count differs')
        observed = report['profiles']['uiua-'+variant]
        require(row['samples'] == observed['samples_seconds'] and
                row['seconds'] == observed['median_seconds'] and row['timing_sd'] == observed['sample_stdev_seconds'],
                'New minimum lacks exact retained timing observations')
        for field in ('required_work_validated', 'source_work_qualified', 'canonical_loc_qualified', 'full_workload_qualified'):
            require(row[field] is True, 'Incomplete admitted source/work qualification')
        for pool in ('programs', 'program_inventory'):
            actual = after[pool][key]
            validate_new_row(after,pool,key)
            for field, value in row.items():
                if field not in ('eligible_for_chart', 'chart_admission'):
                    require(field in actual and actual[field] == value, 'Admitted candidate field changed: '+field)
            require(actual['eligible_for_chart'] is True and
                    actual['chart_admission']['candidate'] == audit['candidate'], 'Missing chart admission')
    require(audit['normalization']['benchmark'] == 'fannkuchredux' and
            audit['normalization']['before'] == 31 and audit['normalization']['after'] == 20,
            'Unapproved Uiua minimum')
    return expected_keys, {'uiua'}


# All values below bind existing reviewed evidence, not arbitrary count claims.
RETAINED = {
    'r': dict(schema='r-retained-three-workload-publication-candidate-v1',forms=6,sources=6,aliases=0,
        subjects=18,controls=9,workloads=('nbody','binarytrees','fannkuchredux'),count_field='source_counts',
        report=('archive/comparisons/r-apl-uiua-comparison/20261011/results/timings-r.json',
                'ce37df0204cd7880033206f3afb2f91296d4b757090c5026947a414c224f1c6e'),
        source_audit=('archive/comparisons/r-apl-uiua-comparison/20261011/source-audit-r.json',
                      'd76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'),
        source_counts=('experiments/r/retained-source-counts-v1/qualified-source-counts-v1.json',
                       '835ded7cc27df684f6628048b90f4ec06ef249ba8f58ed207016a669dcacb0cf')),
    'apl': dict(schema='apl-retained-five-workload-publication-candidate-v1',forms=11,sources=9,aliases=2,
        subjects=27,controls=15,workloads=('nbody','mandelbrot','knucleotide','fannkuchredux','fasta'),count_field='source_counts',
        report=('archive/qualification/shared/records/apl-sample84-recovery-v1/full-owner/timings-apl.json',
                'd8281e04af0cfb460364af540d7cb158074df8dad6238c78cc8d8cd971257bda'),
        source_audit=('archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/apl-argv-v1/full-owner/source-audit-apl-argv.json',
                      'b00de5ce41c3a6322f4ab9a3e194775723c8889d3143573d93a21ced75e22e6b'),
        source_counts=('experiments/apl/retained-counts-v1/qualified-source-counts-v1.json',
                       'e6202963c207ec0ead8c0e95565b2af5050696671ed1c653dcdc1fa92479d24f')),
    'uiua': dict(schema='uiua-retained-nbody-trees-publication-candidate-v1',forms=4,sources=3,aliases=1,
        subjects=9,controls=6,workloads=('nbody','binarytrees'),count_field='count_approval',
        report=('archive/comparisons/r-apl-uiua-comparison/20261011/results/timings-uiua.json',
                'da5ccf102e90dc2755388414390f6401402b2f67edb177ba74a377f2c5cae709'),
        source_audit=('archive/comparisons/r-apl-uiua-comparison/20261011/source-audit-uiua.json',
                      '82b15648d0c49c6393a0eec1efb441f1ee11237ceae4a8f41ca854c0b7ee0860'),
        source_counts=('experiments/uiua/retained-counts-v1/qualified-source-counts.json',
                       'f2d5763e6ef958a0dbffad3a5a9d72c20767642fb131e978f168c361b4bb7607')),
}


APL_RUNTIME_REVIEW=dict(path='experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json',
    sha256='76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6')


def validate_apl_runtime(root,audit,candidate,report):
    require(audit.get('runtime_publication_scope_review')==APL_RUNTIME_REVIEW,
            'Separate exact APL runtime scope review required')
    review=strict_json(checked(root,APL_RUNTIME_REVIEW))
    require(review['schema']=='apl-retained-runtime-publication-scope-review-v1' and
            review['status']=='qualified-recorded-runtime-metadata-with-explicit-static-scope' and
            review['runtime_publication_metadata_qualified'] is True,'APL runtime scope is unqualified')
    scope=review['scope_qualifiers']
    require(scope['recorded_static_dependencies_qualified'] is scope['physical_pin_replay_required_before_publication'] is True
            and all(scope[field] is False for field in ('per_process_loaded_images_qualified',
                'complete_transitive_os_dependency_inventory_qualified','full_inherited_environment_qualified',
                'native_toolchain_reexecution_performed','physical_pin_replay_performed','chart_admission'))
            and scope['new_native_processes']==0,'APL runtime observation scope changed')
    require(candidate['runtime_publication_metadata_qualified'] is False and
            set(review['profile_bindings'])==set(candidate['program_inventory']),
            'Frozen APL candidate disposition or runtime coverage changed')
    for key,row in candidate['program_inventory'].items():
        binding=review['profile_bindings'][key];original=report['programs'][key]
        require(row['runtime_publication_metadata_qualified'] is False and row['runtime']==review['runtime'] and
                row['source_sha256']==binding['source_sha256'] and row['runtime_arguments']==binding['command'] and
                row['runtime_environment']==binding['runtime_environment'] and
                row['maximum_workers']==binding['requested_worker_ceiling'], 'APL recorded profile/runtime join differs')
        for field in ('runtime_sha256','binary','binary_sha256','library_support'):
            require(original[field]==binding[field],'APL original recorded runtime binding differs')
    # Physical inherited-pin replay belongs to the held publication context;
    # this portable verifier does not claim or perform a new runtime discovery.


def validate_retained(root,audit,before,after):
    language=audit['language'];scope=RETAINED[language]
    require(audit['schema']=='retained-language-catalog-admission-v1' and
            audit['status']=='prepared-qualified-retained-cohort', 'Unknown retained admission')
    expected=dict(source_forms=scope['forms'],distinct_subject_sources=scope['sources'],timing_aliases=scope['aliases'],
        subject_native_observations=scope['subjects'],control_native_observations=scope['controls'],
        imported_program_inventory=scope['forms'],native_runs=0,historical_reports_mutated=False,old_raw_measurements_changed=False)
    for field,value in expected.items():require(field in audit and audit[field]==value,'Retained admission scope differs: '+field)
    candidate=strict_json(checked(root,audit['candidate']))
    require(candidate['schema']==scope['schema'] and candidate['status']=='validated-retained-observations-awaiting-publication-review'
            and candidate['chart_admission'] is candidate['dataset_files_changed'] is False and
            candidate['historical_reports_mutated'] is False and candidate['native_processes_started']==0,
            'Retained candidate disposition differs')
    evidence={}
    for field in ('report','source_audit','source_counts'):
        ref=candidate[scope['count_field'] if field=='source_counts' else field]
        path,digest=scope[field]
        require(audit[field]==ref and ref['path']==path and ref['sha256']==digest,'Unapproved retained evidence: '+field)
        evidence[field]=strict_json(checked(root,ref))
    counts=evidence['source_counts']
    require(counts['canonical_loc_qualified'] is True and counts['formatted_loc_qualified'] is False,
            'Qualified canonical source receipt required')
    inventory=candidate['program_inventory'];report=evidence['report']
    if language=='apl':validate_apl_runtime(root,audit,candidate,report)
    else:require('runtime_publication_scope_review' not in audit,'Unexpected runtime scope override')
    if language=='uiua':
        by_identity=index(counts['profiles'],'identity','counted source')
        count_rows={
            'binarytrees:binarytrees-uiua-compact':by_identity['binarytrees'],
            'binarytrees:binarytrees-uiua-optimized':by_identity['binarytrees'],
            'nbody:nbody-uiua-native-denominator-compact-v3':by_identity['nbody-compact'],
            'nbody:nbody-uiua-native-denominator-optimized-v3':by_identity['nbody-fast']}
    else:
        count_rows=index(counts['profiles'],'key','counted source')
    require(set(inventory)==set(count_rows) and len(inventory)==scope['forms'] and
            len(candidate['files'])==scope['sources'], 'Exact counted source inventory differs')
    aliases=0
    for key,row in inventory.items():
        count=count_rows[key];digest=count['source']['sha256']
        require(row['key']==key and row['language']==language and row['source_sha256']==digest and
                row['loc']==row['canonical_loc']==count['canonical_loc'] and row['formatted_loc'] is None and
                row['physical_loc']==count.get('physical_loc',count.get('original_physical_loc')),
                'Canonical source identity/count differs')
        source=candidate['files'][digest]
        require(source['sha256']==digest==hashlib.sha256(source['code'].encode('utf-8')).hexdigest() and
                row['files']==[digest], 'Counted source bytes differ')
        alias=row['timing_alias_of']
        if language=='uiua':
            wanted_alias='binarytrees:binarytrees-uiua-compact' if key=='binarytrees:binarytrees-uiua-optimized' else None
        else:wanted_alias=count.get('timing_alias_of')
        require(alias==wanted_alias,'Native alias ownership differs')
        aliases+=int(alias is not None)
        native=report['programs'][alias or key]
        require(native['source_sha256']==digest and row['samples']==native['samples_seconds'] and
                row['seconds']==native['median_seconds'] and row['timing_sd']==native['sample_stdev_seconds'] and
                len(row['samples'])==3 and row['seconds']==statistics.median(row['samples']) and
                row['full_output_validation']==native['sample_validation'], 'Retained native observation differs')
        for field in ('required_work_validated','source_work_qualified','canonical_loc_qualified','full_workload_qualified'):
            require(row[field] is True,'Incomplete retained qualification')
        for pool in ('programs','program_inventory'):
            if key not in after[pool]:continue
            actual=after[pool][key]
            validate_new_row(after,pool,key)
            for field,value in row.items():
                if field not in ('eligible_for_chart','chart_admission'):
                    require(field in actual and actual[field]==value,'Admitted candidate field changed: '+field)
            require(actual['eligible_for_chart'] is True and actual['chart_admission']['candidate']==audit['candidate'],
                    'Missing retained chart admission')
    require(aliases==scope['aliases'],'Alias count differs')
    endpoints={}
    for workload in scope['workloads']:
        rows=[row for row in inventory.values() if row['benchmark']==workload]
        require(rows,'Missing retained workload')
        fast=min(rows,key=lambda row:(row['seconds'],row['loc'],row['key']))['key']
        small=min(rows,key=lambda row:(row['loc'],row['seconds'],row['key']))['key']
        group=audit['endpoints'][workload]
        require(group['language']==language and group['fast']==fast and group['small']==small and
                group['programs']==list(dict.fromkeys((fast,small))) and
                group['formatted_fast'] is group['formatted_small'] is None, 'Retained endpoint selection differs')
        endpoints[workload]=group
    require(audit['endpoints']==endpoints,'Unexpected retained workload group')
    selected={key for group in endpoints.values() for key in group['programs']}
    require(audit['imported_endpoint_programs']==len(selected),'Selected source count differs')
    for item in audit['normalizations']:
        change=item['benchmark'],item['before'],item['after']
        require(change in ({('nbody',20,19),('binarytrees',16,15)} if language=='r' else
                           {('binarytrees',16,15)} if language=='uiua' else set()),
                'Unapproved retained minimum change')
    require(audit['aggregate_change']['after']['lang']==language and
            audit['aggregate_change']['after']['label']=={'r':'R','apl':'APL (GNU APL)','uiua':'Uiua'}[language],
            'Wrong own-language aggregate')
    added_refs=set() if any(ref['lang']==language for ref in before['reference_summary']) else {language}
    return dict(programs=selected,program_inventory=set(inventory)),added_refs


# Registration requires reviewed code and exact evidence; JSON cannot add one.
ADAPTERS={UIUA_AUDIT:validate_uiua,**{language+'_retained_publication_audit':validate_retained for language in RETAINED}}

def normalization_items(audit):
    if 'normalizations' in audit:
        require('normalization' not in audit and type(audit['normalizations']) is list,
                'Ambiguous normalization shape')
        return audit['normalizations']
    return [audit['normalization']]


def strip_reference_x(reference):
    result = copy.deepcopy(reference)
    for kind in ('fast', 'small'):
        result[kind].pop('x', None)
    return result


def additions_by_pool(added):
    if type(added) is dict:
        require(set(added) == {'programs', 'program_inventory'}, 'Invalid admitted source pools')
        return {pool:set(keys) for pool,keys in added.items()}
    return {pool:set(added) for pool in ('programs', 'program_inventory')}


def preserve_coordinate_availability(old,current):
    require(('x' in old)==('x' in current),'Old coordinate field availability changed')
    previous=old.get('x');present=current.get('x')
    require(positive(previous)==positive(present),'Old positive coordinate availability changed')
    if not positive(previous):
        require(previous==present,'Old null/unqualified coordinate changed')
    old_publication=old.get('publication_record');new_publication=current.get('publication_record')
    if type(old_publication) is dict:
        require(type(new_publication) is dict and ('x' in old_publication)==('x' in new_publication),
                'Old publication coordinate field availability changed')
        previous=old_publication.get('x');present=new_publication.get('x')
        require(positive(previous)==positive(present),'Old positive publication coordinate availability changed')
        if not positive(previous):
            require(previous==present,'Old null/unqualified publication coordinate changed')


def validate_transition(before, after, audit, added_keys, added_references):
    """Replay one admission's ordered LOC changes using one snapshot pair.

    The concrete adapter supplies per-pool added identities and new reference
    languages. `aggregate_change` authorizes only the admission's own expanded
    reference, and is separately bound by that adapter.
    """
    items = normalization_items(audit)
    added = additions_by_pool(added_keys)
    old_b = index(before['benchmarks'], 'key', 'workload')
    new_b = index(after['benchmarks'], 'key', 'workload')
    require(old_b.keys() == new_b.keys(), 'Workload inventory differs')
    endpoints = audit.get('endpoints')
    if endpoints is None:
        require(len(items) == 1, 'Single endpoint requires exactly one normalization')
        endpoints = {items[0]['benchmark']:audit['endpoint']}
    require(type(endpoints) is dict and set(endpoints) <= set(old_b), 'Invalid admission endpoints')
    workloads = {item['benchmark'] for item in items}
    require(workloads <= set(old_b), 'Unknown normalization workload')
    expected_baselines = {key:value['baseline_loc'] for key,value in old_b.items()}
    for item in items:
        workload, low, high = item['benchmark'], item['after'], item['before']
        require(item['axis'] == 'canonical-loc' and positive(low) and positive(high) and low < high and
                expected_baselines[workload] == high, 'Invalid or discontinuous canonical-LOC change')
        for flag in ('timing_baseline_changed', 'formatted_baselines_changed', 'raw_source_counts_changed',
                     'timing_samples_changed', 'source_or_receipt_bytes_changed'):
            require(item.get(flag) is False, 'Unauthorized normalization scope: '+flag)
        expected_baselines[workload] = low
    for name, old in old_b.items():
        require(new_b[name]['baseline_loc'] == expected_baselines[name], 'Recorded baseline differs')
        for field, value in old.items():
            if field in ('baseline_loc', 'groups'):
                continue
            require(field in new_b[name] and new_b[name][field] == value,
                    'Unrelated benchmark metadata changed')
        groups = old['groups']+([endpoints[name]] if name in endpoints else [])
        require(new_b[name]['groups'] == groups, 'Admission endpoint differs')
        if name in workloads or name in endpoints:
            require(expected_baselines[name] == minimum(after,new_b[name]), 'Recorded canonical minimum differs')
    for pool in ('programs','program_inventory'):
        require(set(after[pool])-set(before[pool]) == added[pool] and not(set(before[pool])-set(after[pool])),
                'Admission source inventory differs')
        for key in added[pool]:
            validate_new_row(after,pool,key)
        for key, old in before[pool].items():
            row = after[pool][key]
            require(raw_row(old) == raw_row(row), 'Raw source/timing fields changed: '+key)
            preserve_coordinate_availability(old,row)
            if row['benchmark'] not in workloads:
                require(row == old, 'Unrelated program coordinate changed')
    for key, row in before['files'].items():
        require(key in after['files'] and after['files'][key] == row, 'Old source bytes/metadata changed')
    require(before.get('formatted_reference_summary') == after.get('formatted_reference_summary'),
            'Formatted coordinates changed')
    old_refs = index(before['reference_summary'],'lang','aggregate')
    new_refs = index(after['reference_summary'],'lang','aggregate')
    require(set(new_refs)-set(old_refs) == set(added_references) and not(set(old_refs)-set(new_refs)),
            'Aggregate inventory differs')
    for reference in old_refs.values():
        for kind in ('fast','small'):
            equal_number(reference[kind]['x'],aggregate(before,reference,kind),'Original aggregate x differs')

    # New groups/rows are present before normalization, while a newly created
    # or expanded own-language aggregate is published after the sequence.
    state = copy.deepcopy(after)
    state['reference_summary'] = copy.deepcopy(before['reference_summary'])
    state_b = index(state['benchmarks'],'key','workload')
    for name in workloads:
        state_b[name]['baseline_loc'] = old_b[name]['baseline_loc']
    for pool in ('programs','program_inventory'):
        for key,row in state[pool].items():
            if row['benchmark'] not in workloads or not positive(row.get('x')):
                continue
            baseline = old_b[row['benchmark']]['baseline_loc']
            old = before[pool].get(key)
            row['x'] = old['x'] if old is not None else row['loc']/baseline
            equal_number(row['x'],row['loc']/baseline,'Original program x differs')
            if type(row.get('publication_record')) is dict:
                require(row['publication_record'].get('loc') == row['loc'], 'Publication source count differs')
                row['publication_record']['x'] = old['publication_record']['x'] if old is not None else row['x']
                equal_number(row['publication_record']['x'],row['x'],'Original publication coordinate differs')
    boundaries = []
    for item in items:
        workload,low,high = item['benchmark'],item['after'],item['before']
        require(state_b[workload]['baseline_loc'] == high, 'Discontinuous normalization sequence')
        expected, prior_publication = {}, {}
        for pool in ('programs','program_inventory'):
            for key,row in state[pool].items():
                if row['benchmark'] != workload or not positive(row.get('x')):
                    continue
                prior = row['x'];row['x'] = row['loc']/low
                expected[pool,key] = dict(pool=pool,key=key,before=prior,after=row['x'])
                if type(row.get('publication_record')) is dict:
                    prior_publication[pool,key] = row['publication_record']['x']
                    row['publication_record']['x'] = row['x']
        recorded = {}
        for change in item['changed_program_coordinates']:
            identity = change['pool'],change['key']
            require(identity not in recorded,'Duplicate program coordinate audit')
            recorded[identity] = change
        require(recorded == expected, 'Incomplete or altered program coordinate audit')
        state_b[workload]['baseline_loc'] = low
        affected = {g['language'] for g in state_b[workload]['groups']}
        expected_refs, prior_refs = {}, {}
        for reference in state['reference_summary']:
            language = reference['lang']
            if language not in affected:
                continue
            prior_refs[language] = copy.deepcopy(reference)
            for kind in ('fast','small'):
                prior = reference[kind]['x']
                reference[kind]['x'] = aggregate(state,reference,kind)
                expected_refs[language,kind] = dict(language=language,kind=kind,before=prior,after=reference[kind]['x'])
        recorded_refs = {}
        for change in item['changed_aggregate_coordinates']:
            identity = change['language'],change['kind']
            require(identity not in recorded_refs,'Duplicate aggregate coordinate audit')
            recorded_refs[identity] = change
        require(recorded_refs == expected_refs,'Incomplete or altered aggregate coordinate audit')
        boundaries.append(dict(normalization=item,program_before={key:value['before'] for key,value in expected.items()},
                               publication_before=prior_publication,reference_before=prior_refs))
    for pool in ('programs','program_inventory'):
        for key,row in state[pool].items():
            require(row == after[pool][key], 'Rebased program or publication x differs')
    changed = audit.get('aggregate_change')
    own_language = None
    if changed is not None:
        require(type(changed) is dict and set(changed)=={'before','after'} and
                type(changed['after']) is dict, 'Invalid own aggregate change')
        own_language = changed['after']['lang']
        state_refs = index(state['reference_summary'],'lang','aggregate')
        require(changed['before'] == state_refs.get(own_language) and
                changed['after'] == new_refs.get(own_language), 'Own aggregate before/after differs')
        if changed['before'] is not None:
            preserved=copy.deepcopy(changed['before'])
            preserved['measured_benchmarks']=changed['after']['measured_benchmarks']
            for kind in ('fast','small'):
                for axis in ('x','y'):
                    preserved[kind][axis]=changed['after'][kind][axis]
            require(preserved==changed['after'],'Own aggregate unrelated metadata changed')
    state_refs = index(state['reference_summary'],'lang','aggregate')
    for language,reference in new_refs.items():
        if language in added_references or language == own_language:
            for kind in ('fast','small'):
                for axis in ('x','y'):
                    equal_number(reference[kind][axis],aggregate(after,reference,kind,axis),
                                 'New or expanded aggregate '+axis+' differs')
            if language == own_language:
                # Coverage changes are admitted explicitly, not inferred merely
                # because an aggregate's old value no longer matches.
                groups = [b['key'] for b in after['benchmarks'] if any(g['language']==language for g in b['groups'])]
                require(reference.get('measured_benchmarks') == groups, 'Own aggregate coverage differs')
        else:
            require(reference == state_refs[language], 'Existing aggregate timing/metadata changed')
    return boundaries


def reverse_boundary(current, boundary):
    """Restore derived x only; retain separately admitted expanded coverage."""
    norm = boundary['normalization']
    workload, old_base, new_base = norm['benchmark'],norm['before'],norm['after']
    bench = index(current['benchmarks'],'key','workload')[workload]
    require(bench['baseline_loc'] == new_base, 'Normalization history is missing, reordered or discontinuous')
    affected = {g['language'] for g in bench['groups']}
    references = index(current['reference_summary'],'lang','aggregate')
    for language in affected & set(references):
        for kind in ('fast','small'):
            equal_number(references[language][kind]['x'],aggregate(current,references[language],kind),
                         'Current aggregate x differs')
    for (pool,key) in boundary['program_before']:
        require(key in current[pool] and positive(current[pool][key].get('x')),
                'Previously normalized positive coordinate is missing')
    for pool in ('programs','program_inventory'):
        for key,row in current[pool].items():
            if row['benchmark'] != workload or not positive(row.get('x')):
                continue
            equal_number(row['x'],row['loc']/new_base,'Current program x differs')
            if type(row.get('publication_record')) is dict:
                require(row['publication_record'].get('loc') == row['loc'] and
                        row['publication_record'].get('x') == row['x'], 'Current publication x differs')
            prior = boundary['program_before'].get((pool,key),row['loc']/old_base)
            equal_number(prior,row['loc']/old_base,'Historical canonical source count changed')
            row['x'] = prior
            if type(row.get('publication_record')) is dict:
                row['publication_record']['x'] = boundary['publication_before'].get((pool,key),prior)
    bench['baseline_loc'] = old_base
    for language in affected & set(references):
        reference = references[language]
        prior = boundary['reference_before'].get(language)
        for kind in ('fast','small'):
            value = aggregate(current,reference,kind)
            # Exact historical values preserve existing digest invariants when
            # the endpoint/coverage metadata is unchanged. Expanded coverage
            # has already been bound to a later successful admission snapshot.
            if prior is not None and strip_reference_x(reference) == strip_reference_x(prior):
                equal_number(value,prior[kind]['x'],'Historical aggregate x differs')
                value = prior[kind]['x']
            reference[kind]['x'] = value


def reverse_transition(current, before, after, audit):
    # Convenience for pure single-admission callers; file replay uses the
    # already validated boundaries returned by validate_transition.
    added = {pool:set(after[pool])-set(before[pool]) for pool in ('programs','program_inventory')}
    refs = set(index(after['reference_summary'],'lang','aggregate'))-set(index(before['reference_summary'],'lang','aggregate'))
    boundaries = validate_transition(before,after,audit,added,refs)
    for boundary in reversed(boundaries):
        reverse_boundary(current,boundary)


def validate_registry(history):
    require(type(history) is dict and set(history) == {'schema','admissions'} and
            history['schema'] == 'canonical-loc-normalization-history-v1' and
            type(history['admissions']) is list, 'Invalid normalization history')
    seen = set()
    for entry in history['admissions']:
        require(type(entry) is dict and set(entry) == {'audit_key','success'} and
                isinstance(entry['audit_key'],str) and entry['audit_key'] not in seen,
                'Duplicate or malformed normalization admission')
        seen.add(entry['audit_key'])
        ref = entry['success']
        require(type(ref) is dict and set(ref) == {'path','sha256'} and
                isinstance(ref['sha256'],str) and re.fullmatch('[0-9a-f]{64}',ref['sha256']),
                'Invalid successful-apply reference')
        safe_path(ref['path'])
    return history


def historical_view(root, data):
    """Return a validated copy used ONLY by legacy preservation checks."""
    root = Path(root)
    history_path = root/HISTORY
    active = {key for key in ADAPTERS if key in data}
    if not history_path.exists():
        require(not active, 'Admitted normalization requires a saved successful-apply history')
        return data
    history = validate_registry(strict_json(read_bytes(root, HISTORY)))
    events, seen, latest_references, admitted_workloads, latest_endpoints = [], set(), {}, set(), {}
    for entry in history['admissions']:
        key = entry['audit_key']
        require(key in ADAPTERS and key not in seen and key in data,
                'Unregistered, duplicate or absent normalization admission')
        seen.add(key)
        success = strict_json(checked(root, entry['success']))
        require(success.get('status') == 'applied' and success.get('catalog_changed') is True and
                success['audit'] == data[key], 'History does not bind the successful current admission')
        if success['audit'].get('schema')=='retained-language-catalog-admission-v1':
            require(key==success['audit']['language']+'_retained_publication_audit','Admission key/language mismatch')
        base = str(safe_path(entry['success']['path']).parent)
        before = strict_json(checked(root, dict(path=base+'/before/'+CATALOG,
                                               sha256=success['originals'][CATALOG])))
        after = strict_json(checked(root, dict(path=base+'/after/'+CATALOG,
                                              sha256=success['prepared'][CATALOG])))
        require(after.get(key) == success['audit'] and key not in before,
                'Snapshot admission identity differs')
        require({k for k in ADAPTERS if k in before} == seen-{key},
                'Snapshot admission order differs')
        for prior_key in seen-{key}:
            require(before[prior_key] == data[prior_key], 'Earlier normalization audit changed')
        # The existing driver also pins language metadata; verify its retained
        # payloads without making them a substitute for source/count evidence.
        for phase, pins in (('before', 'originals'), ('after', 'prepared')):
            checked(root, dict(path=base+'/'+phase+'/'+LANGUAGES, sha256=success[pins][LANGUAGES]))
        added, references = ADAPTERS[key](root, success['audit'], before, after)
        boundaries = validate_transition(before, after, success['audit'], added, references)
        added = additions_by_pool(added)
        admitted_workloads.update(success['audit'].get('endpoints',
            {item['benchmark']:None for item in normalization_items(success['audit'])}))
        # Newly admitted source measurements must remain the exact qualified
        # rows too; the older archive checks do not know these identities.
        for pool in ('programs', 'program_inventory'):
            for identity in added[pool]:
                require(identity in data[pool], 'Admitted source row is missing')
                validate_new_row(data,pool,identity)
                current_raw = raw_row(data[pool][identity])
                for field, value in raw_row(after[pool][identity]).items():
                    require(field in current_raw and current_raw[field] == value,
                            'Admitted raw source/timing field changed: '+identity+'.'+field)
                for source_key in after[pool][identity].get('files', []):
                    require(data['files'].get(source_key) == after['files'][source_key],
                            'Admitted counted source bytes changed')
        events.extend(boundaries)
        endpoints=success['audit'].get('endpoints')
        if endpoints is None:
            endpoints={success['audit']['normalization']['benchmark']:success['audit']['endpoint']}
        for workload,group in endpoints.items():
            latest_endpoints[workload,group['language']]=group
        for reference in after['reference_summary']:
            latest_references[reference['lang']] = reference
    require(seen == active, 'Normalization history omits an admitted rebase')
    # Check the real present-day minimum before introducing historical axes.
    for workload in admitted_workloads:
        bench = index(data['benchmarks'], 'key', 'workload')[workload]
        require(bench['baseline_loc'] == minimum(data, bench), 'Current canonical minimum differs')
    current_benches=index(data['benchmarks'],'key','workload')
    for (workload,language),group in latest_endpoints.items():
        groups=[value for value in current_benches[workload]['groups'] if value['language']==language]
        require(groups==[group],'Current admitted endpoint group differs')
    current_references = index(data['reference_summary'],'lang','aggregate')
    for language,reference in latest_references.items():
        require(language in current_references and
                strip_reference_x(current_references[language]) == strip_reference_x(reference),
                'Current aggregate coverage/timing lacks a recorded admission: '+language)
        for kind in ('fast','small'):
            for axis in ('x','y'):
                equal_number(current_references[language][kind][axis],
                             aggregate(data,current_references[language],kind,axis),
                             'Current aggregate '+axis+' differs')
    result = copy.deepcopy(data)
    for boundary in reversed(events):
        reverse_boundary(result,boundary)
    return result
