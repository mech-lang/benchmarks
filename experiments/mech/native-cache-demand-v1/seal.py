"""Pin read-only native cache demand evidence; no owner execution admission."""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('MECH_CHECKOUT', '/private/tmp/mech-native-hashmap-performance'))
COMMIT = '79a344544c3f023246c7dcee7380f2748029bd9d'
BASE = 'c84c8a704f16a6e131984d8c602fa26138bd22b8'
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
    assert [int(n) for n in re.findall(r'test result: ok\. (\d+) passed;', native)] == [202, 0]
    assert '3 ignored;' in native
    assert 'repeated_cache_demand_is_read_only_account_bound_and_keeps_nested_fuel ... ok' in native
    files = subprocess.check_output(['git', 'diff', '--name-only', BASE, COMMIT], cwd=ROOT, text=True).splitlines()
    assert set(files) == {
        'hosts/gpu/src/native_artifact/program_call_cache_tests.rs',
        'src/engine/src/resident/general/native_collection_prepared.rs',
        'src/engine/src/resident/native_turn_plan_cache.rs',
    }
    assert sha((HERE.parents[2] / 'data/benchmarks.json').read_bytes()) == DATA
    evidence = {
        str(p.relative_to(HERE)): sha(p.read_bytes())
        for p in sorted(HERE.rglob('*'))
        if p.is_file() and '.build' not in p.parts and '__pycache__' not in p.parts and p.name != 'seal.json'
    }
    return dict(
        schema='mech.native-cache-demand.v1', compiler_commit=COMMIT, base_commit=BASE,
        canonical_dataset_sha256=DATA, benchmark_samples=0,
        passing_native_checks=202, preexisting_ignored_native_checks=3,
        native_program_typed_ir=30, native_program_work_policy=44, native_program_abi=15,
        bound_cache_retained_demand_qualified=True,
        original_and_decoded_work_account_and_nested_fuel_checks_qualified=True,
        complete_private_builder_and_native_frame_geometry_qualified=False,
        runtime_program_storage_selection_changed=False,
        whole_program_native_owner_lowering_qualified=False,
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
print('Verified 202 native checks, one closed subject and zero benchmark samples.')
