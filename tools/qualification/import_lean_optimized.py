"""Admit reconciled Lean candidates while preserving prior programs and samples."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path.read_bytes()))


def transform(data, metadata, result_path):
    before = copy.deepcopy(data)
    prior_metadata = copy.deepcopy(metadata)
    results = json.loads(result_path.read_text())
    assert results['status'] == 'FULL_SIZE_SAMPLES_AND_NORMALIZED_LOC_RECONCILED'
    assert results['timing_processes_serial'] and results['saved_stream_hashes_recomputed']
    assert results['source_counts_independently_replayed'] and not results['global_optimality_claimed']
    assert results['benchmark_samples'] == 3 * len(results['profiles'])
    assert all(sha((ROOT / path).read_bytes()) == digest for cohort in results['cohorts']
               for path, digest in cohort['hashes'].items())
    result_ref = binding(result_path)
    appended = []
    minima = []
    for candidate in results['profiles']:
        b, variant = candidate['benchmark'], candidate['variant']
        assert variant in ('fast','concise')
        benchmark = next(row for row in data['benchmarks'] if row['key'] == b)
        group = next(row for row in benchmark['groups'] if row['language'] == 'lean4')
        counts_path = ROOT / candidate['counts_report']
        counts = json.loads(counts_path.read_text())
        full = json.loads((ROOT / candidate['full_report']).read_text())
        samples = [row for row in full['cases'] if row['benchmark'] == b]
        assert candidate['samples'] == [row['elapsed_seconds'] for row in samples] and len(samples) == 3
        assert statistics.median(candidate['samples']) == candidate['median_seconds']
        assert statistics.stdev(candidate['samples']) == candidate['sample_sd_seconds']
        assert candidate['normalized_loc'] == counts['profiles'][b]['canonical_loc']
        assert candidate['files'] == counts['profiles'][b]['files']
        refs = {name: binding(ROOT / path) for name, path in {
            'results': str(result_path), 'counts': candidate['counts_report'], 'work': candidate['work_report'],
            'full': candidate['full_report'], 'build': candidate['build_report']}.items()}
        for ref in refs.values():
            data['archive_paths'][ref['path']] = ref['path']
        source = Path(candidate['source_directory'])
        files, roles, expansions = [], {}, []
        for name in candidate['files']:
            unit = counts['units'][name]
            path = source / name
            raw = path.read_bytes()
            digest = sha(raw)
            assert digest == unit['sha256']
            relative = path.relative_to(ROOT).as_posix()
            files.append(digest)
            if digest not in data['files']:
                data['files'][digest] = dict(sha256=digest, name=name, code=raw.decode(), archive_path=relative, path=relative)
            else:
                assert data['files'][digest]['code'].encode() == raw
            data['archive_paths'][relative] = relative
            roles[digest] = dict(role='application' if name == b + '.lean' else 'application-helper',
                source_path=relative, normalized_loc=unit['canonical_loc'], physical_loc=unit['physical_loc'],
                canonical_projection=refs['counts'])
            lines = raw.decode().splitlines()
            expansions.append(dict(source=relative, name=name, sha256=digest,
                source_language='Lean' if name.endswith('.lean') else 'C', physical_loc=unit['physical_loc'],
                normalized_loc=unit['canonical_loc'], expansions=[dict(line=e['line'], units=e['extra_units'] + 1,
                    original=lines[e['line'] - 1], reason=e['reason']) for e in unit['expansions']]))
        label = 'optimized' if variant == 'fast' else 'compact'
        identity = f'lean4-{b}-{label}-v1'
        key = b + ':' + identity
        assert key not in data['programs'] and key not in data['program_inventory']
        original = data['program_inventory'][b + ':lean4-' + b + '-native-v1']
        row = copy.deepcopy(original)
        row.pop('publication_record')
        row.update(key=key, id=identity, receipt_key=identity, variant=label + '-v1',
            loc=candidate['normalized_loc'], canonical_loc=candidate['normalized_loc'], physical_loc=candidate['physical_loc'],
            files=files, file_roles=roles, seconds=candidate['median_seconds'], samples=candidate['samples'],
            timing_sd=candidate['sample_sd_seconds'], binary_sha256=candidate['binary_sha256'],
            command=samples[0]['command'], sample_execution_metadata=samples, native_observations=3,
            source_alias_of=None, timing_alias_of=None, distinct_optimization_claimed=b in ['nbody','mandelbrot','spectralnorm','fannkuchredux'],
            chart_admission=dict(historical_reports_unchanged=True, **refs),
            report=result_ref['path'], report_sha256=result_ref['sha256'],
            source_report=refs['counts']['path'], loc_report=refs['counts']['path'], loc_expansions=expansions,
            source_provenance_record=dict(canonical_source_evidence=refs['counts'], required_work_evidence=refs['work']),
            source_url=data['repository']['url'] + '/blob/main/' + (source / (b + '.lean')).relative_to(ROOT).as_posix(),
            source_provenance='Locally authored Lean candidate. Normalized LOC includes every authored Lean/C compilation input; native lexical ownership and independent statement expansion are replayed. General libraries and generated compiler output are excluded. No global optimality claim.',
            timing_summary='Three complete fresh native processes including startup, input, full work/output, flush and shutdown. Builds and validation are outside timing. Historical candidates remain available; no fresh matched Mech controls were run.',
            x=candidate['normalized_loc'] / benchmark['baseline_loc'],
            y=candidate['median_seconds'] / benchmark['baseline_seconds'])
        backend = row['measured_backend']
        backend['evidence']['command'] = row['command']
        backend['evidence']['source_sha256'] = files
        backend['evidence']['candidate_build'] = refs['build']
        row['publication_record'] = copy.deepcopy(row)
        data['programs'][key] = data['program_inventory'][key] = row
        group['programs'].append(key)
        appended.append(key)
        if row['x'] < 1 or row['y'] < 1:
            minima.append(dict(program=key, x=row['x'], y=row['y'],
                review='Qualified full workload and normalized bundle. Historical normalization is preserved; sub-baseline coordinates are displayed without rebasing earlier observations.'))
    endpoints = []
    for benchmark in data['benchmarks']:
        group = next(row for row in benchmark['groups'] if row['language'] == 'lean4')
        candidates = [data['programs'][key] for key in group['programs']]
        group['fast'] = min(candidates, key=lambda row:(row['seconds'],row['loc'],row['key']))['key']
        group['small'] = min(candidates, key=lambda row:(row['loc'],row['seconds'],row['key']))['key']
        endpoints.append(dict(benchmark=benchmark['key'],fast=group['fast'],small=group['small']))
    summary = next(row for row in data['reference_summary'] if row['lang'] == 'lean4')
    for kind in ('fast','small'):
        selected = [data['programs'][row[kind]] for row in endpoints]
        summary[kind] = {axis:statistics.geometric_mean(row[axis] for row in selected) for axis in ('x','y')}
    total = len([p for p in data['program_inventory'].values() if p['language'] == 'lean4'])
    next(l for l in data['languages'] if l['key'] == 'lean4')['coverage_note'] = f'10/10 full workloads; {total} measured candidates with three whole-process samples each.'
    metadata['languages']['lean4']['displayed_program_count'] = total
    metadata['languages']['lean4']['measurement_basis'].append(result_ref)
    data['protocol']['lean4'] = (f'Lean 4.35.0 native arm64 with strict floating point and the standard reference-counted runtime. '
        f'{total} candidate programs, three complete fresh-process samples each. Fastest and fewest normalized LOC select measured endpoints across the retained pool. '
        'All authored Lean/C helper inputs count; generated compiler output and general libraries do not. Original programs, observations and fixed baselines are preserved. No fresh matched Mech controls or global optimality claim.')
    for section in ('programs','program_inventory','files','archive_paths'):
        assert all(data[section][key] == value for key, value in before[section].items()), section
    for old, new in zip(before['benchmarks'], data['benchmarks']):
        assert {k:v for k,v in old.items() if k!='groups'} == {k:v for k,v in new.items() if k!='groups'}
        assert [g for g in old['groups'] if g['language']!='lean4'] == [g for g in new['groups'] if g['language']!='lean4']
    assert [l for l in before['languages'] if l['key']!='lean4'] == [l for l in data['languages'] if l['key']!='lean4']
    assert [l for l in before['reference_summary'] if l['lang']!='lean4'] == [l for l in data['reference_summary'] if l['lang']!='lean4']
    assert all(metadata['languages'][key] == value for key, value in prior_metadata['languages'].items() if key!='lean4')
    return data, metadata, dict(schema='lean-optimized-catalog-admission.v1', status='PREPARED',
        result_evidence=result_ref, appended_programs=appended, endpoints=endpoints, new_minimum_review=minima,
        baseline_changed=False, historical_programs_and_samples_unchanged=True, benchmark_executions=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    assert not args.output.exists()
    targets = ('data/benchmarks.json','data/languages.json')
    originals = {name:(ROOT / name).read_bytes() for name in targets}
    data, metadata, receipt = transform(*(json.loads(originals[name]) for name in targets),args.results.resolve())
    encoded = {name:(json.dumps(value,indent=2,allow_nan=False)+'\n').encode() for name,value in zip(targets,(data,metadata))}
    receipt.update(before={k:sha(v) for k,v in originals.items()},after={k:sha(v) for k,v in encoded.items()})
    args.output.mkdir(parents=True)
    for name, raw in originals.items():
        backup = ROOT / ('experiments/lean4/.build/optimization-v1/catalog-backup-' + args.output.name) / name
        backup.parent.mkdir(parents=True,exist_ok=True)
        with backup.open('xb') as stream:
            stream.write(raw)
    if args.apply:
        assert all((ROOT / name).read_bytes() == value for name,value in originals.items())
        replaced = []
        try:
            for name,raw in encoded.items():
                assert (ROOT / name).read_bytes() == originals[name]
                tmp = ROOT / (name+'.lean-optimized-tmp')
                with tmp.open('xb') as stream:
                    stream.write(raw)
                tmp.replace(ROOT / name)
                replaced.append(name)
        except BaseException:
            for name in reversed(replaced):
                if (ROOT / name).read_bytes() == encoded[name]:
                    (ROOT / name).write_bytes(originals[name])
            raise
        receipt['status'] = 'APPLIED'
    (args.output / 'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(receipt['status'],len(receipt['appended_programs']),'profiles',flush=True)


if __name__ == '__main__':
    main()
