"""Authored synthetic dump/sidecar faults; no native observations supplied."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('rebol_map_contract', Path(__file__).with_name('map_contract.py'))
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

INPUT = b'>ONE\nIGNORE\n>THREE comment\nacgtACGTGGTATTTTAATTTATAGTACGT\n;ignored\nGGTACGT\n>FOUR\nINVALID\n'
EXPECTED = b'synthetic pinned output\n'


def header(address, wide, tail, rest, bias=0):
    return (f'Dump Series #{address:08X}: wide: {wide:2d} size: {(rest + bias) * wide:6d} '
            f'bias: {bias} tail: {tail} rest: {rest} flags: #00000000 "-"\n').encode()


def fixture():
    sequence = m.selected_sequence(INPUT)
    maps = m.independent_maps(sequence)
    sidecar = bytearray(f'rebol-knucleotide-map-observation-v1\t7\t{len(sequence)}\n'.encode())
    dump = bytearray()
    for index, width in enumerate(m.WIDTHS):
        pairs = sorted(maps[width].items())
        sidecar.extend(f'map\t{width}\t{len(pairs)}\t{sum(count for _, count in pairs)}\n'.encode())
        for key, count in pairs:
            sidecar.extend(f'entry\t{width}\t{key}\t{count}\n'.encode())
        sidecar.extend(f'end\t{width}\n'.encode())
        values = [value for pair in pairs for value in pair]
        dump.extend(header(0x1000 + index * 0x100, 32, len(values), len(values) + 9))
        dump.extend((''.join(f' {value}' for value in values) + '\n').encode())
    return bytes(dump), bytes(sidecar)


def byte_record(data, address=0x9000):
    # Include a native terminator in the payload. The declared tail omits it.
    raw = header(address, 1, len(data) - 1, len(data))
    for offset in range(0, min(len(data), 120 * 16), 16):
        part = data[offset:offset + 16]
        slots = [f'{byte:02X}' for byte in part] + ['  '] * (16 - len(part))
        hexes = ''.join(''.join(slots[start:start + 4]) + ' ' for start in (0, 4, 8, 12))
        ascii_part = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in part) + ' ' * (16 - len(part))
        raw += f'{0xA000 + offset:08X}: {hexes}{ascii_part}\n'.encode()
    return raw


class MapContract(unittest.TestCase):
    def check(self, dump=None, sidecar=None, **kwargs):
        original_dump, original_sidecar = fixture()
        values = dict(stdin=INPUT, stdout=EXPECTED, stderr=original_dump if dump is None else dump,
                      exit_status=0, sidecar=original_sidecar if sidecar is None else sidecar,
                      expected_stdout=EXPECTED)
        values.update(kwargs)
        return m.validate(**values)

    def test_exact_maps_and_final_capacity_keep_admission_separate(self):
        result = self.check()
        self.assertEqual([row['width'] for row in result['complete_maps']], list(m.WIDTHS))
        self.assertEqual(len({row['backing_series_displayed_address_low32'] for row in result['complete_maps']}), 7)
        for row in result['complete_maps']:
            self.assertEqual(row['backing_tail_values'], row['entries'] * 2)
            self.assertEqual(row['backing_allocation_bytes'], row['backing_rest_values'] * 32)
        for key in ('full_pointer_identity_observed', 'hash_bucket_capacities_observed', 'capacity_growth_trajectory_observed',
                    'native_process_verified', 'runtime_source_equivalence_proven', 'full_size_work_qualified',
                    'source_work_qualified', 'full_timing_qualified', 'chart_admission'):
            self.assertIs(result[key], False)

    def test_record_selection_is_byte_exact(self):
        value = b'>THREEISH\rBAD\r>THREE\tname\r\nacgt\n;skip\rGg\r>NEXT\nBAD'
        self.assertEqual(m.selected_sequence(value), b'ACGTGG')
        for bad in (b'>THREE\nACNT', b'>THREE\n', b'>THREEISH\nACGT'):
            with self.assertRaises(ValueError):
                m.selected_sequence(bad)

    def test_missing_extra_and_changed_sidecar_entries_reject(self):
        dump, sidecar = fixture()
        lines = sidecar.splitlines(keepends=True)
        entry = next(index for index, line in enumerate(lines) if line.startswith(b'entry\t'))
        fields = lines[entry].rstrip(b'\n').split(b'\t')
        changed = b'\t'.join(fields[:-1] + [str(int(fields[-1]) + 1).encode()]) + b'\n'
        for broken in (b''.join(lines[:entry] + lines[entry + 1:]),
                       b''.join(lines[:entry] + [changed] + lines[entry + 1:]),
                       sidecar + b'extra\n', sidecar[:-1]):
            with self.assertRaises(ValueError):
                self.check(dump, broken)

    def test_duplicate_sidecar_key_cannot_replace_another(self):
        _, sidecar = fixture()
        lines = sidecar.splitlines(keepends=True)
        entries = [index for index, line in enumerate(lines) if line.startswith(b'entry\t1\t')]
        lines[entries[1]] = lines[entries[0]]
        with self.assertRaises(ValueError):
            self.check(sidecar=b''.join(lines))

    def test_dump_order_must_match_actual_complete_iteration(self):
        dump, _ = fixture()
        lines = dump.splitlines(keepends=True)
        values = lines[1].strip().split(b' ')
        values[:4] = values[2:4] + values[:2]
        lines[1] = b' ' + b' '.join(values) + b'\n'
        with self.assertRaises(ValueError):
            self.check(dump=b''.join(lines))

    def test_ambiguous_equal_series_and_duplicate_address_reject(self):
        dump, _ = fixture()
        first = b'\n'.join(dump.split(b'\n')[:2]) + b'\n'
        for extra in (first, first.replace(b'#00001000', b'#00009000', 1)):
            with self.assertRaises(ValueError):
                self.check(dump=dump + extra)

    def test_missing_truncated_and_unrelated_stderr_reject(self):
        dump, _ = fixture()
        for broken in (b'', dump[:-1], dump.split(b'\n', 1)[0] + b'\n',
                       b'warning\n' + dump, dump + b'warning\n', dump + b'\n',
                       dump.replace(b'#00001000', b'#0000000000001000', 1)):
            with self.assertRaises(ValueError):
                self.check(dump=broken)

    def test_tail_and_allocation_dimensions_reject(self):
        dump, _ = fixture()
        lines = dump.splitlines(keepends=True)
        for broken in (lines[0].replace(b'size:    544', b'size:    545'),
                       lines[0].replace(b'tail: 8', b'tail: 7')):
            self.assertNotEqual(broken, lines[0])
            with self.assertRaises(ValueError):
                self.check(dump=broken + b''.join(lines[1:]))

    def test_unrelated_complete_value_lines_are_structurally_checked(self):
        dump, _ = fixture()
        opaque = header(0x9900, 32, 3, 4) + b' hello [nested values] .\n'
        self.assertEqual(self.check(dump=dump + opaque)['dump_records'], 8)
        self.assertEqual(m.VALUE_LINE_BYTES_PER_VALUE, 1 + 4 * (1024 + 3))
        unicode_payload = b' ' + '\U0001f600'.encode('utf-8') * 1024 + b'...\n'
        self.assertEqual(self.check(dump=dump + header(0x9900, 32, 1, 2) + unicode_payload)['dump_records'], 8)
        over_bound = b' ' + b'x' * m.VALUE_LINE_BYTES_PER_VALUE + b'\n'
        with self.assertRaises(ValueError):
            self.check(dump=dump + header(0x9900, 32, 1, 2) + over_bound)
        for payload in (b'warning\n', b' one\tvalue\n', b'\n'):
            with self.assertRaises(ValueError):
                self.check(dump=dump + header(0x9900, 32, 3, 4) + payload)

    def test_byte_payload_hex_ascii_padding_addresses_and_rows(self):
        dump, _ = fixture()
        byte_dump = byte_record(bytes(range(19)))
        self.assertEqual(self.check(dump=dump + byte_dump)['dump_records'], 8)
        wrapped = byte_dump.replace(b'0000A000:', b'FFFFFFF0:').replace(b'0000A010:', b'00000000:')
        self.assertEqual(self.check(dump=dump + wrapped)['dump_records'], 8)
        for broken in (byte_dump.replace(b'0000A010:', b'0000A011:'),
                       byte_dump.replace(b'0000A000:', b'000000000000A000:'),
                       byte_dump.replace(b'00010203', b'0G010203'),
                       byte_dump.replace(b'................', b'X...............'),
                       b'\n'.join(byte_dump.split(b'\n')[:-2]) + b'\n'):
            with self.assertRaises(ValueError):
                self.check(dump=dump + broken)

    def test_documented_byte_payload_row_cap_is_not_map_completeness(self):
        dump, _ = fixture()
        self.assertEqual(self.check(dump=dump + byte_record(b'x' * 2001))['dump_records'], 8)
        # Unrelated byte records can never substitute for a map REBVAL series.
        first_end = dump.find(b'\n', dump.find(b'\n') + 1) + 1
        with self.assertRaises(ValueError):
            self.check(dump=dump[first_end:] + byte_record(b'x' * 2001))

    def test_exact_streams_limits_status_and_canonical_numbers(self):
        for changes in ({'stdout': EXPECTED + b'\n'}, {'exit_status': 1}, {'exit_status': False},
                        {'stderr': b'x' * (m.STDERR_LIMIT + 1)},
                        {'sidecar': b'x' * (m.SIDECAR_LIMIT + 1)},
                        {'stdout': b'x' * (m.STDOUT_LIMIT + 1)}):
            with self.assertRaises(ValueError):
                self.check(**changes)
        _, sidecar = fixture()
        with self.assertRaises(ValueError):
            self.check(sidecar=sidecar.replace(b'entry\t1\t0\t', b'entry\t1\t00\t', 1))


if __name__ == '__main__':
    unittest.main()
