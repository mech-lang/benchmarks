"""Independent slice/count oracle; creates no Prolog process or timing sample."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

WIDTHS = (1, 2, 3, 4, 6, 12, 18)
QUERIES = (b'GGT', b'GGTA', b'GGTATT', b'GGTATTTTAATT', b'GGTATTTTAATTTATAGT')
RETAINED_CASES = ('ties-and-stop', 'one-base', 'empty', 'missing', 'crlf-comment-eof',
    'embedded-header-comment', 'arbitrary-widths', 'header-eof', 'empty-input',
    'exact-token-cr', 'exact-token-controls', 'tail')


class InvalidBase(ValueError):
    def __init__(self, code):
        self.code = code


def sequence(raw):
    selected = False
    parts = []
    for line in re.split(br'[\r\n]', raw):
        if not selected:
            if line == b'>THREE' or line.startswith((b'>THREE ', b'>THREE\t')):
                selected = True
        elif line.startswith(b'>'):
            break
        elif not line.startswith(b';'):
            parts.append(line)
    value = b''.join(parts)
    for code in value:
        if code not in b'ACGTacgt':
            raise InvalidBase(code)
    return value.upper()


def counts(raw):
    text = sequence(raw)
    return text, {width: Counter(text[i:i+width] for i in range(len(text)-width+1))
                  for width in WIDTHS}


def reference(raw):
    text, tables = counts(raw)
    output = []
    for width in WIDTHS[:2]:
        denominator = len(text)-width+1
        for word, count in sorted(tables[width].items(), key=lambda pair: (-pair[1], pair[0])):
            output.append(word.decode('ascii')+' '+format(100.0*count/denominator, '.3f')+'\n')
        output.append('\n')
    output.extend(str(tables[len(word)][word])+'\t'+word.decode('ascii')+'\n' for word in QUERIES)
    return ''.join(output).encode('ascii')


def complete_maps(raw):
    text, tables = counts(raw)
    def key(word):
        return int(''.join(format(b'ACGT'.index(code), '02b') for code in word), 2)
    return dict(length=len(text), sequence_is_atom=True, widths=list(WIDTHS),
        maps=[dict(width=width, windows=max(0, len(text)-width+1),
                   pairs=sorted([[key(word), count] for word,count in tables[width].items()]))
              for width in WIDTHS])


def additional_cases():
    # Dense repeats, every short word, long keys, case folding and parser tails.
    words = b''.join(bytes((a,b,c,d)) for a in b'ACGT' for b in b'ACGT'
                     for c in b'ACGT' for d in b'ACGT')
    rows = [('all-four-base-words', b'>THREE\n'+words+b'\n'),
            ('query-overlaps', b'>THREE\n'+b'GGTATTTTAATTTATAGT'*8+b'\n'),
            ('lowercase-long-line', b'>THREE detail\n'+(b'acgt'*1025)),
            ('homopolymer', b'>THREE\n'+b'T'*257+b'\n')]
    rows.extend(('length-'+str(n), b'>THREE\n'+(b'GGTATTTTAATTTATAGTACGT'*3)[:n]+b'\n')
                for n in (2,3,4,5,6,11,12,17,18,19))
    rows.extend(('invalid-'+str(code), b'>THREE\nACG'+bytes((code,))+b'T\n')
                for code in (32,9,33,78,255))
    return rows


def self_check():
    assert sequence(b'>THREEISH\nBAD\n>THREE\tinfo\r\naCgT\n;skip\n>FOUR\nN') == b'ACGT'
    assert reference(b'') == b'\n\n0\tGGT\n0\tGGTA\n0\tGGTATT\n0\tGGTATTTTAATT\n0\tGGTATTTTAATTTATAGT\n'
    assert reference(b'>THREE\nA').startswith(b'A 100.000\n\n\n0\tGGT\n')
    maps = complete_maps(b'>THREE\nAAAA')
    assert [m['windows'] for m in maps['maps']] == [4,3,2,1,0,0,0]
    assert maps['maps'][0]['pairs'] == [[0,4]]
    assert maps['maps'][3]['pairs'] == [[0,1]]


def manifest_rows(retained):
    """retained is the exact ordered list of already-pinned input/output bytes."""
    assert [name for name,_,_ in retained] == list(RETAINED_CASES)
    rows=[]
    for name, raw, expected in retained:
        assert reference(raw) == expected, 'Independent oracle differs from retained case: '+name
        rows.append((name,raw,expected))
    for name,raw in additional_cases():
        try: expected=reference(raw)
        except InvalidBase as error: expected=error.code
        rows.append((name,raw,expected))
    assert len(rows)==31 and len({name for name,_,_ in rows})==31
    return rows


def write(directory, retained, generator_sha256):
    self_check()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    cases=[]
    for name,raw,expected in manifest_rows(retained):
        entry=dict(id=name,stdin=name+'/stdin.bin',input_bytes=len(raw),
                   input_sha256=hashlib.sha256(raw).hexdigest())
        target=directory/name;target.mkdir();(target/'stdin.bin').write_bytes(raw)
        if type(expected) is int:
            entry.update(expected_status='invalid-acgt',expected_invalid_code=expected)
        else:
            (target/'expected.stdout').write_bytes(expected)
            entry.update(expected_status='success',stdout=name+'/expected.stdout',
                         output_bytes=len(expected),output_sha256=hashlib.sha256(expected).hexdigest())
        cases.append(entry)
    manifest=dict(schema='prolog-knucleotide-linear-fixtures-v1',generator_sha256=generator_sha256,
                  cases=cases,complete_map_cases=['empty','all-four-base-words','query-overlaps','lowercase-long-line'])
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
