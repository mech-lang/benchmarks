"""Qualify public native builds and physical table work before admitting timing."""
import sys,json,fcntl,shutil,subprocess,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'revcomp-streaming-v1'))
from build_baseline import PLAN,process
sys.path.insert(0,str(HERE.parent/'canonical-native-integration-v1'))
from qualify import oracle
WORKSPACE=Path('/private/tmp/mech-native-hashmap-performance')
def main():
 prepared=json.loads((HERE/'compiler-v1/results.json').read_bytes());assert prepared['status']=='compiler-built'
 assert subprocess.check_output(['git','-C',str(WORKSPACE),'rev-parse','HEAD'],text=True).strip()==prepared['source_commit']
 assert not subprocess.check_output(['git','-C',str(WORKSPACE),'status','--porcelain'])
 log=(HERE/'tests-v6/stdout.bin').read_text();assert '166 passed; 0 failed' in log
 r=json.loads((HERE/'tests-v6/process.json').read_bytes());assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors']
 resume='--resume-preparation' in sys.argv
 out=HERE/('qualification-v2' if resume else 'qualification-v1');out.mkdir(exist_ok=False);b=HERE/'.build';env=prepared['environment'];cli=b/'mech-canonical'
 assert process.sha(cli)==prepared['compiler_sha256']
 source=out/'knucleotide.mec';shutil.copyfile(WORKSPACE/'hosts/gpu/tests/fixtures/native/knucleotide-idiomatic.mec',source)
 assert process.sha(source)=='12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f'
 full=ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
 assert process.sha(full)=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
 # Large but finite collision envelopes bound the actual pinned library,
 # including unfavourable hashing; no unlimited or refreshed work account.
 policy=dict(grants=[dict(target='cli/stdin',operations=['read'],paths=['text']),dict(target='cli/stdout',operations=['write'],paths=['text'])],max_ports=16,input_text_bytes=full.stat().st_size,output_text_bytes=1048576,memory_bytes=1073741824,work=1<<56,transport_bytes=16777216,native_stack_bytes=1048576,library=dict(output_elements=1000000,output_bytes=134217728,temporary_bytes=536870912,cloned_bytes=536870912,retained_nodes=1000000,compute_work=1<<54,comparison_work=1<<50))
 launch=out/'launch.json';process.save(launch,policy)
 cases=[b'>ONE\nAAAA\n>THREE\nGGTA\n>FOUR\nTTTT\n',b'>THREE\n',b'>ONE\nACGT\n',b'>THREE description\r\nggta\r\nACGT\r\n>FOUR\r\nTT\r\n',b'>THREEish\nTTTT\n>THREE\tselected\nACGTTGGTATT\n',b'>THREE\n' + b'ACGTGGTA'*500+b'\n']
 report=dict(status='running',hash_table_work_preserved=False,benchmark_admission_allowed=False,source_commit=prepared['source_commit'],source_sha256=process.sha(source),input_sha256=process.sha(full),input_bytes=full.stat().st_size,selected_bases=125000000,required_table_regions=7,required_table_updates=874999961,policy=policy,policy_sha256=process.sha(launch),scope='Public source/decoded secured native AOT correctness, actual table updates, denial and lifecycle; zero benchmark timing samples.',variants={},samples=[])
 process.save(out/'results.json',report)
 with Path(PLAN['common_mutex']).open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def execute(cmd,dest,stdin=None,extra=None,deadline=1800):
   return process.execute(cmd,dest,{**env,**(extra or {})},lock,stdin=stdin,deadline=deadline,quantitative=False)
  try:
   for label,command in [('hardware',['/usr/sbin/sysctl','machdep.cpu.brand_string','hw.model','hw.memsize','hw.ncpu']),('os',['/usr/bin/sw_vers']),('power-source',['/usr/bin/pmset','-g','batt']),('power-settings',['/usr/bin/pmset','-g','custom'])]:
    r=execute(command,out/label,deadline=30);assert r['exit_status']==0,(out/label/'stderr.bin').read_text()
   bytecode=b/'knucleotide.mecb'
   if resume:
    seed=HERE/'qualification-v1'
    assert json.loads((seed/'results.json').read_bytes())['status']=='failed'
    assert process.sha(seed/'knucleotide.mec')==process.sha(source)
    for label in ['bytecode','build-source']:
     previous=json.loads((seed/label/'process.json').read_bytes())
     assert previous['exit_status']==0 and previous['reaped'] and previous['group_closed'] and not previous['cleanup_errors']
    report['reused_preparation']=dict(directory=str(seed),bytecode_sha256=process.sha(bytecode))
   else:
    r=execute([str(cli),'--no-config','build',str(source),'--name','canonical-knucleotide','--emit','bytecode','--offline','--workspace-root',str(WORKSPACE),'-o',str(bytecode)],out/'bytecode')
    assert r['exit_status']==0,(out/'bytecode/stderr.bin').read_text()[-5000:]
   for variant,src in [('source',source),('decoded',bytecode)]:
    binary=b/('knucleotide-'+variant)
    cmd=[str(cli),'--no-config','build',str(src),'--backend','cranelift','--profile','release','--keep-project','--offline','--workspace-root',str(WORKSPACE),'--name','canonical-knucleotide','-o',str(binary)]
    if resume and variant=='source':
     print('Reuse verified completed source build',flush=True)
    else:
     print('Build',variant,flush=True);r=execute(cmd,out/('build-'+variant),deadline=3600)
     assert r['exit_status']==0,(out/('build-'+variant)/'stderr.bin').read_text()[-6000:]
    project=Path(str(binary)+'.project');manifest=json.loads((project/'linked-manifest.json').read_bytes())
    for relative,pin in manifest['pins'].items():assert process.sha(project/relative)==pin,relative
    metadata=manifest['object'];assert metadata['compiled_window_accumulator']=='hashbrown-0.15.5-entry-updates'
    assert metadata['compiled_window_query_regions']==1 and metadata['compiled_window_histogram_regions']==1 # two static functions, seven dynamic invocations
    report['variants'][variant]=dict(binary_sha256=process.sha(binary),build_command=cmd,manifest=manifest,build_reused_from=str(HERE/'qualification-v1/build-source/process.json') if resume and variant=='source' else None)
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
   for variant in ['source','decoded']:
    label=f'full-{variant}';receipt=out/(label+'.report.json');binary=b/('knucleotide-'+variant)
    r=execute([str(binary),str(launch),str(receipt),'--'],out/label,full,deadline=900)
    assert r['exit_status']==0,(out/label/'stderr.bin').read_text()[-4000:]
    assert process.sha(out/label/'stdout.bin')=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
    native=json.loads(receipt.read_bytes());assert native['native_aot'] and not native['resident_body_evaluation'] and native['shutdown']=='completed'
    assert native['native_hash_table_regions']==7 and native['native_hash_table_updates']==874999961,native
    process.save(out/'results.json',report);print(label,'passed with all required table updates',flush=True)
   report.update(status='public-source-decoded-security-full-output-and-table-work-passed',hash_table_work_preserved=True,benchmark_admission_allowed=False,benchmark_admission_reason='Correctness and required work passed; a new measured cohort and admission remain separate.')
  except BaseException as error:
   report.update(status='failed',failure=repr(error));raise
  finally:
   assert not report['samples'];process.save(out/'results.json',report)
if __name__=='__main__':main()
