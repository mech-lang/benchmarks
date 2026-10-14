"""Independent supplemental expectations; no scored Kotlin code is imported."""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT/'archive/languages/c3/20261012/revisions/private-v1/references.py'
REFERENCE_SHA = '6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3'
PATTERNS = (
    'agggtaaa|tttaccct', '[cgt]gggtaaa|tttaccc[acg]',
    'a[act]ggtaaa|tttacc[agt]t', 'ag[act]gtaaa|tttac[agt]ct',
    'agg[act]taaa|ttta[agt]cct', 'aggg[acg]aaa|ttt[cgt]ccct',
    'agggt[cgt]aa|tt[acg]accct', 'agggta[cgt]a|t[acg]taccct',
    'agggtaa[cgt]|[acg]ttaccct',
)
# Explicit strings, not regular expressions: each group is disjoint and every
# member has length eight. The first group contains two words; each other
# group contains all three substitutions in each of its two alternatives.
WORDS = (
    ('agggtaaa', 'tttaccct'),
    ('cgggtaaa', 'ggggtaaa', 'tgggtaaa', 'tttaccca', 'tttacccc', 'tttacccg'),
    ('aaggtaaa', 'acggtaaa', 'atggtaaa', 'tttaccat', 'tttaccgt', 'tttacctt'),
    ('agagtaaa', 'agcgtaaa', 'agtgtaaa', 'tttacact', 'tttacgct', 'tttactct'),
    ('aggataaa', 'aggctaaa', 'aggttaaa', 'tttaacct', 'tttagcct', 'tttatcct'),
    ('agggaaaa', 'agggcaaa', 'aggggaaa', 'tttcccct', 'tttgccct', 'ttttccct'),
    ('agggtcaa', 'agggtgaa', 'agggttaa', 'ttaaccct', 'ttcaccct', 'ttgaccct'),
    ('agggtaca', 'agggtaga', 'agggtata', 'tataccct', 'tctaccct', 'tgtaccct'),
    ('agggtaac', 'agggtaag', 'agggtaat', 'attaccct', 'cttaccct', 'gttaccct'),
)


def legacy():
    raw = REFERENCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REFERENCE_SHA:
        raise AssertionError('Independent reference source changed')
    spec = importlib.util.spec_from_file_location('kotlin_specified_independent_reference', REFERENCE)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(REFERENCE), 'exec'), module.__dict__)
    return module


def literal_counts(sequence, *, overlapping=False):
    counts = []
    for words in WORDS:
        choices = {word.encode('ascii') for word in words}
        position, total = 0, 0
        while position + 8 <= len(sequence):
            matched = sequence[position:position+8] in choices
            total += matched
            position += 8 if matched and not overlapping else 1
        counts.append(total)
    return counts


def regex_expectation(fixture):
    """The new regex fixtures need no regular-expression engine.

    Headers and LF are removed by a line scanner. Payload bytes are restricted
    to ACGTacgtZ. Of the first three substitutions, only literal ``at`` can
    match: it becomes <2>, then | in pass four. Pass five consumes bar pairs
    with a nonempty intervening span; adjacent bars do not match.
    """
    payload = fixture['stdin_ascii'].encode('ascii')
    if not payload.endswith(b'\n'):
        raise AssertionError('Expected complete LF fixture')
    sequence = b''.join(line for line in payload.split(b'\n') if not line.startswith(b'>'))
    if not set(sequence) <= set(b'ACGTacgtZ'):
        raise AssertionError('Fixture would require a substitution oracle')
    counts = literal_counts(sequence)
    if counts != fixture['expected_counts']:
        raise AssertionError('Explicit independently reviewed regex counts differ')
    if literal_counts(sequence, overlapping=True) != fixture['overlapping_candidate_counts']:
        raise AssertionError('Explicit overlapping candidate counts differ')
    replaced = sequence.replace(b'at', b'|')
    output = bytearray(); position = 0
    while position < len(replaced):
        end = -1
        if replaced[position:position+1] == b'|' and position+1 < len(replaced) and replaced[position+1] != ord('|'):
            end = replaced.find(b'|', position+2)
        if end >= 0:
            output.append(ord('-')); position = end+1
        else:
            output.append(replaced[position]); position += 1
    result = ''.join(f'{pattern} {count}\n' for pattern, count in zip(PATTERNS, counts)).encode()
    return result + f'\n{len(payload)}\n{len(sequence)}\n{len(output)}\n'.encode()


def expected(fixture, references):
    benchmark = fixture['benchmark']
    payload = fixture.get('stdin_ascii')
    if benchmark == 'regexredux':
        result = regex_expectation(fixture)
        if result != references.regexredux(payload.encode('ascii')):
            raise AssertionError('Literal count oracle and retained regex oracle differ')
        return result
    return getattr(references, benchmark)(fixture['n'] if payload is None else payload.encode('ascii'))
