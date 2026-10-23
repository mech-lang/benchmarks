"""Pin supported live-caller geometry; retain explicit unqualified owner scopes."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '942976a898c2942e5e68b4cc95e6d7225db5aa74'
BASE = '79a344544c3f023246c7dcee7380f2748029bd9d'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(path):
    return subprocess.check_output(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT)

def build():
    expected = {
        'native-regressions-v1': (101, []),
        'geometry-v2': (101, []),
        'geometry-v3': (0, [2, 0]),
        'native-regressions-v2': (0, [204, 0]),
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
        'generated_caller_geometry_includes_prior_roots_without_payload_dependent_work',
        'generated_caller_geometry_covers_live_collection_builder_families',
    ]:
        assert f'{test} ... ok' in native
    assert '3 ignored;' in native
    assert '202 passed; 2 failed;' in (HERE / 'native-regressions-v1/stdout.bin').read_text()
    assert 'unknown-function' in (HERE / 'native-regressions-v1/stderr.bin').read_text()
    assert 'missing builder 8' in (HERE / 'geometry-v2/stderr.bin').read_text()
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/program_caller_geometry.rs',
        'hosts/gpu/src/native_artifact/program_caller_geometry_tests.rs',
        'hosts/gpu/src/native_artifact/program_collection.rs',
        'hosts/gpu/src/native_artifact/program_histogram.rs',
        'hosts/gpu/src/native_artifact/program_histogram_query.rs',
        'hosts/gpu/src/native_artifact/program_runtime.rs',
        'hosts/gpu/src/native_artifact/program_selected_join.rs',
        'hosts/gpu/src/native_artifact/program_session.rs',
        'hosts/gpu/src/native_artifact/program_text_join.rs',
    }
    source = blob('hosts/gpu/src/native_artifact/program_caller_geometry.rs')
    assert b'memory.retained_snapshot_nodes()' in source and b'memory.used_bytes()' in source
    assert b'return Ok(None)' in source and b'self.line_window.is_some()' in source
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.native-caller-geometry.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_native_checks=204, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=44, native_program_abi=15,
        supported_canonical_caller_view_qualified=True,
        prior_output_cell_counts=[1, 4096], artifact_forms=2,
        payload_size_independent_preview_debit_qualified=True,
        observed_collection_builder_families=['draft_matrix', 'text_join', 'histogram', 'guarded_query'],
        active_source_and_compiled_window_loan_geometry_qualified=False,
        retained_map_owner_lane_and_final_geometry_qualified=False,
        runtime_program_storage_selection_changed=False,
        whole_program_native_owner_lowering_qualified=False,
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
print('Verified 204 native checks, four closed subjects and zero benchmark samples.')
