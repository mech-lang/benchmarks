"""Pin session-owned map lifetime checks; normal word transport remains unselected."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = 'e3c32d51bd6c3b6465d4318c09ce43b9d6802edc'
BASE = '426d1cadffe5b75c31a74555086b01f5779a63a3'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(path):
    return subprocess.check_output(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT)

def build():
    expected = {
        'owner-session-v1': (0, [3, 0]),
        'native-regressions-v1': (0, [208, 0]),
        'map-contracts-v1': (101, []), 'map-contracts-v2': (0, [11]),
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
    native = (HERE / 'native-regressions-v1/stdout.bin').read_text()
    for test in [
        'actual_generated_visits_bind_tables_validate_calls_and_publish_equal_results',
        'actual_generated_visits_reject_foreign_descriptors_and_preserve_refused_entry',
        'owning_session_lazily_admits_maps_and_retires_tables_without_external_owner',
        'owning_session_failure_retires_an_unpublished_live_table',
    ]:
        assert f'{test} ... ok' in native
    assert '3 ignored;' in native
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/' + name for name in [
            'program_identity.rs', 'program_line_matrix_tests.rs',
            'program_map_owner_runtime.rs', 'program_map_owner_runtime_tests.rs',
            'program_runtime.rs', 'program_session.rs', 'program_structural_projection_tests.rs',
        ]
    }
    owner = blob('hosts/gpu/src/native_artifact/program_map_owner_runtime.rs')
    assert b'core::ptr::eq' in owner and b'last_owned_visit' in owner
    assert b'knucleotide' not in owner and b'ACGT' not in owner
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.native-owner-session.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_distinct_checks=219, passing_native_checks=208,
        passing_map_integration_checks=11, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=46, native_program_abi=15,
        configured_node_limit_unchanged=65536,
        session_owned_lazy_lifetime_under_generated_visits_qualified=True,
        failed_unpublished_table_teardown_qualified=True,
        original_and_decoded_shadow_storage_agreement_qualified=True,
        foreign_descriptor_ledger_stale_and_repeat_rejection_qualified=True,
        refused_entry_preserves_canonical_execution_qualified=True,
        normal_generated_owner_dispatch_selected=False,
        native_opaque_word_transport_selected=False,
        full_input_work_qualified=False,
        closed_attempts=attempts, compiler_files={p: sha(blob(p)) for p in files}, evidence_sha256=evidence,
    )

result = build()
path = HERE / 'seal.json'
if '--check' in sys.argv:
    assert json.loads(path.read_text()) == result
else:
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + '\n')
print('Verified 219 distinct checks, four closed subjects and zero benchmark samples. Normal owner transport remains unselected.')
