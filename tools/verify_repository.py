#!/usr/bin/env python3
"""Verify the portable benchmark catalog and preserved archive without running programs."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_COLUMNS = ['language', 'benchmark', 'program', 'canonical_loc', 'physical_loc', 'median_seconds',
                   'sample_sd_seconds', 'sample_count', 'selected_for_chart', 'manifest', 'timing_alias_of']
SAMPLE_COLUMNS = ['language', 'benchmark', 'program', 'run', 'seconds', 'selected_for_chart', 'original_report',
                  'timing_owner', 'timing_alias_of']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def safe_relative(value):
    path = PurePosixPath(value)
    require(bool(value) and not path.is_absolute() and '..' not in path.parts and '\\' not in value,
            f'Unsafe repository-relative path: {value!r}')
    return Path(*path.parts)


def slug(value):
    return re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('.') or 'source'


def preserve_fields(previous, current, label):
    require(isinstance(current, dict), f'Missing {label}')
    for key, value in previous.items():
        require(key in current and current[key] == value, f'Changed preserved {label} field: {key}')


def read_table(path, columns, delimiter=','):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        require(reader.fieldnames == columns, f'Unexpected columns in {path}')
        rows = list(reader)
    require(all(set(row) == set(columns) and all(value is not None for value in row.values()) for row in rows),
            f'Malformed rows in {path}')
    return rows


def check_csv(path, columns, expected):
    rows = read_table(path, columns)
    wanted = [{column: '' if value is None else str(value) for column, value in zip(columns, row)} for row in expected]
    require(rows == wanted, f'Recorded values, ordering or row count changed in {path}')
    return len(rows)


def check_timing_owner(catalog, key):
    """Resolve only a canonical explicit alias, independently of the exporter."""
    program = catalog[key]
    owner_key = program.get('timing_alias_of')
    if owner_key is None:
        return key
    label = f'Invalid canonical timing alias: {key}'
    require(type(owner_key) is str and bool(owner_key) and owner_key != key and owner_key in catalog, label)
    owner = catalog[owner_key]
    require(program.get('key') == key and owner.get('key') == owner_key
            and owner.get('timing_alias_of') is None, label)
    require(type(program.get('native_observations')) is int
            and program['native_observations'] == 0, label)
    require('aliased_sample_source' not in program or program['aliased_sample_source'] == owner_key, label)
    for field in ('language', 'benchmark', 'samples'):
        require(json.dumps(program.get(field), sort_keys=True, allow_nan=False)
                == json.dumps(owner.get(field), sort_keys=True, allow_nan=False), f'{label}: {field}')
    return owner_key


def check_migration(root, check_index):
    rows = read_table(root / 'migration/reorganization-paths.tsv',
                      ['original_path', 'current_path', 'git_blob', 'mode'], '\t')
    require(rows, 'The migration map is empty')
    original, current = set(), set()
    for row in rows:
        safe_relative(row['original_path'])
        destination = safe_relative(row['current_path'])
        require(row['original_path'] not in original, f'Duplicate original path: {row["original_path"]}')
        require(row['current_path'] not in current, f'Duplicate current path: {row["current_path"]}')
        original.add(row['original_path']); current.add(row['current_path'])
        require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', row['git_blob']), f'Invalid Git blob for {destination}')
        require(row['mode'] in {'100644', '100755', '120000', '160000'}, f'Invalid Git mode for {destination}')
        require((root / destination).exists() or (root / destination).is_symlink(), f'Missing archived path: {destination}')
    if check_index:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--stage', '-z'],
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        entries = {}
        for item in result.stdout.split(b'\0'):
            if not item:
                continue
            metadata, name = item.split(b'\t', 1)
            mode, blob, stage = metadata.decode('ascii').split()
            path = name.decode('utf-8', errors='surrogateescape')
            require(stage == '0', f'Unmerged Git index path: {path}')
            require(path not in entries, f'Duplicate Git index path: {path}')
            entries[path] = (mode, blob)
        for row in rows:
            require(entries.get(row['current_path']) == (row['mode'], row['git_blob']),
                    f'Archive index mode/blob mismatch: {row["current_path"]}')
    return rows


def check_previous(root, data):
    # Authorship is a later source-bound annotation. Replay the frozen admission
    # checks against the original measurement record without rewriting its
    # publication snapshot or relaxing any of its existing field comparisons.
    data={**data,**{pool:{key:{field:value for field,value in p.items() if field!='authorship'}
                         for key,p in data.get(pool,{}).items()}
                   for pool in ('programs','program_inventory')}}
    previous = read_json(root / 'archive/site/explorer/dist/data.json')
    spec = importlib.util.spec_from_file_location('interpreted_publication', root / 'tools/import_mech_interpreted_rerun.py')
    publication = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publication)
    normalization_spec = importlib.util.spec_from_file_location(
        'saved_normalization_history', root / 'tools/normalization_history_apl_trees.py')
    normalization = importlib.util.module_from_spec(normalization_spec)
    normalization_spec.loader.exec_module(normalization)
    # A rebase may change derived chart coordinates only. All legacy raw-field
    # and immediate-input checks run unchanged against validated historical axes.
    data = normalization.historical_view(root, data)
    replaced_interpreted = publication.verify_saved_publication(root, data, previous)
    benches = {b['key']: b for b in data['benchmarks']}
    for old in previous['benchmarks']:
        require(old['key'] in benches, f'Missing original benchmark: {old["key"]}')
        for field, value in old.items():
            if field.startswith('baseline_'):
                require(benches[old['key']].get(field) == value,
                        f'Changed original baseline: {old["key"]}.{field}')
    for section in ('programs', 'program_inventory', 'files'):
        for key, value in previous.get(section, {}).items():
            if section == 'programs' and key in replaced_interpreted:
                continue
            preserve_fields(value, data.get(section, {}).get(key), f'{section}.{key}')
    return len(previous['programs'])


def check_v(root, data, catalog, migration):
    forms = {key: p for key, p in catalog.items() if p['language'] == 'v'}
    selected = {key: p for key, p in data['programs'].items() if p['language'] == 'v'}
    require(len(forms) == 20 and len(selected) == 19, 'V must retain 20 forms and 19 selected endpoint programs')
    require(all(key in data.get('program_inventory', {}) for key in forms), 'V full inventory is incomplete')
    require(sum(len(p.get('samples', [])) for p in forms.values()) == 60, 'V saved sample count differs from 60')
    audit = data.get('v_audit', {})
    for field, expected in {'candidate_sources': 20, 'samples_per_source': 3, 'v_samples': 60,
                            'matched_mech_samples': 30, 'actual_full_native_processes': 90,
                            'source_or_timing_mutations': 0, 'historical_reports_mutated': False,
                            'baseline_changed': False}.items():
        require(audit.get(field) == expected, f'V audit mismatch: {field}')
    old_suite = 'benchmarks/clbg/' + audit['suite']
    suite_path = next((row['current_path'] for row in migration if row['original_path'] == old_suite), None)
    require(suite_path is not None, 'V original reconciliation report is absent from the migration map')
    suite = read_json(root / safe_relative(suite_path))
    require(suite.get('report_only') is True and suite.get('never_chart_eligible') is True
            and suite.get('chart_admission') is False, 'V historical policy flags changed')
    require(len(suite['benchmarks']) == 10, 'V reconciliation must cover ten workloads')
    controls = []
    for benchmark, evidence in suite['benchmarks'].items():
        candidates = [p for p in forms.values() if p['benchmark'] == benchmark]
        require(len(candidates) == 2, f'V source-form coverage changed: {benchmark}')
        control = [p for p in evidence['profiles'].values() if p['language'] == 'mech']
        require(len(control) == 1 and len(control[0]['samples_seconds']) == 3, f'V matched control missing: {benchmark}')
        controls.extend(control[0]['samples_seconds'])
        b = next((b for b in data['benchmarks'] if b['key'] == benchmark), None)
        require(b is not None, f'V benchmark is absent: {benchmark}')
        groups = [g for g in b['groups'] if g['language'] == 'v']
        require(len(groups) == 1, f'V comparison group is absent or repeated: {benchmark}')
        fast = min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))
        small = min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))
        require(groups[0]['fast'] == fast['key'] and groups[0]['small'] == small['key']
                and set(groups[0]['programs']) == {fast['key'], small['key']}, f'Incorrect V endpoint selection: {benchmark}')
        for p in candidates:
            old = evidence['profiles'].get(p['id'])
            require(old is not None and p['samples'] == old['samples_seconds']
                    and p['seconds'] == old['median_seconds'] and len(p['samples']) == 3,
                    f'V saved timing changed: {p["key"]}')
            require(p['seconds'] == statistics.median(p['samples']), f'V median differs from saved samples: {p["key"]}')
            require(p['matched_mech_control'] == control[0], f'V matched control changed: {p["key"]}')
            require(p['original_admission_policy'] == {'report_only': True, 'never_chart_eligible': True, 'chart_admission': False}
                    and p.get('chart_admission', {}).get('historical_reports_unchanged') is True,
                    f'V historical/publication distinction missing: {p["key"]}')
    require(len(controls) == 30, 'V matched Mech sample count differs from 30')
    return {'v_forms': len(forms), 'v_samples': 60, 'v_endpoint_programs': len(selected), 'matched_mech_samples': len(controls)}


def verify(root, check_index=False):
    root = Path(root).resolve()
    data = read_json(root / 'data/benchmarks.json')
    migration = check_migration(root, check_index)
    prior_programs = check_previous(root, data)
    for key, program in data.get('program_inventory', {}).items():
        require(key not in data['programs'] or data['programs'][key] == program, f'Conflicting catalog identity: {key}')
    catalog = {**data['programs'], **data.get('program_inventory', {})}
    if any('authorship' in p for p in catalog.values()):
        source_models=read_json(root/'data/source-model-evidence.json')['files']
        for key,p in catalog.items():
            a=p.get('authorship',{})
            require(a.get('schema')=='benchmark-authorship.v1' and a.get('source_sha256')==p['files'],
                    f'Authorship source binding differs: {key}')
            expected=[] if a.get('kind')=='upstream' else [row for f in p['files'] for row in source_models.get(f,[])]
            require(a.get('ai',{}).get('evidence')==expected and
                    a['ai']['models']==sorted({row['model'] for row in expected}),
                    f'Authorship model evidence differs: {key}')
    for key, source in data['files'].items():
        require(hashlib.sha256(source['code'].encode('utf-8')).hexdigest() == source['sha256'],
                f'Dataset source hash mismatch: {key}')
    expected_programs, expected_samples = [], []
    unique_samples, selected_unique_samples = set(), set()
    timing_aliases = 0
    manifests, destinations = set(), set()
    source_copies = 0
    for key, p in sorted(catalog.items()):
        require(p.get('key') == key, f'Program key mismatch: {key}')
        timing_owner = check_timing_owner(catalog, key)
        timing_aliases += timing_owner != key
        relative = safe_relative(f'programs/{p["language"]}/{p["benchmark"]}/{slug(p["id"])}')
        folded = relative.as_posix().casefold()
        require(folded not in destinations, f'Program directory collision: {relative}')
        destinations.add(folded)
        manifest_path = relative / 'program.json'; manifests.add(manifest_path.as_posix())
        record = read_json(root / manifest_path)
        runs = p.get('samples', [])
        publication = p.get('publication_record')
        if 'publication_record' in p:
            require(isinstance(publication, dict) and 'timing_sd' in publication, f'Invalid publication record: {key}')
        sd = publication['timing_sd'] if publication is not None else statistics.stdev(runs) if len(runs) > 1 else None
        sources, names = [], {'program.json'}
        for file_key in p['files']:
            source = data['files'][file_key]
            name = slug(Path(source['name']).name)
            if name.casefold() in names:
                name = file_key[:8] + '-' + name
            require(name.casefold() not in names, f'Source filename collision for {key}: {name}')
            names.add(name.casefold())
            exported = (root / relative / name).read_bytes()
            require(exported == source['code'].encode('utf-8')
                    and hashlib.sha256(exported).hexdigest() == source['sha256'], f'Exported source changed: {relative / name}')
            role = p.get('file_roles', {}).get(file_key, source.get('role', 'application'))
            role_evidence = {'role_evidence': role} if isinstance(role, dict) else {}
            if isinstance(role, dict):
                role = role['role']
            require(isinstance(role, str) and role, f'Invalid source role: {key}/{file_key}')
            sources.append({'file': name, 'sha256': source['sha256'], 'original_path': source['path'],
                            'role': role, **role_evidence})
            source_copies += 1
        expected_record = {'key': key, 'language': p['language'], 'benchmark': p['benchmark'], 'program': p['id'],
                           'loc': p.get('loc'), 'loc_metric': p.get('loc_metric', 'statement-normalized'),
                           'physical_loc': p.get('physical_loc'), 'seconds': p.get('seconds'), 'samples': runs,
                           'standard_deviation': sd, 'selected_for_chart': key in data['programs'],
                           'original_timing_report': p.get('report'),
                           'archive_timing_report': data.get('archive_paths', {}).get(p.get('report')), 'sources': sources}
        if publication is not None:
            expected_record['publication_record'] = publication
        for field in ('authorship', 'timing_measurement', 'timing_correction', 'timing_alias_of',
                      'source_alias_of', 'aliased_sample_source', 'native_observations',
                      'distinct_optimization_claimed', 'source_alias_note',
                      'separate_fresh_samples_required'):
            if field in p:
                expected_record[field] = p[field]
        require(record == expected_record, f'Exported program manifest changed: {manifest_path}')
        expected_programs.append([p['language'], p['benchmark'], p['id'], p.get('loc'), p.get('physical_loc'),
                                  p.get('seconds'), sd, len(runs), int(key in data['programs']), manifest_path.as_posix(),
                                  p.get('timing_alias_of', '')])
        for n, elapsed in enumerate(runs, 1):
            expected_samples.append([p['language'], p['benchmark'], p['id'], n, elapsed,
                                     int(key in data['programs']), p.get('report', ''), timing_owner,
                                     p.get('timing_alias_of', '')])
            unique_samples.add((timing_owner, n))
            if key in data['programs']:
                selected_unique_samples.add((timing_owner, n))
    actual_manifests = {path.relative_to(root).as_posix() for path in (root / 'programs').rglob('program.json')}
    require(actual_manifests == manifests, 'Exported catalog has missing or stale program manifests')
    program_count = check_csv(root / 'results/current/programs.csv', PROGRAM_COLUMNS, expected_programs)
    sample_count = check_csv(root / 'results/current/samples.csv', SAMPLE_COLUMNS, expected_samples)
    expected_summary = {'language_variants': len(data['languages']),
                        'language_families': len({l.get('family', l['key']) for l in data['languages']}),
                        'workloads': len(data['benchmarks']), 'programs_in_catalog': len(catalog),
                        'programs_selected_for_chart': len(data['programs']), 'recorded_samples_in_catalog': sample_count,
                        'recorded_samples_selected_for_chart': sum(len(p.get('samples', [])) for p in data['programs'].values()),
                        'source_files': len(data['files']),
                        'unique_recorded_samples_in_catalog': len(unique_samples),
                        'unique_recorded_samples_selected_for_chart': len(selected_unique_samples),
                        'timing_alias_programs': timing_aliases}
    require(read_json(root / 'results/current/summary.json') == expected_summary, 'Exported summary totals differ from the dataset')
    for benchmark in data['benchmarks']:
        expected = {key: benchmark[key] for key in ('key', 'title', 'workload', 'baseline_loc', 'baseline_seconds')}
        require(read_json(root / 'benchmarks' / benchmark['key'] / 'workload.json') == expected,
                f'Exported workload changed: {benchmark["key"]}')
    v_counts = check_v(root, data, catalog, migration)
    return {'status': 'passed', 'programs': program_count, 'samples': sample_count, 'source_files': len(data['files']),
            'exported_source_copies': source_copies, 'prior_programs_preserved': prior_programs,
            'migration_paths': len(migration), 'archive_index_checked': check_index, **v_counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT, help='repository root (default: parent of tools/)')
    parser.add_argument('--check-index', action='store_true', help='also compare every preserved archive mode/blob to the Git index')
    args = parser.parse_args()
    try:
        result = verify(args.repo, args.check_index)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f'Verification failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
