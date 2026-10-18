"""Replay retained source-count rules for reviewed application/support partitions."""
import ast
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = 'archive/qualification/nim/records/formatted-nim-plan-v1/jobs/actual-plans-v1/imports'
sys.path.insert(0, str(ROOT / VENDOR))
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Comment
import pygments

COUNTERS = {
    'cohort': 'archive/comparisons/remaining-languages-comparison/20261011/metrics_final.py',
    'zig': 'archive/comparisons/zig-odin-roc-elm-comparison/20261010/loc.py',
    'lisp': 'archive/comparisons/lisp-racket-comparison/20261010/loc_final.py',
    'd': 'archive/languages/d/20261011/loc.py',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    path = ROOT / COUNTERS[name]
    spec = importlib.util.spec_from_file_location('accounting_counter_' + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def partition(source, ranges, support):
    selected = lambda n: any(a <= n <= b for a, b in ranges)
    return ''.join(line if selected(n) == support else
                   ''.join(c if c in '\r\n' else ' ' for c in line)
                   for n, line in enumerate(source.splitlines(keepends=True), 1))


def lexical_lines(source, language):
    # Replays legacy run_remaining.source_metrics: preprocessor/attributes count.
    cleaned = ''.join('\n' * value.count('\n')
                      if token in Comment and token not in Comment.Preproc else value
                      for token, value in lex(source, get_lexer_by_name(
                          language, stripnl=False, ensurenl=False)))
    count = sum(bool(line.strip()) for line in cleaned.splitlines())
    return dict(normalized_loc=count, physical_loc=count, expansions=[])


def legacy_julia_count(source):
    # Extract only the old pure scanner, never import its measurement runner.
    path = ROOT / 'archive/workloads/nbody/run.py'
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'strip_comments')
    namespace = {'re': re}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return sum(bool(line.strip()) for line in namespace['strip_comments'](source, 'julia').splitlines())


def counter_for(language):
    language = language.removesuffix('-aot')
    if language in ('ada', 'fortran', 'pascal', 'smalltalk', 'csharp', 'fsharp'):
        return 'cohort', lambda source: load('cohort').normalize(source, language)
    if language in ('zig', 'odin'):
        return 'zig', lambda source: load('zig').normalize(source, language)
    if language == 'racket':
        return 'lisp', lambda source: load('lisp').normalize(source, language)
    if language == 'd':
        return 'd', lambda source: load('d').normalize(source)
    if language in ('python', 'rust', 'haskell', 'julia'):
        return 'legacy-pygments', lambda source: lexical_lines(source, language)
    raise ValueError('No retained source-count rule for ' + language)


def qualify(data, review):
    programs = {**data['programs'], **data.get('program_inventory', {})}
    results = {}
    for source_hash, decision in review['embedded_units'].items():
        if not decision['category'].startswith('embedded-'):
            continue
        owners = [p for p in programs.values() if source_hash in p['files']]
        language = owners[0]['language']
        source = data['files'][source_hash]['code']
        assert digest(source.encode()) == source_hash
        ranges = [(span['start'], span['end']) for span in decision['evidence_line_ranges']]
        name, count = counter_for(language)
        full = count(source)
        application = count(partition(source, ranges, False))
        support = count(partition(source, ranges, True))
        assert full['normalized_loc'] == application['normalized_loc'] + support['normalized_loc'], source_hash
        previous = sorted({p['loc'] for p in owners})
        correction = None
        if previous != [full['normalized_loc']]:
            # The old Julia scanner tested '#' before '#=', leaving block-comment
            # bodies counted as source. Require exact replay of that old bug.
            assert language == 'julia' and previous == [legacy_julia_count(source)], (source_hash, previous, full)
            correction = dict(previous_loc=previous[0], corrected_full_loc=full['normalized_loc'],
                              reason='Julia legacy scanner counted the six-line #= block-comment body as source; Pygments excludes it.')
        results[source_hash] = dict(
            source_sha256=source_hash, language=language, counter=name,
            support_line_ranges=decision['evidence_line_ranges'],
            previous_loc=previous[0], full_normalized_loc=full['normalized_loc'],
            application_loc=application['normalized_loc'], support_loc=support['normalized_loc'],
            application_physical_loc=application['physical_loc'], support_physical_loc=support['physical_loc'],
            application_expansions=application['expansions'], legacy_correction=correction,
            policy='Scope partition only; retained cohort normalization and semantic pragmas preserved.')
    # A mixed Prolog source already has exact native term-owner units. Keep the
    # module directive and FASTA-specific recognizers; separate generic line/join.
    path = ROOT / 'experiments/prolog/knucleotide-linear-v1/qualification/run-v1/source-projection-optimized.json'
    projection = json.loads(path.read_text())
    record = next(row for row in projection['files'] if row['source'].endswith('clbg_records.pl'))
    source_hash = record['source_sha256']
    assert source_hash == 'efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19'
    owners = record['projection']['canonical_events']
    generic = lambda line: 2 <= line <= 7 or 21 <= line <= 23
    support = sum(row['units'] for row in owners if generic(row['line']))
    application = sum(row['units'] for row in owners if not generic(row['line']))
    assert (application, support) == (21, 13)
    results[source_hash] = dict(source_sha256=source_hash, language='prolog',
        counter='retained-native-prolog-owners', previous_loc=34, full_normalized_loc=34,
        application_loc=application, support_loc=support, application_physical_loc=11,
        support_physical_loc=9, support_line_ranges=[dict(start=2, end=7), dict(start=21, end=23)],
        count_evidence=dict(path=path.relative_to(ROOT).as_posix(), sha256=digest(path.read_bytes())),
        owner_partition=[dict(line=row['line'], units=row['units'], kind=row['kind'],
                              role='support' if generic(row['line']) else 'application') for row in owners],
        legacy_correction=None)
    pins = {path: digest((ROOT / path).read_bytes()) for path in COUNTERS.values()}
    for relative in ['archive/workloads/nbody/run.py', 'archive/legacy-tools/run_remaining.py',
                     VENDOR + '/pygments/__init__.py', VENDOR + '/pygments/lexers/_mapping.py']:
        pins[relative] = digest((ROOT / relative).read_bytes())
    return dict(schema='benchmark-source-partitions.v1', status='SOURCE_PARTITIONS_RECONCILED',
                pygments_version=pygments.__version__, counters=pins, sources=results,
                source_bytes_changed=False, timing_processes=0)
