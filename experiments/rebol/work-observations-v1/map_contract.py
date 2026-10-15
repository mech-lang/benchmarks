"""Pure bounded map/dump contract; no process or filesystem operations.

The caller pins the exact retained input, expected stdout, unchanged main,
runtime and diagnostic, then independently checks ownership and all artifacts.
The full raw stderr is required. No prefix/suffix stripping is permitted.
"""
from collections import Counter
import re

WIDTHS = (1, 2, 3, 4, 6, 12, 18)
CORPUS_CASE = ('knucleotide', 'arbitrary-widths')
CORPUS_SHA256 = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
STDIN_SHA256 = '337727c8c84e917740d053e1ce95eafdda30069d1669574df9c08b6c38247a1d'
EXPECTED_STDOUT_SHA256 = '78e220a584e4ea619d9ca9b6feff7354cd4950c018b840ffd5f74287117dd930'
STDERR_LIMIT = 16 * 1024 * 1024
SIDECAR_LIMIT = STDOUT_LIMIT = 1024 * 1024
# Retained 64-bit b-init.c:106-110 asserts sizeof(REBVAL) == 32.
# RXIARG's 16-byte extension ABI is a different structure.
VALUE_WIDTH = 32
# Debug_Values emits one separating space per value. Mold_Print_Value truncates
# at 1024 characters, then may append three dots (s-mold.c:1704-1707).
# Four UTF-8 bytes per character is a conservative bound, including the suffix.
VALUE_LINE_BYTES_PER_VALUE = 1 + 4 * (1024 + 3)
UINT = rb'(?:0|[1-9][0-9]*)'
HEADER = re.compile(
    rb'Dump Series #([0-9A-F]{8}): wide: +(' + UINT + rb') size: +(' + UINT +
    rb') bias: (' + UINT + rb') tail: (' + UINT + rb') rest: (' + UINT +
    rb') flags: #([0-9A-F]{8}) "([^"\x00-\x1f]*)"')
INTEGER_VALUES = re.compile(rb'(?: ' + UINT + rb')+')
BYTE_ROW = re.compile(rb'([0-9A-F]{8}): (.{36})(.{16})')


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


def byte_payload(lines, cursor, size):
    """Check every emitted row, including hex/ASCII identity and padding.

    Dump_Bytes intentionally emits at most 120 rows of unrelated byte series.
    This is its complete declared format, not capture truncation. Such records
    never establish complete map contents or map capacity.
    """
    address = None
    for row in range(min((size + 15) // 16, 120)):
        require(cursor < len(lines), 'Missing byte-dump payload')
        match = BYTE_ROW.fullmatch(lines[cursor])
        cursor += 1
        require(match is not None, 'Malformed byte-dump row')
        current = int(match[1], 16)
        require(address is None or current == (address + 16) % (1 << 32), 'Byte-dump displayed addresses are not contiguous')
        address = current
        hex_part, ascii_part = match[2], match[3]
        require(all(hex_part[index] == 32 for index in (8, 17, 26, 35)), 'Byte-dump group separators differ')
        packed = b''.join(hex_part[start:start + 8] for start in (0, 9, 18, 27))
        length = min(16, size - row * 16)
        actual_hex, padding = packed[:length * 2], packed[length * 2:]
        require(re.fullmatch(rb'[0-9A-F]*', actual_hex) is not None and padding == b' ' * len(padding), 'Byte-dump hex/padding differs')
        data = bytes.fromhex(actual_hex.decode('ascii'))
        projected = bytes(byte if 32 <= byte <= 126 else 46 for byte in data) + b' ' * (16 - length)
        require(ascii_part == projected, 'Byte-dump ASCII projection differs')
    return cursor


def dump_records(raw):
    require(type(raw) is bytes and 0 < len(raw) <= STDERR_LIMIT and raw.endswith(b'\n'), 'Complete bounded stderr dump required')
    lines = raw[:-1].split(b'\n')
    records = []
    addresses = set()
    cursor = 0
    while cursor < len(lines):
        match = HEADER.fullmatch(lines[cursor])
        cursor += 1
        require(match is not None, 'Unexpected stderr outside a complete series record')
        address = int(match[1], 16)
        wide, size, bias, tail, rest = map(number, match.group(2, 3, 4, 5, 6))
        require(address not in addresses, 'Ambiguous repeated displayed series address')
        addresses.add(address)
        require(wide > 0 and size == (rest + bias) * wide and rest >= tail, 'Series allocation dimensions disagree')
        record = dict(address=address, wide=wide, size=size, bias=bias, tail=tail, rest=rest,
                      flags=int(match[7], 16), label=match[8].decode('ascii'), integer_values=None)
        if wide == VALUE_WIDTH:
            require(cursor < len(lines), 'Missing complete value-series line')
            values = lines[cursor]
            cursor += 1
            # Debug_Values removes controls and emits exactly one whole line.
            # Unrelated molded values are opaque; only a full integer line is
            # eligible for exact map identity. No arbitrary extra lines pass.
            require((values == b'' if tail == 0 else values.startswith(b' ')) and
                    all(byte >= 32 for byte in values) and len(values) <= tail * VALUE_LINE_BYTES_PER_VALUE,
                    'Malformed complete value-series line')
            if INTEGER_VALUES.fullmatch(values):
                integers = [number(value) for value in values[1:].split(b' ')]
                require(len(integers) == tail, 'Integer-series tail differs from complete printed values')
                record['integer_values'] = integers
        else:
            cursor = byte_payload(lines, cursor, (tail + 1) * wide)
        records.append(record)
    require(records, 'Empty dump inventory')
    return records


def validate(stdin, stdout, stderr, exit_status, sidecar, expected_stdout):
    require(type(stdout) is bytes and type(expected_stdout) is bytes and len(stdout) <= STDOUT_LIMIT,
            'Complete bounded stdout bytes required')
    require(type(exit_status) is int and exit_status == 0, 'Normal zero exit required')
    require(stdout == expected_stdout, 'Unchanged bounded knucleotide stdout differs')
    sequence = selected_sequence(stdin)
    pairs = sidecar_maps(sidecar, sequence)
    records = dump_records(stderr)
    observed = []
    matched = set()
    for width in WIDTHS:
        flat = [value for pair in pairs[width] for value in pair]
        require(flat, 'This fixed capacity witness requires nonempty maps at every width')
        candidates = [record for record in records if record['wide'] == VALUE_WIDTH and
                      record['tail'] == len(flat) and record['integer_values'] == flat]
        require(len(candidates) == 1, 'Map integer sequence lacks a unique complete backing-series match')
        record = candidates[0]
        require(record['address'] not in matched and record['rest'] >= record['tail'] + 1,
                'Map identities overlap or lack a terminator slot')
        matched.add(record['address'])
        observed.append(dict(width=width, entries=len(pairs[width]), total_windows=sum(count for _, count in pairs[width]),
                             backing_series_displayed_address_low32=record['address'], value_width_bytes=record['wide'],
                             backing_tail_values=record['tail'], backing_rest_values=record['rest'],
                             backing_bias_values=record['bias'], backing_allocation_bytes=record['size']))
    return dict(case='knucleotide:arbitrary-widths', observation_contract_satisfied=True,
                complete_maps=observed, dump_records=len(records), selected_sequence_bytes=len(sequence),
                dump_calls_source_bound=1, capacity_scope='final map backing-series storage only',
                full_pointer_identity_observed=False,
                hash_bucket_capacities_observed=False, capacity_growth_trajectory_observed=False,
                native_process_verified=False, runtime_source_equivalence_proven=False,
                full_size_work_qualified=False, source_work_qualified=False,
                full_timing_qualified=False, chart_admission=False)
