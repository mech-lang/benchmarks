"""Pin shared-account snapshot census evidence; no owner execution admission."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '382b9769739ff804fffa0ff1dd891ad9c04a1ac0'
BASE = '7d5139169f950747d5a8ff00399b47969f4c641c'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build():
    expected = {
        'core-regressions-v1': (101, []),
        'core-regressions-v2': (0, [322, 2]),
        'native-regressions-v1': (0, [201, 0]),
        'map-contracts-v1': (0, [11]),
    }
    paths = sorted(HERE.rglob('process.json'))
    assert {p.parent.name for p in paths} == set(expected)
    attempts = {}
    for path in paths:
        record = json.loads(path.read_bytes())
        status, counts = expected[path.parent.name]
        assert record['exit_status'] == status and record['group_closed'] and record['reaped'], path
        assert not record['cleanup_errors'] and record['inherited_common_mutex'], path
        assert not record['quantitative_benchmark'], path
        stdout = (path.parent / 'stdout.bin').read_text()
        assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', stdout)] == counts, path
        attempts[str(path.relative_to(HERE))] = sha(path.read_bytes())
    core = (HERE / 'core-regressions-v2/stdout.bin').read_text()
    for test in [
        'snapshot_node_census_overflow_preserves_account_and_retires_claim',
        'snapshot_node_census_shares_atomic_claims_across_threads',
        'admitted_node_witness_tracks_exact_account_and_schema_owner',
        'exclusive_strings_transfer_without_payload_copy_or_new_budget_charge',
        'refreezing_reused_string_backing_cannot_revive_old_frozen_identity',
        'shared_wrapper_rejection_preserves_owner_identity_admission_and_import_cache',
    ]:
        assert f'{test} ... ok' in core
    failed = (HERE / 'core-regressions-v1/stdout.bin').read_text()
    assert '321 passed; 1 failed;' in failed
    assert 'limit: 0' in (HERE / 'core-regressions-v1/stderr.bin').read_text()
    assert '3 ignored;' in (HERE / 'native-regressions-v1/stdout.bin').read_text()
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/program_identity.rs',
        'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
        'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs',
        'src/core/src/memory_runtime/budget.rs',
        'src/core/src/memory_runtime/mod.rs',
        'src/core/src/snapshot/owned_string.rs',
        'src/core/src/snapshot/owned_string_tests.rs',
        'src/core/src/snapshot/validation.rs',
    }
    compiler = {p: sha(subprocess.check_output(['git', 'show', f'{COMMIT}:{p}'], cwd=ROOT)) for p in files}
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.account-node-witness.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_distinct_checks=536, passing_core_checks=322,
        passing_catalog_checks=2, passing_native_checks=201,
        passing_map_integration_checks=11, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=43, native_program_abi=15,
        shared_account_admitted_snapshot_census_qualified=True,
        complete_private_builder_and_native_metadata_geometry_qualified=False,
        runtime_program_storage_selection_changed=False,
        whole_program_native_owner_lowering_qualified=False,
        full_input_work_qualified=False,
        closed_attempts=attempts, compiler_files=compiler, evidence_sha256=evidence,
    )

result = build()
path = HERE / 'seal.json'
if '--check' in sys.argv:
    assert json.loads(path.read_text()) == result
else:
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + '\n')
print('Verified 536 distinct passing checks, four closed subjects and zero benchmark samples.')
