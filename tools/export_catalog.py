#!/usr/bin/env python3
"""Export recorded programs, samples and workload definitions into readable folders."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]


def slug(value):
    return re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('.') or 'source'


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def timing_owners(catalog):
    owners = {}
    for key, program in catalog.items():
        owner_key = program.get('timing_alias_of')
        if owner_key is None:
            owners[key] = key
            continue
        owner = catalog.get(owner_key) if isinstance(owner_key, str) else None
        if (owner is None or owner_key == key or owner.get('timing_alias_of') is not None
                or program.get('key') != key or owner.get('key') != owner_key
                or type(program.get('native_observations')) is not int
                or program['native_observations'] != 0
                or ('aliased_sample_source' in program and program['aliased_sample_source'] != owner_key)
                or any(json.dumps(program.get(field), sort_keys=True, allow_nan=False)
                       != json.dumps(owner.get(field), sort_keys=True, allow_nan=False)
                       for field in ('language', 'benchmark', 'samples'))):
            raise ValueError(f'Invalid timing alias: {key}')
        owners[key] = owner_key
    return owners


def export(root=ROOT):
    root = Path(root).resolve()
    data = json.loads((root / 'data/benchmarks.json').read_text(encoding='utf-8'))
    for key, program in data.get('program_inventory', {}).items():
        if key in data['programs'] and data['programs'][key] != program:
            raise ValueError(f'Conflicting catalog identity: {key}')
    catalog = {**data['programs'], **data.get('program_inventory', {})}
    owners = timing_owners(catalog)
    # Validate every directory before writing: different IDs can normalize to
    # the same slug, including on case-insensitive filesystems.
    destinations = {}
    for key, program in sorted(catalog.items()):
        publication = program.get('publication_record')
        if 'publication_record' in program and (not isinstance(publication, dict) or 'timing_sd' not in publication):
            raise ValueError(f'Invalid publication record: {key}')
        for field in ('language', 'benchmark'):
            value = program[field]
            if value in ('.', '..') or not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
                raise ValueError(f'Unsafe {field} directory for {key}: {value!r}')
        relative = Path('programs') / program['language'] / program['benchmark'] / slug(program['id'])
        folded = relative.as_posix().casefold()
        if folded in destinations:
            raise ValueError(f'Program directory collision: {destinations[folded]} and {key} -> {relative}')
        destinations[folded] = key
        existing = root / relative / 'program.json'
        if existing.exists() and json.loads(existing.read_text(encoding='utf-8')).get('key') != key:
            raise ValueError(f'Program directory already belongs to another identity: {relative}')
        names = {'program.json'}
        for file_key in program['files']:
            source = data['files'][file_key]
            name = slug(Path(source['name']).name)
            if name.casefold() in names:
                name = file_key[:8] + '-' + name
            if name.casefold() in names:
                raise ValueError(f'Source filename collision for {key}: {name}')
            names.add(name.casefold())
            if hashlib.sha256(source['code'].encode('utf-8')).hexdigest() != source['sha256']:
                raise ValueError(f'Source hash mismatch for {key}: {source["path"]}')
    language_rows = {l['key']: [] for l in data['languages']}
    samples = []
    totals = []
    for key, program in sorted(catalog.items()):
        relative = Path('programs') / program['language'] / program['benchmark'] / slug(program['id'])
        directory = root / relative
        directory.mkdir(parents=True, exist_ok=True)
        sources = []
        names = {'program.json'}
        for file_key in program['files']:
            source = data['files'][file_key]
            content = source['code'].encode('utf-8')
            assert hashlib.sha256(content).hexdigest() == source['sha256'], source['path']
            name = slug(Path(source['name']).name)
            if name.casefold() in names:
                name = file_key[:8] + '-' + name
            names.add(name.casefold())
            (directory / name).write_bytes(content)
            role = program.get('file_roles', {}).get(file_key, source.get('role', 'application'))
            role_evidence = {'role_evidence': role} if isinstance(role, dict) else {}
            if isinstance(role, dict):
                role = role['role']
            sources.append({'file': name, 'sha256': source['sha256'],
                            'original_path': source['path'], 'role': role, **role_evidence})
        runs = program.get('samples', [])
        # New publication records retain the independently reviewed statistics,
        # including an explicit null for an incomplete sample cohort. Historical
        # records without this additive field keep their original export shape.
        publication = program.get('publication_record')
        sd = publication['timing_sd'] if publication is not None else statistics.stdev(runs) if len(runs) > 1 else None
        record = {'key': key, 'language': program['language'], 'benchmark': program['benchmark'],
                  'program': program['id'], 'loc': program.get('loc'),
                  'loc_metric': program.get('loc_metric', 'statement-normalized'),
                  'physical_loc': program.get('physical_loc'),
                  'seconds': program.get('seconds'), 'samples': runs,
                  'standard_deviation': sd,
                  'selected_for_chart': key in data['programs'],
                  'original_timing_report': program.get('report'),
                  'archive_timing_report': data.get('archive_paths', {}).get(program.get('report')),
                  'sources': sources}
        if publication is not None:
            record['publication_record'] = publication
        for field in ('source_accounting', 'authorship', 'timing_measurement', 'timing_correction', 'timing_alias_of',
                      'source_alias_of', 'aliased_sample_source', 'native_observations',
                      'distinct_optimization_claimed', 'source_alias_note',
                      'separate_fresh_samples_required'):
            if field in program:
                record[field] = program[field]
        save_json(directory / 'program.json', record)
        language_rows[program['language']].append((program, relative))
        totals.append([program['language'], program['benchmark'], program['id'], program.get('loc'),
                       program.get('physical_loc'), program.get('seconds'), record['standard_deviation'],
                       len(runs), int(key in data['programs']), relative.as_posix() + '/program.json',
                       program.get('timing_alias_of', '')])
        for number, seconds in enumerate(runs, 1):
            samples.append([program['language'], program['benchmark'], program['id'], number, seconds,
                            int(key in data['programs']), program.get('report', ''),
                            owners[key], program.get('timing_alias_of', '')])
    results = root / 'results/current'
    results.mkdir(parents=True, exist_ok=True)
    for name, header, rows in [
        ('programs.csv', ['language', 'benchmark', 'program', 'canonical_loc', 'physical_loc', 'median_seconds', 'sample_sd_seconds', 'sample_count', 'selected_for_chart', 'manifest', 'timing_alias_of'], totals),
        ('samples.csv', ['language', 'benchmark', 'program', 'run', 'seconds', 'selected_for_chart', 'original_report', 'timing_owner', 'timing_alias_of'], samples),
    ]:
        with (results / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream); writer.writerow(header); writer.writerows(rows)
    for language in sorted(data['languages'], key=lambda l: l['label'].casefold()):
        directory = root / 'programs' / language['key']
        directory.mkdir(parents=True, exist_ok=True)
        lines = ['# ' + language['label'], '', 'Recorded source bundles, grouped by workload. Each bundle has exact source hashes, timing samples and a link to its original report in `program.json`.', '',
                 '| Benchmark | Program | Canonical LOC | Median seconds | Samples |', '|---|---|---:|---:|---:|']
        for program, path in sorted(language_rows[language['key']], key=lambda row: (row[0]['benchmark'], row[0]['id'])):
            seconds = program.get('seconds')
            elapsed = f'{seconds:.6g}' if seconds is not None else '—'
            link = path.relative_to(Path('programs') / language['key']).as_posix()
            lines.append(f"| {program['benchmark']} | [{program['id']}]({link}/program.json) | {program.get('loc', '—')} | {elapsed} | {len(program.get('samples', []))} |")
        (directory / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for benchmark in data['benchmarks']:
        directory = root / 'benchmarks' / benchmark['key']
        save_json(directory / 'workload.json', {key: benchmark[key] for key in ('key', 'title', 'workload', 'baseline_loc', 'baseline_seconds')})
        (directory / 'README.md').write_text(f"# {benchmark['title']}\n\n{benchmark['workload']}.\n\nThe fixed chart baselines are {benchmark['baseline_seconds']:.9g} seconds and {benchmark['baseline_loc']} canonical source lines. Lower ratios are better.\n\nSource bundles are under [`programs/<language>/{benchmark['key']}/`](../../programs/). Recorded sample rows and per-program summaries are in [`results/current/`](../../results/current/). Historical full reports, output validation and compiler evidence remain in [`archive/`](../../archive/).\n", encoding='utf-8')
    (root / 'programs/README.md').write_text('# Benchmark programs\n\nExact measured source bundles, organized by language variant, workload, then program. `program.json` includes every source/helper, its original hash, all saved samples and provenance. These are recorded programs; a source bundle alone is not a portable build environment.\n\n' + '\n'.join(f"- [{l['label']}]({l['key']}/)" for l in sorted(data['languages'], key=lambda l: l['label'].casefold())) + '\n', encoding='utf-8')
    summary = {'language_variants': len(data['languages']), 'language_families': len({l.get('family', l['key']) for l in data['languages']}),
               'workloads': len(data['benchmarks']), 'programs_in_catalog': len(catalog), 'programs_selected_for_chart': len(data['programs']),
               'recorded_samples_in_catalog': len(samples), 'recorded_samples_selected_for_chart': sum(len(p.get('samples', [])) for p in data['programs'].values()),
               'source_files': len(data['files'])}
    summary.update(
        unique_recorded_samples_in_catalog=len({(owners[key], run) for key, program in catalog.items()
                                               for run in range(1, len(program.get('samples', [])) + 1)}),
        unique_recorded_samples_selected_for_chart=len({(owners[key], run) for key, program in data['programs'].items()
                                                        for run in range(1, len(program.get('samples', [])) + 1)}),
        timing_alias_programs=sum(owner != key for key, owner in owners.items()))
    save_json(results / 'summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT, help='repository root (default: parent of tools/)')
    export(parser.parse_args().repo)
