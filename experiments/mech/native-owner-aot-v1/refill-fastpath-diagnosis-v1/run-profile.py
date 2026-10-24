"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '36a0d26e05b92f0f3fb21bdbd3605af2108ec882'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-refill-fastpath-build-v1', '--source', 'counting-refill-fastpath', '--output', 'counting-refill-fastpath-profile', '--package', 'owner-counting-refill-fastpath', '--compiler', 'compiler-v63'])
for index in range(1, 4):
    samples = f'full-profile-refill-fastpath-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-refill-fastpath-build-v1', '--launch', 'full-refill-fastpath-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'refill-fastpath-timing-v1', '--profile-build', 'profile-refill-fastpath-build-v1', '--samples', samples, '--binary', 'counting-refill-fastpath'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'refill-fastpath-codegen-audit-v{index}', '--timing', 'refill-fastpath-timing-v1', '--profile-build', 'profile-refill-fastpath-build-v1', '--samples', samples, '--binary', 'counting-refill-fastpath'])
run('static-paths', ['audit_split_paths.py', '--audit', 'refill-fastpath-codegen-audit-v1'])
run('runtime-refill', ['refill-fastpath-diagnosis-v1/audit-refill.py'])
run('hardware', ['hardware_counters.py', '--receipt', 'refill-fastpath-hardware-v1', '--timing', 'refill-fastpath-timing-v1', '--compiler', 'compiler-v63'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-refill-fastpath-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'refill-fastpath-remaining-profile-v1'])
report = json.loads((HERE / 'refill-fastpath-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'refill-fastpath-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)
