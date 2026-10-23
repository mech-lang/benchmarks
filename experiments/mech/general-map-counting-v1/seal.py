"""Pin focused correctness evidence. No benchmark admission or timing samples."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
COMPILER = Path('/private/tmp/mech-native-hashmap-performance')
COMMIT = 'e4799a38b466c808dc634137992128cf8e17376c'
BASE = 'be81aff98acbaaffb2a41dc2b1dea7c94d6efd2f'
CATALOG_SHA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
EXPECTED = {'source-v12': 5, 'solver-v2': 34, 'catalog-v1': 26, 'map-runtime-v1': 25, 'linkage-v1': 1}
def sha(data): return hashlib.sha256(data).hexdigest()
def build():
    receipts = {}
    for root in [HERE, HERE.parent/'map-hash-histogram-v1']:
        for path in sorted(root.rglob('process.json')):
            receipt = json.loads(path.read_bytes())
            assert receipt['reaped'] and receipt['group_closed'] and not receipt['cleanup_errors'], path
            assert not receipt['quantitative_benchmark'], path
            receipts[str(path.relative_to(HERE.parent))] = dict(sha256=sha(path.read_bytes()), exit_status=receipt['exit_status'])
    for name, count in EXPECTED.items():
        path = HERE/name
        assert json.loads((path/'process.json').read_bytes())['exit_status'] == 0
        assert f'test result: ok. {count} passed; 0 failed;' in (path/'stdout.bin').read_text()
    catalog = HERE.parents[2]/'data/benchmarks.json'
    assert sha(catalog.read_bytes()) == CATALOG_SHA
    files = subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=COMPILER,text=True).splitlines()
    source = {p: sha(subprocess.check_output(['git','show',f'{COMMIT}:{p}'],cwd=COMPILER)) for p in files}
    evidence = {str(p.relative_to(HERE)): sha(p.read_bytes()) for p in sorted(HERE.rglob('*'))
                if p.is_file() and '.build' not in p.parts and p.name != 'seal.json' and '__pycache__' not in p.parts}
    return dict(schema='mech.general-map-correctness.v1', compiler_commit_at_sealing=COMMIT,
                base_commit=BASE, benchmark_samples=0, canonical_dataset_sha256=CATALOG_SHA,
                focused_tests=EXPECTED, focused_test_count=sum(EXPECTED.values()),
                standalone_native_qualification=False, source_counting_machine_qualified=False,
                hash_representation_contract=False, compiler_files=source,
                closed_attempts=receipts, evidence_sha256=evidence)
result=build()
path=HERE/'seal.json'
if '--check' in sys.argv:
    assert json.loads(path.read_text()) == result
else:
    assert not path.exists()
    path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified {result['focused_test_count']} passing focused tests, {len(result['closed_attempts'])} closed attempts, zero benchmark samples.")
