"""Verify archived bytes, raw paired statistics, named wins and deployed streams."""
from hashlib import sha256
from pathlib import Path
from statistics import mean, median
import gzip
import json
import math
import re
import tarfile
import tempfile
import zlib

HERE = Path(__file__).resolve().parent


def digest(data):
    return sha256(data).hexdigest()


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-15), (a, b)


def main():
    archive = json.loads((HERE / 'archive.json').read_text())
    manifest = json.loads((HERE / 'raw-manifest.json').read_text())
    assert digest((HERE / 'raw.tar.gz').read_bytes()) == archive['archive_sha256']
    assert digest((HERE / 'raw-manifest.json').read_bytes()) == archive['manifest_sha256']
    assert len(manifest['files']) == archive['files']
    with tempfile.TemporaryDirectory(prefix='mech-pair-evidence-') as temporary:
        root = Path(temporary)
        seen = set()
        with tarfile.open(HERE / 'raw.tar.gz', 'r|gz') as stream:
            for member in stream:
                assert member.isfile() and re.fullmatch(r'blobs/[0-9a-f]{64}', member.name)
                pin = member.name.split('/')[1]
                assert pin not in seen
                data = stream.extractfile(member).read()
                assert digest(data) == pin
                (root / pin).write_bytes(data)
                seen.add(pin)
        assert len(seen) == archive['unique_blobs']
        for item in manifest['files'].values():
            assert item['sha256'] in seen and (root / item['sha256']).stat().st_size == item['bytes']

        def content(path):
            return (root / manifest['files'][path]['sha256']).read_bytes()

        def read(path):
            return json.loads(content(path))

        summary = json.loads((HERE / 'summary.json').read_text())
        recipes = json.loads((HERE / 'recipes.json').read_text())
        policy = read('study/full81-v1/qualification-policy-as-run.json')
        full = read('study/full81-v1/biased-pair-linear-results.json')
        assert full['complete'] and len(full['runs']) == 2
        total_observations = 0
        for run in full['runs']:
            base = 'runtime/' + Path(run['run']).name
            rows = read(base + '/summary.json')
            assert len(rows) == 81
            wins = {'roc': set(), 'libdeflate': set()}
            for row in rows:
                blocks = json.loads(gzip.decompress(content(
                    base + '/' + row['case'] + '/observations.json.gz')))
                assert len(blocks) == 96
                seconds = {actor: [] for actor in ('mech-control', 'mech-experiment', 'roc', 'libdeflate')}
                ratios = {peer: {actor: [] for actor in seconds} for peer in wins}
                for block in blocks:
                    assert sorted(block['order']) == sorted(seconds)
                    means = {}
                    for actor, samples in block['observations'].items():
                        assert samples
                        for value in samples:
                            assert value['case'] == row['case']
                            assert math.isfinite(value['seconds']) and value['seconds'] >= 0
                            assert not value['warmup'] and not value['profile']
                            assert all(value[k] for k in ('independent_inflation', 'input_alias_unchanged',
                                                         'borrowed_output_alias_unchanged'))
                            if actor != 'libdeflate':
                                assert value['exact_reference']
                            else:
                                assert value['level'] == 12 and value['version'] == '1.26'
                        values = [v['seconds'] for v in samples]
                        seconds[actor].extend(values)
                        means[actor] = mean(values)
                        # Preserve the timer's treatment of quantized individual
                        # zeros on trivial calls; every paired block is positive.
                        assert means[actor] > 0
                        close(means[actor], block['means'][actor])
                        total_observations += len(values)
                    for peer in ratios:
                        for actor in seconds:
                            ratios[peer][actor].append(math.log(means[actor] / means[peer]))
                for actor in seconds:
                    close(median(seconds[actor]), row['median_seconds'][actor])
                    for peer in ratios:
                        calculated = math.exp(mean(ratios[peer][actor]))
                        close(calculated, row['paired_x_' + peer][actor])
                        if actor == 'mech-experiment' and calculated < 1:
                            wins[peer].add(row['case'])
            assert len(wins['roc']) == 81 and len(wins['libdeflate']) == 63
            for peer, names in policy['required_peer_wins'].items():
                assert set(names) <= wins[peer]
            for actor in ('mech-control', 'mech-experiment'):
                assert content(base + '/' + actor + '.stderr').decode().endswith(
                    'CLEANUP private_payload_bytes=0 live_owner_records=0\n')

        for role, recipe in recipes['roles'].items():
            for name, pin in recipe['artifacts'].items():
                assert digest(content('study/census/' + role + '/frontend/' + name)) == pin
                assert digest(content('study/census/' + role + '/checked-emission/frontend/' + name)) == pin
            assert recipe['artifacts']['program.mecb'] == recipes['roles']['control']['artifacts']['program.mecb']
            assert read('study/census/' + role + '/linked-proof.json')['candidate_peak_stack_bytes'] == 4736
            assert read('study/census/' + role + '/promotion-recoveries/result.json')['exact_recoveries'] == 12
        tests = read('study/native-tests-v1/result.json')
        assert tests['complete'] and tests['all_pass'] and len(tests['runs']) == 3
        assert '3 passed; 0 failed' in content('study/native-tests-v1/pairs.log').decode()
        assert '3618' in content('study/native-tests-v1/pairs.log').decode()
        for label in ('scalar-default', 'scalar-pairs-and-native-reuse'):
            assert '80 passed; 0 failed' in content('study/native-tests-v1/' + label + '.log').decode()
        for folder in ('public-source-replay-v1', 'public-checked-replay-v1'):
            replay = read('study/' + folder + '/reproduction.json')
            assert replay['source_commit'] == summary['source_commit']
            assert len(replay['records']) == 2 and all(r['all_three_exact'] for r in replay['records'])

        build = read('study/matched-builds-v1/comparison.json')
        assert len(build['observations']) == 8
        for actor, warm in build['warmup'].items():
            pin = digest(content('study/matched-builds-v1/warmup/' + actor + '/compressor'))
            for index, trial in enumerate(build['observations'], 1):
                assert trial[actor]['stripped_executable'] == warm['stripped_executable']
                assert digest(content('study/matched-builds-v1/order-' + str(index) + '/' + actor + '/compressor')) == pin
            close(median(row[actor]['seconds']['source_through_link'] for row in build['observations']),
                  summary['complete_build']['medians'][actor]['source_through_link'])
        fixtures = read('fixtures.json')
        indices = {row['name']: i for i, row in enumerate(fixtures)}
        deployment = read('study/matched-builds-v1/deployment-smokes.json')
        assert deployment['checked_executions'] == len(deployment['records']) == 324
        for row in deployment['records']:
            index = indices[row['case']]
            original = content(f'fixtures/{index}/input')
            prefix = content(f'fixtures/{index}/prefix')
            expected = content(f'fixtures/{index}/expected')
            raw = content('study/matched-builds-v1/' + row['output_file'])
            assert digest(original) == row['input_sha256'] and digest(raw) == row['output_sha256']
            assert zlib.decompress(raw, -15) == original
            if row['actor'] != 'libdeflate':
                assert raw == expected[len(prefix):]
        report = {'verified': True, 'files': len(manifest['files']), 'blobs': len(seen),
                  'full81_raw_observations': total_observations, 'runtime_wins_each_order': {'roc': 81, 'libdeflate': 63},
                  'standalone_inflations': 324, 'source_commit': summary['source_commit'],
                  'scope': 'Recorded data and source-emission identity checks; no new timing or confidence claim.'}
        (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
