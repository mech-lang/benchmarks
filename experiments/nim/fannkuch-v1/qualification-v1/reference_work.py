"""Bounded trace oracle and strict work replay; never a timing oracle.

Permutation order follows the already retained independent Python reference's
decrementing-count/r state machine, rather than the Nim source's increasing
rotation counters or worker unranking. Actual swap states are checked explicitly.
"""
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def permutations(n):
    require(1 <= n <= 6, 'Detailed work oracle is deliberately bounded to n <= 6')
    permutation = list(range(n))
    count = [0] * n
    r, rank = n, 0
    while True:
        while r != 1:
            count[r - 1] = r
            r -= 1
        yield rank, permutation.copy()
        rank += 1
        while True:
            if r == n:
                require(rank == math.factorial(n), 'Independent permutation coverage differs')
                return
            permutation[:r + 1] = permutation[1:r + 1] + permutation[:1]
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1


def expected_work(n):
    result = []
    for rank, permutation in permutations(n):
        working = permutation.copy()
        reversals = []
        while working[0]:
            bound = working[0]
            before = working.copy()
            swaps = []
            for left in range((bound + 1) // 2):
                right = bound - left
                working[left], working[right] = working[right], working[left]
                swaps.append((left, right, working.copy()))
            reversals.append(dict(bound=bound, before=before, swaps=swaps))
        flips = len(reversals)
        result.append(dict(rank=rank, permutation=permutation, reversals=reversals,
            flips=flips, contribution=flips if rank % 2 == 0 else -flips))
    require(len({tuple(row['permutation']) for row in result}) == math.factorial(n),
        'Independent oracle repeated a permutation')
    return result


def output(rows, n):
    checksum = sum(row['contribution'] for row in rows)
    maximum = max((row['flips'] for row in rows), default=0)
    return f'{checksum}\nPfannkuchen({n}) = {maximum}\n'.encode('ascii')


def parse_array(value, n):
    values = [int(part) for part in value.split(',')]
    require(len(values) == n, 'Trace array width differs')
    return values


def worker_trace(path, n, first, last, oracle, guarded):
    lines = Path(path).read_text(encoding='ascii').splitlines()
    index = 0

    def take(expected):
        nonlocal index
        require(index < len(lines), 'Work trace ended before an expected event')
        actual = lines[index].split('\t')
        index += 1
        require(actual == list(map(str, expected)),
            f'Work event differs at {path}:{index}: {actual!r} != {expected!r}')

    def event(kind, rank, x, y, values):
        take([kind, rank, x, y, ','.join(map(str, values))])

    take(['begin', first, last, n])
    checksum = maximum = copies = flips = swaps = zero_first = 0
    ranks = []
    for rank in range(first, last):
        row = oracle[rank]
        permutation = row['permutation']
        require(sorted(permutation) == list(range(n)), 'Oracle permutation domain differs')
        event('rank', rank, -1, -1, permutation)
        counters = [0] + [(rank // math.factorial(width - 1)) % width for width in range(2, n + 1)]
        event('rotations', rank, -1, -1, counters)
        zero_first += int(permutation[0] == 0)
        if not guarded or permutation[0] != 0:
            copies += 1
            event('copy', rank, -1, -1, permutation)
        for reversal in row['reversals']:
            event('flip', rank, reversal['bound'], 0, reversal['before'])
            flips += 1
            for left, right, state in reversal['swaps']:
                require(sorted(state) == list(range(n)), 'Swap altered the value domain')
                event('swap', rank, left, right, state)
                swaps += 1
        checksum += row['contribution']
        maximum = max(maximum, row['flips'])
        event('done', rank, row['flips'], checksum, permutation)
        event('maximum', rank, maximum, 0, permutation)
        ranks.append(rank)
    take(['end', first, last, checksum, maximum])
    require(index == len(lines), 'Unexpected additional work trace records')
    return dict(first=first, last=last, permutations=len(ranks), ranks=ranks,
        scratch_copies=copies, zero_first_permutations=zero_first,
        actual_prefix_reversals=flips, actual_endpoint_swaps=swaps,
        checksum=checksum, maximum=maximum, exact_all_events=True,
        no_missing_or_additional_records=True)


def validate(directory, n, parallel, guarded, raw, first=None, last=None):
    directory = Path(directory)
    oracle = expected_work(n)
    total = math.factorial(n)
    interval_mode = first is not None or last is not None
    require((first is not None) == (last is not None), 'Partial diagnostic interval')
    if interval_mode:
        require(parallel and 0 <= first < last <= total, 'Invalid diagnostic worker range')
        ranges = [(first, last)]
        expected_files = {f'{first}-{last}.tsv'}
    elif parallel:
        count = min(8, total)
        ranges = [(total * worker // count, total * (worker + 1) // count) for worker in range(count)]
        main = (directory / 'main.tsv').read_text(encoding='ascii').splitlines()
        expected_main = [f'workers\t{count}']
        expected_main += [f'created\t{worker}\t{lo}\t{hi}' for worker, (lo, hi) in enumerate(ranges)]
        expected_main += [f'joined\t{worker}' for worker in range(count)]
        require(main == expected_main, 'Actual native thread creation/join events differ')
        expected_files = {'main.tsv'} | {f'{lo}-{hi}.tsv' for lo, hi in ranges}
    else:
        ranges = [(0, total)]
        expected_files = {f'0-{total}.tsv'}
    require({path.name for path in directory.iterdir()} == expected_files,
        'Unexpected, missing or duplicate native worker trace files')
    workers = [worker_trace(directory / f'{lo}-{hi}.tsv', n, lo, hi, oracle, guarded)
        for lo, hi in ranges]
    ranks = [rank for worker in workers for rank in worker.pop('ranks')]
    lo, hi = (first, last) if interval_mode else (0, total)
    require(ranks == list(range(lo, hi)), 'Native worker intervals overlap or omit ranks')
    expected = output(oracle[lo:hi], n)
    require(raw == expected, 'Instrumented whole output differs from the trace oracle')
    aggregate = {key: sum(worker[key] for worker in workers) for key in
        ['permutations', 'scratch_copies', 'zero_first_permutations',
         'actual_prefix_reversals', 'actual_endpoint_swaps', 'checksum']}
    aggregate['maximum'] = max(worker['maximum'] for worker in workers)
    require(aggregate['permutations'] == hi - lo, 'Observed permutation count differs')
    if not interval_mode:
        require(aggregate['zero_first_permutations'] == math.factorial(n - 1),
            'Zero-first permutation count differs')
    expected_copies = hi - lo - (aggregate['zero_first_permutations'] if guarded else 0)
    require(aggregate['scratch_copies'] == expected_copies, 'Scratch-copy guard work differs')
    return dict(status='PASSED', n=n, interval=[lo, hi], interval_mode=interval_mode,
        workers=workers, aggregate=aggregate, exact_native_events=True,
        actual_created_threads=0 if interval_mode or not parallel else len(workers),
        actual_joined_threads=0 if interval_mode or not parallel else len(workers),
        maximum_workers=8, no_gap_or_overlap=True, all_native_threads_joined=True,
        full_array_domain_checked=True, expected_output_hex=expected.hex())
