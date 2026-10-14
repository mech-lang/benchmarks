"""Canonical source-owner coverage for two reviewed Uiua fannkuch v5 sources.

This is an exact-source policy, not a general Uiua parser. Changed or unrelated
source bytes require their own semantic review. No source is executed, and no
producer LOC value is consulted. The caller binds the reviewed code, complete
authored bundle and native evidence before admitting the returned counts.
"""
import hashlib
import re

POLICY = 'uiua-fann-v5-exact-source-owners-v1'
HASHES = {
    'compact': '95f622e306aa23ce3678e6c5aba0dfec8f303bf31b294d78124c7e451ea65489',
    'fast': 'b3a2563f7d6503d03d2c0bbd7edae82f9743f137f7d47b3fa561970cfa0a4a0e',
}
COMPACT_OWNERS = (
    ('binding', 'N'), ('binding', 'Widths'), ('binding', 'Divisors'),
    ('binding', 'Total'), ('binding', 'Rotate'), ('binding', 'Permutation'),
    ('binding', 'FlipIndices'), ('record-declaration', 'FlipState'),
    ('binding', 'FlipStep'), ('binding', 'Flips'), ('record-declaration', 'F'),
    ('record-declaration', 'Ranks'), ('record-declaration', 'Block'),
    ('binding', 'BlockIndices'), ('binding', 'Ranked'), ('binding', 'Candidate'),
    ('binding', 'Work'), ('binding', 'Result'),
    ('output-statement', 'checksum'), ('output-statement', 'maximum'),
)
OWNERS = {
    'compact': COMPACT_OWNERS,
    'fast': COMPACT_OWNERS[:7] + (('binding', 'FlipPermutations'),) + COMPACT_OWNERS[7:],
}
RECORD_FIELDS = {
    'FlipState': ('Permutations', 'Counts'),
    'F': ('Index', 'End', 'Checksum', 'Maximum'),
    'Ranks': ('State', 'Indices'),
    'Block': ('State', 'Indices', 'Counts'),
}


def count_source(source, variant):
    if type(source) is not bytes or variant not in HASHES:
        raise ValueError('Exact registered source bytes and variant required')
    digest = hashlib.sha256(source).hexdigest()
    if digest != HASHES[variant]:
        raise ValueError('Source identity is outside the two-source owner review')
    text = source.decode('utf-8')
    lines = text.splitlines()
    expected = OWNERS[variant]
    if not text.endswith('\n') or len(lines) != len(expected):
        raise ValueError('Reviewed physical source coverage changed')
    owners = []
    for number, (line, (kind, name)) in enumerate(zip(lines, expected), 1):
        if kind == 'binding':
            if not re.fullmatch(re.escape(name) + r'\s+←\s+\S.*', line):
                raise ValueError('Reviewed binding owner changed')
        elif kind == 'record-declaration':
            if line != '~' + name + ' {' + ' '.join(RECORD_FIELDS[name]) + '}':
                raise ValueError('Reviewed record declaration changed')
        elif name == 'checksum':
            if line != '&p /+ ≡F.Checksum Result':
                raise ValueError('Reviewed checksum output changed')
        elif line != '&p $"Pfannkuchen(_) = _" N /↥ ≡F.Maximum Result':
            raise ValueError('Reviewed maximum output changed')
        owners.append(dict(line=number, kind=kind, name=name, canonical_units=1))
    return dict(schema='uiua-exact-source-unit-count-v1', policy=POLICY,
        variant=variant, source_sha256=digest, canonical_loc=len(owners),
        original_physical_loc=len(lines), formatted_loc=None,
        formatted_loc_qualified=False, source_owners=owners,
        independent_bindings=sum(x['kind'] == 'binding' for x in owners),
        record_declarations=sum(x['kind'] == 'record-declaration' for x in owners),
        output_statements=sum(x['kind'] == 'output-statement' for x in owners),
        unowned_noncomment_lines=[], packed_independent_owners=[],
        generic_language_certificate=False, native_execution=False,
        chart_admission=False)
