"""Compare macOS whole-process instruction/cycle counters on qualified input."""
import argparse
import fcntl
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('--timing', required=True)
parser.add_argument('--compiler', required=True)
parser.add_argument('--input-mode', choices=('full', 'prefix'), default='full')
args = parser.parse_args()
timing = json.loads((HERE / args.timing / 'results.json').read_text())
compiler = json.loads((HERE / args.compiler / 'results.json').read_text())
assert timing['status'] == 'all-outputs-and-update-counts-verified'
assert timing['source_commit'] == compiler['source_commit']
config = timing['configuration']
targets = dict(mech=HERE / '.build' / config['binary'],
               baseline=HERE / '.build' / config['parent_binary'],
               rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
for label, key in [('mech', 'candidate_sha256'), ('baseline', 'baseline_sha256'), ('rust', 'rust_sha256')]:
    assert process.sha(targets[label]) == timing[key]
if args.input_mode == 'full':
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    input_sha = '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    launch = HERE / 'full-lookup-facts-v1/launch.json'
    launch_sha = '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
    bases, updates = 125000000, 874999961
    output_sha = 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
else:
    inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
    input_sha = 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
    launch = HERE / 'full-timing-v1/launch.json'
    launch_sha = '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
    bases, updates = 1000000, 6999961
    output_sha = 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
assert process.sha(inp) == input_sha and process.sha(launch) == launch_sha
out = HERE / args.receipt
out.mkdir(exist_ok=False)
report = dict(status='running', source_commit=timing['source_commit'],
              candidate_sha256=timing['candidate_sha256'], baseline_sha256=timing['baseline_sha256'],
              rust_sha256=timing['rust_sha256'], input_sha256=process.sha(inp),
              source_sha256=timing['source_sha256'], baseline_source_sha256=timing.get('baseline_source_sha256', timing['source_sha256']),
              source_comparison=timing.get('source_comparison', 'unchanged-source'), launch_sha256=process.sha(launch),
              timer='/usr/bin/time -l', input_mode=args.input_mode, selected_bases=bases, expected_table_updates=updates,
              observations=[], benchmark_samples=0, script_sha256=process.sha(Path(__file__)),
              scope='macOS whole-process counters reported by time -l, including startup/shutdown and all target threads; diagnostic executions under the shared serial lock, not additional benchmark timing observations.')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index, order in enumerate([['rust', 'mech', 'baseline'], ['baseline', 'rust', 'mech'], ['mech', 'baseline', 'rust']]):
        for label in order:
            native_path = out / f'{index}-{label}.native.json'
            command = ['/usr/bin/time', '-l', str(targets[label])]
            if label != 'rust': command += [str(launch), str(native_path), '--']
            folder = out / f'{index}-{label}'
            result = process.execute(command, folder, compiler['environment'], lock, stdin=inp, deadline=60, quantitative=False)
            assert result['exit_status'] == 0
            assert process.sha(folder / 'stdout.bin') == output_sha
            if label != 'rust':
                native = json.loads(native_path.read_text())
                assert native['shutdown'] == 'completed'
                assert native['native_packed_map_regions'] == native['native_packed_ssa_regions'] == 7
                # Explicit source studies can intentionally change which loop
                # certificates apply. Require the independently observed prefix
                # strategy, and retain the original seven-guard requirement.
                prefix_label = 'candidate' if label == 'mech' else 'baseline'
                entries = [row for row in timing['native_executions'] if row['label'] == prefix_label]
                expected_guards = {row['guarded_loop_regions'] for row in entries}
                assert len(expected_guards) == 1
                assert native['native_guarded_loop_regions'] in expected_guards
                if label == 'baseline' or timing.get('require_guarded_loops'):
                    assert native['native_guarded_loop_regions'] == 7
                assert native['native_packed_map_updates'] == updates
                assert native['native_frozen_map_regions'] == 5 and native['native_frozen_map_reads'] == 10
                assert native['native_parallel_tasks'] == native['native_parallel_peak_workers'] == 7
                if label == 'mech' and timing.get('require_loop_invariants'):
                    assert native['native_guarded_call_regions'] == 7
            raw = (folder / 'stderr.bin').read_text()
            def counter(name):
                found = re.findall(r'^\s*(\d+)\s+' + re.escape(name) + r'\s*$', raw, re.M)
                assert len(found) == 1, (name, raw)
                return int(found[0])
            elapsed = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', raw)
            assert elapsed
            observation = dict(cohort=index, label=label, instructions=counter('instructions retired'),
                               cycles=counter('cycles elapsed'), real_seconds=float(elapsed[1]),
                               user_seconds=float(elapsed[2]), system_seconds=float(elapsed[3]),
                               maximum_rss_bytes=counter('maximum resident set size'),
                               involuntary_context_switches=counter('involuntary context switches'),
                               process_sha256=process.sha(folder / 'process.json'), counters_sha256=process.sha(folder / 'stderr.bin'))
            assert observation['instructions'] > 0 and observation['cycles'] > 0
            report['observations'].append(observation)
            process.save(out / 'results.json', report)
            print(json.dumps(observation), flush=True)
report['medians'] = {label: {metric: statistics.median(row[metric] for row in report['observations'] if row['label'] == label)
                           for metric in ('instructions', 'cycles', 'real_seconds', 'user_seconds', 'system_seconds')}
                     for label in targets}
report['status'] = 'all-complete-outputs-updates-and-hardware-counters-verified'
process.save(out / 'results.json', report)
