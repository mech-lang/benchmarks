#!/usr/bin/env python3
"""Bind source-accounting findings to the published catalog without changing LOC."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path('experiments/source-size-audit/v1')
SUPPORT_DISPOSITIONS = {'separate-support', 'separate-authored-library'}
ABI_INDICATORS = re.compile(
    r'__gmpz_|pcre2_(?:compile|match|jit|substitute|code_free)|'
    r'\bforeign import (?:capi|ccall)\b|\b(?:DllImport|LibraryImport)\s*\(|'
    r'ffiCall:|\bffi-lib\b|\bctypes\b|\bffi\.cdef\b|'
    r'\bforeign import\s+\w+\s+"|\bbind\s*\(\s*C\b|'
    r'\bextern\s+"[cC]"|pragma\s+Import\s*\(\s*C|'
    r'extern\s+proc|@cImport|FFI::|\bFiddle\b', re.IGNORECASE)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def source_role(program, digest, source):
    metadata = program.get('file_roles', {}).get(digest, source)
    role = metadata.get('role', 'application') if isinstance(metadata, dict) else metadata
    count = metadata.get('normalized_loc') if isinstance(metadata, dict) else None
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError(f'Invalid recorded source count: {program["key"]}/{digest}')
    # Existing runtime-support annotations explicitly exclude these files.
    # No count is invented for a source whose per-file normalization is absent.
    charged = role != 'runtime-support'
    return role, count, charged


def analyze(root=ROOT):
    root = Path(root)
    raw = (root / 'data/benchmarks.json').read_bytes()
    data = json.loads(raw)
    if 'source_accounting' in data:
        import source_accounting
        data = source_accounting.historical_catalog(root, data)
        import gzip
        raw = gzip.decompress((root / source_accounting.PACKET / 'before.json.gz').read_bytes())
    review = json.loads((root / 'data/source-size-review.json').read_text())
    if review['catalog_sha256'] != sha(raw):
        raise ValueError('Review is bound to a different catalog; review new source changes first')
    programs = dict(data['programs'])
    for key, program in data.get('program_inventory', {}).items():
        if key in programs and programs[key] != program:
            raise ValueError(f'Conflicting program identity: {key}')
        programs[key] = program
    files = data['files']
    if set(review['support_units']) & set(review['embedded_units']):
        raise ValueError('Support and embedded review identities overlap')
    for digest, source in files.items():
        if source['sha256'] != digest or sha(source['code'].encode()) != digest:
            raise ValueError(f'Catalog source bytes do not match their identity: {digest}')
    source_uses = collections.defaultdict(list)
    source_paths = collections.defaultdict(list)
    profile_rows, support_candidates = [], set()
    per_file_complete = 0
    for key, program in sorted(programs.items()):
        program_id = re.sub(r'[^A-Za-z0-9_.-]+', '-', program['id']).strip('.') or 'source'
        directory = Path('programs') / program['language'] / program['benchmark'] / program_id
        manifest = json.loads((root / directory / 'program.json').read_text())
        if manifest['key'] != key or [s['sha256'] for s in manifest['sources']] != program['files']:
            raise ValueError(f'Exported source manifest differs: {key}')
        units, normalized = [], []
        support_charge, mixed_charge, configuration_charge = 0, 0, 0
        support_unknown = False
        for index, digest in enumerate(program['files']):
            source = files[digest]
            path = directory / manifest['sources'][index]['file']
            if sha((root / path).read_bytes()) != digest:
                raise ValueError(f'Exported source differs: {path}')
            source_paths[digest].append(path.as_posix())
            role, count, charged = source_role(program, digest, source)
            if index > 0 or role != 'application':
                support_candidates.add(digest)
            decision = review['support_units'].get(digest)
            if decision:
                if decision['recommended_accounting'] in SUPPORT_DISPOSITIONS and charged:
                    if count is None:
                        support_unknown = True
                    else:
                        support_charge += count
                elif decision['category'] == 'workload-specific-mixed' and charged:
                    mixed_charge += count or 0
                elif decision['category'] == 'configuration' and charged:
                    configuration_charge += count or 0
            unit = dict(sha256=digest, name=source['name'], role=role,
                        recorded_normalized_loc=count, currently_charged=charged,
                        exported_source=path.as_posix(),
                        review_category=decision['category'] if decision else None)
            units.append(unit)
            source_uses[digest].append(dict(program=key, language=program['language'],
                                           selected_for_chart=key in data['programs'],
                                           role=role, currently_charged=charged,
                                           recorded_normalized_loc=count))
            normalized.append(count if charged else 0)
        complete = all(type(n) is int for n in normalized)
        if complete:
            if sum(normalized) != program['loc']:
                raise ValueError(f'Recorded file counts do not sum to profile LOC: {key}')
            per_file_complete += 1
        profile_rows.append(dict(
            program=key, language=program['language'], benchmark=program['benchmark'],
            selected_for_chart=key in data['programs'], published_loc=program['loc'],
            published_seconds=program.get('seconds'), per_file_counts_complete=complete,
            included_generic_support_normalized_loc=support_charge,
            included_generic_support_count_incomplete=support_unknown,
            included_mixed_helper_normalized_loc=mixed_charge,
            included_configuration_normalized_loc=configuration_charge,
            embedded_review_files=[h for h in program['files'] if h in review['embedded_units']],
            files=units))
    if support_candidates != set(review['support_units']):
        raise ValueError('Support-file review does not cover exactly the attached support candidates')
    reviewed = {}
    for digest, decision in sorted({**review['support_units'], **review['embedded_units']}.items()):
        source = files[digest]
        lines = source['code'].splitlines()
        for span in decision.get('evidence_line_ranges', []):
            if not 1 <= span['start'] <= span['end'] <= len(lines):
                raise ValueError(f'Review line range outside exact source: {digest}')
        uses = source_uses[digest]
        reviewed[digest] = dict(
            name=source['name'], sha256=digest, source=sorted(source_paths[digest])[0],
            languages=sorted({u['language'] for u in uses}),
            source_line_count=len(lines), **decision, uses=uses)
    screening = []
    for digest, source in sorted(files.items()):
        hits = [n for n, line in enumerate(source['code'].splitlines(), 1)
                if ABI_INDICATORS.search(line)]
        if hits:
            screening.append(dict(sha256=digest, name=source['name'],
                                  languages=sorted({u['language'] for u in source_uses[digest]}),
                                  indicator_lines=hits, content_reviewed=digest in reviewed))
    language_rows = []
    for language in sorted({p['language'] for p in profile_rows}):
        rows = [p for p in profile_rows if p['language'] == language]
        affected = [p for p in rows if p['included_generic_support_normalized_loc'] > 0]
        support = [u for h, u in reviewed.items() if h in review['support_units']
                   and language in u['languages']]
        embedded = [u for h, u in reviewed.items() if h in review['embedded_units']
                    and language in u['languages'] and u['category'] != 'direct-library-use']
        language_rows.append(dict(
            language=language, profiles=len(rows), selected_profiles=sum(p['selected_for_chart'] for p in rows),
            support_units=len(support), embedded_binding_units=len(embedded),
            charged_generic_support_profiles=len(affected),
            charged_support_range=[min(p['included_generic_support_normalized_loc'] for p in affected),
                                   max(p['included_generic_support_normalized_loc'] for p in affected)]
                                  if affected else None,
            excluded_support_units=sum(any(not use['currently_charged'] for use in u['uses']
                                           if use['language'] == language) for u in support)))
    affected = [p for p in profile_rows if p['included_generic_support_normalized_loc'] > 0]
    totals = dict(
        profiles=len(programs), selected_profiles=len(data['programs']), source_files=len(files),
        exported_source_copies=sum(len(p['files']) for p in profile_rows),
        language_variants=len(language_rows), language_families=len({l.get('family', l['key']) for l in data['languages']}),
        attached_support_units_reviewed=len(review['support_units']),
        embedded_or_direct_use_units_reviewed=len(review['embedded_units']),
        fully_attributed_normalized_profiles=per_file_complete,
        profiles_without_complete_per_file_counts=len(programs) - per_file_complete,
        single_source_profiles_without_per_file_counts=sum(
            not p['per_file_counts_complete'] and len(p['files']) == 1 for p in profile_rows),
        multiple_source_profiles_without_per_file_counts=sum(
            not p['per_file_counts_complete'] and len(p['files']) > 1 for p in profile_rows),
        profiles_with_charged_generic_support=len(affected),
        variants_with_charged_generic_support=len({p['language'] for p in affected}),
        main_source_files_with_reviewed_embedded_bindings=sum(u['category'].startswith('embedded-') for h,u in reviewed.items()),
        review_categories=dict(sorted(collections.Counter(u['category'] for u in reviewed.values()).items())))
    return dict(schema='benchmark-source-size-audit.v1', status=review['status'],
                review_date=review['review_date'], catalog_commit=review['catalog_commit'],
                catalog_sha256=sha(raw), review_sha256=sha((root / 'data/source-size-review.json').read_bytes()),
                methodology='Existing normalized counts are reported verbatim. No physical or heuristic counts substitute for qualified normalized source counts.',
                limitations=review['scope_limitations'], totals=totals,
                languages=language_rows, reviewed_sources=reviewed,
                native_binding_screening=screening, profiles=profile_rows)


def render(report):
    t = report['totals']
    lines = ['# Source-size accounting audit', '',
             'The published LOC metric includes reusable support for some languages and excludes comparable support for others. The difference affects source-size comparisons independently of runtime performance.', '',
             f'The audit is bound to catalog commit `{report["catalog_commit"]}` and catalog SHA-256 `{report["catalog_sha256"]}`. It inspects {t["profiles"]:,} profiles across {t["language_variants"]} execution variants, {t["source_files"]} source files and {t["exported_source_copies"]:,} exported source copies. Every attached non-primary/support unit ({t["attached_support_units_reviewed"]}) received a content review; {t["embedded_or_direct_use_units_reviewed"]} additional primary-source units received targeted binding/direct-use review.', '',
             '**Status: findings only. Published source counts, chart coordinates, source bytes and timing observations are unchanged.**', '',
             '## Included reusable support', '',
             'The following counts come from existing per-file normalization evidence. A range covers different profiles, not measurement uncertainty. These are support-code charges, not newly approved application LOC deductions. Mixed workload helpers and runtime directives are reported separately.', '',
             '| Execution variant | Profiles charging generic support | Included support LOC per affected profile |',
             '| --- | ---: | ---: |']
    for row in report['languages']:
        if row['charged_generic_support_profiles']:
            low, high = row['charged_support_range']
            count = str(low) if low == high else f'{low}–{high}'
            lines.append(f'| {row["language"]} | {row["charged_generic_support_profiles"]} | {count} |')
    lines += ['', 'Clojure, Kotlin and Elixir charge complete shared support modules, including services a particular workload does not use. Gleam charges its I/O and launcher layer in every profile and additional storage/task/regex bindings as needed. Lua charges an entire 218-line GMP compatibility module to each of four pi-digits profiles. Earlier Lean profiles include `Common.lean` and `Format.c` in every bundle; later profiles remove unused helpers, so only five later profiles retain native helper charges.', '',
              'For example, one Lua pi profile has 281 published LOC, comprising 63 application lines and 218 binding lines. Clojure compact binary trees has 89, comprising 43 application and 46 shared support lines. These source splits are already recorded; changing the ranking metric still requires a consistent policy.', '',
              '## Support already excluded elsewhere', '',
              'Futhark, Mojo, BQN/K, Elm, MATLAB and Swift exclude general helpers, adapters or dependency configuration from application LOC. The audited excluded launchers do not contain the benchmark algorithm. Their current treatment is inconsistent with charging the comparable Luau host or Gleam/Prolog launch layer.', '',
              'A second distinction matters: Futhark excludes authored bigint, map, formatting and regex implementations, and Mojo excludes an authored integer map as well as native bindings. Those are substantial general library implementations, not just launch glue or preinstalled standard libraries. Their provenance and separate library size should remain visible. General API names alone do not establish that a helper is an external dependency.', '',
              'Mech built-in and standard-library implementations are also outside its application counts, as are installed runtimes and libraries for other languages. A separate authored-library accounting rule must apply consistently to comparable Mech library additions. Having no attached helper file does not prove that a program has no supporting implementation.', '',
              '## Embedded bindings', '',
              'Separate-file accounting alone misses general bindings written inside the application file. Content review found examples in Ada, C#, F#, D, Fortran, Haskell, Julia, Odin, Pascal, Python, Racket, Rust, Smalltalk and Zig. The source ranges below identify evidence, not complete normalized partitions. Direct library use in Swift and a Chapel CTypes import were also reviewed and do not establish an extra handwritten wrapper.', '',
              '| Source | Languages | Evidence lines | Content |', '| --- | --- | --- | --- |']
    for source in report['reviewed_sources'].values():
        if source['category'].startswith('embedded-'):
            spans = ', '.join(f'{s["start"]}–{s["end"]}' for s in source['evidence_line_ranges'])
            lines.append(f'| [{source["name"]}](../{source["source"]}) | {", ".join(source["languages"])} | {spans} | {source["reason"]} |')
    lines += ['', '## Workload logic and configuration', '',
              'The Prolog `clbg_records.pl` module is mixed: generic line handling and string assembly sit beside FASTA header/comment recognition and literal `>THREE` selection. The FASTA-specific sections must remain application code. Its 34 normalized lines cannot all be subtracted as generic support.', '',
              'Likewise, pi extraction/recurrence helpers, tree construction/checks, DNA complement tables, workload pattern lists and the prescribed replacement sequence remain application logic even when they call a native library. Racket’s spigot-specific compose macros are distinct from its general arithmetic syntax wrapper.', '',
              'Two Pony profiles include five legacy test-package compatibility alias lines. Two APL profiles charge a one-line workspace system-limit setting. The former belongs in support; the latter needs a configuration rule consistent with the existing meaningful-pragma policy. No setting is silently removed by this audit.', '',
              '## Proposed accounting boundary', '',
              'Record application/workload LOC, reusable support LOC and authored library LOC separately, with total authored LOC available. Track third-party dependencies and configuration separately from authored application source. Apply the same roles to embedded source sections and separate files. Application call sites and workload-specific helpers continue to count; moving benchmark logic to a native helper cannot erase its source cost or establish a pure named-language implementation.', '',
              'Before changing published coordinates, qualify normalized splits for embedded/mixed sections, agree how authored general libraries enter the main metric, and recompute affected endpoint selection and fixed LOC baselines. This is source-accounting work and does not require rerunning saved timing samples.', '',
              '## Coverage and reproduction', '',
              f'Existing per-file normalized counts sum exactly to profile LOC for {t["fully_attributed_normalized_profiles"]} profiles. Another {t["single_source_profiles_without_per_file_counts"]} have a single attached source, so their recorded total requires no cross-file partition. The remaining {t["multiple_source_profiles_without_per_file_counts"]} multi-source profiles exclude support without complete per-file normalized counts; their total including excluded support cannot be recovered by subtraction. Missing normalized counts are not replaced with physical-line estimates. Native-binding text screening is a discovery aid, not a semantic proof for every source or installed dependency.', '',
              'Rebuild or check the hash-bound audit:', '', '```sh', 'python3 tools/audit_source_size.py', 'python3 tools/audit_source_size.py --check', '```', '',
              'The [structured report](../experiments/source-size-audit/v1/report.json) contains every profile/file relationship, current charging role, recorded normalized counts, evidence ranges and language-level totals. The [review decisions](../data/source-size-review.json) bind content judgments to exact source hashes.', '',
              'This audit does not recertify historical compiler/runtime implementations, inspect every installed dependency, or claim that all possible inline reusable helpers have been identified.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify retained audit outputs without modifying them')
    args = parser.parse_args()
    report = analyze()
    outputs = {OUTPUT / 'report.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n',
               Path('docs/source-size-audit.md'): render(report)}
    for relative, content in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_text() != content:
                raise SystemExit(f'Audit output differs: {relative}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(json.dumps(dict(status='AUDIT_VERIFIED' if args.check else 'AUDIT_WRITTEN',
                          **report['totals']), ensure_ascii=False))


if __name__ == '__main__':
    main()
