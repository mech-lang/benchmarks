"""Fresh, explicitly adopted public builds of I or F; retained controls stay pinned."""
import argparse
import fcntl
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from study import HERE, ROOT, RETAINED, process, read, source_state


def allocate(subject, run_id):
    assert subject in ('I', 'F')
    assert run_id and all(c.isalnum() or c in '-_' for c in run_id)
    receipts = HERE / ('baseline-builds' if subject == 'I' else 'candidate-builds') / run_id
    binary = HERE / '.build' / f'{subject}-{run_id}'
    assert not binary.exists() and not Path(str(binary) + '.project').exists()
    assert not Path(str(binary) + '-compiler').exists()
    receipts.mkdir(parents=True, exist_ok=False)
    binary.parent.mkdir(exist_ok=True)
    return receipts, binary


def main(subject):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--target-dir', required=True, type=Path)
    parser.add_argument('--run-id', default=uuid.uuid4().hex)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    plan = read(HERE / 'plan.json')
    before = source_state(workspace)
    expected = plan['implementation_base' if subject == 'I' else 'final_compiler_source']
    assert before['commit'] == expected and not before['status']
    source = RETAINED / 'experiments/mech/native-owner-aot-v1/knucleotide-source-map.mec'
    assert process.sha(source) == plan['source_sha256']
    receipts, binary = allocate(subject, args.run_id)
    compiler = Path(str(binary) + '-compiler')
    env = read(ROOT / 'experiments/mech/canonical-native-integration-v1/validation-v2/results.json')['environment']
    env.update(CARGO_TARGET_DIR=str(args.target_dir.resolve()), TMPDIR=str(receipts / 'tmp'))
    Path(env['TMPDIR']).mkdir()
    compiler_cmd = ['/Users/cim310/.cargo/bin/cargo', '+nightly-2026-03-03', 'build', '--locked', '--offline', '--bin', 'mech', '--no-default-features', '--features', 'cli_core,full_compiler,cranelift_build,system_gmp,mech-build/standard-hosts']
    command = [str(compiler), '--no-config', 'build', str(source), '--backend', 'cranelift', '--profile', 'release', '--keep-project', '--offline', '--workspace-root', str(workspace), '--name', 'native-consolidation-' + subject.lower(), '-o', str(binary)]
    mutex = Path(plan['common_mutex'])
    assert mutex.is_file() and mutex.stat().st_ino == 83858837
    with mutex.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        wrapper = 'import os;os.chdir(' + repr(str(workspace)) + ');os.execve(' + repr(compiler_cmd[0]) + ',' + repr(compiler_cmd) + ',os.environ)'
        for stage, cmd in [('compiler-build', [sys.executable, '-c', wrapper]), ('aot-build', command)]:
            receipt = process.execute(cmd, receipts / stage, env, lock, deadline=1800)
            assert receipt['exit_status'] == 0, (receipts / stage / 'stderr.bin').read_text()[-9000:]
            if stage == 'compiler-build':
                assert not compiler.exists()
                shutil.copy2(Path(env['CARGO_TARGET_DIR']) / 'debug/mech', compiler)
    assert source_state(workspace) == before
    project = Path(str(binary) + '.project')
    assert process.sha(project / 'program.mecb') == plan['bytecode_sha256']
    report = dict(subject=subject, source=before, workspace=str(workspace), compiler_command=compiler_cmd, command=command, environment=env,
                  compiler_sha256=process.sha(compiler), source_sha256=process.sha(source), bytecode_sha256=process.sha(project / 'program.mecb'),
                  executable=str(binary), executable_sha256=process.sha(binary), object_sha256=process.sha(project / 'program.o'),
                  compiler_process_receipt=str((receipts / 'compiler-build/process.json').relative_to(HERE)),
                  process_receipt=str((receipts / 'aot-build/process.json').relative_to(HERE)), benchmark_samples=0, status='public-subject-built')
    report_path = receipts / 'public-aot.json'
    process.save(report_path, report)
    print(json.dumps(report, indent=2))
    print('Adopt explicitly in plan.json: ' + ('baseline_receipt' if subject == 'I' else 'candidate_receipt') + ' = ' + str(report_path.relative_to(HERE)))
