"""Fresh serial Mech/Rust cohort using the unchanged protected Rust #7 source."""
import sys,json,fcntl,shutil,statistics,subprocess,random,tomllib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
WORKSPACE=Path('/private/tmp/mech-native-hashmap-performance')
EXPECTED='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
def main():
 qualified=json.loads((HERE/'qualification-v4/results.json').read_bytes());assert qualified['status']=='public-source-decoded-security-full-output-and-table-work-passed'
 assert qualified['hash_table_work_preserved'] and set(qualified['full_checks'])=={'source','decoded'}, 'Refuse a benchmark comparison until actual library hash-table work is qualified'
 prepared=json.loads((HERE/'compiler-v1/results.json').read_bytes());env={**prepared['environment'],'RUSTUP_TOOLCHAIN':'nightly-2026-03-03'}
 assert not any(k.startswith('DYLD_') for k in env)
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==qualified['source_commit']
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 out=HERE/'rust-comparison-v2';out.mkdir(exist_ok=False);b=HERE/'.build';target=b/'rust-knucleotide-deps';assert target.exists()
 source=ROOT/'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs';digest='47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851';assert process.sha(source)==digest
 inventory=json.loads((ROOT/'experiments/implementation-audit/coverage-v5/coverage.json').read_bytes());assert inventory['programs']['knucleotide:knucleotide-rust-7']['protected_upstream']
 mech=b/'knucleotide-source';assert process.sha(mech)==qualified['variants']['source']['binary_sha256']
 inp=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin';assert process.sha(inp)==qualified['input_sha256']
 policy=HERE/'qualification-v4/launch.json';assert process.sha(policy)==qualified['policy_sha256']
 dependencies=ROOT/'archive/workloads/knucleotide/rust-deps';manifest=dependencies/'Cargo.toml';lockfile=dependencies/'Cargo.lock'
 for file in ['Cargo.toml','Cargo.lock']:shutil.copyfile(dependencies/file,out/file)
 report=dict(status='running',mech_source_commit=qualified['source_commit'],input_sha256=process.sha(inp),policy_sha256=process.sha(policy),rust_source_sha256=digest,rust_protected_source_unchanged=True,rust_library_manifest_sha256=process.sha(manifest),rust_library_lock_sha256=process.sha(lockfile),environment=env,rounds=7,shuffle_seed=20261023,samples=[],scope='Fresh warm-cache processes including startup, input, complete output and shutdown. Mech includes secured native admission and security-report publication. Build and parent validation excluded. Whole implementations, not isolated security overhead.',algorithm_scope='Rust #7 retains seven complete typed hash maps and its default Tokio pool. Generated Mech producer loops perform all 874,999,961 library hash-table updates and answer queries from completed tables; runtime witnesses are required for every measured process. Both retain the specified table work; Rust uses its default Tokio pool and Mech currently uses one serial accumulator. No Rust application changes.')
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def execute(cmd,label,stdin=None,quant=False,environment=None,deadline=1200):
   r=process.execute(cmd,out/label,environment or env,lock,stdin=stdin,deadline=deadline,quantitative=quant)
   assert r['exit_status']==0,(label,(out/label/'stderr.bin').read_text()[-6000:]);return r
  for label,command in [('hardware',['/usr/sbin/sysctl','machdep.cpu.brand_string','hw.model','hw.memsize','hw.ncpu']),('os',['/usr/bin/sw_vers']),('power-source',['/usr/bin/pmset','-g','batt']),('power-settings',['/usr/bin/pmset','-g','custom']),('rust-version',['/Users/cim310/.cargo/bin/rustc','-Vv']),('cargo-version',['/Users/cim310/.cargo/bin/cargo','-Vv'])]:execute(command,label,deadline=30)
  depenv={**env,'RUSTFLAGS':env['RUSTFLAGS']+' -C target-cpu=native'}
  execute(['/Users/cim310/.cargo/bin/cargo','build','--release','--locked','--offline','--manifest-path',str(manifest),'--target-dir',str(target),'--message-format=json'],'rust-dependencies',environment=depenv)
  libs={};direct=tomllib.loads(manifest.read_text())['dependencies']
  artifacts=[json.loads(line) for line in (out/'rust-dependencies/stdout.bin').read_text().splitlines()]
  for name in ['futures','tokio_threadpool','itertools','num','hashbrown']:
   package=name.replace('_','-');version=direct[package].removeprefix('=')
   selected=[artifact for artifact in artifacts if artifact.get('reason')=='compiler-artifact' and artifact['target']['name']==name and artifact['package_id'].endswith('#'+package+'@'+version)]
   assert len(selected)==1,(name,version,[a.get('package_id') for a in artifacts if a.get('reason')=='compiler-artifact'])
   matches=[Path(file) for file in selected[0]['filenames'] if file.endswith('.rlib')]
   assert len(matches)==1,(name,matches);libs[name]=matches[0]
  rust=b/'knucleotide-rust-7';assert not rust.exists()
  command=['/Users/cim310/.cargo/bin/rustc','--edition=2021','-Copt-level=3','-Ctarget-cpu=native','-Ccodegen-units=1','-Ldependency='+str(target/'release/deps')]
  for name,path in libs.items():command+=['--extern',name+'='+str(path)]
  command += [str(source),'-o',str(rust)];execute(command,'rust-build')
  assert process.sha(source)==digest and process.sha(lockfile)==report['rust_library_lock_sha256']
  report.update(rust_compile_command=command,rust_binary_sha256=process.sha(rust),mech_binary_sha256=process.sha(mech),rust_libraries={n:dict(path=str(p),sha256=process.sha(p)) for n,p in libs.items()});process.save(out/'results.json',report)
  def run(label,subject,quant):
   binary=mech if subject=='mech' else rust;assert process.sha(binary)==report[subject+'_binary_sha256']
   cmd=[str(binary),str(policy),str(out/(label+'.security.json')),'--'] if subject=='mech' else [str(binary),'0']
   r=execute(cmd,label,stdin=inp,quant=quant,deadline=900)
   assert process.sha(out/label/'stdout.bin')==EXPECTED and (out/label/'stderr.bin').stat().st_size==0
   if subject=='mech':
    native=json.loads((out/(label+'.security.json')).read_bytes());assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation'] and native['shutdown']=='completed' and native['route']=='canonical-artifact-program-object-secured-cli'
    assert native['native_hash_table_regions']==7 and native['native_hash_table_updates']==874999961
   return r
  for subject in ['mech','rust']:run('qualification-'+subject,subject,False)
  rng=random.Random(report['shuffle_seed'])
  for round_id in range(7):
   order=['mech','rust'];rng.shuffle(order)
   for subject in order:
    label=f'round-{round_id}-{subject}';r=run(label,subject,True)
    report['samples'].append(dict(subject=subject,round=round_id,seconds=r['elapsed_seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],process=str((out/label/'process.json').relative_to(ROOT))));process.save(out/'results.json',report)
   print('Matched round',round_id,'passed',flush=True)
  stats={}
  for subject in ['mech','rust']:
   values=[s['seconds'] for s in report['samples'] if s['subject']==subject];assert len(values)==7
   stats[subject]=dict(median_seconds=statistics.median(values),sample_sd_seconds=statistics.stdev(values))
  denominator=stats['mech']['median_seconds']
  for subject in stats:stats[subject]['x_mech_aot']=stats[subject]['median_seconds']/denominator
  report.update(status='seven-matched-serial-rounds-all-full-outputs-pass',statistics=stats,denominator='This cohort canonical secured Mech AOT source executable median',full_outputs_verified=16)
  assert process.sha(source)==digest and process.sha(inp)==report['input_sha256'] and process.sha(policy)==report['policy_sha256']
  process.save(out/'results.json',report)
if __name__=='__main__':main()
