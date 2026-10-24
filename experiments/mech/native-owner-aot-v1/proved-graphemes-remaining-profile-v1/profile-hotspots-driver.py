"""Summarize exclusive worker observations without treating them as wall time."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

from analyze_profile import sha

HERE = Path(__file__).resolve().parent
TAXONOMY_VERSION = 5
WAIT = ('__psynch_cvwait', '__psynch_mutexwait', '__ulock_wait',
        'semaphore_wait_trap', '__semwait_signal', 'mach_msg2_trap')
BUDGET = ('7workers11lock_escrow', '::budget::workers::lock_escrow',
          'NativeLibraryWorkBudget6charge', 'NativeWorkDebitBatch6charge',
          '::NativeWorkDebitBatch::charge', 'NativeWorkMeter6charge',
          'NativeLibraryWorkBudget18unscoped_remaining',
          '::NativeLibraryWorkBudget::unscoped_remaining',
          'NativeWorkerWorkLoan9remaining', '::NativeWorkerWorkLoan::remaining',
          'NativeWorkerWorkLoan6charge', '::NativeWorkerWorkLoan::charge',
          '19with_unscoped_debit', '::with_unscoped_debit')
STORAGE = ('program_packed_map', '10map_owners6closed')
# The refill helper validates the private frame, calculates finite fuel and
# debits it. Its only mutex is worker escrow. LLVM may inline the transaction
# into this helper, so a vanished API symbol must not hide its waits or work.
REFILL = ('9PackedMap6refill', '::PackedMap::refill')


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
            thread = symbol.rstrip(':')
            roots[thread] = roots.get(thread, 0) + count
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
    budget = matches(context, BUDGET) or (language == 'mech' and matches(context, REFILL))
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
    budget_routes, wait_contexts = Counter(), Counter()
    for thread, symbol, count, context in entries:
        if thread in workers:
            label = category(symbol, context, language)
            buckets[label] += count
            symbols[symbol] += count
            by_thread[thread] += count
            if label in ('work_budget_wait', 'work_budget_active'):
                if matches(context, ('18unscoped_remaining', '::unscoped_remaining')):
                    route = 'remaining_work_query'
                elif matches(context, ('14insert_missing', '::insert_missing')):
                    route = 'missing_key_charge'
                elif matches(context, REFILL):
                    route = 'loop_refill'
                elif matches(context, ('6frozen', '::frozen::')):
                    route = 'frozen_map_charge'
                else:
                    route = 'other_budget_operation'
                budget_routes[(label, route)] += count
            if label.endswith('_wait'):
                wait_contexts[(label, tuple(context[-8:]))] += count
    assert set(by_thread) == workers and sum(by_thread.values()) == expected
    assert sum(budget_routes.values()) == sum(buckets[key] for key in
                                              ('work_budget_wait', 'work_budget_active'))
    return dict(stacks=str(path.relative_to(HERE)), stacks_sha256=sha(path.read_bytes()),
                observed_worker_threads=len(workers), worker_observations=expected,
                exclusive_buckets=dict(buckets),
                exclusive_percent={key: 100 * count / expected for key, count in buckets.items()},
                work_budget_routes=[dict(category=label, route=route, observations=count)
                                    for (label, route), count in budget_routes.most_common()],
                top_wait_contexts=[dict(category=label, ancestors=context, observations=count)
                                   for (label, context), count in wait_contexts.most_common(10)],
                top_exclusive_symbols=[dict(symbol=symbol, observations=count)
                                       for symbol, count in symbols.most_common(20)])


def main():
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
        counts, routes, total = Counter(), Counter(), 0
        for sample in observations:
            counts.update(sample['exclusive_buckets'])
            routes.update({(item['category'], item['route']): item['observations']
                           for item in sample['work_budget_routes']})
            total += sample['worker_observations']
        assert sum(counts.values()) == total
        assert sum(routes.values()) == sum(counts[key] for key in
                                          ('work_budget_wait', 'work_budget_active'))
        aggregates[language] = dict(worker_observations=total, exclusive_buckets=dict(counts),
                                   work_budget_routes=[dict(category=label, route=route, observations=count)
                                                       for (label, route), count in routes.most_common()],
                                   exclusive_percent={key: 100 * count / total for key, count in counts.items()})
    result = dict(status='exclusive-worker-observations-partitioned', samples=samples,
                  aggregates=aggregates, evidence=evidence, script_sha256=sha(Path(__file__).read_bytes()),
                  taxonomy_version=TAXONOMY_VERSION,
                  taxonomy_change='The shared worker-escrow lock helper is accounting, including active bounded spins and blocked fallback frames. Repeated thread-ID roots are disjoint observed phases and are merged without double counting. Main-thread flags accept both startup and dispatch-queue labels. Work-budget observations include remaining-work queries, charges and the entire packed-loop refill helper, including its validation/pricing. The refill helper has only the worker escrow mutex; transaction inlining must not hide its waits. Earlier taxonomies can classify remaining queries or inlined refill work as storage/other waits. Use this same taxonomy on both parent and candidate before comparing distributions.',
                  scope='Exclusive observed stack leaves, classified with ancestor context. Buckets partition worker observations, including waits. These are sampled thread observations, not elapsed-time shares, CPU utilization, instruction costs or benchmark samples. Capture windows differ; loader/startup overhead and collapsed PCs prohibit assigning precise wall seconds to these categories.',
                  benchmark_samples=0)
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(aggregates, indent=2))


if __name__ == "__main__":
    main()
