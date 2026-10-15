"""Synthetic selected-form comparisons; no actual images/tools are opened."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('relocation', Path(__file__).with_name('compare.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def image(name, installed=False):
    suffix = '/opt/'+name+'/lib/'+('libgmp.10.dylib' if name == 'gmp' else 'libpcre2-8.0.dylib')
    identity = (('/opt/homebrew' if installed else '@@HOMEBREW_PREFIX@@')+suffix).encode()+b'\0'
    identity_size = (24+len(identity)+7)//8*8
    identity_command = struct.pack('<6I',0xd,identity_size,24,0,0x10000,0x10000)+identity
    identity_command += b'\0'*(identity_size-len(identity_command))
    uuid = struct.pack('<II',0x1b,24)+bytes(range(16))
    signature = struct.pack('<4I',0x1d,16,4096,176)
    commands = identity_command+uuid+signature
    raw = bytearray(struct.pack('<8I',0xfeedfacf,0x0100000c,0,6,3,len(commands),0,0)+commands)
    raw += b'\0'*(512-len(raw))+b'\xa5'*(4096-512)
    cd = bytearray(struct.pack('>9I4B4I4Q',0xfade0c02,144,0x20400,2,112,88,0,1,4096,
        32,2,0,12,0,0,0,0,0,0,4096,1))
    cd += b'selected\0'+b'\0'*(112-len(cd)-9)
    cd += hashlib.sha256(raw).digest()
    raw += struct.pack('>5I',0xfade0cc0,164,1,0,20)+cd+b'\0'*12
    return bytes(raw)


def rehash_first_page(raw):
    raw = bytearray(raw)
    raw[4096+20+112:4096+20+144] = hashlib.sha256(raw[:4096]).digest()
    return bytes(raw)


class SelectedRelocation(unittest.TestCase):
    def test_exact_prefix_and_command_resize_preserve_body(self):
        for name in ('gmp','pcre2'):
            result = r.compare(image(name),image(name,True),name)
            self.assertTrue(result['installed_prefix_relocation_verified'])
            self.assertTrue(result['unchanged_image_body'])
            self.assertFalse(result['source_rebuild_equivalence_proven'])
            self.assertFalse(result['code_directory']['cryptographic_trust_or_signature_authority_verified'])

    def test_altered_executable_bytes_rejected_even_after_valid_resign(self):
        old=image('gmp');new=bytearray(image('gmp',True));new[1024]^=1
        with self.assertRaisesRegex(AssertionError,'Executable/data/linkedit'):
            r.compare(old,rehash_first_page(new),'gmp')

    def test_stale_page_hash_cannot_excuse_install_name_change(self):
        old=image('gmp');new=bytearray(image('gmp',True))
        new[4096+20+112:4096+20+144]=old[4096+20+112:4096+20+144]
        with self.assertRaisesRegex(AssertionError,'page hash'):
            r.compare(old,bytes(new),'gmp')

    def test_non_identity_load_command_change_rejected_with_valid_hash(self):
        old=image('pcre2');new=bytearray(image('pcre2',True))
        identity_size=struct.unpack_from('<I',new,36)[0]
        new[32+identity_size+8]^=1
        with self.assertRaisesRegex(AssertionError,'Non-identity load command'):
            r.compare(old,rehash_first_page(new),'pcre2')

    def test_signature_metadata_or_unrelated_prefix_is_not_exempt(self):
        old=image('gmp');new=bytearray(image('gmp',True));new[4096+20+88]^=1
        with self.assertRaisesRegex(AssertionError,'Signature changed outside'):
            r.compare(old,bytes(new),'gmp')
        new=bytearray(image('gmp',True));new[56:69]=b'/opt/otherxxx'
        with self.assertRaisesRegex(AssertionError,'installed-prefix'):
            r.compare(old,rehash_first_page(new),'gmp')


if __name__=='__main__':unittest.main()
