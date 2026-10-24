"""Summarize complete full-input cohorts without dropping any observations."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--receipt', required=True)
parser.add_argument('runs', nargs='+')
args = parser.parse_args()
assert len(args.runs) >= 3 and len(set(args.runs)) == len(args.runs)
reports = [json.loads((HERE / run / 'results.json').read_text()) for run in args.runs]
identity = ['source_commit', 'baseline_source_commit', 'source_sha256', 'input_sha256',
            'source_comparison', 'baseline_source_sha256', 'bytecode_sha256', 'baseline_bytecode_sha256',
            'candidate_sha256', 'baseline_sha256', 'rust_sha256', 'launch_sha256',
            'selected_bases', 'expected_table_updates', 'require_packed_map',
            'require_packed_ssa', 'require_parallel_tasks', 'minimum_parallel_peak',
            'source_edge_facts_qualified', 'compiled_source_edge_facts',
            'qualified_source_edge_regions', 'object_sha256', 'linked_manifest_sha256',
            'source_tag_threading_qualified', 'compiled_tag_threading', 'qualified_tag_regions',
            'source_frame_effects_qualified', 'compiled_frame_effects', 'qualified_frame_regions',
            'require_guarded_loops', 'source_guarded_loops_qualified',
            'compiled_guarded_loops', 'qualified_guarded_regions', 'native_descriptor_sha256',
            'require_frozen_maps', 'source_frozen_maps_qualified', 'frozen_map_layout', 'qualified_frozen_regions',
            'require_lookup_facts', 'source_lookup_facts_qualified', 'compiled_lookup_facts', 'qualified_lookup_regions',
            'require_cfg_cleanup', 'cfg_cleanup_qualified', 'compiled_cfg_cleanup', 'cfg_cleanup_removed_total', 'single_data_pass_qualified',
            'require_outlined_loops', 'outlined_loops_qualified', 'compiled_outlined_loops',
            'require_loop_invariants', 'loop_invariants_qualified', 'compiled_loop_invariants', 'qualified_invariant_regions',
            'require_preserving_calls', 'preserving_calls_qualified', 'compiled_bound_call_shim', 'compiled_preserving_call_regions',
            'require_mutation_facts', 'mutation_facts_qualified', 'compiled_mutation_loops', 'qualified_mutation_regions',
            'require_count_values', 'count_values_qualified', 'compiled_count_value_loops', 'qualified_count_value_regions']
first = reports[0]
samples = {}
receipts = []
for run, report in zip(args.runs, reports):
    assert report['status'] == 'full-output-and-update-counts-verified'
    assert all(report.get(key) == first.get(key) for key in identity)
    if report.get('require_preserving_calls'):
        assert report.get('preserving_calls_qualified') is True
        assert report['compiled_bound_call_shim']['code_bytes'] <= 512
    if report.get('require_mutation_facts'):
        assert report.get('mutation_facts_qualified') is True
        assert report['compiled_mutation_loops'] and report['qualified_mutation_regions']
    if report.get('require_count_values'):
        assert report.get('count_values_qualified') is True and report.get('require_mutation_facts')
        assert report['compiled_count_value_loops'] and report['qualified_count_value_regions']
    if report.get('require_loop_invariants'):
        assert report.get('loop_invariants_qualified') is True
        native = json.loads((HERE / run / 'native.report.json').read_text())
        assert native['native_guarded_call_regions'] == 7
    if report.get('require_cfg_cleanup'):
        assert report.get('cfg_cleanup_qualified') is True
        assert report['compiled_cfg_cleanup']['enabled'] is True
        assert report.get('cfg_cleanup_removed_total', report['compiled_cfg_cleanup']['constant_branches_removed']) > 0
    if report.get('require_guarded_loops'):
        assert report.get('source_guarded_loops_qualified') is True and report.get('source_tag_threading_qualified') is True
        assert report['compiled_guarded_loops']['complete'] is True
        native = json.loads((HERE / run / 'native.report.json').read_text())
        assert native['native_guarded_loop_regions'] == native['native_packed_ssa_regions'] == native['native_packed_map_regions'] == 7
        assert native['native_packed_map_updates'] == report['expected_table_updates']
    if report.get('require_frozen_maps'):
        assert report.get('source_frozen_maps_qualified') is True
        native = json.loads((HERE / run / 'native.report.json').read_text())
        assert native['native_frozen_map_regions'] == 5 and native['native_frozen_map_reads'] == 10
    labels = [sample['label'] for sample in report['samples']]
    assert len(labels) == len(set(labels)) and set(labels) == set(s['label'] for s in first['samples'])
    for sample in report['samples']:
        label = sample['label']
        process = json.loads((HERE / run / label / 'process.json').read_text())
        assert process['exit_status'] == 0 and process['reaped'] and process['group_closed']
        assert not process['cleanup_errors'] and process['quantitative_benchmark']
        assert sample['seconds'] == process['elapsed_seconds']
        output = (HERE / run / label / 'stdout.bin').read_bytes()
        assert hashlib.sha256(output).hexdigest() == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
        samples.setdefault(label, []).append(sample['seconds'])
    path = HERE / run / 'results.json'
    receipts.append({'path': str(path.relative_to(HERE)),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'order': labels})
medians = {label: statistics.median(values) for label, values in samples.items()}
summary = {key: first.get(key) for key in identity}
summary.update(status='all-cohorts-and-outputs-verified', cohort_count=len(reports),
               scope='Fresh complete processes, including secured startup/shutdown; no excluded warmups or outliers; cohorts run serially in their recorded orders',
               evidence=receipts, samples_seconds=samples, median_seconds=medians,
               stdev_seconds={label: statistics.stdev(values) for label, values in samples.items()},
               x_rust={label: value / medians['rust'] for label, value in medians.items()},
               speedup_over_parent=medians['baseline'] / medians['mech'] if 'baseline' in medians else None)
out = HERE / args.receipt
out.mkdir(exist_ok=False)
(out / 'results.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
