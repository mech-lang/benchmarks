"""Publish a complete fresh Mech interpreted process-timing cohort, purely.

Only decoded data is transformed. Historical records remain nested verbatim;
no source, benchmark baseline, AOT/JIT row or non-Mech row is rewritten.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import statistics
import types

ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = 'mech-resident'
FIELD = 'mech_interpreted_rerun'
REPORT = 'experiments/mech/interpreted-whole-process-v1/run-v1/report.json'
OLD_REPORT = 'interpreter-integration/20261011/timings.json'
OLD_PATH = 'archive/compiler/interpreter-integration/20261011/timings.json'
OLD_SHA = '88aa48fc3dc53d57347819602026788d3ee8c5144680da4e927d1e7a62913820'
BINARY_SHA = 'aa335bc1d8c2c103cc0d6581be3cbc021111f1d26b695c371e0bf8422fba84d4'
FULL = dict(nbody=50000000, mandelbrot=16000, knucleotide=25000000,
            spectralnorm=5500, revcomp=25000000, fannkuchredux=12,
            fasta=25000000, binarytrees=21, regexredux=5000000, pidigits=10000)
SUMMARY = 'Full process: startup, source preparation, execution, input/output and shutdown included.'
POLICY = 'Mech typed interpreter · full-process wall time'
CONTROLLER_SHA = 'a523a2262848e351bd5a6a4f1b41e64ae0bb2c444fe1c2d4b5bf50c523a08cc2'
HELPER_SHA = '27e42b3f54b5cef9c17b8fea65b789b370b7eda714fdd27f575c7850c553001c'
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
PYTHON = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'


def require(value, message):
    if not value:
        raise ValueError(message)


def equal(actual, expected, message):
    require(actual == expected, message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def content_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode())


def report_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()


def finite(value, positive=True):
    require(type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), 'Invalid elapsed time')


def retained(root=ROOT):
    raw = (Path(root) / OLD_PATH).read_bytes()
    equal(digest(raw), OLD_SHA, 'Historical report bytes changed')
    report = json.loads(raw)
    rows = {r['source_key'] + ':resident': r for r in report['programs'].values()
            if r['phase'] == 'after'}
    require(len(rows) == 15 and {r['benchmark'] for r in rows.values()} == set(FULL),
            'Historical source cohort differs')
    return report, rows


def runner_plan(report):
    """Read definitions and construct the producer's pure static plan only."""
    path = ROOT / 'tools/rerun_mech_interpreted.py'
    raw = path.read_bytes()
    equal(digest(raw), CONTROLLER_SHA, 'Frozen fresh-run producer changed')
    recorded_root = Path(report['controller']).parents[1]
    equal(report['controller'], str(recorded_root/'tools/rerun_mech_interpreted.py'), 'Wrong measured controller')
    equal(report['output'], str(recorded_root/Path(REPORT).parent), 'Wrong measured output directory')
    equal(report.get('controller_sha256'), digest(raw), 'Measured controller source differs')
    module = types.ModuleType('interpreted_rerun_publication_definition_review')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    historical, _ = retained()
    expected = module.make_plan(historical, Path(report['output']))
    for field,value in expected.items():
        if field != 'programs':
            equal(report.get(field), value, 'Fresh plan differs: '+field)
    for key,row in expected['programs'].items():
        for field,value in row.items():
            equal(report['programs'][key].get(field), value, key+': static plan differs: '+field)
    pins = report['pins']
    equal(pins.get(report['controller']), digest(raw), 'Controller is not in measured pins')
    equal(pins.get(str(recorded_root / OLD_PATH)), OLD_SHA, 'Historical report is not in measured pins')
    required = {report['controller']:CONTROLLER_SHA,
                str(recorded_root/OLD_PATH):OLD_SHA,
                str(recorded_root/'tools/mech_timing_boundary.py'):HELPER_SHA,
                str(Path(report['output'])/'plan.json'):report['plan_sha256'], PYTHON:PYTHON_SHA}
    for row in expected['programs'].values():
        for kind in ('source','binary'):
            equal(pins.get(row[kind]), row[kind+'_sha256'], 'Missing measured '+kind+' pin')
            required[row[kind]] = row[kind+'_sha256']
        if row['stdin']:
            equal(pins.get(row['stdin']['path']), row['stdin']['sha256'], 'Missing full input pin')
            required[row['stdin']['path']] = row['stdin']['sha256']
    for path,value in required.items():
        equal(pins.get(path),value,'Missing prerequisite pin: '+path)
    equal(pins,required,'Measured prerequisite pin inventory differs')
    return expected


def endpoints(rows, benchmark):
    candidates = [r for r in rows.values() if r['benchmark'] == benchmark]
    fast = min(candidates, key=lambda r: (r['seconds'], r['loc'], r['key']))['key']
    small = min(candidates, key=lambda r: (r['loc'], r['seconds'], r['key']))['key']
    return dict(fast=fast, small=small, programs=list(dict.fromkeys((fast, small))))


def snapshots(data):
    return {section:{k:dict(fields=sorted(r),sha256=content_digest(r))
        for k,r in data.get(section,{}).items() if section=='files' or r['language']!=LANGUAGE}
        for section in ('programs','program_inventory','files')}


def validate_old(data, old):
    require(FIELD not in data and 'mech_timing_boundary_correction' not in data,
            'Dataset is already changed or uses the superseded historical-wall correction')
    require(not any(r['language'] == LANGUAGE for r in data.get('program_inventory', {}).values()),
            'Unexpected prior interpreted inventory')
    selected = {k:r for k,r in data['programs'].items() if r['language'] == LANGUAGE}
    require(len(selected) == 14 and set(selected) < set(old), 'Wrong original interpreted selection')
    for key, row in selected.items():
        prior = old[key]
        fields = dict(key=key, id=prior['source_key'].split(':', 1)[1] + ':resident',
            benchmark=prior['benchmark'], language=LANGUAGE, loc=prior['loc'],
            physical_loc=prior['physical_loc'], files=[prior['source_sha256']],
            samples=prior['samples_seconds'], seconds=prior['median_seconds'],
            timing_sd=prior['sample_stdev_seconds'], report=OLD_REPORT,
            binary_sha256=BINARY_SHA, sample_details=prior['sample_details'],
            full_output_validation=prior['sample_validation'], full_validation=prior['full_validation'])
        for field, value in fields.items():
            equal(row.get(field), value, 'Original interpreted field differs: '+key+'.'+field)
        require('timing_measurement' not in row and 'timing_correction' not in row,
                'Unexpected earlier timing replacement')
    for row in old.values():
        source = data['files'][row['source_sha256']]
        equal(source['sha256'], row['source_sha256'], 'Source identity differs')
        equal(digest(source['code'].encode()), row['source_sha256'], 'Source bytes differ')
    audit = data['interpreter_integration_audit']
    equal(audit['report_sha256'], OLD_SHA, 'Original integration audit differs')
    equal(audit['plotted_programs'], sorted(selected), 'Original plotted forms differ')
    return selected


def validate_report(report, old):
    require(type(report) is dict, 'Missing fresh report')
    content_digest(report)  # Reject nonfinite JSON anywhere, including diagnostics.
    equal(report.get('status'), 'complete', 'Fresh run is incomplete or failed')
    for key, value in dict(sample_count=3, completed_samples=45, native_processes=45,
                           timing_measurement='full-process-wall').items():
        require(type(report.get(key)) is type(value) and report[key] == value,
                'Fresh run policy differs: '+key)
    require(isinstance(report.get('timing_boundary'), str) and report['timing_boundary'],
            'Missing actual timer boundary')
    equal(report.get('retained_report_sha256'), OLD_SHA, 'Wrong retained source cohort')
    equal(report.get('retained_report'), OLD_REPORT, 'Wrong retained report path')
    require(report.get('active') is None and report.get('active_run') is None and not report.get('error')
            and not report.get('discarded') and not report.get('integrity_errors'),
            'Unclosed or discarded fresh work')
    equal(set(report['programs']), set(old), 'All 15 fresh forms are required')
    plan = runner_plan(report)
    require(len(report['attempts']) == 45, 'Missing native receipts')
    receipts = {}
    for slot,attempt in zip(plan['schedule'], report['attempts']):
        equal({k:attempt.get(k) for k in slot}, slot, 'Missing, repeated or reordered native slot')
        require(attempt.get('qualified') is True, 'Unqualified native attempt')
        expected_path = str(Path(report['output']) / 'samples' / f"{slot['ordinal']:03d}" / 'process.json')
        equal(attempt.get('receipt'), expected_path, 'Native receipt path differs')
        receipts.setdefault(slot['key'], []).append(expected_path)
    expected_artifacts = {'plan.json'} | {
        f'samples/{i:03d}/{name}' for i in range(1,46)
        for name in ('stdout.bin','stderr.txt','process.json')}
    equal(set(report['artifacts']), expected_artifacts, 'Missing or extra sample artifact')
    for metadata in report['artifacts'].values():
        require(set(metadata) == {'sha256','bytes'} and type(metadata['bytes']) is int
                and metadata['bytes'] >= 0 and isinstance(metadata['sha256'],str)
                and len(metadata['sha256']) == 64
                and all(c in '0123456789abcdef' for c in metadata['sha256']), 'Invalid artifact identity')
    equal(report['plan_sha256'], report['artifacts']['plan.json']['sha256'], 'Plan artifact linkage differs')
    equal(report['pins'].get(str(Path(report['output'])/'plan.json')), report['plan_sha256'], 'Missing closed plan pin')
    for key, row in report['programs'].items():
        prior = old[key]
        for field in ('source_key','benchmark','source','source_sha256','binary','binary_sha256',
                      'loc','physical_loc'):
            equal(row.get(field), prior[field], key+': changed '+field)
        command = [part.replace('{n}', str(FULL[prior['benchmark']])) for part in prior['command']]
        equal(row['command'], command, key+': full invocation changed')
        samples, details, validations = row['samples_seconds'], row['sample_details'], row['sample_validation']
        equal(row['sample_receipts'], receipts[key], 'Sample/attempt receipt routing differs')
        require(type(samples) is list and len(samples) == len(details) == len(validations) == 3,
                key+': missing sample, detail or validation')
        for sample, detail, validation in zip(samples, details, validations):
            finite(sample)
            equal(detail.get('seconds'), sample, key+': sample is not the recorded external duration')
            equal(detail.get('wall_seconds'), sample, key+': phase subtraction or kernel-only selection')
            require(validation.get('reference_match') is True, key+': output failed')
            for field in ('bytes','sha256'):
                equal(validation.get(field), prior['full_validation'][field], key+': full output differs')
            for field in ('kernel_seconds','prepare_seconds'):
                if detail.get(field) is not None:
                    finite(detail[field], positive=False)
        equal(row['median_seconds'], statistics.median(samples), key+': median differs')
        equal(row['sample_stdev_seconds'], statistics.stdev(samples), key+': SD differs')
        equal(row['full_validation'], validations[-1], key+': full validation is not last actual sample')
    return report['programs']


def make_program(data, previous, row, old, bench, report, relative):
    key = row['source_key'] + ':resident'
    if previous is None:
        aot = {**data.get('program_inventory', {}), **data['programs']}.get(row['source_key'])
        require(aot is not None and aot['files'] == [row['source_sha256']], 'Missing exact source metadata')
        result = {field:deepcopy(aot[field]) for field in ('algorithm','source_url','source_provenance',
            'formatted_loc','formatted_loc_status','formatted_loc_complete','formatted_loc_evidence','formatted_x')
            if field in aot}
        result.update(key=key, id=row['source_key'].split(':',1)[1]+':resident', language=LANGUAGE,
            benchmark=row['benchmark'], files=[row['source_sha256']], loc=row['loc'],
            physical_loc=row['physical_loc'], loc_expansions=deepcopy(old['loc_expansions']),
            source_report='interpreter-integration/20261011/baseline.json', required_work_validated=True,
            historical_execution_record=dict(report=OLD_REPORT, report_sha256=OLD_SHA, record=deepcopy(old)))
    else:
        result = deepcopy(previous)
        result['previous_measurement'] = deepcopy(previous)
    selector = '/programs/' + key
    evidence = dict(verified=True, report=relative, report_sha256=digest(report_bytes(report)),
        report_content_sha256=content_digest(report),
        source_sha256=[row['source_sha256']], command=deepcopy(row['command']),
        measurement_selector=selector, actual_sample_array=deepcopy(row['samples_seconds']),
        selected_sample_field='samples_seconds', original_timing_boundary=report['timing_boundary'],
        source_receipt=dict(report=relative, report_sha256=digest(report_bytes(report)),
                            field=selector, source_sha256=row['source_sha256']),
        command_role='fresh-timed-argv', historical_command_template=False,
        executable=dict(path=row['binary'], sha256=row['binary_sha256']),
        scope='Fresh process timing of the same retained interpreter executable and audited source.')
    result.update(samples=deepcopy(row['samples_seconds']), seconds=row['median_seconds'],
        timing_sd=row['sample_stdev_seconds'], sample_details=deepcopy(row['sample_details']),
        full_output_validation=deepcopy(row['sample_validation']), full_validation=deepcopy(row['full_validation']),
        report=relative, binary=row['binary'], binary_sha256=row['binary_sha256'],
        compiler_sha256=row['binary_sha256'], runtime_arguments=deepcopy(row['command']),
        runtime_environment=deepcopy(row['runtime_environment']), execution_mode='interpreted',
        environment_scope=report['environment_policy'],
        timing_boundary=report['timing_boundary'], timing_summary=SUMMARY, runtime_policy=POLICY,
        measurement_status='measured', measurement_cohort=str(Path(relative).parent), measurement_phase='fresh',
        x=row['loc']/bench['baseline_loc'], y=row['median_seconds']/bench['baseline_seconds'],
        timing_measurement=dict(kind='full-process-wall', report=relative,
            report_sha256=digest(report_bytes(report)), report_content_sha256=content_digest(report), measurement_selector=selector,
            selected_sample_field='samples_seconds', sample_count=3, phase_sum_used=False,
            samples_discarded=0, new_native_processes=3),
        measured_backend=dict(key='native-interpreter', execution='interpreted', label=POLICY,
            verified=True, evidence=evidence))
    if previous is not None:
        result['measured_backend']['prior_audit'] = deepcopy(previous['measured_backend'])
    return result


def import_dataset(data, new_report, reportrelative=REPORT):
    """Return a new dataset and review; no files or inputs are modified."""
    equal(reportrelative, REPORT, 'Unexpected publication report location')
    _, old = retained()
    previous = validate_old(data, old)
    fresh = validate_report(new_report, old)
    output = deepcopy(data)
    benches = {b['key']:b for b in output['benchmarks']}
    require(set(FULL) <= set(benches) and len(benches) == len(output['benchmarks']), 'Invalid workloads')
    for b in benches.values():
        finite(b['baseline_loc']); finite(b['baseline_seconds'])
    forms = {key:make_program(data, previous.get(key), row, old[key], benches[row['benchmark']],
                              new_report, reportrelative) for key,row in fresh.items()}
    chosen = {b:endpoints(forms,b) for b in FULL}
    selected = {key for e in chosen.values() for key in e['programs']}
    output['programs'] = {k:r for k,r in output['programs'].items() if r['language'] != LANGUAGE}
    output['programs'].update({k:deepcopy(forms[k]) for k in sorted(selected)})
    output.setdefault('program_inventory', {}).update(deepcopy(forms))
    mapping = output.setdefault('archive_paths',{})
    require(REPORT not in mapping or mapping[REPORT]==REPORT, 'Conflicting fresh report archive path')
    mapping[REPORT] = REPORT
    for b in FULL:
        groups = [g for g in benches[b]['groups'] if g['language'] == LANGUAGE]
        require(len(groups) == 1, 'Missing or duplicate interpreted group')
        groups[0].update(deepcopy(chosen[b]))
    summaries = [r for r in output['reference_summary'] if r['lang'] == LANGUAGE]
    require(len(summaries) == 1, 'Missing or duplicate interpreted summary')
    for mode in ('fast','small'):
        candidates = [forms[chosen[b][mode]] for b in FULL]
        summaries[0][mode] = dict(x=statistics.geometric_mean(r['x'] for r in candidates),
                                  y=statistics.geometric_mean(r['y'] for r in candidates))
    review = dict(schema='mech-interpreted-fresh-process-publication-v1', status='imported',
        report=reportrelative, report_sha256=digest(report_bytes(new_report)), report_content_sha256=content_digest(new_report),
        retained_report=OLD_PATH, retained_report_sha256=OLD_SHA, source_forms=15,
        fresh_samples=45, native_processes=45, samples_discarded=0, phase_sum_used=False,
        previous_program_keys=sorted(previous), selected_program_keys=sorted(selected),
        preserved_sections=snapshots(data),
        preserved_context={section:deepcopy(data.get(section,[])) for section in
            ('benchmarks','reference_summary','formatted_reference_summary')},
        historical_integration_audit_sha256=content_digest(data['interpreter_integration_audit']),
        endpoints=chosen, other_programs_changed=False, benchmark_baselines_changed=False,
        historical_integration_audit_changed=False)
    output[FIELD] = deepcopy(review)
    return output, review


def preserve(previous, current, label):
    require(isinstance(current, dict), 'Missing preserved '+label)
    for field,value in previous.items():
        require(field in current, 'Missing preserved '+label+'.'+field)
        equal(current.get(field), value, 'Changed preserved '+label+'.'+field)


def verify_receipts(root, report, raw):
    """Check retained small receipts and producer closure, without runtime scans.

    Large stdout is represented by its complete-output validation and terminal
    artifact digest. Its bytes need not be distributed with the public catalog.
    """
    directory = Path(root) / Path(REPORT).parent
    terminal = json.loads((directory/'terminal.json').read_bytes())
    for field,value in dict(status='complete', report_sha256=digest(raw), completed_samples=45,
            native_processes=45, integrity_errors=[], common_mutex_inode=79859134,
            common_mutex_held=True, artifacts=report['artifacts']).items():
        require(type(terminal.get(field)) is type(value), 'Invalid terminal field type')
        equal(terminal[field], value, 'Terminal closure differs: '+field)
    def artifact(relative):
        content = (directory/relative).read_bytes()
        equal(dict(sha256=digest(content), bytes=len(content)), report['artifacts'][relative],
              'Changed saved artifact: '+relative)
        return json.loads(content)
    plan = artifact('plan.json')
    expected = runner_plan(report)
    equal(plan, dict(expected, pins={k:v for k,v in report['pins'].items()
                                   if k != str(Path(report['output'])/'plan.json')}), 'Closed plan differs')
    positions = {k:0 for k in report['programs']}
    previous_stop = 0
    for attempt in report['attempts']:
        ordinal, key = attempt['ordinal'], attempt['key']
        relative = f'samples/{ordinal:03d}/process.json'
        receipt = artifact(relative)
        row = report['programs'][key]; index = positions[key]; positions[key] += 1
        for field,value in dict(status='passed', qualified=True, native_process_started=True,
                exit_code=0, command=row['command'], cwd=row['cwd'], environment=row['runtime_environment'],
                stdin=row['stdin'], common_mutex_inode=79859134, native_inherits_common_mutex=True,
                timing_measurement='full-process-wall', sample_details=row['sample_details'][index],
                validation=row['sample_validation'][index], seconds=row['samples_seconds'][index],
                wall_seconds=row['samples_seconds'][index], monitor_errors=[]).items():
            require(type(receipt.get(field)) is type(value), 'Invalid process receipt field type: '+field)
            equal(receipt[field], value, 'Process receipt differs: '+field)
        require(not receipt.get('error') and not receipt.get('cleanup_error'), 'Failed process cleanup')
        require(type(receipt['pid']) is int and receipt['pid'] > 0
                and receipt['process_group_id'] == receipt['pid'], 'Invalid owned native group')
        start,stop = receipt['clock_start_ns'], receipt['clock_stop_ns']
        require(type(start) is int and type(stop) is int and 0 < start < stop, 'Invalid external clock')
        require(previous_stop <= start, 'Native timing intervals overlap or are reordered')
        previous_stop = stop
        equal(receipt['seconds'], (stop-start)/1e9, 'Selected sample is not external clock duration')
        require(receipt['monitor_observations'] and all(
            v['power'] == {'source':'AC Power','low_power_mode':0} and not v['competing_compilers']
            for v in receipt['monitor_observations']), 'Unqualified power/compiler observations')
        for stream,name in (('stdout','stdout.bin'),('stderr','stderr.txt')):
            equal(receipt[stream], str(Path(report['output'])/'samples'/f'{ordinal:03d}'/name),
                  'Output artifact routing differs')
        equal(report['artifacts'][f'samples/{ordinal:03d}/stdout.bin'],
              {k:receipt['validation'][k] for k in ('sha256','bytes')}, 'Validated stdout pin differs')
        equal(report['artifacts'][f'samples/{ordinal:03d}/stderr.txt'],
              dict(sha256=receipt['stderr_sha256'], bytes=receipt['stderr_bytes']), 'Diagnostic pin differs')


def verify_saved_publication(root, data, previous):
    """Verify the narrow historical-row exception; return its 14 legacy keys."""
    root = Path(root)
    review = data[FIELD]
    equal(review['report'], REPORT, 'Publication report location changed')
    raw = (root / REPORT).read_bytes()
    fresh = json.loads(raw)
    equal(digest(raw), review['report_sha256'], 'Saved report bytes changed')
    equal(raw, report_bytes(fresh), 'Unexpected report serialization')
    equal(content_digest(fresh), review['report_content_sha256'], 'Saved fresh report changed')
    retained(root)
    # The older public snapshot predates later additive source/runtime metadata.
    # Reconstruct the immediate input from the verbatim prior records, then
    # independently enforce every field of the older public snapshot below.
    before = deepcopy(data)
    before.pop(FIELD)
    for section,records in review['preserved_sections'].items():
        before[section] = {}
        for key,record in records.items():
            current = data[section][key]
            require(all(field in current for field in record['fields']), 'Missing preserved current field')
            prior = {field:deepcopy(current[field]) for field in record['fields']}
            equal(content_digest(prior),record['sha256'],'Changed unaffected current record: '+key)
            before[section][key] = prior
    for section,value in review['preserved_context'].items():
        before[section] = deepcopy(value)
    corrected = set(review['previous_program_keys'])
    legacy_keys = {k for k,r in previous['programs'].items() if r['language'] == LANGUAGE}
    equal(corrected,legacy_keys,'Legacy interpreted key set changed')
    for key in corrected:
        prior = data['program_inventory'][key]['previous_measurement']
        preserve(previous['programs'][key],prior,'previous_measurement.'+key)
        before['programs'][key] = deepcopy(prior)
    expected, expected_review = import_dataset(before, fresh, REPORT)
    equal(review, expected_review, 'Publication review differs')
    verify_receipts(root, fresh, raw)
    for section in ('programs','program_inventory','files'):
        for key,row in previous.get(section,{}).items():
            if section=='programs' and key in corrected:
                continue
            preserve(row,data.get(section,{}).get(key),section+'.'+key)
    for section in ('programs','program_inventory','files'):
        for key,row in expected.get(section, {}).items():
            preserve(row, data.get(section, {}).get(key), section+'.'+key)
    current_selected = {k for k,r in data['programs'].items() if r['language'] == LANGUAGE}
    equal(current_selected, set(review['selected_program_keys']), 'Interpreted endpoints differ')
    equal({k for k,r in data['program_inventory'].items() if r['language'] == LANGUAGE},
          set(fresh['programs']), 'Interpreted inventory differs')
    for key in fresh['programs']:
        equal(data['program_inventory'][key], expected['program_inventory'][key], 'Fresh inventory record differs')
        if key in current_selected:
            equal(data['programs'][key], data['program_inventory'][key], 'Catalog copies conflict')
    current_benches = {b['key']:b for b in data['benchmarks']}
    require(len(current_benches) == len(data['benchmarks']), 'Duplicate workload')
    for b in expected['benchmarks']:
        actual = current_benches[b['key']]
        for field,value in b.items():
            if field.startswith('baseline_'):
                equal(actual.get(field), value, 'Changed fixed baseline')
        for group in b['groups']:
            matches = [g for g in actual['groups'] if g['language'] == group['language']]
            require(len(matches) == 1, 'Missing or duplicate language group')
            preserve(group, matches[0], 'workload group')
    for b in previous['benchmarks']:
        actual = current_benches[b['key']]
        for field,value in b.items():
            if field.startswith('baseline_'):
                equal(actual.get(field),value,'Historical baseline changed')
        for group in b['groups']:
            matches=[g for g in actual['groups'] if g['language']==group['language']]
            require(len(matches)==1,'Missing historical group')
            preserve({k:v for k,v in group.items() if group['language']!=LANGUAGE
                      or k not in ('fast','small','programs')},matches[0],'historical group')
    for r in expected['reference_summary']:
        matches = [s for s in data['reference_summary'] if s['lang'] == r['lang']]
        require(len(matches) == 1, 'Missing or duplicate reference summary')
        preserve(r, matches[0], 'reference summary')
    for r in previous['reference_summary']:
        matches=[s for s in data['reference_summary'] if s['lang']==r['lang']]
        require(len(matches)==1,'Missing historical summary')
        preserve({k:v for k,v in r.items() if r['lang']!=LANGUAGE or k not in ('fast','small')},
                 matches[0],'historical summary')
    for r in previous.get('formatted_reference_summary', []):
        matches = [s for s in data.get('formatted_reference_summary', []) if s['lang'] == r['lang']]
        require(len(matches) == 1, 'Missing or duplicate formatted reference summary')
        preserve(r, matches[0], 'formatted reference summary')
    preserve(previous['interpreter_integration_audit'],data['interpreter_integration_audit'],
             'historical integration audit')
    return corrected
