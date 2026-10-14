"""Exact source-owner counts for retained Uiua n-body and binary trees.

The three reviewed byte identities have one complete owner on each line.
Changed sources require a new review; this is not a general Uiua parser.
No benchmark, runtime, old source-count approval or timing record is changed.
"""
import hashlib
import re

POLICY = 'uiua-retained-three-source-owners-v1'
HASHES = {
    'nbody-compact': '76919fb2df86a83d659a8996a04455a2a451ab40bdf516e97bf9da414ca6689f',
    'nbody-fast': '62c676844b0e65f13a8229c283cadf926effa83ac51694ce3c726873371e3ec8',
    'binarytrees': '1fa04992eb6cc1d917b30a96af486f03b4de266fb169b88e7ae8602e85fd3887',
}
NBODY_BINDINGS = ('N', 'Solar', 'Masses', 'Positions', 'Velocities', 'Initial',
    'Pos', 'Vel', 'Differences', 'Norm', 'Diagonal', 'Upper', 'Acceleration',
    'NewVelocity', 'Advance', 'Potential', 'Energy', 'Fixed', 'Print')
TREE_OWNERS = (
    ('binding', 'N'), ('record-declaration', 'Tree'), ('binding', 'Leaf'),
    ('binding', 'Build'), ('binding', 'Check'), ('binding', 'TreeAt'),
    ('output-statement', 'stretch'), ('binding', 'Long'), ('binding', 'Depths'),
    ('binding', 'Iteration'), ('binding', 'Iterations'), ('binding', 'SumChecks'),
    ('binding', 'Batch'), ('output-statement', 'batches'), ('output-statement', 'long-lived'),
)
OUTPUTS = {
    'initial-energy': 'Print Initial',
    'final-energy': 'Print ⍥Advance N Initial',
    'stretch': '&p $"stretch tree of depth _\\t check: _" ⟜(Check TreeAt) +1N',
    'batches': '≡Batch Depths',
    'long-lived': '&p $"long lived tree of depth _\\t check: _" N Check Long',
}


def count_source(source, identity):
    if type(source) is not bytes or identity not in HASHES:
        raise ValueError('Registered source bytes and identity required')
    digest = hashlib.sha256(source).hexdigest()
    if digest != HASHES[identity]:
        raise ValueError('Source is outside the three exact reviewed identities')
    text = source.decode('utf-8')
    lines = text.splitlines()
    expected = (TREE_OWNERS if identity == 'binarytrees' else
        tuple(('binding', name) for name in NBODY_BINDINGS) +
        (('output-statement', 'initial-energy'), ('output-statement', 'final-energy')))
    if not text.endswith('\n') or len(lines) != len(expected):
        raise ValueError('Complete reviewed source coverage changed')
    owners = []
    for number, (line, (kind, name)) in enumerate(zip(lines, expected), 1):
        if kind == 'binding':
            valid = re.fullmatch(re.escape(name) + r'\s+←\s+\S.*', line)
        elif kind == 'record-declaration':
            valid = line == '~Tree {Id Left Right}'
        else:
            valid = line == OUTPUTS[name]
        if not valid:
            raise ValueError('Reviewed owner changed on line '+str(number))
        owners.append(dict(line=number, kind=kind, name=name, canonical_units=1))
    return dict(schema='uiua-exact-source-unit-count-v1', policy=POLICY,
        identity=identity, source_sha256=digest, canonical_loc=len(owners),
        original_physical_loc=len(lines), formatted_loc=None, formatted_loc_qualified=False,
        source_owners=owners, independent_bindings=sum(v['kind']=='binding' for v in owners),
        record_declarations=sum(v['kind']=='record-declaration' for v in owners),
        output_statements=sum(v['kind']=='output-statement' for v in owners),
        unowned_noncomment_lines=[], packed_independent_owners=[],
        generic_language_certificate=False, native_execution=False, chart_admission=False)
