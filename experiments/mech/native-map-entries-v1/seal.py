"""Verify native entry-call evidence without claiming full counting execution."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/mech-native-hashmap-performance')
COMMIT='72cb3bfcd1e6e9c29c57bc4afaabff6a49392c11'
BASE='684e7471151b122c5c8c5bd15a0b0231e28b3be3'
DATA_SHA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
def sha(data): return hashlib.sha256(data).hexdigest()
def build():
    attempts={}
    for path in sorted(HERE.rglob('process.json')):
        record=json.loads(path.read_bytes())
        assert record['group_closed'] and record['reaped'] and not record['cleanup_errors'],path
        assert not record['quantitative_benchmark'],path
        attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':record['exit_status']}
    suites={'templates-v8':[4], 'native-regressions-v1':[31,6,3,5]}
    for name,expected in suites.items():
        assert json.loads((HERE/name/'process.json').read_bytes())['exit_status']==0
        actual=[int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', (HERE/name/'stdout.bin').read_text())]
        assert actual==expected,(name,actual)
    files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
    blobs={p:subprocess.check_output(['git','show',f'{COMMIT}:{p}'],cwd=ROOT) for p in files}
    source=blobs['src/stdlib/tests/native_map_entries.rs'].decode()
    assert 'non-U64 structural native binding' in source
    assert 'for width in [1, 2, 3, 4, 6, 12, 18]' in source
    assert 'NativeScalarOp::U64Add' in source
    assert 'shares_frozen_storage(&prior)' in source
    assert not any(b'MAP_NATIVE_SCHEMA_DIAGNOSTIC' in blob for blob in blobs.values())
    assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA_SHA
    evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
    return dict(schema='mech.native-map-entries.v1',compiler_commit=COMMIT,base_commit=BASE,
        benchmark_samples=0,canonical_dataset_sha256=DATA_SHA,distinct_passing_tests=49,preexisting_ignored_tests=1,
        native_map_leaf_calls_qualified=True,native_scalar_arithmetic_preserved=True,
        whole_counting_state_machine_native_qualified=False,remaining_rejection='non-U64 structural native binding',
        hash_representation_contract=False,full_input_work_qualified=False,
        final_suites=suites,closed_attempts=attempts,compiler_files={p:sha(b) for p,b in blobs.items()},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv: assert json.loads(path.read_text())==result
else:
    assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified 49 passing checks, one pre-existing ignored check, {len(result['closed_attempts'])} closed attempts, zero benchmark samples; whole counting AOT remains unqualified.")
