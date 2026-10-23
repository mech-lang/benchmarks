"""Verify source-entry correctness evidence without admitting benchmark data."""
import gzip, hashlib, json, re, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/mech-native-hashmap-performance')
BASE='e4799a38b466c808dc634137992128cf8e17376c'
COMMIT='fdb489566a7fa0a52cdb3086d9db3bfb12909ea0'
DATA_SHA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
EXPECTED={'source-suite-v3':[20,3,7,3,6,5,13], 'core-types-v1':[26,34], 'map-runtime-v4':[28,0], 'linkage-v1':[1], 'map-schema-regression-v1':[2,0]}
def sha(data): return hashlib.sha256(data).hexdigest()
def blob(path): return subprocess.check_output(['git','show',f'{COMMIT}:{path}'],cwd=ROOT)
def build():
    attempts={}
    for path in sorted(HERE.rglob('process.json')):
        receipt=json.loads(path.read_bytes())
        assert receipt['reaped'] and receipt['group_closed'] and not receipt['cleanup_errors'],path
        assert not receipt['quantitative_benchmark'],path
        attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':receipt['exit_status']}
    for name,expected in EXPECTED.items():
        root=HERE/name
        assert json.loads((root/'process.json').read_bytes())['exit_status']==0
        found=[int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', (root/'stdout.bin').read_text())]
        assert found==expected,(name,found)
    assert 'required: 65925, limit: 65536' in (HERE/'all-widths-diagnostic-v1/stderr.bin').read_text()
    capture=HERE/'catalog-capture-v1/catalog-inventory.json.gz'
    raw=gzip.decompress(capture.read_bytes())
    inventory=json.loads(raw)
    for name in ['catalog-capture-v1','source-suite-v2','source-suite-v3']:
        reference=HERE/name/'catalog-inventory.ref.json'
        entry=json.loads(reference.read_bytes())
        target=reference.parent/entry['gzip_path']
        assert sha(target.read_bytes())==entry['gzip_sha256']
        assert len(raw)==entry['raw_bytes'] and sha(raw)==entry['raw_sha256']
        assert gzip.decompress(target.read_bytes())==raw
    additions={'map/new','map/insert'}
    frozen=json.loads(blob('tests/architecture/function-system/function-surface.json'))
    assert [v for v in inventory['full_source_specializers'] if v['name'] not in additions]==frozen['full_source_specializers']
    assert inventory['prelude_source_specializers']==frozen['prelude_source_specializers']
    assert [v for v in inventory['module_exports'] if v['canonical_name'] not in additions]==frozen['module_exports']
    runtime=json.loads(blob('tests/architecture/function-system/runtime-factory-surface.json'))
    actual={(v['name'],v['id_hex']) for v in inventory['runtime_factories']}
    assert all((v['name'],v['id_hex']) in actual for v in runtime['runtime_factories'])
    assert inventory['runtime_factory_count']==9730
    assert inventory['source_runtime_factory_count']==15711
    files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
    assert all(not path.startswith('tests/architecture/function-system/') for path in files)
    assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA_SHA
    evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
    return dict(schema='mech.general-map-entry-correctness.v1',compiler_commit_at_sealing=COMMIT,
        base_commit=BASE,benchmark_samples=0,canonical_dataset_sha256=DATA_SHA,
        distinct_passing_tests=146,final_suites=EXPECTED,extra_schema_tests_are_repeats=True,
        default_resident_all_widths_qualified=False,standalone_native_qualified=False,
        hash_representation_contract=False,compiler_files={p:sha(blob(p)) for p in files},
        historical_factory_identities_retained=True,catalog_capture_sha256=sha(raw),
        closed_attempts=attempts,evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:
    assert json.loads(path.read_text())==result
else:
    assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified 146 passing distinct tests, {len(result['closed_attempts'])} closed attempts, retained catalog identities, zero benchmark samples.")
