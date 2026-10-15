"""Narrow draft byte comparison for the two selected Homebrew Mach-O dylibs.

Not a signer, loader, general Mach-O parser or source-rebuild proof. Layout is
the retained LLVM22 include/llvm/BinaryFormat/MachO.h CS_* declarations. The
initial exact-byte-equality failure remains separate retained evidence.
"""
import hashlib
import struct


def require(value, message):
    if not value:
        raise AssertionError(message)


def load_commands(raw):
    header = struct.unpack_from('<8I', raw)
    require(header[0] == 0xfeedfacf and header[1] == 0x0100000c and header[3] == 6,
            'Only the selected thin arm64 dylibs are supported')
    count, size = header[4:6]
    require(0 < count <= 64 and 32 + size <= len(raw), 'Load command extent differs')
    at, commands = 32, []
    for _ in range(count):
        kind, length = struct.unpack_from('<II', raw, at)
        require(length >= 8 and length % 8 == 0 and at + length <= 32 + size,
                'Malformed selected load command')
        commands.append((kind, raw[at:at+length]))
        at += length
    require(at == 32 + size, 'Load command total differs')
    return header, commands, at


def id_name(command):
    require(len(command) >= 24, 'Truncated dylib identity')
    offset = struct.unpack_from('<I', command, 8)[0]
    require(offset == 24 and b'\0' in command[offset:], 'Unexpected identity layout')
    name, padding = command[offset:].split(b'\0', 1)
    require(not padding.strip(b'\0'), 'Unexpected identity padding')
    return name


def code_slot_zero(raw, signature):
    offset, extent = struct.unpack_from('<II', signature, 8)
    require(offset + extent == len(raw), 'Signature is not the unchanged image suffix')
    magic, length, count = struct.unpack_from('>III', raw, offset)
    require(magic == 0xfade0cc0 and 0 < count <= 16 and 12 + 8*count <= length <= extent,
            'Unsupported embedded signature layout')
    entries = [struct.unpack_from('>II', raw, offset + 12 + 8*i) for i in range(count)]
    selected = [position for kind, position in entries if kind == 0]
    require(len(selected) == 1, 'One primary CodeDirectory required')
    start = offset + selected[0]
    require(offset + 12 + 8*count <= start and start + 88 <= offset + length,
            'CodeDirectory outside signature')
    values = struct.unpack_from('>9I4BI', raw, start)
    cdmagic, cdlength, version, flags, hashes, identifier, special, slots, limit = values[:9]
    hashsize, hashtype, platform, page_exp, spare = values[9:]
    require(cdmagic == 0xfade0c02 and version >= 0x20400 and cdlength >= 88
            and start + cdlength <= offset + length and hashsize == 32 and hashtype == 2
            and page_exp == 12 and spare == 0 and limit == offset
            and slots == (limit + 4095)//4096 and 0 <= special <= 16
            and 88 + special*hashsize <= hashes and hashes + slots*hashsize <= cdlength,
            'Unsupported selected CodeDirectory hashing policy')
    scatter = struct.unpack_from('>I', raw, start + 44)[0]
    spare3, limit64 = struct.unpack_from('>IQ', raw, start + 52)
    require(scatter == spare3 == limit64 == 0, 'Scatter or extended code extent unsupported')
    for slot in range(slots):
        expected = raw[start+hashes+slot*32:start+hashes+(slot+1)*32]
        actual = hashlib.sha256(raw[slot*4096:min((slot+1)*4096,limit)]).digest()
        require(actual == expected, 'CodeDirectory page hash differs')
    return start + hashes, dict(signature_offset=offset, signature_bytes=extent,
        code_directory_offset=start, code_directory_version=version, flags=flags,
        hash_type='SHA256', page_bytes=4096, code_pages=slots, special_slots=special,
        cryptographic_trust_or_signature_authority_verified=False)


def compare(original, installed, name):
    require(name in ('gmp', 'pcre2') and len(original) == len(installed), 'Unexpected selected library or size')
    old_header, old, old_end = load_commands(original)
    new_header, new, new_end = load_commands(installed)
    require(old_header[:5] == new_header[:5] and old_header[6:] == new_header[6:],
            'Mach-O header changed beyond command byte count')
    require(len(old) == len(new) and [x[0] for x in old] == [x[0] for x in new], 'Load command sequence differs')
    require(sum(kind == 0xd for kind, raw in old) == 1, 'One dylib identity required')
    require(sum(kind == 0x1d for kind, raw in old) == 1, 'One code signature required')
    path = b'/opt/'+name.encode()+b'/lib/'+(b'libgmp.10.dylib' if name == 'gmp' else b'libpcre2-8.0.dylib')
    for (kind, a), (_, b) in zip(old, new):
        if kind == 0xd:
            require(a[8:24] == b[8:24] and id_name(a) == b'@@HOMEBREW_PREFIX@@'+path
                    and id_name(b) == b'/opt/homebrew'+path,
                    'Change is not the exact installed-prefix identity replacement')
        else:
            require(a == b, 'Non-identity load command changed')
    boundary = max(old_end, new_end)
    require(not original[old_end:boundary].strip(b'\0') and not installed[new_end:boundary].strip(b'\0'),
            'Command resize altered nonzero header padding')
    sig = next(raw for kind, raw in old if kind == 0x1d)
    slot_old, old_sig = code_slot_zero(original, sig)
    slot_new, new_sig = code_slot_zero(installed, sig)
    require(slot_old == slot_new and old_sig == new_sig, 'Signature layout changed')
    offset = old_sig['signature_offset']
    require(original[boundary:offset] == installed[boundary:offset], 'Executable/data/linkedit bytes changed')
    require(original[offset:slot_old] == installed[offset:slot_new]
            and original[slot_old+32:] == installed[slot_new+32:],
            'Signature changed outside the independently verified first-page hash')
    return dict(library=name, installed_prefix_relocation_verified=True,
        unchanged_non_identity_load_commands=True, unchanged_image_body=True,
        changed_signature_field='Primary CodeDirectory first code-page SHA256 only',
        code_directory=old_sig, original_sha256=hashlib.sha256(original).hexdigest(),
        installed_sha256=hashlib.sha256(installed).hexdigest(),
        source_rebuild_equivalence_proven=False, native_execution=False)
