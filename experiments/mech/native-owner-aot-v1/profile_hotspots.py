"""Summarize exclusive worker observations without treating them as wall time."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

from analyze_profile import sha

HERE = Path(__file__).resolve().parent
WAIT = ('__psynch_cvwait', '__psynch_mutexwait', '__ulock_wait',
        'semaphore_wait_trap', '__semwait_signal', 'mach_msg2_trap')
BUDGET = ('NativeLibraryWorkBudget6charge', 'NativeWorkDebitBatch6charge',
          '::NativeWorkDebitBatch::charge', 'NativeWorkMeter6charge')
STORAGE = ('program_packed_map', '10map_owners6closed')


def leaves(content):
    """Return exclusive stack observations, preserving their ancestor context."""
    graph = content.split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
    result, stack, roots = [], [], {}
    thread = None

    def finish():
        depth, count, children, symbol = stack.pop()
        assert 0 <= children <= count
        if count > children:
            result.append((thread, symbol, count - children,
                           tuple(node[3] for node in stack) + (symbol,)))

    for line in graph.splitlines():
        match = re.match(r'^[\s+!:|]*(\d+) (\S+)', line)
        if not match:
            continue
        count, symbol, depth = int(match[1]), match[2], match.start(1)
        if symbol.startswith('Thread_'):
            while stack:
                finish()
            thread = symbol
            assert thread not in roots
            roots[thread] = count
            continue
        assert thread is not None
        while stack and stack[-1][0] >= depth:
            finish()
        if stack:
            stack[-1][2] += count
        stack.append([depth, count, 0, symbol])
    while stack:
        finish()
    totals = Counter()
    for thread, _, count, _ in result:
        totals[thread] += count
    assert dict(totals) == roots, 'Exclusive stack partition differs from thread roots'
    return result


def matches(context, patterns):
    return any(pattern in symbol for symbol in context for pattern in patterns)


def category(symbol, context, language):
    budget = matches(context, BUDGET)
    if matches((symbol,), WAIT):
        return 'work_budget_wait' if budget else 'other_wait'
    if language == 'mech':
        if symbol.startswith('mech_canonical_program_entry_v1_packed_loop_'):
            return 'generated_counting_loop'
        if symbol.endswith('_preserving_bound_call'):
            return 'generated_helper_bridge'
        if symbol == 'mech_canonical_program_entry_v1':
            return 'generated_root'
        if budget:
            return 'work_budget_active'
        if matches(context, STORAGE):
            return 'storage_helper_active'
    elif any('knucleotide_rust_74freq' in value or
             ('knucleotide_rust_74calc' in value and '7ExecuteI' in value and '6Future4poll' in value)
             for value in context):
        return 'rust_counting_task_active'
    return 'other_active'


def summarize(path, workers, language, expected):
    content = path.read_text()
    entries = leaves(content)
    buckets, symbols, by_thread = Counter(), Counter(), Counter()
    for thread, symbol, count, context in entries:
        if thread in workers:
            buckets[category(symbol, context, language)] += count
            symbols[symbol] += count
            by_thread[thread] += count
    assert set(by_thread) == workers and sum(by_thread.values()) == expected
    return dict(stacks=str(path.relative_to(HERE)), stacks_sha256=sha(path.read_bytes()),
                observed_worker_threads=len(workers), worker_observations=expected,
                exclusive_buckets=dict(buckets),
                exclusive_percent={key: 100 * count / expected for key, count in buckets.items()},
                top_exclusive_symbols=[dict(symbol=symbol, observations=count)
                                       for symbol, count in symbols.most_common(20)])


parser = argparse.ArgumentParser()
parser.add_argument('--mech', nargs='+', required=True)
parser.add_argument('--rust', required=True)
parser.add_argument('--receipt', required=True)
args = parser.parse_args()
out = HERE / args.receipt
out.mkdir(exist_ok=False)
evidence, samples = [], dict(mech=[], rust=[])
for folder in args.mech:
    path = HERE / folder / 'analysis.json'
    report = json.loads(path.read_text())
    assert report['machine_code_identical'] and report['completed_output_verified']
    evidence.append(dict(path=str(path.relative_to(HERE)), sha256=sha(path.read_bytes())))
    for item in report['samples']:
        workers = {thread['thread'] for thread in item['threads'] if thread['observed_native_worker']}
        sample = summarize(HERE / item['stacks'], workers, 'mech', item['observed_workers']['thread_samples'])
        assert sample['stacks_sha256'] == item['stacks_sha256']
        sample['main_observations'] = item['main_thread']['samples']
        sample['main_join_observations'] = item['main_thread']['inclusive_samples']['thread_join']
        samples['mech'].append(sample)
path = HERE / args.rust / 'analysis.json'
report = json.loads(path.read_text())
assert report['status'] == 'exact-timed-rust-binary-profiled'
evidence.append(dict(path=str(path.relative_to(HERE)), sha256=sha(path.read_bytes())))
for item in report['samples']:
    workers = {thread['thread'] for thread in item['threads'] if thread['counting_task_samples'] > 0}
    expected = sum(thread['samples'] for thread in item['threads'] if thread['thread'] in workers)
    sample = summarize(HERE / item['stacks'], workers, 'rust', expected)
    assert sample['stacks_sha256'] == item['stacks_sha256']
    samples['rust'].append(sample)
aggregates = {}
for language, observations in samples.items():
    counts, total = Counter(), 0
    for sample in observations:
        counts.update(sample['exclusive_buckets'])
        total += sample['worker_observations']
    assert sum(counts.values()) == total
    aggregates[language] = dict(worker_observations=total, exclusive_buckets=dict(counts),
                               exclusive_percent={key: 100 * count / total for key, count in counts.items()})
result = dict(status='exclusive-worker-observations-partitioned', samples=samples,
              aggregates=aggregates, evidence=evidence, script_sha256=sha(Path(__file__).read_bytes()),
              scope='Exclusive observed stack leaves, classified with ancestor context. Buckets partition worker observations, including waits. These are sampled thread observations, not elapsed-time shares, CPU utilization, instruction costs or benchmark samples. Capture windows differ; loader/startup overhead and collapsed PCs prohibit assigning precise wall seconds to these categories.',
              benchmark_samples=0)
(out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(aggregates, indent=2))
