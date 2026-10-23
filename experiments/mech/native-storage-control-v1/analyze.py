"""Inclusive stack categories for the exact direct-storage control binary."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
folder = HERE / 'full-profile-v1'
patterns = dict(lookup='string_maps6lookup', insert='string_maps6insert',
                string_comparison='memcmp', utf8_validation='converts9from_utf8')
samples = []
for path in sorted(folder.glob('sample-*/stacks.txt')):
    graph = path.read_text().split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    counts = dict.fromkeys(patterns, 0)
    total = None
    root_samples = None
    ancestors = []
    for line in graph.splitlines():
        match = re.match(r'^[\s+!:|]*(\d+) (\S+)', line)
        if not match:
            continue
        count, symbol, depth = int(match[1]), match[2], match.start(1)
        while ancestors and ancestors[-1][0] >= depth:
            ancestors.pop()
        if symbol.startswith('Thread_') and 'com.apple.main-thread' in line:
            assert total is None
            total = count
        if symbol == 'start':
            assert root_samples is None
            root_samples = count
        active = set().union(*(labels for _, labels in ancestors))
        matched = {label for label, pattern in patterns.items() if pattern in symbol}
        for label in matched - active:
            counts[label] += count
        ancestors.append((depth, matched))
    assert total and all(n <= total for n in counts.values())
    samples.append(dict(stacks=str(path.relative_to(HERE)), main_samples=total,
                        samples_unwound_to_start=root_samples,
                        inclusive_samples=counts, inclusive_percent={k: 100 * v / total for k, v in counts.items()}))
assert len(samples) == 3
result = dict(scope='Exact diagnostic control binary; sampled beginning of full input; denominator is all main-thread samples, including partial unwinds; inclusive overlapping categories, not benchmark times',
              patterns=patterns, samples=samples)
(folder / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
