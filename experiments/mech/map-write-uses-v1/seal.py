"""Pin use-analysis evidence without claiming mutable owner lowering."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='013f1a8a4c2ce143cdbaeb4e0d91c31f6ce815a3'
BASE='18d4dc7cb8e7e3b6a24fdb063c19433fc041d0d8'
DATA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path):return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=ROOT)
def build():
 attempts={}
 for path in sorted(HERE.rglob('process.json')):
  record=json.loads(path.read_bytes())
  assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'],path
  assert not record['quantitative_benchmark'],path
  attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':record['exit_status']}
 assert len(attempts)==6
 assert [attempts[f'uses-v{i}/process.json']['exit_status'] for i in range(1,6)]==[101,0,101,101,0]
 assert attempts['engine-guards-v1/process.json']['exit_status']==0
 final=(HERE/'uses-v5/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',final)]==[9]
 assert len(re.findall(r'test native_map_write_use_analysis_.* \.\.\. ok',final))==4
 guard=(HERE/'engine-guards-v1/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',guard)]==[198,1]
 assert 'counted application requires a pure scalar or flat matrix carrier' in (HERE/'uses-v1/stderr.bin').read_text()
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'src/engine/src/native_artifact/mod.rs','src/engine/src/native_artifact/map_write_uses.rs','src/stdlib/tests/native_map_entries.rs'}
 analysis=blob('src/engine/src/native_artifact/map_write_uses.rs')
 assert b'ACGT' not in analysis and b'knucleotide' not in analysis
 assert b'core::mem::replace' not in analysis
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.map-write-uses.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_distinct_checks=208,passing_analysis_tests=4,
  analysis_source_and_decoded_cases=22,source_hash_contract=False,native_owner_lowering_qualified=False,
  runtime_storage_selection_changed=False,repeated_map_application_qualified=False,full_input_work_qualified=False,
  closed_attempts=attempts,compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified 208 distinct checks, 22 source/decoded analysis cases, six closed attempts and zero benchmark samples. Owner lowering remains unfinished.')
