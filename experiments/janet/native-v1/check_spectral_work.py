"""Execute source-projected term counters; no quantitative timing."""
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
corpus_path = root/plan['corpus']
corpus = json.loads(corpus_path.read_bytes())
out = Path(__file__).parent/'spectral-work-v1'
out.mkdir(exist_ok=False)
report = dict(status='running', benchmark_samples=0, chart_admission=False, observations=[],
              runner_sha256=controller.sha(Path(__file__)), source_projection_only_counters=True)
source_paths = {}
for label, name in [('parent','source-v2'), ('candidate','source-v3')]:
    source = root/f'experiments/janet/{name}/spectralnorm.janet'
    text = source.read_text()
    assert text.count('(for j 0 n') == 1
    assert text.count('(def n (length input))') == 1
    text = '(var term-count 0)\n(var product-count 0)\n' + text
    text = text.replace('(def n (length input))', '(++ product-count)\n  (def n (length input))')
    text = text.replace('(for j 0 n', '(for j 0 n\n      (++ term-count)')
    text = text.replace('(print (string/format "%.9f"', '(file/write stderr (string/format "%d %d\\n" product-count term-count))\n  (print (string/format "%.9f"')
    projection = out/f'{label}.janet'; projection.write_text(text)
    source_paths[label] = projection
    report[label] = dict(source=str(source.relative_to(root)), sha256=controller.sha(source), projection_sha256=controller.sha(projection))
with Path(plan['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for row in plan['schedule']:
        if row['benchmark'] != 'spectralnorm': continue
        case = corpus['cases'][row['corpus_index']]
        for label, source in source_paths.items():
            command = list(row['command']); command[3] = str(source)
            directory = out/f"{label}-{row['case']}"
            process = controller.execute(command, directory, plan['environment'], lock, root/row['stdin'])
            expected_counts = f"40 {40*case['n']**2}\n".encode()
            assert (directory/'stderr.bin').read_bytes() == expected_counts
            validate_success(case, (directory/'stdout.bin').read_bytes(), b'', process['exit_status'], (corpus_path.parent/case['expected']['path']).read_bytes())
            report['observations'].append(dict(label=label, case=row['case'], products=40, terms=40*case['n']**2,
                                              diagnostic_stream_verified=True, stdout_contract_pass=True))
            controller.save(out/'results.json', report)
report['status'] = 'fourteen-source-projected-work-checks-pass'
controller.save(out/'results.json', report)
print(report['status'])
