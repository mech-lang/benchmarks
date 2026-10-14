"""Fail-closed preparation and serial full90 measurement of retained Kotlin.

The qualification receipt consumed here does not exist yet. Its independent
decisions and successful remaining-three capture are mandatory. Definition-only
imports reuse the frozen full-workload sampler, output oracle and supervision.
No diagnostic, compiler, warmup wrapper or subject rebuild is timed or launched.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/kotlin/full90-v1'
HELPERS = ROOT / 'tools/qualification/elixir_full.py'
HELPERS_SHA = '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cold(path, expected, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Frozen helper source changed')
    require(name not in sys.modules, 'Unexpected cached helper module')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


helpers = cold(HELPERS, HELPERS_SHA, 'kotlin_full_shared_policy')
shared = helpers.shared
merge, new_json, verify = shared.merge, shared.new_json, shared.verify
isolated_failure = shared.isolated_failure
refresh_attempt_accounting = shared.refresh_attempt_accounting
preserve_wrapper_failure = shared.preserve_wrapper_failure
LOCK, PYTHON, PYTHON_SHA, BENCHES = helpers.LOCK, helpers.PYTHON, helpers.PYTHON_SHA, helpers.BENCHES
SUPERVISOR, SUPERVISOR_SHA = helpers.SUPERVISOR, helpers.SUPERVISOR_SHA
FULL, SAMPLER_PINS = helpers.FULL, helpers.SAMPLER_PINS
verify_lock, common_lock, held_lock = helpers.verify_lock, helpers.common_lock, helpers.held_lock
WORK = ROOT / 'experiments/kotlin/compiled-work-v1'
LOC = ROOT / 'experiments/kotlin/source-units-v1/qualified-source-counts.json'
LOC_SHA = '0f956d1dffcdcf688637b092004e32c1ce8818be16819871725a58ec7bd78e69'
WORK_REFS = {
    'plan': {'path': str(WORK/'plan-v2.json'), 'sha256': '4566d835d9dd264c57397ba52b6ec1e89e6f69fbbbec263187ff8030f7cd77bd'},
    'report': {'path': str(WORK/'run-v2/report.json'), 'sha256': '85060333d1a2287ecd0897d80c86d77712c8b7ddffc5a97a077a2ea4d62f3d24'},
    'terminal': {'path': str(WORK/'run-v2/terminal.json'), 'sha256': '38070e4fd756fbb4c8dc8888b3f87a5063b4f38313ca2c50971e714bca234b25'},
}
FIRST = ROOT / 'experiments/kotlin/single-entry-work-v1'
FIRST_REFS = {
    'plan': {'path': str(FIRST/'plan-v1.json'), 'sha256': '363f5a7af8a10e0dc93b88e3da3d371872ae0737e91d8f2a4591889d8885e88d'},
    'report': {'path': str(FIRST/'run-v1/report.json'), 'sha256': '5918aed5d40abb86e1c647dcad9e3664062be762f47a63d1e4d59d0730c52aea'},
    'terminal': {'path': str(FIRST/'run-v1/terminal.json'), 'sha256': 'e69e7f55f8ae63dfd6f516b82256625fd13cd8c53e9e359d5cef943266260097'},
}
WORK_CONTROLLER_SHA = '7a24ddefd83ca03e3135adc43334f91e935f944379e435da1d37be78a5bbecc2'
REMAINING_CONTROLLER_SHA = '1daa20808a0f023041ce72c6e5d7578430ac69fcea6ca3ff30f7c48e0ebc5297'
CAPTURE_SHA = 'baeb42da62b8bb4020fe019a2c0c22e47f4bb401852339d6c383b93ad76fd7a4'
REMAINING_IDS = ['kotlin-binarytrees-optimized', 'kotlin-pidigits-compact', 'kotlin-pidigits-optimized']
FIRST_ID = 'kotlin-binarytrees-compact'
REMAINING_COMPLETE = 'all3-additional-native-captures-awaiting-instruction-review'
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
ROLES = ['application', 'application-helper']
INJECTION_ENV = ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS',
                 'LD_PRELOAD', 'DYLD_INSERT_LIBRARIES', 'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH')
COMMON_CHECKS = {'required_work_preserved', 'retained_bytecode_and_source_binding', 'runtime_dependency_closure'}
SPECIAL_CHECKS = {
    'binarytrees': {'single_entry_compiled_versions', 'surviving_leaf_and_internal_allocations',
                    'fresh_disjoint_tree_construction', 'long_lived_graph_gc_roots'},
    'pidigits': {'single_entry_compiled_versions', 'both_general_divisions_before_every_comparison'},
}


def valid_ref(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'Exact path/hash reference required')
    path, digest = Path(ref['path']), ref['sha256']
    require(path.is_absolute() and '..' not in path.parts and str(path) == ref['path'], 'Unsafe metadata path')
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
            'Invalid SHA-256 reference')
    return path


def read_ref(ref, pins):
    path = valid_ref(ref)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], ('Metadata changed', str(path)))
    pins.update(merge(pins, {str(path): ref['sha256']}))
    return json.loads(raw)


def keyed(rows):
    result = {r['id']: r for r in rows}
    wanted = {f'kotlin-{b}-{v}' for b in BENCHES for v in ('compact', 'optimized')}
    require(len(rows) == len(result) == 20 and set(result) == wanted, 'Exact twenty retained Kotlin forms required')
    return result


def clean_terminal(terminal, report_ref, status, native_count):
    require(terminal['status'] == status and terminal['report_sha256'] == report_ref['sha256']
            and type(terminal['native_processes_started']) is int
            and terminal['native_processes_started'] == native_count
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
            'Native terminal is not closed under the original mutex')
    require(all(terminal[k] == [] for k in ('integrity_errors', 'artifact_errors', 'process_receipt_errors')),
            'Native prerequisite contains integrity, artifact or process errors')


def add_artifacts(terminal_ref, terminal, pins, closures):
    directory = valid_ref(terminal_ref).parent
    inventory = terminal['available_evidence']
    require(type(inventory) is dict and inventory and 'terminal.json' not in inventory,
            'Terminal must enumerate its pre-terminal artifact inventory')
    additions = helpers.artifact_pins(directory, inventory)
    pins.update(merge(pins, additions))
    closures.append(dict(directory=str(directory), terminal=copy.deepcopy(terminal_ref),
                         artifacts=copy.deepcopy(inventory)))


def validate_work_producer(plan, report, terminal):
    status = 'all20-bounded-work-witnesses-recorded-with-separate-open-gates'
    require(plan['schema'] == 'kotlin-retained-compiled-work-plan-v1'
            and plan['controller_sha256'] == WORK_CONTROLLER_SHA and plan['planned_native_commands'] == 21,
            'Retained compiled-work plan differs')
    require(report['schema'] == 'kotlin-retained-compiled-work-results-v1'
            and report['status'] == status and report['plan'] == WORK_REFS['plan']['path']
            and report['plan_sha256'] == WORK_REFS['plan']['sha256'] and report['active'] is None,
            'Retained compiled-work report is incomplete')
    clean_terminal(terminal, WORK_REFS['report'], status, 21)
    for key, value in [('native_processes_started', 21), ('diagnostic_compiler_processes_started', 1),
                       ('work_jvm_processes_started', 20), ('observed_main_invocations', 200000),
                       ('observed_main_returns', 200000)]:
        require(type(report[key]) is type(terminal[key]) is int and report[key] == terminal[key] == value,
                'Compiled-work count differs: '+key)
    for key in ('required_work_witnesses_qualified', 'subject_JIT_method_evidence_qualified',
                'actual_subject_runtime_dependency_closure_qualified', 'specified_case_coverage_qualified'):
        require(report[key] is terminal[key] is True, 'Compiled-work observation missing: '+key)
    require(all(report[k] == [] for k in ('integrity_errors', 'process_receipt_errors', 'missing_main_observations'))
            and terminal['missing_main_observations'] == [], 'Compiled-work reconciliation failed')
    require(report['source_work_qualified'] is terminal['source_work_qualified'] is False
            and report['subject_recompilations'] == report['benchmark_samples'] == 0,
            'Producer scope must remain unchanged; qualification is a separate receipt')
    require(set(keyed(plan['profiles'])) == set(keyed(report['profiles'])), 'Compiled-work form inventory differs')


def validate_remaining(refs, plan, report, terminal, first):
    require(set(refs) == {'plan', 'report', 'terminal', 'first_capture_reconciliation'},
            'Complete remaining-three references required')
    for ref in refs.values(): valid_ref(ref)
    directory = Path(refs['terminal']['path']).parent
    require(refs['report']['path'] == str(directory/'report.json')
            and refs['first_capture_reconciliation']['path'] == str(directory/'first-capture-reconciliation.json')
            and plan['output'] == str(directory),
            'Remaining capture report/reconciliation are outside the native artifact directory')
    require(plan['schema'] == 'kotlin-single-entry-remaining-plan-v1'
            and plan['controller_sha256'] == REMAINING_CONTROLLER_SHA and plan['capture_sha256'] == CAPTURE_SHA
            and plan['ids'] == REMAINING_IDS and plan['excluded_id'] == FIRST_ID
            and [r['id'] for r in plan['profiles']] == REMAINING_IDS
            and plan['planned_native_commands'] == 3 and plan['prior_native_commands_reused'] == 1
            and plan['automatic_retries'] == 0 and plan['prescribed_inputs'] == {'binarytrees': 21, 'pidigits': 10000},
            'Remaining capture plan differs or repeats the first tree')
    require(report['schema'] == 'kotlin-single-entry-remaining-results-v1' and report['status'] == REMAINING_COMPLETE
            and report['plan'] == refs['plan']['path'] and report['plan_sha256'] == refs['plan']['sha256']
            and report['active'] is None and [r['id'] for r in report['profiles']] == REMAINING_IDS
            and report['native_processes_started'] == 3 and report['prior_native_commands_reused'] == 1,
            'Successful remaining-three native report required')
    clean_terminal(terminal, refs['report'], REMAINING_COMPLETE, 3)
    require(report['remaining_receipt_errors'] == report['process_receipt_errors'] == report['integrity_errors'] == []
            and report['registered_native_commands'] == terminal['registered_native_commands']
            and [r['id'] for r in report['registered_native_commands']] == REMAINING_IDS
            and len({r['pid'] for r in report['registered_native_commands']}) == 3
            and all(type(r['pid']) is int and r['pid'] > 0 and r['pgid'] == r['pid']
                    for r in report['registered_native_commands'])
            and set(report['commands']) == set(report['validated_command_artifacts']) == set(REMAINING_IDS),
            'Remaining native process or artifact reconciliation is incomplete')
    require(first == plan['first_capture_reconciliation'] == report['first_capture_reconciliation']
            and first['schema'] == 'kotlin-first-single-entry-additive-reconciliation-v1'
            and first['id'] == FIRST_ID and first['original_status'] == 'failed'
            and first['original_error'] == 'Prescribed complete stdout differs'
            and first['original_plan_sha256'] == FIRST_REFS['plan']['sha256']
            and first['original_report_sha256'] == FIRST_REFS['report']['sha256']
            and first['original_terminal_sha256'] == FIRST_REFS['terminal']['sha256']
            and first['complete_subject_output_match'] is True and first['native_commands_reexecuted'] == 0
            and first['retained_vm_diagnostic'] == '[0.023s][warning][os] Loading hsdis library failed\n',
            'Saved first capture must be reused and separately reconciled')
    for document in (plan, report, terminal, first):
        require(document['source_work_qualified'] is False and document['benchmark_samples'] == 0,
                'Capture evidence cannot self-grant required-work qualification')
    require(all(r['complete_output_match'] is True for r in report['profiles']), 'Incomplete single-entry output')


def validate_decisions(receipt, decisions, work_plan, remaining_plan, pins, capture_refs):
    require(receipt['schema'] == 'kotlin-retained-compiled-work-qualified-v1'
            and receipt['status'] == 'all20-retained-required-work-qualified'
            and receipt['source_work_qualified'] is True and receipt['compiled_work_profiles'] == 20
            and receipt['compiled_work'] == WORK_REFS
            and receipt['subject_recompilations'] == receipt['benchmark_samples'] == 0
            and receipt['full_timings_qualified'] is receipt['chart_admission'] is False,
            'Independent compiled-work qualification receipt required')
    require(decisions['schema'] == 'kotlin-independent-required-work-decisions-v1'
            and decisions['status'] == 'all20-retained-required-work-reviewed'
            and decisions['compiled_work'] == receipt['compiled_work']
            and decisions['single_entry_remaining'] == receipt['single_entry_remaining'],
            'Independent decisions are not bound to the same native evidence')
    expected, qualified, reviewed = keyed(work_plan['profiles']), keyed(receipt['profiles']), keyed(decisions['profiles'])
    for identity, original in expected.items():
        decision, granted = reviewed[identity], qualified[identity]
        require(granted == dict(id=identity, decision_id=identity, source_work_qualified=True),
                'Every retained form needs its own independent required-work decision')
        require(decision['source_work_qualified'] is True
                and decision['physical_inputs'] == original['physical_inputs']
                and decision['class_artifacts'] == original['class_artifacts']
                and decision['runtime_binding'] == {k: work_plan[k] for k in ('java', 'stdlib', 'runtime_expected')}
                and decision['retained_runtime_command'] == original['retained_runtime_command']
                and decision['runtime_environment'] == original['runtime_environment'],
                'Decision changed source, generated classes or runtime policy')
        checks = COMMON_CHECKS | SPECIAL_CHECKS.get(original['benchmark'], set())
        require(set(decision['checks']) == checks and all(v is True for v in decision['checks'].values()),
                'Required native-work decision missing or unqualified')
        require(type(decision['rationale']) is str and decision['rationale'].strip(), 'Direct evidence rationale missing')
        evidence = decision['evidence_pins']
        require(type(evidence) is dict and evidence and all(pins.get(p) == digest for p, digest in evidence.items()),
                'Decision cites unretained or changed evidence')
        required = [str(WORK/'run-v2'/identity/name) for name in ('validated.json', 'process.json', 'hotspot.xml')]
        if identity in [FIRST_ID]+REMAINING_IDS:
            directory = (FIRST/'run-v1'/identity if identity == FIRST_ID
                         else Path(capture_refs['terminal']['path']).parent/identity)
            required += [str(directory/name) for name in ('process.json', 'hotspot.xml')]
            required.append(capture_refs['first_capture_reconciliation']['path'] if identity == FIRST_ID
                            else str(directory/'capture-index.json'))
        require(set(required) <= set(evidence), 'Decision omits actual native capture or compiled-work evidence')
    for row in remaining_plan['profiles']:
        original = expected[row['id']]
        require(row == original, 'Single-entry retained form differs from the qualified compiled-work form')
    return expected


def prerequisites(work_ref):
    pins, closures = {}, []
    qualification = read_ref(work_ref, pins)
    require(qualification.get('compiled_work') == WORK_REFS, 'Exact clean21 compiled-work evidence required')
    produced = {kind: read_ref(ref, pins) for kind, ref in WORK_REFS.items()}
    validate_work_producer(produced['plan'], produced['report'], produced['terminal'])
    refs = qualification['single_entry_remaining']
    require(set(refs) == {'plan', 'report', 'terminal', 'first_capture_reconciliation'}, 'Missing remaining-three evidence')
    remaining = {kind: read_ref(ref, pins) for kind, ref in refs.items()}
    validate_remaining(refs, remaining['plan'], remaining['report'], remaining['terminal'],
                       remaining['first_capture_reconciliation'])
    original_first = {kind: read_ref(ref, pins) for kind, ref in FIRST_REFS.items()}
    require(original_first['report']['status'] == original_first['terminal']['status'] == 'failed'
            and original_first['report']['error'] == 'Prescribed complete stdout differs'
            and original_first['report']['native_processes_started'] == 1,
            'Original failed first capture must remain intact')
    for group, group_refs in ((produced, WORK_REFS), (remaining, refs), (original_first, FIRST_REFS)):
        pins.update(merge(pins, group['plan']['pins'], group['report']['pins']))
        add_artifacts(group_refs['terminal'], group['terminal'], pins, closures)
    for key in ('java', 'stdlib', 'runtime_expected'):
        require(produced['plan'][key] == remaining['plan'][key] == original_first['plan'][key],
                'Single-entry and compiled-work runtime bindings differ')
    decisions = read_ref(qualification['decisions'], pins)
    original = validate_decisions(qualification, decisions, produced['plan'], remaining['plan'], pins, refs)
    require(original_first['plan']['profiles'][0] == original[FIRST_ID], 'First capture retained form differs')
    counted = read_ref(dict(path=str(LOC), sha256=LOC_SHA), pins)
    require(counted['schema'] == 'kotlin-qualified-source-counts-v1'
            and counted['status'] == 'twenty-retained-canonical-source-counts-qualified'
            and counted['canonical_loc_qualified'] is True and counted['formatted_loc_qualified'] is False
            and counted['formatted_loc'] is None and counted['chart_admission'] is False,
            'Qualified canonical counts required; formatter evidence must not be invented')
    source_plan = read_ref(dict(path=counted['source_plan'], sha256=counted['source_plan_sha256']), pins)
    terminal_ref = dict(path=counted['terminal'], sha256=counted['terminal_sha256'])
    source_terminal = read_ref(terminal_ref, pins)
    read_ref(dict(path=counted['report'], sha256=counted['report_sha256']), pins)
    for key in ('review_manifest', 'replay'):
        read_ref(dict(path=counted[key], sha256=counted[key+'_sha256']), pins)
    clean_terminal(source_terminal, dict(path=counted['report'], sha256=counted['report_sha256']),
                   'read-awaiting-canonical-owner-review', 2)
    require(source_terminal['reader_evidence_validated'] is True
            and len(source_terminal['available_evidence']) == counted['native_artifact_closure']['files'] == 192,
            'Native source-reader closure differs')
    pins.update(merge(pins, source_plan['pins']))
    add_artifacts(terminal_ref, source_terminal, pins, closures)
    return original, keyed(counted['profiles']), counted['files'], produced['plan'], pins, closures


def candidate(original, counted, files, runtime, pins):
    identity, bench = original['id'], original['benchmark']
    require(counted['id'] == identity == f"kotlin-{bench}-{original['variant']}", 'Retained identity differs')
    sources = original['physical_inputs']
    require([s['role'] for s in sources] == ROLES and all(s['counted'] is True for s in sources),
            'Both authored source/helper inputs must be counted')
    counted_files = [files[key] for key in counted['inputs']]
    require([(s['path'], s['sha256'], s['role']) for s in sources] ==
            [(s['source'], s['source_sha256'], s['role']) for s in counted_files], 'Canonical source linkage differs')
    for aggregate in ('canonical_loc', 'original_physical_loc'):
        require(type(counted[aggregate]) is int and counted[aggregate] > 0
                and counted[aggregate] == sum(f[aggregate] for f in counted_files), 'Source total differs')
    require(counted['canonical_loc_qualified'] is True and counted['formatted_loc_qualified'] is False
            and counted['formatted_loc'] is None, 'Canonical/formatter qualification changed')
    env = original['runtime_environment']
    options = FLAGS + ['-Duser.home='+env['HOME'], '-Djava.io.tmpdir='+env['TMPDIR'].rstrip('/')]
    command = [runtime['java']]+options+['-cp', original['classes']+os.pathsep+runtime['stdlib'],
                                        'clbg.'+bench+'.MainKt', '{n}']
    require(original['retained_runtime_command'] == command and original['main_owner'] == command[-2],
            'Only the retained direct-main command is allowed; no diagnostics or warmup')
    require(env['JAVACMD'] == runtime['java'] and env['JAVA_OPTS'] == ' '.join(options)
            and env['JAVA_HOME'] == str(Path(runtime['java']).parent.parent)
            and env['PATH'] == str(Path(runtime['java']).parent)+':/usr/bin:/bin:/usr/sbin:/sbin'
            and all(env[k] == '' for k in ('CLASSPATH', 'KOTLIN_RUNNER', 'KOTLIN_COMPILER', 'KOTLIN_TOOL'))
            and not any(k in env for k in INJECTION_ENV), 'Retained JVM environment policy changed')
    artifacts = original['class_artifacts']
    require(artifacts and len({a['relative_path'] for a in artifacts}) == len(artifacts), 'Duplicate or empty retained classes')
    for item in artifacts:
        part = Path(item['relative_path'])
        require(not part.is_absolute() and '..' not in part.parts
                and item['path'] == str(Path(original['classes'])/part), 'Generated class escaped retained classpath')
    require(all(pins.get(a['path']) == a['sha256'] for a in sources+artifacts)
            and runtime['java'] in pins and runtime['stdlib'] in pins, 'Source/class/JVM dependency missing from closure')
    return dict(id=identity, key=identity, benchmark=bench, variant=original['variant'], language='kotlin',
        source=sources[0]['path'], source_sha256=sources[0]['sha256'], binary=runtime['java'],
        binary_sha256=pins[runtime['java']], command=command, cwd=str(Path(sources[0]['path']).parent),
        runtime_environment=copy.deepcopy(env), maximum_workers=8, physical_inputs=copy.deepcopy(sources),
        class_artifacts=copy.deepcopy(artifacts), classes=original['classes'], stdlib=runtime['stdlib'],
        class_owner_names=copy.deepcopy(original['class_owner_names']), alias_of=original['alias_of'],
        optimization_claim=False, source_work_qualified=True, canonical_loc_qualified=True,
        formatted_loc_qualified=False, loc=counted['canonical_loc'], canonical_loc=counted['canonical_loc'],
        formatted_loc=None, physical_loc=counted['original_physical_loc'],
        memory_policy='Retained -Xms64m -Xmx8g G1; ActiveProcessorCount=8; default tiered compilation',
        runtime_policy_changes=[], diagnostic_flags=[], chart_admission=False)


def controls(pins):
    result = helpers.controls(pins)
    for bench, row in result.items(): row['key'] = bench+':kotlin-full-study:mech-control'
    return result


def schedule_for(manifests):
    require(set(manifests) == set(BENCHES), 'Exactly ten full-workload manifests required')
    schedule = []
    for bench in BENCHES:
        manifest = manifests[bench]
        ids = [f'kotlin-{bench}-compact', f'kotlin-{bench}-optimized', 'mech-aot-control']
        rows = manifest['profiles']
        require([r['id'] for r in rows] == ids and [r['language'] for r in rows] == ['kotlin', 'kotlin', 'mech']
                and all(r['benchmark'] == bench for r in rows), 'Full cohort membership/order changed')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        require(manifest['orders'] == orders and type(manifest['samples']) is int and manifest['samples'] == 3,
                'Exactly three balanced rounds required')
        keys = {r['id']: r['key'] for r in rows}
        schedule.extend((bench, order['round'], identity, keys[identity]) for order in orders for identity in order['profiles'])
    require(len(schedule) == len(set(schedule)) == 90 and len({s[3] for s in schedule}) == 30, 'Full90 schedule differs')
    return schedule


def build_draft(output, work_ref):
    original, counted, files, runtime, pins, closures = prerequisites(work_ref)
    control_rows = controls(pins)
    manifests = {}
    for bench in BENCHES:
        rows = [candidate(original[i], counted[i], files, runtime, pins)
                for i in (f'kotlin-{bench}-compact', f'kotlin-{bench}-optimized')]+[control_rows[bench]]
        ids = [r['id'] for r in rows]
        size, count, digest = FULL[bench]
        manifests[bench] = dict(benchmark=bench, profiles=rows, samples=3, size=size, canonical_full_workload=True,
            orders=[dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)], timeout_seconds=21600,
            supervisor_timeout_seconds=22200, maximum_rss_mib=10240,
            full_output_reference=None if bench == 'nbody' else dict(bytes=count, sha256=digest),
            shared_timing_lock=str(LOCK), no_automatic_retry=True, chart_admission=False,
            retained_subject_compilation_outside_timer=True, runtime_and_class_loading_inside_timer=True,
            runtime_JIT_inside_timer=True, direct_main_invocations_per_sample=1)
    pins = merge(pins, SAMPLER_PINS, {str(HELPERS): HELPERS_SHA, str(helpers.SHARED): helpers.SHARED_SHA,
        str(SUPERVISOR): SUPERVISOR_SHA, str(PYTHON.resolve()): PYTHON_SHA,
        str(Path(__file__).resolve()): sha(__file__), str(HERE/'README.md'): sha(HERE/'README.md')})
    return dict(schema='kotlin-qualified-retained-full90-v1', status='draft-metadata-only-not-executable',
        pins_verified=False, controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
        repository=str(ROOT), output=str(Path(output).resolve()), qualified_work=copy.deepcopy(work_ref),
        qualified_source_counts=dict(path=str(LOC), sha256=LOC_SHA), source_work_profiles=20,
        canonical_loc_profiles=20, formatted_loc_profiles=0, formatted_loc_qualified=False,
        retained_bounded_cases=186, compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0,
        count_replays=0, new_native_probes=0, original_files_mutated=False, samples=3,
        kotlin_samples=60, matched_mech_samples=30, full_processes=90,
        schedule=[list(s) for s in schedule_for(manifests)], manifests=manifests, pins=pins,
        prerequisite_artifact_closures=closures, shared_timing_lock=str(LOCK), common_mutex_inode=79859134,
        continuous_common_mutex=True, no_automatic_retry=True, full_timings_qualified=False, chart_admission=False,
        timing_policy='Fresh direct JVM process including startup, retained class loading, tiered JIT, full input, '
                      'all work, complete output and shutdown; subject compilation, pin hashing and output validation excluded')


def validate_plan(plan, prepared=False):
    expected = build_draft(plan['output'], plan['qualified_work'])
    if prepared: expected.update(status='prepared-awaiting-independent-review', pins_verified=True)
    require(plan == expected, 'Plan differs from the exact qualified prerequisites, cohort, closure, schedule or policy')


def checked_runtime():
    helpers.checked_runtime()
    require(not any(key in os.environ for key in INJECTION_ENV), 'Ambient JVM/native injection variables must be absent')


def qualified_sample(attempt, manifest, row, fingerprint):
    shared.qualified_sample(attempt, manifest, row, fingerprint)
    require(attempt.get('stderr') == '', 'Qualified full sample requires empty native stderr')


def load_measurement():
    guard, harness = helpers.load_measurement()
    require(not any(key in harness.compact.ENV for key in INJECTION_ENV), 'Sampler inherited an unqualified JVM environment')
    return guard, harness


def verify_artifact_inventories(closures):
    for closure in closures:
        directory = Path(closure['directory'])
        require(str(directory/'terminal.json') == closure['terminal']['path'], 'Wrong terminal inventory path')
        paths = list(directory.rglob('*'))
        require(not directory.is_symlink() and not any(p.is_symlink() for p in paths), 'Prerequisite artifact symlink appeared')
        actual = {str(p.relative_to(directory)): p.stat().st_size for p in paths if p.is_file()}
        require(set(actual) == set(closure['artifacts']) | {'terminal.json'}, 'Prerequisite artifact inventory changed')
        require(all(actual[name] == item['bytes'] for name, item in closure['artifacts'].items()),
                'Prerequisite artifact size changed')


def check_execution_inputs(plan, harness):
    helpers.check_execution_inputs(plan, harness)
    verify_artifact_inventories(plan['prerequisite_artifact_closures'])
    for manifest in plan['manifests'].values():
        for row in manifest['profiles']:
            if row['language'] != 'kotlin': continue
            directory = Path(row['classes'])
            paths = list(directory.rglob('*'))
            require(not directory.is_symlink() and not any(p.is_symlink() for p in paths)
                    and {str(p.relative_to(directory)) for p in paths if p.is_file()} ==
                    {a['relative_path'] for a in row['class_artifacts']}, 'Retained classpath inventory changed')
            require(all(Path(row['runtime_environment'][name]).is_dir()
                        for name in ('HOME', 'TMPDIR', 'XDG_CONFIG_HOME')), 'Retained JVM working directory missing')


def draft(args):
    require(not args.plan.exists() and not args.output.exists(), 'Fresh draft and output paths required')
    work_ref = dict(path=str(args.qualified_work.resolve()), sha256=args.qualified_work_sha256)
    plan = build_draft(args.output, work_ref)
    require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan cannot lie inside the fresh output')
    new_json(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_executions=0, pins_verified=False)), flush=True)


def prepare(args):
    require(not args.plan.exists(), 'Prepared plan must be new')
    with common_lock() as lock:
        checked_runtime()
        pins = {}
        plan = read_ref(dict(path=str(args.draft.resolve()), sha256=args.draft_sha256), pins)
        validate_plan(plan)
        require(not Path(plan['output']).exists() and not args.plan.resolve().is_relative_to(Path(plan['output'])),
                'Fresh output must remain absent and separate from its plan')
        verify(plan['pins'])
        _, harness = load_measurement()
        check_execution_inputs(plan, harness)
        plan.update(status='prepared-awaiting-independent-review', pins_verified=True)
        verify_lock(lock)
        new_json(args.plan, plan)
        print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), full_processes=90, native_executions=0)), flush=True)


def run_locked(args, live_lock):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan, prepared=True)
    output = Path(plan['output'])
    require(not output.exists(), 'No overwrite, implicit resume, or repeated sample')
    output.parent.mkdir(parents=True,exist_ok=True)
    # The suite lease also excludes another cohort using a different output.
    lease_path = ROOT / 'experiments/kotlin/kotlin-full90.owner.lock'
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with held_lock(live_lock) as lock:
            verify(plan['pins'])
            guard,harness = load_measurement()
            check_execution_inputs(plan, harness)
            supervisor = cold(SUPERVISOR, SUPERVISOR_SHA, 'kotlin_full90_independent_supervisor')
            verify_lock(lock)
            schedule = schedule_for(plan['manifests'])
            require([list(slot) for slot in schedule] == plan['schedule'], 'Reviewed schedule changed')
            pins = merge(plan['pins'],{str(args.plan.resolve()):args.plan_sha256})
            manifests = {bench:dict(manifest,pins=pins) for bench,manifest in plan['manifests'].items()}
            for bench,manifest in manifests.items():
                require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                        and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                        and manifest['maximum_rss_mib'] == 10240,
                        'Workload or resource policy changed')
            output.mkdir()
            guard.OUT,guard.REPORT = output,output/'report.json'
            harness.install_interrupt_handlers()
            rows = {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],measurement_status='pending')
                    for manifest in manifests.values() for row in manifest['profiles']}
            require(len(rows) == 30,'Full cohort changed')
            report = dict(status='running',started_at=guard.now(),supervisor=guard.identity(os.getpid()),
                plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,programs=rows,attempts=[],active=None,
                benchmark_order=BENCHES,completed_benchmarks=[],sample_count=3,full_performance_runs=0,
                skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=str(LOCK),
                source_work_profiles=20,canonical_loc_profiles=20,formatted_loc_profiles=0,
                planned_kotlin_samples=60,planned_matched_mech_samples=30,full_timings_qualified=False,
                chart_admission=False,no_automatic_retry=True)
            refresh_attempt_accounting(report)
            guard.save(guard.REPORT,report)
        try:
            for bench,round_index,identifier,key in schedule:
                row,manifest = rows[key],manifests[bench]
                if row.get('full_failure'):
                    report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                    guard.save(guard.REPORT,report)
                    continue
                with held_lock(live_lock) as lock:
                    verify(pins)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    check_execution_inputs(plan, harness)
                    verify_lock(lock)
                    print('KOTLIN FULL',bench,round_index,identifier,manifest['size'],flush=True)
                    try:
                        attempt = supervisor.one_attempt(guard,harness,row,manifest,report,round_index,lock.fileno())
                    except BaseException as error:
                        preserve_wrapper_failure(guard,report,row,round_index,error)
                        raise
                    verify_lock(lock)
                    report['attempts'].append(attempt)
                    report['active']=None
                    row['attempts'].append(attempt['attempt'])
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    # Frozen sampler and supervisor artifacts are never edited.
                    raw = json.loads(Path(attempt['result_path']).read_bytes())
                    supervised = json.loads(Path(attempt['supervisor_result_path']).read_bytes())
                    require(supervised == attempt and all(attempt.get(k) == v for k,v in raw.items()),
                            'Raw sampler and supervised records differ')
                    if attempt['qualified']:
                        qualified_sample(attempt,manifest,row,harness.execution_fingerprint(row))
                        row['samples_seconds'].append(attempt['seconds'])
                        row['sample_validation'].append(attempt['validation'])
                        row['measurement_status']='measured' if len(row['samples_seconds']) == 3 else 'partial'
                    elif isolated_failure(guard,attempt):
                        row['measurement_status']='failed-full-workload'
                        row['full_failure']=dict(attempt)
                        report['isolated_failed_profiles'].append(key)
                    else:
                        row['measurement_status']='stopped-unqualified'
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')
                group = [rows[r['key']] for r in manifest['profiles']]
                if all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in group):
                    control = next(r for r in group if r['language']=='mech')
                    for r in group:
                        if not r.get('full_failure'):
                            r.update(median_seconds=statistics.median(r['samples_seconds']),
                                     sample_stdev_seconds=statistics.stdev(r['samples_seconds']))
                    for r in group:
                        r['time_x_mech'] = (r['median_seconds']/control['median_seconds']
                                           if not r.get('full_failure') and not control.get('full_failure') else None)
                        r['matched_mech_control']=control['key']
                        r['matched_mech_source_sha256']=control['source_sha256']
                    if bench not in report['completed_benchmarks']:
                        report['completed_benchmarks'].append(bench)
                    guard.save(guard.REPORT,report)
            require(len(report['attempts'])+len(report['skipped_failed_profile_slots']) == 90
                    and len(report['completed_benchmarks']) == 10,'Incomplete full90 accounting')
            require(report['full_performance_runs'] == len(report['attempts']),'Native attempt accounting mismatch')
            report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                          finished_at=guard.now())
        except BaseException as error:
            report.update(status='stopped-unqualified',finished_at=guard.now(),error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
            (output/'error.log').write_text(traceback.format_exc())
            raise
        finally:
            with held_lock(live_lock) as lock:
                errors=[]
                for path,expected in pins.items():
                    try:
                        require(sha(path)==expected,'Pinned bytes changed')
                    except BaseException as error:
                        errors.append(dict(path=path,error=str(error) or type(error).__name__,error_type=type(error).__name__))
                try:
                    check_execution_inputs(plan, harness)
                except BaseException as error:
                    errors.append(dict(path='<prerequisite-and-retained-class-inventories>',
                        error=str(error) or type(error).__name__, error_type=type(error).__name__))
                report['pins_unchanged_at_end'] = not errors
                refresh_attempt_accounting(report)
                if errors:
                    report['status_before_terminal_integrity_failure'] = report['status']
                    report['status'] = 'failed-terminal-integrity'
                    report['terminal_integrity_errors'] = errors
                verify_lock(lock)
                guard.save(guard.REPORT,report)
                available={str(p):sha(p) for p in output.rglob('*') if p.is_file()}
                new_json(output/'terminal.json',dict(status='failed-terminal-integrity' if errors else report['status'],
                    report=str(guard.REPORT),report_sha256=sha(guard.REPORT),prerequisite_pins=pins,
                    available_evidence_pins=available,integrity_errors=errors,common_mutex_held=True,
                    full_performance_runs=report['full_performance_runs'],saved_attempts=len(report['attempts']),
                    registered_native_attempts=report['registered_native_attempts'],
                    native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
                    qualified_samples=report['qualified_samples'],
                    skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
                    compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,
                    repeated_completed_samples=0,original_files_mutated=False,full_timings_qualified=False,chart_admission=False))
                verify_lock(lock)
                require(not errors,'Terminal integrity failed; actual attempts preserved')


def run(args):
    # A single inherited descriptor remains locked through environment waits,
    # all 90 slots, every cleanup and the final evidence/terminal write.
    with common_lock() as lock:
        run_locked(args, lock)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    source = modes.add_parser('draft', help='Require independently qualified metadata; no full closure hashing or native run')
    source.add_argument('--qualified-work', type=Path, required=True)
    source.add_argument('--qualified-work-sha256', required=True)
    source.add_argument('--plan', type=Path, required=True)
    source.add_argument('--output', type=Path, required=True)
    prep = modes.add_parser('prepare', help='Verify exact reviewed draft and closures under the common mutex')
    prep.add_argument('--draft', type=Path, required=True)
    prep.add_argument('--draft-sha256', required=True)
    prep.add_argument('--plan', type=Path, required=True)
    execute = modes.add_parser('run', help='Run only the reviewed prepared plan under a durable owner')
    execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    {'draft': draft, 'prepare': prepare, 'run': run}[args.mode](args)


if __name__ == '__main__':
    main()
