"""Collect exact-code profiles and separate counters after the qualified trial."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '8c9713b5a77e44175609d5dadef5d86a8b480593'
assert not subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True)
def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode: sys.exit(result.returncode)
run('profile-build', ['build_profile.py', '--receipt', 'profile-line-offset-crlf-build-v1', '--source', 'counting-line-offset-crlf', '--output', 'counting-line-offset-crlf-profile', '--package', 'owner-counting-line-offset-crlf', '--compiler', 'compiler-v67'])
for index in range(1, 4):
    samples = f'full-profile-line-offset-crlf-v{index}'
    run('profile-' + str(index), ['profile_full.py', samples, 'profile-line-offset-crlf-build-v1', '--launch', 'full-line-offset-crlf-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1', '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'line-offset-crlf-timing-v1', '--profile-build', 'profile-line-offset-crlf-build-v1', '--samples', samples, '--binary', 'counting-line-offset-crlf'])
    run('audit-' + str(index), ['audit_entry.py', '--receipt', f'line-offset-crlf-codegen-audit-v{index}', '--timing', 'line-offset-crlf-timing-v1', '--profile-build', 'profile-line-offset-crlf-build-v1', '--samples', samples, '--binary', 'counting-line-offset-crlf'])
run('static-paths', ['audit_split_paths.py', '--audit', 'line-offset-crlf-codegen-audit-v1'])
run('hardware', ['hardware_counters.py', '--receipt', 'line-offset-crlf-hardware-v1', '--timing', 'line-offset-crlf-timing-v1', '--compiler', 'compiler-v67'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-line-offset-crlf-v{i}' for i in range(1, 4)], '--rust', 'rust-full-profile-v17', '--receipt', 'line-offset-crlf-remaining-profile-v1'])
report = json.loads((HERE / 'line-offset-crlf-remaining-profile-v1/results.json').read_text())
driver = (HERE / 'profile_hotspots.py').read_bytes()
assert hashlib.sha256(driver).hexdigest() == report['script_sha256']
(HERE / 'line-offset-crlf-remaining-profile-v1/profile-hotspots-driver.py').write_bytes(driver)
