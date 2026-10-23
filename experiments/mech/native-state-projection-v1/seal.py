"""Verify native state bindings without asserting hashing or full-input timing."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('MECH_CHECKOUT','/private/tmp/mech-native-hashmap-performance'))
COMMIT='f6fb76f5f284b8731368a5d30028cc1663c2bb03'
BASE='72cb3bfcd1e6e9c29c57bc4afaabff6a49392c11'
DATA_SHA='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
SUITES={'engine-guards-v1':[198,1], 'native-regressions-v3':[169,0], 'map-contracts-v3':[31,5,6,3,5]}
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(path,commit=COMMIT):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def build():
    attempts={}
    for path in sorted(HERE.rglob('process.json')):
        record=json.loads(path.read_bytes())
        assert record['group_closed'] and record['reaped'] and not record['cleanup_errors'],path
        assert not record['quantitative_benchmark'],path
        attempts[str(path.relative_to(HERE))]={'sha256':sha(path.read_bytes()),'exit_status':record['exit_status']}
    for name,expected in SUITES.items():
        assert json.loads((HERE/name/'process.json').read_bytes())['exit_status']==0
        actual=[int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', (HERE/name/'stdout.bin').read_text())]
        assert actual==expected,(name,actual)
    assert sum(map(sum,SUITES.values()))==418
    engine=(HERE/'engine-guards-v1/stdout.bin').read_text()
    assert 'denied_native_projection_preflight_keeps_spent_comparisons_on_retry ... ok' in engine
    assert 'tail_proof_keeps_nominal_enum_identity_and_validates_tag_and_projection_paths ... ok' in engine
    host=(HERE/'native-regressions-v3/stdout.bin').read_text()
    assert 'native_structural_map_states_execute_all_seven_counting_widths ... ok' in host
    source=blob('hosts/gpu/src/native_artifact/program_structural_projection_tests.rs').decode()
    assert 'let widths = [1usize, 2, 3, 4, 6, 12, 18]' in source
    assert 'for artifact in [original, decoded]' in source
    assert 'for text in ["ACGTACGTNACGTTACGTACGTACGT", "", "GGTAGGT"]' in source
    assert '"width" => ValueDataDraft::U64(width as u64)' in source
    assert 'assert_eq!(counts, expected' in source
    assert 'decode_build_owned_image' in source and 'emit_program_object' in source
    assert 'limits.library.max_comparison_work = Some(10_000_000)' in source
    helper=blob('src/engine/src/resident/general/native_structural_projection.rs').decode()
    assert 'ACGT' not in helper and '#Count' not in helper
    assert helper.index('reserve_capacity(workspace)') < helper.index('canonical_snapshot_data_draft_with_context')
    assert 'clone_allocation_bound_bytes_with_precharge' in helper
    assert 'structural_values::supported(body)' in helper
    policy=blob('hosts/gpu/src/native_artifact/program_identity.rs').decode()
    assert 'NATIVE_PROGRAM_TYPED_IR_VERSION: u64 = 28' in policy
    assert 'NATIVE_PROGRAM_WORK_POLICY_VERSION: u64 = 41' in policy
    assert 'VERSION: u64 = 15' in blob('hosts/gpu/src/native_artifact/program_abi.rs').decode()
    assert blob('src/core/src/memory_plan/target.rs')==blob('src/core/src/memory_plan/target.rs',BASE)
    files=subprocess.check_output(['git','diff','--name-only',BASE,COMMIT],cwd=ROOT,text=True).splitlines()
    assert not any(path.startswith(('src/syntax/','tests/architecture/function-system/')) for path in files)
    assert sha((HERE.parents[2]/'data/benchmarks.json').read_bytes())==DATA_SHA
    evidence={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in sorted(HERE.rglob('*')) if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name!='seal.json'}
    return dict(schema='mech.native-state-projection.v1',compiler_commit=COMMIT,base_commit=BASE,
        benchmark_samples=0,canonical_dataset_sha256=DATA_SHA,distinct_passing_tests=418,preexisting_ignored_tests=4,
        original_and_decoded_machine_code_cases=42,native_ir_version=28,native_work_policy=41,native_abi=15,
        compiled_counting_procedure_qualified=True,descriptor_images_and_object_identities_qualified=True,
        standalone_executable_qualified=False,full_input_work_qualified=False,hash_representation_contract=False,
        default_resident_policy_unchanged=True,final_suites=SUITES,closed_attempts=attempts,
        compiler_files={p:sha(blob(p)) for p in files},evidence_sha256=evidence)
result=build();path=HERE/'seal.json'
if '--check' in sys.argv:assert json.loads(path.read_text())==result
else:
    assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n')
print(f"Verified 418 passing checks, four pre-existing ignored checks, 42 native counting cases, {len(result['closed_attempts'])} closed attempts, zero benchmark samples; standalone/full-input/hash work remains unqualified.")
