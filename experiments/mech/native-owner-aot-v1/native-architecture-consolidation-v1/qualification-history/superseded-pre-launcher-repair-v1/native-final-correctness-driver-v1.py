#!/usr/bin/env python3
"""Run all 51 local correctness scopes on one clean, immutable source revision.

Invoke with the CI Python environment (PyYAML 6.0.3 is required by workflow
contracts). Every stage runs through the checkout's bounded native stage owner.
This driver never reuses historical result rows and never collects primary timings.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


TOOLCHAIN = 'nightly-2026-03-03'
CARGO = ['cargo', '+' + TOOLCHAIN, 'test', '--locked', '--offline', '-j1']
EMPTY_COMPANIONS = {'native-unit', 'native-catalog', 'maintained-hosted-runner'}
CLOSURE_FORBIDDEN = re.compile(
    r'cranelift|mech-syntax|feature "(?:full_compiler|resident-routing|canonical-native-program|canonical-native|jit|aot)"'
)
RUST_RESULTS = re.compile(
    r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;', re.M
)


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def source_state(workspace, head):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=workspace, text=True).strip()
    state = {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
             'status': git('status', '--porcelain=v1', '--untracked-files=all')}
    require(state['commit'] == head, f'source commit changed: {state}')
    require(not state['status'], f'source is not clean: {state}')
    return state


def stage_specs(evidence):
    """Pure construction: importing this module or inspecting specs runs no tools."""
    stages = []

    def run(name, command, tests=False, timeout=1800):
        stages.append({'stage': name, 'command': command, 'tests': tests,
                       'timeout_seconds': timeout})

    def test(name, packages, features, selection, timeout=1800):
        command = CARGO.copy()
        for package in packages:
            command += ['-p', package]
        command += ['--no-default-features', '--features', features] + selection
        command += ['--', '--test-threads=1', '--nocapture']
        run(name, command, True, timeout)
        stages[-1]['expected_harnesses'] = (selection.count('--test') or
            selection.count('--example') or len(packages))

    for name,feature in [('none',None),('scalar-runtime','canonical-native-runtime'),('program-runtime','canonical-native-program-runtime'),('host-runtime','canonical-native-program-host-runtime'),('scalar-compiler','canonical-native'),('program-compiler','canonical-native-program')]:
        cmd=['cargo','+nightly-2026-03-03','check','--locked','--offline','-j1','-p','mech-gpu','--no-default-features','--lib']
        if feature:cmd+=['--features',feature]
        run(name+'-check',cmd)
        if name not in ('scalar-compiler','program-compiler'):
            tree=['cargo','+nightly-2026-03-03','tree','--locked','--offline','-p','mech-gpu','--no-default-features','--edges','normal,build,features']
            if feature:tree+=['--features',feature]
            run(name+'-tree',tree)
    host='mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host'
    # The retained full command runs every native contract, including renamed modules.
    test('native-unit',['mech-stdlib','mech-gpu'],host,['--lib','native_artifact::'])
    for name,selection in [('native-facts','native_artifact::'),('native-lines','native_text_line'),('worker-credit','workers::')]:
        test(name,['mech-engine'],'mech-engine/full_compiler,mech-engine/native-artifact',['--lib',selection])
    test('native-catalog',['mech-stdlib','mech-gpu'],host,['--lib','native_plan_catalog'])
    scalar=['canonical_artifact_native','canonical_artifact_i64','canonical_artifact_f64','canonical_artifact_cast','canonical_artifact_match','canonical_artifact_iteration']
    test('scalar-integration',['mech-gpu'],'canonical-native',[x for name in scalar for x in ['--test',name]])
    test('program-integration',['mech-gpu'],'canonical-native-program',['--test','canonical_artifact_program'])
    test('scalar-unit',['mech-gpu'],'canonical-native',['--lib','native_artifact::'])
    native=['native_artifact_lowering','native_artifact_i64_lowering','native_artifact_f64_lowering','native_artifact_cast_lowering','native_artifact_match_lowering','native_artifact_iteration_lowering','native_collection_templates','native_map_entries','native_artifact_output_initializers']
    test('native-source-lowering',['mech-stdlib'],'full_compiler,native-artifact',[x for name in native for x in ['--test',name]])
    source=['comprehension_captures','comprehension_work_source','control_local_geometry','control_matrix_captures','control_result_shapes','function_output_contexts','knucleotide_record_source','map_keys_comprehensions','map_source','source_map_entry_contract','source_map_lookup_contract','match_result_schemas','matrix_block_comprehensions','postfix_selection','primitive_snapshot_constructors','pure_text_managed','pure_text_source','retention_work','sequence_sort','set_comprehension_operands','string_generators','string_literal_match','string_membership_comprehensions','string_selector_shapes','text_operations','u64_float_conversion_source','underscore_addressing']
    test('source-contracts',['mech-stdlib'],'full_compiler',[x for name in source for x in ['--test',name]])
    test('source-applications',['mech-stdlib'],'full_compiler',['--test','applications','--test','tail_control'])
    test('source-assignment',['mech-stdlib'],'full_compiler,matrix2,vector2',['--test','source_op_assign_contract','--test','specialization_contract'])
    test('benchmark-policy-unit',['mech-gpu'],'canonical-native-benchmark-policy',['--lib','native_artifact::benchmark_policy::'])

    # Native witnesses required by the current ci-full.yml, omitted by the initial driver.
    test('resident-factory-attachment',['mech-core'],'functions',['--test','resident_factory_lowering_attachment'])
    for name,features,selection in [
     ('native-collection-templates','full_compiler,native-artifact','resident::general::native_collection_templates::tests'),
     ('native-set-conversion','full_compiler,native-artifact','resident::set_conversion::'),
     ('native-kind-conversion','full_compiler,native-artifact','intrinsics::kind_conversion::'),
     ('native-annotation-conversion','full_compiler,native-artifact','source_semantics::frontend::annotation_conversion_shape_tests::'),
     ('source-set-conversion','full_source,native-artifact','resident::set_conversion::'),
     ('source-kind-conversion','full_source,native-artifact','intrinsics::kind_conversion::'),
     ('source-annotation-conversion','full_source,native-artifact','source_semantics::frontend::annotation_conversion_shape_tests::'),
     ('native-semantics','full_compiler,native-artifact','resident::native_semantics::tests'),
     ('iteration-proofs','full_compiler,native-artifact','resident::general::native_match_lowering::iteration_proof_tests')]:
        test(name,['mech-engine'],features,['--lib',selection])
    for name,selection in [
     ('program-runtime-unit','native_artifact::program::runtime::tests'),
     ('program-prefix-unit','native_artifact::program::runtime::session::prefix_tests'),
     ('program-prefix-window-unit','native_artifact::program::runtime::session::prefix_window_tests'),
     ('program-prefix-retention-unit','native_artifact::program::runtime::invocation::prefix::retention_tests')]:
        test(name,['mech-gpu'],'canonical-native-program',['--lib',selection])

    # The current native/source linked CI family also retains its ordinary routes.
    legacy=['native_host_io','repeated_application','native_host_application','native_source_admission','control_fsm','control_postfix_selection','control_selection','control_signed','idiomatic_sources']
    test('native-source-integration',['mech-gpu'],'native-build,native-io',[x for name in legacy for x in ['--test',name]])
    test('canonical-host-reference',['mech-runtime'],'full_compiler,resident-routing-source',['--example','canonical_host_reference'])
    cli=['canonical_cli_bytes','canonical_cli_argument_count','canonical_resource_execution','canonical_resource_planning','canonical_map_features','canonical_pure_text_features']
    test('canonical-cli-byte-contracts',['mech-build'],'standard-hosts',[x for name in cli for x in ['--test',name]])


    # Required repository guard commands, with retained diagnostics and exit status.
    checks=[('format',['cargo','+nightly-2026-03-03','fmt','--all','--','--check']),('unsafe',['bash','scripts/check-unsafe-boundaries.sh']),('unsafe-contract',['bash','scripts/test-unsafe-boundaries.sh']),('runtime-factory-safety',['python3','scripts/check-runtime-factory-safety.py']),('build-analysis-layout',['python3','scripts/check-native-build-analysis-layout.py']),('warning-policy',['python3','scripts/check-warning-policy.py']),('module-layout',['python3','scripts/check-rust-module-layout.py']),('planning-quarantine',['python3','scripts/check-compiler-planning-quarantine.py']),('workflow-contracts',[sys.executable,'-B','-m','unittest','tests/ci/test_ci_full_contract.py','tests/ci/test_ci_test_inventory.py']),('process-contracts',['python3','-B','-m','unittest','scripts/tests/test_canonical_cli_ci.py','scripts/tests/test_native_plan_stage.py','scripts/tests/test_probe_unix_kill_targeting.py'])]
    for name,cmd in checks:run(name,cmd)

    run('maintained-hosted-runner',['env','CARGO_TARGET_DIR='+str(evidence/'maintained-hosted-runner-target'),sys.executable,'scripts/check-canonical-hosted-runner.py','--fetch'],True)

    names = [stage['stage'] for stage in stages]
    require(len(names) == len(set(names)) == 51, f'incorrect stage inventory: {names}')
    return stages


def validate_stage(spec, log, summary, status, source_before, source_after):
    name = spec['stage']
    require(status == 0, f'{name}: bounded wrapper failed ({status})')
    require(summary.get('stage') == name and summary.get('reason') == 'exit',
            f'{name}: missing successful terminal wrapper summary')
    require(summary.get('command_exit_status') == 0 and
            summary.get('owned_group_cleanup') == 'complete',
            f'{name}: process exit or owned group cleanup failed')
    require(summary.get('timeout_seconds') == spec['timeout_seconds'],
            f'{name}: stage deadline differs from declared deadline')
    require(source_before == source_after, f'{name}: source changed during stage')
    counts = [tuple(map(int, match)) for match in RUST_RESULTS.findall(log)]
    if counts:
        require(sum(row[0] for row in counts) > 0 and all(row[1] == 0 for row in counts),
                f'{name}: failing or empty test results: {counts}')
    if spec['tests']:
        minimum = 13 if name == 'benchmark-policy-unit' else 1
        require(sum(row[0] for row in counts) >= minimum,
                f'{name}: fewer than {minimum} tests passed: {counts}')
        if name not in EMPTY_COMPANIONS:
            require(all(row[0] > 0 for row in counts), f'{name}: empty selected harness: {counts}')
        if 'expected_harnesses' in spec:
            require(len(counts) == spec['expected_harnesses'],
                    f'{name}: incomplete selected harnesses: {counts}')
    if name.endswith('-tree'):
        require(CLOSURE_FORBIDDEN.search(log) is None,
                f'{name}: compiler/parser feature entered runtime dependency closure')
    if name in {'workflow-contracts', 'process-contracts'}:
        totals = re.findall(r'^Ran (\d+) tests? in ', log, re.M)
        require(totals and sum(map(int, totals)) > 0, f'{name}: no Python tests executed')
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--target-dir', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9a-f]{40}', args.head) is not None, '--head must be a full commit SHA')
    workspace = args.workspace.resolve(strict=True)
    target = args.target_dir.resolve()
    evidence = args.evidence.resolve()
    require(not evidence.exists(), f'evidence directory already exists: {evidence}')
    require(target != evidence and not target.is_relative_to(evidence),
            'main target must be separate from fresh evidence; runner owns its evidence target')
    require(importlib.metadata.version('PyYAML') == '6.0.3',
            'run this driver with the CI Python environment containing PyYAML==6.0.3')
    initial = source_state(workspace, args.head)
    owner = workspace / 'scripts/run-native-plan-stage.py'
    owner_digest = sha(owner)
    specs = stage_specs(evidence)
    environment = os.environ.copy()
    environment.update(CARGO_TARGET_DIR=str(target), CARGO_INCREMENTAL='0',
                       CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
                       CARGO_BUILD_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
    evidence.mkdir(parents=True, exist_ok=False)
    write(evidence / 'context.json', {
        'source': initial, 'workspace': str(workspace), 'target_dir': str(target),
        'driver_sha256': sha(Path(__file__).resolve()), 'stage_owner_sha256': owner_digest,
        'python': sys.executable, 'toolchain': TOOLCHAIN, 'stages': specs,
        'reuse_of_old_results': False, 'primary_timing_samples': 0,
    })
    rows = []
    for spec in specs:
        name = spec['stage']
        before = source_state(workspace, args.head)
        require(before == initial and sha(owner) == owner_digest,
                f'{name}: source or bounded owner differs from initial pin')
        wrapper = [sys.executable, str(owner), '--stage', name, '--timeout-secs',
                   str(spec['timeout_seconds']), '--log-dir', str(evidence), '--'] + spec['command']
        started = time.monotonic()
        with (evidence / (name + '.console.log')).open('wb') as console:
            result = subprocess.run(wrapper, cwd=workspace, env=environment,
                                    stdout=console, stderr=subprocess.STDOUT)
        log_path = evidence / (name + '.log')
        summary_path = evidence / (name + '.summary.json')
        log = log_path.read_text(errors='replace') if log_path.exists() else ''
        row = {'stage': name, 'head': args.head, 'command': spec['command'],
               'wrapper': wrapper, 'exit_code': result.returncode,
               'wrapper_exit_code': result.returncode, 'seconds': time.monotonic() - started,
               'counts': [tuple(map(int, match)) for match in RUST_RESULTS.findall(log)],
               'source_before': before}
        error = None
        try:
            after = source_state(workspace, args.head)
            row['source_after'] = after
            summary = json.loads(summary_path.read_text())
            validate_stage(spec, log, summary, result.returncode, before, after)
            require(sha(owner) == owner_digest, f'{name}: bounded owner changed')
            row.update(log_sha256=sha(log_path), summary_sha256=sha(summary_path))
        except Exception as failure:
            error = failure
            row['verification_error'] = str(failure)
            row['exit_code'] = result.returncode or 1
        rows.append(row)
        write(evidence / 'results.json', rows)
        print(name, row['exit_code'], row['counts'], flush=True)
        if error is not None:
            raise error
    require(source_state(workspace, args.head) == initial, 'final source pin changed')
    write(evidence / 'complete.json', {
        'head': args.head, 'source': initial, 'stages': len(rows),
        'status': 'correctness-passed', 'results_sha256': sha(evidence / 'results.json'),
        'primary_timing_samples': 0,
    })


if __name__ == '__main__':
    main()
