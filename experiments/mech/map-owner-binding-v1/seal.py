"""Pin private table binding evidence without claiming program activation."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='14e012525a2c6709603f6ac6dcabfd288d9063b3'
BASE='a3ddc2f8c55afb2b3b6d6835368eee89d71fecbb'
DATA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path):return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=ROOT)
def counts(path):return [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',path.read_text())]
def build():
 attempts={}
 for path in sorted(HERE.rglob('process.json')):
  record=json.loads(path.read_bytes())
  assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'],path
  assert not record['quantitative_benchmark'] and record['exit_status']==0,path
  attempts[str(path.relative_to(HERE))]=sha(path.read_bytes())
 assert len(attempts)==4
 assert counts(HERE/'binding-v1/stdout.bin')==[5,0]
 assert counts(HERE/'native-regressions-v1/stdout.bin')==[196,0]
 assert counts(HERE/'binding-v2/stdout.bin')==[6,0]
 assert counts(HERE/'map-contracts-v1/stdout.bin')==[11]
 native=(HERE/'native-regressions-v1/stdout.bin').read_text()
 assert '3 ignored;' in native
 assert len(re.findall(r'test native_artifact::owned_map_binding::tests::.* \.\.\. ok',native))==6
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'src/engine/src/native_artifact/map_owner_region.rs','hosts/gpu/src/native_artifact/mod.rs','hosts/gpu/src/native_artifact/owned_string_map.rs','hosts/gpu/src/native_artifact/owned_map_binding.rs','hosts/gpu/src/native_artifact/owned_map_binding_tests.rs','hosts/gpu/tests/fixtures/native/map-owner-binding-state.mec'}
 source=blob('hosts/gpu/src/native_artifact/owned_map_binding.rs')
 assert b'ACGT' not in source and b'knucleotide' not in source and b'previous + n' not in source
 assert b'map.insert(key, value)' in source and b'stale or foreign map reference' in source
 assert b'foreign program revision' in source and b'compare_exchange_weak' in source
 assert source.index(b'let next = token_from(&TOKENS, &work)?') < source.index(b'map.insert(key, value)?')
 test=blob('hosts/gpu/src/native_artifact/owned_map_binding_tests.rs')
 assert b'nested publication must not renew the enclosing call allowance' in test
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.retained-map-binding.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_distinct_checks=207,passing_native_checks=196,
  passing_map_integration_checks=11,passing_binding_checks=6,preexisting_ignored_native_checks=3,
  private_table_binding_qualified=True,versioned_reference_consistency_qualified=True,
  runtime_program_storage_selection_changed=False,source_hash_contract=False,
  complete_current_visit_frame_and_caller_authority_qualified=False,
  whole_program_native_owner_lowering_qualified=False,full_input_work_qualified=False,
  closed_attempts=attempts,compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified 207 distinct checks, six private binding checks, four closed subjects and zero benchmark samples. Whole-program binding/authority remains unfinished.')
