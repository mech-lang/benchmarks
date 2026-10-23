"""Probe ordinary source-level map primitives, without benchmark timing."""
import sys,json,fcntl
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
old=HERE.parent/'native-hashmap-batch-v1'
prepared=json.loads((old/'compiler-v1/results.json').read_bytes())
cli=old/'.build/mech-canonical';assert process.sha(cli)==prepared['compiler_sha256']
cases={
 'update': '~counts<{string:u64}> := {"a": 0u64}\ncounts{"a"} = counts{"a"} + 1u64\ncounts\n',
 'insert': '~counts<{string:u64}> := {"a": 0u64}\ncounts{"b"} = 1u64\ncounts\n',
 'empty': '~counts<{string:u64}> := {}\ncounts\n',
 'contains': 'counts := {"a": 1u64}\n"a" ∈ counts\n',
 'update-function': 'increment(h<{string:u64}>, key<string>) => (out<{string:u64}>) :=\n  ~counts := h\n  counts{key} = counts{key} + 1u64\n  out := counts.\nincrement({"a": 0u64}, "a")\n',
}
out=HERE/'source-probes-v1';out.mkdir(exist_ok=False);results={}
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name,source in cases.items():
  path=out/(name+'.mec');path.write_text(source)
  cmd=[str(cli),'--no-config','build',str(path),'--emit','bytecode','--offline','--name','map-counting','--workspace-root','/private/tmp/mech-native-hashmap-performance','-o',str(out/(name+'.mecb'))]
  r=process.execute(cmd,out/name,prepared['environment'],lock,deadline=120,quantitative=False)
  results[name]=dict(exit_status=r['exit_status'],source_sha256=process.sha(path),process=str(out/name/'process.json'))
  process.save(out/'results.json',dict(compiler_source_commit=prepared['source_commit'],compiler_sha256=process.sha(cli),benchmark_samples=0,cases=results))
  print(name,r['exit_status'],(out/name/'stderr.bin').read_text()[-2000:],flush=True)
