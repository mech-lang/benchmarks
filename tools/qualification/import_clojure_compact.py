"""Admit the independently timed compact typed-aset Clojure source, preserving prior cohorts.

Offline evidence only: preparation verifies local runtime/class artifacts, while
archived replay checks retained manifests and complete streams without claiming
to rehash absent ignored binaries. No subprocess, compiler or subject is started.
"""
import argparse
import copy
import hashlib
import math
from pathlib import Path
import random
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from qualification import import_bqn_knucleotide as shared

BASE = 'experiments/clojure/compact-primitive-v1/'
QUAL = BASE + 'hot-only-v2/'
ADMISSION = BASE + 'admission-v1/'
PLAN, RESULTS, PREPARED = [ADMISSION + name + '.json' for name in ('plan', 'results', 'prepared')]
KEY = 'nbody:clojure-nbody-compact-hot-aset-v1'
PARENT = 'nbody:clojure-nbody-compact'
CONTROL = 'nbody:clojure-nbody-primitive-updates-v1'
SOURCE = BASE + 'sources/clbg/nbody/compact_hot_aset.clj'
SOURCE_SHA = 'e73abcb37312c1f54fd71e4fbc80042d0581b5e36bc26e06a2d46aebe575ef05'
PARENT_SOURCE = 'programs/clojure/nbody/clojure-nbody-compact/compact.clj'
PARENT_SHA = '193e26ad8dfd011fd1835d9d67be04bb223d088e6cdd3e2d6302ca8cae2f46d4'
CONTROL_SHA = '12d61dd8a07254f6ba94652fb30b63cc305ec0145e482f1136044a1dc8c88fe2'
SUPPORT_SHA = 'ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446'
SOURCE_REVISION = '612fb31e030be207779c03cddb00a16af56f0173'
NAMES = ['parent', 'primitive-control', 'compact-hot-aset']
SELECTED = ['primitive-control', 'compact-hot-aset']
NS = [0, 1, 2, 3, 7, 10, 31, 1000, 1001, 10000]
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
FULL = b'-0.169075164\n-0.169059907\n'
NOTES = b'NOTE: Picked up JDK_JAVA_OPTIONS: \nPicked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \n'
TOOL_NOTES = b'Picked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \n'
WARNING = b"Reflection warning, clbg/support.clj:19:16 - reference to field get can't be resolved.\n"
AUTHOR_CONTEXT = copy.deepcopy(shared.AUTHOR_CONTEXT)
FROZEN = {
    'foundation': (QUAL + 'execution-plan.json', 'd01f6b3a93d04c3589a81beca46baf8cca3b0f24d4df06589ae2745a6fa6ac3f'),
    'runtime': (QUAL + 'runtime-build.json', '8a77c406dacff8f397359bba295d2f92ece05ee2270c2f7c83f517ac576e9f3a'),
    'builds': (QUAL + 'builds.json', 'f8151bcdeb5e3c9c69af7dca0d7816563b822e95949f2693d2df70688a437e65'),
    'state': (QUAL + 'state-probe-report.json', '8b13f887b5c126a84a0163e2efd8517cc6f6cb2584bd016f578940d77985529d'),
    'bounded': (QUAL + 'bounded-v1/report.json', '2dcb1d8e59ab4434ee28d47491ee3f86abf945e8064bb3f9b7253dfe2c8624c1'),
    'pilot': (QUAL + 'pilot-v1/report.json', 'ec1df186a8a64626ddd6ff0e6b12be2eb0d65911b37d695ec732e42190632d47'),
    'selected_plan': (QUAL + 'selected-full-v1/plan.json', 'afd6d6aa7718f11af1f1d0055e3fc70f6bea6d929756c2b04da6a2a31c2ea906'),
    'full': (QUAL + 'selected-full-v1/full-v1/report.json', '49eeeabf6d73b10f4a354d49db5def45ba7266c50ba970edbc8116365f48c7ad'),
    'ownership': (BASE + 'source-ownership-approved.json', '81173c609ae02211f4cb3c16d312520d395921d73bc1a8570a516ee4e41c87d7'),
}
sha, pin, load, encoded, require, relative = shared.sha, shared.pin, shared.load, shared.encoded, shared.require, shared.relative


def make_plan(root=ROOT):
    root = Path(root)
    evidence = {name: dict(path=path, sha256=digest) for name, (path, digest) in FROZEN.items()}
    evidence.update(importer=pin(root, 'tools/qualification/import_clojure_compact.py'),
                    shared_helpers=pin(root, 'tools/qualification/import_bqn_knucleotide.py'))
    return dict(schema='clojure-compact-admission-plan.v1', key=KEY, parent=PARENT, control=CONTROL,
        source=dict(path=SOURCE, sha256=SOURCE_SHA), source_revision=SOURCE_REVISION,
        evidence=evidence, author_context=AUTHOR_CONTEXT, chart_admission=False,
        selection='Retain the qualified compact candidate despite its slower matched control. Its own three full observations are independent; earlier cohorts and the existing fast profile remain unchanged.',
        source_size_scope='Approved retained count of 109 units and 49 physical lines for this exact source. The supplemental native logical count of 63 units is not admitted by this importer and needs its own binder extension.',
        historical_measurements_unchanged=True)


def check_closure(evidence, pins, local_artifacts, recorded):
    require(isinstance(pins, dict) and pins, 'Empty evidence closure')
    for path, digest in pins.items():
        path = relative(evidence.root, path, recorded)
        if '/.build/' in path and not local_artifacts:
            continue
        evidence.check(dict(path=path, sha256=digest))


def recorded_root(foundation, full, runtime):
    executable = full['cases'][0]['command'][0]
    suffix = '/' + runtime['java']['path']
    require(isinstance(executable, str) and executable.endswith(suffix), 'Wrong exact JVM executable suffix')
    recorded = executable[:-len(suffix)]
    require(recorded and Path(recorded).is_absolute() and str(Path(recorded)) == recorded
            and '..' not in Path(recorded).parts, 'Unsafe recorded execution root')
    require(full['cases'][0]['cwd'] == recorded, 'Recorded command/cwd roots differ')
    for name, program in foundation['programs'].items():
        require(name in NAMES and program['flags'] == FLAGS
                and program['compile_options'] == dict(direct_linking=True, warn_on_reflection=True),
                'Wrong compiled-source options')
        classes = str(Path(recorded) / (QUAL + '.build/classes-build-v1/' + name))
        jars = [str(Path(recorded) / item['path']) for item in runtime['jars']]
        expected = [str(Path(recorded) / runtime['java']['path']), *FLAGS, '-cp', ':'.join([classes, *jars]), program['main_class']]
        require(program['classes'] == classes and program['run_argv'] == expected, 'Changed JVM/classpath or mixed recorded roots')
    return recorded


def process_stream(evidence, value, path, recorded):
    require(relative(evidence.root, value['path'], recorded) == path, 'Wrong stream path or recorded root')
    return evidence.check({**value, 'path': path}).read_bytes()


def check_processes(evidence, report, label, foundation, recorded):
    full, pilot = label == 'full', label == 'pilot'
    expected_schema = 'clojure-compact-expression-selected-full-execution.v1' if full else 'clojure-compact-hot-only-execution.v2'
    require(report['schema'] == expected_schema and report['mode'] == label and report['status'] == 'PASSED'
        and report['active'] is None and report['pins_unchanged'] is True and report.get('finished_utc')
        and report['chart_admission'] is False and report['diagnostic_profile'] is pilot and report['full_workload'] is full
        and report['timing_boundary'] == foundation['timing_boundary'] and report['required_work'] == foundation['required_work'],
        'Incomplete or changed process cohort')
    names = SELECTED if full or pilot else NAMES
    require(report['sources'] == names, 'Wrong measured/qualification source pool')
    schedule = [(50000000, i) for i in (1, 2, 3)] if full else [(1000000, 1)] if pilot else [(n, 1) for n in NS]
    rng = random.Random(20261020)
    orders = []
    for n, sample in schedule:
        order = names.copy(); rng.shuffle(order)
        orders.append(dict(n=n, sample=sample, sources=order))
    rows = report['cases']
    require(report['orders'] == orders and [(r['n'], r['sample'], r['source']) for r in rows]
            == [(o['n'], o['sample'], name) for o in orders for name in o['sources']],
            'Missing, duplicate or reordered process observations')
    extras = {'source', 'n', 'sample', 'case', 'output_valid', 'exact_reference_bytes', 'exact_parent_bytes',
              'source_sha256', 'power_before', 'power_after'}
    outputs = {}
    for row in rows:
        name, n, sample = row['source'], row['n'], row['sample']
        program = foundation['programs'][name]
        require(row['command'] == program['run_argv'] + [str(n)] and row['cwd'] == recorded
            and row['environment'] == foundation['environment'] and row['stdin'] == '/dev/null'
            and row['source_sha256'] == program['source']['sha256'] and row['exit_code'] == 0
            and row['timed_out'] is False and row['remaining_process_group'] == [] and row['output_valid'] is True
            and row['common_mutex_inherited'] is True and row['common_mutex_inode'] == report['common_mutex_inode']
            and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds'] > 0
            and row['maximum_rss_bytes'] <= 10 * 1024**3, 'Invalid process/source/runtime boundary')
        directory = QUAL + ('selected-full-v1/full-v1/round-' + str(sample) + '-' + name if full
                            else label + '-v1/n-' + str(n) + '-round-' + str(sample) + '-' + name)
        raw = evidence.document(pin(evidence.root, directory + '/process.json'))
        require(raw == {k: v for k, v in row.items() if k not in extras}, 'Raw process receipt differs')
        stdout = process_stream(evidence, row['stdout'], directory + '/stdout.bin', recorded)
        stderr = process_stream(evidence, row['stderr'], directory + '/stderr.bin', recorded)
        require(stderr in (b'', NOTES), 'Unexpected JVM/application stderr')
        shared.check_power(row['power_before']); shared.check_power(row['power_after'])
        if full:
            require(row['exact_reference_bytes'] is True and stdout == FULL, 'Full output differs from the exact 26-byte reference')
        elif not pilot:
            ref = report['references'][str(n)]
            expected = evidence.check({**ref, 'path': relative(evidence.root, ref['path'], recorded)}).read_bytes()
            require(row['exact_reference_bytes'] is True and stdout == expected, 'Bounded output differs from independent reference')
        else:
            require(row['exact_parent_bytes'] is True, 'Pilot does not match its exact qualified control')
        outputs[name, n, sample] = stdout
    if pilot:
        require(outputs['primitive-control', 1000000, 1] == outputs['compact-hot-aset', 1000000, 1], 'Pilot exact control bytes differ')
    samples = {name: [r['elapsed_seconds'] for r in rows if r['source'] == name] for name in names}
    require(report['samples'] == samples and report['medians'] == {k: statistics.median(v) for k, v in samples.items()},
            'Stale sample/median aggregates')
    if full:
        saved = report['sample_sd_seconds']
        require(saved.keys() == samples.keys() and all(math.isfinite(saved[name])
            and math.isclose(saved[name], statistics.stdev(values), rel_tol=1e-14, abs_tol=0)
            for name, values in samples.items()), 'Stale sample dispersion')


def check_builds(evidence, builds, foundation, runtime, recorded):
    require(builds['schema'] == 'clojure-nbody-builds.v1' and builds['status'] == 'PASSED' and builds['active'] is None
            and builds['runtime'] == dict(path=FROZEN['runtime'][0], sha256=FROZEN['runtime'][1]), 'Wrong build/runtime receipt')
    observations = {}
    for name in NAMES:
        program = foundation['programs'][name]
        require(builds['programs'][name] == program, 'Measured classes differ from built classes')
        for ref in program['evidence']:
            path = evidence.check(ref)
            if path.name != 'process.json':
                continue
            raw = load(path)
            require(raw['exit_code'] == 0 and raw['timed_out'] is False and raw['remaining_process_group'] == []
                    and raw['cwd'] == recorded and raw['environment'] == runtime['environment'], 'Unclean compiler/diagnostic process')
            for stream in ('stdout', 'stderr'):
                item = raw[stream]
                content = evidence.check({**item, 'path': relative(evidence.root, item['path'], recorded)}).read_bytes()
                if stream == 'stderr':
                    compile_process = '/compile-' in ref['path']
                    allowed = (b'', NOTES, TOOL_NOTES, WARNING, NOTES + WARNING) if compile_process else (b'', NOTES, TOOL_NOTES)
                    require(content in allowed, 'Unreviewed application/compiler warning')
        path = QUAL + 'build-v1/javap-advance-' + name + '/stdout.bin'
        text = evidence.check(pin(evidence.root, path)).read_text()
        observations[name] = dict(evidence=pin(evidence.root, path),
            typed_array_store_sites=len(re.findall(r'invokestatic.*Method clojure/lang/RT\.aset:\(\[DID\)D', text)),
            double_boxing_sites=len(re.findall(r'invokestatic.*Method java/lang/Double\.valueOf:', text)),
            tuple_construction_sites=len(re.findall(r'invokestatic.*Method clojure/lang/Tuple\.create:', text)))
    hot = observations['compact-hot-aset']
    require((hot['typed_array_store_sites'], hot['double_boxing_sites'], hot['tuple_construction_sites']) == (5, 3, 4),
            'Unexpected exact compiled compact update')
    return observations


def reconcile(root=ROOT, local_artifacts=True):
    evidence = shared.Evidence(root); root = evidence.root
    plan = load(root / PLAN)
    require(plan == make_plan(root), 'Changed/stale compact admission plan')
    docs = {name: evidence.document(ref) for name, ref in plan['evidence'].items() if name in FROZEN}
    for ref in plan['evidence'].values(): evidence.check(ref)
    require(plan['evidence']['shared_helpers']['sha256'] == '5e79b71fc96822ece4604f4075bae444f25ecaf2b65bd3af07d9cea66c6f1843', 'Frozen evidence helper changed')
    foundation, selected, full, runtime = [docs[k] for k in ('foundation', 'selected_plan', 'full', 'runtime')]
    recorded = recorded_root(foundation, full, runtime)
    require(runtime['schema'] == 'clojure-runtime-build.v1' and runtime['status'] == 'PASSED'
            and foundation['environment'] == runtime['environment'] and foundation['java'] == runtime['java'], 'Unqualified JVM/runtime')
    require(sorted(foundation['programs']) == sorted(NAMES)
        and foundation['programs']['parent']['source'] == dict(path=PARENT_SOURCE, sha256=PARENT_SHA)
        and foundation['programs']['primitive-control']['source']['sha256'] == CONTROL_SHA
        and foundation['programs']['compact-hot-aset']['source'] == plan['source']
        and all(p['support']['sha256'] == SUPPORT_SHA for p in foundation['programs'].values()), 'Wrong exact source/support pool')
    require(selected['sources'] == SELECTED and selected['retained_qualification_pool'] == NAMES
        and selected['retained_pilot_pool'] == SELECTED and selected['full_n'] == 50000000 and selected['rounds'] == 3
        and len(selected['pins']) == 706 and selected['foundation'] == plan['evidence']['foundation']
        and full['plan'] == plan['evidence']['selected_plan'] and full['pins'] == selected['pins']
        and selected['preselection']['objective'] == 'retain-compact-expression-despite-slower-pilot', 'Changed selected full protocol')
    require(full['preselection'] == selected['preselection'] and full['foundation'] == selected['foundation']
        and full['bounded'] == selected['bounded'] and full['pilot'] == selected['pilot']
        and full['runtime'] == selected['runtime'] and full['builds'] == selected['builds']
        and full['state_probe'] == selected['state_probe'], 'Full prerequisite bindings differ')
    state = docs['state']
    require(state['schema'] == 'clojure-nbody-state-probe.v1' and state['status'] == 'PASSED'
        and state['runtime'] == plan['evidence']['runtime'] and state['builds'] == plan['evidence']['builds']
        and state['implementations'] == 3 and state['raw_bit_state_slots'] == 35 and state['advance_function_invocations'] == 348
        and state['inner_pair_store_counters'] == 'not-instrumented-source-proof-only' and state['timing_sample'] is False,
        'Incomplete or overstated raw-bit state proof')
    source = evidence.check(plan['source']).read_text()
    parent = evidence.check(dict(path=PARENT_SOURCE, sha256=PARENT_SHA)).read_text()
    prefix, advance = parent.replace('clbg.nbody.compact ', 'clbg.nbody.compact-hot-aset ', 1).split('(defn advance ', 1)
    require(source == prefix + '(defn advance ' + advance.replace('(aset-double', '(aset')
        and source.count('(aset ') == 3 and source.count('(doseq ') == 1, 'Unreviewed compact source delta')
    count = docs['ownership']
    require(count['schema'] == 'clojure-compact-retained-source-review.v1' and count['independent_review_approved'] is True
        and count['application_loc'] == 109 and count['physical_loc'] == 49 and count['native_grammar_replay_claimed'] is False
        and count['source'] == plan['source'] and [r['text'] for r in count['line_ledger']] == source.splitlines()
        and sum(r['retained_rule_proposed_units'] for r in count['line_ledger']) == 109, 'Unapproved retained owner ledger: 109 units and 49 physical lines')
    check_closure(evidence, selected['pins'], local_artifacts, recorded)
    for document in docs.values():
        if isinstance(document.get('pins'), dict): check_closure(evidence, document['pins'], local_artifacts, recorded)
    for program in foundation['programs'].values():
        check_closure(evidence, program['class_pins'], local_artifacts, recorded)
    observations = check_builds(evidence, docs['builds'], foundation, runtime, recorded)
    for name in NAMES:
        evidence.check(dict(path=QUAL + 'selected-full-v1/full-v1/sources/' + name + '.clj',
                            sha256=foundation['programs'][name]['source']['sha256']))
    evidence.check(dict(path=QUAL + 'selected-full-v1/full-v1/sources/support.clj', sha256=SUPPORT_SHA))
    for field, name in (('controller', 'run_selected_full.py'), ('frozen_helper', 'run_serial.py')):
        evidence.check(dict(path=QUAL + 'selected-full-v1/full-v1/controllers/' + name, sha256=full[field]['sha256']))
    for label in ('bounded', 'pilot', 'full'):
        check_processes(evidence, docs[label], label, foundation, recorded)
    require(docs['bounded']['common_mutex_inode'] == docs['pilot']['common_mutex_inode'] == full['common_mutex_inode'], 'Different common mutexes')
    rows = [copy.deepcopy(row) for row in full['cases'] if row['source'] == 'compact-hot-aset']
    for row in rows: row.update(producer_report=plan['evidence']['full'], producer_plan=plan['evidence']['selected_plan'])
    samples = [row['elapsed_seconds'] for row in rows]
    program = foundation['programs']['compact-hot-aset']
    return dict(schema='clojure-compact-admission-results.v1', status='RECONCILED', plan=pin(root, PLAN), evidence=plan['evidence'],
        programs=[dict(key=KEY, id=KEY.split(':', 1)[1], source_sha256=SOURCE_SHA, loc=109, physical_loc=49,
            samples_seconds=samples, median_seconds=statistics.median(samples),
            sample_sd_seconds=full['sample_sd_seconds']['compact-hot-aset'],
            command=rows[0]['command'], build_command=program['compile_command'], sample_execution_metadata=rows)],
        recorded_at=full['finished_utc'], recorded_execution_root=recorded, author_context=AUTHOR_CONTEXT,
        matched_candidate_medians=full['medians'], matched_control_program=CONTROL,
        candidate_time_over_matched_control=statistics.median(samples) / full['medians']['primitive-control'],
        comparison_scope='The compact candidate is slower than the freshly matched primitive control. No matched speedup against the earlier cohort near 165 seconds is claimed; existing fast-profile observations are unchanged.',
        source_count_review=count, logical_source_count_status='separate-supplemental-proof-needs-explicit-binder-extension',
        required_work=foundation['required_work'], timing_boundary=foundation['timing_boundary'],
        runtime_environment=foundation['environment'], bytecode_observations=observations,
        bytecode_limit='Static instruction sites, not dynamic allocation counts; no claim that HotSpot retains or eliminates every boxed value/vector.',
        statistics_policy='Sample arrays and medians match exactly. The producer standard deviation is retained exactly and checked against recomputation with relative tolerance 1e-14 and no absolute tolerance, allowing Python rounding differences.',
        toolchains=dict(clojure=dict(version='Clojure 1.12.6; Temurin 25.0.4.1+1 ARM64; spec.alpha 0.5.238; core.specs.alpha 0.4.74')),
        archive_replay_limit='Archived replay verifies retained runtime/class manifests, source and full streams; ignored binary rehashing happens only during local-artifact preparation.',
        historical_data_preserved=True, new_observations=3, selection=plan['selection'],
        artifacts=[dict(path=path, sha256=digest) for path, digest in sorted(evidence.fingerprints.items()) if '/.build/' not in path])


def authorship_record(parent, results, evidence):
    record = copy.deepcopy(parent['authorship'])
    record.update(kind='ai-adapted', label='AI adapted · retained local predecessor', source_sha256=[SOURCE_SHA, SUPPORT_SHA],
        origin_status='unresolved', parent_programs=[PARENT],
        parent_sources=[dict(program_key=PARENT, relationship='local predecessor', **copy.deepcopy(ref)) for ref in parent['authorship'].get('retained_sources', [])],
        retained_sources=[dict(source_sha256=SOURCE_SHA, url='https://github.com/mech-lang/benchmarks/blob/' + SOURCE_REVISION + '/' + SOURCE)]
            + [copy.deepcopy(ref) for ref in parent['authorship'].get('retained_sources', []) if ref['source_sha256'] == SUPPORT_SHA],
        ai=dict(tool=AUTHOR_CONTEXT['tool'], models=[], model_family=AUTHOR_CONTEXT['model_family'], exact_model=None,
            status='family-identified-exact-model-unverified', matched_source_files=[SOURCE_SHA], total_source_files=2,
            evidence=[evidence['plan'], evidence['results']]),
        local_change_license=dict(status='suite-license', id='Apache-2.0', evidence='LICENSE',
                                 scope='New local changes only; inherited terms remain unresolved.'),
        evidence=[evidence['plan']['path'], evidence['results']['path'], evidence['ownership']['path']])
    return record


def bound_authorship(data, profile, root=ROOT):
    root = Path(root); results = load(root / RESULTS)
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    detail = profile.get('source_provenance_record') or {}
    require(profile.get('key') == KEY and profile.get('files') == [SOURCE_SHA, SUPPORT_SHA]
        and detail.get('kind') == 'suite-authored-optimization' and detail.get('source_sha256') == SOURCE_SHA
        and detail.get('original_program_key') == PARENT and detail.get('admission') == evidence['results']
        and detail.get('author_context') == AUTHOR_CONTEXT and results['author_context'] == AUTHOR_CONTEXT
        and results['status'] == 'RECONCILED' and results['plan'] == evidence['plan']
        and sha(root / SOURCE) == SOURCE_SHA
        and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest() == SOURCE_SHA, 'Unbound compact Clojure source/authorship')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT], results, evidence)


def append_catalog(before, root=ROOT):
    root = Path(root); results = load(root / RESULTS)
    require(results == reconcile(root, local_artifacts=False), 'Stale compact admission results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'] and 'clojure_compact_audit' not in before, 'Compact already admitted')
    data = copy.deepcopy(before); parent = before['programs'][PARENT]; control = before['programs'][CONTROL]
    require(parent['files'] == [PARENT_SHA, SUPPORT_SHA] and parent['loc'] == 109 and parent['physical_loc'] == 49, 'Historical compact parent changed')
    require(control['files'] == [CONTROL_SHA, SUPPORT_SHA] and control['loc'] == 111 and control['physical_loc'] == 52, 'Existing fast control source/count differs')
    result = results['programs'][0]; bench = next(b for b in data['benchmarks'] if b['key'] == 'nbody')
    require(result['loc'] >= bench['baseline_loc'] and result['median_seconds'] >= bench['baseline_seconds'], 'New global baseline needs separate review')
    require(SOURCE_SHA not in data['files'], 'Compact source already cataloged')
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    data['files'][SOURCE_SHA] = dict(name='compact_hot_aset.clj', path=SOURCE, archive_path=SOURCE, sha256=SOURCE_SHA, code=(root / SOURCE).read_text())
    row = copy.deepcopy(parent)
    for field in ('publication_record', 'timing_measurement', 'timing_correction', 'aliased_sample_source', 'source_alias_of', 'source_alias_note',
                  'loc_expansions', 'source_accounting', 'authorship', 'source_metrics', 'reproducibility', 'execution'):
        row.pop(field, None)
    runtime = load(root / FROZEN['runtime'][0])
    row.update(key=KEY, id=result['id'], receipt_key=result['id'], files=[SOURCE_SHA, SUPPORT_SHA], loc=109, physical_loc=49,
        seconds=result['median_seconds'], samples=result['samples_seconds'], timing_sd=result['sample_sd_seconds'],
        x=109 / bench['baseline_loc'], y=result['median_seconds'] / bench['baseline_seconds'],
        formatted_loc=None, formatted_x=None, formatted_loc_status='pending', formatted_loc_complete=False, formatted_loc_evidence={},
        report=RESULTS, report_sha256=evidence['results']['sha256'], source_report=evidence['ownership']['path'], loc_report=evidence['ownership']['path'],
        command=result['command'], runtime_arguments=['50000000'], build_command=result['build_command'], cwd=results['recorded_execution_root'],
        execution_mode='jvm-aot-classes-jit', binary_sha256=None, runtime_sha256=runtime['java']['sha256'],
        native_observations=3, timing_alias_of=None, sample_execution_metadata=result['sample_execution_metadata'],
        original_program_key=PARENT, retained_source_revision=SOURCE_REVISION, local_adaptation=True, distinct_optimization_claimed=True,
        candidate_role='expressiveness-candidate',
        source_provenance='Suite-authored adaptation using typed aset while retaining the compact Clojure pair, axis and vector structure; predecessor origin and inherited terms remain unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization', original_program_key=PARENT, source_sha256=SOURCE_SHA,
            admission=evidence['results'], origin_status='inherited-unresolved', author_context=AUTHOR_CONTEXT),
        runtime_policy='Clojure 1.12.6; Temurin 25.0.4.1+1 ARM64; direct-linking classes, fresh HotSpot JVM; ActiveProcessorCount=8 Xms64m Xmx8g G1GC',
        runtime_support='Unchanged generic clbg.support; no foreign n-body kernel or new workload helper.',
        runtime_environment=results['runtime_environment'], timing_boundary=results['timing_boundary'],
        timing_summary='Three independently timed fresh JVM processes, each completing 50 million steps. Slower than the primitive control measured alongside it. The earlier compact observations near 165 seconds and the existing fast profile remain unchanged. No matched comparison with that earlier cohort or global optimality is claimed.',
        matched_control=dict(program_key=CONTROL, report=evidence['full'], median_seconds=results['matched_candidate_medians']['primitive-control'],
            candidate_time_ratio=results['candidate_time_over_matched_control'], existing_profile_observations_unchanged=True),
        algorithm=dict(strict=True, status='required-work-reviewed', native_benchmark_kernel=False,
            reason='Original ordered pair and doseq axis/vector loops, floating groupings, delayed positions, momentum and both energies; exactly three hot setter heads changed.',
            full_work=results['required_work'], evidence=evidence['state']),
        source_accounting=dict(policy='application-loc-v1', application_loc=109, physical_loc=49, evidence=evidence['ownership']['path'],
            review_sha256=evidence['ownership']['sha256'], qualification='Approved retained Clojure owner count of 109 units and 49 physical lines for this exact source. Native logical source evidence requires its own binder.', files=[]),
        file_roles={SOURCE_SHA: dict(role='application', included_in_application_loc=True, normalized_loc=109, physical_loc=49),
                    SUPPORT_SHA: copy.deepcopy(parent['file_roles'][SUPPORT_SHA])},
        full_output_validation=dict(all_three_samples_passed=True, exact_reference_bytes=True, evidence=evidence['full']),
        chart_admission=dict(historical_reports_unchanged=True, **evidence),
        measured_backend=dict(key='clojure', execution='jit', label='Clojure (HotSpot)', verified=True,
            evidence=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'], command=result['command'], source_sha256=[SOURCE_SHA, SUPPORT_SHA],
                runtime_receipt=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'], field='/toolchains/clojure/version',
                    value=results['toolchains']['clojure']['version'], value_encoding='literal-saved-string'))))
    row['authorship'] = authorship_record(parent, results, evidence)
    data['programs'][KEY] = row; data['program_inventory'][KEY] = copy.deepcopy(row)
    group = next(g for g in bench['groups'] if g['language'] == 'clojure')
    require(group['fast'] == CONTROL, 'Existing fast endpoint differs')
    group['programs'].append(KEY)
    candidates = [data['programs'][key] for key in group['programs']]
    group['fast'] = min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))['key']
    group['small'] = min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))['key']
    require(group['fast'] == CONTROL and group['small'] == KEY, 'Unexpected compact/fast endpoint selection')
    for summary in data['reference_summary']:
        if summary['lang'] != 'clojure': continue
        groups = [g for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'clojure']
        for kind in ('fast', 'small'):
            selected = [data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind] = dict(x=statistics.geometric_mean(p['x'] for p in selected), y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*evidence.values(), *results['artifacts'], dict(path=SOURCE, sha256=SOURCE_SHA)]:
        data['archive_paths'][ref['path']] = ref['path']
    data['clojure_compact_audit'] = dict(schema='clojure-compact-catalog-extension.v1', appended_programs=[KEY], evidence=evidence,
        new_observations=3, source_files_added=1, old_profiles_unchanged=True, old_baselines_unchanged=True,
        prior_fast_endpoint_preserved=True, historical_cohorts_not_rematched=True)
    for pool in ('programs', 'program_inventory', 'files', 'archive_paths'):
        require(all(data[pool][key] == old for key, old in before[pool].items()), 'Historical ' + pool + ' changed')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-before-sha256'); parser.add_argument('--expected-prepared-sha256')
    args = parser.parse_args(); require(args.prepare != args.apply, 'Choose exactly one of prepare/apply')
    catalog = ROOT / 'data/benchmarks.json'
    if args.prepare:
        raw = catalog.read_bytes(); before_sha = hashlib.sha256(raw).hexdigest(); before = shared.load(catalog)
        shared.write(ROOT / PLAN, make_plan()); shared.write(ROOT / RESULTS, reconcile())
        after = append_catalog(before)
        require(sha(catalog) == before_sha, 'Canonical catalog changed during preparation')
        shared.write(ROOT / PREPARED, after)
        print(dict(before_sha256=before_sha, prepared_sha256=sha(ROOT / PREPARED), results_sha256=sha(ROOT / RESULTS), canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256, 'Apply needs both reviewed hashes')
        require(sha(catalog) == args.expected_before_sha256 and sha(ROOT / PREPARED) == args.expected_prepared_sha256, 'Reviewed catalog/preview identity differs')
        after = append_catalog(load(catalog)); require(encoded(after) == (ROOT / PREPARED).read_bytes(), 'Preview does not reproduce')
        require(sha(catalog) == args.expected_before_sha256, 'Canonical changed during replay')
        shared.write(catalog, after)
        print('Added independently timed compact Clojure source; existing fast and historical profiles retained.')


if __name__ == '__main__': main()
