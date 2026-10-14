"""Source-owner coverage for nine exact retained GNU APL implementations.

Each independent statement/header and every written function closer counts.
Labels belong to their statement, and header-local names are declaration syntax.
This exact-source review never admits an unknown source by counting its lines.
"""
import hashlib

POLICY = 'apl-retained-nine-source-owners-with-closers-v1'
# identity: (complete source SHA-256, canonical units, written function closers)
SOURCES = {
    'nbody-canonical-v2': ('f457238f6be864126d9ea967de7ce283056f48e8afb2917ac7643b1781f1726d',32,2),
    'mandelbrot-original': ('ce26bde246eea5020d33f80f3168f712a0ddc74594ad00f98b3b0c6014d18eeb',34,1),
    'mandelbrot-compact-v2': ('5c25c451aa2d8f6cad0e18e77a40d05d9bb47e816eeb55ebee9d865626c41a43',36,1),
    'mandelbrot-optimized-v2': ('74dc3d19f12a83b1c14f0c2f83f5edb343147cdcb9a312d020d679084be9cfaa',38,1),
    'knucleotide-compact-v2': ('45c747027626fe1497e45fff4238476600c8025c7c11f823bce0895a06b28af6',185,12),
    'knucleotide-optimized-v2': ('6c7a7f1b24930901f2ebe0adc6845c07320c5075cdb4608d459238b5dc57cffa',205,12),
    'fannkuchredux': ('e40e4b49c7f892f3a3c497a05124b07d825cf1d65906fb28b0dc3047eb11de7f',38,1),
    'fasta-compact': ('d41ae162630187a26ee6f1ca2a89e9e83e8cfe0130d5aa3d7eafc5351337b21f',41,3),
    'fasta-optimized-v3': ('48002bf2a99dea328634775e7b26fcb2c57be38aa596e01675c671181548d43b',60,5),
}


def code_without_literals_or_comment(line):
    """Preserve positions while ignoring quoted syntax and doubled APL quotes."""
    result, quoted, index = [], False, 0
    while index < len(line):
        char = line[index]
        if char == "'":
            if quoted and index+1 < len(line) and line[index+1] == "'":
                result.extend('  '); index += 2; continue
            quoted = not quoted
            result.append(' ')
        elif char == '⍝' and not quoted:
            break
        else:
            result.append(' ' if quoted else char)
        index += 1
    if quoted:
        raise ValueError('Reviewed source contains an unfinished quoted value')
    return ''.join(result)


def count_source(source, identity):
    if type(source) is not bytes or identity not in SOURCES:
        raise ValueError('Registered source bytes and identity required')
    expected, expected_units, expected_closers = SOURCES[identity]
    digest = hashlib.sha256(source).hexdigest()
    if digest != expected:
        raise ValueError('Source is outside the nine exact reviewed identities')
    text = source.decode('utf-8')
    if not text.endswith('\n'):
        raise ValueError('Complete reviewed source must end in a newline')
    owners, excluded, current, pairs = [], [], None, []
    for number, line in enumerate(text.splitlines(),1):
        code = code_without_literals_or_comment(line).strip()
        if not code:
            # None of these exact files has a standalone string-expression row.
            if line.strip() and not line.lstrip().startswith('⍝'):
                raise ValueError('Unowned literal-only source row')
            excluded.append(dict(line=number, reason='comment' if line.strip() else 'blank'))
            continue
        if '⋄' in code or code.count('←') > 1:
            raise ValueError('Packed independent statements require another owner review')
        if code == '∇':
            if current is None:
                raise ValueError('Unmatched written function closer')
            kind = 'function-close'
            pairs.append(dict(header_line=current, close_line=number))
            current = None
        elif code.startswith('∇'):
            if current is not None:
                raise ValueError('Nested function header outside reviewed policy')
            kind, current = 'function-header', number
        else:
            kind = 'statement'
        owners.append(dict(line=number, kind=kind, canonical_units=1, source_text=line))
    if current is not None or len(owners) != expected_units or len(pairs) != expected_closers:
        raise ValueError('Reviewed owner or closer coverage changed')
    return dict(schema='apl-exact-source-unit-count-v1',policy=POLICY,identity=identity,
        source_sha256=digest,canonical_loc=len(owners),original_physical_loc=len(owners),
        formatted_loc=None,formatted_loc_qualified=False,source_owners=owners,
        excluded_rows=excluded,function_pairs=pairs,function_headers=len(pairs),written_function_closers=len(pairs),
        independent_statement_rows=len(owners)-2*len(pairs),unowned_noncomment_lines=[],
        packed_independent_owners=[],generic_language_certificate=False,native_execution=False,chart_admission=False)
