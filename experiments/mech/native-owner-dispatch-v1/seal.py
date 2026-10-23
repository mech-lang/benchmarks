"""Pin actual generated retained-map dispatch and bounded source counting evidence."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '9e2d1a29cdeee612dcae850c32eb326755e14d8a'
BASE = 'e3c32d51bd6c3b6465d4318c09ce43b9d6802edc'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(path):
    return subprocess.check_output(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT)

def build():
    expected = {
        'dispatch-compile-v1': (0, [0, 0]),
        'owner-routing-v1': (0, [5, 0]), 'owner-routing-v2': (0, [5, 0]),
        'native-regressions-v1': (101, []), 'native-regressions-v2': (0, [209, 0]),
        'counting-routing-v1': (0, [1, 0]), 'map-contracts-v1': (0, [11]),
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
    native = (HERE / 'native-regressions-v2/stdout.bin').read_text()
    for test in [
        'actual_generated_visits_bind_tables_validate_calls_and_publish_equal_results',
        'actual_generated_visits_reject_foreign_descriptors_and_preserve_refused_entry',
        'owning_session_lazily_admits_maps_and_retires_tables_without_external_owner',
        'owning_session_failure_retires_an_unpublished_live_table',
        'generated_corrupted_owner_words_fail_and_release_the_invocation',
        'abi16_keeps_the_frozen_scalar_prefix_and_disjoint_helper_lanes',
    ]:
        assert f'{test} ... ok' in native
    assert '3 ignored;' in native
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/' + name for name in [
            'iteration_compiler.rs', 'mod.rs', 'program_abi.rs', 'program_compiler.rs',
            'program_descriptor.rs', 'program_hooks.rs', 'program_identity.rs',
            'program_line_matrix_tests.rs', 'program_linked.rs', 'program_map_owner_runtime.rs',
            'program_map_owner_runtime_tests.rs', 'program_runtime.rs',
            'program_selected_join_layout_tests.rs', 'program_session.rs',
            'program_structural_projection_tests.rs', 'program_map_owner_codegen.rs',
            'program_map_owner_layout.rs',
        ]
    } | {'src/engine/src/native_artifact/map_owner_words.rs'}
    failed = (HERE / 'native-regressions-v1/stdout.bin').read_text()
    assert 'FAILED. 208 passed; 1 failed; 3 ignored;' in failed
    assert 'abi15_keeps_the_frozen_scalar_prefix_and_disjoint_helper_lanes' in failed
    counting = (HERE / 'counting-routing-v1/stdout.bin').read_text()
    assert 'native_structural_map_states_execute_all_seven_counting_widths ... ok' in counting
    driver = blob('hosts/gpu/src/native_artifact/program_structural_projection_tests.rs')
    assert b'evaluate_count_case' in driver and b'1usize, 2, 3, 4, 6, 12, 18' in driver
    observations = blob('hosts/gpu/src/native_artifact/program_map_owner_runtime_tests.rs')
    assert b'assert_eq!(report.canonical_map_calls, 0' in observations
    assert b'(report.entries, report.exits, report.writes), (1, 1, updates)' in observations
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
        schema='mech.native-owner-dispatch.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_distinct_checks=220, passing_native_checks=209,
        passing_map_integration_checks=11, preexisting_ignored_native_checks=3,
        native_program_typed_ir=31, native_program_work_policy=47, native_program_abi=16,
        configured_node_limit_unchanged=65536,
        session_owned_lazy_lifetime_under_generated_visits_qualified=True,
        failed_unpublished_table_teardown_qualified=True,
        original_and_decoded_actual_generated_storage_qualified=True,
        bounded_source_counting_dispatch_cases=42,
        nonempty_seed_and_wider_carrier_qualified=True,
        foreign_descriptor_ledger_stale_and_repeat_rejection_qualified=True,
        refused_entry_preserves_canonical_execution_qualified=True,
        normal_generated_owner_dispatch_selected=True,
        native_opaque_word_transport_selected=True,
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
print('Verified 220 distinct checks, seven closed subjects and 42 bounded source-counting cases. No benchmark samples admitted.')
