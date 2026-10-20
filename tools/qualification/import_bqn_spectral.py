"""Offline additive admission of the exact measured BQN native-row-sum source.

--prepare writes a reviewable overlay. --apply needs both reviewed hashes.
Neither path launches native code, compilation, a browser or a network request.
The earlier k-nucleotide admission module is imported as frozen utility code.
"""
import argparse
import copy
import difflib
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from qualification import import_bqn_knucleotide as shared

BASE = 'experiments/bqn/spectral-sum-v1/'
ADMISSION = BASE+'admission-v1/'
PLAN, RESULTS, PREPARED = [ADMISSION+name+'.json' for name in ['plan', 'results', 'prepared']]
KEY, PARENT = 'spectralnorm:array-bqn-native-sum', 'spectralnorm:array-bqn-faithful'
SOURCE = BASE+'sources/row-sum.bqn'
SOURCE_SHA = '5366d80b35f49fd6aecdf3ffd1144c285a5b6df7d01be366d5012f3290a835c9'
PARENT_SOURCE = 'archive/comparisons/array-comparison/all-20261009/sources/spectralnorm-faithful.bqn'
PARENT_SHA = '5e6955104b07d3c2fdda9b5ee29c80ced059c064bd386db33d941f6c2b29d380'
SOURCE_REVISION = 'cecbaea3c6f62f8049d7e036bef003eb4286039e'
SOURCES = dict(zip(['parent-faithful', 'row-sum', 'row-and-dots-sum'], [PARENT_SHA, SOURCE_SHA,
    '59f937ff3e761f9812f3f440ea465b925a3f073460737c686c11d6adb4a88769']))
NS = [1, 2, 3, 5, 9, 10, 100]
FULL = dict(n=5500, bytes=12, sha256='f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb')
CONTROLLER_SHA = 'b31c9d8fd0c212046aa2e91640c6e264422a17f8d4add5a2625baaaa4c9de0de'
PROCESS_SHA = '313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
PRODUCER_PLAN_SHA = 'f109e1438c97e77c3575559391d9b4ae7573f5ab6f575f1c27612f7f50ff0822'
REVIEW_SHA = 'd9570d1833c06800119cd01612bfe3f64ffc96fd9326959b5ae6a11b836834a0'
SHARED_SHA = '5e79b71fc96822ece4604f4075bae444f25ecaf2b65bd3af07d9cea66c6f1843'
FFI = dict(path='/opt/homebrew/opt/libffi/lib/libffi.8.dylib',
    resolved_path='/opt/homebrew/Cellar/libffi/3.8.0/lib/libffi.8.dylib',
    sha256='e400b27537b9c7ff08e4e1d89fafc83e233020fcfb425a3ad25cb8c35029e1e1')
WORK = dict(status='source-reviewed-awaiting-native-output', separate_functions=['A', 'Av', 'Atv', 'AtAv'],
    atav_applications=20, matrix_vector_products=40, coefficient_evaluations='40*n*n',
    single_thread_application=True, new_ffi_or_native_helper=False, precomputed_matrix=False)
TIMING_BOUNDARY = 'Fresh BQN process through exit, including startup, parsing argv, all forty matrix-vector products and output; excludes hashing, reference validation and power checks.'
AUTHOR_CONTEXT = copy.deepcopy(shared.AUTHOR_CONTEXT)
REFS = dict(importer='tools/qualification/import_bqn_spectral.py', shared_helpers='tools/qualification/import_bqn_knucleotide.py',
    producer_plan=BASE+'plan.json', controller=BASE+'run_serial.py', process_controller='tools/qualification/lean_run.py',
    frozen_review=BASE+'REVIEW.md', measured_review=BASE+'README.md',
    ownership=BASE+'source-ownership-v1/row-sum-counts.json', ownership_review=BASE+'source-ownership-v1/REVIEW.md',
    corpus=shared.CORPUS, runtime_build=shared.REFS['runtime_build'],
    bounded=BASE+'bounded-v1/report.json', full=BASE+'full-matched-v1/report.json')
REPORT_HASHES = dict(bounded='722e63d306e2ebd9286448f6af147a1f7191bd0d5812ca4df4abbfed1b6ad0d4',
    full='2fa8ccc2b871585538faf8e4cca68d789d639e93ce050a984c846ce8b09f922e')
sha, pin, load, encoded, require, relative = shared.sha, shared.pin, shared.load, shared.encoded, shared.require, shared.relative


def recorded_root(report):
    rows = report.get('cases', []); command = rows[0].get('command') if rows else None
    suffix = '/'+shared.RUNTIME
    require(isinstance(command, list) and len(command) == 3 and isinstance(command[0], str)
            and Path(command[0]).is_absolute() and command[0].endswith(suffix), 'Wrong recorded runtime command')
    prefix = command[0][:-len(suffix)]
    require(prefix and '..' not in Path(prefix).parts and Path(prefix).as_posix() == prefix, 'Unsafe recorded repository root')
    return prefix


def make_plan(root=ROOT):
    root = Path(root)
    return dict(schema='bqn-spectral-admission-plan.v1', source=dict(path=SOURCE, sha256=SOURCE_SHA),
        selected='row-sum', parent_program=PARENT, source_revision=SOURCE_REVISION,
        recorded_execution_root=recorded_root(load(root/REFS['full'])),
        evidence={name: pin(root, path) for name, path in REFS.items()}, author_context=AUTHOR_CONTEXT,
        selection='Admit the minimal row-reduction change. It has the lowest saved matched median; retain the final-dot alternative as evidence without interpreting its small difference as a separate speed claim.',
        chart_admission=False, historical_observations_unchanged=True)


def check_sources(evidence):
    old = evidence.check(dict(path=PARENT_SOURCE, sha256=PARENT_SHA)).read_bytes()
    require(old.count('{+´v×'.encode()) == 2 and old.count('+´'.encode()) == 4, 'Parent reduction inventory differs')
    rows = old.replace('{+´v×'.encode(), '{•math.Sum v×'.encode())
    expected = [old, rows, rows.replace('+´'.encode(), '•math.Sum '.encode())]
    for (name, digest), content in zip(SOURCES.items(), expected):
        require(evidence.check(dict(path=BASE+'sources/'+name+'.bqn', sha256=digest)).read_bytes() == content,
                'Candidate contains an unreviewed source change')
    return old.decode(), rows.decode()


def check_ownership(evidence, ref):
    receipt = evidence.document(ref)
    require(receipt.get('schema') == 'bqn-spectral-source-ownership-review.v1'
            and receipt.get('source') == SOURCE and receipt.get('source_sha256') == SOURCE_SHA,
            'Source-count identity differs')
    require(receipt.get('independent_review_approved') is True and receipt.get('application_loc') == 13
            and receipt.get('physical_loc') == 9 and receipt.get('retained_rule_proposed_loc') == 13,
            'Exact-source count needs independent13/9 approval')
    require(receipt.get('policy') == 'application-loc-v1 / retained BQN physical-plus-packed-statements'
            and receipt.get('source_bytes_changed') is False and receipt.get('native_or_language_execution') is False,
            'Source-count policy/scope changed')
    old, new = check_sources(evidence); lines = new.splitlines(); ledger = receipt['line_ledger']
    require(len(ledger) == len(lines) and all(row['line'] == i+1 and row['source_text'] == text
        for i, (row, text) in enumerate(zip(ledger, lines))), 'Stale source ownership ledger')
    for i, row in enumerate(ledger, 1):
        significant = bool(lines[i-1].strip()) and not lines[i-1].lstrip().startswith('#')
        units = 3 if i in [4, 5] else int(significant)
        require(row['significant'] is significant and type(row['retained_rule_units']) is int
                and row['retained_rule_units'] == units and len(row['retained_rule_owners']) == units,
                'Changed source owner units')
    require(sum(row['retained_rule_units'] for row in ledger) == 13 and sum(row['significant'] for row in ledger) == 9,
            'Source count does not reconcile')
    policy = receipt['policies']['retained']
    for key in ['source', 'saved_audit']: evidence.check(dict(path=policy[key], sha256=policy[key+'_sha256']))
    audit = load(evidence.root/policy['saved_audit'])
    parent = next(row for row in audit['rows'] if row['file'] == 'spectralnorm-faithful.bqn')
    require(parent['sha256'] == PARENT_SHA and parent['physical_loc'] == 9 and parent['normalized_loc'] == 13
            and parent['expansions'] == receipt['baseline_comparison']['retained_expansions']
            and receipt['baseline_comparison']['source'] == PARENT_SOURCE
            and receipt['baseline_comparison']['source_sha256'] == PARENT_SHA
            and receipt['baseline_comparison']['canonical_retained_loc'] == 13, 'Historical parent count differs')
    require(receipt['source_delta']['unified_diff'] == ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile=PARENT_SOURCE, tofile=SOURCE)), 'Reviewed source delta differs')
    work = receipt['required_work']
    require(work == dict(status='source-reviewed-with-bounded-and-full-output', separate_functions=['A','Av','Atv','AtAv'],
        atav_applications=20, matrix_vector_products=40, coefficient_evaluations_full=1210000000, full_n=5500,
        precomputed_matrix=False, new_ffi_or_native_helper=False, single_thread_application=True, bounded_cases=NS),
        'Required-work source review differs')
    for label, target in [('plan', 'producer_plan'), ('bounded', 'bounded'), ('full', 'full')]:
        require(receipt['execution_evidence'][label] == pin(evidence.root, REFS[target]), 'Work/source evidence differs')
    return receipt


def check_producer_plan(evidence, ref):
    require(ref['sha256'] == PRODUCER_PLAN_SHA, 'Unreviewed producer plan')
    plan = evidence.document(ref)
    require(plan.get('schema') == 'bqn-spectral-sum-plan.v1' and plan.get('status') == 'PREPARED-NO-EXECUTION'
            and plan.get('benchmark') == 'spectralnorm' and plan.get('full') == FULL and plan.get('samples') == 3
            and plan.get('order_seed') == 20261020 and plan.get('common_mutex') == '/tmp/mech-clbg-timing.lock'
            and plan.get('required_work') == WORK and plan.get('timing_boundary') == TIMING_BOUNDARY
            and plan.get('chart_admission') is False, 'Wrong spectral execution plan')
    expected = dict(parent=dict(path=PARENT_SOURCE, sha256=PARENT_SHA), runtime=dict(path=shared.RUNTIME, sha256=shared.RUNTIME_SHA),
        controller=dict(path=REFS['controller'], sha256=CONTROLLER_SHA), process_controller=dict(path=REFS['process_controller'], sha256=PROCESS_SHA),
        review=dict(path=REFS['frozen_review'], sha256=REVIEW_SHA), corpus=dict(path=shared.CORPUS, sha256=shared.CORPUS_SHA))
    require(all(plan[key] == value for key, value in expected.items()) and plan['runtime_commit'] == shared.COMMIT
            and plan['sources'] == {name: dict(path=BASE+'sources/'+name+'.bqn', sha256=digest) for name, digest in SOURCES.items()}
            and plan['runtime_dependencies'] == [FFI], 'Source/runtime/support producer pins differ')
    corpus = evidence.document(plan['corpus'])
    cases = sorted((row for row in corpus['cases'] if row['benchmark'] == 'spectralnorm'), key=lambda row: row['n'])
    require([row['n'] for row in cases] == NS and cases == plan['bounded_cases'], 'Missing shared spectral bounded case')
    refs = []
    for row in cases:
        require(row['expected_exit'] == 0 and row['validation'] == 'exact-complete-bytes', 'Wrong reference policy')
        for key in ['stdin', 'expected']:
            ref = {**row[key], 'path': str(Path(shared.CORPUS).parent/row[key]['path'])}
            evidence.check(ref); refs.append({k: ref[k] for k in ['path', 'sha256']})
    require(plan['reference_files'] == refs, 'Reference file inventory differs')
    return plan


def expected_pins(plan):
    refs = [plan[key] for key in ['parent', 'runtime', 'runtime_build', 'controller', 'process_controller', 'review', 'corpus']]
    refs += [dict(path=REFS['producer_plan'], sha256=PRODUCER_PLAN_SHA)] + list(plan['sources'].values()) + plan['reference_files'] + plan['runtime_dependencies']
    return {row['path']: row['sha256'] for row in refs}


def check_execution(evidence, ref, mode, producer_plan, recorded, local_artifacts=False):
    report = evidence.document(ref)
    require(report.get('schema') == 'bqn-spectral-sum-execution.v1' and report.get('mode') == mode
            and report.get('status') == 'PASSED' and report.get('active') is None and report.get('pins_unchanged') is True
            and report.get('chart_admission') is False and report.get('diagnostic_profile') is False
            and report.get('full_workload') is (mode == 'full'), 'Incomplete/diagnostic spectral cohort')
    require(report.get('controller_sha256') == CONTROLLER_SHA and report.get('process_controller_sha256') == PROCESS_SHA
            and report.get('runtime_sha256') == shared.RUNTIME_SHA and report.get('plan') == dict(path=REFS['producer_plan'], sha256=PRODUCER_PLAN_SHA)
            and report.get('required_work') == WORK and report.get('timing_boundary') == TIMING_BOUNDARY
            and report.get('pins') == expected_pins(producer_plan) and recorded_root(report) == recorded,
            'Cohort source/runtime/controller pins differ')
    require(type(report.get('common_mutex_inode')) is int and report['common_mutex_inode'] > 0
            and report.get('started_utc') and report.get('finished_utc'), 'Mutex/process dates missing')
    prerequisite = pin(evidence.root, REFS['bounded']) if mode == 'full' else None
    require(report.get('bounded_prerequisite') == prerequisite, 'Bounded prerequisite differs')
    directory = str(Path(ref['path']).parent)
    for name, digest in SOURCES.items(): evidence.check(dict(path=directory+'/sources/'+name+'.bqn', sha256=digest))
    evidence.check(dict(path=directory+'/controllers/run_serial.py', sha256=CONTROLLER_SHA))
    evidence.check(dict(path=directory+'/controllers/lean_run.py', sha256=PROCESS_SHA))
    evidence.check(dict(path=directory+'/plan.json', sha256=PRODUCER_PLAN_SHA))
    for path, digest in report['pins'].items():
        if path == shared.RUNTIME or Path(path).is_absolute():
            if local_artifacts:
                target = evidence.root/path
                require(sha(target) == digest, 'Changed local runtime/dependency artifact')
        else: evidence.check(dict(path=path, sha256=digest))
    cases = producer_plan['bounded_cases']
    schedule = [(row['n'], 1, row['case']) for row in cases] if mode == 'bounded' else [(5500, sample, 'full-'+str(sample)) for sample in [1,2,3]]
    rng = random.Random(20261020); orders = []
    for n, sample, _ in schedule:
        names = list(SOURCES); rng.shuffle(names); orders.append(dict(n=n, sample=sample, sources=names))
    require(report.get('orders') == orders, 'Shuffled round order differs')
    identities = [(n, sample, case, name) for (n, sample, case), order in zip(schedule, orders) for name in order['sources']]
    rows = report.get('cases', [])
    require([(row.get('n'), row.get('sample'), row.get('case'), row.get('source')) for row in rows] == identities,
            'Missing/duplicated execution or incorrect sample order')
    additions = {'source', 'n', 'sample', 'case', 'output_valid', 'source_sha256', 'runtime_sha256', 'power_before', 'power_after'}
    for row in rows:
        n, sample, case, name = row['n'], row['sample'], row['case'], row['source']
        require(row['command'] == [str(Path(recorded)/shared.RUNTIME), str(Path(recorded)/(BASE+'sources/'+name+'.bqn')), str(n)]
                and row.get('source_sha256') == SOURCES[name] and row.get('runtime_sha256') == shared.RUNTIME_SHA,
                'Wrong process command/source/runtime')
        reference = FULL if mode == 'full' else next(case for case in cases if case['n'] == n)['expected']
        if mode == 'full': require(row.get('stdin') == '/dev/null', 'Full spectral stdin must be /dev/null')
        else:
            stdin = next(case for case in cases if case['n'] == n)['stdin']
            require(relative(evidence.root, row['stdin'], recorded) == str(Path(shared.CORPUS).parent/stdin['path']), 'Wrong recorded bounded stdin')
        seconds = row.get('elapsed_seconds')
        require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0 and row.get('output_valid') is True
                and row.get('exit_code') == 0 and row.get('timed_out') is False and type(row.get('pid')) is int and row['pid'] > 0
                and row.get('started_utc') and row.get('finished_utc'), 'Failed/nonfinite process receipt')
        attempt = directory+'/'+case+'-'+name
        for stream in ['stdout', 'stderr']:
            require(relative(evidence.root, row[stream]['path'], recorded) == attempt+'/'+stream+'.bin', 'Wrong process stream path')
            evidence.check({**row[stream], 'path': attempt+'/'+stream+'.bin'})
        require(row['stdout']['bytes'] == reference['bytes'] and row['stdout']['sha256'] == reference['sha256']
                and row['stderr']['bytes'] == 0, 'Output differs from complete reference')
        raw = evidence.document(pin(evidence.root, attempt+'/process.json'))
        require(raw == {key: value for key, value in row.items() if key not in additions}, 'Raw process receipt differs')
        shared.check_power(row['power_before']); shared.check_power(row['power_after'])
    if mode == 'full':
        samples = {name: [row['elapsed_seconds'] for row in rows if row['source'] == name] for name in SOURCES}
        require(report.get('samples') == samples and report.get('medians') == {name: statistics.median(values) for name, values in samples.items()}
                and report.get('sample_sd_seconds') == {name: statistics.stdev(values) for name, values in samples.items()}, 'Stale sample aggregation')
    return report


def reconcile(root=ROOT, local_artifacts=True):
    evidence = shared.Evidence(root); root = evidence.root
    plan = load(root/PLAN)
    require(plan == make_plan(root) and plan['source'] == dict(path=SOURCE, sha256=SOURCE_SHA), 'Stale/changed admission plan')
    for ref in plan['evidence'].values(): evidence.check(ref)
    require(plan['evidence']['shared_helpers']['sha256'] == SHARED_SHA
            and all(plan['evidence'][label]['sha256'] == digest for label, digest in REPORT_HASHES.items()), 'Changed frozen helper/cohort')
    producer = check_producer_plan(evidence, plan['evidence']['producer_plan'])
    require(producer['runtime_build'] == plan['evidence']['runtime_build'], 'Runtime build receipt differs')
    ownership = check_ownership(evidence, plan['evidence']['ownership'])
    recorded = plan['recorded_execution_root']
    build = shared.check_build(evidence, plan['evidence']['runtime_build'], local_artifacts, recorded)
    bounded = check_execution(evidence, plan['evidence']['bounded'], 'bounded', producer, recorded, local_artifacts)
    full = check_execution(evidence, plan['evidence']['full'], 'full', producer, recorded, local_artifacts)
    require(bounded['common_mutex_inode'] == full['common_mutex_inode'], 'Cohorts used different common locks')
    require(min(full['medians'], key=lambda name: (full['medians'][name], name)) == 'row-sum', 'Selected source is not the retained lowest matched median')
    selected = [copy.deepcopy(row) for row in full['cases'] if row['source'] == 'row-sum']
    for row in selected: row.update(producer_report=plan['evidence']['full'], producer_plan=plan['evidence']['producer_plan'])
    samples = [row['elapsed_seconds'] for row in selected]
    program = dict(key=KEY, id=KEY.split(':')[1], original_program_key=PARENT, source_sha256=SOURCE_SHA,
        loc=13, physical_loc=9, samples_seconds=samples, median_seconds=statistics.median(samples), sample_sd_seconds=statistics.stdev(samples),
        command=selected[0]['command'], sample_execution_metadata=selected, build_command=build['flags'], build_cwd=shared.BASE+'.build/CBQN')
    artifacts = [dict(path=path, sha256=digest) for path, digest in sorted(evidence.fingerprints.items()) if '/.build/' not in path]
    return dict(schema='bqn-spectral-admission-results.v1', status='RECONCILED', plan=pin(root, PLAN), evidence=plan['evidence'],
        programs=[program], recorded_at=full['finished_utc'], recorded_execution_root=recorded, new_observations=3,
        historical_data_preserved=True, full_workload_n=5500, matched_candidate_medians=full['medians'],
        matched_control_speedup=full['medians']['parent-faithful']/program['median_seconds'], selection=plan['selection'],
        source_count_review=ownership, required_work=dict(status='source-reviewed-with-bounded-and-full-output', **{key: value for key, value in WORK.items() if key != 'status'},
            weighted_contributions=1210000000), author_context=AUTHOR_CONTEXT,
        toolchains=dict(bqn=dict(version=build['version'], commit=shared.COMMIT, sha256=shared.RUNTIME_SHA)),
        runtime_details=dict(build=plan['evidence']['runtime_build'], official_repository=build['official_repository'],
            restoration_limitation=build['restoration_limitation'], application_imports=[], linked_runtime_dependencies=[FFI]),
        runtime_environment=dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC'), timing_boundary=TIMING_BOUNDARY, artifacts=artifacts)


def authorship_record(parent, results, evidence):
    result = copy.deepcopy(parent['authorship'])
    result.update(kind='ai-adapted', label='AI adapted · retained faithful predecessor', source_sha256=[SOURCE_SHA], origin_status='unresolved',
        parent_programs=[PARENT], parent_sources=[dict(program_key=PARENT, relationship='local predecessor', **ref) for ref in parent['authorship'].get('retained_sources', [])],
        retained_sources=[dict(source_sha256=SOURCE_SHA, url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)],
        ai=dict(tool=AUTHOR_CONTEXT['tool'], models=[], model_family=AUTHOR_CONTEXT['model_family'], exact_model=None,
            status='family-identified-exact-model-unverified', matched_source_files=[SOURCE_SHA], total_source_files=1, evidence=[evidence['plan'], evidence['results']]),
        local_change_license=dict(status='suite-license', id='Apache-2.0', evidence='LICENSE', scope='New local changes only; inherited terms remain unresolved.'),
        evidence=[evidence['plan']['path'], evidence['results']['path'], evidence['ownership']['path']])
    return result


def bound_authorship(data, profile, root=ROOT):
    root = Path(root); detail = profile.get('source_provenance_record') or {}; results = load(root/RESULTS)
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    require(profile.get('key') == KEY and profile.get('files') == [SOURCE_SHA] and detail.get('kind') == 'suite-authored-optimization'
            and detail.get('source_sha256') == SOURCE_SHA and detail.get('original_program_key') == PARENT
            and detail.get('admission') == evidence['results'] and detail.get('author_context') == AUTHOR_CONTEXT
            and results.get('schema') == 'bqn-spectral-admission-results.v1' and results.get('status') == 'RECONCILED'
            and results.get('plan') == evidence['plan'] and results.get('author_context') == AUTHOR_CONTEXT
            and results['programs'][0]['key'] == KEY and results['programs'][0]['source_sha256'] == SOURCE_SHA
            and sha(root/SOURCE) == SOURCE_SHA and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest() == SOURCE_SHA,
            'Unbound spectral source/authorship admission')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT], results, evidence)


def append_catalog(before, root=ROOT):
    root = Path(root).resolve(); results = load(root/RESULTS)
    require(results == reconcile(root, local_artifacts=False), 'Stale reconciled spectral results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'] and 'bqn_spectral_audit' not in before, 'Spectral candidate already admitted')
    data = copy.deepcopy(before); parent = before['programs'][PARENT]; r = results['programs'][0]
    require(parent['files'] == [PARENT_SHA] and parent['loc'] == 13 and parent['physical_loc'] == 9, 'Historical faithful parent changed')
    bench = next(b for b in data['benchmarks'] if b['key'] == 'spectralnorm')
    require(r['loc'] >= bench['baseline_loc'] and r['median_seconds'] >= bench['baseline_seconds'], 'New global baseline needs separate normalization review')
    require(SOURCE_SHA not in data['files'], 'Source already cataloged')
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    data['files'][SOURCE_SHA] = dict(name='row-sum.bqn', path=SOURCE, archive_path=SOURCE, sha256=SOURCE_SHA, code=(root/SOURCE).read_text())
    row = copy.deepcopy(parent)
    for field in ['publication_record','timing_measurement','timing_correction','aliased_sample_source','source_alias_of','source_alias_note','loc_expansions','source_accounting','authorship','source_metrics']:
        row.pop(field, None)
    row.update(key=KEY, id=r['id'], receipt_key=r['id'], files=[SOURCE_SHA], loc=13, physical_loc=9, loc_metric='assignment-normalized',
        seconds=r['median_seconds'], samples=r['samples_seconds'], timing_sd=r['sample_sd_seconds'], x=13/bench['baseline_loc'], y=r['median_seconds']/bench['baseline_seconds'],
        formatted_loc=None, formatted_x=None, formatted_loc_status='pending', formatted_loc_complete=False, formatted_loc_evidence={},
        report=RESULTS, report_sha256=evidence['results']['sha256'], source_report=evidence['ownership']['path'], loc_report=evidence['ownership']['path'],
        command=r['command'], runtime_arguments=['5500'], build_command=r['build_command'], build_cwd=str(Path(results['recorded_execution_root'])/r['build_cwd']),
        cwd=results['recorded_execution_root'], execution_mode='interpreter', binary_sha256=shared.RUNTIME_SHA, runtime_sha256=shared.RUNTIME_SHA,
        native_observations=3, timing_alias_of=None, sample_execution_metadata=r['sample_execution_metadata'],
        original_program_key=PARENT, retained_source_revision=SOURCE_REVISION, local_adaptation=True, distinct_optimization_claimed=True,
        source_provenance='Suite-authored native row-sum optimization of the retained faithful BQN source; predecessor origin and inherited terms remain unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization', original_program_key=PARENT, source_sha256=SOURCE_SHA,
            admission=evidence['results'], origin_status='inherited-unresolved', author_context=AUTHOR_CONTEXT),
        runtime_policy='CBQN commit '+shared.COMMIT+'; exact uninstrumented rebuilt release; single-process source; native math.Sum primitive',
        runtime_support='Existing CBQN runtime primitives only; no application imports, FFI helper or benchmark executor.',
        runtime_environment=results['runtime_environment'], timing_boundary=TIMING_BOUNDARY,
        timing_summary='Three fresh matched complete-process observations; row reductions use native math.Sum. Historical samples remain unchanged. Final-dot alternative retained as evidence; no global optimality claim.',
        algorithm=dict(strict=True, status='required-work-reviewed', native_benchmark_kernel=False,
            reason='Four source functions and twenty AtAv applications perform all forty matrix-vector products and 1,210,000,000 coefficient evaluations. Only two row reductions use the ordinary CBQN math.Sum primitive; no stored matrix or answer shortcut.',
            full_work=dict(n=5500, power_applications=20, matrix_vector_products=40, weighted_contributions=1210000000), evidence=evidence['ownership']),
        source_accounting=dict(policy='application-loc-v1', application_loc=13, physical_loc=9, evidence=evidence['ownership']['path'],
            review_sha256=evidence['ownership']['sha256'], qualification='Exact-source approved replay of retained BQN physical-plus-packed-statements13/9; no native parser certificate.', files=[]),
        file_roles={SOURCE_SHA:dict(role='application', included_in_application_loc=True, normalized_loc=13, physical_loc=9)},
        full_output_validation=dict(all_three_samples_passed=True, evidence=evidence['full']), chart_admission=dict(historical_reports_unchanged=True, **evidence),
        measured_backend=dict(key='bqn', execution='interpreter', label='BQN (CBQN)', verified=True,
            evidence=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'], command=r['command'], source_sha256=[SOURCE_SHA],
                runtime_receipt=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'], field='/toolchains/bqn/version',
                    value=results['toolchains']['bqn']['version'], value_encoding='literal-saved-string'))))
    row['authorship'] = authorship_record(parent, results, evidence)
    data['programs'][KEY] = row; data['program_inventory'][KEY] = copy.deepcopy(row)
    group = next(g for g in bench['groups'] if g['language'] == 'bqn'); group['programs'].append(KEY)
    candidates = [data['programs'][key] for key in group['programs']]
    group['fast'] = min(candidates, key=lambda p:(p['seconds'],p['loc'],p['key']))['key']
    group['small'] = min(candidates, key=lambda p:(p['loc'],p['seconds'],p['key']))['key']
    for summary in data['reference_summary']:
        if summary['lang'] != 'bqn': continue
        groups = [g for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'bqn']
        for kind in ['fast','small']:
            selected = [data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind] = dict(x=statistics.geometric_mean(p['x'] for p in selected), y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*evidence.values(), *results['artifacts'], dict(path=SOURCE, sha256=SOURCE_SHA)]: data['archive_paths'][ref['path']] = ref['path']
    data['bqn_spectral_audit'] = dict(schema='bqn-spectral-catalog-extension.v1', appended_programs=[KEY], evidence=evidence,
        measured_at=results['recorded_at'], new_observations=3, source_files_added=1, old_profiles_unchanged=True, old_baselines_unchanged=True)
    for pool in ['programs','program_inventory','files','archive_paths']:
        require(all(data[pool][key] == old for key, old in before[pool].items()), 'Historical '+pool+' changed')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-before-sha256'); parser.add_argument('--expected-prepared-sha256')
    args = parser.parse_args(); require(args.prepare != args.apply, 'Choose exactly one of --prepare/--apply')
    catalog = ROOT/'data/benchmarks.json'
    if args.prepare:
        before_bytes = catalog.read_bytes()
        before = json.loads(before_bytes, object_pairs_hook=shared.no_duplicates,
            parse_constant=lambda value: require(False, 'Nonfinite JSON constant: '+value))
        before_sha = hashlib.sha256(before_bytes).hexdigest()
        shared.write(ROOT/PLAN, make_plan()); shared.write(ROOT/RESULTS, reconcile())
        shared.write(ROOT/PREPARED, append_catalog(before))
        require(sha(catalog) == before_sha, 'Canonical changed during preview preparation; regenerate against the settled catalog')
        print(dict(before_sha256=before_sha, prepared_sha256=sha(ROOT/PREPARED), results_sha256=sha(ROOT/RESULTS), canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256, 'Apply needs reviewed before/preview hashes')
        require(sha(catalog) == args.expected_before_sha256 and sha(ROOT/PREPARED) == args.expected_prepared_sha256, 'Reviewed before/preview identity differs')
        after = append_catalog(load(catalog)); require(encoded(after) == (ROOT/PREPARED).read_bytes(), 'Preview does not reproduce')
        require(sha(catalog) == args.expected_before_sha256, 'Canonical changed during reconciliation')
        shared.write(catalog, after)
        print('Added exact qualified BQN native row-sum source; historical observations retained.')


if __name__ == '__main__': main()
