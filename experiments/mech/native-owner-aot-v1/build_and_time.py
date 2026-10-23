"""Build the candidate and compare identical source/input using complete secured processes."""
import fcntl,json,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKSPACE=Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
out=HERE/'candidate-timing-v1';out.mkdir(exist_ok=False)
prepared=json.loads((HERE/'compiler-v2/results.json').read_bytes())
assert prepared['status']=='compiler-built'
assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==prepared['source_commit']
assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
env=prepared['environment'];cli=HERE/'.build/mech-canonical'
assert process.sha(cli)==prepared['compiler_sha256']
source=HERE/'knucleotide-source-map.mec';old=HERE.parent/'native-state-aot-v1/.build/counting-source'
assert process.sha(source)==process.sha(HERE.parent/'native-state-aot-v1/knucleotide-source-map.mec')
old_results=json.loads((HERE/'available-timing-v1/results.json').read_bytes())
assert process.sha(old)==old_results['binary_sha256']
binary=HERE/'.build/counting-candidate';inp=HERE/'available-timing-v1/input.fasta';policy=HERE/'available-timing-v1/launch.json'
expected=(HERE/'available-timing-v1/run-0/stdout.bin').read_bytes()
report=dict(status='building',source_commit=prepared['source_commit'],baseline_commit=old_results['source_commit'],source_sha256=process.sha(source),input_sha256=process.sha(inp),input_bases=1000,launch_sha256=process.sha(policy),scope='identical source and 1000-base diagnostic input; fresh secured complete processes; not the full benchmark input',samples=[])
process.save(out/'results.json',report)
with Path(PLAN['common_mutex']).open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 cmd=[str(cli),'--no-config','build',str(source),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(WORKSPACE),'--name','owner-counting','-o',str(binary)]
 r=process.execute(cmd,out/'build-candidate',env,lock,deadline=3600)
 assert r['exit_status']==0,(out/'build-candidate/stderr.bin').read_text()[-6000:]
 manifest=json.loads(Path(str(binary)+'.project/linked-manifest.json').read_bytes())
 assert manifest['object']['typed_ir_version']==31 and manifest['object']['abi_version']==16
 report.update(status='timing',candidate_sha256=process.sha(binary),baseline_sha256=process.sha(old),manifest=manifest)
 process.save(out/'results.json',report)
 for i,order in enumerate([['candidate','baseline'],['baseline','candidate'],['candidate','baseline']]):
  for label in order:
   target=binary if label=='candidate' else old
   receipt=out/f'round-{i}-{label}.report.json';name=f'round-{i}-{label}'
   r=process.execute([str(target),str(policy),str(receipt),'--'],out/name,env,lock,stdin=inp,deadline=180,quantitative=True)
   assert r['exit_status']==0,(out/name/'stderr.bin').read_text()[-3000:]
   assert (out/name/'stdout.bin').read_bytes()==expected,label
   n=json.loads(receipt.read_bytes());assert n['native_aot'] and not n['jit'] and not n['resident_body_evaluation']
   s=dict(label=label,seconds=r['elapsed_seconds'],maximum_rss_bytes=r['maximum_rss_bytes'])
   report['samples'].append(s);process.save(out/'results.json',report);print(json.dumps(s),flush=True)
 medians={label:statistics.median(s['seconds'] for s in report['samples'] if s['label']==label) for label in ['candidate','baseline']}
 for s in report['samples']:s['x_mech_aot']=s['seconds']/medians['candidate']
 report.update(status='measured-identical-input-and-output-verified',median_seconds=medians,x_mech_aot={k:v/medians['candidate'] for k,v in medians.items()},denominator='Candidate Mech AOT median on this identical 1000-base diagnostic')
 process.save(out/'results.json',report);print(json.dumps({k:report[k] for k in ['median_seconds','x_mech_aot']}),flush=True)
