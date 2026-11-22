"""Recompute the retained packet-motion study without rerunning primary clocks."""
import argparse
import ast
from collections import Counter
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from runpy import run_path
import statistics
import struct
import tarfile
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: sha256(Path(p).read_bytes()).hexdigest()
path = HERE.parent / 'argument-jump-forwarding/verify_runtime.py'
spec = importlib.util.spec_from_file_location('private_packet_raw_runtime', path)
raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw)


def helpers():
    path = HERE.parent / 'encoder-size-gap/packet-family-root-study/verify.py'
    source = path.read_text()
    selected = '\n\n'.join(ast.get_source_segment(source, node)
                           for node in ast.parse(source).body
                           if isinstance(node, ast.FunctionDef)
                           and node.name in ['native', 'text_bytes', 'complete_builds'])

    def checked_output(root, role, name, file):
        historical = role / 'checked-emission/frontend' / file
        # Early raw probes saved only normal emission. Their actual public
        # checked source replay supplies the independent checked artifact.
        return historical if historical.is_file() else (
            root / 'study/public-replays' / (name + '-checked') / 'frontend' / file)

    needle = "sha(role/'checked-emission/frontend'/file)"
    assert selected.count(needle) == 1
    selected = selected.replace(needle, 'sha(checked_output(root, role, name, file))')
    scope = dict(HERE=HERE, read=read, sha=sha, sha256=sha256, Counter=Counter,
                 Path=Path, generate=lambda source: source, struct=struct,
                 statistics=statistics, zlib=zlib, raw=raw, checked_output=checked_output)
    exec(compile(selected, str(path), 'exec'), scope)
    return scope


def source_proofs(root):
    producers = {}
    for kind, version in [('compiler', 1), ('compiler', 2), ('compiler', 3), ('tests', 1)]:
        folder = root / f'study/producers/{kind}-v{version}'
        producer = read(folder / 'build.json')
        assert producer['exit_code'] == 0 and len(producer['source_sha256']) >= 63
        for name, pin in producer['source_sha256'].items():
            assert sha(folder / 'source-inputs' / name) == pin
        producers[kind, version] = producer
    compiler = producers['compiler', 3]
    binding = read(root / 'study/committed-source-binding.json')
    assert binding['source_sha256'] == compiler['source_sha256']
    assert binding['producer_sha256'] == sha(root / 'study/producers/compiler-v3/build.json')
    assert binding['implementation_commit'] == read(HERE / 'summary.json')['source_implementation_commit']
    recipes = read(HERE / 'recipes.json')['roles']
    records = read(root / 'study/public-replays/verification.json')
    assert records['all_three_exact'] and len(records['records']) == 2 * len(recipes)
    assert all(record['compiler_sha256'] == compiler['compiler_sha256']
               for record in records['records'])
    assert all(recipe['compiler_sha256'] == compiler['compiler_sha256']
               for recipe in recipes.values())
    assert len({recipe['artifacts']['program.mecb'] for recipe in recipes.values()}) == 1
    prior = read(HERE.parent / 'packed-node-histogram/recipes.json')['roles']['progressive-16']
    assert recipes['control']['artifacts'] == prior['artifacts']
    assert recipes['control']['text_bytes'] == prior['text_bytes'] == 63784
    assert recipes['control']['worker_sha256'] == prior['worker_sha256']
    assert not read(HERE / 'summary.json')['selected_default_changed']
    tests = producers['tests', 1]
    folder = root / 'study/test-execution-v1'
    result = read(folder / 'result.json')
    binary, = [row for row in tests['executables'] if row['target'] == 'mech_gpu']
    assert result['executable_sha256'] == binary['sha256']
    for run in result['runs']:
        assert run['exit_code'] == 0
        assert f"test result: ok. {run['passed_expected']} passed; 0 failed;" in (
            folder / (run['name'] + '.stdout')).read_text()
    transcript = (folder / 'packet_storage.stderr').read_text()
    calls = sum(int(line.rsplit(': ', 1)[1]) for line in transcript.splitlines()
                if 'native calls:' in line)
    assert calls == result['movable_packet_native_calls'] == 25344
    assert result['movable_packet_native_calls_recomputed_from_transcript'] == calls
    validation = read(root / 'study/child-profile-validation/result.json')
    assert validation['mismatched_child_profile_rejected'] and validation['exit_code'] != 0
    return calls


def instruction_counts(root):
    kernel = run_path(str(HERE.parent / 'semantic-block-map/derive_static_register_weights.py'))['kernel']
    checked = 0
    for recipe in read(HERE / 'recipes.json')['roles'].values():
        role = root / 'study' / recipe['local_role']
        for folder in sorted(role.glob('counts-*')):
            counts = read(folder / 'counts.json')
            canonical = read(folder / 'canonical-counts.json')
            assert counts['object_sha256'] == sha(role / 'frontend/program.o') == recipe['artifacts']['program.o']
            assert sha(folder / 'canonical-counts.json') == counts['canonical_counts_sha256']
            original = role / 'canonical-counter-input/frontend/program.o'
            assert sha(original) == canonical['object_sha256']
            atom = read(role / 'receipt.json')['layout']['symbols'][counts['symbol']]
            body = kernel(role / 'frontend/program.o', atom['start'], atom['extent'])
            assert sha256(body).hexdigest() == atom['sha256']
            assert body == kernel(original, atom['start'] - counts['address_translation'], atom['extent'])
            plan = read(folder / 'plan.json')
            assert sha(role / 'bound/mech-worker') == sha(role / 'canonical-counter-input/bound/mech-worker') == plan['source_worker_sha256'] == plan['canonical_worker_sha256']
            for sample in canonical['cases'].values():
                for block in sample['blocks']:
                    block['address'] = hex(int(block['address'], 16) + counts['address_translation'])
            assert canonical['cases'] == counts['cases'] and len(counts['cases']) == 9
            for sample in counts['cases'].values():
                assert sample['counts']['instructions'] == sum(
                    block['visits'] * len(block['instructions']) for block in sample['blocks'])
            checked += len(counts['cases'])
    return checked


def runtime(root, summary):
    fixtures = {row['name']:row for row in read(root / 'runtime/fixtures.json')}
    oracle = {row['case']:row for row in read(root / 'runtime/C-output-oracle.json')}
    policy = read(root / 'runtime/working-selection-policy.json')
    recipes = read(HERE / 'recipes.json')['roles']

    def validate(actor, value, row):
        assert all(value[key] == fixtures[row['case']][key] for key in ['input_bytes', 'prefix_bytes'])
        assert not value['warmup'] and not value['profile']
        if actor == 'libdeflate':
            assert value['level'] == 12 and value['version'] == '1.26'
            assert all(value[key] == oracle[row['case']][key]
                       for key in ['output_sha256', 'capacity', 'raw_bytes', 'matches_reference_bytes'])
        else:
            assert value['raw_bytes'] == fixtures[row['case']]['raw_bytes']
            assert value['capacity'] == fixtures[row['case']]['capacity']

    raw.VALUE_VALIDATOR = validate
    observations = zeros = orders = 0
    for campaign in summary['runtime_campaigns']:
        role = campaign['plan']['role']
        assert campaign['complete'] and len(campaign['runs']) == 2
        assert campaign['plan']['control_worker_sha256'] == recipes['control']['worker_sha256']
        assert campaign['plan']['candidate_worker_sha256'] == recipes[role]['worker_sha256']
        assert len(campaign['plan']['cases']) == 21
        for run in campaign['runs']:
            assert all(not names for names in run['required_named_missing'].values())
            cases = {row['case'] for row in run['results']}
            for peer, names in policy['required_peer_wins'].items():
                wins = {row['case'] for row in run['results']
                        if row['paired_x_' + peer]['mech-experiment'] < 1}
                assert sorted((set(names) & cases) - wins) == run['required_named_missing'][peer]
        checked, _, zero = raw.runtime(root / 'runtime', campaign['runs'], 21, 96)
        observations += checked
        zeros += zero
        orders += len(campaign['runs'])
    return observations, zeros, orders


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    summary, manifest = read(HERE / 'summary.json'), read(HERE / 'archives.json')
    with tempfile.TemporaryDirectory(prefix='mech-private-packet-verify-') as temporary:
        root = Path(temporary)
        for name, record in manifest.items():
            archive = HERE / name
            assert archive.stat().st_size == record['bytes'] and sha(archive) == record['sha256']
            with tarfile.open(archive, 'r:gz') as stream:
                stream.extractall(root, filter='data')
            for member, pin in record['files_sha256'].items():
                assert sha(root / member) == pin
        functions = helpers()
        native = functions['native'](root)
        focused = source_proofs(root)
        dense = run_path(str(HERE / 'analyze_dense_codes.py'))['analyze'](
            root / 'study/disabled/frontend/program.o')
        assert dense == summary['next_dense_code_study']
        counters = instruction_counts(root)
        observed, zeros, orders = runtime(root, summary)
        builds, outputs = functions['complete_builds'](root, summary)
        result = {'native_source_replays':native, 'focused_packet_native_calls':focused,
                  'actual_counter_cases':counters, 'runtime_observations':observed,
                  'zero_durations_retained':zeros, 'runtime_orders':orders,
                  'complete_build_orders':builds, 'deployment_outputs':outputs}
        if args.record:
            (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
        else:
            assert result == read(HERE / 'verification.json')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
