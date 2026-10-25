"""Build an exact-code profile image, then run serial fresh diagnostics."""
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


run('profile-build', ['build_profile.py', '--receipt', 'profile-aligned-probe-groups-build-v1',
    '--source', 'counting-aligned-probe-groups', '--output', 'counting-aligned-probe-groups-profile',
    '--package', 'owner-counting-aligned-probe-groups', '--compiler', 'compiler-v75'])
run('profile-capture', ['aligned-probe-groups-v1/profile-capture.py'])
run('profile-analysis', ['aligned-probe-groups-v1/analyze.py'])
run('counter', ['aligned-probe-groups-v1/counters.py'])
run('threads', ['aligned-probe-groups-v1/threads.py', 'aligned-probe-groups-v1/thread-observations'])
