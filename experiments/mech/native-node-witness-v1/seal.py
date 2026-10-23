"""Pin correctness evidence for admitted node witnesses; no timing admission."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '2d6f032655be091832f73ca05570d5a5f154df6e'
BASE = '14e012525a2c6709603f6ac6dcabfd288d9063b3'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build():
    attempts = {}
    expected = {
        'core-witness-v1': (101, []),
        'core-witness-v2': (0, [1, 0]),
        'core-regressions-v1': (0, [320, 2]),
        'native-regressions-v1': (0, [197, 0]),
        'map-contracts-v1': (0, [11]),
    }
    paths = sorted(HERE.rglob('process.json'))
    assert {p.parent.name for p in paths} == set(expected)
    for path in paths:
        record = json.loads(path.read_bytes())
        exit_status, counts = expected[path.parent.name]
        assert record['exit_status'] == exit_status, path
        assert record['reaped'] and record['group_closed'] and not record['cleanup_errors'], path
        assert record['inherited_common_mutex'] and not record['quantitative_benchmark'], path
        stdout = (path.parent / 'stdout.bin').read_text()
        assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', stdout)] == counts, path
        attempts[str(path.relative_to(HERE))] = sha(path.read_bytes())
    native = (HERE / 'native-regressions-v1/stdout.bin').read_text()
    assert '3 ignored;' in native
    assert 'arena_node_bound_tracks_aliases_replacement_retirement_and_take ... ok' in native
    core = (HERE / 'core-regressions-v1/stdout.bin').read_text()
    assert 'admitted_node_witness_tracks_exact_account_and_schema_owner ... ok' in core
    failure = (HERE / 'core-witness-v1/stderr.bin').read_text()
    assert 'retained_nodes' in failure and 'error' in failure
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'src/core/src/snapshot/validation.rs',
        'src/core/src/snapshot/owned_string.rs',
        'hosts/gpu/src/native_artifact/values.rs',
        'hosts/gpu/src/native_artifact/program_identity.rs',
        'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
        'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs',
    }
    compiler = {p: sha(subprocess.check_output(['git', 'show', f'{COMMIT}:{p}'], cwd=ROOT)) for p in files}
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.native-node-witness.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, passing_distinct_checks=530,
        passing_core_checks=320, passing_catalog_checks=2,
        passing_native_checks=197, passing_map_integration_checks=11,
        preexisting_ignored_native_checks=3, benchmark_samples=0,
        native_program_typed_ir=28, native_program_work_policy=42, native_program_abi=15,
        exact_account_admitted_node_witness_qualified=True,
        conservative_arena_slot_census_qualified=True,
        complete_caller_geometry_qualified=False,
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
print('Verified 530 distinct passing checks, five closed subjects and zero benchmark samples.')
