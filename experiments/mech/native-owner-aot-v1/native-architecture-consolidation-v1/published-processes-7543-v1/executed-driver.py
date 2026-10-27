#!/usr/bin/env python3
"""Run 16 substantive process scopes with existing bounds and immutable harnesses.

No historic result rows are reused. Compile/selection/checker receipts accompany
the 16 substantive gates. Linux strace-specific CI qualification remains separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


LINKED_PROCESS_TESTS = {'canonical-hosted-linked': 'linked::complete_original_and_decoded_knucleotide_linked_processes_are_secured_and_pinned', 'canonical-policy-linked': 'linked::benchmark::complete_original_and_decoded_knucleotide_same_binary_policy_controls', 'canonical-scalar-linked': 'linked_canonical_artifact_scalar_applications_are_typed_bounded_and_atomic', 'canonical-cast-linked': 'linked_canonical_artifact_cast_applications_preserve_checked_boundaries', 'canonical-match-linked': 'linked_canonical_match_applications_are_lazy_bounded_and_atomic', 'canonical-iteration-linked': 'linked_qualification::one_linked_iteration_executable_preserves_exact_typed_loops_and_denials', 'canonical-program-linked': 'linked_qualification::linked_managed_programs_preserve_canonical_outputs_errors_and_denials', 'native-source-host-linked': 'one_linked_executable_runs_secure_and_trusted_without_rebuilding', 'native-source-control-linked': 'one_linked_control_executable_preserves_signed_machine_outputs', 'native-source-stdin-linked': 'one_linked_stdin_executable_preserves_unicode_snapshots_and_launch_policy', 'canonical-resident-cli-linked': 'linked_canonical_cli_arguments_and_stdin_finish_without_drivers'}
PROCESS_TESTS = ['canonical-cast-linked', 'canonical-cli-public-qualification', 'canonical-cli-unit-contracts', 'canonical-hosted-contracts', 'canonical-hosted-linked', 'canonical-iteration-linked', 'canonical-match-linked', 'canonical-policy-contracts', 'canonical-policy-kernel', 'canonical-policy-linked', 'canonical-program-linked', 'canonical-resident-cli-linked', 'canonical-scalar-linked', 'native-source-control-linked', 'native-source-host-linked', 'native-source-stdin-linked']


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--target-dir', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--hosted-target-dir', type=Path, required=True,
                        help='explicit task-owned Cargo cache shared by hosted and policy')
    args = parser.parse_args()
    require(sys.flags.optimize == 0, 'run without Python -O; retained harness pin assertions must execute')
    require(re.fullmatch(r'[0-9a-f]{40}', args.head) is not None, '--head must be a full SHA')
    ROOT = args.workspace.resolve(strict=True)
    HEAD = args.head
    OUT = args.evidence.resolve()
    target = args.target_dir.resolve()
    hosted_target = args.hosted_target_dir.resolve()
    require(not OUT.exists(), f'evidence directory already exists: {OUT}')
    require(not OUT.is_relative_to(ROOT), 'evidence must be outside the immutable source checkout')
    require(target != OUT and hosted_target != OUT, 'Cargo targets must differ from the evidence root')
    ENV = os.environ.copy()
    ENV.update(CARGO_TARGET_DIR=str(target), CARGO_PROFILE_DEV_DEBUG='0',
               CARGO_PROFILE_TEST_DEBUG='0', CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='1',
               MECH_CANONICAL_HOSTED_TARGET_DIR=str(hosted_target),
               MECH_CANONICAL_HOSTED_PROFILE='debug',
               PYTHONDONTWRITEBYTECODE='1')
    # Preserve any explicitly configured compiler/library search paths. This
    # controller introduces no optimization flags or generated Cargo profile edits.
    if sys.platform == 'darwin' and Path('/opt/homebrew/opt/gmp/include').is_dir():
        ENV.setdefault('CFLAGS', '-I/opt/homebrew/opt/gmp/include')
        ENV.setdefault('LIBRARY_PATH', '/opt/homebrew/opt/gmp/lib')
        ENV.setdefault('CPATH', '/opt/homebrew/opt/gmp/include')
    CARGO = ['cargo', '+nightly-2026-03-03', 'test', '--locked', '--offline', '-j1']
    owner = ROOT / 'scripts/run-native-plan-stage.py'
    owner_hash = sha(owner)
    fixture_paths = ['hosts/gpu/tests/support/' + name for name in (
        'canonical_hosted_linked.rs', 'canonical_hosted_benchmark.rs',
        'canonical_hosted_launcher_tests.rs', 'canonical_hosted_profile.rs')]
    fixture_pins = {name: sha(ROOT / name) for name in fixture_paths}
    require('cargo_target(&evidence)' in (ROOT / fixture_paths[1]).read_text(),
            'policy source does not use the supported shared target helper')
    require('MECH_CANONICAL_HOSTED_TARGET_DIR' in (ROOT / fixture_paths[0]).read_text(),
            'hosted source does not expose the supported shared target override')
    rows = []

    def clean():
        def git(*arguments):
            return subprocess.check_output(['git', *arguments], cwd=ROOT, text=True).strip()
        state = {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                 'status': git('status', '--porcelain=v1', '--untracked-files=all')}
        require(state['commit'] == HEAD and not state['status'], f'source pin changed: {state}')
        require(sha(owner) == owner_hash, 'bounded stage owner changed')
        return state

    initial = clean()
    OUT.mkdir(parents=True, exist_ok=False)
    write(OUT / 'context.json', {
        'source': initial, 'workspace': str(ROOT), 'target_dir': str(target),
        'hosted_policy_target_dir': str(hosted_target),
        'hosted_policy_cache_preexisting': hosted_target.exists(),
        'driver_sha256': sha(Path(__file__).resolve()), 'stage_owner_sha256': owner_hash,
        'fixture_sha256': fixture_pins,
        'compiler_environment': {name: ENV.get(name) for name in ('CFLAGS', 'CPATH', 'LIBRARY_PATH')},
        'required_process_tests': PROCESS_TESTS, 'reuse_of_old_results': False,
        'primary_timing_samples': 0,
        'profiles': {'hosted': 'debug', 'policy': 'release'},
        'preserved_outer_seconds': {'hosted': 7320, 'policy': 11820},
        'compiled_launcher_seconds': {'compile': 1080, 'execute': 300},
        'outer_budget_note': 'Preserves v7 aggregate bounds despite two added launcher compile phases; no deadline extension or template substitution.',
        'platform': sys.platform,
        'linux_strace_probe': 'separate required CI evidence, not exercised by this local driver',
    })

    def harness_pin(harness):
        pin = json.loads((OUT / (harness + '.pin.json')).read_text())
        executable = Path((OUT / harness).read_text().strip())
        require(pin['source_commit'] == HEAD and pin['executable'] == str(executable),
                f'harness identity changed: {harness}')
        require(executable.is_file() and sha(executable) == pin['sha256'],
                f'harness content changed: {harness}')
        return pin

    def call(stage, cmd, timeout=1800, record=None, harness=None, extra=None):
        before = clean()
        require(before == initial, f'{stage}: source tree changed')
        require(stage not in {row['stage'] for row in rows}, f'duplicate stage: {stage}')
        if harness and not record:
            harness_pin(harness)
        wrapper = [sys.executable, str(owner), '--stage', stage, '--timeout-secs',
                   str(timeout), '--log-dir', str(OUT)]
        if record:
            require(harness is not None, 'recorded harness needs an output path')
            wrapper += ['--record-test-executable', record]
        if harness:
            wrapper += ['--test-executable-file', str(OUT / harness)]
        wrapper += ['--'] + cmd
        env = ENV.copy()
        env.update(extra or {})
        require(env['MECH_CANONICAL_HOSTED_TARGET_DIR'] == str(hosted_target),
                'hosted/policy shared cache override changed')
        started = time.monotonic()
        with (OUT / (stage + '.console.log')).open('wb') as console:
            result = subprocess.run(wrapper, cwd=ROOT, env=env,
                                    stdout=console, stderr=subprocess.STDOUT)
        log_path = OUT / (stage + '.log')
        summary_path = OUT / (stage + '.summary.json')
        log = log_path.read_text(errors='replace') if log_path.exists() else ''
        counts = [tuple(map(int, values)) for values in re.findall(
            r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;', log, re.M)]
        row = {'stage': stage, 'head': HEAD, 'command': cmd, 'wrapper': wrapper,
               'exit_code': result.returncode, 'wrapper_exit_code': result.returncode,
               'seconds': time.monotonic() - started, 'counts': counts,
               'source_before': before, 'environment_overrides': extra or {}}
        error = None
        try:
            after = clean()
            row['source_after'] = after
            require(after == before, f'{stage}: source changed during execution')
            require(result.returncode == 0, f'{stage}: wrapper failed ({result.returncode})')
            summary = json.loads(summary_path.read_text())
            require(summary.get('stage') == stage and summary.get('reason') == 'exit'
                    and summary.get('command_exit_status') == 0
                    and summary.get('owned_group_cleanup') == 'complete'
                    and summary.get('timeout_seconds') == timeout,
                    f'{stage}: invalid terminal/cleanup/deadline receipt')
            if counts:
                require(sum(row[0] for row in counts) > 0 and all(row[1] == 0 for row in counts),
                        f'{stage}: empty or failing results: {counts}')
            if stage in PROCESS_TESTS:
                minimum = {'canonical-cli-unit-contracts': 5,
                           'canonical-cli-public-qualification': 3,
                           'canonical-policy-kernel': 13}.get(stage, 1)
                require(sum(row[0] for row in counts) >= minimum and
                        all(row[0] > 0 and row[1] == 0 for row in counts),
                        f'{stage}: insufficient passed tests: {counts}')
                if stage in LINKED_PROCESS_TESTS:
                    name = LINKED_PROCESS_TESTS[stage]
                    require('--list' not in cmd and '--no-run' not in cmd
                            and cmd.count('--ignored') == cmd.count('--exact') == 1
                            and cmd[cmd.index('--exact') + 1] == name
                            and counts == [(1, 0, 0)],
                            f'{stage}: exact linked test was not executed once')
            if record:
                executable = Path((OUT / harness).read_text().strip())
                write(OUT / (harness + '.pin.json'), {
                    'executable': str(executable), 'sha256': sha(executable), 'source_commit': HEAD})
            if harness:
                row['harness_pin'] = harness_pin(harness)
            row.update(log_sha256=sha(log_path), summary_sha256=sha(summary_path))
        except Exception as failure:
            error = failure
            row.update(exit_code=result.returncode or 1, verification_error=str(failure))
        rows.append(row)
        write(OUT / 'results.json', rows)
        print(stage, row['exit_code'], counts, flush=True)
        if error is not None:
            raise error
        return log

    def check(mode, *arguments):
        call('checker-' + mode,
             [sys.executable, 'scripts/check_canonical_cli_ci.py', mode,
              '--log-dir', str(OUT)] + list(arguments))

    def selected(log, name):
        require(log.splitlines().count(name + ': test') == 1,
                f'exact ignored test selection differs: {name}')

    workflow=(ROOT/'.github/workflows/ci-native-plan.yml').read_text()
    start=workflow.index('sha256sum Cargo.toml', workflow.index('  canonical-native-cli:'))
    block=workflow[start:workflow.index('> target/native-plan-logs/canonical-cli-source.sha256',start)]
    source_files=[]
    for token in shlex.split(block.replace('\\\n',' '))[1:]:
        paths=sorted(ROOT.glob(token))
        require(paths, f'source pin glob is empty: {token}')
        source_files.extend(str(p.relative_to(ROOT)) for p in paths)
    pins={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(set(source_files))};(OUT/'source-pins.json').write_text(json.dumps(dict(head=HEAD,files=pins),indent=2)+'\n')
    call('canonical-cli-lib-compile',CARGO+['-p','mech','--features','full_compiler,cranelift_build','--lib','--no-run','--message-format=json-render-diagnostics'],1380,'mech','canonical-cli-lib-executable')
    call('canonical-cli-public-compile',CARGO+['-p','mech','--features','full_compiler,cranelift_build','--test','canonical_native_build','--no-run','--message-format=json-render-diagnostics'],1380,'canonical_native_build','canonical-cli-public-executable')
    check('pins')
    call('canonical-cli-unit-selection',['--list','cli::commands::build::cranelift::tests::'],60,harness='canonical-cli-lib-executable');check('unit-selection')
    call('canonical-cli-unit-contracts',['cli::commands::build::cranelift::tests::','--test-threads=1','--nocapture'],480,harness='canonical-cli-lib-executable')
    call('canonical-cli-public-selection',['--list','--ignored'],60,harness='canonical-cli-public-executable');check('public-selection')
    call('canonical-cli-public-qualification',['--ignored','--test-threads=1','--nocapture'],8460,harness='canonical-cli-public-executable',extra={'MECH_CANONICAL_CLI_EVIDENCE_DIR':str(OUT/'cli-evidence')})
    check('complete','--evidence-dir',str(OUT/'cli-evidence'))
    packages=['-p', 'mech-core','-p','mech-engine','-p','mech-runtime','-p','mech-stdlib','-p','mech-syntax','-p','mech-gpu']
    host='mech-stdlib/full_compiler,mech-stdlib/native-artifact,mech-gpu/canonical-native-program-host'
    call('canonical-hosted-compile',CARGO+packages+['--no-default-features','--features',host,'--test','canonical_hosted_artifact','--no-run','--message-format=json-render-diagnostics'],1080,'canonical_hosted_artifact','canonical-hosted-executable')
    call('canonical-hosted-contracts',['--test-threads=1','--nocapture'],480,harness='canonical-hosted-executable')
    name='linked::complete_original_and_decoded_knucleotide_linked_processes_are_secured_and_pinned'
    selected(call('canonical-hosted-selection',['--list','--ignored','--exact',name],60,harness='canonical-hosted-executable'),name)
    call('canonical-hosted-linked',['--ignored','--exact',name,'--test-threads=1','--nocapture'],7320,harness='canonical-hosted-executable',extra={'MECH_CANONICAL_HOSTED_SOURCE_COMMIT':HEAD,'MECH_CANONICAL_HOSTED_EVIDENCE_DIR':str(OUT/'hosted-evidence'),'MECH_CANONICAL_HOSTED_PROFILE':'debug'})
    policy=host.replace('mech-gpu/canonical-native-program-host','mech-gpu/canonical-native-benchmark-policy')
    call('canonical-policy-compile',CARGO+packages+['--no-default-features','--features',policy,'--test','canonical_hosted_artifact','--no-run','--message-format=json-render-diagnostics'],1080,'canonical_hosted_artifact','canonical-policy-executable')
    call('canonical-policy-kernel',CARGO+['-p','mech-gpu','--no-default-features','--features','canonical-native-benchmark-policy','--lib','native_artifact::benchmark_policy::','--','--test-threads=1','--nocapture'],1680)
    call('canonical-policy-contracts',['--test-threads=1','--nocapture'],480,harness='canonical-policy-executable')
    name='linked::benchmark::complete_original_and_decoded_knucleotide_same_binary_policy_controls'
    selected(call('canonical-policy-selection',['--list','--ignored','--exact',name],60,harness='canonical-policy-executable'),name)
    call('canonical-policy-linked',['--ignored','--exact',name,'--test-threads=1','--nocapture'],11820,harness='canonical-policy-executable',extra={'MECH_CANONICAL_POLICY_SOURCE_COMMIT':HEAD,'MECH_CANONICAL_POLICY_EVIDENCE_DIR':str(OUT/'policy-evidence'),'MECH_CANONICAL_HOSTED_PROFILE':'release'})
    require(pins=={s:sha(ROOT/s) for s in pins}, 'CLI source pins changed')

    families=[
     ('canonical-scalar-linked','canonical_artifact_application','canonical-native','linked_canonical_artifact_scalar_applications_are_typed_bounded_and_atomic','MECH_CANONICAL_NATIVE'),
     ('canonical-cast-linked','canonical_artifact_application','canonical-native','linked_canonical_artifact_cast_applications_preserve_checked_boundaries','MECH_CANONICAL_NATIVE'),
     ('canonical-match-linked','canonical_artifact_match_application','canonical-native','linked_canonical_match_applications_are_lazy_bounded_and_atomic','MECH_CANONICAL_MATCH'),
     ('canonical-iteration-linked','canonical_artifact_iteration','canonical-native','linked_qualification::one_linked_iteration_executable_preserves_exact_typed_loops_and_denials','MECH_CANONICAL_ITERATION'),
     ('canonical-program-linked','canonical_artifact_program','canonical-native-program','linked_qualification::linked_managed_programs_preserve_canonical_outputs_errors_and_denials','MECH_CANONICAL_PROGRAM')]
    compiled=set()
    for stage,target,features,name,environment in families:
        harness=target+'-executable'
        if target not in compiled:
            call(target+'-compile',CARGO+['-p','mech-gpu','--no-default-features','--features',features,'--test',target,'--no-run','--message-format=json-render-diagnostics'],1800,target,harness)
            compiled.add(target)
            executable=Path((OUT/harness).read_text().strip())
            (OUT/(harness+'.pin.json')).write_text(json.dumps(dict(executable=str(executable),sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),source_commit=HEAD),indent=2)+'\n')
        selected(call(stage+'-selection',['--list','--ignored','--exact',name],60,harness=harness),name)
        call(stage,['--ignored','--exact',name,'--test-threads=1','--nocapture'],14400,harness=harness,extra={environment+'_SOURCE_COMMIT':HEAD,environment+'_EVIDENCE_DIR':str(OUT/(stage+'-evidence'))})
        executable=Path((OUT/harness).read_text().strip())
        assert hashlib.sha256(executable.read_bytes()).hexdigest()==json.loads((OUT/(harness+'.pin.json')).read_text())['sha256']

    # The same current linked CI job maintains activated native-source routes.
    for stage,target,name,variable,extra in [
     ('native-source-host-linked','native_host_application','one_linked_executable_runs_secure_and_trusted_without_rebuilding','MECH_NATIVE_QUALIFICATION_DIRECTORY',{}),
     ('native-source-control-linked','control_application','one_linked_control_executable_preserves_signed_machine_outputs','MECH_CONTROL_QUALIFICATION_DIRECTORY',{'MECH_CONTROL_INLINE':'0'}),
     ('native-source-stdin-linked','native_stdin_application','one_linked_stdin_executable_preserves_unicode_snapshots_and_launch_policy','MECH_NATIVE_STDIN_QUALIFICATION_DIRECTORY',{})]:
        harness=target+'-executable'
        call(target+'-compile',CARGO+['-p','mech-gpu','--no-default-features','--features','native-build,native-io','--test',target,'--no-run','--message-format=json-render-diagnostics'],1800,target,harness)
        executable=Path((OUT/harness).read_text().strip());digest=hashlib.sha256(executable.read_bytes()).hexdigest()
        (OUT/(harness+'.pin.json')).write_text(json.dumps(dict(executable=str(executable),sha256=digest,source_commit=HEAD),indent=2)+'\n')
        selected(call(stage+'-selection',['--list','--ignored','--exact',name],60,harness=harness,extra=extra),name)
        call(stage,['--ignored','--exact',name,'--test-threads=1','--nocapture'],14400,harness=harness,extra={**extra,variable:str(OUT/(stage+'-evidence'))})
        assert hashlib.sha256(executable.read_bytes()).hexdigest()==digest
    stage='canonical-resident-cli-linked';target='canonical_cli_application';harness=target+'-executable'
    name='linked_canonical_cli_arguments_and_stdin_finish_without_drivers'
    call(target+'-compile',CARGO+['-p','mech-build','--no-default-features','--features','standard-hosts,process-supervision','--test',target,'--no-run','--message-format=json-render-diagnostics'],1800,target,harness)
    executable=Path((OUT/harness).read_text().strip());digest=hashlib.sha256(executable.read_bytes()).hexdigest()
    (OUT/(harness+'.pin.json')).write_text(json.dumps(dict(executable=str(executable),sha256=digest,source_commit=HEAD),indent=2)+'\n')
    selected(call(stage+'-selection',['--list','--ignored','--exact',name],60,harness=harness),name)
    call(stage,['--ignored','--exact',name,'--test-threads=1','--nocapture'],14400,harness=harness,extra={'MECH_CANONICAL_CLI_SOURCE_COMMIT':HEAD,'MECH_CANONICAL_CLI_EVIDENCE_DIR':str(OUT/(stage+'-evidence'))})
    assert hashlib.sha256(executable.read_bytes()).hexdigest()==digest

    require(pins=={s:sha(ROOT/s) for s in pins}, 'final CLI source pins changed')

    require(clean() == initial, 'final source pin changed')
    require(fixture_pins == {name: sha(ROOT / name) for name in fixture_paths},
            'hosted/policy fixture source pins changed')
    substantive = [row for row in rows if row['stage'] in PROCESS_TESTS]
    require(len(substantive) == len(PROCESS_TESTS) == 16 and
            {row['stage'] for row in substantive} == set(PROCESS_TESTS),
            'incomplete substantive process inventory')
    require(all(row['exit_code'] == 0 for row in rows), 'failed process stage')
    write(OUT / 'process-results.json', substantive)
    write(OUT / 'complete.json', {
        'head': HEAD, 'source': initial, 'stages': len(rows), 'substantive_stages': 16,
        'status': 'all-sixteen-generated-process-scopes-qualified',
        'results_sha256': sha(OUT / 'results.json'),
        'process_results_sha256': sha(OUT / 'process-results.json'),
        'primary_timing_samples': 0,
    })


if __name__ == '__main__':
    main()
