"""Analyze observed prefix stacks and resume only unfinished diagnostics.

All three prearmed captures are retained. Capture 1 has an empty call graph;
indices 0 and 2 are the complete inventory of captures with stack observations.
This selects diagnostic observations only, never benchmark timing samples.
"""
import json
import re
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

prefix = 'prefix-profile-sized-schedule-prearmed-v1'
r = json.loads((HERE / prefix / 'results.json').read_text())
observed, empty = [], []
for i, item in enumerate(r['samples']):
    path = HERE / prefix / Path(item['stacks']).parent.name / 'stacks.txt'
    graph = path.read_text().split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    (observed if re.search(r'\d+ Thread_', graph) else empty).append(i)
assert observed == [0, 2] and empty == [1]
(STUDY / 'prefix-observation-inventory.json').write_text(json.dumps(dict(
    capture_count=len(r['samples']), observed_indices=observed, empty_indices=empty,
    selection='All nonempty diagnostic call graphs. All raw captures and all timing observations remain retained.'), indent=2) + '\n')
run('prefix-prearmed-analysis-v2', ['analyze_profile.py', '--timing', 'sized-schedule-timing-v1',
    '--profile-build', 'profile-sized-schedule-build-v1', '--samples', prefix, '--binary', 'counting-sized-schedule',
    '--sample-index', '0', '--sample-index', '2'])
run('prefix-prearmed-partition-v2', ['profile_hotspots.py', '--mech', prefix, '--rust', 'rust-full-profile-v17',
    '--receipt', 'sized-schedule-prefix-remaining-profile-v2'])
run('threads', ['sized-schedule-v1/thread-driver.py', 'sized-schedule-thread-lifetimes-v1'])
run('diagnostics', ['sized-schedule-v1/diagnostics.py'])
run('prefix-counters', ['sized-schedule-v1/prefix-counters.py'])
