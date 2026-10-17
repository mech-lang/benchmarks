"""Admit the closed native Lean cohort without changing historical observations."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/lean4'
TARGETS = ('data/benchmarks.json', 'data/languages.json', 'site/src/languages.mjs')
META_FIELDS = ('platform', 'runtime', 'execution', 'typing', 'style', 'memory', 'note', 'sources')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path.read_bytes()))


def inputs():
    results = json.loads((HERE / 'results-v1.json').read_text())
    counts = json.loads((HERE / 'source-counts-v1/qualification-v4/qualified-counts.json').read_text())
    replay = json.loads((HERE / 'source-counts-v1/qualification-v4/independent-replay.json').read_text())
    meta = json.loads((HERE / 'runtime-metadata-v1.json').read_text())
    assert results['status'] == 'THIRTY_FULL_SIZE_SAMPLES_RECONCILED' and results['benchmark_samples'] == 30
    assert results['timing_processes_serial'] and results['all_saved_stream_hashes_recomputed']
    assert counts['status'] == 'QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES' and replay['status'] == 'PASSED'
    assert replay['source_units_sha256_verified'] == 13 and meta['execution'] == ['aot'] and meta['memory'] == ['rc']
    assert len(results['results']) == len(counts['profiles']) == 10
    cases = {}
    for relative, digest in results['reports'].items():
        raw = (ROOT / relative).read_bytes()
        assert sha(raw) == digest
        report = json.loads(raw)
        assert report['status'] == 'PASSED' and report['active'] is None
        for path, expected in report['sources'].items():
            assert sha((ROOT / path).read_bytes()) == expected
        for row in report['cases']:
            assert row['valid'] and row['exit_code'] == 0 and not row['timed_out']
            cases.setdefault(row['benchmark'], []).append(row)
    for bench, row in results['results'].items():
        assert len(row['samples_seconds']) == len(cases[bench]) == 3
        assert row['samples_seconds'] == [c['elapsed_seconds'] for c in cases[bench]]
        assert row['median_seconds'] == statistics.median(row['samples_seconds'])
        assert row['sample_sd_seconds'] == statistics.stdev(row['samples_seconds'])
    for name, unit in counts['units'].items():
        assert sha((HERE / 'source-v1' / name).read_bytes()) == unit['sha256']
    return results, counts, meta, cases


def transform(originals, results, counts, meta, cases):
    data = json.loads(originals[TARGETS[0]])
    before = copy.deepcopy(data)
    languages = json.loads(originals[TARGETS[1]])
    match = re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)', originals[TARGETS[2]].decode(), re.S)
    assert match
    module = json.loads(match[2])
    assert 'lean4' not in {l['key'] for l in data['languages']} and 'lean4' not in module
    refs = {name: binding(HERE / path) for name, path in {
        'results': 'results-v1.json', 'counts': 'source-counts-v1/qualification-v4/qualified-counts.json',
        'count_replay': 'source-counts-v1/qualification-v4/independent-replay.json',
        'work': 'required-work-v1/review.json', 'runtime': 'runtime-metadata-v1.json', 'toolchain': 'toolchain-v1.json',
    }.items()}
    for relative in refs.values():
        data['archive_paths'][relative['path']] = relative['path']
    for relative in results['reports']:
        data['archive_paths'][relative] = relative
    for name, unit in counts['units'].items():
        path = HERE / 'source-v1' / name
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        digest = sha(raw)
        assert digest == unit['sha256']
        file = dict(sha256=digest, name=name, code=raw.decode('utf-8'), archive_path=relative, path=relative)
        if digest in data['files']:
            assert data['files'][digest]['code'] == file['code']
        else:
            data['files'][digest] = file
        data['archive_paths'][relative] = relative
    appended = []
    for bench in data['benchmarks']:
        b = bench['key']
        timing = results['results'][b]
        bundle = counts['profiles'][b]
        assert timing['median_seconds'] >= bench['baseline_seconds'] and bundle['canonical_loc'] >= bench['baseline_loc'], 'New minimum requires separate normalization review'
        identity = f'lean4-{b}-native-v1'
        key = b + ':' + identity
        assert key not in data['programs'] and key not in data['program_inventory']
        roles, files, expansions = {}, [], []
        for name in bundle['files']:
            unit = counts['units'][name]
            digest = unit['sha256']
            relative = f'experiments/lean4/source-v1/{name}'
            files.append(digest)
            roles[digest] = dict(role='application' if name == b + '.lean' else 'application-helper',
                                 source_path=relative, normalized_loc=unit['canonical_loc'], physical_loc=unit['physical_loc'],
                                 canonical_projection=refs['counts'])
            text = (ROOT / relative).read_text().splitlines()
            expansions.append(dict(source=relative, name=name, sha256=digest,
                source_language='Lean' if name.endswith('.lean') else 'C', physical_loc=unit['physical_loc'],
                normalized_loc=unit['canonical_loc'], expansions=[dict(line=e['line'], units=e['extra_units'] + 1,
                    original=text[e['line'] - 1], reason=e['reason']) for e in unit['expansions']]))
        row = dict(key=key, id=identity, receipt_key=identity, benchmark=b, language='lean4', variant='native-v1',
            loc=bundle['canonical_loc'], canonical_loc=bundle['canonical_loc'], physical_loc=bundle['physical_loc'],
            loc_metric='statement-normalized', files=files, file_roles=roles,
            seconds=timing['median_seconds'], samples=timing['samples_seconds'], timing_sd=timing['sample_sd_seconds'],
            native_observations=3, source_alias_of=None, timing_alias_of=None, distinct_optimization_claimed=False,
            command=cases[b][0]['command'], binary_sha256=json.loads((ROOT / next(p for p in results['reports'] if ('fasta' in p) == (b == 'fasta'))).read_text())['binaries'][b],
            execution_mode='aot', sample_execution_metadata=cases[b],
            source_work_qualified=True, canonical_loc_qualified=True, full_workload_qualified=True,
            required_work_validated=True, eligible_for_chart=True, exclusion_reason=None,
            formatted_loc=None, formatted_x=None, formatted_loc_qualified=False, formatted_loc_complete=False,
            formatted_loc_status='unavailable', formatted_loc_evidence=None,
            chart_admission=dict(historical_reports_unchanged=True, **refs),
            report=refs['results']['path'], report_sha256=refs['results']['sha256'],
            loc_report=refs['counts']['path'], source_report=refs['counts']['path'], loc_expansions=expansions,
            runtime_policy=meta['runtime_policy'], memory_policy=meta['memory_policy'], runtime_support=meta['note'],
            runtime_evidence=meta, runtime_evidence_scope=meta['evidence_scope'],
            timing_summary='Median of three complete native process samples, including startup, input, full work/output, flush and shutdown. Builds and comparisons are excluded. Other language results are historical cohorts; no new matched Mech controls were run.',
            source_provenance='Authored Lean application and all authored shared compilation units, including C interoperability leaves, count in canonical LOC. Native Lean parser and Clang token positions retain expansion evidence. Formatted LOC is unavailable.',
            source_provenance_record=dict(canonical_source_evidence=refs['counts'], required_work_evidence=refs['work']),
            source_url=data['repository']['url'] + '/blob/main/experiments/lean4/source-v1/' + b + '.lean',
            source_link_label='Exact retained source', local_adaptation=True,
            x=bundle['canonical_loc'] / bench['baseline_loc'], y=timing['median_seconds'] / bench['baseline_seconds'])
        row['measured_backend'] = dict(key='lean4-native-aot', execution='aot', label=meta['runtime'], verified=True,
            evidence=dict(verified=True, report=refs['runtime']['path'], report_sha256=refs['runtime']['sha256'],
                command=row['command'], source_sha256=files,
                runtime_receipt=dict(verified=True, report=refs['runtime']['path'], report_sha256=refs['runtime']['sha256'],
                    field='/execution/0', value='aot', value_encoding='literal-saved-string')))
        row['publication_record'] = copy.deepcopy(row)
        data['programs'][key] = data['program_inventory'][key] = row
        bench['groups'].append(dict(language='lean4', label=meta['label'], fast=key, small=key,
                                    formatted_fast=None, formatted_small=None, programs=[key]))
        appended.append(key)
    benches = [b['key'] for b in data['benchmarks']]
    language = dict(key='lean4', label=meta['label'], family='lean4', color='#4b83bb',
                    timed_benchmarks=benches, source_benchmarks=benches, formatted_timed_benchmarks=[], formatted_source_benchmarks=[],
                    runtime_family=meta['platform'], runtime=meta['runtime'], execution_modes=['aot'], typing='static', execution='AOT',
                    line_style='solid', runtime_policy=meta['runtime_policy'], paradigms=meta['style'], memory_models=meta['memory'],
                    classification_note=meta['note'], coverage_note='10/10 full workloads, three complete native process samples each.')
    language.update({k:meta[k] for k in ('release_year', 'release_name', 'release_source', 'release_note')})
    data['languages'].append(language)
    module['lean4'] = {k:meta[k] for k in META_FIELDS}
    languages['languages']['lean4'] = dict(meta, displayed_program_count=10, measurement_basis=[refs['results']])
    languages['scope'] = f'{len(data["languages"])} measured variants; all classifications explicit.'
    endpoints = [data['programs'][k] for k in appended]
    aggregate = {axis:statistics.geometric_mean(p[axis] for p in endpoints) for axis in ['x', 'y']}
    data['reference_summary'].append(dict(lang='lean4', label=meta['label'], fast=aggregate, small=aggregate,
                                           measured_benchmarks=benches))
    for group in data['language_groups']:
        if group['key'] in ['aot', 'functional']:
            group['languages'].append('lean4')
    data['protocol']['lean4'] = ('Lean 4.35.0 native arm64, strict floating point, standard reference-counted runtime. '
        'Thirty serial fresh-process observations across ten workloads. All authored Lean/C helper units count; '
        'compiler output and general libraries do not. Existing observations and baselines are preserved; no fresh matched controls.')
    for section in ['programs', 'program_inventory', 'files', 'archive_paths']:
        assert all(data[section][k] == v for k, v in before[section].items()), section
    for old, new in zip(before['benchmarks'], data['benchmarks']):
        assert dict(new, groups=[g for g in new['groups'] if g['language'] != 'lean4']) == old
    for section in ['languages', 'reference_summary', 'formatted_reference_summary']:
        assert data[section][:len(before[section])] == before[section]
    allowed = {'programs','program_inventory','files','archive_paths','benchmarks','languages','reference_summary','language_groups','protocol'}
    assert all(data[k] == v for k, v in before.items() if k not in allowed)
    assert set(module) == set(languages['languages']) == {l['key'] for l in data['languages']}
    encoded = {TARGETS[0]:(json.dumps(data, indent=2, allow_nan=False) + '\n').encode(),
               TARGETS[1]:(json.dumps(languages, indent=2, allow_nan=False) + '\n').encode(),
               TARGETS[2]:(match[1] + json.dumps(module, indent=2, allow_nan=False) + match[3]).encode()}
    receipt = dict(schema='lean-catalog-import.v1', status='PREPARED', evidence=refs,
                   appended_programs=appended, full_samples=30, matched_controls=0,
                   historical_data_preserved=True, baseline_changed=False, benchmark_executions=0,
                   before={p:sha(b) for p, b in originals.items()}, after={p:sha(b) for p, b in encoded.items()})
    return encoded, receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    originals = {p:(ROOT / p).read_bytes() for p in TARGETS}
    prepared, receipt = transform(originals, *inputs())
    backup = HERE / '.build/publication-backup-v1'
    backup.mkdir(exist_ok=False)
    for name, raw in originals.items():
        path = backup / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if args.apply:
        assert all((ROOT / name).read_bytes() == raw for name, raw in originals.items())
        replaced = []
        try:
            for name, raw in prepared.items():
                assert (ROOT / name).read_bytes() == originals[name]
                tmp = ROOT / (name + '.lean-tmp')
                with tmp.open('xb') as stream:
                    stream.write(raw)
                tmp.replace(ROOT / name)
                replaced.append(name)
        except BaseException:
            for name in reversed(replaced):
                if (ROOT / name).read_bytes() == prepared[name]:
                    (ROOT / name).write_bytes(originals[name])
            raise
        receipt['status'] = 'APPLIED'
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
