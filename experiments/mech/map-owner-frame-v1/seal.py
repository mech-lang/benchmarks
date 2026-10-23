"""Pin occupied-frame composition evidence without admitting owner execution."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '7d5139169f950747d5a8ff00399b47969f4c641c'
BASE = '2efe102fad8541261044e65431b68dc94e44814a'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build():
    paths = sorted(HERE.rglob('process.json'))
    expected = {'native-regressions-v1': [201, 0], 'map-contracts-v1': [11]}
    assert {p.parent.name for p in paths} == set(expected)
    attempts = {}
    for path in paths:
        record = json.loads(path.read_bytes())
        assert record['exit_status'] == 0 and record['group_closed'] and record['reaped'], path
        assert not record['cleanup_errors'] and record['inherited_common_mutex'], path
        assert not record['quantitative_benchmark'], path
        stdout = (path.parent / 'stdout.bin').read_text()
        assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', stdout)] == expected[path.parent.name], path
        attempts[str(path.relative_to(HERE))] = sha(path.read_bytes())
    native = (HERE / 'native-regressions-v1/stdout.bin').read_text()
    for test in [
        'owner_word_relocation_preserves_occupied_prefix_and_emitted_transport',
        'retained_map_descriptor_appends_state_after_existing_closed_loop_metadata',
        'map_owner_descriptor_images_preserve_complete_same_build_layout',
        'map_owner_identity_covers_unused_candidates_words_and_site_inventories',
    ]:
        assert f'{test} ... ok' in native
    assert '3 ignored;' in native
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'src/engine/src/native_artifact/map_owner_words.rs',
        'hosts/gpu/src/native_artifact/program_descriptor.rs',
        'hosts/gpu/src/native_artifact/program_identity.rs',
        'hosts/gpu/src/native_artifact/program_identity_inventory_tests.rs',
        'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
        'hosts/gpu/src/native_artifact/program_map_owner_word_tests.rs',
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
        schema='mech.retained-map-frame.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_distinct_checks=212, passing_native_checks=201,
        passing_map_integration_checks=11, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=42, native_program_abi=15,
        protected_sentinel_gap_words=37, artifact_forms=2,
        identity_mutations_per_artifact=16,
        nonoverlapping_candidate_frame_composition_qualified=True,
        mixed_scalar_and_map_canonical_execution_qualified=True,
        runtime_program_storage_selection_changed=False,
        complete_caller_geometry_and_current_visit_routing_qualified=False,
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
print('Verified 212 distinct passing checks, two closed subjects and zero benchmark samples.')
