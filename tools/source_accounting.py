"""Apply and validate the application-LOC policy without changing source or timings."""
import copy
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = 'experiments/source-size-correction/v1'
POLICY = 'application-loc-v1'
SEPARATE = {'separate-support', 'separate-authored-library', 'retain-dependency-exclusion'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transform(before, review, partitions):
    data = copy.deepcopy(before)
    assert 'source_accounting' not in before
    catalog = {**data['programs'], **data.get('program_inventory', {})}
    changes = []
    for key, row in catalog.items():
        roles = copy.deepcopy(row.get('file_roles', {}))
        removed, removed_physical, removed_formatted = 0, 0, 0
        comment_adjustment = 0
        files = []
        for index, digest in enumerate(row['files']):
            source = data['files'][digest]
            original = roles.get(digest, source)
            metadata = copy.deepcopy(original) if isinstance(original, dict) else {'role': original}
            # File content remains in data.files. Role overrides carry metadata only.
            metadata = {k: v for k, v in metadata.items() if k not in ('code', 'archive_path', 'sha256')}
            old_role = metadata.get('role', 'application')
            decision = review['support_units'].get(digest)
            split = partitions['sources'].get(digest)
            if decision and decision['recommended_accounting'] in SEPARATE:
                charged = old_role != 'runtime-support'
                count = metadata.get('normalized_loc')
                if charged:
                    assert type(count) is int, (key, digest, 'missing source count')
                    removed += count
                    assert type(metadata.get('physical_loc')) is int
                    removed_physical += metadata['physical_loc']
                    if row.get('formatted_loc_complete') is True:
                        formatted_count = metadata.get('formatted_loc')
                        if formatted_count is None:
                            evidence = row['formatted_loc_evidence']['files']
                            assert all(f['status'] == 'qualified' and type(f['physical_loc']) is int for f in evidence)
                            assert sum(f['physical_loc'] for f in evidence) == row['formatted_loc']
                            formatted_count = next(f['physical_loc'] for f in evidence if f['published_file'] == digest)
                        assert type(formatted_count) is int, (key, 'missing helper formatter count')
                        removed_formatted += formatted_count
                metadata.update(role='runtime-support', source_path=metadata.get('source_path') or
                                source.get('archive_path') or source['path'],
                                support_category=decision['category'], included_in_application_loc=False,
                                loc_note='Reusable support/dependency source; excluded from application LOC. Original source is retained.')
                roles[digest] = metadata
                files.append(dict(sha256=digest, name=source['name'], category=decision['category'],
                                  application_loc=0, support_loc=count,
                                  previously_included=charged, support_line_ranges=None))
            elif split:
                old_unit = metadata.get('normalized_loc', row['loc'] if len(row['files']) == 1 else None)
                assert old_unit == split['previous_loc'], (key, old_unit, split['previous_loc'])
                removed += old_unit - split['application_loc']
                comment_adjustment += split['full_normalized_loc'] - old_unit
                if len(row['files']) == 1:
                    removed_physical = None
                else:
                    removed_physical += split['support_physical_loc']
                assert row.get('formatted_loc_complete') is not True, (key, 'embedded formatter partition required')
                metadata.update(role='application' if index == 0 else 'application-helper',
                    source_path=metadata.get('source_path') or source.get('archive_path') or source['path'],
                    normalized_loc=split['application_loc'], physical_loc=split['application_physical_loc'],
                    bundle_normalized_loc=split['full_normalized_loc'], support_normalized_loc=split['support_loc'],
                    support_line_ranges=split['support_line_ranges'], included_in_application_loc=True,
                    loc_note='Application LOC excludes the reviewed generic binding/library sections; workload logic remains counted.')
                roles[digest] = metadata
                files.append(dict(sha256=digest, name=source['name'], category='mixed-source',
                    application_loc=split['application_loc'], support_loc=split['support_loc'],
                    previously_included=True, support_line_ranges=split['support_line_ranges']))
        if files:
            old_loc = row['loc']
            row['loc'] = old_loc - removed
            assert type(row['loc']) is int and row['loc'] > 0, key
            if 'canonical_loc' in row:
                row['canonical_loc'] = row['loc']
            old_physical = row.get('physical_loc')
            if removed_physical is None:
                row['physical_loc'] = partitions['sources'][row['files'][0]]['application_physical_loc']
            elif old_physical is not None:
                row['physical_loc'] = old_physical - removed_physical
                assert row['physical_loc'] > 0
            if row.get('formatted_loc_complete') is True:
                row['formatted_loc'] -= removed_formatted
                assert row['formatted_loc'] > 0
            support_counts = [f['support_loc'] for f in files]
            row['file_roles'] = roles
            row['source_accounting'] = dict(
                policy=POLICY, application_loc=row['loc'], previous_loc=old_loc,
                previous_physical_loc=old_physical,
                support_loc=sum(n for n in support_counts if n is not None)
                            if all(n is not None for n in support_counts) else None,
                removed_loc=removed, lexical_correction=comment_adjustment,
                files=files, evidence=PACKET + '/partitions.json')
            if removed_formatted:
                row['source_accounting']['previous_formatted_loc'] = row['formatted_loc'] + removed_formatted
            if row['source_accounting']['removed_loc']:
                changes.append(dict(program=key, language=row['language'], benchmark=row['benchmark'],
                                    previous_loc=old_loc, application_loc=row['loc'], removed_loc=removed))
    # Aliases share the exact same source accounting; no observations are added.
    for pool in ('programs', 'program_inventory'):
        data[pool] = {key: catalog[key] for key in data.get(pool, {})}
    baselines = []
    for bench in data['benchmarks']:
        all_candidates = [catalog[key] for group in bench['groups'] for key in group['programs']
                          if catalog[key].get('eligible_for_chart') is not False]
        baseline = min(row['loc'] for row in all_candidates)
        baselines.append(dict(benchmark=bench['key'], previous=bench['baseline_loc'], application=baseline))
        bench['baseline_loc'] = baseline
        formatted = [row['formatted_loc'] for row in all_candidates
                     if row.get('formatted_loc_complete') is True and row.get('formatted_loc')]
        if formatted:
            bench['baseline_formatted_loc'] = min(formatted)
        for row in catalog.values():
            if row['benchmark'] != bench['key']:
                continue
            row['x'] = row['loc'] / baseline
            if row.get('formatted_loc_complete') is True:
                row['formatted_x'] = row['formatted_loc'] / bench['baseline_formatted_loc']
        for group in bench['groups']:
            candidates = [catalog[key] for key in group['programs']
                          if catalog[key].get('eligible_for_chart') is not False]
            timed = [row for row in candidates if row.get('seconds') is not None]
            if timed:
                group['fast'] = min(timed, key=lambda row: (row['seconds'], row['loc'], row['key']))['key']
            group['small'] = min(candidates, key=lambda row: (row['loc'], row.get('seconds') or math.inf, row['key']))['key']
            formatted = [row for row in candidates if row.get('formatted_loc_complete') is True]
            formatted_timed = [row for row in formatted if row.get('seconds') is not None]
            group['formatted_fast'] = min(formatted_timed, key=lambda row:(row['seconds'], row['formatted_loc'], row['key']))['key'] if formatted_timed else None
            group['formatted_small'] = min(formatted, key=lambda row:(row['formatted_loc'], row.get('seconds') or math.inf, row['key']))['key'] if formatted else None
    for section, prefix, axis in [('reference_summary', '', 'x'), ('formatted_reference_summary', 'formatted_', 'formatted_x')]:
        for reference in data.get(section, []):
            selected = reference.get('measured_benchmarks')
            groups = [group for bench in data['benchmarks'] if selected is None or bench['key'] in selected
                      for group in bench['groups'] if group['language'] == reference['lang']]
            for kind in ('fast', 'small'):
                rows = [catalog[group[prefix + kind]] for group in groups if group.get(prefix + kind)]
                if rows:
                    reference[kind] = dict(x=statistics.geometric_mean(row[axis] for row in rows),
                                           y=statistics.geometric_mean(row['y'] for row in rows))
    data['protocol']['metric'] = ('Application LOC: nonblank, noncomment source with the retained normalized statement rules. '
        'Reusable hosts, generic bindings and general libraries are excluded; workload-specific logic and meaningful pragmas count. '
        'Reviewed embedded sections follow the same policy as separate files. Prior counts remain in source_accounting metadata.')
    data['source_accounting'] = dict(schema='benchmark-source-accounting.v1', policy=POLICY,
        review='data/source-size-review.json', partitions=PACKET + '/partitions.json',
        before=PACKET + '/before.json.gz', changed_profiles=len(changes),
        policy_url='https://github.com/mech-lang/benchmarks/blob/main/docs/methodology.md#timing-and-source-size',
        timings_changed=False, source_bytes_changed=False)
    return data, dict(schema='benchmark-source-size-correction.v1', policy=POLICY,
                      changed_profiles=changes, baselines=baselines, timing_processes=0)


def historical_catalog(root, current):
    """Validate this correction before reconstructing records for older audits."""
    if 'source_accounting' not in current:
        return current
    root = Path(root)
    receipt = json.loads((root / PACKET / 'receipt.json').read_text())
    raw = gzip.decompress((root / PACKET / 'before.json.gz').read_bytes())
    assert sha(raw) == receipt['before_catalog_sha256'], 'Historical catalog hash differs'
    before = json.loads(raw)
    review_raw = (root / 'data/source-size-review.json').read_bytes()
    partitions_raw = (root / PACKET / 'partitions.json').read_bytes()
    assert sha(review_raw) == receipt['review_sha256']
    assert sha(partitions_raw) == receipt['partitions_sha256']
    expected, report = transform(before, json.loads(review_raw), json.loads(partitions_raw))
    if 'ruby_zjit_audit' in current:
        from qualification.import_ruby_zjit import append_catalog
        expected = append_catalog(expected, root)
    if 'bqn_knucleotide_audit' in current:
        from qualification.import_bqn_knucleotide import append_catalog
        expected = append_catalog(expected, root)
    if 'nim_knucleotide_audit' in current:
        from qualification.import_nim_knucleotide import append_catalog
        expected = append_catalog(expected, root)
    if 'matlab_regex_case_audit' in current:
        from qualification.import_matlab_regex import append_catalog
        expected = append_catalog(expected, root)
    if 'bqn_spectral_audit' in current:
        from qualification.import_bqn_spectral import append_catalog
        expected = append_catalog(expected, root)
    if 'bqn_fasta_audit' in current:
        from qualification.import_bqn_fasta import append_catalog
        expected = append_catalog(expected, root)
    if 'clojure_nbody_audit' in current:
        from qualification.import_clojure_nbody import append_catalog
        expected = append_catalog(expected, root)
    if 'futhark_knucleotide_eligibility' in current:
        from qualification.apply_futhark_knucleotide_eligibility import append_catalog
        expected = append_catalog(expected, root)
    if 'clojure_compact_audit' in current:
        from qualification.import_clojure_compact import append_catalog
        expected = append_catalog(expected, root)
    if 'prolog_spectral_audit' in current:
        from qualification.import_prolog_spectral import append_catalog
        expected = append_catalog(expected, root)
    if 'nim_formatted_audit' in current:
        from qualification.nim_formatted_overlay import append_catalog
        expected = append_catalog(expected, root)
    if 'lean4_knucleotide_eligibility' in current:
        from qualification.apply_lean4_knucleotide_eligibility import append_catalog
        expected = append_catalog(expected, root)
    if 'crystal_scan_audit' in current:
        from qualification.import_crystal_scan import append_catalog
        expected = append_catalog(expected, root)
    if 'mech_pidigits_20261022_audit' in current:
        from qualification.import_mech_pidigits import append_catalog as append_mech_pi, reconcile as reconcile_mech_pi
        languages = json.loads((root / 'data/languages.json').read_bytes())
        expected, _ = append_mech_pi(expected, languages, reconcile_mech_pi(root), root)
    assert current == expected, 'Current catalog differs from the validated source-accounting transformation'
    assert report == receipt['transformation'], 'Source-accounting result differs'
    return before
