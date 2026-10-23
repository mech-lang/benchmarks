"""Pin arena bookkeeping removal without claiming a timed speedup."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = 'c84c8a704f16a6e131984d8c602fa26138bd22b8'
BASE = '382b9769739ff804fffa0ff1dd891ad9c04a1ac0'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(path):
    return subprocess.check_output(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT)

def build():
    paths = list(HERE.rglob('process.json'))
    assert len(paths) == 1 and paths[0].parent.name == 'native-regressions-v1'
    path = paths[0]
    record = json.loads(path.read_bytes())
    assert record['exit_status'] == 0 and record['group_closed'] and record['reaped']
    assert not record['cleanup_errors'] and record['inherited_common_mutex']
    assert not record['quantitative_benchmark']
    native = (path.parent / 'stdout.bin').read_text()
    assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', native)] == [201, 0]
    assert '3 ignored;' in native
    assert 'arena_transport_preserves_shared_account_census_and_external_roots ... ok' in native
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/values.rs',
        'hosts/gpu/src/native_artifact/program_identity.rs',
        'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
        'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs',
    }
    source = blob('hosts/gpu/src/native_artifact/values.rs')
    assert b'live_nodes' not in source and b'retained_node_upper_bound' not in source
    assert b'NativeWordStorage::new(types.len(),' in source
    assert b'let retirement = retained' in source
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.arena-census-elision.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_native_checks=201, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=44, native_program_abi=15,
        removed_word_backing_bytes_per_slot=8, removed_setup_work_units_per_slot=8,
        shared_account_external_root_retention_qualified=True,
        core_snapshot_and_map_library_sources_unchanged=True,
        runtime_program_storage_selection_changed=False,
        complete_caller_geometry_and_retained_map_routing_qualified=False,
        full_input_work_qualified=False,
        closed_attempts={str(path.relative_to(HERE)): sha(path.read_bytes())},
        compiler_files={p: sha(blob(p)) for p in files}, evidence_sha256=evidence,
    )

result = build()
path = HERE / 'seal.json'
if '--check' in sys.argv:
    assert json.loads(path.read_text()) == result
else:
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + '\n')
print('Verified 201 native checks, one closed subject and zero benchmark samples.')
