"""Verify public source/decoded executable qualification without hashing claims."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'canonical-native-integration-v1'))
from qualify import oracle
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
SOURCE='f6fb76f5f284b8731368a5d30028cc1663c2bb03'
METADATA='c303620e657af9a856f01d660654fc368813c0b6'
DATA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
BINARY='a7c22076b2a3e65d5c84e1d616ac2cc5d263e26121536add1c9b64cfa03a0398'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path,commit):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def build():
 attempts={}
 for path in sorted(HERE.rglob('process.json')):
  if '.build' in path.parts:continue
  record=json.loads(path.read_bytes())
  assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'],path
  assert not record['quantitative_benchmark'],path
  attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':record['exit_status']}
 compiler=json.loads((HERE/'compiler-v1/results.json').read_bytes())
 assert compiler['status']=='compiler-built' and compiler['source_commit']==SOURCE
 report=json.loads((HERE/'qualification-v1/results.json').read_bytes())
 assert report['status']=='bounded-source-decoded-standalone-output-and-permission-checks-passed'
 assert report['source_commit']==SOURCE and report['benchmark_samples']==0
 assert not report['hash_representation_qualified'] and not report['full_input_qualified']
 source=(HERE/'knucleotide-source-map.mec').read_bytes()
 assert sha(source)==report['source_sha256'] and b'map/histogram' not in source
 assert b'previous + 1u64' in source and b'counts := #Count' in source and b'@out/text <-' in source
 cases=0;denials=0
 for variant in ['source','decoded']:
  value=report['variants'][variant]
  assert value['binary_sha256']==BINARY
  assert len(value['cases'])==7
  assert value['manifest']['object']['compiled_window_histogram_regions']==0
  assert value['manifest']['object']['compiled_window_query_regions']==0
  for index,case in enumerate(value['cases']):
   base=HERE/'qualification-v1'/f'{variant}-case-{index}'
   assert json.loads((base/'process.json').read_bytes())['exit_status']==0
   output=(base/'stdout.bin').read_bytes()
   raw=(HERE/'qualification-v1'/f'input-{index}.fasta').read_bytes()
   assert sha(raw)==case['input_sha256'] and output==oracle(raw)
   assert sha(output)==case['output_sha256']
   actual=json.loads((HERE/'qualification-v1'/f'{variant}-case-{index}.report.json').read_bytes())
   assert actual==case['native_receipt']
   for key,expected in dict(native_aot=True,jit=False,source_parser=False,resident_body_evaluation=False,shutdown='completed',native_hash_table_regions=0,native_hash_table_updates=0).items():assert actual[key]==expected,(key,actual[key])
   cases+=1
  for host in ['stdin','stdout']:
   base=HERE/'qualification-v1'/f'{variant}-denied-{host}'
   assert json.loads((base/'process.json').read_bytes())['exit_status']!=0
   assert not (base/'stdout.bin').stat().st_size
   assert not (HERE/'qualification-v1'/f'{variant}-denied-{host}.report.json').exists()
   denials+=1
 expected=[2,0]
 log=(HERE/'metadata-v1/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',log)]==expected
 assert json.loads((HERE/'metadata-v1/process.json').read_bytes())['exit_status']==0
 assert 'native_structural_metadata_names_only_a_selected_window_accumulator ... ok' in log
 path='hosts/gpu/src/native_artifact/program_compiler.rs'
 before=blob(path,SOURCE);after=blob(path,METADATA)
 assert before.split(b'pub fn emit_program_object(',1)[1]==after.split(b'pub fn emit_program_object(',1)[1]
 assert b'window_regions.is_empty()).then_some' in after
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.source-map-standalone-aot.v1',qualified_compiler_commit=SOURCE,metadata_fix_commit=METADATA,
  benchmark_samples=0,canonical_dataset_sha256=DATA,source_sha256=sha(source),binary_sha256=BINARY,
  standalone_source_decoded_qualified=True,identical_executables=True,bounded_output_cases=cases,permission_denials=denials,
  metadata_checks=2,hash_representation_qualified=False,full_input_work_qualified=False,same_binary_benchmark_policy_qualified=False,
  closed_attempts=attempts,evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified 14 standalone output cases, four permission denials, identical source/decoded executables, two metadata checks, {len(result['closed_attempts'])} closed attempts and zero benchmark samples; physical hashing/full input remain unqualified.")
