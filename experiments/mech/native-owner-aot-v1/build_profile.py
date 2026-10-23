"""Relink only the profiling shell with symbols; keep the same generated Mech Object."""
import argparse,fcntl,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
from analyze_profile import text_section, sha
parser=argparse.ArgumentParser()
parser.add_argument('--receipt',default='profile-build-v2')
parser.add_argument('--source',default='counting-candidate')
parser.add_argument('--output',default='counting-profile')
parser.add_argument('--package',default='owner-counting')
parser.add_argument('--compiler',default='compiler-v2')
parser.add_argument('--target')
args=parser.parse_args()
out=HERE/args.receipt;out.mkdir(exist_ok=False)
source=HERE/'.build'/f'{args.source}.project';project=HERE/'.build'/f'{args.receipt}.project'
shutil.copytree(source,project)
cargo=project/'Cargo.toml'
assert process.sha(source/'program.o')==process.sha(project/'program.o')
prepared=json.loads((HERE/args.compiler/'results.json').read_bytes())
workspace=Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git','-C',str(workspace),'rev-parse','HEAD'],text=True).strip()==prepared['source_commit']
# Match CargoInvocation::build_linked_native_host, including its environment
# isolation and final-host FatLTO. Preserve symbols only in the final binary.
env={k:v for k,v in prepared['environment'].items() if not ((k.startswith('CARGO_') and k!='CARGO_HOME') or (k.startswith('RUST') and k!='RUSTUP_HOME'))}
target=Path(args.target or workspace/'target/mech-native/cargo-target')
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 cmd=['/Users/cim310/.cargo/bin/cargo','+nightly-2026-03-03','rustc','--manifest-path',str(cargo),'--release','--offline','--locked','--jobs','1','--bin',args.package,'--target-dir',str(target),'--','-C','lto=fat','-C','codegen-units=1','-C','strip=none']
 r=process.execute(cmd,out/'build',env,lock,deadline=1800)
 assert r['exit_status']==0,(out/'build/stderr.bin').read_text()[-4000:]
 binary=HERE/'.build'/args.output;shutil.copy2(target/'release'/args.package,binary)
 code=text_section(binary);assert code==text_section(HERE/'.build'/args.source), 'Profiling executable has different machine code'
 process.save(out/'results.json',dict(status='profile-binary-built',source_commit=prepared['source_commit'],binary=str(binary),binary_sha256=process.sha(binary),object_sha256=process.sha(project/'program.o'),candidate_object_sha256=process.sha(source/'program.o'),machine_code_bytes=len(code),machine_code_sha256=sha(code),whole_machine_code_matches_timed=True,host_optimization='release opt-level=3; final host lto=fat and codegen-units=1; dependency ThinLTO; same as public CLI',only_package_profile_override=f'strip=none for {args.package}',environment=env,benchmark_samples=0))
 print('Profiling binary built with the same Mech Object.',flush=True)
