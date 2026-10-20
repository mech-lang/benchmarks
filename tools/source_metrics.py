#!/usr/bin/env python3
"""Measure retained submitted/application source; never execute a benchmark.

This is additive accounting, not a new language-independent logical-LOC parser.
See docs/source-metrics.md for the boundaries and interpretation of each metric.
"""
import argparse
import ast
import collections
import copy
import csv
import gzip
import hashlib
import importlib.metadata
import io
import json
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = Path('experiments/source-metrics/v1')
TOKENIZER_VERSION = '0.12.0'
REGEX_VERSION = '2026.1.15'
BPE_SHA256 = '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7'
BPE_URL = 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken'
PATTERN = r"'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"
SPECIAL_TOKENS = {'<|endoftext|>': 100257, '<|fim_prefix|>': 100258,
                  '<|fim_middle|>': 100259, '<|fim_suffix|>': 100260,
                  '<|endofprompt|>': 100276}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def gzip_bytes(raw):
    """Level 9 gzip, mtime=0, no filename, fixed OS=255 via GzipFile.

    zlib versions can affect DEFLATE output; the report records the runtime pin.
    Each source unit/scope is compressed independently, without path metadata.
    """
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0, compresslevel=9) as stream:
        stream.write(raw)
    return buffer.getvalue()


def tokenizer(root=ROOT, enabled=True):
    spec = dict(name='cl100k_base', package='tiktoken', package_version=TOKENIZER_VERSION,
                regex_version=REGEX_VERSION, vocabulary_url=BPE_URL,
                vocabulary_sha256=BPE_SHA256,
                definition_sha256=sha(canonical(dict(pattern=PATTERN, special_tokens=SPECIAL_TOKENS))),
                special_token_policy='encode_ordinary; special-looking source is ordinary text',
                scope='Per-file source text; sum token counts without inserting filenames or separators.',
                bias='BPE vocabulary and Unicode spelling dependent; not language lexical tokens or a fairness score.')
    if not enabled:
        return None, dict(spec, status='disabled', reason='Explicit --tokenizer none.')
    try:
        import tiktoken
        from tiktoken.load import load_tiktoken_bpe
        versions = {name: importlib.metadata.version(name) for name in ('tiktoken', 'regex')}
        if versions != {'tiktoken': TOKENIZER_VERSION, 'regex': REGEX_VERSION}:
            raise ValueError('Expected pinned tiktoken/regex versions; found ' + str(versions))
        path = Path(root) / PACKET / 'cl100k_base.tiktoken'
        if sha(path.read_bytes()) != BPE_SHA256:
            raise ValueError('Pinned vocabulary SHA-256 differs')
        encoding = tiktoken.Encoding(name='cl100k_base', pat_str=PATTERN,
                    mergeable_ranks=load_tiktoken_bpe(str(path), expected_hash=BPE_SHA256),
                    special_tokens=SPECIAL_TOKENS)
        return encoding, dict(spec, status='available')
    except (ImportError, importlib.metadata.PackageNotFoundError, OSError, ValueError) as error:
        return None, dict(spec, status='unavailable', reason=str(error))


def measure(text, encoder=None):
    raw = text.encode('utf-8')
    compressed = gzip_bytes(raw)
    return dict(sha256=sha(raw), utf8_bytes=len(raw), unicode_codepoints=len(text),
                physical_lines=len(text.splitlines()), gzip_bytes=len(compressed),
                gzip_sha256=sha(compressed),
                cl100k_base_tokens=len(encoder.encode_ordinary(text)) if encoder else None)


def partition_text(text, ranges):
    """Keep exact original lines; never add padding, normalize newlines or lex.

    Return application and excluded fragments plus selected inclusive line ranges.
    Ranges refer to the exact hash-verified UTF-8 catalog source, not formatted text.
    """
    lines = text.splitlines(keepends=True)
    excluded = set()
    prior_end = 0
    for span in ranges:
        start, end = span['start'], span['end']
        if type(start) is not int or type(end) is not int or not (prior_end < start <= end <= len(lines)):
            raise ValueError('Support ranges must be ordered, disjoint and within source')
        excluded.update(range(start, end + 1))
        prior_end = end
    selected = []
    for number in range(1, len(lines) + 1):
        if number not in excluded:
            if selected and selected[-1]['end'] == number - 1:
                selected[-1]['end'] = number
            else:
                selected.append(dict(start=number, end=number))
    return (''.join(line for n, line in enumerate(lines, 1) if n not in excluded),
            ''.join(line for n, line in enumerate(lines, 1) if n in excluded), selected)


def metadata_for(row, digest, source):
    override = row.get('file_roles', {}).get(digest, {})
    if isinstance(override, str):
        override = {'role': override}
    metadata = {**source, **override}
    role = metadata.get('role', 'application')
    if role not in ('application', 'application-helper', 'runtime-setup', 'runtime-support'):
        raise ValueError('Unreviewed source role: ' + role)
    included = role != 'runtime-support'
    if 'included_in_application_loc' in metadata and metadata['included_in_application_loc'] != included:
        raise ValueError('Source role contradicts explicit application inclusion')
    return metadata, role, included


def totals(units, scope):
    # Empty/excluded units cost no gzip member in an application bundle.
    present = [unit[scope] for unit in units if unit[scope]['utf8_bytes']]
    fields = ('utf8_bytes', 'unicode_codepoints', 'physical_lines', 'gzip_bytes')
    result = {name: sum(unit[name] for unit in present) for name in fields}
    result['cl100k_base_tokens'] = (sum(unit['cl100k_base_tokens'] for unit in present)
                if all(unit[scope]['cl100k_base_tokens'] is not None for unit in units) else None)
    result['content_manifest_sha256'] = sha(canonical([
        dict(source_sha256=unit['source_sha256'], scope_sha256=unit[scope]['sha256'])
        for unit in units if unit[scope]['utf8_bytes']]))
    return result


def metric_profile(key, row, files, selected, encoder=None):
    units = []
    for digest in row['files']:
        source = files[digest]
        text = source['code']
        if sha(text.encode('utf-8')) != digest or source.get('sha256', digest) != digest:
            raise ValueError('Catalog source hash differs: ' + digest)
        metadata, role, included = metadata_for(row, digest, source)
        spans = metadata.get('support_line_ranges', [])
        application, excluded, selected_spans = partition_text(text, spans) if included else ('', text, [])
        unit = dict(source_sha256=digest, name=source['name'], role=role,
                    included_in_application=included,
                    application_line_ranges=selected_spans,
                    embedded_support_line_ranges=spans,
                    submitted=measure(text, encoder), application=measure(application, encoder),
                    excluded_support=measure(excluded, encoder))
        # Compression and BPE are not additive across a split; only raw sizes are.
        for field in ('utf8_bytes', 'unicode_codepoints'):
            if unit['submitted'][field] != unit['application'][field] + unit['excluded_support'][field]:
                raise ValueError('Partition does not conserve source text: ' + digest)
        units.append(unit)
    complete = row.get('formatted_loc_complete') is True
    formatted = row.get('formatted_loc') if complete else None
    if complete and (type(formatted) is not int or not row.get('formatted_loc_evidence')):
        raise ValueError('Qualified formatter count lacks evidence: ' + key)
    evidence = {name: row[name] for name in ('loc_report', 'loc_report_sha256', 'source_report') if row.get(name)}
    return dict(key=key, language=row['language'], benchmark=row['benchmark'],
                selected_for_chart=selected, eligible_for_chart=row.get('eligible_for_chart') is not False,
                timing_alias_of=row.get('timing_alias_of'),
                retained_application_loc=dict(value=row['loc'], metric=row.get('loc_metric', 'unspecified-legacy'),
                    status='retained-not-uniformly-recertified', physical_loc=row.get('physical_loc'),
                    evidence=evidence),
                canonical_formatted_loc=dict(value=formatted, complete=complete,
                    status=row.get('formatted_loc_status', 'unavailable'),
                    evidence_sha256=sha(canonical(row['formatted_loc_evidence'])) if row.get('formatted_loc_evidence') else None),
                submitted=totals(units, 'submitted'), application=totals(units, 'application'),
                excluded_support=totals(units, 'excluded_support'), files=units)


def load_function(path, name, namespace=None):
    """Read one pure historical scanner without importing a measurement runner."""
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = dict(namespace or {})
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


def normalization_audit(root=ROOT):
    """Counterexamples and positive controls, not a replacement universal lexer."""
    import source_accounting_counts as retained
    old = Path(root) / 'archive/workloads/nbody/run.py'
    strip_comments = load_function(old, 'strip_comments', {'re': re})
    physical = lambda source, lang: sum(bool(line.strip()) for line in strip_comments(source, lang).splitlines())
    probes = []
    def add(name, language, packed, expanded, count, relationship, explanation, path):
        left, right = count(packed), count(expanded)
        acceptance = dict(status='not-run', parser=None,
                          reason='Retained-counter probe only; native parser acceptance is not established here.')
        if language == 'python':
            ast.parse(packed); ast.parse(expanded)
            acceptance = dict(status='accepted', parser='CPython ast.parse',
                              version=sys.version.split()[0], sources_accepted=2)
        probes.append(dict(id=name, language=language, compact_source=packed, expanded_source=expanded,
                           compact_count=left, expanded_count=right,
                           desired_relationship=relationship,
                           aligned=(left == right) if relationship == 'equal' else None,
                           native_acceptance=acceptance, interpretation=explanation, counter_path=path))
    for language in ('python', 'julia'):
        add(language + '-independent-semicolon-statements', language, 'x = 1; y = 2\n', 'x = 1\ny = 2\n',
            lambda source, lang=language: retained.lexical_lines(source, lang)['normalized_loc'], 'equal',
            'Retained legacy lexical-line counting changes with packing independent assignments. This is a known logical-LOC gap.',
            'tools/source_accounting_counts.py:lexical_lines')
    add('mech-independent-semicolon-statements', 'mech', 'x := 1; y := 2\n', 'x := 1\ny := 2\n',
        lambda source: physical(source, 'mech'), 'syntax-unqualified',
        'Historical scanner returns these text counts, but native acceptance of this independent-semicolon form is unverified. This is not a confirmed Mech packing counterexample.',
        'archive/workloads/nbody/run.py:strip_comments + metrics')
    for language, left, right in (
        ('csharp', 'x=1; y=2;\n', 'x=1;\ny=2;\n'),
        ('fsharp', 'x <- 1; y <- 2\n', 'x <- 1\ny <- 2\n'),
        ('zig', 'x = 1; y = 2;\n', 'x = 1;\ny = 2;\n')):
        counter, count = retained.counter_for(language)
        add(language + '-independent-semicolon-statements', language, left, right,
            lambda source, fn=count: fn(source)['normalized_loc'], 'equal',
            'Positive control: retained counter expands these independent statements. This does not certify its entire grammar.',
            retained.COUNTERS[counter])
    _, fsharp = retained.counter_for('fsharp')
    add('fsharp-array-literal-wrapping', 'fsharp', 'let a=[|1;2;3;4|]\n', 'let a=[|1;2;\n3;4|]\n',
        lambda source: fsharp(source)['normalized_loc'], 'equal',
        'Literal separators are not executable statements, yet the retained baseline still charges extra wrapped literal rows.',
        retained.COUNTERS['cohort'])
    add('mech-matrix-literal-wrapping', 'mech', 'x := [1 2; 3 4]\n', 'x := [1 2;\n3 4]\n',
        lambda source: physical(source, 'mech'), 'equal',
        'Matrix row separators express data shape. The historical line scanner still changes with literal wrapping; it cannot decide logical ownership.',
        'archive/workloads/nbody/run.py:strip_comments + metrics')
    array_audit = 'archive/comparisons/array-comparison/all-20261009/audit_sources.py'
    paths = set(retained.COUNTERS.values()) | {'tools/source_accounting_counts.py',
             'archive/workloads/nbody/run.py', array_audit,
             'tools/qualification/apl_retained_source_units.py', 'tools/qualification/r_retained_source_units.py',
             retained.VENDOR + '/pygments/__init__.py', retained.VENDOR + '/pygments/lexers/_mapping.py'}
    return dict(status='gaps-demonstrated-not-uniform-logical-loc', benchmark_executions=0,
        probes=probes, counter_pins={path: sha((Path(root) / path).read_bytes()) for path in sorted(paths)},
        scope='Eight small source-counter probes; not compilation, source admission, exhaustive grammars or a full suite recount.',
        findings=[
            'Independent statements should have separate owners regardless of semicolons/newlines; positive controls and counterexamples differ across retained counters.',
            'Array/matrix literal separators, arguments and loop-control punctuation must not be expanded as independent workload statements.',
            'Succinct array primitives, reductions, compositions and pure expression functions are legitimate language constructs; do not expand implicit operations or invent scalar loops.',
            'BQN/K have exact-source manual packed-statement adjustments, not a general parser certificate. APL/R retained owner tools reject changed source hashes.',
            'Written headers/closes, expression-function bodies, callback blocks and literal wrapping follow different cohort rules. A native per-language owner specification is needed before one uniform logical ranking.',
            'Qualified native formatter counts remain a separate incomplete metric; unavailable formatters supply no substitute count.'])


def proposed_logical_policy():
    """A testable target policy; no speculative counts enter scored profiles."""
    return dict(schema='logical-source-owners.v1-draft', status='proposed-not-qualified',
        scope='Application source under the retained application/support boundary.',
        units=dict(independent_binding=1, expression_statement=1, control_header=1,
                   explicit_function_or_type_declaration=1, written_close=0,
                   literal_data_continuation=0, structural_separator=0),
        rules=[
            'Each independent written executable statement or binding owns one unit, regardless of semicolon, diamond or newline packing.',
            'A matrix or array literal is owned by its enclosing binding/expression once. Literal element/row separators and row wrapping add no units.',
            'A pure expression function binding owns one unit; its expression is not separately charged as an imperative body. A block function declaration owns one header plus independent body owners.',
            'Count explicit control headers plus their independent bodies; punctuation and the init/test/step inside a for header do not become additional statement owners.',
            'Each independently initialized binding counts; a destructuring pattern with one initializer is one binding. Chained written assignments need a native binding-owner decision.',
            'Closers and argument/index/list separators add zero units. Strings/comments/quoted data cannot create executable owners. Meaningful directives retain an explicit owner.',
            'Do not scalarize array primitives, reductions, compositions, implicit loops, installed library calls or glyph functions.',
            'Reject unknown/ambiguous source ownership and unaccepted fixtures; do not substitute physical lines.'],
        acceptance_cases=[
            dict(id='python-independent-statements', language='python', compact='x = 1; y = 2\n',
                 expanded='x = 1\ny = 2\n', expected_units=2, native_acceptance='CPython ast.parse in normalization_audit'),
            dict(id='mech-matrix-literal', language='mech', compact='x := [1 2; 3 4]\n',
                 expanded='x := [1 2;\n3 4]\n', expected_units=1, native_acceptance='required-before-qualification'),
            dict(id='matlab-matrix-literal', language='matlab', compact='x = [1 2; 3 4];\n',
                 expanded='x = [1 2;\n3 4];\n', expected_units=1, native_acceptance='required-before-qualification'),
            dict(id='fsharp-array-literal', language='fsharp', compact='let a=[|1;2;3;4|]\n',
                 expanded='let a=[|1;2;\n3;4|]\n', expected_units=1, native_acceptance='required-before-qualification'),
            dict(id='csharp-loop-header-and-body', language='csharp', compact='for(int i=0;i<n;i++) f(i);\n',
                 expanded='for(int i=0;i<n;i++)\n  f(i);\n', expected_units=2, native_acceptance='required-before-qualification')],
        qualification_required=['Native parser/reader acceptance of both members of each pair in valid enclosing contexts.',
            'Native owner ranges and zero unowned significant characters for every exact scored source.',
            'Independent embedded-support review, pinned tools/config/source/policy, and complete candidate recount before any rebase.'],
        departures_from_retained_policy='This proposed metric excludes written closing delimiters and literal continuation rows; it does not reinterpret existing canonical LOC.')


def build_report(data, raw, root=ROOT, encoder=None, tokenizer_spec=None, include_audit=True):
    original = copy.deepcopy(data)
    catalog = {**data.get('program_inventory', {}), **data['programs']}
    profiles = {key: metric_profile(key, row, data['files'], key in data['programs'], encoder)
                for key, row in sorted(catalog.items())}
    metric_types = collections.Counter(row['retained_application_loc']['metric'] for row in profiles.values())
    formats = collections.Counter(row['canonical_formatted_loc']['status'] for row in profiles.values())
    report = dict(schema='benchmark-source-metrics.v1', catalog_path='data/benchmarks.json',
        catalog_sha256=sha(raw), tool_sha256=sha(Path(__file__).read_bytes()), benchmark_executions=0,
        source_boundary_policy=data.get('source_accounting', {}).get('policy', 'retained-file-roles'),
        scope_definition=dict(submitted='All attached catalog source files, once per profile, including excluded support.',
            application='Included file roles with reviewed embedded support line ranges removed; original retained lines are concatenated within each file.',
            excluded_support='Separate support files plus removed embedded line fragments; not all installed runtime/library code.',
            raw_text='UTF-8 catalog text, including comments, whitespace, meaningful pragmas, BOM and original retained line endings. No lexical masking, whitespace or Unicode normalization.',
            aggregation='Per-file scope sizes summed. Gzip and BPE do not cross file boundaries; no filenames, tar headers or separators are added.'),
        compression=dict(format='gzip', level=9, mtime=0, filename='', os_byte=255,
            zlib_compile_version=zlib.ZLIB_VERSION, zlib_runtime_version=zlib.ZLIB_RUNTIME_VERSION,
            empty_units='No gzip member charged for an empty or excluded program scope; file records still disclose gzip(empty).',
            qualification='Deterministic with the recorded zlib implementation; different zlib versions may emit different DEFLATE bytes.'),
        tokenizer=tokenizer_spec or dict(status='unavailable', reason='No tokenizer supplied.'),
        language_lexical_tokens=dict(status='unavailable', value=None,
            reason='No qualified language-lexer token protocol across all languages; BPE tokens are a separate tokenizer-dependent metric.'),
        uniform_logical_loc=dict(status='unavailable', value=None,
            reason='Retained cohort rules differ; counterexamples are recorded in normalization_audit. Retained LOC is not recertified by copying it.'),
        proposed_logical_policy=proposed_logical_policy(),
        totals=dict(profiles=len(profiles), source_files=len(data['files']),
            language_variants=len({row['language'] for row in profiles.values()}),
            formatted_complete=sum(row['canonical_formatted_loc']['complete'] for row in profiles.values()),
            formatted_statuses=dict(sorted(formats.items())), retained_loc_metrics=dict(sorted(metric_types.items())),
            profiles_with_excluded_source=sum(row['excluded_support']['utf8_bytes'] > 0 for row in profiles.values())),
        normalization_audit=normalization_audit(root) if include_audit else None,
        profiles=profiles)
    if data != original:
        raise AssertionError('Measurement mutated catalog')
    return report


def csv_text(report):
    stream = io.StringIO(newline='')
    names = ['program', 'language', 'benchmark', 'selected_for_chart', 'retained_application_loc',
             'retained_loc_metric', 'canonical_formatted_loc', 'formatted_status']
    measures = ('utf8_bytes', 'unicode_codepoints', 'physical_lines', 'gzip_bytes', 'cl100k_base_tokens')
    names += [scope + '_' + name for scope in ('submitted', 'application', 'excluded_support') for name in measures]
    writer = csv.DictWriter(stream, names, lineterminator='\n'); writer.writeheader()
    for key, row in report['profiles'].items():
        output = dict(program=key, language=row['language'], benchmark=row['benchmark'],
            selected_for_chart=row['selected_for_chart'],
            retained_application_loc=row['retained_application_loc']['value'],
            retained_loc_metric=row['retained_application_loc']['metric'],
            canonical_formatted_loc=row['canonical_formatted_loc']['value'],
            formatted_status=row['canonical_formatted_loc']['status'])
        output.update({scope + '_' + name: row[scope][name]
                       for scope in ('submitted', 'application', 'excluded_support') for name in measures})
        writer.writerow(output)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare generated artifacts without writing them.')
    parser.add_argument('--tokenizer', choices=('cl100k_base', 'none'), default='cl100k_base')
    parser.add_argument('--require-tokenizer', action='store_true', help='Fail if pinned optional tokenizer is unavailable.')
    args = parser.parse_args()
    encoder, spec = tokenizer(enabled=args.tokenizer != 'none')
    if args.require_tokenizer and encoder is None:
        parser.error('Pinned tokenizer unavailable: ' + spec.get('reason', 'unknown'))
    raw = (ROOT / 'data/benchmarks.json').read_bytes()
    report = build_report(json.loads(raw), raw, encoder=encoder, tokenizer_spec=spec)
    outputs = {'metrics.json': json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
               'metrics.csv': csv_text(report)}
    for name, text in outputs.items():
        path = ROOT / PACKET / name
        if args.check:
            if not path.exists() or path.read_bytes() != text.encode('utf-8'):
                raise SystemExit(str(path.relative_to(ROOT)) + ' differs; regenerate with the pinned environment.')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode('utf-8'))
    print(json.dumps(dict(status='verified' if args.check else 'generated', **report['totals'],
                          tokenizer=spec['status'], benchmark_executions=0), sort_keys=True))


if __name__ == '__main__':
    main()
