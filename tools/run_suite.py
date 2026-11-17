#!/usr/bin/env python3
"""Run validated Mech benchmark campaigns, sequentially, with immutable raw evidence."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import random
import subprocess
import sys

from benchmark_suite import (ROOT, SCHEMA, campaign_lock, comparison, digest, environment,
    file_digest, invoke, load_catalog, measurement_response, report, save, summarize,
    verify_response, worker_provenance, preserve_worker, seal_evidence, archive_evidence)


def run(args):
    catalog = load_catalog(args.catalog)
    selected = set(args.case or [])
    if selected - {c['id'] for c in catalog['cases']}:
        raise ValueError('unknown case id: ' + ', '.join(sorted(selected - {c['id'] for c in catalog['cases']})))
    cases = [c for c in catalog['cases'] if (not selected or c['id'] in selected) and c['progress'] != 'planned'
             and set(c['backends']) & {'source', 'bytecode'}]
    if not cases:
        raise ValueError('selection has no implemented cases; planned coverage cannot be reported as unsupported')
    profile = dict(catalog['profiles'][args.profile])
    if args.forks is not None:
        profile['forks'] = args.forks
    if args.cycles is not None:
        profile['cycles'] = args.cycles
    if min(profile.values()) < 1:
        raise ValueError('forks, cycles and warmup must be positive')
    workers = {'candidate': worker_provenance(args.worker)}
    if args.baseline:
        workers['baseline'] = worker_provenance(args.baseline)
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f'campaign directory already exists: {output}; use a new directory to preserve raw evidence')
    rng = random.Random(args.seed)
    host = environment()
    campaign = {'schema': SCHEMA, 'id': output.name, 'started_at': datetime.now(timezone.utc).isoformat(),
                'profile': args.profile, 'sampling': profile, 'seed': args.seed, 'environment': host,
                'environment_hash': digest(host), 'workers': workers, 'catalog_sha256': file_digest(args.catalog),
                'harness_sha256': {name: file_digest(ROOT / 'tools' / name) for name in
                    ('run_suite.py', 'benchmark_suite.py', 'suite_oracle.py')},
                'performance_gate': False, 'results': [], 'order': [], 'comparisons': [], 'complete': False}
    with campaign_lock(ROOT / '.local'):
        output.mkdir(parents=True)
        for lane, worker in workers.items():
            preserve_worker(worker, output / 'workers' / lane)
        save(output / 'campaign.json', campaign)
        for case in cases:
            print(f"Verify {case['id']}", flush=True)
            source = (ROOT / case['source']).read_text()
            save(output / 'fixtures' / (case['id'] + '.json'), case)
            (output / 'fixtures' / (case['id'] + '.mec')).write_text(source)
            measurement = {**case['measurement'], 'warmup': profile['warmup'], 'cycles': profile['cycles'],
                           'output': case['task']['outputs'][0], 'timing_loop': 'v1 explicit Instant block; setup/destruction outside',
                           'memory_budget_bytes':1 << 34,'summary':'included in turn',
                           'allocator':'global allocation/reallocation counter with relaxed atomics'}
            count = len(measurement['schedule']) * profile['cycles']
            oracle = invoke([sys.executable, str(ROOT / 'tools/suite_oracle.py')],
                            {'case': case, 'count': count}, output / 'raw' / case['id'] / 'oracle', args.timeout)
            if oracle.get('outcome') != 'ok' or len(oracle.get('outputs', [])) != count:
                raise ValueError(f"independent oracle failed for {case['id']}")
            expected = oracle['outputs']
            records = {}
            for backend in case['backends']:
                if args.backend and backend not in args.backend:
                    continue
                for lane, worker in workers.items():
                    record = {'case_id': case['id'], 'title': case['title'], 'family': case['family'],
                              'backend': backend, 'lane': lane, 'revision': worker['revision'], 'progress': 'implemented',
                              'feature_profile':{'profile':worker['feature_profile'],'native_generation':worker.get('native_generation',False)},
                              'capability': 'unknown', 'outcome': 'pending', 'task_hash': digest(case['task']),
                              'measurement_hash': digest(measurement), 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                              'environment_hash': campaign['environment_hash'], 'task': case['task'],
                              'measurement': measurement, 'source': source, 'samples': []}
                    records[backend, lane] = record
                    campaign['results'].append(record)
                    request = {'protocol': 1, 'action': 'verify', 'source': source, 'backend': backend,
                               'output': case['task']['outputs'][0], **measurement, 'iterations': count}
                    raw = Path('raw') / case['id'] / backend / lane / 'verify'
                    response = invoke([worker['binary']], request, output / raw, args.timeout)
                    status, reason = verify_response(response, expected, case)
                    record['verification'] = {'outcome': status, 'reason': reason, 'raw': raw.as_posix(),
                                              'outputs': response.get('outputs'), 'before_execution': response.get('before_execution')}
                    if status == 'ok':
                        record.update(progress='verified', capability='supported', outcome='ok')
                    else:
                        record.update(outcome=status, reason=reason)
                # Alternating, seed-selected order creates recorded baseline/candidate blocks.
                first = list(workers)
                rng.shuffle(first)
                for fork in range(profile['forks']):
                    lanes = first if fork % 2 == 0 else first[::-1]
                    for lane in lanes:
                        record = records[backend, lane]
                        if record['outcome'] != 'ok':
                            continue
                        print(f"Measure {case['id']} / {backend} / {lane} / fork {fork + 1}", flush=True)
                        worker = workers[lane]
                        if file_digest(worker['binary']) != worker['binary_sha256']:
                            raise ValueError('worker binary changed during campaign')
                        request = {'protocol': 1, 'action': 'measure', 'source': source, 'backend': backend,
                                   **measurement, 'iterations': count}
                        raw = Path('raw') / case['id'] / backend / lane / f'fork-{fork + 1}'
                        campaign['order'].append({'case_id': case['id'], 'backend': backend, 'fork': fork, 'lane': lane})
                        response = invoke([worker['binary']], request, output / raw, args.timeout)
                        status, reason = measurement_response(response, expected[-1], case, count)
                        if status == 'ok':
                            record['samples'].append({'fork': fork, 'raw': raw.as_posix(), 'metrics': response['metrics'],
                                                      'final_output': response['final_output'],
                                                      'worker_protocol_process_seconds': response['worker_protocol_process_seconds']})
                        else:
                            record.update(outcome=status, reason=reason)
                            record['failed_observation'] = raw.as_posix()
                    save(output / 'campaign.json', campaign)
                for lane in workers:
                    record = records[backend, lane]
                    if record['outcome'] == 'ok' and len(record['samples']) == profile['forks']:
                        record['progress'] = 'measured'
                        record['summary'] = summarize(record['samples'])
                    else:
                        record['summary'] = {}  # Partial/incorrect samples never become accepted timings.
                if args.baseline:
                    campaign['comparisons'].append({'case_id': case['id'], 'backend': backend,
                        **comparison(records[backend, 'baseline'], records[backend, 'candidate'], seed=args.seed)})
            save(output / 'campaign.json', campaign)
        campaign['complete'] = True
        campaign['finished_at'] = datetime.now(timezone.utc).isoformat()
        campaign['outcome'] = 'ok' if all(r['outcome'] == 'ok' for r in campaign['results']) else 'failed'
        save(output / 'campaign.json', campaign)
        (output / 'report.md').write_text(report(campaign))
        seal_evidence(output)
        archive_evidence(output)
        print(f"Campaign {campaign['outcome']}: {output / 'report.md'}", flush=True)
    return 0 if campaign['outcome'] == 'ok' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', required=True, type=Path, help='candidate worker.json from build_worker.py')
    parser.add_argument('--baseline', type=Path, help='independently built baseline worker.json')
    parser.add_argument('--output', required=True, type=Path, help='new campaign directory, normally results/campaigns/<id>')
    parser.add_argument('--catalog', type=Path, default=ROOT / 'suite/catalog.json')
    parser.add_argument('--profile', choices=('smoke', 'standard', 'regression'), default='standard')
    parser.add_argument('--case', action='append', help='repeat to select cases')
    parser.add_argument('--backend', action='append', choices=('source', 'bytecode'))
    parser.add_argument('--forks', type=int)
    parser.add_argument('--cycles', type=int)
    parser.add_argument('--seed', type=int, default=1729)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('timeout must be positive')
    try:
        sys.exit(run(args))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, f'Campaign error: {error}\n')


if __name__ == '__main__':
    main()
