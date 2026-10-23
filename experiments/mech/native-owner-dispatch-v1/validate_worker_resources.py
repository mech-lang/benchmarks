"""Serial bounded checks for shared worker fuel, memory, and lazy cache ownership."""
import fcntl
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

ROOT = Path('/private/tmp/mech-native-hashmap-performance')
out = HERE / sys.argv[1]
out.mkdir(exist_ok=False)
env = json.loads((HERE.parent / 'canonical-native-integration-v1/validation-v2/results.json').read_text())['environment']
env['TMPDIR'] = str(HERE / '.build/tmp')
filters = [
    ('core-memory', 'memory_runtime::budget::tests', 12),
    ('worker-fuel', 'resident::budget::workers::tests', 11),
    ('worker-debit-batches', 'resident::budget::workers::debit_batch::tests', 7),
    ('text-cache', 'resident::text_index::snapshot::tests', 8),
    ('binding-cache', 'resident::general::native_collection_calls::invocation::data_footprint_tests::boundary_tests', 4),
    ('plan-cache', 'resident::budget::native_turn_plan_cache::tests', 1),
]
summary = []
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for name, test_filter, expected_tests in filters:
        command = ['/Users/cim310/.cargo/bin/cargo', 'test', '--manifest-path', str(ROOT / 'Cargo.toml'),
                   '--offline', '--locked', '-p', 'mech-core', '-p', 'mech-engine', '--no-default-features',
                   '--features', 'mech-engine/full_compiler,mech-engine/native-artifact',
                   '--lib', test_filter, '--', '--test-threads=1', '--nocapture']
        result = process.execute(command, out / name, env, lock, deadline=3600)
        row = dict(name=name, **{key: result[key] for key in ['exit_status', 'elapsed_seconds', 'group_closed', 'reaped', 'cleanup_errors']})
        counts = re.findall(r'test result: ok\. (\d+) passed;', (out / name / 'stdout.bin').read_text())
        row['tests_passed'] = sum(map(int, counts))
        row['expected_tests'] = expected_tests
        summary.append(row)
        process.save(out / 'summary.json', summary)
        print(json.dumps(row), flush=True)
        if result['exit_status']:
            sys.exit(result['exit_status'])
        assert row['tests_passed'] == expected_tests, 'test filter did not execute the intended checks'
