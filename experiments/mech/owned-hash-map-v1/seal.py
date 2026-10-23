"""Verify owned storage in isolation, without claiming native integration."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='18d4dc7cb8e7e3b6a24fdb063c19433fc041d0d8'
BASE='c303620e657af9a856f01d660654fc368813c0b6'
DATA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path):return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=ROOT)
def build():
 attempts={}
 for path in sorted(HERE.rglob('process.json')):
  record=json.loads(path.read_bytes())
  assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'],path
  assert not record['quantitative_benchmark'] and record['exit_status']==0,path
  attempts[str(path.relative_to(HERE))]=sha(path.read_bytes())
 log=(HERE/'native-regressions-v1/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',log)]==[179,0]
 assert len(re.findall(r'test native_artifact::owned_string_map::tests::.* \.\.\. ok',log))==9
 assert '3 ignored;' in log
 for name in ['owned_map_denies_work_before_hashing_and_cannot_refill_on_retry','owned_map_replacement_peak_has_an_exact_and_one_short_boundary','owned_map_uses_library_hashing_under_complete_collisions_and_repeated_growth']:
  assert name+' ... ok' in log
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'hosts/gpu/src/native_artifact/mod.rs','hosts/gpu/src/native_artifact/owned_string_map.rs','hosts/gpu/src/native_artifact/owned_string_map_tests.rs'}
 source=blob('hosts/gpu/src/native_artifact/owned_string_map.rs')
 assert b'HashMap<Box<str>, u64, S>' in source
 assert b'core::mem::replace(current, value)' in source and b'self.values.insert(key, value)' in source
 assert b'ACGT' not in source and b'histogram(' not in source and b'value.checked_add' not in source
 assert source.index(b'memory.reserve_capacity(table_bytes)') < source.index(b'.try_reserve_exact') < source.index(b'.try_reserve(target')
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.owned-hash-map-storage.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_native_tests=179,passing_storage_tests=9,preexisting_ignored_tests=3,
  isolated_storage_qualified=True,source_hash_contract=False,native_owner_lowering_qualified=False,full_input_work_qualified=False,
  caller_geometry_and_publication_qualified=False,closed_attempts=attempts,compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified nine isolated storage checks within 179 passing native checks, three pre-existing ignored checks, and zero benchmark samples; source selection and owner lowering remain unqualified.')
