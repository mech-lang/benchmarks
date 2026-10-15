"""Pure complete-seven-map contract; storage capacities are not observed.

The caller pins the exact input, expected stdout, unchanged main and additive
wrapper, then verifies native ownership, limits and complete saved artifacts.
"""
from collections import Counter
import re

WIDTHS = (1, 2, 3, 4, 6, 12, 18)
CORPUS_CASE = ('knucleotide', 'arbitrary-widths')
CORPUS_SHA256 = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
STDIN_SHA256 = '337727c8c84e917740d053e1ce95eafdda30069d1669574df9c08b6c38247a1d'
EXPECTED_STDOUT_SHA256 = '78e220a584e4ea619d9ca9b6feff7354cd4950c018b840ffd5f74287117dd930'
SIDECAR_LIMIT = STDOUT_LIMIT = 1024 * 1024
UINT = rb'(?:0|[1-9][0-9]*)'


def require(value, message):
    if not value:
        raise ValueError(message)


def number(raw):
    require(re.fullmatch(UINT, raw) is not None and len(raw) <= 20, 'Canonical bounded unsigned integer required')
    return int(raw)


def selected_sequence(stdin):
    """Independent byte record selection, followed by sliced-window counting."""
    require(type(stdin) is bytes, 'Complete input bytes required')
    selected = False
    pieces = []
    for line in re.split(rb'\r\n|\r|\n', stdin):
        if not line:
            continue
        if line.startswith(b'>'):
            if selected:
                break
            selected = re.split(rb'[\t ]', line[1:], maxsplit=1)[0] == b'THREE'
        elif selected and not line.startswith(b';'):
            pieces.append(line.upper())
    result = b''.join(pieces)
    require(result and all(byte in b'ACGT' for byte in result), 'Nonempty ACGT selected record required')
    return result


def validate(stdin, stdout, stderr, exit_status, sidecar, expected_stdout):
    require(type(stdout) is bytes and type(expected_stdout) is bytes and len(stdout) <= STDOUT_LIMIT,
            'Complete bounded stdout bytes required')
    require(type(exit_status) is int and exit_status == 0, 'Normal zero exit required')
    require(type(stderr) is bytes and stderr == b'', 'Complete empty stderr required')
    require(stdout == expected_stdout, 'Unchanged bounded knucleotide stdout differs')
    sequence = selected_sequence(stdin)
    pairs = sidecar_maps(sidecar, sequence)
    require(all(pairs[width] for width in WIDTHS), 'This fixed bounded case requires seven nonempty maps')
    observed = [dict(width=width,entries=len(pairs[width]),
                     total_windows=sum(count for _,count in pairs[width])) for width in WIDTHS]
    return dict(case='knucleotide:arbitrary-widths',observation_contract_satisfied=True,
        observation_scope='post-main complete seven-map contents on the bounded arbitrary-widths input',
        complete_maps=observed,selected_sequence_bytes=len(sequence),dump_calls_source_bound=0,
        capacity_scope='not observed',backing_series_capacity_observed=False,
        backing_series_identity_observed=False,full_pointer_identity_observed=False,
        hash_bucket_capacities_observed=False,capacity_growth_trajectory_observed=False,
        native_process_verified=False,runtime_source_equivalence_proven=False,
        full_size_work_qualified=False,source_work_qualified=False,
        full_timing_qualified=False,chart_admission=False)


def independent_maps(sequence):
    result = {}
    digits = {65: 0, 67: 1, 71: 2, 84: 3}
    for width in WIDTHS:
        words = Counter(sequence[index:index + width] for index in range(max(0, len(sequence) - width + 1)))
        result[width] = {sum(digits[byte] * 4 ** (width - position - 1)
                              for position, byte in enumerate(word)): count
                         for word, count in words.items()}
    return result


def sidecar_maps(raw, sequence):
    require(type(raw) is bytes and 0 < len(raw) <= SIDECAR_LIMIT and raw.endswith(b'\n'), 'Complete bounded sidecar required')
    lines = raw[:-1].split(b'\n')
    require(lines[0] == b'rebol-knucleotide-map-observation-v1\t7\t' + str(len(sequence)).encode(), 'Exact map sidecar header required')
    expected = independent_maps(sequence)
    result = {}
    cursor = 1
    for width in WIDTHS:
        require(cursor < len(lines), 'Missing map header')
        fields = lines[cursor].split(b'\t')
        cursor += 1
        require(len(fields) == 4 and fields[:2] == [b'map', str(width).encode()], 'Ordered exact map header required')
        entries, total = map(number, fields[2:])
        require(entries == len(expected[width]) and total == max(0, len(sequence) - width + 1), 'Complete entry/window totals differ')
        pairs = []
        for _ in range(entries):
            require(cursor < len(lines), 'Missing map entry')
            fields = lines[cursor].split(b'\t')
            cursor += 1
            require(len(fields) == 4 and fields[:2] == [b'entry', str(width).encode()], 'Exact map entry required')
            key, count = map(number, fields[2:])
            require(0 <= key < 4 ** width and count > 0, 'Invalid map key/count')
            pairs.append((key, count))
        require(len(dict(pairs)) == entries and dict(pairs) == expected[width], 'Complete independent histogram differs')
        require(cursor < len(lines) and lines[cursor] == b'end\t' + str(width).encode(), 'Exact map end required')
        cursor += 1
        result[width] = pairs
    require(cursor == len(lines), 'Extra sidecar rows')
    return result

