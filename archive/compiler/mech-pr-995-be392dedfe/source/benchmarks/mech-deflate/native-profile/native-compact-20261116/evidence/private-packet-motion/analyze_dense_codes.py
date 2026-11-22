"""Inspect the actual readonly cost table; no compression or speed claim."""
from hashlib import sha256
from pathlib import Path
import struct


def analyze(path):
    image = Path(path).read_bytes()
    assert struct.unpack_from('<II', image)[0] == 0xfeedfacf
    assert struct.unpack_from('<I', image, 12)[0] == 1
    sections, symbols, at = [], None, 32
    for _ in range(struct.unpack_from('<I', image, 16)[0]):
        kind, size = struct.unpack_from('<II', image, at)
        if kind == 0x19:
            for index in range(struct.unpack_from('<I', image, at + 64)[0]):
                pos = at + 72 + index * 80
                name, segment = struct.unpack_from('<16s16s', image, pos)
                address, extent, offset = struct.unpack_from('<QQI', image, pos + 32)
                sections.append((name.rstrip(b'\0'), segment.rstrip(b'\0'), address, extent, offset))
        elif kind == 2:
            symbols = struct.unpack_from('<IIII', image, at + 8)
        at += size
    assert symbols is not None
    symoff, count, stroff, strsize = symbols
    found = []
    for index in range(count):
        key, kind, section, _, value = struct.unpack_from('<IBBHQ', image, symoff + 16 * index)
        assert key < strsize
        end = image.index(b'\0', stroff + key, stroff + strsize)
        if image[stroff + key:end] == b'_mech_compact_cost_codes_0':
            assert kind == 0xe and section > 0
            name, segment, address, extent, offset = sections[section - 1]
            assert (name, segment) == (b'__const', b'__TEXT')
            begin = value - address
            assert 0 <= begin <= extent - 65536
            found.append(image[offset + begin:offset + begin + 65536])
    table, = found
    base = table[1:257]
    predicted = []
    for word in range(65536):
        upper = word > 256
        index = ((word - 1) & ((1 << 64) - 1)) >> (7 if upper else 0)
        predicted.append((base[index] if index < 256 else 0) + (14 if upper else 0))
    assert bytes(predicted) == table
    pages = [table[index:index + 256] for index in range(0, 65536, 256)]
    unique = list(dict.fromkeys(pages))
    alternatives = []
    for shift in range(4, 13):
        size = 1 << shift
        blocks = [table[index:index + size] for index in range(0, len(table), size)]
        dictionary = list(dict.fromkeys(blocks))
        directory_width = 1 if len(dictionary) <= 256 else 2
        alternatives.append({'page_shift':shift, 'unique_pages':len(dictionary),
                             'directory_bytes':len(blocks) * directory_width,
                             'page_bytes':len(dictionary) * size,
                             'total_bytes':len(blocks) * directory_width + len(dictionary) * size})
    return {'object_sha256':sha256(image).hexdigest(),
            'symbol':'_mech_compact_cost_codes_0', 'table_bytes':len(table),
            'table_sha256':sha256(table).hexdigest(), 'all_65536_values_exact':True,
            'base_bytes':len(base), 'high_shift':7, 'bias':14,
            'unique_256B_pages':len(unique),
            'two_level_data_bytes':len(unique) * 256 + 256 * 2,
            'page_alternatives':alternatives,
            'source_formula':'CodeKey::encode: upper = word > split; index = wrapping_sub(word,1) >> (upper ? high_shift : 0); output = defaulting_base[index] + (upper ? bias : 0).',
            'status':'Analytical proof only. No compressed compiler emission or runtime gain claimed.'}
