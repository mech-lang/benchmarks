#!/usr/bin/env python3
"""One-shot audit/adoption preparation; delegates execution to the existing owner."""
if not __debug__:
    raise RuntimeError('Optimized Python is not allowed')
import argparse, fcntl, hashlib, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path('/private/tmp/benchmarks-native-consolidation')
CODE = ROOT / 'experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1'
ARCH = CODE
CLEANUP = CODE.parent / 'post-native-architecture-cleanup-v1'
CANONICAL = ROOT / 'experiments/mech/canonical-native-integration-v1/validation-v2/results.json'
PUBLIC_TARGET = Path('/private/tmp/mech-native-consolidation-perf-target')
SOURCES = {
 'baseline': ('a093aea452340a70c1e72a1f58bd831f1edef70f', Path('/private/tmp/mech-native-base-ci-repair-next')),
 'architecture': ('7543c56d5efc4df30d0b60961922024d74caa9d7', Path('/private/tmp/mech-native-consolidation-final')),
 'cleanup': ('a68fb2e60d7afbc59bc146f8878b17181e275645', Path('/private/tmp/mech-post-native-authority-cleanup-v2'))}
CONTROLLERS = ['study.py', 'build_subject.py', 'build-baseline.py', 'build-candidate.py']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def save(p, v): Path(p).write_text(json.dumps(v, indent=2) + '\n')
def require(v, message):
    if not v: raise RuntimeError(message)
def state(path):
    def git(*args): return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
    return dict(commit=git('rev-parse','HEAD'), tree=git('rev-parse','HEAD^{tree}'), status=git('status','--porcelain'))
def pins():
    paths = [CODE / p for p in CONTROLLERS] + [ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py', ROOT / 'tools/qualification/prolog_supervisor.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}
def clean_receipt(r):
    require(r.get('exit_status') == 0 and r.get('group_closed') is True and r.get('reaped') is True, 'Process did not finish successfully')
    require(r.get('cleanup_errors') == [] and r.get('signals') == [] and not r.get('error') and not r.get('observer_still_waiting'), 'Process cleanup/deadline error')
    require(r.get('inherited_common_mutex') is True and r.get('quantitative_benchmark') is False, 'Wrong process ownership or timing status')
    require(r.get('controller_sha256') == sha(ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py'), 'Process controller differs')
def validate(base, reference, commit):
    path = base / reference
    r = read(path)
    plan = read(base / 'plan.json')
    require(r['source']['commit'] == commit and not r['source']['status'] and state(r['workspace']) == r['source'], 'Source is not exact and clean')
    require(r['benchmark_samples'] == 0 and r['status'] == 'public-subject-built', 'Build receipt status differs')
    env = read(CANONICAL)['environment']
    env.update(CARGO_TARGET_DIR=str(PUBLIC_TARGET), TMPDIR=str(path.parent / 'tmp'))
    require(r['environment'] == env, 'Canonical build environment differs')
    binary = Path(r['executable'])
    require(sha(binary) == r['executable_sha256'], 'Executable changed')
    require(sha(str(binary) + '-compiler') == r['compiler_sha256'], 'Compiler changed')
    require(sha(r['command'][3]) == r['source_sha256'] == plan['source_sha256'], 'Public source differs')
    project = Path(str(binary) + '.project')
    require(sha(project / 'program.mecb') == r['bytecode_sha256'] == plan['bytecode_sha256'], 'Bytecode differs')
    controls = read(base / 'retained-controls.json')
    winner = Path(controls['W']['path'])
    require(sha(winner) == controls['W']['sha256'], 'W executable changed')
    require(sha(Path(controls['R']['path'])) == controls['R']['sha256'], 'R executable changed')
    require(sha(project / 'program.o') == r['object_sha256'] == sha(Path(str(winner) + '.project') / 'program.o'), 'Guest Object differs from W')
    stages = {}
    for key in ('compiler_process_receipt', 'process_receipt'):
        p = base / r[key]; stage = read(p); clean_receipt(stage)
        require(stage['deadline_seconds'] == 1800, 'Build deadline differs')
        if key == 'process_receipt': require(stage['command'] == r['command'], 'AOT command differs')
        else:
            wrapper = 'import os;os.chdir(' + repr(r['workspace']) + ');os.execve(' + repr(r['compiler_command'][0]) + ',' + repr(r['compiler_command']) + ',os.environ)'
            require(stage['command'][1:] == ['-c', wrapper], 'Compiler command differs')
        stages[key] = dict(path=r[key], sha256=sha(p), elapsed_seconds=stage['elapsed_seconds'], stdout_sha256=sha(p.parent/'stdout.bin'), stderr_sha256=sha(p.parent/'stderr.bin'))
    result = dict(status='validated-public-build-no-primary-observations', receipt=reference, receipt_sha256=sha(path), source=r['source'], controller_pins=pins(), canonical_build_environment_sha256=sha(CANONICAL), executable_sha256=sha(binary), executable_size_bytes=binary.stat().st_size, compiler_sha256=r['compiler_sha256'], guest_artifacts={n:sha(project/n) for n in ('program.o','program.mecb','native-descriptor.bin','native-descriptor.json','native-resources.json','object-identity.bin')}, stages=stages, benchmark_samples=0, validation_driver_sha256=sha(__file__))
    save(path.parent / 'adoption-validation.json', result)
    shutil.copy2(__file__, path.parent / 'adoption-validation.py')
    print(json.dumps(result, indent=2))
def clean(which):
    commit, workspace = SOURCES[which]
    base = ARCH if which in ('baseline', 'architecture') else CLEANUP
    dest = base / 'public-cache-preparation' / ('adopted-' + commit[:7] + '-v1')
    dest.mkdir(parents=True, exist_ok=False)
    before = state(workspace)
    require(before['commit'] == commit and not before['status'], 'Workspace differs')
    require(PUBLIC_TARGET.is_dir(), 'Expected existing public cache')
    metadata_cmd = ['/Users/cim310/.cargo/bin/cargo','+nightly-2026-03-03','metadata','--format-version','1','--no-deps','--locked','--offline']
    metadata = subprocess.check_output(metadata_cmd, cwd=workspace)
    (dest/'workspace-metadata.json').write_bytes(metadata)
    m = json.loads(metadata)
    names = sorted(p['name'] for p in m['packages'] if p['id'] in m['workspace_members'])
    expected = sorted(read('/private/tmp/native-consolidation-final-perf-cache.json')['cleaned_all_workspace_packages'])
    require(names == expected, 'Workspace package set changed; review before cleaning')
    command = ['/Users/cim310/.cargo/bin/cargo','+nightly-2026-03-03','clean','--locked','--offline','--target-dir',str(PUBLIC_TARGET)]
    for name in names: command += ['-p',name]
    env = read(CANONICAL)['environment']; env.update(CARGO_TARGET_DIR=str(PUBLIC_TARGET), TMPDIR=str(dest/'tmp'))
    (dest/'tmp').mkdir()
    context = dict(source=before, workspace=str(workspace), target=str(PUBLIC_TARGET), command=command, environment=env, workspace_packages=names, controller_pins=pins(), driver_sha256=sha(__file__), purpose='Reuse external dependency cache only; clean every workspace package across checkout paths. Pinned public executables and generated projects live outside the target and remain untouched.')
    save(dest/'context.json',context); shutil.copy2(__file__,dest/'executed-driver.py')
    old = sys.argv; sys.argv = [str(__file__)]; sys.path.insert(0,str(CODE))
    import study
    sys.argv = old
    mutex = Path('/private/tmp/mech-clbg-timing.lock')
    require(mutex.stat().st_ino == 83858837, 'Mutex inode changed')
    wrapper = 'import os;os.chdir(' + repr(str(workspace)) + ');os.execve(' + repr(command[0]) + ',' + repr(command) + ',os.environ)'
    with mutex.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        receipt = study.process.execute([sys.executable,'-c',wrapper],dest/'clean',env,lock,deadline=180)
    clean_receipt(receipt)
    require(state(workspace) == before and pins() == context['controller_pins'], 'Source or controller changed')
    save(dest/'receipt.json',dict(status='workspace-packages-cleaned-external-cache-retained',context_sha256=sha(dest/'context.json'),process_sha256=sha(dest/'clean/process.json'),source_after=state(workspace)))
    print(str(dest))
if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['validate','clean']); p.add_argument('study',choices=['baseline','architecture','cleanup']); p.add_argument('--receipt'); p.add_argument('--commit'); a=p.parse_args()
    if a.mode=='validate': validate(ARCH if a.study in ('baseline','architecture') else CLEANUP,a.receipt,a.commit)
    else: clean(a.study)
