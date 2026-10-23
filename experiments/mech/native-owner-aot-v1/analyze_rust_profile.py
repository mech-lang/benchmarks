"""Identify counting-task and waiting stacks per thread in the exact Rust binary."""
import json
import re
import sys
from pathlib import Path
from analyze_profile import sha

HERE = Path(__file__).resolve().parent
folder = HERE / sys.argv[1]
receipt = json.loads((folder / 'results.json').read_text())
assert receipt['status'] == 'three-full-output-verified-profiles'
binary = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
assert sha(binary.read_bytes()) == receipt['binary_sha256']
summaries = []
for index, subject in enumerate(receipt['subjects']):
    path = folder / str(index) / 'stacks.txt'
    assert sha(path.read_bytes()) == subject['sample']['stacks_sha256']
    graph = path.read_text().split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    threads = []
    ancestors = []
    for line in graph.splitlines():
        match = re.match(r'^[\s+!:|]*(\d+) (\S+)', line)
        if not match:
            continue
        count, symbol = int(match[1]), match[2]
        depth = match.start(1)
        if symbol.startswith('Thread_'):
            threads.append(dict(thread=symbol, samples=count, counting_task_samples=0, waiting_samples=0))
            ancestors = []
            continue
        while ancestors and ancestors[-1][0] >= depth:
            ancestors.pop()
        active = set().union(*(labels for _, labels in ancestors))
        matched = set()
        patterns = {
            'counting_task_samples': 'knucleotide_rust_74freq' in symbol or (
                'knucleotide_rust_74calc' in symbol and '7ExecuteI' in symbol and '6Future4poll' in symbol),
            'waiting_samples': symbol == '__psynch_cvwait',
        }
        for label, present in patterns.items():
            if present:
                matched.add(label)
                if label not in active:
                    threads[-1][label] += count
        ancestors.append((depth, matched))
    assert threads
    assert all(t['counting_task_samples'] <= t['samples'] and t['waiting_samples'] <= t['samples'] for t in threads)
    summaries.append(dict(stacks=str(path.relative_to(HERE)), stacks_sha256=sha(path.read_bytes()),
                          counting_threads=sum(t['counting_task_samples'] > 0 for t in threads), threads=threads))
result = dict(status='exact-timed-rust-binary-profiled', binary_sha256=receipt['binary_sha256'],
              scope='Inclusive per-thread stack observations; includes idle/waiting samples; not CPU utilization or benchmark timings',
              aggregation='Union of matching subtrees within each category and thread', samples=summaries)
(folder / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
for sample in summaries:
    print(json.dumps(dict(stacks=sample['stacks'], counting_threads=sample['counting_threads'], main=sample['threads'][0])))
