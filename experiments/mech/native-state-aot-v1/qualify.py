"""Bounded public AOT qualification of the source-written counting procedure."""
import fcntl,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
sys.path.insert(0,str(HERE.parent/'canonical-native-integration-v1'))
from qualify import oracle
WORKSPACE=Path('/private/tmp/mech-native-hashmap-performance')
def main():
 prepared=json.loads((HERE/'compiler-v1/results.json').read_bytes())
 assert prepared['status']=='compiler-built'
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==prepared['source_commit']
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 out=HERE/sys.argv[1];out.mkdir(exist_ok=False)
 env=prepared['environment'];b=HERE/'.build';cli=b/'mech-canonical'
 assert process.sha(cli)==prepared['compiler_sha256']
 source=HERE/'knucleotide-source-map.mec'
 assert 'map/histogram' not in source.read_text()
 policy=json.loads((HERE.parent/'native-hashmap-batch-v1/qualification-v1/launch.json').read_bytes())
 policy.update(input_text_bytes=4096,memory_bytes=536870912)
 launch=out/'launch.json';process.save(launch,policy)
 cases=[b'>ONE\nAAAA\n>THREE\nGGTA\n>FOUR\nTTTT\n',b'>THREE\n',b'>ONE\nACGT\n',b'>THREE description\r\nggta\r\nACGT\r\n>FOUR\r\nTT\r\n',b'>THREEish\nTTTT\n>THREE\tselected\nACGTTGGTATT\n',b'>THREE\nACGTACGTACGTACGTACGTACGTACGTACGTACGT\n',b'>THREE\nGGTATTTTAATTTATAGT\n']
 report=dict(status='running',source_commit=prepared['source_commit'],source_sha256=process.sha(source),compiler_sha256=process.sha(cli),policy=policy,benchmark_samples=0,hash_representation_qualified=False,full_input_qualified=False,variants={})
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def execute(cmd,name,stdin=None,extra=None,deadline=3600):
   result=process.execute(cmd,out/name,{**env,**(extra or {})},lock,stdin=stdin,deadline=deadline,quantitative=False)
   return result
  try:
   bytecode=b/'counting.mecb'
   result=execute([str(cli),'--no-config','build',str(source),'--name','source-counting','--emit','bytecode','--offline','--workspace-root',str(WORKSPACE),'-o',str(bytecode)],'bytecode')
   assert result['exit_status']==0,(out/'bytecode/stderr.bin').read_text()[-6000:]
   report['bytecode_sha256']=process.sha(bytecode)
   for variant,path in [('source',source),('decoded',bytecode)]:
    binary=b/('counting-'+variant)
    cmd=[str(cli),'--no-config','build',str(path),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(WORKSPACE),'--name','source-counting','-o',str(binary)]
    print('Build',variant,flush=True)
    result=execute(cmd,'build-'+variant)
    assert result['exit_status']==0,(out/('build-'+variant)/'stderr.bin').read_text()[-10000:]
    project=Path(str(binary)+'.project');manifest=json.loads((project/'linked-manifest.json').read_bytes())
    for relative,pin in manifest['pins'].items():assert process.sha(project/relative)==pin,relative
    metadata=manifest['object']
    assert metadata['compiled_window_histogram_regions']==0,metadata
    assert metadata['compiled_window_query_regions']==0,metadata
    report['variants'][variant]=dict(binary_sha256=process.sha(binary),build_command=cmd,manifest=manifest,cases=[])
    process.save(out/'results.json',report)
    for index,raw in enumerate(cases):
     inp=out/f'input-{index}.fasta'
     if not inp.exists():inp.write_bytes(raw)
     name=f'{variant}-case-{index}';receipt=out/(name+'.report.json')
     result=execute([str(binary),str(launch),str(receipt),'--'],name,inp,deadline=120)
     assert result['exit_status']==0,(out/name/'stderr.bin').read_text()[-5000:]
     assert (out/name/'stdout.bin').read_bytes()==oracle(raw),(variant,index,(out/name/'stdout.bin').read_bytes(),oracle(raw))
     native=json.loads(receipt.read_bytes())
     for key,value in dict(native_aot=True,jit=False,source_parser=False,resident_body_evaluation=False,shutdown='completed').items():assert native[key]==value,(key,native[key])
     assert native['native_hash_table_regions']==0 and native['native_hash_table_updates']==0,native
     report['variants'][variant]['cases'].append(dict(input_sha256=process.sha(inp),output_sha256=process.sha(out/name/'stdout.bin'),native_receipt=native))
     process.save(out/'results.json',report)
    for denied_host in ['cli/stdin','cli/stdout']:
     denied=out/f'denied-{denied_host.rsplit("/",1)[1]}.json'
     if not denied.exists():process.save(denied,{**policy,'grants':[grant for grant in policy['grants'] if grant['target']!=denied_host]})
     name=f'{variant}-denied-{denied_host.rsplit("/",1)[1]}';receipt=out/(name+'.report.json')
     result=execute([str(binary),str(denied),str(receipt),'--'],name,out/'input-0.fasta',extra={'MECH_NATIVE_SECURITY':'trusted'},deadline=30)
     assert result['exit_status']!=0 and not (out/name/'stdout.bin').stat().st_size and not receipt.exists()
    process.save(out/'results.json',report)
   assert report['variants']['source']['binary_sha256']==report['variants']['decoded']['binary_sha256']
   report['status']='bounded-source-decoded-standalone-output-and-permission-checks-passed'
  except BaseException as error:
   report.update(status='failed',failure=repr(error));raise
  finally:process.save(out/'results.json',report)
if __name__=='__main__':main()
