"""Fresh exact-code full profiles and separate diagnostic counters."""
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent

def run(label, arguments):
    with (STUDY / (label + '.controller.stdout')).open('xb') as stdout, (STUDY / (label + '.controller.stderr')).open('xb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)

run('profile-build', ['build_profile.py', '--receipt', 'profile-prepared-refill-build-v1',
    '--source', 'counting-prepared-refill', '--output', 'counting-prepared-refill-profile',
    '--package', 'owner-counting-prepared-refill', '--compiler', 'compiler-v73'])
for i in (1, 2, 3):
    folder = f'full-profile-prepared-refill-v{i}'
    run('full-profile-' + str(i), ['profile_full.py', folder, 'profile-prepared-refill-build-v1',
        '--input-mode', 'full', '--launch', 'full-disjoint-state-v1/launch.json',
        '--interval', '0.001', '--sample-count', '1', '--sample-duration', '1',
        '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('full-analysis-' + str(i), ['analyze_profile.py', '--timing', 'prepared-refill-timing-v1',
        '--profile-build', 'profile-prepared-refill-build-v1', '--samples', folder,
        '--binary', 'counting-prepared-refill'])
run('full-partition', ['profile_hotspots.py', '--mech', *[f'full-profile-prepared-refill-v{i}' for i in (1, 2, 3)],
    '--rust', 'rust-full-profile-v17', '--receipt', 'prepared-refill-full-remaining-profile-v1'])
run('diagnostics', ['prepared-refill-v1/diagnostics.py'])
run('prefix-counters', ['prepared-refill-v1/prefix-counters.py'])
