"""Replay native gates, source provenance, diagnostic counts and saved runtime observations."""
import argparse
import ast
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from runpy import run_path
import statistics
import struct
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / 'argument-jump-forwarding'
sys.path.insert(0, str(PREVIOUS))
import verify_runtime as raw

read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: sha256(Path(p).read_bytes()).hexdigest()


def native_helpers():
    path = HERE.parent / 'encoder-size-gap/packet-family-root-study/verify.py'
    text = path.read_text()
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)
             and n.name in ['native', 'text_bytes', 'complete_builds']]
    source = '\n\n'.join(ast.get_source_segment(text, n) for n in nodes)
    source = source.replace("sha(role/'checked-emission/frontend'/file)",
                            "sha(root/'study/public-replays'/(name+'-checked')/'frontend'/file)")
    scope = dict(HERE=HERE, read=read, sha=sha, sha256=sha256, Counter=Counter,
                 Path=Path, generate=lambda s: s, struct=struct, statistics=statistics,
                 zlib=zlib, raw=raw)
    exec(compile(source, str(path), 'exec'), scope)
    return scope


def source_provenance(root):
    compiler = read(root / 'study/compiler-source/build.json')
    assert compiler['exit_code'] == 0 and len(compiler['source_sha256']) == 52
    assert compiler['source_base'].startswith('a26552db4')
    for name, pin in compiler['source_sha256'].items():
        assert sha(root / 'study/compiler-source/source-inputs' / name) == pin
    records = read(root / 'study/source-replays-reviewed/verification.json')
    assert records['all_three_exact'] and len(records['records']) == 16
    for record in records['records']:
        assert record['compiler_sha256'] == compiler['compiler_sha256']
        folder = root / 'study/source-replays-reviewed' / (record['role'] + ('-checked' if record['checked'] else '-normal'))
        for name, pin in record['artifacts'].items():
            assert sha(folder / 'frontend' / name) == pin
    reference = read(HERE.parent / 'histogram-counter-capacity/recipes.json')['roles']['capacity-grouped']
    recipes = read(HERE / 'recipes.json')['roles']
    assert recipes['control']['artifacts'] == reference['artifacts']
    for recipe in recipes.values():
        assert recipe['source_sha256'] == reference['source_sha256']
        assert recipe['artifacts']['program.mecb'] == reference['artifacts']['program.mecb']
        assert recipe['compiler_sha256'] == compiler['compiler_sha256']
    execution = root / 'study/optimized-execution'
    result = read(execution / 'result.json')
    producer = read(root / 'study/optimized-tests-source/build.json')
    assert result['executable_sha256'] == producer['executables'][0]['sha256']
    assert result['histogram_focused_native_calls'] == 40725
    assert result['common_select_focused_native_calls'] == 12
    for name, count in [('selects',8), ('histogram',5), ('scalar',79),
                        ('current_predicates',10), ('identical_arguments',2), ('selected_increments',4)]:
        record = next(r for r in result['runs'] if r['name'] == name)
        assert record['exit_code'] == 0
        assert f'test result: ok. {count} passed; 0 failed;' in (execution / (name + '.stdout')).read_text()
    return len(records['records'])


def training_counts(root):
    kernel = run_path(str(HERE.parent / 'semantic-block-map/derive_static_register_weights.py'))['kernel']
    cases = 0
    for path in sorted((root / 'study').glob('*/counts-475/counts.json')):
        role = path.parent.parent
        if role.name == 'control':
            continue
        counts = read(path)
        receipt = read(role / 'receipt.json')
        assert counts['object_sha256'] == sha(role / 'frontend/program.o') == receipt['artifacts']['program.o']
        canonical_path = path.with_name('canonical-counts.json')
        canonical = read(canonical_path)
        assert sha(canonical_path) == counts['canonical_counts_sha256']
        original = role / 'canonical-counter-input/frontend/program.o'
        assert sha(original) == canonical['object_sha256']
        atom = receipt['layout']['symbols'][counts['symbol']]
        body = kernel(role / 'frontend/program.o', atom['start'], atom['extent'])
        assert sha256(body).hexdigest() == atom['sha256']
        assert body == kernel(original, atom['start'] - counts['address_translation'], atom['extent'])
        plan = read(path.with_name('plan.json'))
        assert sha(role / 'bound/mech-worker') == sha(role / 'canonical-counter-input/bound/mech-worker') == plan['source_worker_sha256'] == plan['canonical_worker_sha256']
        for sample in canonical['cases'].values():
            for block in sample['blocks']:
                block['address'] = hex(int(block['address'], 16) + counts['address_translation'])
        assert canonical['cases'] == counts['cases'] and len(counts['cases']) == 9
        for sample in counts['cases'].values():
            assert sample['counts']['instructions'] == sum(b['visits'] * len(b['instructions']) for b in sample['blocks'])
        cases += len(counts['cases'])
    assert cases == 207
    return cases


def register_profiles(root):
    derive = run_path(str(HERE.parent / 'semantic-block-map/derive_static_register_weights.py'))['derive']
    arms = ['control','select','early-cheap','late-cheap','combined-cheap','late-existing','late-paired']
    for arm in arms:
        profiles, proof = derive(root / 'study' / (arm + '-raw'))
        folder = root / 'study/register-profiles' / arm
        assert proof == read(folder / 'derivation.json')
        for name, profile in profiles.items():
            assert profile == read(folder / (name + '.json'))
    return len(arms)


def machine_layouts(root):
    path = root / 'study/tools/derive-coalesced-layout.py'
    derive = run_path(str(path))['derive']
    count = 0
    for profile_path in sorted((root / 'study/machine-layouts').glob('*.json')):
        role = root / 'study' / (profile_path.stem + '-raw')
        shape = read(role / 'counts-475/native-shape.json')
        trace = read(role / 'counts-475/counts.json')
        profile, proof = derive(shape, trace)
        record = read(role / 'flow-layout-derivation.json')
        assert profile == read(profile_path)
        assert sha(profile_path) == record['profile_sha256']
        assert sha(path) == record['deriver_sha256']
        assert sha(role / 'counts-475/counts.json') == record['training_counts_sha256']
        serialized_proof = json.loads(json.dumps(proof))
        assert all(record[key] == value for key, value in serialized_proof.items())
        count += 1
    assert count == 14
    return count


def runtime_observations(root, summary):
    fixtures = {v['name']:v for v in read(root / 'runtime/fixtures.json')}
    oracle = {v['case']:v for v in read(root / 'runtime/C-output-oracle.json')}
    policy = read(root / 'runtime/working-selection-policy.json')
    recipes = read(HERE / 'recipes.json')['roles']
    def validate(actor, value, row):
        fixture = fixtures[row['case']]
        assert all(value[k] == fixture[k] for k in ['input_bytes','prefix_bytes'])
        assert not value['warmup'] and not value['profile']
        if actor == 'libdeflate':
            assert value['level'] == 12 and value['version'] == '1.26'
            assert all(value[k] == oracle[row['case']][k] for k in ['output_sha256','capacity','raw_bytes','matches_reference_bytes'])
        else:
            assert value['raw_bytes'] == fixture['raw_bytes'] and value['capacity'] == fixture['capacity']
    raw.VALUE_VALIDATOR = validate
    observations = zeros = 0
    for role, campaign in summary['panels'].items():
        assert campaign['complete'] and len(campaign['runs']) == 2
        assert campaign['plan']['control_worker_sha256'] == recipes['control']['worker_sha256']
        assert campaign['plan']['candidate_worker_sha256'] == recipes[role]['worker_sha256']
        for run in campaign['runs']:
            cases = {r['case'] for r in run['results']}
            for peer, required in policy['required_peer_wins'].items():
                wins = {r['case'] for r in run['results'] if r['paired_x_' + peer]['mech-experiment'] < 1}
                assert sorted((set(required) & cases) - wins) == run['required_named_missing'][peer]
        checked, _, zero = raw.runtime(root / 'runtime', campaign['runs'], 21, 96)
        observations += checked; zeros += zero
    for role, campaign in summary['full_qualification'].items():
        assert campaign['complete'] and len(campaign['runs']) == 2
        assert campaign['plan']['selected_control_worker'] == recipes['control']['worker_sha256']
        assert campaign['plan']['candidate_worker'] == recipes[role]['worker_sha256']
        passed = True
        for run in campaign['runs']:
            for peer, names in policy['required_peer_wins'].items():
                wins = {r['case'] for r in run['results'] if r['paired_x_' + peer]['mech-experiment'] < 1}
                missing = sorted(set(names) - wins)
                outcome = {'wins':len(wins), 'required_missing':missing,
                           'passed':not missing and len(wins) >= policy['peer_win_floors'][peer]}
                assert outcome == run['peers'][peer]
                passed &= outcome['passed']
        assert campaign['point_passed'] == passed
        checked, _, zero = raw.runtime(root / 'runtime', campaign['runs'], 81, 96)
        observations += checked; zeros += zero
    return observations, zeros


def sampled_observations(root):
    path = HERE.parent / 'histogram-counter-capacity/verify.py'
    source = path.read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'sampling')
    source = ast.get_source_segment(source, node).replace('study/capacity-grouped/bound/mech-worker','study/late-existing-linear/bound/mech-worker')
    namespace = dict(read=read, sha=sha, json=json)
    exec(compile(source, str(path), 'exec'), namespace)
    count = namespace['sampling'](root)
    assert count == 200800
    assert run_path(str(HERE / 'derive_sampling.py'))['derive'](root / 'study') == read(HERE / 'sampling.json')
    return count


def main_source_recipes(root, summary):
    if not summary['selected_default_changed']:
        return 0
    folder = root / 'study/main-default-source-replays'
    records = read(folder / 'verification.json')
    recipes = read(HERE / 'recipes.json')['roles']
    assert len(records) == 2 and sum(r['default_invocation'] for r in records.values()) == 1
    for role in ['late-existing-linear','late-existing-sqrt']:
        name = 'm1-matcher-existing-' + role.removeprefix('late-existing-')
        record = records[name]
        assert record['all_three_exact'] and record['artifacts'] == recipes[role]['artifacts']
        assert record['compiler_sha256'] == recipes[role]['compiler_sha256']
        assert record['default_invocation'] == (role == summary['selected_role'])
        assert record['rebuild_py_sha256'] == sha(folder / 'rebuild-as-run.py')
        assert sha(folder / role / 'native/program.o') == record['artifacts']['program.o']
        assert sha(folder / role / 'native/metadata.json') == record['artifacts']['metadata.json']
        assert sha(folder / role / 'frontend/program.mecb') == record['artifacts']['program.mecb']
    return len(records)


def compiler_bindings(root):
    plan = read(root / 'builds/plan.json')
    for actor, job in plan['actors'].items():
        if not actor.startswith('mech-'):
            continue
        folder = 'reference-compiler' if actor == 'mech-control-reference' else 'compiler-source'
        path = root / 'study' / folder / 'build.json'
        compiler = read(path)
        assert sha(path) == job['compiler_source_overlay_manifest_sha256']
        assert compiler['compiler_sha256'] == job['compiler_sha256']
        for name, pin in compiler['source_sha256'].items():
            assert sha(path.parent / 'source-inputs' / name) == pin
    comparison = read(root / 'builds/comparison.json')
    for actor, phases in comparison['phases'].items():
        for phase, value in phases.items():
            raw.close(value, statistics.median(next(p['seconds'] for p in trial[actor]['compiler_phases'] if p['phase'] == phase) for trial in comparison['observations']))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--extract-to', type=Path)
    args = parser.parse_args()
    manifest = read(HERE / 'manifest.json')
    for name, pin in manifest['helper_sha256'].items():
        assert sha(HERE / name) == pin
    previous = run_path(str(PREVIOUS / 'verify.py'), run_name='prior_extract_helper')
    with tempfile.TemporaryDirectory() as directory:
        root = args.extract_to.resolve() if args.extract_to else Path(directory)
        if args.extract_to:
            root.mkdir(parents=True, exist_ok=False)
        for name, spec in manifest['archives'].items():
            previous['extract'](root, spec, HERE / name)
        functions = native_helpers()
        replays = functions['native'](root)
        reviewed = source_provenance(root)
        diagnostic_cases = training_counts(root)
        profiles = register_profiles(root)
        layouts = machine_layouts(root)
        summary = read(HERE / 'summary.json')
        observations, zeros = runtime_observations(root, summary)
        main_replays = main_source_recipes(root, summary)
        sampled = sampled_observations(root)
        parity = run_path(str(HERE / 'derive_parity.py'))['derive'](summary)
        assert parity == read(HERE / 'parity.json')
        build_orders = deployments = 0
        if 'builds' in summary:
            compiler_bindings(root)
            build_orders, deployments = functions['complete_builds'](root, summary)
        print(json.dumps({'public_source_replays':replays,'reviewed_earlier_source_replays':reviewed,
                          'diagnostic_cases':diagnostic_cases,'register_profile_arms':profiles,
                          'recomputed_machine_layouts':layouts,
                          'runtime_observations':observations,'retained_zero_observations':zeros,
                          'complete_build_orders':build_orders,'deployed_executions':deployments,
                          'actual_main_source_replays':main_replays,'diagnostic_sampling_observations':sampled,
                          'selected_default_changed':summary['selected_default_changed']}, indent=2))


if __name__ == '__main__':
    main()
