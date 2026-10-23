"""Pin word-transport evidence without claiming runtime owner activation."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='a3ddc2f8c55afb2b3b6d6835368eee89d71fecbb'
BASE='bff3176869d7bc8f6d4151d586f205c3f4fbc6cf'
DATA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path):return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=ROOT)
def counts(path):return [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',path.read_text())]
def build():
 attempts={}
 for path in sorted(HERE.rglob('process.json')):
  record=json.loads(path.read_bytes())
  assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'],path
  assert not record['quantitative_benchmark'],path
  attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':record['exit_status']}
 assert len(attempts)==5
 assert [attempts[f'words-v{i}/process.json']['exit_status'] for i in range(1,4)]==[101,101,0]
 assert attempts['native-regressions-v1/process.json']['exit_status']==0
 assert attempts['map-contracts-v1/process.json']['exit_status']==0
 assert counts(HERE/'words-v3/stdout.bin')==[2,0]
 assert counts(HERE/'native-regressions-v1/stdout.bin')==[190,0]
 assert counts(HERE/'map-contracts-v1/stdout.bin')==[11]
 native=(HERE/'native-regressions-v1/stdout.bin').read_text()
 assert '3 ignored;' in native
 assert 'OWNER_WORD_NATIVE_CASES functions=18 success=54 guard_denials=18 multiword_functions=6' in native
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'src/engine/src/native_artifact/mod.rs','src/engine/src/native_artifact/map_owner_words.rs','src/engine/src/native_artifact/scalar_aggregates.rs','src/stdlib/tests/native_map_entries.rs','hosts/gpu/src/native_artifact/program_scalar_aggregates.rs','hosts/gpu/src/native_artifact/program_map_owner_word_tests.rs','hosts/gpu/tests/fixtures/native/map-owner-word-state.mec'}
 source=blob('src/engine/src/native_artifact/map_owner_words.rs')
 assert b'ACGT' not in source and b'knucleotide' not in source and b'ValueDataDraft' not in source
 assert b'ordinary.slots.to_vec()' in source and b'ordinary.actions.to_vec()' in source and b'ordinary.constants.clone()' in source
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.map-owner-word-transport.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_distinct_checks=201,passing_native_checks=190,
  passing_map_integration_checks=11,preexisting_ignored_native_checks=3,positive_source_decoded_layout_cases=16,
  native_transport_functions=18,native_transport_successes=54,native_wrong_variant_denials=18,native_multiword_functions=6,
  existing_scalar_layout_preserved=True,runtime_storage_selection_changed=False,source_hash_contract=False,
  native_owner_lowering_qualified=False,full_input_work_qualified=False,closed_attempts=attempts,
  compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified 201 distinct checks and 72 generated transport outcomes; default storage selection, full owner execution and timings remain unchanged/unqualified.')
