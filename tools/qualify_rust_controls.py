#!/usr/bin/env python3
"""Check independent Rust task trajectories and complete compressed streams; no performance gate."""
import argparse
import copy
import json
from pathlib import Path

from benchmark_suite import ROOT, file_digest, invoke, load_catalog, save
from run_rust_suite import checked, rust_response
from suite_oracle import outputs
from application_tasks import validate_deflate


def qualify(binary_directory, directory):
    directory = directory.resolve()
    if directory.exists(): raise ValueError('choose a fresh evidence directory')
    directory.mkdir(parents=True)
    checked_cases = []
    cases = [c for c in load_catalog()['cases'] if set(c['backends']) & {'source', 'bytecode', 'jit'}]
    # Additional inputs exercise arbitrary data rather than just catalog answers.
    for identifier, schedule in [('scalar-changed', [[-13.25], [0.125], [4.5], [-13.25]]),
                                 ('retained-snapshots', [[float(i-20) for i in range(70)], [0., -2.], [3., -4., 5.]]),
                                 ('table-full-outer-join', [[4.], [-9.], [1.], [4.]]),
                                 ('graphs', [[-2.], [0.125], [3.5]])]:
        case = copy.deepcopy(next(c for c in cases if c['id'] == identifier))
        case['id'] += '-additional-inputs'; case['measurement']['schedule'] = schedule; cases.append(case)
    for case in cases:
        count = len(case['measurement']['schedule']) * (1 if case['id'] == 'ekf' else 2)
        request = {'protocol': 1, 'action': 'verify', 'oracle': case['task']['oracle'], 'output': case['task']['outputs'][0],
                   **case['measurement'], 'warmup': 32, 'iterations': count}
        response = invoke([str(binary_directory / 'resident')], request, directory / case['id'], 120)
        rust_response(response, outputs(case, count), case, count, verify=True)
        checked_cases.append(case['id']); print('PASS ' + case['id'], flush=True)
    fixtures = json.loads((ROOT / 'suite/applications/deflate-compress-reference.json').read_text())['cases']
    fixtures = [{**f, 'input': bytes(f['input']), 'prefix': bytes(f['prefix'])} for f in fixtures]
    for name in ('16384-distribution-change', '33027-periodic-window'):
        fixtures.append({'name': name, 'input': (ROOT / 'suite/applications' / ('deflate-boundary-' + name + '.input')).read_bytes(), 'prefix': b''})
    for fixture in fixtures:
        path = directory / 'compression' / fixture['name']; path.mkdir(parents=True)
        for name in ('input', 'prefix'): (path / name).write_bytes(fixture[name])
        checked([binary_directory / 'deflate', path / 'input', path / 'prefix', '1', path / 'output'], path / 'run', 120)
        response = json.loads((path / 'run/stdout.txt').read_text())
        if response.get('aliases_preserved') is not True or response.get('separately_owned_output') is not True: raise ValueError('compression ownership failed')
        validate_deflate((path / 'output').read_bytes(), fixture['input'], fixture['prefix'])
        checked_cases.append('deflate-' + fixture['name']); print('PASS deflate-' + fixture['name'], flush=True)
    receipt = {'schema': 'mech.rust-control-correctness.v1', 'outcome': 'ok', 'checks': checked_cases,
               'binaries': {name: file_digest(binary_directory / name) for name in ('resident', 'deflate')}}
    save(directory / 'qualification.json', receipt)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--binaries', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); qualify(a.binaries.resolve(), a.output)
