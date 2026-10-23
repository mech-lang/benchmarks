"""Pin descriptor association evidence; no runtime owner or timing admission."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '2efe102fad8541261044e65431b68dc94e44814a'
BASE = '2d6f032655be091832f73ca05570d5a5f154df6e'
DATA = '849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build():
    expected = {
        'native-regressions-v1': (101, []),
        'native-regressions-v2': (101, []),
        'native-regressions-v3': (0, [199, 0]),
        'map-contracts-v1': (0, [11]),
    }
    paths = sorted(HERE.rglob('process.json'))
    assert {p.parent.name for p in paths} == set(expected)
    attempts = {}
    for path in paths:
        record = json.loads(path.read_bytes())
        status, counts = expected[path.parent.name]
        assert record['exit_status'] == status, path
        assert record['group_closed'] and record['reaped'] and not record['cleanup_errors'], path
        assert record['inherited_common_mutex'] and not record['quantitative_benchmark'], path
        stdout = (path.parent / 'stdout.bin').read_text()
        assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', stdout)] == counts, path
        attempts[str(path.relative_to(HERE))] = sha(path.read_bytes())
    native = (HERE / 'native-regressions-v3/stdout.bin').read_text()
    for test in [
        'map_owner_descriptor_images_preserve_complete_same_build_layout',
        'map_owner_identity_covers_unused_candidates_words_and_site_inventories',
        'shared_descriptor_proofs_preserve_fresh_identity_and_complete_inventory',
    ]:
        assert f'{test} ... ok' in native
    assert '3 ignored;' in native
    assert 'E0061' in (HERE / 'native-regressions-v1/stderr.bin').read_text()
    assert 'E0308' in (HERE / 'native-regressions-v2/stderr.bin').read_text()
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/program_descriptor.rs',
        'hosts/gpu/src/native_artifact/program_descriptor_wire.rs',
        'hosts/gpu/src/native_artifact/program_identity.rs',
        'hosts/gpu/src/native_artifact/program_identity_inventory_tests.rs',
        'hosts/gpu/src/native_artifact/program_line_matrix_tests.rs',
        'hosts/gpu/src/native_artifact/program_prefix_tests.rs',
        'hosts/gpu/src/native_artifact/program_structural_projection_tests.rs',
        'src/engine/src/native_artifact/map_owner_region.rs',
        'src/engine/src/native_artifact/map_owner_words.rs',
        'src/engine/src/native_artifact/program_image_proofs.rs',
    }
    compiler = {p: sha(subprocess.check_output(['git', 'show', f'{COMMIT}:{p}'], cwd=ROOT)) for p in files}
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.retained-map-descriptor.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_distinct_checks=210, passing_native_checks=199,
        passing_map_integration_checks=11, preexisting_ignored_native_checks=3,
        original_and_decoded_descriptor_layouts_qualified=True,
        identity_mutations_per_artifact=15, artifact_forms=2,
        native_program_typed_ir=29, native_program_work_policy=42, native_program_abi=15,
        retained_map_layout_association_qualified=True,
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
print('Verified 210 distinct passing checks, four closed subjects and zero benchmark samples.')
