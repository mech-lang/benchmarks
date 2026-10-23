"""Verify direct-membership evidence, retaining the full-input/native gaps."""
import gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/mech-native-hashmap-performance')
BASE='fdb489566a7fa0a52cdb3086d9db3bfb12909ea0'
COMMIT='684e7471151b122c5c8c5bd15a0b0231e28b3be3'
DATA_SHA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
SUITES={'source-suite-v2':[20,3,7,3,6,3,5,13], 'map-runtime-v1':[30,0], 'core-types-v1':[26,34], 'linkage-v1':[1]}
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path,commit=COMMIT):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def build():
    attempts={}
    for path in sorted(HERE.rglob('process.json')):
        entry=json.loads(path.read_bytes())
        assert entry['reaped'] and entry['group_closed'] and not entry['cleanup_errors'],path
        assert not entry['quantitative_benchmark'],path
        attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':entry['exit_status']}
    for name,expected in SUITES.items():
        root=HERE/name
        assert json.loads((root/'process.json').read_bytes())['exit_status']==0
        found=[int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', (root/'stdout.bin').read_text())]
        assert found==expected,(name,found)
    assert sum(map(sum,SUITES.values()))==151
    for name,count in [('source-v3',2),('decoded-source-v2',3)]:
        root=HERE/name
        assert json.loads((root/'process.json').read_bytes())['exit_status']==0
        assert f'test result: ok. {count} passed;' in (root/'stdout.bin').read_text()
    assert blob('src/core/src/memory_plan/target.rs')==blob('src/core/src/memory_plan/target.rs',BASE)
    assert blob('src/engine/src/resident/numeric/string_map_access.rs')==blob('src/engine/src/resident/numeric/string_map_access.rs',BASE)
    source=blob('src/stdlib/tests/source_map_lookup_contract.rs').decode()
    assert 'previous := (key ∈ h)?' in source and 'h_keys' not in source
    assert 'for width in [1, 2, 3, 4, 6, 12, 18]' in source
    assert 'ACGTACGTNACGTTACGTACGTACGT' in source
    assert 'evaluate_with_source_catalog_decoded as evaluate' in source
    raw=gzip.decompress((HERE/'catalog-capture-v1/catalog-inventory.json.gz').read_bytes())
    for name in ['catalog-capture-v1','source-suite-v1','source-suite-v2']:
        path=HERE/name/'catalog-inventory.ref.json';ref=json.loads(path.read_bytes());target=path.parent/ref['gzip_path']
        assert sha(target.read_bytes())==ref['gzip_sha256']
        assert sha(raw)==ref['raw_sha256'] and len(raw)==ref['raw_bytes']
        assert gzip.decompress(target.read_bytes())==raw
    inventory=json.loads(raw);new={'map/new','map/insert','map/contains-key'}
    frozen=json.loads(blob('tests/architecture/function-system/function-surface.json'))
    assert [v for v in inventory['full_source_specializers'] if v['name'] not in new]==frozen['full_source_specializers']
    assert inventory['prelude_source_specializers']==frozen['prelude_source_specializers']
    assert [v for v in inventory['module_exports'] if v['canonical_name'] not in new]==frozen['module_exports']
    old=json.loads(blob('tests/architecture/function-system/runtime-factory-surface.json'))['runtime_factories']
    actual={(v['name'],v['id_hex']) for v in inventory['runtime_factories']}
    assert all((v['name'],v['id_hex']) in actual for v in old)
    assert inventory['runtime_factory_count']==9731 and inventory['source_runtime_factory_count']==15712
    files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
    assert not any(p.startswith(('src/syntax/','tests/architecture/function-system/')) for p in files)
    assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA_SHA
    evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
    return dict(schema='mech.general-map-membership.v1',compiler_commit_at_sealing=COMMIT,base_commit=BASE,
        benchmark_samples=0,canonical_dataset_sha256=DATA_SHA,distinct_passing_tests=151,final_suites=SUITES,
        original_and_decoded_diagnostic_all_widths_qualified=True,default_resident_policy_unchanged=True,
        full_input_work_qualified=False,standalone_native_qualified=False,hash_representation_contract=False,
        compiler_files={p:sha(blob(p)) for p in files},historical_catalog_identities_retained=True,
        catalog_capture_sha256=sha(raw),closed_attempts=attempts,evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
    assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified 151 passing distinct tests, {len(result['closed_attempts'])} closed attempts, seven-width diagnostic success, unchanged policy, zero benchmark samples.")
