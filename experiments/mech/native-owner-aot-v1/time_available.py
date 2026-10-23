"""Immediate fixed-input diagnostic of the latest available standalone executable."""
import fcntl,json,random,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
sys.path.insert(0,str(HERE.parent/'canonical-native-integration-v1'))
from qualify import oracle
out=HERE/'available-timing-v1';out.mkdir(exist_ok=False)
previous=HERE.parent/'native-state-aot-v1'
qualified=json.loads((previous/'qualification-v1/results.json').read_bytes())
binary=previous/'.build/counting-source'
assert process.sha(binary)==qualified['variants']['source']['binary_sha256']
env=json.loads((HERE.parent/'canonical-native-integration-v1/validation-v2/results.json').read_bytes())['environment']
rng=random.Random(42)
text=''.join(rng.choice('ACGT') for _ in range(1000))
raw=('>THREE\n'+'\n'.join(text[i:i+60] for i in range(0,len(text),60))+'\n').encode()
inp=out/'input.fasta';inp.write_bytes(raw);expected=oracle(raw)
policy=out/'launch.json';policy.write_bytes((previous/'qualification-v1/launch.json').read_bytes())
report=dict(status='running',scope='1000-base fixed-input standalone diagnostic; complete secured process; not the full benchmark input; no current compiler-candidate claim',source_commit=qualified['source_commit'],binary_sha256=process.sha(binary),input_sha256=process.sha(inp),input_bases=1000,input_bytes=len(raw),launch_sha256=process.sha(policy),samples=[])
process.save(out/'results.json',report)
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for i in range(3):
  receipt=out/f'run-{i}.report.json'
  result=process.execute([str(binary),str(policy),str(receipt),'--'],out/f'run-{i}',env,lock,stdin=inp,deadline=180,quantitative=True)
  assert result['exit_status']==0,(out/f'run-{i}/stderr.bin').read_text()[-3000:]
  assert (out/f'run-{i}/stdout.bin').read_bytes()==expected
  native=json.loads(receipt.read_bytes());assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
  sample=dict(seconds=result['elapsed_seconds'],maximum_rss_bytes=result['maximum_rss_bytes'],x_mech_aot=1.0)
  report['samples'].append(sample);process.save(out/'results.json',report);print(json.dumps(sample),flush=True)
 report.update(status='measured-and-output-verified',median_seconds=statistics.median(s['seconds'] for s in report['samples']),median_maximum_rss_bytes=statistics.median(s['maximum_rss_bytes'] for s in report['samples']),denominator='This preserved source-written Mech AOT executable on this 1000-base diagnostic')
 process.save(out/'results.json',report)
 print(json.dumps({k:report[k] for k in ['source_commit','median_seconds','median_maximum_rss_bytes','input_bases']}),flush=True)
