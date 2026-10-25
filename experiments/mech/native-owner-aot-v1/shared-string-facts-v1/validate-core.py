"""Validate immutable-owner metadata, ownership transfer and concurrency."""
import fcntl
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state

plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
env = read(HERE.parent / 'canonical-native-integration-v1/validation-v2/results.json')['environment']
env['TMPDIR'] = str(HERE / '.build/tmp')
out = STUDY / 'core-validation-v1'
assert not out.exists()
command = ['/Users/cim310/.cargo/bin/cargo', 'test', '--manifest-path',
           '/private/tmp/mech-native-hashmap-performance/Cargo.toml', '--offline', '--locked',
           '-p', 'mech-core', '--no-default-features', '--features', 'mech-core/full',
           '--lib', 'snapshot::validation::', '--', '--test-threads=1', '--nocapture']
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    receipt = process.execute(command, out, env, lock, deadline=3600, quantitative=False)
    after = source_state()
    process.save(out / 'source-provenance.json', dict(before=before, after=after,
                 source_unchanged=before == after, driver_sha256=process.sha(Path(__file__))))
    assert before == after
    print(receipt['exit_status'], flush=True)
    sys.exit(receipt['exit_status'])
