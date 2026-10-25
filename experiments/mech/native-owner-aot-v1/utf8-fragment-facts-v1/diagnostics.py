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


run('profile-build', ['build_profile.py', '--receipt', 'profile-utf8-fragment-facts-build-v1',
    '--source', 'counting-utf8-fragment-facts', '--output', 'counting-utf8-fragment-facts-profile',
    '--package', 'owner-counting-utf8-fragment-facts', '--compiler', 'compiler-v76'])
run('profile-capture', ['utf8-fragment-facts-v1/profile-capture.py'])
run('profile-analysis', ['utf8-fragment-facts-v1/analyze.py'])
run('counter', ['utf8-fragment-facts-v1/counters.py'])
run('threads', ['utf8-fragment-facts-v1/threads.py', 'utf8-fragment-facts-v1/thread-observations'])

run('assembly', ['utf8-fragment-facts-v1/audit.py'])
