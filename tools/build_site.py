#!/usr/bin/env python3
"""Build the static explorer from its editable source and recorded dataset."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
from source_metrics import canonical, metadata_for, partition_text, totals

ROOT = Path(__file__).resolve().parents[1]
SOURCE_METRICS_PATH = Path('experiments/source-metrics/v1/metrics.json')

# The canonical catalog also contains admission ledgers and producer closures.
# The explorer reads this view; the complete recorded catalog remains in data/.
# Keep source text, LOC owners, samples and evidence links inline for inspection.
BROWSER_FIELDS = frozenset({
    'schema', 'schema_version', 'languages', 'benchmarks', 'programs',
    'program_inventory', 'files', 'repository', 'archive_paths', 'protocol',
    'reference_summary', 'source_accounting',
})
PROGRAM_FIELDS = frozenset({
    'key', 'id', 'benchmark', 'language', 'loc', 'loc_metric', 'physical_loc', 'x', 'y',
    'seconds', 'samples', 'timing_sd', 'timing_summary', 'sample_details',
    'files', 'file_roles', 'report', 'report_sha256', 'source_report', 'loc_report',
    'binary_sha256', 'runtime_arguments', 'command', 'execution_mode', 'measured_backend',
    'formatted_loc', 'formatted_loc_status', 'formatted_loc_complete',
    'formatted_loc_evidence', 'formatted_x', 'eligible_for_chart', 'exclusion_reason',
    'loc_expansions', 'loc_expansion_format', 'source_url', 'source_link_label',
    'license_url', 'local_adaptation', 'source_provenance', 'algorithm', 'authorship',
    'runtime_policy', 'runtime_support',
    'timing_alias_of', 'source_alias_of', 'aliased_sample_source',
    'native_observations', 'distinct_optimization_claimed', 'source_alias_note',
    'separate_fresh_samples_required', 'source_accounting',
})
FILE_ROLE_FIELDS = frozenset({
    'role', 'source_path', 'name', 'path', 'code', 'sha256', 'physical_loc',
    'normalized_loc', 'loc_note', 'source_url', 'support_category',
    'included_in_application_loc', 'bundle_normalized_loc', 'support_normalized_loc',
    'support_line_ranges',
})


def pick(value, fields):
    return {key: item for key, item in value.items() if key in fields}


def browser_loc_audit(program):
    """Keep the three renderLocAudit formats, including exact displayed text."""
    audit = program['loc_expansions']
    if not isinstance(audit, list):
        return audit
    if program.get('loc_expansion_format') == 'source-bound-canonical-owner-audit-v1':
        result = []
        for source in audit:
            row = pick(source, {'source', 'name', 'sha256', 'source_language',
                               'physical_loc', 'normalized_loc'})
            for field in ('expansions', 'canonical_events'):
                if field in source:
                    row[field] = [pick(owner, {'full_owner_start', 'start', 'kind',
                                              'units', 'original_source'})
                                  for owner in source[field]]
            result.append(row)
        return result
    if any(isinstance(source.get('source'), str) and isinstance(source.get('expansions'), list)
           for source in audit):
        return [dict(pick(source, {'source', 'name', 'sha256', 'source_language',
                                  'physical_loc', 'normalized_loc'}),
                     expansions=[pick(owner, {'line', 'units', 'original', 'reason'})
                                 for owner in source['expansions']])
                for source in audit]
    return [pick(owner, {'line', 'extra_lines', 'units', 'reason', 'original'}) for owner in audit]


def browser_program(program):
    row = pick(program, PROGRAM_FIELDS)
    for field, fields in (('formatted_loc_evidence', {'reasons'}), ('algorithm', {'reason'})):
        if isinstance(row.get(field), dict):
            row[field] = pick(row[field], fields)
    if isinstance(row.get('file_roles'), dict):
        row['file_roles'] = {key: pick(value, FILE_ROLE_FIELDS) if isinstance(value, dict) else value
                             for key, value in row['file_roles'].items()}
    if 'loc_expansions' in row:
        row['loc_expansions'] = browser_loc_audit(program)
    return row


def validate_timing_aliases(catalog):
    """Check explicit shared observations; source aliases can have fresh samples.

    The supported timing aliases name a direct owner in the same workload and
    language, with the same recorded samples, source bundle and coordinates.
    Missing optional coordinates must stay missing on both rows. No alias or
    observation is inferred from equal numbers or shared source bytes.
    """
    pools = [catalog.get(name, {}) for name in ('program_inventory', 'programs')]
    programs = {key: row for pool in pools for key, row in pool.items()}
    fields = ('benchmark', 'language', 'samples', 'seconds', 'timing_sd', 'x', 'y',
              'loc', 'physical_loc', 'formatted_loc', 'formatted_x', 'files')
    def fail(key, detail):
        raise ValueError('Invalid timing alias ' + key + ': ' + detail)
    for pool in pools:
        for key, row in pool.items():
            owner_key = row.get('timing_alias_of')
            if owner_key is None:
                continue
            if (type(owner_key) is not str or not owner_key or owner_key == key
                    or row.get('key') != key or owner_key not in programs):
                fail(key, 'explicit different existing owner required')
            owner = programs[owner_key]
            if owner.get('key') != owner_key or owner.get('timing_alias_of') is not None:
                fail(key, 'owner must directly own the observations')
            if type(row.get('native_observations')) is not int or row['native_observations'] != 0:
                fail(key, 'alias must record zero additional native observations')
            if 'aliased_sample_source' in row and row['aliased_sample_source'] != owner_key:
                fail(key, 'sample source differs from timing owner')
            for field in fields:
                if (field in row) != (field in owner):
                    fail(key, field + ' presence differs from owner')
                if field in row and json.dumps(row[field], sort_keys=True, allow_nan=False) != json.dumps(owner[field], sort_keys=True, allow_nan=False):
                    fail(key, field + ' differs from owner')


def bind_source_metrics(catalog, catalog_raw, report, report_raw=None):
    """Fail closed on stale source/count evidence without recomputing BPE.

    Validate exact catalog/tool bindings and every source partition against the
    current retained source text, roles and line ranges. The report owns gzip
    and tokenizer measurements; their method pins and report digest are emitted
    with the browser view. No compiler, tokenizer or benchmark is launched.
    """
    def fail(detail):
        raise ValueError('Invalid source metrics: ' + detail)
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    if report.get('schema') != 'benchmark-source-metrics.v1':
        fail('unsupported schema')
    if report.get('catalog_sha256') != sha(catalog_raw) or json.loads(catalog_raw) != catalog:
        fail('catalog SHA-256 differs; regenerate the bound report')
    tool = ROOT/'tools/source_metrics.py'
    if not tool.is_file() or report.get('tool_sha256') != sha(tool.read_bytes()):
        fail('measurement tool SHA-256 differs; regenerate the bound report')
    programs = {**catalog.get('program_inventory', {}), **catalog['programs']}
    if set(report.get('profiles', {})) != set(programs):
        fail('profile set differs')
    tokenized = report.get('tokenizer', {}).get('status') == 'available'
    for key, program in programs.items():
        profile = report['profiles'][key]
        if (profile.get('key') != key or profile.get('language') != program['language']
                or profile.get('benchmark') != program['benchmark']):
            fail(key + ': identity differs')
        retained = profile.get('retained_application_loc', {})
        if (retained.get('value') != program['loc']
                or retained.get('metric') != program.get('loc_metric', 'unspecified-legacy')
                or retained.get('status') != 'retained-not-uniformly-recertified'):
            fail(key + ': retained LOC qualification differs')
        formatted = profile.get('canonical_formatted_loc', {})
        complete = program.get('formatted_loc_complete') is True
        evidence = program.get('formatted_loc_evidence')
        if (formatted.get('complete') is not complete
                or formatted.get('value') != (program.get('formatted_loc') if complete else None)
                or formatted.get('status') != program.get('formatted_loc_status', 'unavailable')
                or formatted.get('evidence_sha256') != (sha(canonical(evidence)) if evidence else None)):
            fail(key + ': formatter qualification differs')
        units = profile.get('files', [])
        if [unit.get('source_sha256') for unit in units] != program['files']:
            fail(key + ': source bundle differs')
        for digest, unit in zip(program['files'], units):
            source = catalog['files'][digest]
            text = source['code']
            if sha(text.encode('utf-8')) != digest or source.get('sha256', digest) != digest:
                fail(key + ': retained source SHA-256 differs')
            metadata, role, included = metadata_for(program, digest, source)
            if metadata.get('code', text) != text or metadata.get('sha256', digest) != digest:
                fail(key + ': displayed per-file source override differs from bound source')
            spans = metadata.get('support_line_ranges', [])
            application, excluded, selected = partition_text(text, spans) if included else ('', text, [])
            if (unit.get('role') != role or unit.get('included_in_application') is not included
                    or unit.get('application_line_ranges') != selected
                    or unit.get('embedded_support_line_ranges') != spans):
                fail(key + ': application/source partition differs')
            for scope, fragment in [('submitted', text), ('application', application), ('excluded_support', excluded)]:
                measured = unit.get(scope, {})
                raw = fragment.encode('utf-8')
                if any(measured.get(field) != value for field, value in {
                    'sha256': sha(raw), 'utf8_bytes': len(raw),
                    'unicode_codepoints': len(fragment), 'physical_lines': len(fragment.splitlines()),
                }.items()):
                    fail(key + ': ' + scope + ' source metrics differ')
                if (type(measured.get('gzip_bytes')) is not int or measured['gzip_bytes'] < 0
                        or not re.fullmatch('[0-9a-f]{64}', str(measured.get('gzip_sha256')))):
                    fail(key + ': invalid gzip evidence')
                tokens = measured.get('cl100k_base_tokens')
                if (tokenized and (type(tokens) is not int or tokens < 0)) or (not tokenized and tokens is not None):
                    fail(key + ': tokenizer availability/count differs')
        for scope in ('submitted', 'application', 'excluded_support'):
            if profile.get(scope) != totals(units, scope):
                fail(key + ': ' + scope + ' totals differ from measured files')
    metadata = {name: report[name] for name in (
        'schema', 'catalog_sha256', 'tool_sha256', 'source_boundary_policy',
        'scope_definition', 'compression', 'tokenizer', 'uniform_logical_loc',
        'language_lexical_tokens') if name in report}
    metadata['report_path'] = SOURCE_METRICS_PATH.as_posix()
    metadata['report_sha256'] = sha(report_raw if report_raw is not None else canonical(report))
    return metadata, report['profiles']


def browser_data(catalog, *, source_metrics=None, catalog_raw=None, metrics_raw=None):
    """Project the recorded catalog without mutating or recomputing observations.

    Both ordered program maps remain intact: their order drives source browsing.
    Only chart/selection inputs and displayed inspector details are included.
    Full receipt objects, repeated publication records and unrendered proof
    ledgers remain in the unchanged canonical catalog. No samples or coordinates
    are recomputed, and all source text and rendered owner text are preserved.
    """
    for field in ('languages', 'benchmarks', 'programs', 'files'):
        if field not in catalog:
            raise ValueError('Missing browser catalog field: ' + field)
    validate_timing_aliases(catalog)
    result = {key: value for key, value in catalog.items() if key in BROWSER_FIELDS}
    for field in ('programs', 'program_inventory'):
        if field in result:
            result[field] = {key: browser_program(row) for key, row in result[field].items()}
    if source_metrics is not None:
        if catalog_raw is None:
            raise ValueError('Exact catalog bytes are required to bind source metrics')
        result['source_metrics'], profiles = bind_source_metrics(catalog, catalog_raw, source_metrics, metrics_raw)
        for pool in ('programs', 'program_inventory'):
            for key, row in result.get(pool, {}).items():
                row['source_metrics'] = profiles[key]
    reproduction=ROOT/'data/reproducibility.json'
    if reproduction.exists():
        index=json.loads(reproduction.read_text())
        # Fixture builds and other catalogs never inherit unrelated recipes.
        catalog_programs={**catalog.get('program_inventory',{}),**catalog['programs']}
        result['reproducibility']={key:pick(row,{'source_sha256','version_label','host','recorded_at','status','missing'}) for key,row in index['programs'].items()
            if key in catalog_programs and row['source_sha256']==catalog_programs[key]['files']}
    return result


def browser_payload(catalog, **bindings):
    return (json.dumps(browser_data(catalog, **bindings), ensure_ascii=False, allow_nan=False,
                       separators=(',', ':')) + '\n').encode('utf-8')


def build():
    source = ROOT / 'site/src'
    output = ROOT / 'site/public'
    dataset = ROOT / 'data/benchmarks.json'
    catalog_raw = dataset.read_bytes()
    metrics_raw = (ROOT/SOURCE_METRICS_PATH).read_bytes()
    payload = browser_payload(json.loads(catalog_raw), catalog_raw=catalog_raw,
                              source_metrics=json.loads(metrics_raw), metrics_raw=metrics_raw)
    reproduction=ROOT/'data/reproducibility.json'
    recipe_payload=(json.dumps(json.loads(reproduction.read_text()),ensure_ascii=False,separators=(',',':'))+'\n').encode() if reproduction.exists() else None
    inputs = sorted(source.iterdir()) + [Path(__file__)]
    digest = hashlib.sha256()
    for path in inputs:
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    # A projection implementation or emitted-data change invalidates every
    # versioned asset, even when the canonical input happens to be unchanged.
    digest.update(b'\0data.json\0')
    digest.update(payload)
    if recipe_payload:
        digest.update(b'\0reproduction.json\0');digest.update(recipe_payload)
    version = digest.hexdigest()[:16]
    output.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if not path.is_file():
            continue
        if path.suffix in {'.html', '.mjs'}:
            text = path.read_text()
            text = re.sub(r"(\./[A-Za-z0-9_.-]+\.(?:mjs|css))(?:\?v=[A-Za-z0-9_.-]+)?", lambda m: m[1] + '?v=' + version, text)
            (output / path.name).write_text(text)
        else:
            shutil.copyfile(path, output / path.name)
    for path in (ROOT / 'site/reports').iterdir():
        if path.is_file():
            shutil.copyfile(path, output / path.name)
    (output / 'data.json').write_bytes(payload)
    # GitLab Pages negotiates this sidecar for clients accepting gzip. Keep the
    # original JSON for ordinary clients and exact local/browser parity checks.
    (output / 'data.json.gz').write_bytes(gzip.compress(payload, mtime=0))
    if recipe_payload:
        (output/'reproduction.json').write_bytes(recipe_payload)
        (output/'reproduction.json.gz').write_bytes(gzip.compress(recipe_payload,mtime=0))
    manifest = {'version': version, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.iterdir()) if p.is_file() and p.name != 'build.json'}}
    (output / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Built site/public ({len(manifest["files"])} files, {version})')
    return output


if __name__ == '__main__':
    build()
