"""Paired source-map measurements on a pinned prefix of the standard sequence."""
import fcntl, json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process
sys.path.insert(0, str(HERE.parent / 'canonical-native-integration-v1'))
from qualify import oracle

out = HERE / 'cache-scale-v1'
out.mkdir()
measured = json.loads((HERE / 'cache-timing-v2/results.json').read_bytes())
assert measured['status'] == 'all-outputs-verified'
env = json.loads((HERE / 'compiler-v3/results.json').read_bytes())['environment']
targets = dict(candidate=HERE / '.build/counting-cache', baseline=HERE / '.build/counting-candidate')
for label, binary in targets.items():
    assert process.sha(binary) == measured[label + '_sha256']
policy = HERE / 'full-timing-v1/launch.json'
report = dict(status='running',source_commit=measured['source_commit'],candidate_sha256=measured['candidate_sha256'],baseline_sha256=measured['baseline_sha256'],input_bases=100000,scope='First 100000 bases of standard THREE; complete secured processes; same full-input launch limits; diagnostic only',samples=[])
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    pieces = []
    length = 0
    selected = False
    with (ROOT / 'experiments/janet/.build/inputs/fasta-n25000000.stdin').open('rb') as full:
        for line in full:
            if not selected:
                selected = line.startswith(b'>THREE ')
                continue
            chunk = line.strip()
            pieces.append(chunk[:100000-length])
            length += len(pieces[-1])
            if length == 100000:
                break
    assert length == 100000
    sequence = b''.join(pieces)
    raw = b'>THREE\n' + b'\n'.join(sequence[i:i+60] for i in range(0, len(sequence), 60)) + b'\n'
    inp = out / 'input.fasta'
    inp.write_bytes(raw)
    expected = oracle(raw)
    (out / 'expected.txt').write_bytes(expected)
    report.update(input_sha256=process.sha(inp),launch_sha256=process.sha(policy))
    process.save(out / 'results.json', report)
    for i, order in enumerate([['candidate','baseline'],['baseline','candidate'],['candidate','baseline']]):
        for label in order:
            name = f'round-{i}-{label}'
            r = process.execute([str(targets[label]), str(policy), str(out / (name + '.report.json')), '--'], out / name, env, lock, stdin=inp, deadline=120, quantitative=True)
            assert r['exit_status'] == 0, (out / name / 'stderr.bin').read_text()[-3000:]
            assert (out / name / 'stdout.bin').read_bytes() == expected
            row = dict(label=label,seconds=r['elapsed_seconds'],maximum_rss_bytes=r['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)
medians = {label: statistics.median(s['seconds'] for s in report['samples'] if s['label'] == label) for label in targets}
report.update(status='all-outputs-verified',median_seconds=medians,x_mech_aot={label: value/medians['candidate'] for label,value in medians.items()},denominator='Current source-map Mech AOT median on the same 100000-base prefix')
process.save(out / 'results.json', report)
print(json.dumps({k:report[k] for k in ['median_seconds','x_mech_aot']}), flush=True)
