"""Pin storage publication evidence without claiming compiler selection."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='5047ac667f7a739fa9499dbf30b0c855a507e642'
BASE='013f1a8a4c2ce143cdbaeb4e0d91c31f6ce815a3'
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
 assert len(attempts)==2
 first=(HERE/'publication-v1/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',first)]==[16,0]
 final=(HERE/'native-regressions-v1/stdout.bin').read_text()
 assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;',final)]==[187,0]
 assert len(re.findall(r'test native_artifact::owned_string_map::publication::tests::.* \.\.\. ok',final))==8
 assert '3 ignored;' in final
 for name in ['owned_map_publication_enters_typed_native_transport_without_reviving_stale_handles','owned_map_publication_checks_complete_geometry_and_exact_temporary_boundary','owned_map_publication_sort_denial_keeps_spent_work_and_releases_workspace']:
  assert name+' ... ok' in final
 files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
 assert set(files)=={'hosts/gpu/src/native_artifact/owned_string_map.rs','hosts/gpu/src/native_artifact/owned_string_map_publication.rs','hosts/gpu/src/native_artifact/owned_string_map_publication_tests.rs'}
 publication=blob('hosts/gpu/src/native_artifact/owned_string_map_publication.rs')
 assert b'ACGT' not in publication and b'histogram' not in publication and b'value.checked_add' not in publication
 assert publication.index(b'reserve_capacity(plan.workspace)') < publication.index(b'order = exact_vec')
 assert b'with_call_limits' in publication and b'with_shared_schemas' in publication
 assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA
 evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
 return dict(schema='mech.owned-map-publication.v1',compiler_commit=COMMIT,base_commit=BASE,
  benchmark_samples=0,canonical_dataset_sha256=DATA,passing_native_tests=187,passing_publication_tests=8,
  preexisting_ignored_tests=3,storage_publication_qualified=True,typed_arena_compatibility_qualified=True,
  runtime_storage_selection_changed=False,source_hash_contract=False,native_owner_lowering_qualified=False,
  complete_caller_geometry_and_site_authority_qualified=False,full_input_work_qualified=False,
  closed_attempts=attempts,compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
 assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print('Verified eight publication checks within 187 passing native checks; three pre-existing ignored checks and zero benchmark samples. Compiled owner selection remains unfinished.')
