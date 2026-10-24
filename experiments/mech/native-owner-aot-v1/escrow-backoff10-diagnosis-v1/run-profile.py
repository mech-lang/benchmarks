"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '0b4ce3e7c316ae4248399c3ce1b2ed14b8eb65e2'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-escrow-backoff10-build-v1', '--source', 'counting-escrow-backoff10', '--output', 'counting-escrow-backoff10-profile', '--package', 'owner-counting-escrow-backoff10', '--compiler', 'compiler-v65'])
for index in range(1, 4):
    samples = f'full-profile-escrow-backoff10-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-escrow-backoff10-build-v1', '--launch', 'full-escrow-backoff10-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'escrow-backoff10-timing-v1', '--profile-build', 'profile-escrow-backoff10-build-v1', '--samples', samples, '--binary', 'counting-escrow-backoff10'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'escrow-backoff10-codegen-audit-v{index}', '--timing', 'escrow-backoff10-timing-v1', '--profile-build', 'profile-escrow-backoff10-build-v1', '--samples', samples, '--binary', 'counting-escrow-backoff10'])
run('static-paths', ['audit_split_paths.py', '--audit', 'escrow-backoff10-codegen-audit-v1'])
run('hardware', ['hardware_counters.py', '--receipt', 'escrow-backoff10-hardware-v1', '--timing', 'escrow-backoff10-timing-v1', '--compiler', 'compiler-v65'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-escrow-backoff10-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'escrow-backoff10-remaining-profile-v1'])
report = json.loads((HERE / 'escrow-backoff10-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'escrow-backoff10-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)

