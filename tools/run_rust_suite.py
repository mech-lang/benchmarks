#!/usr/bin/env python3
"""Paired Mech/Rust task measurements, with independent correctness and raw evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import sys
import time

from benchmark_suite import (ROOT, SCHEMA, archive_evidence, campaign_lock, digest, environment,
    equal, execute, file_digest, invoke, load_catalog, measurement_response, preserve_worker,
    save, seal_evidence, summarize, validate_campaign, verify_response, worker_provenance)
from run_concurrent import group as mech_group

TOOLCHAIN = 'nightly-2026-03-03'
NOTE = ('Same inputs, accepted turns, warmup and output/retention obligations, paired on the same machine. '
        'Rust is an independent AOT task implementation with typed input validation, change detection and owned publication. '
        'Rust uses native ownership; it is not qualified for equivalent transactional rollback, runtime admission, dependency scheduling, budget accounting and turn publication. '
        'These resident measurements are not semantically equivalent cross-runtime performance comparisons. No Mech/Rust ratio or win/loss is assigned. '
        'Compilation is outside the resident timer. Rust preparation is not presented as a Mech artifact or JIT metric.')


def task_report(campaign, group, introduction):
    resident = group in ('resident', 'concurrent')
    if resident:
        lines = ['# Mech resident measurements', '', introduction, '',
                 'Rust task controls are retained as separate correctness evidence; their runtime semantics are not equivalent.', '',
                 '| Task / Mech path | Measurement | Mech seconds |', '| --- | --- | ---: |']
    else:
        lines = ['# Paired Rust task controls', '', introduction, '',
                 '| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |', '| --- | ---: | ---: | ---: |']
    for record in campaign['results']:
        if record['lane'] == 'control':
            continue
        metric = record['measurement'].get('primary_metric', 'resident_turn_seconds')
        measured = record['summary'][metric]['median']
        if resident:
            lines.append(f'| {record["case_id"]} / {record["backend"]} | {metric} | {measured:.9g} |')
            continue
        control = next(r for r in campaign['results'] if r['case_id'] == record['case_id'] and r['lane'] == 'control')
        mapped = control['measurement'].get('metric_mapping', {}).get(metric, metric)
        reference = control['summary'][mapped]['median']
        lines.append(f'| {record["case_id"]} / {record["backend"]} | {measured:.9g} | {reference:.9g} | {measured/reference:.3f} |')
    return '\n'.join(lines) + '\n'


def rust_response(response, expected, case, count, verify=False):
    if response.get('outcome') != 'ok':
        raise ValueError('Rust worker failed: ' + str(response.get('error')))
    if response.get('iterations') != count or response.get('output_name') != case['task']['outputs'][0]:
        raise ValueError('Rust iteration count or named output differs')
    if not equal(response.get('final_output'), expected[-1], case['task']):
        raise ValueError('Rust endpoint differs from independent oracle')
    if case['task'].get('oracle') in ('strings', 'graphemes') and type(response['final_output'].get('value')) is not int:
        raise ValueError('Rust string selector must publish an unsigned integer result')
    if verify:
        if not equal(response.get('outputs'), expected, case['task']):
            raise ValueError('Rust trajectory differs from independent oracle')
        if not equal(response.get('before_execution'), expected[:-1], case['task']):
            raise ValueError('Rust changed publication without execution')
        if case['measurement']['retain_snapshots'] and not equal(response.get('retained_outputs'), expected, case['task']):
            raise ValueError('Rust retained snapshots changed')
    if response.get('owned_outputs_released') is not True:
        raise ValueError('Rust owned output remained live after teardown')
    metrics = response.get('metrics', {})
    if not metrics or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in metrics.values()):
        raise ValueError('Rust numeric metrics invalid')
    if metrics.get('resident_turn_seconds', 0) <= 0 or metrics.get('execution_block_seconds', 0) <= 0:
        raise ValueError('Rust duration missing or nonpositive')
    if not math.isclose(metrics['resident_turn_seconds'] * count, metrics['execution_block_seconds'], rel_tol=1e-12):
        raise ValueError('Rust per-turn duration differs from its complete timed block')


def checked(command, directory, timeout, **kwargs):
    result = execute([str(x) for x in command], directory, timeout, **kwargs)
    if result['outcome'] != 'ok':
        raise ValueError(f'command failed: {directory}; raw output retained')
    return result


def build_rust(directory, timeout):
    source = directory / 'rust-source'
    shutil.copytree(ROOT / 'suite/controls/rust', source)
    target = ROOT / '.local/rust-controls-target'
    env = dict(os.environ, RUSTFLAGS='-Ctarget-cpu=native')
    command = ['cargo', '+' + TOOLCHAIN, 'build', '--release', '--offline', '--locked',
               '--manifest-path', str(source / 'Cargo.toml'), '--target-dir', str(target)]
    checked(command, directory / 'raw/build-rust', timeout, env=env)
    checked(['rustc', '+' + TOOLCHAIN, '-Vv'], directory / 'raw/rust-version', timeout)
    binaries = {name: {'binary': str(target / 'release' / name), 'binary_sha256': file_digest(target / 'release' / name)} for name in ('resident', 'deflate')}
    return {'toolchain': TOOLCHAIN, 'version': (directory / 'raw/rust-version/stdout.txt').read_text(),
            'build_command': command, 'build_environment': {'RUSTFLAGS': env['RUSTFLAGS']},
            'source_sha256': {p.name: file_digest(p) for p in source.iterdir() if p.is_file()}, 'binaries': binaries}


def make_record(campaign, case, backend, measurement, source, revision, contract, **extra):
    record = {'case_id': case['id'], 'title': 'Rust · task control' if backend == 'rust' else case['title'],
              'family': case['family'], 'backend': backend, 'lane': 'control' if backend == 'rust' else 'candidate',
              'revision': revision, 'task': case['task'], 'task_hash': digest(case['task']),
              'measurement': measurement, 'measurement_hash': digest(measurement), 'source': source,
              'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'environment_hash': campaign['environment_hash'],
              'feature_profile': {'profile': 'rust-aot' if backend == 'rust' else campaign['workers']['candidate']['feature_profile']},
              'control_contract': digest(contract), 'progress': 'implemented', 'outcome': 'pending', 'capability': 'unknown', 'samples': [], **extra}
    campaign['results'].append(record)
    return record


def accept(campaign, directory, record, response, raw, fork, reason):
    relative = raw.relative_to(directory).as_posix()
    if fork is None:
        record.update(outcome='ok', capability='supported', progress='verified', verification={
            'outcome': 'ok', 'raw': relative, 'reason': reason, 'outputs': response.get('outputs', [response.get('final_output')]),
            'before_execution': response.get('before_execution'), 'retained_outputs': response.get('retained_outputs')})
        # Complete trajectories already live in pinned raw stdout/supervision.
        # Keep the campaign index small so progress persistence does not repeatedly
        # serialize every verified matrix and retained snapshot between forks.
        for field in ('outputs', 'before_execution', 'retained_outputs'):
            values = record['verification'].get(field)
            if isinstance(values, list) and len(values) > 6:
                record['verification'][field + '_count' if field != 'outputs' else 'output_count'] = len(values)
                record['verification']['preview_' + field] = values[:3] + values[-3:]
                del record['verification'][field]
    else:
        record['samples'].append({'fork': fork, 'raw': relative, 'metrics': response['metrics'], 'final_output': response.get('final_output', response.get('outputs'))})
        campaign['order'].append({'case_id': record['case_id'], 'backend': record['backend'], 'fork': fork, 'lane': record['lane']})
    save(directory / 'campaign.json', campaign)


def resident(args, campaign, directory, worker, rust, rng):
    cases = [c for c in load_catalog()['cases'] if set(c['backends']) & {'source', 'bytecode', 'jit'}]
    if args.case:
        if set(args.case) - {c['id'] for c in cases}: raise ValueError('unknown resident case selection')
        cases = [c for c in cases if c['id'] in args.case]
    for case in cases:
        source = (ROOT / case['source']).read_text()
        measurement = {**case['measurement'], 'warmup': case['measurement'].get('warmup', 32),
                       'cycles': case['measurement'].get('cycles', args.cycles), 'output': case['task']['outputs'][0],
                       'memory_budget_bytes': 1 << 34, 'summary': 'included in Mech turn',
                       'comparison_note': NOTE, 'timing_loop': 'typed schedule parsed before timer; accepted turns and retained snapshot publication inside timer'}
        count = len(measurement['schedule']) * measurement['cycles']
        contract = {'task': case['task'], 'schedule': measurement['schedule'], 'iterations': count,
                    'warmup': measurement['warmup'], 'retain_snapshots': measurement['retain_snapshots'],
                    'abort_before_accept': measurement['abort_before_accept'], 'reject_before_accept': measurement.get('reject_before_accept', False),
                    'boundary': 'Resident accepted input through published owned result; retained snapshots inside; preparation and teardown outside', 'note': NOTE}
        save(directory / 'fixtures' / (case['id'] + '.json'), case)
        expected_response = invoke([sys.executable, str(ROOT / 'tools/suite_oracle.py')], {'case': case, 'count': count}, directory / 'raw' / case['id'] / 'oracle', args.timeout)
        if expected_response.get('outcome') != 'ok' or len(expected_response.get('outputs', [])) != count:
            raise ValueError('independent oracle failed: ' + case['id'])
        expected = expected_response['outputs']
        records = {backend: make_record(campaign, case, backend, measurement, source, worker['revision'], contract) for backend in case['backends']}
        rust_measurement = {**measurement, 'metric_mapping': {'jit_invocation_seconds': 'rust_call_seconds'}}
        records['rust'] = make_record(campaign, case, 'rust', rust_measurement, (directory / 'rust-source/resident.rs').read_text(), rust['source_sha256']['resident.rs'], contract, implementation=rust)
        for fork in [None, *range(args.forks)]:
            order = list(records)
            rng.shuffle(order)
            for backend in order:
                print(f'{case["id"]} / {backend} / {"verify" if fork is None else "fork " + str(fork+1)}', flush=True)
                request = {'protocol': 1, 'action': 'verify' if fork is None else 'measure', 'source': source, 'backend': backend,
                           **measurement, 'iterations': count, 'oracle': case['task']['oracle']}
                binary = rust['binaries']['resident'] if backend == 'rust' else worker
                if file_digest(binary['binary']) != binary['binary_sha256']:
                    raise ValueError('measured binary changed')
                raw = directory / 'raw' / case['id'] / backend / ('verify' if fork is None else f'fork-{fork+1}')
                response = invoke([binary['binary']], request, raw, args.timeout)
                if backend == 'rust':
                    rust_response(response, expected, case, count, fork is None)
                else:
                    status, reason = verify_response(response, expected, case) if fork is None else measurement_response(response, expected[-1], case, count)
                    if status != 'ok':
                        raise ValueError(f'{case["id"]}/{backend}: {reason}')
                accept(campaign, directory, records[backend], response, raw, fork,
                       'Every turn matches the independent Python trajectory; publication before execution, abort/reject recovery, held snapshots where requested and complete ownership teardown checked.')


def concurrent(args, campaign, directory, worker, rust, rng):
    from suite_oracle import outputs
    for case in [c for c in load_catalog()['cases'] if c['family'] == 'concurrency']:
        measurement = {**case['measurement'], 'comparison_note': NOTE + ' Complete supervised group startup through exit, fixed total work; one execution thread per process.'}
        contract = {'task': case['task'], 'measurement': measurement}
        source = (ROOT / case['source']).read_text()
        records = {'process-workers': make_record(campaign, case, 'process-workers', measurement, source, worker['revision'], contract),
                   'rust': make_record(campaign, case, 'rust', measurement, (directory / 'rust-source/resident.rs').read_text(), rust['source_sha256']['resident.rs'], contract, implementation=rust)}
        for fork in [None, *range(args.forks)]:
            order = list(records); rng.shuffle(order)
            for backend in order:
                print(f'{case["id"]} / {backend} / {fork}', flush=True)
                raw = directory / 'raw' / case['id'] / backend / ('verify' if fork is None else f'fork-{fork+1}')
                if backend != 'rust':
                    response = mech_group(worker, case, raw, fork is None, args.timeout)
                else:
                    workers = measurement['workers']; schedule = measurement['schedule']
                    count = len(schedule) * 2 if fork is None else measurement['total_turns'] // workers
                    expected = outputs(case, count)
                    request = {'protocol': 1, 'action': 'verify' if fork is None else 'measure', 'oracle': 'pipeline', 'output': 'result',
                               'schedule': schedule, 'warmup': measurement['warmup'], 'iterations': count}
                    started = time.perf_counter()
                    with ThreadPoolExecutor(max_workers=workers) as pool:
                        futures = [pool.submit(invoke, [rust['binaries']['resident']['binary']], request, raw / f'worker-{i}', args.timeout) for i in range(workers)]
                        responses = [f.result() for f in futures]
                    seconds = time.perf_counter() - started
                    for r in responses: rust_response(r, expected, case, count, fork is None)
                    response = {'outcome': 'ok', 'outputs': [r['final_output'] for r in responses], 'metrics': {
                        'worker_group_process_seconds': seconds, 'accepted_turns_per_second': count * workers / seconds, 'total_turns': count * workers,
                        'sum_worker_execution_block_seconds': sum(r['metrics']['execution_block_seconds'] for r in responses),
                        'execution_allocations': sum(r['metrics']['execution_allocations'] for r in responses)},
                        'worker_observations': [{'path': f'worker-{i}/supervised.json', 'sha256': file_digest(raw / f'worker-{i}/supervised.json')} for i in range(workers)]}
                    save(raw / 'supervised.json', response)
                accept(campaign, directory, records[backend], response, raw, fork, 'All independent processes checked; complete group lifecycle and exact fixed accepted-turn count retained.')


def native(args, campaign, directory, worker, rust, rng):
    from run_native import build_and_run, sections, text_size
    from suite_oracle import outputs
    if not worker.get('native_generation'): raise ValueError('native-capable Mech worker required')
    case = next(c for c in load_catalog()['cases'] if c['id'] == 'native-build')
    source = (ROOT / case['source']).read_text()
    rust_source = ('fn main(){let a=std::env::args().nth(1).unwrap();let bits=u64::from_str_radix(a.strip_prefix("f64:").unwrap(),16).unwrap();'
                   'let mut x=f64::from_bits(bits);assert!(x.is_finite());' + 'x=x*1.0001+0.01;' * 128 + 'println!("f64:{:016x}",x.to_bits());}\n')
    (directory / 'rust-source/scalar.rs').write_text(rust_source)
    note = ('Source to linked executable, with a fresh source/project per fork and warmed support dependencies. '
            'Mech includes its compiler worker, dependency resolution, checked runtime support build and link; Rust includes rustc and final link with prebuilt standard library. '
            'Both produce a complete scalar CLI checked against all scheduled inputs. This compares deployment paths, including their different support machinery.')
    measurement = {**case['measurement'], 'primary_metric': 'source_to_executable_seconds', 'comparison_note': note, 'cache': 'Untimed qualification warms support dependencies; fresh project per measured build', 'stripping_policy': 'strip=symbols'}
    contract = {'task': case['task'], 'schedule': measurement['schedule'], 'boundary': 'Source to complete linked scalar application; support dependencies warmed by qualification', 'note': note}
    records = {'native': make_record(campaign, case, 'native', measurement, source, worker['revision'], contract),
               'rust': make_record(campaign, case, 'rust', measurement, rust_source, hashlib.sha256(rust_source.encode()).hexdigest(), contract, implementation=rust)}
    records['rust']['implementation'] = {'toolchain': TOOLCHAIN, 'rustc': rust['version'], 'adapter_sha256': records['rust']['source_sha256'],
                                         'build_policy': 'rustc -Copt-level=3 -Ctarget-cpu=native -Ccodegen-units=1 -Cstrip=symbols --emit=obj,link', 'builds': []}
    target = ROOT / '.local/native-target' / worker['revision']
    expected = outputs(case, len(measurement['schedule']))
    for fork in [None, *range(args.forks)]:
        order = list(records); rng.shuffle(order)
        for backend in order:
            print(f'native build / {backend} / {fork}', flush=True)
            raw = directory / 'raw/native-build' / backend / ('verify' if fork is None else f'fork-{fork+1}')
            if backend == 'native':
                response = build_and_run(worker, case, raw, target, args.timeout)
            else:
                import struct
                raw.mkdir(parents=True); project = raw / 'project'; project.mkdir()
                path = project / 'scalar.rs'; path.write_text(rust_source)
                command = ['rustc', '+' + TOOLCHAIN, str(path), '--crate-name', 'scalar_control', '--emit=obj,link', '--out-dir', str(project),
                           '-C', 'opt-level=3', '-C', 'target-cpu=native', '-C', 'codegen-units=1', '-C', 'strip=symbols']
                built = checked(command, raw / 'build', args.timeout)
                binary = project / 'scalar_control'; obj = project / 'scalar_control.o'
                process_times = []; observed = []
                for i, frame in enumerate(measurement['schedule']):
                    command = [str(binary), 'f64:' + struct.pack('>d', frame[0]).hex()]
                    result = checked(command, raw / f'program-{i+1}', args.timeout)
                    lines = (raw / f'program-{i+1}/stdout.txt').read_text().splitlines()
                    if len(lines) != 1 or not lines[0].startswith('f64:') or len(lines[0]) != 20: raise ValueError('invalid Rust CLI output')
                    value = {'kind': 'scalar', 'value': struct.unpack('>d', bytes.fromhex(lines[0][4:]))[0]}
                    if not equal(value, expected[i], case['task']): raise ValueError('Rust native CLI differs from independent oracle')
                    observed.append(value); process_times.append(result['seconds'])
                object_sections = sections(obj, raw / 'object-sections', args.timeout); linked_sections = sections(binary, raw / 'linked-sections', args.timeout)
                metrics = {'source_to_executable_seconds': built['seconds'], 'native_process_seconds': sum(process_times) / len(process_times),
                           'object_bytes': obj.stat().st_size, 'executable_bytes': binary.stat().st_size}
                for key, value in [('object_text_bytes', text_size(object_sections)), ('linked_text_bytes', text_size(linked_sections))]:
                    if value is not None: metrics[key] = value
                response = {'outcome': 'ok', 'metrics': metrics, 'outputs': observed, 'process_samples': process_times,
                            'object_sha256': file_digest(obj), 'executable_sha256': file_digest(binary), 'object_sections': object_sections, 'linked_sections': linked_sections}
            if response.get('outcome') != 'ok': raise ValueError('native build failed: ' + str(response.get('reason')))
            save(raw / 'supervised.json', response)
            if backend == 'rust': records['rust']['implementation']['builds'].append({'fork': fork, 'object_sha256': response['object_sha256'], 'binary_sha256': response['executable_sha256'], 'raw': raw.relative_to(directory).as_posix()})
            accept(campaign, directory, records[backend], response, raw, fork, 'Fresh complete source-to-executable build, object/linked footprint and every scheduled native process output checked.')


def applications(args, campaign, directory, worker, rust, rng):
    from application_tasks import FASTA_N, deflate_cases, validate_deflate
    if not args.application_worker or not args.fasta or not args.corpus: raise ValueError('application worker, complete FASTA and Reymont corpus required')
    apps = worker_provenance(args.application_worker)
    if apps['revision'] != worker['revision']: raise ValueError('application workers pin different Mech revisions')
    campaign['workers']['applications'] = apps; preserve_worker(apps, directory / 'workers/applications')
    catalog = load_catalog()['cases']
    case = next(c for c in catalog if c['id'] == 'knucleotide')
    # Rebuild the fastest retained upstream Rust example, unchanged, with its pinned dependencies.
    project = directory / 'knucleotide-rust'; project.mkdir()
    dependencies = ROOT / 'archive/workloads/knucleotide/rust-deps'
    for name in ('Cargo.toml', 'Cargo.lock'): shutil.copyfile(dependencies / name, project / name)
    with (project / 'Cargo.toml').open('a') as f: f.write('\n[[bin]]\nname="knucleotide-control"\npath="main.rs"\n\n[profile.release]\nopt-level=3\ncodegen-units=1\n')
    parent = ROOT / 'programs/rust/knucleotide/knucleotide-rust-7'
    shutil.copyfile(parent / 'knucleotide-rust-7.rs', project / 'main.rs'); shutil.copyfile(parent / 'program.json', project / 'program.json')
    target = ROOT / '.local/knucleotide-rust-target'; env = dict(os.environ, RUSTFLAGS='-Ctarget-cpu=native')
    command = ['cargo', '+' + TOOLCHAIN, 'build', '--release', '--offline', '--locked', '--manifest-path', str(project / 'Cargo.toml'), '--target-dir', str(target)]
    checked(command, directory / 'raw/knucleotide-build', args.timeout, env=env)
    binary = target / 'release/knucleotide-control'
    implementation = {'source_sha256': file_digest(project / 'main.rs'), 'manifest_sha256': file_digest(project / 'Cargo.toml'),
                      'lock_sha256': file_digest(project / 'Cargo.lock'), 'binary_sha256': file_digest(binary), 'command': command,
                      'build_environment': {'RUSTFLAGS': env['RUSTFLAGS']}, 'rustc': rust['version'], 'authorship': json.loads((project / 'program.json').read_text())['authorship']}
    expected = (ROOT / 'suite/applications/knucleotide-25000000.expected').read_bytes()
    if args.fasta.stat().st_size != 254166745: raise ValueError('full FASTA N=25,000,000 required')
    oracle = directory / 'raw/knucleotide-oracle'
    (directory / 'oracles').mkdir()
    shutil.copyfile(ROOT / 'suite/controls/knucleotide_oracle.c', directory / 'oracles/knucleotide.c')
    (directory / 'oracles/knucleotide.expected.txt').write_bytes(expected)
    checked(['clang', '-O3', directory / 'oracles/knucleotide.c', '-o', directory / 'knucleotide-oracle'], oracle / 'build', args.timeout)
    checked([directory / 'knucleotide-oracle'], oracle / 'run', args.timeout, stdin_path=args.fasta)
    if (oracle / 'run/stdout.txt').read_bytes() != expected: raise ValueError('FASTA failed independent full-input count oracle')
    (directory / 'knucleotide-oracle').unlink()
    campaign['fasta'] = {'n': FASTA_N, 'bytes': args.fasta.stat().st_size, 'sha256': file_digest(args.fasta)}
    note = ('Complete FASTA N=25,000,000 (254,166,745 bytes), exact complete frequency/query output, fresh process launch through exit. '
            'Compiling executables excluded; Mech source preparation/JIT during startup included. '
            'Mech uses four partitions; unchanged retained Rust #7 uses its upstream Tokio thread-pool policy. This is a tuned task comparison, not identical threading or algorithms.')
    measurement = {**case['measurement'], 'comparison_note': note}
    contract = {'task': case['task'], 'input_sha256': campaign['fasta']['sha256'], 'boundary': 'Fresh whole process through complete output and exit', 'note': note}
    records = {'source-native': make_record(campaign, case, 'source-native', {**measurement, 'threads': 4}, (ROOT / case['source']).read_text(), worker['revision'], contract),
               'rust': make_record(campaign, case, 'rust', measurement, (project / 'main.rs').read_text(), implementation['source_sha256'], contract, implementation=implementation)}
    records['rust']['title'] = 'Rust · upstream #7'
    mech_app = apps['applications']['mech-application']; mech_env = dict(os.environ, MECH_SEQUENCE_PARTITIONS='4', MECH_SEQUENCE_STD_MAP='1', MECH_SEQUENCE_NARROW='1', MECH_SEQUENCE_ASYNC='0')
    for fork in [None, *range(args.forks)]:
        order = list(records); rng.shuffle(order)
        for backend in order:
            print(f'Full K-nucleotide / {backend} / {fork}', flush=True)
            raw = directory / 'raw/knucleotide' / backend / ('verify' if fork is None else f'fork-{fork+1}')
            if backend == 'rust':
                if file_digest(binary) != implementation['binary_sha256']: raise ValueError('Rust K-nucleotide binary changed')
                command = [binary]; run_env = None
            else:
                if file_digest(mech_app['binary']) != mech_app['binary_sha256']: raise ValueError('Mech application changed')
                command = [mech_app['binary'], ROOT / case['source'], 'jit']; run_env = mech_env
            response = checked(command, raw, args.timeout, stdin_path=args.fasta, env=run_env)
            actual = (raw / 'stdout.txt').read_bytes()
            if actual != expected: raise ValueError('K-nucleotide complete output differs from independent full oracle')
            receipt = {**response, 'final_output': {'kind': 'text', 'value': actual.decode()}, 'metrics': {'native_process_seconds': response['seconds']}}
            save(raw / 'supervised.json', receipt)
            accept(campaign, directory, records[backend], receipt, raw, fork, 'Entire FASTA read; independent full-input counting oracle and all exact output bytes checked.')
    # Mech level 12 and Rust zlib-rs maximum level 9 are distinct codecs. Keep compressed size beside time.
    note = ('Same full input/prefix, one untimed warmup and one fresh owned compressor/output per call; input import, compilation, warmup and returned-output destruction excluded. '
            'Input/prefix aliases survive and the complete stream independently inflates without trailing bytes. '
            'Mech level 12 must match the pinned Roc stream; Rust uses zlib-rs 0.6.8 maximum level 9 and may produce different valid bytes. '
            'Compression quality is not identical: compare output_bytes as well as time; the ratio alone is not an equal-quality speed claim. '
            'Rust includes output allocation and scratch destruction; Mech additionally includes checked invocation, resource accounting and publication.')
    controls_path = ROOT / '.local/controls/qualified-001/controls.json'
    controls = json.loads(controls_path.read_text()); roc = controls['roc']
    if file_digest(roc['binary']) != roc['binary_sha256']: raise ValueError('pinned Roc reference changed')
    save(directory / 'roc-reference.json', controls)
    fixtures = []; compression_records = {}
    for fixture in deflate_cases(args.corpus):
        path = directory / 'raw/deflate-inputs' / fixture['name']; path.mkdir(parents=True)
        for name in ('input', 'prefix'): (path / name).write_bytes(fixture[name])
        expected_stream = fixture['expected']
        if expected_stream is None:
            capacity = len(fixture['prefix']) + len(fixture['input']) + 5 * max(1, (len(fixture['input']) + 4999) // 5000)
            checked([roc['binary'], path / 'input', path / 'prefix', str(capacity)], path / 'reference', args.timeout)
            expected_stream = (path / 'reference/stdout.txt').read_bytes()
            validate_deflate(expected_stream, fixture['input'], fixture['prefix'])
        (path / 'expected').write_bytes(expected_stream)
        fixtures.append({'name': fixture['name'], **{name: str(path / name) for name in ('input', 'prefix', 'expected')}})
        id_ = 'deflate' if fixture['name'] == 'full-reymont' else 'deflate-' + fixture['name']
        definition = next(c for c in catalog if c['id'] == id_)
        measurement = {**definition['measurement'], 'comparison_note': note, 'warmup_calls': 1}
        contract = {'input_sha256': file_digest(path / 'input'), 'prefix_sha256': file_digest(path / 'prefix'), 'required': 'complete valid raw DEFLATE; unchanged held aliases; independently owned output',
                    'quality': 'Mech/Roc exact level-12; Rust zlib-rs maximum level 9; output size reported', 'boundary': 'One complete compressor call, output allocation and scratch destruction included', 'warmup_calls': 1}
        records = {backend: make_record(campaign, definition, backend, {**measurement, 'artifact_form': backend}, (ROOT / definition['source']).read_text(), worker['revision'], contract)
                   for backend in ('program-jit', 'program-jit-bytecode')}
        records['rust'] = make_record(campaign, definition, 'rust', measurement, (directory / 'rust-source/deflate.rs').read_text(), rust['source_sha256']['deflate.rs'], contract, implementation=rust)
        records['rust']['title'] = 'Rust · zlib-rs level 9'
        records['rust']['task'] = {**definition['task'], 'dtype': 'u8 stream; zlib-rs maximum level 9', 'arithmetic': 'Raw DEFLATE, zlib-rs 0.6.8 level 9, complete input consumed',
                                  'ordering': 'Owned prefix followed by complete independently valid DEFLATE stream; different compressed bytes permitted',
                                  'ownership': 'Native Rust ownership; input/prefix held unchanged; fresh separately owned output; compressor scratch released during call'}
        records['rust']['task_hash'] = digest(records['rust']['task'])
        compression_records[fixture['name']] = records
    for fork in [None, *range(args.forks)]:
        order = ['program-jit', 'program-jit-bytecode', 'rust']; rng.shuffle(order)
        for backend in order:
            label = 'verify' if fork is None else f'fork-{fork+1}'
            print(f'Deflate all 12 inputs / {backend} / {label}', flush=True)
            if backend == 'rust':
                for f in fixtures:
                    raw = directory / 'raw/deflate-rust' / label / f['name']
                    out_path = raw / 'compressed.deflate'
                    response = checked([rust['binaries']['deflate']['binary'], f['input'], f['prefix'], '1', out_path], raw, args.timeout)
                    receipt = json.loads((raw / 'stdout.txt').read_text())
                    if receipt.get('aliases_preserved') is not True or receipt.get('separately_owned_output') is not True: raise ValueError('Rust compression ownership failed')
                    compressed = out_path.read_bytes()
                    validation = validate_deflate(compressed, Path(f['input']).read_bytes(), Path(f['prefix']).read_bytes())
                    if receipt['metrics'].get('output_bytes') != len(compressed) or receipt['metrics'].get('input_bytes') != validation['input_bytes']:
                        raise ValueError('Rust reported sizes differ from independently checked input/output')
                    receipt['metrics']['native_process_seconds'] = response['seconds']
                    receipt['final_output'] = {'kind': 'deflate', 'sha256': hashlib.sha256(compressed).hexdigest(), **validation}
                    save(raw / 'supervised.json', receipt)
                    accept(campaign, directory, compression_records[f['name']][backend], receipt, raw, fork, note)
            else:
                form = 'source' if backend == 'program-jit' else 'bytecode'
                raw = directory / 'raw/deflate-mech' / form / label
                request = {'protocol': 1, 'action': 'application_jit', 'backend': form, 'source': (ROOT / 'suite/applications/deflate.mec').read_text(),
                           'schedule': [[]], 'output': 'result', 'application_cases': fixtures, 'warmup': 1,
                           'compile_limits': json.loads((ROOT / 'suite/applications/deflate-compiler-policy.json').read_text()),
                           'launch_policy': json.loads((ROOT / 'suite/applications/deflate-launch-policy.json').read_text())}
                response = invoke([worker['binary']], request, raw, args.timeout)
                if response.get('outcome') != 'ok': raise ValueError('Mech full compressor failed: ' + str(response.get('error')))
                if [r['name'] for r in response['application_results']] != [f['name'] for f in fixtures]: raise ValueError('Mech omitted or reordered compressor input')
                for f, result in zip(fixtures, response['application_results']):
                    compressed = bytes.fromhex(result['raw_hex'])
                    validation = validate_deflate(compressed, Path(f['input']).read_bytes(), Path(f['prefix']).read_bytes(), Path(f['expected']).read_bytes())
                    if result.get('aliases_preserved') is not True or result['metrics']['managed_after_drop_bytes'] != 0: raise ValueError('Mech compressor ownership failed')
                    case_raw = raw / 'cases' / f['name']
                    receipt = {'outcome': 'ok', 'metrics': {**result['metrics'], **response['metrics'], 'output_bytes': len(compressed)}, 'derived_metrics': ['output_bytes'], 'final_output': {'kind': 'deflate', 'sha256': hashlib.sha256(compressed).hexdigest(), **validation},
                               'parent_observation': {'path': (raw / 'stdout.json').relative_to(directory).as_posix(), 'sha256': file_digest(raw / 'stdout.json'), 'case': f['name']}}
                    save(case_raw / 'supervised.json', receipt)
                    accept(campaign, directory, compression_records[f['name']][backend], receipt, case_raw, fork, note)


def run(args):
    directory = args.output.resolve()
    if directory.exists(): raise ValueError('choose a new campaign directory')
    worker = worker_provenance(args.worker)
    host = environment(); rng = random.Random(args.seed)
    campaign = {'schema': SCHEMA, 'id': directory.name, 'started_at': datetime.now(timezone.utc).isoformat(),
                'profile': 'paired-rust-' + args.group, 'environment': host, 'environment_hash': digest(host),
                'workers': {'candidate': worker}, 'sampling': {'forks': args.forks, 'cycles': args.cycles, 'seed': args.seed,
                'order': 'Seeded random order within every case/fork block; verification separate; all measured observations retained'},
                'results': [], 'order': [], 'comparisons': [], 'complete': False, 'performance_gate': False,
                'catalog_sha256': file_digest(ROOT / 'suite/catalog.json')}
    with campaign_lock(ROOT / '.local'):
        directory.mkdir(parents=True)
        save(directory / 'campaign.json', campaign)
        try:
            preserve_worker(worker, directory / 'workers/candidate')
            shutil.copyfile(ROOT / 'suite/catalog.json', directory / 'catalog.json')
            harness = directory / 'harness'; harness.mkdir()
            for name in ('run_rust_suite.py', 'benchmark_suite.py', 'suite_oracle.py', 'extended_oracles.py', 'run_concurrent.py', 'run_native.py', 'application_tasks.py'):
                shutil.copyfile(ROOT / 'tools' / name, harness / name)
            campaign['harness_sha256'] = {p.name: file_digest(p) for p in harness.iterdir()}
            rust = build_rust(directory, args.timeout); campaign['rust'] = rust
            globals()[args.group](args, campaign, directory, worker, rust, rng)
            if not campaign['results']: raise ValueError('selection produced no task records')
            for record in campaign['results']:
                if len(record['samples']) != args.forks: raise ValueError('incomplete forks')
                record.update(outcome='ok', progress='measured', summary=summarize(record['samples']))
            campaign.update(complete=True, outcome='ok', finished_at=datetime.now(timezone.utc).isoformat())
        except Exception as error:
            for record in campaign['results']:
                record.update(outcome='error', summary={}, reason=str(error))
            campaign.update(complete=True, outcome='failed', error=str(error), finished_at=datetime.now(timezone.utc).isoformat())
            save(directory / 'campaign.json', campaign)
            (directory / 'report.md').write_text('# Rust task controls failed\n\n' + str(error) + '\n')
            seal_evidence(directory); archive_evidence(directory)
            raise
        save(directory / 'campaign.json', campaign)
        introduction = {'resident': NOTE, 'concurrent': NOTE + ' The primary clock is the complete supervised process group.',
                        'native': campaign['results'][0]['measurement']['comparison_note'],
                        'applications': 'Full-size K-nucleotide uses the complete fresh-process boundary. The 12 compressor cases use complete checked compressor calls, with output allocation and scratch destruction included. Compilation, input import, one warmup and returned-output destruction are outside the call. Rust zlib-rs level 9 and Mech level 12 may produce different compressed sizes; inspect size with time.'}[args.group]
        (directory / 'report.md').write_text(task_report(campaign, args.group, introduction))
        seal_evidence(directory); archive_evidence(directory); validate_campaign(directory, campaign)
    print(directory / 'report.md', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--group', choices=('resident', 'concurrent', 'applications', 'native'), default='resident')
    p.add_argument('--application-worker', type=Path); p.add_argument('--fasta', type=Path); p.add_argument('--corpus', type=Path)
    p.add_argument('--forks', type=int, default=5); p.add_argument('--cycles', type=int, default=1000)
    p.add_argument('--seed', type=int, default=202611172); p.add_argument('--timeout', type=float, default=1800)
    p.add_argument('--case', action='append')
    a = p.parse_args()
    if a.forks < 3 or a.cycles < 1 or a.timeout <= 0: p.error('at least three forks and positive cycles/deadline required')
    run(a)
