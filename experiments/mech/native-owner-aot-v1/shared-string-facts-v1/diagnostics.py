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


run('profile-build', ['build_profile.py', '--receipt', 'profile-shared-string-facts-build-v1',
    '--source', 'counting-shared-string-facts', '--output', 'counting-shared-string-facts-profile',
    '--package', 'owner-counting-shared-string-facts', '--compiler', 'compiler-v74'])
run('profile-capture', ['shared-string-facts-v1/profile-capture.py'])
run('profile-analysis', ['shared-string-facts-v1/analyze.py'])
run('counter', ['shared-string-facts-v1/counters.py'])
run('threads', ['shared-string-facts-v1/threads.py', 'shared-string-facts-v1/thread-observations'])
