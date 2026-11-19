"""Full-size application fixtures and independent output validators."""
import json
import math
from pathlib import Path
import struct
import zlib
from benchmark_suite import ROOT, file_digest

FASTA_N = 25_000_000
NBODY_STEPS = 50_000_000
REYMONT_SHA256 = '0eac0114a3dfe6e2ee1f345a0f79d653cb26c3bc9f0ed79238af4933422b7578'


def deflate_cases(corpus):
    corpus = Path(corpus)
    if corpus.stat().st_size != 6_627_202 or file_digest(corpus) != REYMONT_SHA256:
        raise ValueError('Deflate requires the complete pinned Reymont corpus')
    fixtures = ROOT / 'suite/applications'
    small = json.loads((fixtures/'deflate-compress-reference.json').read_text())['cases']
    cases = [{'name':x['name'], 'input':bytes(x['input']), 'prefix':bytes(x['prefix']), 'expected':bytes(x['expected'])} for x in small]
    for name in ('16384-distribution-change', '33027-periodic-window'):
        base = fixtures / ('deflate-boundary-'+name)
        cases.append({'name':name,'input':base.with_suffix('.input').read_bytes(),'prefix':b'','expected':base.with_suffix('.deflate').read_bytes()})
    cases.append({'name':'full-reymont','input':corpus.read_bytes(),'prefix':b'','expected':None})
    return cases


def validate_deflate(raw, plain, prefix, expected=None):
    if not raw.startswith(prefix):
        raise ValueError('compressed output changed the owned prefix')
    decoder = zlib.decompressobj(-15)
    restored = decoder.decompress(raw[len(prefix):]) + decoder.flush()
    if restored != plain or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('invalid, incomplete, or trailing DEFLATE stream')
    if expected is not None and raw != expected:
        raise ValueError('Mech/Roc level-12 stream differs from the pinned bytes')
    return {'input_bytes':len(plain),'output_bytes':len(raw),'prefix_bytes':len(prefix),
            'complete_input_consumption':True,'complete_stream':True,'prefix_preserved':True,
            'exact_reference':expected is not None}


def snapshot_u8(snapshot):
    prefix = b'mech-snapshot-v1\0'
    if not snapshot.startswith(prefix):
        raise ValueError('invalid snapshot header')
    at = len(prefix)+32
    if len(snapshot)<at+8:
        raise ValueError('truncated snapshot')
    shape_bytes, = struct.unpack_from('<Q',snapshot,at)
    at += 8+shape_bytes
    if len(snapshot)<at+8:
        raise ValueError('truncated snapshot shape')
    count, = struct.unpack_from('<Q',snapshot,at)
    raw = snapshot[at+8:]
    if len(raw)!=count:
        raise ValueError('snapshot length does not match its complete payload')
    return raw


def nbody_output(raw):
    lines = raw.decode('ascii').splitlines()
    if len(lines)!=2:
        raise ValueError('N-body must print initial and final energy, exactly two lines')
    values = [float(line) for line in lines]
    if not all(math.isfinite(n) for n in values):
        raise ValueError('non-finite N-body energy')
    return values


def validate_nbody(raw, expected):
    values = nbody_output(raw)
    if any(not math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-8) for a,b in zip(values,expected)):
        raise ValueError('N-body energy disagrees with the independent Java implementation')
    return {'kind':'matrix','shape':[1,2],'values':values}
