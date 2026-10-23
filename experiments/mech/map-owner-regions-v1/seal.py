"""Pin owner-candidate analysis and predicate-schema regression evidence."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='bff3176869d7bc8f6d4151d586f205c3f4fbc6cf'
BASE='5047ac667f7a739fa9499dbf30b0c855a507e642'
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
 assert len(attempts)==9
 assert [attempts[f'regions-v{i}/process.json']['exit_status'] for i in range(1,7)]==[101,101,101,101,101,0]
 assert all(attempts[p]['exit_status']==0 for p in ['source-semantics-v1/process.json','source-semantics-v2/process.json','native-regressions-v1/process.json'])
 assert counts(HERE/'regions-v6/stdout.bin')==[11]
 assert counts(HERE/'source-semantics-v1/stdout.bin')==[0]
 assert counts(HERE/'source-semantics-v2/stdout.bin')==[147]
 assert counts(HERE/'native-regressions-v1/stdout.bin')==[188,0]
 native=(HERE/'native-regressions-v1/stdout.bin').read_text()
 assert 'native_unconditional_map_states_execute_without_source_boolean_expressions ... ok' in native
 assert '3 ignored;' in native
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'src/engine/src/native_artifact/mod.rs','src/engine/src/native_artifact/map_owner_region.rs','src/engine/src/source_semantics/frontend.rs','src/stdlib/tests/native_map_entries.rs','hosts/gpu/src/native_artifact/program_structural_projection_tests.rs','hosts/gpu/tests/fixtures/native/map-state-two-updates.mec'}
 source=blob('src/engine/src/native_artifact/map_owner_region.rs')
 assert b'ACGT' not in source and b'knucleotide' not in source
 fixture=blob('hosts/gpu/tests/fixtures/native/map-state-two-updates.mec')
 assert b'true' not in fixture and b'false' not in fixture and b'bool' not in fixture
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.map-owner-candidates.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_distinct_checks=346,
  passing_map_integration_checks=11,passing_source_semantics_checks=147,passing_native_checks=188,
  preexisting_ignored_native_checks=3,owner_analysis_source_and_decoded_cases=22,
  unconditional_state_native_source_and_decoded_cases=2,source_predicate_schema_closure_qualified=True,
  old_manually_constructed_schema_artifacts_retrofitted=False,
  runtime_storage_selection_changed=False,source_hash_contract=False,native_owner_lowering_qualified=False,
  full_input_work_qualified=False,closed_attempts=attempts,
  compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified 346 distinct checks, closed candidate analysis and source/decoded unconditional native state execution. Retained storage selection and timings remain unfinished.')
