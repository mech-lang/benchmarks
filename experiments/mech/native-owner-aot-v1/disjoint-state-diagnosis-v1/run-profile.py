"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == 'a94d34d60ab7bc503603217d0baa49397143eb09'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-disjoint-state-build-v1', '--source', 'counting-disjoint-state', '--output', 'counting-disjoint-state-profile', '--package', 'owner-counting-disjoint-state', '--compiler', 'compiler-v68'])
for index in range(1, 4):
    samples = f'full-profile-disjoint-state-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-disjoint-state-build-v1', '--launch', 'full-disjoint-state-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'disjoint-state-timing-v1', '--profile-build', 'profile-disjoint-state-build-v1', '--samples', samples, '--binary', 'counting-disjoint-state'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'disjoint-state-codegen-audit-v{index}', '--timing', 'disjoint-state-timing-v1', '--profile-build', 'profile-disjoint-state-build-v1', '--samples', samples, '--binary', 'counting-disjoint-state'])
run('static-paths', ['audit_split_paths.py', '--audit', 'disjoint-state-codegen-audit-v1'])
run('hardware', ['hardware_counters.py', '--receipt', 'disjoint-state-hardware-v1', '--timing', 'disjoint-state-timing-v1', '--compiler', 'compiler-v68'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-disjoint-state-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'disjoint-state-remaining-profile-v1'])
report = json.loads((HERE / 'disjoint-state-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'disjoint-state-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)
