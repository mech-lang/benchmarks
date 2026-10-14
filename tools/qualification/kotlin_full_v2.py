"""Additive required-work admission for the frozen Kotlin full90 sampler.

The two failed capture producers remain failed. Four observed subjects are
accepted through their exact additive reconciliation and independent reviews.
Timing, supervision, workload sizes and failure accounting are delegated to the
unchanged v1 implementation. Importing this module launches no native process.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'experiments/kotlin/full90-v2'
FROZEN = ROOT/'tools/qualification/kotlin_full.py'
FROZEN_SHA = '06f52fac0287b64ae0c231df8f8eb4a4793112a91efb01c5dde9b107c743c6e7'
FINAL_READER = ROOT/'tools/qualification/kotlin_single_entry_final.py'
FINAL_READER_SHA = '396cd2bc93fad28f9a24a93f3320cfab1888fdf60db0b8519a1496b00322e6c6'


def frozen(path, digest, name):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise AssertionError('Frozen prerequisite implementation changed')
    if name in sys.modules:
        raise AssertionError('Unexpected prerequisite module cache')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


full = frozen(FROZEN, FROZEN_SHA, 'kotlin_v2_frozen_full90')
final = frozen(FINAL_READER, FINAL_READER_SHA, 'kotlin_v2_frozen_final_capture')
require, read_ref, merge = full.require, full.read_ref, full.merge
SECOND, LAST = final.SECOND, final.PACKET
LAST_JOB = ROOT/'experiments/kotlin/dispatch-v1/owned-jobs/single-entry-final-pi-v1'


def ref(path, digest):
    return dict(path=str(path), sha256=digest)


CAPTURES = {
    'first': copy.deepcopy(full.FIRST_REFS),
    'remaining': {
        'plan': ref(SECOND/'plan-v1.json', final.SECOND_PLAN_SHA),
        'report': ref(SECOND/'run-v1/report.json', final.SECOND_REPORT_SHA),
        'terminal': ref(SECOND/'run-v1/terminal.json', final.SECOND_TERMINAL_SHA),
    },
    'final': {
        'plan': ref(LAST/'plan-v1.json', '42abaa1db26d19086a249a95745bc1d602e935591cd3b46e25ef1f254e1d39d8'),
        'report': ref(LAST/'run-v1/report.json', 'b9983050f1853687643a4ed9ce7c3c0f8d5cfe10894fd41296ef3dfb58e0534c'),
        'terminal': ref(LAST/'run-v1/terminal.json', '68363e9df0f137824cc40ad84dd6327824fab22edb65fffabe08e6092be07144'),
    },
}
REVIEWS = {
    'first_tree': ref(SECOND/'first-capture-reconciliation.md', '07a284e074401b545d112017ef01cb9078de0274ef84e874e1974b9ad770f4dc'),
    'remaining': ref(SECOND/'actual-instruction-review-evidence.json', 'ee747ebe79427e53b4b67f435074dc95b55c3298a4b00cf9aecc56dd19f80806'),
    'remaining_text': ref(SECOND/'actual-instruction-review.md', '8c54a1f182a18659278dd09d0165796f8d37e92ee04b819309d2733622fcc705'),
    'final': ref(LAST/'actual-instruction-review.json', 'e526002ee480dfbd45273d5fe791a17f81233d1b8c22e54763d75523c6a92bc0'),
    'final_text': ref(LAST/'actual-instruction-review.md', 'a7d794562c1037d09a265c2ec7b720f8dd70bd8cc88e342e7382ab281095d0e8'),
    'source': ref(ROOT/'experiments/kotlin/source-owner-review-v1/review.json', 'd1c246197cfe23e9c86df45171211f8e45352785701bc48082f1bca47cea746e'),
    'source_text': ref(ROOT/'experiments/kotlin/source-owner-review-v1/README.md', '20db15edf3a9677157285c038a2abec09c7fdf8ce290a8586c17d7662a2a1d76'),
}
DURABLE = ref(LAST_JOB/'terminal.json', 'ea207a000bc47dbda3d0da4e2efca39f298909ef96cec94d653462e3d43cb46b')
SPECIAL = dict(full.SPECIAL_CHECKS, pidigits={
    'single_entry_execution_path', 'both_general_divisions_before_every_comparison'})


def read_text_ref(reference, pins):
    path = full.valid_ref(reference)
    require(full.sha(path) == reference['sha256'], 'Independent review text changed')
    pins.update(merge(pins, {str(path): reference['sha256']}))


def check_final_durable(documents):
    command = [str(full.PYTHON), '-I', '-S', '-B', '-u', str(FINAL_READER), 'run',
               '--plan', CAPTURES['final']['plan']['path'], '--plan-sha256', CAPTURES['final']['plan']['sha256']]
    for name in ('request.json', 'launch.json', 'worker-started.json', 'command-started.json'):
        require(documents[name]['command'] == command and documents[name]['cwd'] == str(ROOT),
                'Final durable argv/cwd differs')
    terminal, started = documents['terminal.json'], documents['command-started.json']
    require(terminal['status'] == 'command-exited-zero-awaiting-report-review'
            and terminal['actual_command_started'] is True and type(terminal['exit_code']) is int
            and terminal['exit_code'] == 0 and terminal['qualification_granted'] is False
            and terminal['automatic_retry'] is False and terminal['stop_signals'] == []
            and terminal['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False
            and terminal['command_pid'] == started['command_pid'] == 62776
            and terminal['command_identity'] == started['command_identity'], 'Final durable terminal differs')
    identity = terminal['command_identity']; parts = identity['listing'].split(None, 7)
    require(identity['pid'] == 62776 and len(parts) == 8 and parts[:7] ==
            ['62776', '62772', 'Wed', 'Oct', '14', '07:26:30', '2026']
            and parts[7] == ' '.join(command), 'Final durable observed controller identity differs')
    worker = [str(full.PYTHON), '-B', '-u', str(ROOT/'experiments/kotlin/dispatch-v1/launch_durable.py'),
              '--worker', str(LAST_JOB), '--lease-fd', '3', '--go-fd', '4']
    for name in ('launch.json', 'worker-started.json', 'terminal.json'):
        identity = documents[name]['worker_identity']; parts = identity['listing'].split(None, 7)
        require(identity['pid'] == 62772 and len(parts) == 8 and parts[:7] ==
                ['62772', '62758' if name == 'launch.json' else '1', 'Wed', 'Oct', '14', '07:26:30', '2026']
                and parts[7] == ' '.join(worker), 'Final durable observed worker identity differs')
    require(documents['request.json']['automatic_retry'] is False
            and documents['launch.json']['automatic_retry'] is False
            and documents['launch.json']['detached_session'] is True
            and documents['request.json']['common_mutex_owned_by_target_command'] is True
            and documents['worker-started.json']['inherited_private_lease'] is True
            and documents['worker-started.json']['detached_session'] is True
            and documents['worker-started.json']['common_mutex_owned_by_target_command'] is True
            and all(documents[n]['qualification_granted'] is False for n in
                    ('request.json', 'launch.json', 'worker-started.json')), 'Final durable ownership policy differs')


def validate_final_metadata(plan, report, terminal, work_plan):
    require(plan['schema'] == 'kotlin-single-entry-final-plan-v1'
            and plan['controller_sha256'] == FINAL_READER_SHA
            and plan['ids'] == [final.FINAL_ID] and plan['reused_ids'] == final.REUSED_IDS
            and type(plan['planned_native_commands']) is int and plan['planned_native_commands'] == 1
            and type(plan['prior_native_commands_reused']) is int and plan['prior_native_commands_reused'] == 3
            and type(plan['automatic_retries']) is int and plan['automatic_retries'] == 0
            and plan['prescribed_inputs'] == {'binarytrees': 21, 'pidigits': 10000}
            and plan['profiles'] == [full.keyed(work_plan['profiles'])[final.FINAL_ID]], 'Final one-shot plan differs')
    require(report['schema'] == 'kotlin-single-entry-final-results-v1' and report['status'] == final.COMPLETE
            and report['plan'] == CAPTURES['final']['plan']['path']
            and report['plan_sha256'] == CAPTURES['final']['plan']['sha256']
            and report['active'] is None and report['prior_native_commands_reused'] == 3
            and type(report['native_processes_started']) is int and report['native_processes_started'] == 1
            and report['registered_native_commands'] == terminal['registered_native_commands'] ==
                [dict(id=final.FINAL_ID, pid=62778, pgid=62778)]
            and [row['id'] for row in report['profiles']] == [final.FINAL_ID]
            and set(report['commands']) == set(report['validated_command_artifacts']) == {final.FINAL_ID}
            and report['final_receipt_errors'] == report['process_receipt_errors'] == report['integrity_errors'] == [],
            'Final one-shot native closure differs')
    full.clean_terminal(terminal, CAPTURES['final']['report'], final.COMPLETE, 1)
    for document in (plan, report, terminal):
        require(all(document[k] is False for k in ('source_work_qualified', 'full_timings_qualified', 'chart_admission'))
                and all(type(document[k]) is int and document[k] == 0 for k in
                        ('subject_recompilations', 'diagnostic_compilations', 'benchmark_samples')),
                'Capture producer scope changed')


def capture_evidence(work_plan, pins, closures):
    groups = {name: {kind: read_ref(reference, pins) for kind, reference in refs.items()}
              for name, refs in CAPTURES.items()}
    expected = full.keyed(work_plan['profiles'])
    for name, group in groups.items():
        require(all(group['plan'][k] == work_plan[k] for k in ('java', 'stdlib', 'runtime_expected')),
                'Capture/runtime binding differs')
        require(all(row == expected[row['id']] for row in group['plan']['profiles']), 'Capture source/class row differs')
        pins.update(merge(pins, group['plan']['pins'], group['report']['pins']))
        full.add_artifacts(CAPTURES[name]['terminal'], group['terminal'], pins, closures)
    latest = groups['final']; plan, report = latest['plan'], latest['report']
    validate_final_metadata(plan, report, latest['terminal'], work_plan)
    _, prior = final.reconcile_prior(pins, False)
    require(prior == plan['prior_capture_reconciliation'] == report['prior_capture_reconciliation'],
            'Preserved failed producers or additive reconciliation changed')
    directory = Path(plan['output'])/final.FINAL_ID
    command = report['commands'][final.FINAL_ID]
    current = final.validate_capture(directory, plan['profiles'][0], plan,
                                     command['argv'], command['environment'], 62776)
    require(current == report['profiles'][0] == json.loads((directory/'validated.json').read_bytes())
            and current['capture'] == json.loads((directory/'capture-index.json').read_bytes())
            and final.base.snapshot(directory) == report['validated_command_artifacts'][final.FINAL_ID],
            'Final validated capture differs')
    final.closed_inventory(Path(plan['output']), latest['terminal'], pins, False)
    documents = {n: json.loads((LAST_JOB/n).read_bytes()) for n in
                 ('request.json', 'launch.json', 'worker-started.json', 'command-started.json')}
    documents['terminal.json'] = read_ref(DURABLE, pins)
    check_final_durable(documents)
    for path in LAST_JOB.iterdir():
        require(path.is_file() and not path.is_symlink(), 'Unexpected final durable artifact')
        pins.update(merge(pins, {str(path): full.sha(path)}))
    final.durable_inventory(LAST_JOB, pins, False)
    # Preserve the inventories of every durable owner through final full-run
    # reconciliation, including extra files added after native startup.
    durable_refs = [ref(final.previous.DURABLE, 'e550b132232a4fdb5cf87c46516a2444f267ff8faeb40dc8f7f8e52cf39a6814'),
                    ref(final.SECOND_JOB/'terminal.json', final.SECOND_DURABLE_SHA), DURABLE]
    for terminal_ref in durable_refs:
        directory = Path(terminal_ref['path']).parent
        final.durable_inventory(directory, pins, False)
        require(pins[terminal_ref['path']] == terminal_ref['sha256'], 'Durable terminal pin differs')
        artifacts = {p.name: dict(sha256=pins[str(p)], bytes=p.stat().st_size)
                     for p in directory.iterdir() if p.name != 'terminal.json'}
        closures.append(dict(directory=str(directory), terminal=terminal_ref, artifacts=artifacts))
    for name, reference in REVIEWS.items():
        if Path(reference['path']).suffix == '.json': read_ref(reference, pins)
        else: read_text_ref(reference, pins)
    return groups


def required_evidence(original):
    identity = original['id']
    paths = {str(full.WORK/'run-v2'/identity/name) for name in
             ('validated.json', 'summary.json', 'process.json', 'hotspot.xml', 'classes.log', 'native-libraries.txt')}
    paths.update(item['path'] for item in original['physical_inputs']+original['class_artifacts'])
    paths.update((original['retained_disassembly']['path'], REVIEWS['source']['path'], REVIEWS['source_text']['path']))
    if original['benchmark'] in ('binarytrees', 'pidigits'):
        group = 'first' if identity == full.FIRST_ID else 'final' if identity == final.FINAL_ID else 'remaining'
        directory = Path(CAPTURES[group]['terminal']['path']).parent/identity
        paths.update(str(directory/name) for name in ('process.json', 'hotspot.xml', 'stdout.bin', 'classes.log'))
        paths.add(REVIEWS['first_tree' if group == 'first' else 'final' if group == 'final' else 'remaining']['path'])
        if group != 'first' and identity != 'kotlin-pidigits-compact': paths.add(str(directory/'capture-index.json'))
    return paths


def validate_decisions(receipt, decisions, work_plan, pins):
    require(receipt['schema'] == 'kotlin-retained-compiled-work-qualified-v2'
            and receipt['status'] == 'all20-retained-required-work-qualified'
            and receipt['source_work_qualified'] is True and type(receipt['compiled_work_profiles']) is int
            and receipt['compiled_work_profiles'] == 20 and receipt['compiled_work'] == full.WORK_REFS
            and receipt['single_entry_captures'] == CAPTURES and receipt['independent_reviews'] == REVIEWS
            and all(type(receipt[k]) is int and receipt[k] == 0 for k in ('subject_recompilations', 'benchmark_samples'))
            and receipt['full_timings_qualified'] is receipt['full_size_feasibility_qualified'] is receipt['chart_admission'] is False,
            'Independent twenty-form required-work receipt required')
    require(decisions['schema'] == 'kotlin-independent-required-work-decisions-v2'
            and decisions['status'] == 'all20-retained-required-work-reviewed'
            and decisions['compiled_work'] == full.WORK_REFS and decisions['single_entry_captures'] == CAPTURES
            and decisions['independent_reviews'] == REVIEWS, 'Decision evidence chain differs')
    expected, reviewed, granted = full.keyed(work_plan['profiles']), full.keyed(decisions['profiles']), full.keyed(receipt['profiles'])
    for identity, original in expected.items():
        decision = reviewed[identity]
        require(granted[identity] == dict(id=identity, decision_id=identity, source_work_qualified=True),
                'Each retained form requires its own qualification')
        require(decision['source_work_qualified'] is True
                and decision['physical_inputs'] == original['physical_inputs']
                and decision['class_artifacts'] == original['class_artifacts']
                and decision['runtime_binding'] == {k: work_plan[k] for k in ('java', 'stdlib', 'runtime_expected')}
                and decision['retained_runtime_command'] == original['retained_runtime_command']
                and decision['runtime_environment'] == original['runtime_environment'], 'Decision source/class/runtime differs')
        checks = full.COMMON_CHECKS | SPECIAL.get(original['benchmark'], set())
        require(set(decision['checks']) == checks and all(v is True for v in decision['checks'].values()),
                'Required work or single-entry execution-path decision missing')
        require(type(decision['rationale']) is str and decision['rationale'].strip(), 'Direct work rationale missing')
        evidence = decision['evidence_pins']
        require(type(evidence) is dict and required_evidence(original) <= set(evidence)
                and all(pins.get(path) == digest for path, digest in evidence.items()), 'Unretained or missing decision evidence')
        if original['benchmark'] == 'pidigits':
            require(decision['single_entry_execution_path'] == 'interpreted-main'
                    and decision['numeric_runtime_division_count_proved'] is False,
                    'Pi path or numeric count claim differs from actual evidence')
    return expected


def prerequisites(work_ref):
    pins, closures = {str(FROZEN): FROZEN_SHA, str(FINAL_READER): FINAL_READER_SHA}, []
    qualification = read_ref(work_ref, pins)
    require(qualification.get('compiled_work') == full.WORK_REFS
            and qualification.get('single_entry_captures') == CAPTURES
            and qualification.get('independent_reviews') == REVIEWS, 'Exact native and independent review chain required')
    produced = {kind: read_ref(reference, pins) for kind, reference in full.WORK_REFS.items()}
    full.validate_work_producer(produced['plan'], produced['report'], produced['terminal'])
    pins.update(merge(pins, produced['plan']['pins'], produced['report']['pins']))
    full.add_artifacts(full.WORK_REFS['terminal'], produced['terminal'], pins, closures)
    capture_evidence(produced['plan'], pins, closures)
    decisions = read_ref(qualification['decisions'], pins)
    original = validate_decisions(qualification, decisions, produced['plan'], pins)
    counted = read_ref(ref(full.LOC, full.LOC_SHA), pins)
    require(counted['schema'] == 'kotlin-qualified-source-counts-v1'
            and counted['status'] == 'twenty-retained-canonical-source-counts-qualified'
            and counted['canonical_loc_qualified'] is True and counted['formatted_loc_qualified'] is False
            and counted['formatted_loc'] is None and counted['chart_admission'] is False,
            'Canonical counts required; formatted counts remain unqualified')
    source_plan = read_ref(ref(counted['source_plan'], counted['source_plan_sha256']), pins)
    terminal_ref = ref(counted['terminal'], counted['terminal_sha256'])
    source_terminal = read_ref(terminal_ref, pins)
    read_ref(ref(counted['report'], counted['report_sha256']), pins)
    for key in ('review_manifest', 'replay'): read_ref(ref(counted[key], counted[key+'_sha256']), pins)
    full.clean_terminal(source_terminal, ref(counted['report'], counted['report_sha256']),
                        'read-awaiting-canonical-owner-review', 2)
    require(source_terminal['reader_evidence_validated'] is True
            and len(source_terminal['available_evidence']) == counted['native_artifact_closure']['files'] == 192,
            'Native source-reader artifact closure differs')
    pins.update(merge(pins, source_plan['pins']))
    full.add_artifacts(terminal_ref, source_terminal, pins, closures)
    return original, full.keyed(counted['profiles']), counted['files'], produced['plan'], pins, closures


# Only prerequisite selection and adapter identity differ. These functions keep
# their original code objects and reference this privately loaded module state.
full.prerequisites = prerequisites
full.__file__ = str(Path(__file__).resolve())
full.HERE = HERE


if __name__ == '__main__':
    full.main()
