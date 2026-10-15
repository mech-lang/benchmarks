#!/usr/bin/env python3
"""Build the static explorer from its editable source and recorded dataset."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]

# The canonical catalog also contains admission ledgers and producer closures.
# The explorer reads this view; the complete recorded catalog remains in data/.
# Keep source text, LOC owners, samples and evidence links inline for inspection.
BROWSER_FIELDS = frozenset({
    'schema', 'schema_version', 'languages', 'benchmarks', 'programs',
    'program_inventory', 'files', 'repository', 'archive_paths', 'protocol',
    'reference_summary',
})
PROGRAM_FIELDS = frozenset({
    'key', 'id', 'benchmark', 'language', 'loc', 'physical_loc', 'x', 'y',
    'seconds', 'samples', 'timing_sd', 'timing_summary', 'sample_details',
    'files', 'file_roles', 'report', 'report_sha256', 'source_report', 'loc_report',
    'binary_sha256', 'runtime_arguments', 'command', 'execution_mode', 'measured_backend',
    'formatted_loc', 'formatted_loc_status', 'formatted_loc_complete',
    'formatted_loc_evidence', 'formatted_x', 'eligible_for_chart', 'exclusion_reason',
    'loc_expansions', 'loc_expansion_format', 'source_url', 'source_link_label',
    'license_url', 'local_adaptation', 'source_provenance', 'algorithm',
    'runtime_policy', 'runtime_support',
})
FILE_ROLE_FIELDS = frozenset({
    'role', 'source_path', 'name', 'path', 'code', 'sha256', 'physical_loc',
    'normalized_loc', 'loc_note', 'source_url',
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


def browser_data(catalog):
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
    result = {key: value for key, value in catalog.items() if key in BROWSER_FIELDS}
    for field in ('programs', 'program_inventory'):
        if field in result:
            result[field] = {key: browser_program(row) for key, row in result[field].items()}
    return result


def browser_payload(catalog):
    return (json.dumps(browser_data(catalog), ensure_ascii=False, allow_nan=False,
                       separators=(',', ':')) + '\n').encode('utf-8')


def build():
    source = ROOT / 'site/src'
    output = ROOT / 'site/public'
    dataset = ROOT / 'data/benchmarks.json'
    payload = browser_payload(json.loads(dataset.read_bytes()))
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
    manifest = {'version': version, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.iterdir()) if p.is_file() and p.name != 'build.json'}}
    (output / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Built site/public ({len(manifest["files"])} files, {version})')
    return output


if __name__ == '__main__':
    build()
