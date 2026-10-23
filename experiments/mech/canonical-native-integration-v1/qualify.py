"""Public source/bytecode native builds, denials, exact outputs and fresh-process timing."""
import sys,json,fcntl,shutil,statistics,subprocess,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process,WORKSPACE

def oracle(raw):
 lines=raw.decode().splitlines();selected=[];active=False
 for line in lines:
  if line.startswith('>'):
   if active: break
   active=line=='>'+'THREE' or line.startswith('>THREE ') or line.startswith('>THREE\t')
  elif active: selected.append(line)
 s=''.join(selected).upper();out=''
 for width in [1,2]:
  counts={}
  for i in range(max(0,len(s)-width+1)):
   word=s[i:i+width];counts[word]=counts.get(word,0)+1
  total=sum(counts.values())
  out+=''.join(f'{k} {100*v/total:.3f}\n' for k,v in sorted(counts.items(),key=lambda p:(-p[1],p[0])))+'\n'
  if not counts:out+='\n'
 for q in ['GGT','GGTA','GGTATT','GGTATTTTAATT','GGTATTTTAATTTATAGT']:
  out+=f'{sum(s[i:i+len(q)]==q for i in range(max(0,len(s)-len(q)+1)))}\t{q}\n'
 return out.encode()

def main():
 validation=json.loads((HERE/'validation-v1/results.json').read_bytes());assert validation['status']=='integration-tests-and-compiler-build-passed'
 correction=json.loads((HERE/'corrected-contracts-v1/results.json').read_bytes());assert correction['status']=='final-head-native-contracts-passed'
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==correction['source_commit']
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 out=HERE/'qualification-v1';out.mkdir(exist_ok=False);b=HERE/'.build';env=validation['environment'];cli=b/'mech-canonical'
 assert process.sha(cli)==validation['compiler_sha256']
 source=out/'knucleotide.mec';shutil.copyfile(WORKSPACE/'hosts/gpu/tests/fixtures/native/knucleotide-idiomatic.mec',source)
 assert process.sha(source)=='12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f'
 full=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
 assert process.sha(full)=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
 policy=dict(grants=[dict(target='cli/stdin',operations=['read'],paths=['text']),dict(target='cli/stdout',operations=['write'],paths=['text'])],max_ports=16,input_text_bytes=full.stat().st_size,output_text_bytes=1048576,memory_bytes=1073741824,work=1<<48,transport_bytes=16777216,native_stack_bytes=1048576,library=dict(output_elements=1000000,output_bytes=134217728,temporary_bytes=536870912,cloned_bytes=536870912,retained_nodes=1000000,compute_work=1<<46,comparison_work=1<<40))
 launch=out/'launch.json';process.save(launch,policy)
 cases=[b'>ONE\nAAAA\n>THREE\nGGTA\n>FOUR\nTTTT\n',b'>THREE\n',b'>ONE\nACGT\n',b'>THREE description\r\nggta\r\nACGT\r\n>FOUR\r\nTT\r\n',b'>THREEish\nTTTT\n>THREE\tselected\nACGTTGGTATT\n',b'>THREE\n' + b'ACGTGGTA'*500+b'\n']
 report=dict(status='running',integration_commit=correction['source_commit'],production_source_validated_at=validation['integration_commit'],source_sha256=process.sha(source),input_sha256=process.sha(full),input_bytes=full.stat().st_size,selected_bases=125000000,policy_sha256=process.sha(launch),benchmark_scope='fresh-process startup through exit including secured capture, native computation, output and report; build and parent validation excluded; warm filesystem cache',variants={},samples=[])
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def execute(cmd,dest,stdin=None,quant=False,extra=None,deadline=1800):
   r=process.execute(cmd,dest,{**env,**(extra or {})},lock,stdin=stdin,deadline=deadline,quantitative=quant)
   return r
  bytecode=b/'knucleotide.mecb'
  r=execute([str(cli),'--no-config','build',str(source),'--emit','bytecode','--offline','--workspace-root',str(WORKSPACE),'-o',str(bytecode)],out/'bytecode')
  assert r['exit_status']==0,(out/'bytecode/stderr.bin').read_text()[-5000:]
  for variant,src in [('source',source),('decoded',bytecode)]:
   binary=b/('knucleotide-'+variant)
   cmd=[str(cli),'--no-config','build',str(src),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(WORKSPACE),'--name','canonical-knucleotide','-o',str(binary)]
   print('Build',variant,flush=True);r=execute(cmd,out/('build-'+variant))
   assert r['exit_status']==0,(out/('build-'+variant)/'stderr.bin').read_text()[-6000:]
   project=Path(str(binary)+'.project');manifest=json.loads((project/'linked-manifest.json').read_bytes())
   for relative,pin in manifest['pins'].items():assert process.sha(project/relative)==pin,relative
   report['variants'][variant]=dict(binary_sha256=process.sha(binary),build_command=cmd,manifest=manifest)
   for index,raw in enumerate(cases):
    inp=out/f'input-{index}.fasta'
    if not inp.exists():inp.write_bytes(raw)
    dest=out/f'{variant}-case-{index}';receipt=out/f'{variant}-case-{index}.report.json'
    r=execute([str(binary),str(launch),str(receipt),'--'],dest,inp)
    assert r['exit_status']==0,(dest/'stderr.bin').read_text()[-4000:]
    assert (dest/'stdout.bin').read_bytes()==oracle(raw),(variant,index,(dest/'stdout.bin').read_bytes(),oracle(raw))
    native=json.loads(receipt.read_bytes())
    for k,v in dict(route='canonical-artifact-program-object-secured-cli',native_aot=True,jit=False,source_parser=False,resident_body_evaluation=False,shutdown='completed').items():assert native[k]==v,(k,native[k])
   denied=out/'denied.json'
   if not denied.exists():process.save(denied,{**policy,'grants':policy['grants'][1:]})
   r=execute([str(binary),str(denied),str(out/f'{variant}-denied.report.json'),'--'],out/f'{variant}-denied',out/'input-0.fasta',extra={'MECH_NATIVE_SECURITY':'trusted'})
   assert r['exit_status']!=0 and (out/f'{variant}-denied/stdout.bin').stat().st_size==0 and not (out/f'{variant}-denied.report.json').exists()
   process.save(out/'results.json',report)
  assert report['variants']['source']['binary_sha256']==report['variants']['decoded']['binary_sha256']
  for round_id in range(4):
   for variant in (['source','decoded'] if round_id%2==0 else ['decoded','source']):
    label=f'full-{round_id}-{variant}';receipt=out/(label+'.report.json');binary=b/('knucleotide-'+variant)
    r=execute([str(binary),str(launch),str(receipt),'--'],out/label,full,quant=round_id>0,deadline=120)
    assert r['exit_status']==0,(out/label/'stderr.bin').read_text()[-4000:]
    assert process.sha(out/label/'stdout.bin')=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    native=json.loads(receipt.read_bytes());assert native['native_aot'] and not native['resident_body_evaluation'] and native['shutdown']=='completed'
    if round_id>0:report['samples'].append(dict(variant=variant,round=round_id,seconds=r['elapsed_seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],process=str((out/label/'process.json').relative_to(ROOT)),security_report=str(receipt.relative_to(ROOT))))
    process.save(out/'results.json',report);print(label,'passed',flush=True)
  report['medians_seconds']={v:statistics.median(s['seconds'] for s in report['samples'] if s['variant']==v) for v in ['source','decoded']}
  report['status']='public-source-decoded-security-and-full-timing-passed';process.save(out/'results.json',report)
if __name__=='__main__':main()
