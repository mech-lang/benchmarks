"""Build one combined configuration and run both planned serial cohorts."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def run(label, arguments):
    with (OUT / (label + '.controller.stdout')).open('wb') as stdout, (OUT / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


run('build', ['preparation-interactions-v1/run-build.py'])
for batch in (1, 2):
    run('batch-' + str(batch), ['preparation-interactions-v1/measure.py',
                              f'full-preparation-interactions-v{batch}', str(batch)])
run('analysis', ['preparation-interactions-v1/analyze.py'])
