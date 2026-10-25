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

run('profile-build', ['build_profile.py', '--receipt', 'profile-packed-domain-validation-build-v1',
    '--source', 'counting-packed-domain-validation', '--output', 'counting-packed-domain-validation-profile',
    '--package', 'owner-counting-packed-domain-validation', '--compiler', 'compiler-v72'])
for i in (1, 2, 3):
    folder = f'full-profile-packed-domain-validation-v{i}'
    run('full-profile-' + str(i), ['profile_full.py', folder, 'profile-packed-domain-validation-build-v1',
        '--input-mode', 'full', '--launch', 'full-disjoint-state-v1/launch.json',
        '--interval', '0.001', '--sample-count', '1', '--sample-duration', '1',
        '--require-completion', '--require-packed-map', '--require-packed-ssa', '--require-parallel'])
    run('full-analysis-' + str(i), ['analyze_profile.py', '--timing', 'packed-domain-validation-timing-v1',
        '--profile-build', 'profile-packed-domain-validation-build-v1', '--samples', folder,
        '--binary', 'counting-packed-domain-validation'])
run('full-partition', ['profile_hotspots.py', '--mech', *[f'full-profile-packed-domain-validation-v{i}' for i in (1, 2, 3)],
    '--rust', 'rust-full-profile-v17', '--receipt', 'packed-domain-validation-full-remaining-profile-v1'])
run('diagnostics', ['packed-domain-validation-v1/diagnostics.py'])
run('prefix-counters', ['packed-domain-validation-v1/prefix-counters.py'])
