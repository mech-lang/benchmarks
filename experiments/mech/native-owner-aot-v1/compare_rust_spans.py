"""Pair existing executables on the same standard-record prefix; no rebuilds."""
import argparse
import fcntl
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process
sys.path.insert(0, str(HERE.parent / 'canonical-native-integration-v1'))
from qualify import oracle

parser = argparse.ArgumentParser()
parser.add_argument('--bases', type=int, default=100000)
parser.add_argument('--receipt', default='rust-span-diagnostic-v1')
args = parser.parse_args()
assert 18 <= args.bases <= 125000000
out = HERE / args.receipt
out.mkdir(exist_ok=False)
env = json.loads((HERE / 'compiler-v4/results.json').read_text())['environment']
mech = HERE / '.build/counting-spans'
rust = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
assert process.sha(mech) == '6dbb7b58332bd8cf6b156f0861e55597440e107c4b940b8bd102c703149b9d8a'
assert process.sha(rust) == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
report = dict(status='preparing', input_bases=args.bases,
              source_commit='7aa1bea1b5565113cd07ddeaeea2bed30ed84a54',
              mech_sha256=process.sha(mech), rust_sha256=process.sha(rust),
              launch_sha256=process.sha(policy), samples=[],
              scope='Standard THREE prefix; complete fresh processes; secured Mech AOT; diagnostic only')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    full_path = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    assert process.sha(full_path) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    pieces, length, selected = [], 0, False
    with full_path.open('rb') as full:
        for line in full:
            if not selected:
                selected = line.startswith(b'>THREE ')
                continue
            chunk = line.strip()[:args.bases-length]
            pieces.append(chunk)
            length += len(chunk)
            if length == args.bases:
                break
    assert length == args.bases
    sequence = b''.join(pieces)
    raw = b'>THREE\n' + b'\n'.join(sequence[i:i+60] for i in range(0, length, 60)) + b'\n'
    inp = out / 'input.fasta'
    inp.write_bytes(raw)
    expected = oracle(raw)
    (out / 'expected.txt').write_bytes(expected)
    report.update(status='running', input_sha256=process.sha(inp))
    process.save(out / 'results.json', report)

    def run(label, round_number, timed):
        name = f'{round_number}-{label}'
        command = [str(rust)] if label == 'rust' else [str(mech), str(policy), str(out / (name + '.report.json')), '--']
        result = process.execute(command, out / name, env, lock, stdin=inp, deadline=120, quantitative=timed)
        assert result['exit_status'] == 0
        if (out / name / 'stdout.bin').read_bytes() != expected:
            report.update(status='correctness-failed', failed_subject=name)
            process.save(out / 'results.json', report)
            raise AssertionError(f'{label} differs from the independent reference')
        if label == 'mech':
            native = json.loads((out / (name + '.report.json')).read_text())
            assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
            assert native['shutdown'] == 'completed'
            assert native['native_hash_table_regions'] == 7 and native['native_hash_table_updates'] == 7 * args.bases - 39
        if timed:
            row = dict(label=label, seconds=result['elapsed_seconds'], maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in ['rust', 'mech']:
        run(label, 'warmup', False)
    for index, order in enumerate([['mech', 'rust'], ['rust', 'mech'], ['mech', 'rust']]):
        for label in order:
            run(label, index, True)
report['median_seconds'] = {label: statistics.median(row['seconds'] for row in report['samples'] if row['label'] == label) for label in ['mech', 'rust']}
report['x_rust'] = {label: seconds / report['median_seconds']['rust'] for label, seconds in report['median_seconds'].items()}
report['denominator'] = f'Unmodified upstream Rust #7 on the same {args.bases}-base input and machine'
report['status'] = 'all-outputs-verified'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
