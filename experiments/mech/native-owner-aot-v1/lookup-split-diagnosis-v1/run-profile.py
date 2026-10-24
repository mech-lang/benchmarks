"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '65dfd8bef29a8aef4cddd6926ff6461a959c24be'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-lookup-split-build-v1', '--source', 'counting-lookup-split', '--output', 'counting-lookup-split-profile', '--package', 'owner-counting-lookup-split', '--compiler', 'compiler-v62'])
for index in range(1, 4):
    samples = f'full-profile-lookup-split-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-lookup-split-build-v1', '--launch', 'full-lookup-split-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'lookup-split-timing-v2', '--profile-build', 'profile-lookup-split-build-v1', '--samples', samples, '--binary', 'counting-lookup-split'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'lookup-split-codegen-audit-v{index}', '--timing', 'lookup-split-timing-v2', '--profile-build', 'profile-lookup-split-build-v1', '--samples', samples, '--binary', 'counting-lookup-split'])
run('hardware', ['hardware_counters.py', '--receipt', 'lookup-split-hardware-v1', '--timing', 'lookup-split-timing-v2', '--compiler', 'compiler-v62'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-lookup-split-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'lookup-split-remaining-profile-v1'])
report = json.loads((HERE / 'lookup-split-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'lookup-split-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)
