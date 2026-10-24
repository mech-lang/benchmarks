"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == 'e82ed4d54d4490102ac41192d1fcbf492d467e08'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-preparation-combined-build-v1', '--source', 'counting-preparation-combined', '--output', 'counting-preparation-combined-profile', '--package', 'owner-counting-preparation-combined', '--compiler', 'compiler-v69'])
for index in range(1, 4):
    samples = f'full-profile-preparation-combined-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-preparation-combined-build-v1', '--launch', 'full-disjoint-state-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'preparation-combined-timing-v1', '--profile-build', 'profile-preparation-combined-build-v1', '--samples', samples, '--binary', 'counting-preparation-combined'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'preparation-combined-codegen-audit-v{index}', '--timing', 'preparation-combined-timing-v1', '--profile-build', 'profile-preparation-combined-build-v1', '--samples', samples, '--binary', 'counting-preparation-combined'])
run('static-paths', ['audit_split_paths.py', '--audit', 'preparation-combined-codegen-audit-v1'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-preparation-combined-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'preparation-combined-remaining-profile-v1'])
report = json.loads((HERE / 'preparation-combined-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'preparation-combined-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)
