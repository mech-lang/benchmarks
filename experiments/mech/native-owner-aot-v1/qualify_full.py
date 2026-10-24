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
parser.add_argument('--order', nargs='+', choices=('rust', 'mech', 'baseline'),
                    help='Execution order; must list each selected executable exactly once')
parser.add_argument('--require-packed-map', action='store_true',
                    help='Require the candidate to select packed storage for all regions and updates; also inherited from its prefix receipt')
parser.add_argument('--require-parallel-tasks', type=int, choices=[7],
                    help='Require one combined batch, two source regions and seven tasks; also inherited from the prefix receipt')
parser.add_argument('--minimum-parallel-peak', type=int,
                    help='Minimum observed simultaneous workers (1–7); cannot weaken the prefix requirement')
args = parser.parse_args()
assert bool(args.parent_receipt) == bool(args.parent_binary)
out = HERE / args.receipt
timing = json.loads((HERE / args.timing / 'results.json').read_text())
compiler = json.loads((HERE / args.compiler / 'results.json').read_text())
assert timing['status'] == 'all-outputs-and-update-counts-verified'
assert compiler['source_commit'] == timing['source_commit']
if timing.get('require_key_bits') is not None:
    assert timing.get('source_key_domains_qualified') is True
require_guarded_loops = timing.get('require_guarded_loops', False)
if require_guarded_loops:
    assert timing.get('source_guarded_loops_qualified') is True
    assert timing.get('source_tag_threading_qualified') is True
require_frozen_maps = timing.get('require_frozen_maps', False)
if require_frozen_maps:
    assert timing.get('source_frozen_maps_qualified') is True
require_lookup_facts = timing.get('require_lookup_facts', False)
if require_lookup_facts:
    assert timing.get('source_lookup_facts_qualified') is True
require_parallel_tasks = args.require_parallel_tasks or timing.get('require_parallel_tasks')
assert require_parallel_tasks in (None, 7)
if args.minimum_parallel_peak is not None and (
        require_parallel_tasks is None or not 1 <= args.minimum_parallel_peak <= require_parallel_tasks):
    parser.error('--minimum-parallel-peak requires seven parallel tasks, explicitly or from the prefix receipt, and a value from 1 to 7')
minimum_parallel_peak = max(args.minimum_parallel_peak or 1,
                            timing.get('minimum_parallel_peak') or 1) if require_parallel_tasks else None
assert minimum_parallel_peak is None or 1 <= minimum_parallel_peak <= require_parallel_tasks
require_packed_map = args.require_packed_map or timing.get('require_packed_map', False) or require_parallel_tasks is not None or require_guarded_loops or require_frozen_maps or require_lookup_facts
require_packed_ssa = timing.get('require_packed_ssa', False) or require_parallel_tasks is not None or require_guarded_loops or require_frozen_maps or require_lookup_facts
out.mkdir(exist_ok=False)
targets = dict(rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7',
               mech=HERE / '.build' / args.binary)
assert process.sha(targets['rust']) == timing['rust_sha256']
assert process.sha(targets['mech']) == timing['candidate_sha256']
if timing.get('source_edge_facts_qualified') or timing.get('source_tag_threading_qualified') or timing.get('source_frame_effects_qualified') or require_guarded_loops or require_frozen_maps or require_lookup_facts:
    project = Path(str(targets['mech']) + '.project')
    for key in ('compiled_source_edge_facts', 'compiled_tag_threading', 'compiled_frame_effects', 'compiled_guarded_loops', 'compiled_lookup_facts'):
        if timing.get(key) is not None:
            assert timing[key]['complete'] is True
    assert process.sha(project / 'program.o') == timing['object_sha256']
    assert process.sha(project / 'linked-manifest.json') == timing['linked_manifest_sha256']
    assert process.sha(project / 'native-descriptor.json') == timing['native_descriptor_sha256']
parent = None
if args.parent_receipt:
    parent = json.loads((HERE / args.parent_receipt / 'results.json').read_text())
    assert parent['status'] == 'all-outputs-and-update-counts-verified'
    assert parent['source_sha256'] == timing['source_sha256']
    assert parent['rust_sha256'] == timing['rust_sha256']
    targets['baseline'] = HERE / '.build' / args.parent_binary
    assert process.sha(targets['baseline']) == parent['candidate_sha256']
order = args.order or list(targets)
if len(order) != len(targets) or set(order) != set(targets):
    parser.error('--order must list each selected executable exactly once')
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
              configuration=vars(args), samples=[], native_executions=[],
              require_packed_map=require_packed_map, require_packed_ssa=require_packed_ssa,
              require_guarded_loops=require_guarded_loops,
              require_frozen_maps=require_frozen_maps,
              require_lookup_facts=require_lookup_facts,
              require_key_bits=timing.get('require_key_bits'),
              source_key_domains_qualified=timing.get('source_key_domains_qualified'),
              closed_key_domains=timing.get('closed_key_domains'),
              native_descriptor_sha256=timing.get('native_descriptor_sha256'),
              require_parallel_tasks=require_parallel_tasks, minimum_parallel_peak=minimum_parallel_peak,
              scope='Single serial complete process per executable, including secured Mech startup/shutdown; full-input qualification, not median benchmark timings; no excluded warmup')
if timing.get('source_edge_facts_qualified'):
    for key in ('source_edge_facts_qualified', 'compiled_source_edge_facts',
                'qualified_source_edge_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if timing.get('source_tag_threading_qualified'):
    for key in ('source_tag_threading_qualified', 'compiled_tag_threading',
                'qualified_tag_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if timing.get('source_frame_effects_qualified'):
    for key in ('source_frame_effects_qualified', 'compiled_frame_effects',
                'qualified_frame_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if require_guarded_loops:
    for key in ('source_guarded_loops_qualified', 'compiled_guarded_loops',
                'qualified_guarded_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if require_frozen_maps:
    for key in ('source_frozen_maps_qualified', 'frozen_map_layout',
                'qualified_frozen_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if require_lookup_facts:
    for key in ('source_lookup_facts_qualified', 'compiled_lookup_facts',
                'qualified_lookup_regions', 'object_sha256', 'linked_manifest_sha256'):
        report[key] = timing[key]
if parent:
    report['baseline_source_commit'] = parent['source_commit']
    report['baseline_sha256'] = parent['candidate_sha256']
process.save(out / 'results.json', report)
try:
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for label in order:
            binary = targets[label]
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
                packed = dict(packed_map_regions=native.get('native_packed_map_regions'),
                              packed_map_updates=native.get('native_packed_map_updates'),
                              packed_ssa_regions=native.get('native_packed_ssa_regions'),
                              guarded_loop_regions=native.get('native_guarded_loop_regions'),
                              frozen_map_regions=native.get('native_frozen_map_regions'),
                              frozen_map_reads=native.get('native_frozen_map_reads'))
                parallel = dict(parallel_batches=native.get('native_parallel_batches'),
                                parallel_regions=native.get('native_parallel_regions'),
                                parallel_tasks=native.get('native_parallel_tasks'),
                                parallel_peak_workers=native.get('native_parallel_peak_workers'))
                report['native_executions'].append(dict(label=label, native_visits=native['native_visits'],
                                                         **packed, **parallel))
                if label == 'mech' and require_packed_map:
                    assert packed['packed_map_regions'] == 7, 'Candidate fell back from packed map regions'
                    assert packed['packed_map_updates'] == 874999961, 'Candidate did not complete every update in packed storage'
                if label == 'mech' and require_packed_ssa:
                    assert packed['packed_ssa_regions'] == 7, 'Candidate fell back from generated SSA loops'
                if label == 'mech' and require_guarded_loops:
                    assert packed['guarded_loop_regions'] == 7, 'Candidate did not select all seven guarded loop versions'
                if label == 'mech' and require_frozen_maps:
                    assert packed['frozen_map_regions'] == 5 and packed['frozen_map_reads'] == 10, 'Candidate did not retain five complete query maps and perform ten original reads'
                if label == 'mech' and require_parallel_tasks:
                    assert parallel['parallel_batches'] == 1, 'Candidate did not combine work into one batch'
                    assert parallel['parallel_regions'] == 2, 'Candidate did not complete both source comprehensions in parallel'
                    assert parallel['parallel_tasks'] == require_parallel_tasks, 'Candidate did not complete all seven parallel tasks'
                    assert isinstance(parallel['parallel_peak_workers'], int) and minimum_parallel_peak <= parallel['parallel_peak_workers'] <= require_parallel_tasks, 'Candidate did not reach the required simultaneous worker count'
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
