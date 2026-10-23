"""One complete full-input execution per binary, with exact independent output checks."""
import argparse
import fcntl
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

parser = argparse.ArgumentParser()
parser.add_argument('--timing', required=True)
parser.add_argument('--compiler', required=True)
parser.add_argument('--binary', required=True)
parser.add_argument('--receipt', required=True)
parser.add_argument('--comparison-work', type=int)
parser.add_argument('--parent-receipt')
parser.add_argument('--parent-binary')
args = parser.parse_args()
assert bool(args.parent_receipt) == bool(args.parent_binary)
out = HERE / args.receipt
out.mkdir(exist_ok=False)
timing = json.loads((HERE / args.timing / 'results.json').read_text())
compiler = json.loads((HERE / args.compiler / 'results.json').read_text())
assert timing['status'] == 'all-outputs-and-update-counts-verified'
assert compiler['source_commit'] == timing['source_commit']
targets = dict(rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7',
               mech=HERE / '.build' / args.binary)
assert process.sha(targets['rust']) == timing['rust_sha256']
assert process.sha(targets['mech']) == timing['candidate_sha256']
parent = None
if args.parent_receipt:
    parent = json.loads((HERE / args.parent_receipt / 'results.json').read_text())
    assert parent['status'] == 'all-outputs-and-update-counts-verified'
    assert parent['source_sha256'] == timing['source_sha256']
    assert parent['rust_sha256'] == timing['rust_sha256']
    targets['baseline'] = HERE / '.build' / args.parent_binary
    assert process.sha(targets['baseline']) == parent['candidate_sha256']
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
assert process.sha(inp) == '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
launch = json.loads(policy.read_text())
old_work = launch['work']
# The prefix's conservative table/collision work envelope scales past the
# earlier root allowance at full size. Increase that finite invocation quota;
# every debit, capability grant and per-call resource limit stays active.
launch['work'] = 1 << 60
old_comparison = launch['library']['comparison_work']
if args.comparison_work is not None:
    assert 0 < args.comparison_work <= (1 << 60)
    launch['library']['comparison_work'] = args.comparison_work
process.save(out / 'launch.json', launch)
report = dict(status='running', source_commit=timing['source_commit'],
              source_sha256=timing['source_sha256'], input_sha256=process.sha(inp),
              selected_bases=125000000, expected_table_updates=874999961,
              candidate_sha256=process.sha(targets['mech']), rust_sha256=process.sha(targets['rust']),
              launch_sha256=process.sha(out / 'launch.json'),
              root_work_quota_change=dict(previous=old_work, current=launch['work']),
              comparison_quota_change=dict(previous=old_comparison,
                                           current=launch['library']['comparison_work']),
              configuration=vars(args), samples=[],
              scope='Single serial complete process per executable, including secured Mech startup/shutdown; full-input qualification, not median benchmark timings; no excluded warmup')
if parent:
    report['baseline_source_commit'] = parent['source_commit']
    report['baseline_sha256'] = parent['candidate_sha256']
process.save(out / 'results.json', report)
try:
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for label, binary in targets.items():
            command = [str(binary)]
            native_report = out / ('native.report.json' if label == 'mech' else label + '.native.report.json')
            if label != 'rust':
                command += [str(out / 'launch.json'), str(native_report), '--']
            result = process.execute(command, out / label, compiler['environment'], lock,
                                     stdin=inp, deadline=300, quantitative=True)
            assert result['exit_status'] == 0, (out / label / 'stderr.bin').read_text()[-3000:]
            assert process.sha(out / label / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
            if label != 'rust':
                native = json.loads(native_report.read_text())
                assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
                assert native['shutdown'] == 'completed'
                assert native['native_hash_table_regions'] == 7
                assert native['native_hash_table_updates'] == 874999961
            row = dict(label=label, seconds=result['elapsed_seconds'],
                       maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)
    seconds = {row['label']: row['seconds'] for row in report['samples']}
    report['x_rust'] = {label: value / seconds['rust'] for label, value in seconds.items()}
    report['status'] = 'full-output-and-update-counts-verified'
except BaseException as error:
    report['status'] = 'not-a-successful-full-timing'
    report['failure'] = repr(error)
    raise
finally:
    process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
