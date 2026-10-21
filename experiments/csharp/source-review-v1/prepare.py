#!/usr/bin/env python3
"""Replay source identities and seal bounded native cases without invoking .NET."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
PACKETS = ('spectral-scratch-v1', 'knucleotide-general-v1', 'regex-managed-v1',
           'regex-generated-v1', 'revcomp-short-read-v1')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path):
    return '\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n'


def section(value, start, stop):
    return value[value.index(start):value.index(stop)]


def literals(value):
    """Only decode the ordinary quoted-literal subset in these exact arrays."""
    return [json.loads(token) for token in re.findall(r'"(?:[^"\\]|\\.)*"', value)]


def build():
    pins = {}

    def bind(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, 'Changed input: ' + str(path))
        name = str(path.relative_to(ROOT))
        require(name not in pins or pins[name] == digest, 'Conflicting input identity')
        pins[name] = digest
        return name

    def read(path, expected=None):
        bind(path, expected)
        return json.loads(path.read_bytes())

    bind(Path(__file__))
    review = read(HERE / 'review.json')
    for row in review['inspected_profiles'] + review['protected_profiles']:
        for source in row['source_bundle']:
            bind(ROOT / source['path'], source['sha256'])
    catalog_pin = next(pin for pin in review['inputs'] if pin['path'] == 'data/benchmarks.json')
    bind(ROOT / catalog_pin['path'], catalog_pin['sha256'])
    corpus = read(CORPUS, CORPUS_SHA)
    extra = read(ROOT / 'experiments/ocaml/fixtures-v1/manifest.json')
    schedules = []
    for packet in PACKETS:
        folder = HERE.parent / packet
        proposal = read(folder / 'proposal.json')
        for key in ('source', 'project', 'upstream_license', 'source_review'):
            pin = proposal[key]
            bind(ROOT / pin['path'], pin['sha256'])
        project = ET.parse(folder / 'app.csproj').getroot()
        require(project.findtext('./PropertyGroup/TargetFramework') == 'net10.0'
                and project.findtext('./PropertyGroup/EnableDefaultCompileItems') == 'false'
                and project.findtext('./ItemGroup/Compile', default=None) is not None,
                'Unexpected project source/target policy')
        require([item.attrib['Include'] for item in project.findall('./ItemGroup/Compile')]
                == ['source/Program.cs'], 'Additional benchmark source is not accounted for')
        cases = [(case, CORPUS.parent) for case in corpus['cases']
                 if case['benchmark'] == proposal['benchmark']]
        if proposal['benchmark'] == 'knucleotide':
            cases += [(case, ROOT / 'experiments/ocaml/fixtures-v1') for case in extra['cases']
                      if case['benchmark'] == 'knucleotide']
        require(len(cases) == proposal['bounded_cases_per_mode'], 'Missing bounded case')
        for mode in proposal['execution_modes']:
            for case, base in cases:
                paths = {}
                for key in ('stdin', 'expected'):
                    if key in case:
                        item = case[key]
                        path = base / item['path']
                        require(path.resolve().is_relative_to(base) and path.stat().st_size == item['bytes'],
                                'Invalid or escaping case artifact')
                        paths[key] = bind(path, item['sha256'])
                rejection = case['expected_exit'] == 'nonzero'
                schedules.append(dict(candidate=proposal['id'], mode=mode,
                    benchmark=case['benchmark'], case=case['case'], n=case['n'],
                    input_kind=case['input_kind'], artifacts=paths,
                    check='capture-only-awaiting-CSharp-rejection-adapter' if rejection else case['validation'],
                    qualified=False))
    require(len(schedules) == 208, 'Changed complete candidate schedule')
    require(sum(row['check'].startswith('capture-only') for row in schedules) == 14,
            'Malformed-input cases cannot be silently accepted or omitted')

    base = ROOT / 'archive/comparisons/remaining-languages-comparison/20261011/sources/csharp'
    spectral = text(base / 'spectralnorm-csharpcore-5-arm64-faithful.cs')
    scratch = text(HERE.parent / 'spectral-scratch-v1/source/Program.cs')
    anchor = '        [MethodImpl(MethodImplOptions.AggressiveInlining)]'
    stop = '        private static void mult_AtAv'
    spectral_preserved = section(spectral, anchor, stop) == section(scratch, anchor, stop)
    knucleotide = text(base / 'knucleotide-csharpcore-1-arm64-faithful.cs')
    general = text(HERE.parent / 'knucleotide-general-v1/source/Program.cs')
    update_preserved = section(knucleotide, '    [MethodImpl(', '    static Task<string> Count(') == section(general, '    [MethodImpl(', '    static Task<string> Count(')
    summary_preserved = section(knucleotide, '    static string WriteFrequencies', '    public static void Main') == section(general, '    static string WriteFrequencies', '    public static void Main')
    masks = [(int(width), int(mask, 0)) for width, mask in re.findall(r'Count\((\d+), (0b[01]+|\d+),', general)]
    require(sorted(width for width, _ in masks) == [1, 2, 3, 4, 6, 12, 18]
            and all(mask == (1 << (2 * (width - 1))) - 1 for width, mask in masks),
            'Wrong complete width set or prior-window rolling mask')
    pcre = text(base / 'regexredux-csharpcore-2-arm64-faithful.cs')
    expected_patterns = literals(section(pcre, '        var regexes = new[]', '        var counts ='))
    expected_substitutions = literals(section(pcre, '            var replacements =', '            return replacements.Aggregate'))
    managed = text(HERE.parent / 'regex-managed-v1/source/Program.cs')
    generated = text(HERE.parent / 'regex-generated-v1/source/Program.cs')
    actual_patterns = literals(section(managed, '        string[] patterns', '        foreach (string pattern'))
    actual_substitutions = literals(section(managed, '        (string Pattern', '        string changed'))
    generated_patterns = [json.loads(token) for token in re.findall(r'\[GeneratedRegex\(("(?:[^"\\]|\\.)*")', generated)]
    require(len(expected_patterns) == 9 and len(expected_substitutions) == 10
            and actual_patterns == expected_patterns and actual_substitutions == expected_substitutions
            and generated_patterns == ['>[^\n]*\n|\n', *expected_patterns, *expected_substitutions[::2]],
            'Regex literal sequence differs from retained source')
    revcomp = text(base / 'revcomp-csharpcore-9-arm64-faithful.cs')
    fixed = text(HERE.parent / 'revcomp-short-read-v1/source/Program.cs')
    start = '    [MethodImpl(MethodImplOptions.AggressiveInlining)]\n    private static int ReadBlock('
    end = '\n    public static byte[] ToASCII'
    headerless = fixed[fixed.index('//* The Computer Language Benchmarks Game'):]
    unchanged_remainder = headerless.replace(section(headerless, start, end), section(revcomp, start, end)) == revcomp
    require(spectral_preserved and update_preserved and summary_preserved and unchanged_remainder,
            'Unrelated numeric/update/output/vector source changed')
    diagnostic = HERE.parent / 'revcomp-short-read-v1/diagnostic-v1'
    read(diagnostic / 'plan.json')
    bind(HERE.parent / 'revcomp-short-read-v1/ReadBlockDiagnostic.cs')
    bind(HERE.parent / 'revcomp-short-read-v1/prepare_probe.py')
    for path in diagnostic.rglob('*'):
        if path.is_file():
            bind(path)
    return dict(schema='csharp-source-and-bounded-preparation.v1',
        status='prepared-not-executed', pins=dict(sorted(pins.items())),
        source_checks=dict(spectral_numeric_bodies_preserved=spectral_preserved,
            dictionary_update_and_summaries_preserved=update_preserved and summary_preserved,
            complete_widths_and_masks_preserved=True, regex_literal_order_preserved=True,
            reverse_complement_remainder_preserved=unchanged_remainder,
            comparison='Exact source text after trimming trailing whitespace; no native parser or lowering claim.'),
        pending_candidate_executions=208, pending_success_cases=194,
        pending_language_rejection_captures=14, pending_helper_diagnostic_processes=4,
        helper_check_pairs_per_process=18, schedule=schedules,
        native_controller_qualified=False, native_processes_started=0,
        subject_executions=0, benchmark_samples=0, chart_admission=False,
        source_count_qualified=False, source_work_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    path = HERE / 'preparation-v1.json'
    if args.check:
        require(json.loads(path.read_bytes()) == result, 'Prepared source/case schedule differs')
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'prepared',
        candidate_executions_pending=208, source_checks='passed', native_processes_started=0)))
