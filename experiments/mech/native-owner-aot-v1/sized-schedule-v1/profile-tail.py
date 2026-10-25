"""Resume after the retained short-lived sampler attachment failure."""
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


prefix = 'prefix-profile-sized-schedule-prearmed-v1'
run('prefix-prearmed', ['profile_short_launch.py', '--receipt', prefix, '--build', 'profile-sized-schedule-build-v1',
    '--captures', '3', '--minimum-parallel-peak', '1'])
run('prefix-prearmed-analysis', ['analyze_profile.py', '--timing', 'sized-schedule-timing-v1',
    '--profile-build', 'profile-sized-schedule-build-v1', '--samples', prefix, '--binary', 'counting-sized-schedule'])
run('prefix-prearmed-partition', ['profile_hotspots.py', '--mech', prefix, '--rust', 'rust-full-profile-v17',
    '--receipt', 'sized-schedule-prefix-remaining-profile-v2'])
run('threads', ['sized-schedule-v1/thread-driver.py', 'sized-schedule-thread-lifetimes-v1'])
run('diagnostics', ['sized-schedule-v1/diagnostics.py'])
run('prefix-counters', ['sized-schedule-v1/prefix-counters.py'])
