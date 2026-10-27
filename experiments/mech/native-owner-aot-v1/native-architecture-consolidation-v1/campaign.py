"""Shared evidence checks for the two separately predeclared campaigns."""
import hashlib
import math
import subprocess
from pathlib import Path
from study import (HERE, CODE_DIR, ROOT, RETAINED, STUDY_ID, process, read, source_state,
                   subjects, inputs, check_native, build_receipt_path, runtime_environment)
import wide_slot
import artifact_equivalence

COMPLETE = 'all-96-complete-processes-output-counters-pins-and-cleanup-verified'
CONTROLLER = 'experiments/janet/knucleotide-bytes-v1/process.py'
CORRECTNESS_TESTS = {
    'native-unit', 'native-facts', 'native-lines', 'worker-credit', 'native-catalog',
    'scalar-integration', 'program-integration', 'scalar-unit', 'native-source-lowering',
    'source-contracts', 'source-applications', 'source-assignment', 'benchmark-policy-unit',
    'resident-factory-attachment', 'native-collection-templates', 'native-set-conversion',
    'native-kind-conversion', 'native-annotation-conversion', 'source-set-conversion',
    'source-kind-conversion', 'source-annotation-conversion', 'native-semantics',
    'iteration-proofs', 'program-runtime-unit', 'program-prefix-unit',
    'program-prefix-window-unit', 'program-prefix-retention-unit',
    'native-source-integration', 'canonical-host-reference', 'canonical-cli-byte-contracts',
    'maintained-hosted-runner',
}
CORRECTNESS = CORRECTNESS_TESTS | {
    'none-check', 'none-tree', 'scalar-runtime-check', 'scalar-runtime-tree',
    'program-runtime-check', 'program-runtime-tree', 'host-runtime-check',
    'host-runtime-tree', 'scalar-compiler-check', 'program-compiler-check',
    'format', 'unsafe', 'unsafe-contract', 'runtime-factory-safety',
    'build-analysis-layout', 'warning-policy', 'module-layout', 'planning-quarantine',
    'workflow-contracts', 'process-contracts',
}
LINKED_PROCESS_TESTS = {
    'canonical-hosted-linked': 'linked::complete_original_and_decoded_knucleotide_linked_processes_are_secured_and_pinned',
    'canonical-policy-linked': 'linked::benchmark::complete_original_and_decoded_knucleotide_same_binary_policy_controls',
    'canonical-scalar-linked': 'linked_canonical_artifact_scalar_applications_are_typed_bounded_and_atomic',
    'canonical-cast-linked': 'linked_canonical_artifact_cast_applications_preserve_checked_boundaries',
    'canonical-match-linked': 'linked_canonical_match_applications_are_lazy_bounded_and_atomic',
    'canonical-iteration-linked': 'linked_qualification::one_linked_iteration_executable_preserves_exact_typed_loops_and_denials',
    'canonical-program-linked': 'linked_qualification::linked_managed_programs_preserve_canonical_outputs_errors_and_denials',
    'native-source-host-linked': 'one_linked_executable_runs_secure_and_trusted_without_rebuilding',
    'native-source-control-linked': 'one_linked_control_executable_preserves_signed_machine_outputs',
    'native-source-stdin-linked': 'one_linked_stdin_executable_preserves_unicode_snapshots_and_launch_policy',
    'canonical-resident-cli-linked': 'linked_canonical_cli_arguments_and_stdin_finish_without_drivers',
}
PROCESS_TESTS = set(LINKED_PROCESS_TESTS) | {
    'canonical-cli-unit-contracts', 'canonical-cli-public-qualification',
    'canonical-hosted-contracts', 'canonical-policy-kernel', 'canonical-policy-contracts',
}
TEST_MINIMUMS = dict.fromkeys(CORRECTNESS_TESTS | PROCESS_TESTS, 1)
TEST_MINIMUMS.update({
    'canonical-cli-unit-contracts': 5, 'canonical-cli-public-qualification': 3,
    'canonical-policy-kernel': 13, 'benchmark-policy-unit': 13,
})
# Multi-package filters and the maintained runner's empty doc-test target are
# legitimate companions. An empty selected integration suite is not.
EMPTY_COMPANION_STAGES = {'native-unit', 'native-catalog', 'maintained-hosted-runner'}


def contained(path):
    candidate = (HERE / path).resolve()
    assert candidate.is_relative_to(HERE.resolve()), path
    return candidate


def evidence(ref):
    path = contained(ref['path'])
    assert process.sha(path) == ref['sha256'], path
    return read(path)


def required_controller_paths():
    return {str((CODE_DIR / name).relative_to(ROOT)) for name in
            ['measure.py', 'analyze.py', 'qualify.py', 'campaign.py', 'study.py', 'wide_slot.py', 'artifact_equivalence.py']} | {CONTROLLER}


def check_controllers(plan):
    assert required_controller_paths() <= set(plan['controller_pins'])
    for path, digest in plan['controller_pins'].items():
        assert not Path(path).is_absolute() and (ROOT / path).resolve().is_relative_to(ROOT.resolve()), path
        assert process.sha(ROOT / path) == digest, path


def stages(rows, head, required):
    assert len({row['stage'] for row in rows}) == len(rows)
    assert required <= {row['stage'] for row in rows}
    for row in rows:
        name = row['stage']
        assert row['head'] == head and row['exit_code'] == 0, name
        counts = []
        for count in row['counts']:
            assert len(count) == 3, name
            assert all(type(value) is int or isinstance(value, str) and value.isdecimal()
                       for value in count), name
            values = tuple(map(int, count))
            assert all(value >= 0 for value in values), name
            counts.append(values)
        if counts:
            assert sum(count[0] for count in counts) > 0, name
            assert all(count[1] == 0 for count in counts), name
        if name in TEST_MINIMUMS:
            assert sum(count[0] for count in counts) >= TEST_MINIMUMS[name], name
            if name not in EMPTY_COMPANION_STAGES:
                assert all(count[0] > 0 for count in counts), name
        if name in LINKED_PROCESS_TESTS:
            command = row['command']
            assert '--list' not in command and '--no-run' not in command, name
            assert command.count('--ignored') == command.count('--exact') == 1, name
            assert command[command.index('--exact') + 1] == LINKED_PROCESS_TESTS[name], name
            assert counts == [(1, 0, 0)], name
    return {row['stage']: row for row in rows}


def prerequisites(plan):
    assert plan['study_id'] == STUDY_ID
    assert plan['status'] == 'frozen-before-first-primary-sample'
    targets, pins, f, i = subjects()
    assert source_state() == f['source'] and not f['source']['status']
    assert plan['final_compiler_source'] == f['source']['commit']
    assert plan['implementation_base'] == i['source']['commit'] and not i['source']['status']
    assert source_state(Path(i['workspace'])) == i['source']
    assert plan['subject_pins'] == pins
    runtime_environment(plan)
    controls = read(HERE / 'retained-controls.json')
    assert process.sha(Path(controls['W']['object_path'])) == controls['W']['object_sha256']
    rust = controls['R']
    assert process.sha(Path(rust['source_path'])) == rust['source_sha256']
    assert process.sha(Path(rust['toolchain_receipt'])) == rust['toolchain_receipt_sha256']
    for library in rust['libraries'].values():
        assert process.sha(Path(library['path'])) == library['sha256']
    dependencies = (RETAINED / rust['provenance_receipt']).parent
    assert process.sha(dependencies / 'Cargo.toml') == rust['library_manifest_sha256']
    assert process.sha(dependencies / 'Cargo.lock') == rust['library_lock_sha256']
    assert plan['bootstrap_seed'] == 2026102595 and plan['bootstrap_resamples'] == 20000
    assert plan['primary_observations'] == 192 and plan['warmups'] == plan['excluded_outliers'] == 0
    assert plan['acceptance_upper_95_percent'] == {'F/I': 1.0, 'F/W': 1.0, 'F/R': 0.0}
    block = [['F','I','R','W'], ['I','W','F','R'], ['W','R','I','F'], ['R','F','W','I']]
    assert plan['session_1'] == block * 6 and plan['session_2'] == list(reversed(block * 6))
    inputs()
    check_controllers(plan)
    gate = read(HERE / 'qualification.json')
    assert process.sha(HERE / 'qualification.json') == plan['qualification_sha256']
    assert gate['source'] == f['source'] and gate['baseline_source'] == i['source']
    assert gate['proceed_to_primary'] is True
    checks = gate['checks']
    stages(evidence(checks['correctness']), f['source']['commit'], CORRECTNESS)
    stages(evidence(checks['generated_processes']), f['source']['commit'], PROCESS_TESTS)
    stages(evidence(checks['baseline_correctness']), i['source']['commit'],
           {'native-unit', 'native-facts', 'native-lines', 'worker-credit', 'native-catalog'})
    changed = evidence(checks['changed_inputs'])
    assert changed['status'] == 'seven-independent-oracles-and-fourteen-pinned-AOT-executions-verified'
    assert changed['source'] == changed['source_after'] == f['source']
    assert changed['pins'] == {s: pins[s] for s in ('F','I')}
    assert len(changed['cases']) == 7 and all(len(c['executions']) == 2 for c in changed['cases'])
    assert {c['name'] for c in changed['cases']} == {
        'one-key-short', 'query-boundaries', 'random-single-row', 'random-short-rows',
        'random-ordinary-rows', 'growth-and-partial-credit', 'repeated-wide-key'}
    assert all({e['subject'] for e in c['executions']} == {'F','I'} for c in changed['cases'])
    code = evidence(checks['guest_code'])
    assert code['F_source'] == f['source'] and code['I_source'] == i['source']
    assert len(code['files']) == 6 and all(row['equal'] and row['F'] == row['I'] for row in code['files'])
    files = {row['file']: row for row in code['files']}
    assert set(files) == {'program.o','program.mecb','native-descriptor.json','native-descriptor.bin','object-identity.bin','native-resources.json'}
    assert files['program.o']['F'] == f['object_sha256'] == i['object_sha256'] == read(HERE / 'retained-controls.json')['W']['object_sha256']
    for subject, receipt in [('F',f), ('I',i)]:
        project = Path(receipt['executable'] + '.project')
        assert all(process.sha(project / name) == row[subject] for name, row in files.items())
        assert all(process.sha(contained(row[subject + '_file'])) == row[subject] for row in files.values())
    representatives = evidence(checks['representative_objects'])
    assert representatives['F_source'] == f['source'] and representatives['I_source'] == i['source']
    assert len(representatives['files']) == 32 and all(row['equal'] and row['F'] == row['I'] for row in representatives['files'])
    expected = {f'{fixture}-{variant}.{suffix}' for fixture in ['aggregate','owner','owner-words','scalar']
                for variant in ['source','decoded'] for suffix in ['o','mecb','metadata.json','descriptor.json']}
    assert {row['path'] for row in representatives['files']} == expected
    for row in representatives['files']:
        assert all(process.sha(contained(row[s + '_file'])) == row[s] for s in ('F','I'))
    for subject, receipt in (('F', f), ('I', i)):
        source, _, hashes = artifact_equivalence.snapshot_receipt(representatives['snapshot_receipts'][subject])
        assert source == receipt['source']
        assert hashes == {row['path']: row[subject] for row in representatives['files']}
    wide_slot.check(checks['wide_slot_artifacts'], f, i)
    return targets, pins, f, i


def committed_before_sampling(revision, plan):
    files = ['plan.json', 'qualification.json', 'retained-controls.json']
    checks = read(HERE / 'qualification.json')['checks']
    files += [ref['path'] for name, ref in checks.items() if name != 'wide_slot_artifacts']
    for name in ['guest_code', 'representative_objects']:
        files += [row[subject + '_file'] for row in evidence(checks[name])['files'] for subject in ('F','I')]
    receipts = [build_receipt_path(plan['baseline_receipt'], shared=True),
                build_receipt_path(plan['candidate_receipt']),
                build_receipt_path(plan['runtime_environment_receipt'], shared=True)]
    paths = [str(path.relative_to(ROOT)) for path in [*(contained(name) for name in files), *receipts]]
    wide_files = wide_slot.check(checks['wide_slot_artifacts'], read(receipts[1]), read(receipts[0]))
    paths += [str(path.relative_to(ROOT)) for path in wide_files]
    representatives = evidence(checks['representative_objects'])
    for reference in representatives['snapshot_receipts'].values():
        paths += [str(path.relative_to(ROOT)) for path in artifact_equivalence.snapshot_archive_files(reference)]
    paths += list(plan['controller_pins'])
    for path in paths:
        blob = subprocess.check_output(['git','-C',str(ROOT),'show',revision + ':' + path])
        assert hashlib.sha256(blob).hexdigest() == process.sha(ROOT / path), path


def observation(sample, session, plan, targets, identities, policy):
    order, position, subject = sample['order'], sample['position'], sample['subject']
    assert subject == plan[f'session_{session}'][order][position]
    expected = f'primary-session-{session}/{order:02d}-{position}-{subject}/process.json'
    assert sample['process'] == expected
    path = contained(expected)
    assert process.sha(path) == sample['process_sha256']
    raw = read(path)
    assert raw['exit_status'] == 0 and raw['quantitative_benchmark'] is True
    assert raw['inherited_common_mutex'] is True and raw['deadline_seconds'] == 30
    assert raw['cleanup_errors'] == [] and raw['group_closed'] is True and raw['reaped'] is True
    assert raw['signals'] == [] and 'error' not in raw and not raw.get('observer_still_waiting')
    assert raw['controller_sha256'] == plan['controller_pins'][CONTROLLER]
    assert math.isfinite(raw['elapsed_seconds']) and raw['elapsed_seconds'] > 0
    assert sample['seconds'] == raw['elapsed_seconds']
    assert sample['maximum_rss_bytes'] == raw['maximum_rss_bytes'] > 0
    identity = raw['birth_identity']
    birth = (identity['pid'], identity['birth_seconds'], identity['birth_microseconds'])
    assert birth not in identities
    identities.add(birth)
    assert process.sha(path.parent / 'stdout.bin') == sample['stdout_sha256'] == plan['output_sha256']
    assert (path.parent / 'stderr.bin').is_file()
    native = path.parent.parent / (path.parent.name + '.native.json')
    command = [str(targets[subject])]
    if subject != 'R':
        command += [str(policy), str(native), '--']
        assert process.sha(native) == sample['native_sha256']
        assert check_native(native) == sample['native']
    else:
        assert sample['native_sha256'] is None and sample['native'] is None
    assert raw['command'] == command and sample['verified'] is True


def validate_reports(reports, plan):
    targets, pins, f, _ = prerequisites(plan)
    assert [r['session'] for r in reports] == [1, 2]
    assert len({r['evidence_revision'] for r in reports}) == 1
    committed_before_sampling(reports[0]['evidence_revision'], plan)
    _, policy, _ = inputs()
    identities = set()
    for report in reports:
        session = report['session']
        assert report['study_id'] == STUDY_ID
        assert report['status'] == COMPLETE and len(report['samples']) == 96
        assert report['source'] == report['source_after'] == f['source']
        assert report['pins'] == pins and report['orders'] == plan[f'session_{session}']
        assert report['excluded_warmups'] == report['excluded_outliers'] == 0
        assert report['plan_sha256'] == process.sha(HERE / 'plan.json')
        assert report['driver_sha256'] == process.sha(CODE_DIR / 'measure.py')
        assert report['controller_sha256'] == plan['controller_pins'][CONTROLLER]
        for key in ['input_sha256','policy_sha256','canonical_data_sha256','source_sha256','bytecode_sha256']:
            assert report[key] == plan[key]
        assert [(r['order'], r['position']) for r in report['samples']] == [(o, p) for o in range(24) for p in range(4)]
        for sample in report['samples']:
            observation(sample, session, plan, targets, identities, policy)
    assert len(identities) == 192
