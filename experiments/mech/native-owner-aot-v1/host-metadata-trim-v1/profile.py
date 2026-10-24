"""Profile the exact-code host candidate, then collect separate startup/memory data."""
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent


def run(label, arguments):
    with (STUDY / (label + '.controller.stdout')).open('wb') as stdout, (STUDY / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


run('profile-build', ['build_profile.py', '--receipt', 'profile-host-metadata-trim-build-v1', '--source', 'counting-host-metadata-trim',
    '--output', 'counting-host-metadata-trim-profile', '--package', 'owner-counting-host-metadata-trim', '--compiler', 'compiler-v70'])
for index in (1, 2, 3):
    folder = f'full-profile-host-metadata-trim-v{index}'
    run('profile-' + str(index), ['profile_full.py', folder, 'profile-host-metadata-trim-build-v1',
        '--launch', 'full-disjoint-state-v1/launch.json', '--interval', '0.01', '--sample-count', '1', '--sample-duration', '1',
        '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('analysis-' + str(index), ['analyze_profile.py', '--timing', 'host-metadata-trim-timing-v1',
        '--profile-build', 'profile-host-metadata-trim-build-v1', '--samples', folder, '--binary', 'counting-host-metadata-trim'])
run('partition', ['profile_hotspots.py', '--mech', *[f'full-profile-host-metadata-trim-v{i}' for i in (1, 2, 3)],
    '--rust', 'rust-full-profile-v17', '--receipt', 'host-metadata-trim-remaining-profile-v1'])
run('startup', ['host-metadata-trim-v1/startup.py'])
run('diagnostics', ['host-metadata-trim-v1/diagnostics.py'])
