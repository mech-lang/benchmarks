"""Six predeclared balanced full-process comparisons; no discarded runs."""
import json
import pathlib
import subprocess
import sys

STUDY = pathlib.Path(__file__).resolve().parent.parent
ORDERS = [
    ['rust', 'mech', 'baseline'], ['baseline', 'rust', 'mech'], ['mech', 'baseline', 'rust'],
    ['baseline', 'mech', 'rust'], ['mech', 'rust', 'baseline'], ['rust', 'baseline', 'mech'],
]
names = []
for i, order in enumerate(ORDERS, 1):
    name = f'full-snapshot-v{i}'
    assert not (STUDY / name).exists()
    command = [sys.executable, str(STUDY / 'qualify_full.py'),
        '--timing', 'snapshot-timing-v1', '--compiler', 'compiler-v49',
        '--binary', 'counting-snapshot', '--receipt', name,
        '--parent-receipt', 'steady-fold-timing-v1', '--parent-binary', 'counting-steady-fold',
        '--comparison-work', str(1 << 56), '--minimum-parallel-peak', '7', '--order', *order]
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode:
        print(process.stdout[-2000:]); print(process.stderr[-2000:])
        raise SystemExit(process.returncode)
    result = json.loads((STUDY / name / 'results.json').read_text())
    assert result['status'] == 'full-output-and-update-counts-verified'
    assert result['launch_sha256'] == '73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9'
    names.append(name)
    print(name, {subject: json.loads((STUDY / name / subject / 'process.json').read_text())['elapsed_seconds']
                 for subject in order}, flush=True)
command = [sys.executable, str(STUDY / 'summarize_full.py'), '--receipt', 'full-snapshot-cohort-v1', *names]
process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if process.returncode:
    print(process.stdout[-2000:]); print(process.stderr[-2000:])
    raise SystemExit(process.returncode)
result = json.loads((STUDY / 'full-snapshot-cohort-v1/results.json').read_text())
print(json.dumps({k: result[k] for k in ['status', 'median_seconds', 'x_rust']}), flush=True)
