#!/usr/bin/env python3
"""Pure, evidence-bound correction of the historical Mech interpreted chart rows.

The retained report's ``samples_seconds`` and ``sample_details[].seconds`` are
loaded-interpreter measurements. Its independently measured ``wall_seconds``
span process launch through child exit. No elapsed time is reconstructed by
adding phases, and no historical report, sample detail, or audit is rewritten.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import statistics

LANGUAGE = 'mech-resident'
REPORT = 'interpreter-integration/20261011/timings.json'
ARCHIVE_REPORT = 'archive/compiler/interpreter-integration/20261011/timings.json'
REPORT_SHA256 = '88aa48fc3dc53d57347819602026788d3ee8c5144680da4e927d1e7a62913820'
# A dict API cannot verify the original whitespace. Bind its entire decoded
# content as well; load_retained_report separately verifies the original bytes.
REPORT_CONTENT_SHA256 = '80c7d48cf4ecbbc8a1cf7f93e1160e246c6f95d44fcb3a98f881aae84f123884'
BASELINE_SHA256 = 'a6ca47c7be028d86dd9f7e78ba36afda6afeaeb83f1a711b83441dbd5ff79437'
BINARY_SHA256 = 'aa335bc1d8c2c103cc0d6581be3cbc021111f1d26b695c371e0bf8422fba84d4'
SELECTED_SAMPLE_FIELD = 'sample_details[].wall_seconds'
CORRECTION_FIELD = 'mech_timing_boundary_correction'
WORKLOADS = {'nbody': [1000, 50000000], 'mandelbrot': [200, 16000],
             'knucleotide': [1000, 25000000], 'spectralnorm': [100, 5500],
             'revcomp': [1000, 25000000], 'fannkuchredux': [7, 12],
             'fasta': [1000, 25000000], 'binarytrees': [10, 21],
             'regexredux': [30, 5000000], 'pidigits': [30, 10000]}
TIMING_BOUNDARY = (
    'Full-process wall time measured before process launch through child exit. '
    'Includes runtime startup, source loading, parsing, graph preparation and '
    'activation, input, interpreted execution, output and flush, and shutdown. '
    'Input/reference preparation and post-exit output validation are outside '
    'the timer. Each sample starts a fresh process; no phase subtraction.')
TIMING_SUMMARY = 'Full process: startup, source preparation, execution, input/output and shutdown included.'
RUNTIME_POLICY = 'Mech typed interpreter · full-process wall time'
BOUNDARY_EVIDENCE = {
    'sampler': 'archive/compiler/execution-modes/20261010-final/run.py',
    'sampler_function': 'execute',
    'process_guard': 'archive/comparisons/compact/run.py',
    'process_guard_function': 'run_process',
    'cohort_producer': 'archive/compiler/interpreter-integration/20261011/run.py',
    'clock': 'time.perf_counter_ns',
    'start': 'Immediately before guard.run_process',
    'stop': 'Immediately after guard.run_process returns following child wait',
    'scope': 'Retained source inspection; not a new claim of execution-time helper pinning',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, label):
    require(actual == expected, f'{label} differs from the retained evidence')


def finite(value, label, positive=True):
    require(type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), f'Invalid {label}')


def load_retained_report(root):
    """Read only the small historical JSON and verify its exact original bytes."""
    raw = (Path(root) / ARCHIVE_REPORT).read_bytes()
    same(hashlib.sha256(raw).hexdigest(), REPORT_SHA256, 'Retained report SHA256')
    report = json.loads(raw)
    _validate_report(report)
    return report


def _validate_report(report):
    require(isinstance(report, dict), 'Retained report must be a decoded JSON object')
    try:
        content = json.dumps(report, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as error:
        raise ValueError('Retained report is not finite JSON') from error
    same(hashlib.sha256(content).hexdigest(), REPORT_CONTENT_SHA256, 'Retained report content')
    same(report['status'], 'complete', 'Report completion')
    same(report['sample_count'], 3, 'Report sample count')
    same(report['baseline_sha256'], BASELINE_SHA256, 'Report baseline identity')
    same(report['workloads'], WORKLOADS, 'Full workloads')
    same(report['discarded'], [], 'Discarded samples')
    same(set(report['completed_benchmarks']), set(WORKLOADS), 'Completed workloads')
    require(len(report['programs']) == 30, 'Expected 15 before and 15 after forms')
    rows = {}
    for key, row in report['programs'].items():
        if row['phase'] != 'after':
            continue
        source_key = row['source_key']
        same(key, source_key + ':after', 'Report key')
        same(row['key'], key, 'Internal report key')
        same(row['language'], LANGUAGE, key + ' language')
        same(row['mode'], 'resident', key + ' execution mode')
        same(row['binary_sha256'], BINARY_SHA256, key + ' executable identity')
        require(row['benchmark'] in WORKLOADS and source_key.startswith(row['benchmark'] + ':'),
                'Report source/workload identity mismatch')
        before = report['programs'][source_key + ':before']
        for field in ('source_key', 'benchmark', 'source', 'source_sha256', 'loc',
                      'physical_loc', 'loc_expansions', 'runtime_environment'):
            same(before[field], row[field], key + ' matched ' + field)
        samples, details, validations = row['samples_seconds'], row['sample_details'], row['sample_validation']
        require(len(samples) == len(details) == len(validations) == 3, key + ': missing sample detail or validation')
        wall = []
        for index, (sample, detail, validation) in enumerate(zip(samples, details, validations)):
            finite(sample, key + ' kernel sample')
            for field in ('seconds', 'kernel_seconds', 'wall_seconds', 'prepare_seconds'):
                finite(detail.get(field), key + ' ' + field, positive=field != 'prepare_seconds')
            same(detail['seconds'], sample, key + ' saved selected sample')
            same(detail['kernel_seconds'], sample, key + ' saved kernel sample')
            require(detail['wall_seconds'] >= sample, key + ': wall time is shorter than kernel time')
            require(validation['reference_match'] is True and validation['bytes'] > 0
                    and len(validation['sha256']) == 64, key + ': output validation failed')
            wall.append(detail['wall_seconds'])
        same(row['median_seconds'], statistics.median(samples), key + ' kernel median')
        same(row['sample_stdev_seconds'], statistics.stdev(samples), key + ' kernel SD')
        require(row['full_validation']['reference_match'] is True, key + ': full-work output failed')
        require(row['command'][0] == row['binary'] and row['command'][1] == row['source']
                and row['command'][2] == 'resident', key + ': command identity mismatch')
        rows[source_key + ':resident'] = {'row': row, 'samples': wall,
                                         'seconds': statistics.median(wall),
                                         'timing_sd': statistics.stdev(wall)}
    require(len(rows) == 15, 'Expected all 15 retained after forms')
    for benchmark in WORKLOADS:
        expected = {key for key, row in report['programs'].items() if row['benchmark'] == benchmark}
        orders = report['orders'][benchmark]
        require(len(orders) == 3 and all(len(order) == len(expected) and set(order) == expected for order in orders),
                benchmark + ': incomplete matched cohort orders')
    return rows


def _endpoints(rows, benchmark, wall=True):
    candidates = [(key, entry) for key, entry in rows.items() if entry['row']['benchmark'] == benchmark]
    elapsed = lambda entry: entry['seconds'] if wall else entry['row']['median_seconds']
    fast = min(candidates, key=lambda item: (elapsed(item[1]), item[1]['row']['loc'], item[0]))[0]
    small = min(candidates, key=lambda item: (item[1]['row']['loc'], elapsed(item[1]), item[0]))[0]
    return {'fast': fast, 'small': small, 'programs': list(dict.fromkeys((fast, small)))}


def _validate_source(data, row):
    source = data['files'].get(row['source_sha256'])
    require(isinstance(source, dict), row['key'] + ': source missing from dataset')
    same(source['sha256'], row['source_sha256'], row['key'] + ' source identity')
    same(hashlib.sha256(source['code'].encode('utf-8')).hexdigest(), row['source_sha256'],
         row['key'] + ' source bytes')


def _validate_program(program, row, benchmark):
    key = row['source_key'] + ':resident'
    expected = {
        'key': key, 'id': row['source_key'].split(':', 1)[1] + ':resident',
        'benchmark': row['benchmark'], 'language': LANGUAGE, 'loc': row['loc'],
        'physical_loc': row['physical_loc'], 'loc_expansions': row['loc_expansions'],
        'files': [row['source_sha256']], 'report': REPORT,
        'source_report': 'interpreter-integration/20261011/baseline.json',
        'measurement_status': 'measured', 'required_work_validated': True,
        'execution_mode': 'interpreted', 'sample_details': row['sample_details'],
        'samples': row['samples_seconds'], 'seconds': row['median_seconds'],
        'timing_sd': row['sample_stdev_seconds'], 'timing_boundary': row['timing_boundary'],
        'binary_sha256': row['binary_sha256'], 'compiler_sha256': row['binary_sha256'],
        'binary': row['binary'], 'runtime_arguments': row['command'],
        'runtime_environment': row['runtime_environment'],
        'full_output_validation': row['sample_validation'], 'full_validation': row['full_validation'],
        'measurement_cohort': 'interpreter-integration/20261011', 'measurement_phase': 'after',
        'x': row['loc'] / benchmark['baseline_loc'],
        'y': row['median_seconds'] / benchmark['baseline_seconds'],
    }
    for field, value in expected.items():
        same(program.get(field), value, key + '.' + field)
    require('timing_measurement' not in program and 'timing_correction' not in program,
            'Timing correction is already present or conflicts with another measurement')
    backend = program['measured_backend']
    same(backend['key'], 'native-interpreter', key + ' backend')
    same(backend['execution'], 'interpreted', key + ' backend execution')
    evidence = backend['evidence']
    for field, value in {'report': REPORT, 'report_sha256': REPORT_SHA256,
                         'source_sha256': [row['source_sha256']], 'command': row['command'],
                         'measurement_selector': '/programs/' + row['key'],
                         'actual_sample_array': row['samples_seconds'],
                         'original_timing_boundary': row['timing_boundary']}.items():
        same(evidence.get(field), value, key + ' backend ' + field)
    require('original_audit_timing_selection' not in evidence and 'selected_sample_field' not in evidence,
            key + ': backend timing selection already changed')


def _correct_program(program, entry, benchmark):
    row = entry['row']
    selector = '/programs/' + row['key']
    original = {field: deepcopy(program[field]) for field in (
        'samples', 'seconds', 'timing_sd', 'y', 'timing_boundary', 'timing_summary', 'runtime_policy')}
    program.update(samples=deepcopy(entry['samples']), seconds=entry['seconds'],
                   timing_sd=entry['timing_sd'], y=entry['seconds'] / benchmark['baseline_seconds'],
                   timing_boundary=TIMING_BOUNDARY, timing_summary=TIMING_SUMMARY,
                   runtime_policy=RUNTIME_POLICY)
    program['timing_measurement'] = {
        'kind': 'full-process-wall', 'selected_sample_field': SELECTED_SAMPLE_FIELD,
        'report': REPORT, 'report_sha256': REPORT_SHA256, 'measurement_selector': selector,
        'sample_selectors': [selector + f'/sample_details/{index}/wall_seconds' for index in range(3)],
        'sample_count': 3, 'phase_sum_used': False, 'samples_discarded': 0,
        'boundary_evidence': deepcopy(BOUNDARY_EVIDENCE),
    }
    program['timing_correction'] = {
        'schema': 'mech-interpreted-full-process-v1',
        'reason': 'Use the already recorded full-process wall samples for the default comparison.',
        'report': REPORT, 'report_sha256': REPORT_SHA256, 'measurement_selector': selector,
        'original_kernel_samples_seconds': deepcopy(row['samples_seconds']),
        'original_display': original, 'historical_reports_changed': False,
        'sample_details_changed': False, 'new_native_processes': 0,
    }
    backend = program['measured_backend']
    evidence = backend['evidence']
    evidence['original_audit_timing_selection'] = {
        'actual_sample_array': deepcopy(evidence['actual_sample_array']),
        'original_timing_boundary': evidence['original_timing_boundary'],
        'selected_sample_field': 'samples_seconds', 'backend_label': backend['label'],
        'scope': 'Original audit selection preserved; historical verification is not reinterpreted as wall-time verification.',
    }
    backend['label'] = RUNTIME_POLICY
    evidence['actual_sample_array'] = deepcopy(entry['samples'])
    evidence['selected_sample_field'] = SELECTED_SAMPLE_FIELD
    evidence['timing_selection_verification'] = {
        'scope': 'Exact field selection from the same retained report; historical backend confidence and limitations unchanged.',
        'report_sha256': REPORT_SHA256, 'measurement_selector': selector,
        'sample_selectors': deepcopy(program['timing_measurement']['sample_selectors']),
    }


def correct_dataset(current_data, retained_report):
    """Return ``(corrected_data, review)`` without modifying either input.

    This one-shot migration accepts only the original loaded-timing rows. It
    validates every retained after form, then selects endpoints using measured
    wall medians. An unexpected endpoint change fails rather than inventing a
    newly published profile from incomplete metadata.
    """
    rows = _validate_report(retained_report)
    require(CORRECTION_FIELD not in current_data, 'Dataset already has a timing correction')
    require(not any(p['language'] == LANGUAGE for p in current_data.get('program_inventory', {}).values()),
            'Unexpected interpreted inventory rows require separate review')
    audit = current_data['interpreter_integration_audit']
    for field, value in {'status': 'complete', 'sample_count': 3, 'sources': 15,
                         'report': REPORT, 'report_sha256': REPORT_SHA256,
                         'baseline_sha256': BASELINE_SHA256, 'selected_phase': 'after',
                         'selected_samples': 45, 'selected_programs': sorted(rows)}.items():
        same(audit.get(field), value, 'Integration audit ' + field)
    for entry in rows.values():
        _validate_source(current_data, entry['row'])
    benchmarks = {b['key']: b for b in current_data['benchmarks']}
    require(len(benchmarks) == len(current_data['benchmarks']) and set(WORKLOADS) <= set(benchmarks),
            'Missing or duplicate benchmark records')
    selected = {key for key, p in current_data['programs'].items() if p['language'] == LANGUAGE}
    same(len(selected), 14, 'Selected interpreted form count')
    same(audit['plotted_programs'], sorted(selected), 'Integration plotted forms')
    endpoint_selection = {b: _endpoints(rows, b) for b in WORKLOADS}
    same(selected, {key for item in endpoint_selection.values() for key in item['programs']},
         'Wall-time endpoint membership')
    for benchmark in WORKLOADS:
        b = benchmarks[benchmark]
        finite(b['baseline_seconds'], benchmark + ' baseline seconds')
        finite(b['baseline_loc'], benchmark + ' baseline LOC')
        groups = [g for g in b['groups'] if g['language'] == LANGUAGE]
        require(len(groups) == 1, benchmark + ': expected exactly one interpreted group')
        for field, value in _endpoints(rows, benchmark, wall=False).items():
            same(groups[0][field], value, benchmark + ' original endpoint ' + field)
    for key in selected:
        row = rows[key]['row']
        _validate_program(current_data['programs'][key], row, benchmarks[row['benchmark']])

    data = deepcopy(current_data)
    for key in sorted(selected):
        _correct_program(data['programs'][key], rows[key], benchmarks[rows[key]['row']['benchmark']])
    for benchmark in data['benchmarks']:
        if benchmark['key'] in endpoint_selection:
            group = next(g for g in benchmark['groups'] if g['language'] == LANGUAGE)
            group.update(deepcopy(endpoint_selection[benchmark['key']]))
    references = [r for r in data['reference_summary'] if r['lang'] == LANGUAGE]
    require(len(references) == 1, 'Expected one interpreted reference summary')
    for kind in ('fast', 'small'):
        selected_rows = [data['programs'][endpoint_selection[b][kind]] for b in WORKLOADS]
        # Endpoint membership and all source ratios are unchanged. Preserve the
        # historical x bit pattern instead of gratuitously recomputing it.
        references[0][kind]['y'] = statistics.geometric_mean(p['y'] for p in selected_rows)
    review = {
        'schema': 'mech-interpreted-full-process-v1', 'status': 'corrected',
        'language': LANGUAGE, 'report': REPORT, 'archive_report': ARCHIVE_REPORT,
        'report_sha256': REPORT_SHA256, 'report_content_sha256': REPORT_CONTENT_SHA256,
        'selected_sample_field': SELECTED_SAMPLE_FIELD, 'retained_forms_validated': 15,
        'retained_wall_samples_validated': 45, 'selected_forms': 14, 'selected_wall_samples': 42,
        'benchmarks': 10, 'new_native_processes': 0, 'samples_discarded': 0,
        'phase_sum_used': False, 'historical_reports_changed': False, 'baseline_changed': False,
        'boundary_evidence': deepcopy(BOUNDARY_EVIDENCE),
        'endpoint_selection': endpoint_selection,
        'forms': {key: {
            'report_selector': '/programs/' + entry['row']['key'],
            'source_sha256': entry['row']['source_sha256'],
            'original_kernel_samples_seconds': deepcopy(entry['row']['samples_seconds']),
            'wall_samples_seconds': deepcopy(entry['samples']),
            'wall_median_seconds': entry['seconds'], 'wall_sample_sd_seconds': entry['timing_sd'],
            'selected_for_chart': key in selected,
        } for key, entry in sorted(rows.items())},
    }
    data[CORRECTION_FIELD] = deepcopy(review)
    return data, review


def verify_correction(before_data, after_data, retained_report):
    """Require exact reproduction, including absence of unrelated mutations."""
    expected, review = correct_dataset(before_data, retained_report)
    same(after_data, expected, 'Corrected dataset')
    return review


def _preserve_fields(previous, current, label):
    require(isinstance(current, dict), 'Missing ' + label)
    for field, value in previous.items():
        require(field in current, 'Missing preserved field ' + label + '.' + field)
        same(current.get(field), value, label + '.' + field)


def verify_previous_correction(previous_data, current_data, retained_report):
    """Validate the narrow exception to archived row preservation.

    Returns the 14 corrected program keys. All fields of every archived row,
    source and inventory record must match the reproduced correction. Later
    additive rows/fields are permitted, matching check_previous's policy.
    Original baseline values, groups, reference entries, and integration audit
    are also preserved except for the reproduced interpreted endpoints/times.
    """
    expected, review = correct_dataset(previous_data, retained_report)
    same(current_data.get(CORRECTION_FIELD), review, 'Timing correction review')
    for section in ('programs', 'program_inventory', 'files'):
        for key, row in expected.get(section, {}).items():
            _preserve_fields(row, current_data.get(section, {}).get(key), section + '.' + key)
    current_benchmarks = {b['key']: b for b in current_data['benchmarks']}
    require(len(current_benchmarks) == len(current_data['benchmarks']), 'Duplicate current benchmarks')
    for old in expected['benchmarks']:
        current = current_benchmarks.get(old['key'])
        require(current is not None, 'Missing original benchmark ' + old['key'])
        for field, value in old.items():
            if field.startswith('baseline_'):
                same(current.get(field), value, old['key'] + '.' + field)
        for old_group in old['groups']:
            matches = [g for g in current['groups'] if g['language'] == old_group['language']]
            require(len(matches) == 1, 'Missing or duplicate original group')
            _preserve_fields(old_group, matches[0], old['key'] + '.' + old_group['language'])
    for old in expected['reference_summary']:
        matches = [r for r in current_data['reference_summary'] if r['lang'] == old['lang']]
        require(len(matches) == 1, 'Missing or duplicate original reference summary')
        _preserve_fields(old, matches[0], 'reference_summary.' + old['lang'])
    same(current_data['interpreter_integration_audit'], previous_data['interpreter_integration_audit'],
         'Historical integration audit')
    return {key for key, p in expected['programs'].items() if p['language'] == LANGUAGE}
