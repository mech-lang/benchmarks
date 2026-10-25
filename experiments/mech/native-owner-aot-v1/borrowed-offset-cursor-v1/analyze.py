"""Partition fresh exact-binary thread observations and retain full contexts."""
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import stack_threads, text_section
from profile_hotspots import leaves, category, matches, WAIT, BUDGET, REFILL, TAXONOMY_VERSION
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state


def rows(counter, limit=60):
    return [dict(symbol=s, observations=n) for s, n in counter.most_common(limit)]


def main():
    plan = read(STUDY / 'plan-v2.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    result = dict(status='analyzing', source=before, analysis_sha256=process.sha(Path(__file__)),
                  taxonomy_version=TAXONOMY_VERSION, benchmark_samples=0, languages={})
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for language in ('mech', 'rust'):
            folder = STUDY / ('early-' + language + '-profile-v1')
            capture = read(folder / 'results.json')
            binary = Path(capture['binary_path'])
            assert capture['status'] == 'profile-captured' and capture['completed_output_verified']
            assert process.sha(binary) == capture['binary_sha256']
            assert hashlib.sha256(text_section(binary)).hexdigest() == capture['machine_code_sha256']
            symbol_paths = {}
            for label, options in [('raw', []), ('pretty', ['--demangle'])]:
                out = folder / ('nm-' + label)
                receipt = process.execute(['/usr/bin/nm', '-n'] + options + [str(binary)],
                                          out, env, lock, deadline=30, quantitative=False)
                assert receipt['exit_status'] == 0
                symbol_paths[label] = out / 'stdout.bin'
            names = {}
            for line in symbol_paths['pretty'].read_text().splitlines():
                match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
                if match:
                    names.setdefault(match[1], []).append(match[2])
            demangled = {}
            for line in symbol_paths['raw'].read_text().splitlines():
                match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
                if match and match[1] in names:
                    demangled[match[2].lstrip('_')] = max(names[match[1]], key=len)
            def readable(symbol):
                return demangled.get(symbol.lstrip('_'), symbol)
            patterns = dict(generated_program_entry=('mech_canonical_program_entry_v1',),
                            parallel_worker_entry=('10run_worker', '::run_worker'),
                            parallel_dispatch=('12run_parallel', '::run_parallel'))
            symbols = dict(main=Counter(), workers=Counter(), other=Counter())
            contexts = dict(main=Counter(), workers=Counter(), other=Counter())
            buckets, routes, samples = Counter(), Counter(), []
            main_categories = Counter()
            per_worker = []
            for index, item in enumerate(capture['samples']):
                path = folder / f'sample-{index}' / 'stacks.txt'
                assert process.sha(path) == item['stacks_sha256']
                content = path.read_text()
                graph = content.split('Call graph:\n', 1)[1].split('Total number in stack', 1)[0]
                if not re.search(r'\d+ Thread_', graph):
                    samples.append(dict(index=index, empty=True, stacks_sha256=process.sha(path)))
                    continue
                threads = stack_threads(content, patterns)
                mains = {t['thread'] for t in threads if t['main_thread']}
                entries = leaves(content)
                if language == 'mech':
                    workers = {t['thread'] for t in threads if t['observed_native_worker']}
                else:
                    workers = {thread for thread, symbol, count, context in entries if thread not in mains
                               and any('knucleotide_rust_7::freq::' in s or
                                       ('knucleotide_rust_7::calc<' in s and
                                        ' as futures::future::Future>::poll' in s)
                                       for s in map(readable, context))}
                local_counts, local_buckets = Counter(), Counter()
                for thread, symbol, count, context in entries:
                    role = 'main' if thread in mains else 'workers' if thread in workers else 'other'
                    symbols[role][readable(symbol)] += count
                    contexts[role][tuple(map(readable, context))] += count
                    local_counts[thread] += count
                    if role == 'workers':
                        label = category(symbol, context, language)
                        buckets[label] += count
                        local_buckets[label] += count
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
                            routes[(label, route)] += count
                    elif role == 'main':
                        main_categories['wait' if matches((symbol,), WAIT) else
                                        'partial_dyld_start' if symbol == '_dyld_start' else 'other_locations'] += count
                assert dict(local_counts) == {t['thread']: t['samples'] for t in threads}
                expected = sum(t['samples'] for t in threads if t['thread'] in workers)
                assert expected == sum(local_buckets.values()) and workers
                local_threads = []
                for t in threads:
                    t['role'] = 'main' if t['thread'] in mains else 'worker' if t['thread'] in workers else 'other'
                    if t['thread'] in workers:
                        hot = Counter()
                        cats = Counter()
                        for th, symbol, count, context in entries:
                            if th == t['thread']:
                                hot[readable(symbol)] += count
                                cats[category(symbol, context, language)] += count
                        local_threads.append(dict(thread=t['thread'], observations=t['samples'],
                                                  buckets=dict(cats), top_symbols=rows(hot, 12)))
                per_worker.extend(dict(sample=index, **t) for t in local_threads)
                samples.append(dict(index=index, empty=False, stacks_sha256=process.sha(path),
                                    threads=threads, worker_count=len(workers),
                                    worker_observations=expected, worker_buckets=dict(local_buckets)))
            total = sum(buckets.values())
            assert total > 0 and len(samples) == 3
            result['languages'][language] = dict(binary_sha256=capture['binary_sha256'],
                machine_code_sha256=capture['machine_code_sha256'],
                capture_sha256=process.sha(folder / 'results.json'), samples=samples, workers=per_worker,
                worker_observations=total, worker_buckets=dict(buckets),
                worker_percent={k: 100 * n / total for k, n in buckets.items()},
                work_budget_routes=[dict(category=k, route=r, observations=n) for (k, r), n in routes.most_common()],
                roles={role: dict(observations=sum(c.values()), top_symbols=rows(c),
                                  top_contexts=[dict(ancestors=s, observations=n) for s, n in contexts[role].most_common(80)])
                       for role, c in symbols.items()}, main_categories=dict(main_categories),
                raw_symbols_sha256=process.sha(symbol_paths['raw']),
                pretty_symbols_sha256=process.sha(symbol_paths['pretty']))
    assert source_state() == before
    result.update(status='exact-current-binary-observations-partitioned', source_after=before,
                  scope='Exclusive stack leaves partition every included thread root. Worker selection uses observed Mech worker-entry/dispatch context or exact demangled Rust freq/future-poll context, always excluding the main thread. Waits, partial unwinds, other threads and empty captures are retained. Observations include profiler overhead and do not divide process elapsed time, CPU time or instruction counts. No successful diagnostic is recaptured to repair its analysis.')
    process.save(STUDY / 'analysis.json', result)
    print(json.dumps({k: dict(worker_percent=v['worker_percent'], main_categories=v['main_categories'],
                             top_main=v['roles']['main']['top_symbols'][:15],
                             top_workers=v['roles']['workers']['top_symbols'][:15])
                      for k, v in result['languages'].items()}, indent=2), flush=True)


if __name__ == '__main__':
    main()
