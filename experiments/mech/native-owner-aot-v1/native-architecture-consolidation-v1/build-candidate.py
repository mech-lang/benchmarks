"""Build F through the pinned public CLI; keep I, W and R immutable."""
import fcntl,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools/qualification'))
spec=importlib.util.spec_from_file_location('owned_process',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
workspace=Path('/private/tmp/mech-native-consolidation')
source=Path('/private/tmp/mech-benchmark-publication/experiments/mech/native-owner-aot-v1/knucleotide-source-map.mec')
plan=json.loads((HERE/'plan.json').read_text())
assert process.sha(source)==plan['source_sha256']
def state():
 def git(*args):return subprocess.check_output(['git','-C',str(workspace),*args],text=True).strip()
 return dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),status=git('status','--porcelain'))
before=state();assert before['commit']=='d4672186304325df2fdd2f50e37225bf34fd0adb' and not before['status']
env=json.loads((ROOT/'experiments/mech/canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env.update(CARGO_TARGET_DIR='/private/tmp/mech-native-consolidation-perf-target',TMPDIR=str(HERE/'.build/F-tmp'))
Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
compiler=HERE/'.build/F-compiler';binary=HERE/'.build/F'
assert not compiler.exists() and not binary.exists()
(HERE/'candidate').mkdir(exist_ok=True)
compiler_cmd=[str(Path('/Users/cim310/.cargo/bin/cargo')),'+nightly-2026-03-03','build','--locked','--offline','--bin','mech','--no-default-features','--features','cli_core,full_compiler,cranelift_build,system_gmp,mech-build/standard-hosts']
command=[str(compiler),'--no-config','build',str(source),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(workspace),'--name','native-consolidation-candidate','-o',str(binary)]
assert Path(plan['common_mutex']).is_file()
with Path(plan['common_mutex']).open('r+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 wrapper='import os;os.chdir('+repr(str(Path('/private/tmp/mech-native-consolidation')))+');os.execve('+repr(compiler_cmd[0])+','+repr(compiler_cmd)+',os.environ)'
 receipt=process.execute([sys.executable,'-c',wrapper],HERE/'candidate/compiler-build-v2',env,lock,deadline=1800)
 assert receipt['exit_status']==0,(HERE/'candidate/compiler-build-v2/stderr.bin').read_text()[-9000:]
 shutil.copy2(Path(env['CARGO_TARGET_DIR'])/'debug/mech',compiler)
 receipt=process.execute(command,HERE/'candidate/aot-build',env,lock,deadline=1800)
 assert receipt['exit_status']==0,(HERE/'candidate/aot-build/stderr.bin').read_text()[-9000:]
assert state()==before
project=Path(str(binary)+'.project')
assert process.sha(project/'program.mecb')==plan['bytecode_sha256']
report=dict(source=before,compiler_command=compiler_cmd,command=command,environment=env,compiler_sha256=process.sha(compiler),source_sha256=process.sha(source),bytecode_sha256=process.sha(project/'program.mecb'),executable=str(binary),executable_sha256=process.sha(binary),object_sha256=process.sha(project/'program.o'),object_matches_baseline=process.sha(project/'program.o')=='a45687cbcb1d8824a1de595545192e14b075462e309cbd3796286f04b1667f4c',compiler_process_receipt='candidate/compiler-build-v2/process.json',process_receipt='candidate/aot-build/process.json',benchmark_samples=0,status='public-candidate-built')
process.save(HERE/'candidate/public-aot.json',report)
print(json.dumps(report,indent=2))
