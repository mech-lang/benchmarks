"""Project retained EKF experiments without running or combining their trials."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import statistics


def ekf_study(root, output=None):
    root = Path(root)
    study = root / 'studies/ekf'
    provenance = json.loads((study / 'provenance.json').read_text())
    entries = {entry['file']: entry for entry in provenance['evidence']}
    sources = {}
    for path, entry in provenance['implementation_sources'].items():
        source = study / entry['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'], path
        name = source.name + '.txt'
        sources[path] = {**entry, 'url': '/benchmarks/ekf-sources/' + name}
        if output:
            target = Path(output) / 'ekf-sources' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    measured = provenance['measured_backend_source']
    source = study / measured['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == measured['sha256']
    measured_url = '/benchmarks/ekf-sources/' + measured['sha256'] + '.mec.txt'
    if output:
        target = Path(output) / measured_url.removeprefix('/benchmarks/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def load(name):
        data = (study / 'evidence' / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entries[name]['sha256'], name
        if output:
            target = Path(output) / 'ekf-evidence' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return json.loads(data)

    def cohort(key, title, name, instances, turns, scope, methods, date):
        return {'id': key, 'title': title, 'machine': 'Apple M1', 'precision': 'f32',
                'instances': instances, 'turns': turns, 'scope': scope, 'methods': methods,
                'recorded_at': date, 'evidence_url': '/benchmarks/ekf-evidence/' + name,
                'original_evidence_url': entries[name]['original_url'], 'rows': []}

    def row(label, mode, rates, source_url, version, expected=None, elapsed_ns=None, total=None, **extra):
        assert rates and all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in rates)
        median = statistics.median(rates)
        if expected is not None:
            assert math.isclose(median, expected, rel_tol=1e-11, abs_tol=1e-10), label
        times = [x * 1e-9 / total for x in elapsed_ns] if elapsed_ns is not None else [1e-6 / x for x in rates]
        assert len(times) == len(rates)
        return {'id': label.lower().replace(' ', '-') + ':' + mode, 'label': label, 'mode': mode,
                'samples_million_filter_turns_per_second': rates, 'median': median,
                'mad': statistics.median(abs(x - median) for x in rates), 'n': len(rates),
                'time_seconds': statistics.median(times), 'samples_seconds_per_filter_turn': times,
                'time_derived_from_reported_throughput': elapsed_ns is None,
                'source_url': source_url, 'version': version, **extra}

    cohorts = []
    name = 'apple-m1-mech-backend-pairs-n10-2026-09-25.json'
    data = load(name)
    assert data['status'] == 'complete' and len(data['records']) == 100
    base = cohort('backends', 'Mech execution backends', name, data['instances'], data['turns'],
                  'Publication after every turn · 5 warmups · compilation, loading, allocation, packing, worker startup and readback excluded.',
                  data['methods'], data['finished_at'])
    labels = {'evaluator': 'Resident numerical evaluator · 1 worker', 'scalar-jit': 'Scalar JIT · 1 worker',
              'simd-aot': 'SIMD AOT · Mech session · 1 worker', 'simd-jit-8w': 'SIMD JIT · 8 workers', 'metal': 'Metal GPU · per turn'}
    categories = {'evaluator': 'cpu-interpreted', 'scalar-jit': 'cpu-jit', 'simd-aot': 'cpu-aot',
                  'simd-jit-8w': 'cpu-jit', 'metal': 'metal'}
    for backend, modes in data['summary'].items():
        for mode, summary in modes.items():
            records = [r for r in data['records'] if r['backend'] == backend and r['mode'] == mode]
            assert len(records) == 10 and all(r['status'] == 'ok' and r['returncode'] == 0 and r['measurement']['faults'] == 0 for r in records)
            rates = [r['measurement']['throughput_million_filter_turns_per_second'] for r in records]
            item = row(labels[backend], mode, rates, measured_url, 'f4b69052 · Cranelift 0.131.3',
                       summary['median_million_filter_turns_per_second'],
                       [r['measurement']['elapsed_ns'] for r in records], data['instances'] * data['turns'],
                       backend=backend, is_mech=True, category=categories[backend], publication='per-turn')
            assert math.isclose(item['mad'], summary['mad_million_filter_turns_per_second'], abs_tol=1e-10)
            base['rows'].append(item)
    cohorts.append(base)

    source_paths = {
        'Rust packed SIMD': 'benchmarks/archive/compute/parallel-ekf/minimal/rust_simd.rs',
        'Julia SIMD.jl': 'benchmarks/archive/compute/parallel-ekf/minimal/julia_simd_threads.jl',
        'NumPy/Numba': 'benchmarks/archive/compute/parallel-ekf/minimal/numpy_numba.py',
        'Futhark ISPC AOT': 'benchmarks/archive/compute/parallel-ekf/minimal/futhark_ekf.fut',
        'Mojo SIMD-4': 'benchmarks/archive/compute/parallel-ekf/mojo_simd.mojo',
        'Halide native CPU': 'benchmarks/iros-2026/halide-metal-matched.cpp',
        'Taichi LLVM CPU': 'benchmarks/iros-2026/taichi-metal-matched.py',
        'Taichi native Metal': 'benchmarks/iros-2026/taichi-metal-matched.py',
        'Rust + hand-written MSL': 'benchmarks/iros-2026/rust-metal/src/ekf.metal',
        'Halide Metal schedule': 'benchmarks/iros-2026/halide-metal-matched.cpp',
        'Julia Metal.jl': 'benchmarks/iros-2026/julia-metal-matched.jl',
        'Mojo native Metal': 'benchmarks/iros-2026/mojo-metal-matched.mojo',
    }
    def version_for(label, data, group):
        versions = data['toolchains']
        if label.startswith('Mech'):
            revision = data['mech_evidence_revisions']['cpu_fused_and_per_turn' if group == 'cpu' else 'direct_metal']
            return revision[:8] + (' · Cranelift 0.131.3' if group == 'cpu' else ' · Metal')
        if label.startswith(('NumPy', 'Taichi')):
            return versions['python_packages']
        for prefix, key in [('Rust', 'rustc'), ('Julia', 'julia'), ('Futhark', 'futhark'), ('Mojo', 'mojo'), ('Halide', 'halide')]:
            if label.startswith(prefix):
                return versions[key].splitlines()[0]
        raise ValueError('Missing implementation version: ' + label)
    for key, title, name in [('cpu', 'CPU implementations', 'apple-m1-cpu-equal-n10-2026-09-24.json'),
                             ('metal', 'Metal implementations', 'apple-m1-metal-equal-n10-2026-09-24.json')]:
        data = load(name)
        scope = ('Eight-worker budget · steady-state execution; the fused Mech/Rust block publishes after 40 turns. Other fault interfaces differ.' if key == 'cpu'
                 else 'Resident GPU state · completed submission and publication every turn; fault-status interfaces differ across implementations.')
        base = cohort(key, title, name, data['configuration']['instances'], data['configuration']['turns'], scope,
                      {**data['configuration'], 'versions': data['toolchains'], 'source_revisions': data['mech_evidence_revisions'],
                       'excluded_work': 'Compilation, device preparation and warmup. These are warm execution measurements, not complete-process timings.'}, data['generated_at'])
        for label, modes in data['campaigns'][key]['rows'].items():
            path = source_paths.get(label)
            url = sources[path]['url'] if path else ('https://github.com/mech-lang/mech/blob/' + data['mech_evidence_revisions']['cpu_fused_and_per_turn' if key == 'cpu' else 'direct_metal'] + '/hosts/gpu/fixtures/ekf-kernel.mec')
            for mode, summary in modes.items():
                rates = [r['throughput_million_ekf_turns_per_second'] for r in summary['records']]
                assert len(rates) == 10
                category = ('metal' if key == 'metal' else
                            'cpu-jit' if label.startswith(('Mech', 'Julia', 'NumPy', 'Taichi', 'Halide')) else 'cpu-aot')
                item = row(label, mode, rates, url, version_for(label, data, key), summary['median_million_ekf_turns_per_second'],
                           is_mech=label.startswith('Mech'), category=category,
                           publication='per-turn' if key == 'metal' or label.startswith(('Mech per-turn', 'Taichi', 'Halide')) else 'fused-block',
                           implementation_url=sources[path]['original_url'] if path else url)
                assert math.isclose(item['mad'], summary['median_absolute_deviation_million_ekf_turns_per_second'], abs_tol=1e-9)
                base['rows'].append(item)
        cohorts.append(base)

    name = 'apple-m1-aot-vs-rust-dylib-2026-09-24.json'
    data = load(name)
    base = cohort('aot-library', 'AOT direct library calls', name, data['configuration']['instances'], data['configuration']['turns'],
                  data['configuration']['timed_region'], {**data['configuration'], 'toolchain': data['toolchain'], 'validation': data['validation'],
                  'reference_scope': 'The retained Rust library is scalar; Mech SIMD AOT uses four lanes. This is the same-loader library experiment, not the eight-worker SIMD language campaign.'}, data['generated_at'])
    for label, summary in data['rows'].items():
        rust = label == 'Rust cdylib'
        rates = summary['throughput_million_ekf_turns_per_second']
        url = 'https://github.com/mech-lang/mech/blob/' + data['implementation_commit'] + '/' + data['sources']['rust_library' if rust else 'mech']
        base['rows'].append(row('Rust scalar' if rust else label, 'checked', rates['samples'], url,
                               data['toolchain']['rustc'] if rust else 'Cranelift ' + data['toolchain']['cranelift'] + ' · ' + data['implementation_commit'][:8],
                               rates['median'], is_mech=not rust, category='cpu-aot', publication='per-turn',
                               summary_path='aot' if label == 'Mech Cranelift SIMD AOT' else None))
    cohorts.append(base)

    name = 'apple-m1-mech-progression-2026-09-01.json'
    data = load(name)
    base = cohort('gpu-batched', 'Batched GPU submission', name, data['configuration']['instances'], data['configuration']['gpu_turns'],
                  'One unchecked GPU submission containing 120 dependent turns. Publication and synchronization occur after the batch.',
                  {**data['configuration'], 'command': data['command'], 'reference_scope': 'No external one-submit batched peer was measured in this campaign. Per-turn GPU timings are not a reference for this boundary.'}, data['generated_at'])
    summary = data['rows']['GPU unchecked one-submit']
    base['rows'].append(row('Mech batched GPU', 'unchecked', summary['throughput_millions'],
                           'https://github.com/mech-lang/mech/blob/cfb51ba74b4eda5e13a77cb357f24767d288d650/hosts/gpu/fixtures/ekf-kernel.mec',
                           'Measured compiler revision not recorded', summary['median_throughput_millions'],
                           is_mech=True, category='metal', publication='fused-block', summary_path='gpu-batched',
                           source_identity_basis='Kernel snapshot at the archive revision; the measured source hash is not recorded.'))
    cohorts.append(base)

    name = 'apple-m3-managed-resident-2026-11-17.json'
    data = load(name)
    record = next(r for r in data['results'] if r['case_id'] == 'ekf' and r['backend'] == 'source' and r['lane'] == 'candidate' and r['outcome'] == 'ok')
    times = [sample['metrics']['resident_turn_seconds'] for sample in record['samples']]
    source = record['source'].encode()
    assert hashlib.sha256(source).hexdigest() == record['source_sha256']
    url = '/benchmarks/ekf-sources/' + record['source_sha256'] + '.mec.txt'
    if output:
        (Path(output) / url.removeprefix('/benchmarks/')).write_bytes(source)
    base = cohort('resident', 'Managed resident runtime', name, 1, 4096,
                  'Captured-input submission, managed f64 execution and publication. No equivalent external rollback/admission/scheduling/accounting/publication control is qualified.',
                  {'revision': record['revision'], 'measurement': record['measurement'], 'reference_scope': 'The saved bare Rust task does not supply equivalent managed runtime semantics.'}, data['started_at'])
    base.update(machine='Apple M3', precision='f64')
    item = row('Mech resident', 'checked', [1e-6 / value for value in times], url, record['revision'],
               is_mech=True, category='resident', publication='per-turn', summary_path='resident')
    item.update(time_seconds=statistics.median(times), samples_seconds_per_filter_turn=times, time_derived_from_reported_throughput=False)
    assert item['time_seconds'] == record['summary']['resident_turn_seconds']['median']
    base['rows'].append(item)
    cohorts.append(base)

    programs = {}
    for original, entry in provenance.get('program_sources', {}).items():
        source = study / entry['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256']
        url = '/benchmarks/ekf-sources/' + source.name + '.txt'
        programs[original] = url
        if output:
            (Path(output) / url.removeprefix('/benchmarks/')).write_bytes(source.read_bytes())
    for experiment in cohorts:
        for item in experiment['rows']:
            if item['source_url'] in programs:
                item['implementation_url'] = item['source_url']
                item['source_url'] = programs[item['source_url']]
            elif item['source_url'] == measured_url:
                item['implementation_url'] = measured['original_url']
    result = {'schema': 'mech.ekf-study.v1', 'article_url': provenance['article_url'], 'studies': cohorts,
              'method': 'Retained, separate experiments. Medians and unscaled MAD are recomputed from every sample. All measured samples are retained; archived warmups remain separate. Samples are not pooled across studies or remeasured.'}
    if output:
        (Path(output) / 'ekf-results.json').write_text(json.dumps(result, separators=(',', ':'), ensure_ascii=False) + '\n')
    return result
