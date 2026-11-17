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
        'Rust uses native ownership; Mech additionally performs its runtime admission, dependency scheduling, budget accounting and turn summary. '
        'This measures the cost of completing the task through each path, not a language-wide speed claim. '
        'Compilation is outside the resident timer. Rust preparation is not presented as a Mech artifact or JIT metric.')


def rust_response(response, expected, case, count, verify=False):
    if response.get('outcome') != 'ok':
        raise ValueError('Rust worker failed: ' + str(response.get('error')))
    if response.get('iterations') != count or response.get('output_name') != case['task']['outputs'][0]:
        raise ValueError('Rust iteration count or named output differs')
    if not equal(response.get('final_output'), expected[-1], case['task']):
        raise ValueError('Rust endpoint differs from independent oracle')
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
    else:
        record['samples'].append({'fork': fork, 'raw': relative, 'metrics': response['metrics'], 'final_output': response.get('final_output', response.get('outputs'))})
        campaign['order'].append({'case_id': record['case_id'], 'backend': record['backend'], 'fork': fork, 'lane': record['lane']})
    save(directory / 'campaign.json', campaign)


def resident(args, campaign, directory, worker, rust, rng):
    cases = [c for c in load_catalog()['cases'] if set(c['backends']) & {'source', 'bytecode', 'jit'}]
    if args.case:
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
        lines = ['# Paired Rust task controls', '', NOTE, '', '| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |', '| --- | ---: | ---: | ---: |']
        for record in campaign['results']:
            if record['lane'] == 'control': continue
            control = next(r for r in campaign['results'] if r['case_id'] == record['case_id'] and r['lane'] == 'control')
            metric = record['measurement'].get('primary_metric', 'resident_turn_seconds')
            mapped = control['measurement'].get('metric_mapping', {}).get(metric, metric)
            m = record['summary'][metric]['median']; r = control['summary'][mapped]['median']
            lines.append(f'| {record["case_id"]} / {record["backend"]} | {m:.9g} | {r:.9g} | {m/r:.3f} |')
        (directory / 'report.md').write_text('\n'.join(lines) + '\n')
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
