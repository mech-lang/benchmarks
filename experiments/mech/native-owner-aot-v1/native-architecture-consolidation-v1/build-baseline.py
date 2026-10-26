"""Build baseline I through the public CLI; never rebuild retained W or R."""
import fcntl, importlib.util, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'tools/qualification'))
spec = importlib.util.spec_from_file_location('owned_process', ROOT/'experiments/janet/knucleotide-bytes-v1/process.py')
process = importlib.util.module_from_spec(spec); spec.loader.exec_module(process)
plan = json.loads((HERE/'plan.json').read_text())
workspace = Path('/private/tmp/mech-911-rebase')
compiler = Path('/private/tmp/native-consolidation-i-compiler')
source = Path('/private/tmp/mech-benchmark-publication/experiments/mech/native-owner-aot-v1/knucleotide-source-map.mec')
assert process.sha(source) == plan['source_sha256']

def state():
    def git(*args): return subprocess.check_output(['git','-C',str(workspace),*args],text=True).strip()
    return dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),status=git('status','--porcelain'))

before = state(); assert before['commit'] == plan['implementation_base'] and not before['status']
env = json.loads((ROOT/'experiments/mech/canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env.update(CARGO_TARGET_DIR=str(HERE/'.build/cargo-target'), TMPDIR=str(HERE/'.build/tmp'))
Path(env['TMPDIR']).mkdir(parents=True,exist_ok=True)
binary = HERE/'.build/I'
command = [str(compiler),'--no-config','build',str(source),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(workspace),'--name','native-consolidation-baseline','-o',str(binary)]
with Path(plan['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    receipt = process.execute(command,HERE/'baseline/aot-build',env,lock,deadline=1800)
    assert receipt['exit_status']==0, (HERE/'baseline/aot-build/stderr.bin').read_text()[-6000:]
assert state() == before
project = Path(str(binary)+'.project')
assert process.sha(project/'program.mecb') == plan['bytecode_sha256']
report = dict(source=before,command=command,environment=env,compiler_sha256=process.sha(compiler),source_sha256=process.sha(source),bytecode_sha256=process.sha(project/'program.mecb'),executable=str(binary),executable_sha256=process.sha(binary),object_sha256=process.sha(project/'program.o'),process_receipt='baseline/aot-build/process.json',benchmark_samples=0,status='public-baseline-built')
process.save(HERE/'baseline/public-aot.json',report)
print(json.dumps(report,indent=2))
