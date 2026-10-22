"""Replay all seven spectral-norm cases against the explicit corrected source overlay."""
import fcntl
import json
from pathlib import Path
import run as controller
from outputs import validate_success

root = controller.ROOT
plan_path = root/'experiments/janet/bounded-v1/plan-v1.json'
plan = json.loads(plan_path.read_bytes())
for name, pin in plan['pins'].items():
    p = Path(name) if name.startswith('/') else root/name
    assert controller.sha(p) == pin['sha256'], name
source = root/'experiments/janet/source-v3/spectralnorm.janet'
output = Path(__file__).parent/'spectral-run-v1'
output.mkdir(exist_ok=False)
report = dict(status='running', source=str(source.relative_to(root)), source_sha256=controller.sha(source),
              plan_sha256=controller.sha(plan_path), observations=[], benchmark_samples=0, chart_admission=False,
              runner_sha256=controller.sha(Path(__file__)))
corpus_path = root/plan['corpus']
corpus = json.loads(corpus_path.read_bytes())
with Path(plan['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    report['mutex_inode'] = __import__('os').fstat(lock.fileno()).st_ino
    for row in plan['schedule']:
        if row['benchmark'] != 'spectralnorm': continue
        command = list(row['command']); command[3] = str(source)
        directory = output/row['case']
        process = controller.execute(command, directory, plan['environment'], lock, root/row['stdin'])
        case = corpus['cases'][row['corpus_index']]
        expected = (corpus_path.parent/case['expected']['path']).read_bytes()
        receipt = validate_success(case, (directory/'stdout.bin').read_bytes(), (directory/'stderr.bin').read_bytes(), process['exit_status'], expected)
        report['observations'].append(receipt)
        controller.save(output/'results.json', report)
    report['status'] = 'seven-spectral-bounded-outputs-pass'
    controller.save(output/'results.json', report)
print(report['status'])
