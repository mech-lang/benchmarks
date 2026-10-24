"""Account exact shipped Mach-O bytes and symbol-preserving identical code."""
from collections import defaultdict
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name(raw):
    return raw.split(b'\0', 1)[0].decode()


def macho(path):
    data = path.read_bytes()
    header = struct.unpack_from('<IiiIIIII', data)
    assert header[0] == 0xfeedfacf and header[1] == 0x100000c
    offset, segments, sections, symbols, starts = 32, [], [], None, None
    for _ in range(header[4]):
        command, size = struct.unpack_from('<II', data, offset)
        assert size >= 8
        if command == 0x19:
            row = struct.unpack_from('<II16sQQQQiiII', data, offset)
            segment = dict(name=name(row[2]), vm_address=row[3], vm_bytes=row[4],
                           file_offset=row[5], file_bytes=row[6])
            segments.append(segment)
            for index in range(row[9]):
                section = struct.unpack_from('<16s16sQQIIIIIIII', data, offset + 72 + index * 80)
                zero_fill = section[8] & 0xff in (1, 0xc, 0x12)
                sections.append(dict(section=name(section[0]), segment=name(section[1]),
                                     address=section[2], bytes=section[3], file_offset=section[4],
                                     zero_fill=zero_fill, ordinal=len(sections) + 1))
        elif command == 2:
            symbols = struct.unpack_from('<IIIIII', data, offset)[2:]
        elif command == 0x26:
            starts = struct.unpack_from('<IIII', data, offset)[2:]
        offset += size
    assert offset == 32 + header[5]
    assert all(s['file_offset'] + s['file_bytes'] <= len(data) for s in segments)
    text = next(s for s in sections if (s['segment'], s['section']) == ('__TEXT', '__text'))
    report = dict(path=str(path), file_bytes=len(data), sha256=sha(path), segments=segments,
                  sections=sections, machine_code_bytes=text['bytes'],
                  machine_code_sha256=hashlib.sha256(data[text['file_offset']:text['file_offset'] + text['bytes']]).hexdigest(),
                  disk_segment_bytes=sum(s['file_bytes'] for s in segments),
                  bytes_outside_segments=len(data) - sum(s['file_bytes'] for s in segments))
    return report, data, symbols, starts, text


def readable(symbol):
    raw = symbol[1:] if symbol.startswith('__ZN') else symbol
    if not raw.startswith('_ZN') or not raw.endswith('E'):
        return symbol.lstrip('_')
    cursor, parts = 3, []
    while cursor < len(raw) - 1:
        match = re.match(r'\d+', raw[cursor:])
        if not match:
            return symbol
        length = int(match[0])
        cursor += len(match[0])
        parts.append(raw[cursor:cursor + length])
        cursor += length
    if parts and re.fullmatch(r'h[0-9a-f]{16}', parts[-1]):
        parts.pop()
    return '::'.join(parts).replace('$LT$', '<').replace('$GT$', '>').replace('$u20$', ' ')


def function_ranges(path, include_all=False):
    report, data, symtab, function_starts, text = macho(path)
    assert function_starts and symtab
    symoff, count, stroff, strsize = symtab
    demangled = subprocess.check_output(['/usr/bin/nm', '-n', '--demangle', str(path)], text=True)
    pretty = defaultdict(list)
    for line in demangled.splitlines():
        match = re.match(r'^([0-9a-fA-F]+) [tT] (.*)$', line)
        if match:
            pretty[int(match[1], 16)].append(match[2])
    names = defaultdict(list)
    for index in range(count):
        string, kind, section, _, address = struct.unpack_from('<IBBHQ', data, symoff + index * 16)
        if kind & 0xe0 or kind & 0xe != 0xe or section != text['ordinal']:
            continue
        assert 0 <= string < strsize
        end = data.index(b'\0', stroff + string, stroff + strsize)
        names[address].append(readable(data[stroff + string:end].decode()))
    base = next(s['vm_address'] for s in report['segments'] if s['name'] == '__TEXT')
    cursor, end = function_starts[0], sum(function_starts)
    address, addresses = base, []
    while cursor < end:
        shift, delta = 0, 0
        while True:
            byte = data[cursor]
            cursor += 1
            delta |= (byte & 0x7f) << shift
            if byte < 128:
                break
            shift += 7
        if not delta:
            break
        address += delta
        assert text['address'] <= address < text['address'] + text['bytes']
        addresses.append(address)
    rows = []
    boundaries = addresses[1:] + [text['address'] + text['bytes']]
    for start, end in zip(addresses, boundaries):
        candidates = pretty.get(start, names.get(start, ['<unnamed>']))
        symbol = max(candidates, key=len)
        # Adjacent LC_FUNCTION_STARTS ranges include alignment padding and any
        # associated in-text data. They are static size estimates, not hotness.
        group = symbol.split('::', 1)[0]
        if symbol.lstrip('_').startswith(('mech_native_', 'mech_canonical_program_entry_v1')):
            group = 'generated Mech object'
        elif group.startswith('<'):
            match = re.search(r'([a-z_]+)::', symbol)
            group = match[1] if match else '<generic/unnamed>'
        rows.append(dict(address=start, bytes=end - start, symbol=symbol, group=group))
    groups = defaultdict(int)
    for row in rows:
        groups[row['group']] += row['bytes']
    assert sum(groups.values()) + addresses[0] - text['address'] == text['bytes']
    result = dict(profile_binary=str(path), profile_sha256=report['sha256'],
                machine_code_sha256=report['machine_code_sha256'],
                machine_code_bytes=text['bytes'], estimated_functions=len(rows),
                prefix_bytes=addresses[0] - text['address'],
                groups=sorted([dict(group=k, bytes=v) for k, v in groups.items()], key=lambda r: -r['bytes']),
                largest_functions=sorted(rows, key=lambda r: -r['bytes'])[:100],
                scope='LC_FUNCTION_STARTS adjacent extents include padding; names come from the exact-code symbol-preserving build. Static sizes do not establish executed cost. Generic group inference is heuristic.')
    result['demangler'] = '/usr/bin/nm -n --demangle'
    result['demangled_symbol_output_sha256'] = hashlib.sha256(demangled.encode()).hexdigest()
    if include_all:
        result['ranges'] = rows
    return result


def main():
    timing = json.loads((HERE / 'full-preparation-interactions-v1/results.json').read_text())
    subjects = {}
    for subject, pin in timing['pins'].items():
        path = HERE / '.build' / pin['binary'] if subject != 'rust' else HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
        parsed = macho(path)[0]
        assert parsed['sha256'] == pin['binary_sha256']
        if subject != 'rust':
            project = path.with_suffix('.project')
            parsed['build_components_not_additive_to_binary'] = {
                n: dict(bytes=(project / n).stat().st_size, sha256=sha(project / n))
                for n in ['program.o', 'program.mecb', 'native-descriptor.bin', 'native-resources.json']}
        subjects[subject] = parsed
    profile = function_ranges(HERE / '.build/counting-preparation-combined-profile')
    assert profile['machine_code_sha256'] == subjects['combined']['machine_code_sha256']
    rust_functions = function_ranges(Path(subjects['rust']['path']))
    out = HERE / 'preparation-interactions-binary-size-v1'
    out.mkdir(exist_ok=True)
    report = dict(status='exact-binary-file-and-machine-code-sizes-verified',
                  driver_sha256=sha(Path(__file__)), subjects=subjects,
                  combined_function_extents=profile, rust_function_extents=rust_functions,
                  benchmark_samples=0,
                  scope='Exact timed executable file bytes, Mach-O on-disk segments, sections and identical-code symbol attribution. __PAGEZERO and BSS are virtual zero-fill, not shipped bytes. Object/descriptor components are provenance and must not be added to executable bytes. No stripping or rebuild alters a timed binary.')
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({s: dict(file_bytes=r['file_bytes'], machine_code_bytes=r['machine_code_bytes']) for s, r in subjects.items()}, indent=2))
    print(json.dumps(profile['groups'][:20], indent=2))
    print(json.dumps(profile['largest_functions'][:15], indent=2))


if __name__ == '__main__':
    main()
