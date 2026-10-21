#!/usr/bin/env python3
"""Generate independent buffer-boundary fixtures; never execute OCaml subjects."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CORPUS = ROOT / 'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
WIDTHS = (1, 2, 3, 4, 6, 12, 18)
QUERIES = ('GGT', 'GGTA', 'GGTATT', 'GGTATTTTAATT', 'GGTATTTTAATTTATAGT')
ALU = (b'GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG'
       b'GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA'
       b'CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT'
       b'ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA'
       b'GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG'
       b'AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC'
       b'AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA')
IUB = list(zip(b'acgtBDHKMNRSVWY', (0.27, 0.12, 0.12, 0.27) + (0.02,) * 11))
HOMO = list(zip(b'acgt', (0.3029549426680, 0.1979883004921,
                           0.1975473066391, 0.3015094502008)))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def selected(raw):
    active = False
    sequence = bytearray()
    for line in re.split(br'\r\n|\r|\n', raw):
        if line.startswith(b';'):
            continue
        if active:
            if line.startswith(b'>'):
                break
            sequence.extend(line.upper())
        elif line == b'>THREE' or line.startswith((b'>THREE ', b'>THREE\t')):
            active = True
    if any(byte not in b'ACGT' for byte in sequence):
        raise ValueError('Fixture has unexpected DNA alphabet')
    return bytes(sequence)


def nucleotide(raw):
    """String slices and Counter are independent of OCaml's packed rolling keys."""
    sequence = selected(raw)
    outputs = []
    for width in WIDTHS:
        counts = Counter(sequence[i:i + width] for i in range(len(sequence) - width + 1))
        if width <= 2:
            total = sum(counts.values())
            rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            outputs.extend(key + f' {100.0 * count / total:.3f}\n'.encode()
                           for key, count in rows)
            outputs.append(b'\n')
        else:
            query = QUERIES[(3, 4, 6, 12, 18).index(width)].encode()
            outputs.append(str(counts[query]).encode() + b'\t' + query + b'\n')
    return b''.join(outputs)


def fasta(n):
    """Simple complete-output oracle with one ordered RNG draw per random base."""
    assert len(ALU) == 287
    output = bytearray(b'>ONE Homo sapiens alu\n')

    def rows(data):
        for start in range(0, len(data), 60):
            output.extend(data[start:start + 60] + b'\n')

    rows((ALU * ((2 * n + len(ALU) - 1) // len(ALU)))[:2 * n])
    state = 42
    for header, length, distribution in (
            (b'>TWO IUB ambiguity codes\n', 3 * n, IUB),
            (b'>THREE Homo sapiens frequency\n', 5 * n, HOMO)):
        output.extend(header)
        cumulative = []
        total = 0.0
        for byte, probability in distribution:
            total += probability
            cumulative.append((byte, total))
        data = bytearray()
        for _ in range(length):
            state = (state * 3877 + 29573) % 139968
            value = state / 139968.0
            data.append(next(byte for byte, threshold in cumulative if value < threshold))
        rows(data)
    return bytes(output)


def fixtures():
    def padding(length):
        return b';' + b'x' * (length - 2) + b'\n'

    raw = [(f'header-start-{offset}', padding(offset) + b'>THREE selected\r\nGGTATTACGT')
           for offset in (65532, 65535, 65536)]
    raw += [
        ('split-crlf', b';' + b'x' * 65534 + b'\r\n>THREE\r\nACGTGGTATT'),
        ('dna-two-chunks', b'>THREE\n' + b'ACGTTGCA' * 16385 + b'GGTATTTTAATTTATAGT'),
        ('comment-two-chunks', b'>THREE\nACGT\n;' + b'GGTATT' * 22000 + b'\r\nGGTATT'),
        ('stop-header-split', b'>THREE\n' + b'ACGT' * 16381 + b'ACG\n>FOUR decoy\nGGGG'),
        ('header-at-eof', padding(65535) + b'>THREE')]
    for name, data in raw:
        yield dict(benchmark='knucleotide', case=name, n=0, input_kind='stdin'), data, nucleotide(data)
    for n in (12287, 12288, 12289, 20479, 20480, 20481):
        yield dict(benchmark='fasta', case=f'n-{n}', n=n, input_kind='integer-argument'), b'', fasta(n)


def build(check):
    corpus_bytes = CORPUS.read_bytes()
    assert sha(corpus_bytes) == CORPUS_SHA
    corpus = json.loads(corpus_bytes)
    references = []
    for row in corpus['cases']:
        if row['benchmark'] not in ('fasta', 'knucleotide'):
            continue
        actual_input = (CORPUS.parent / row['stdin']['path']).read_bytes()
        expected = (CORPUS.parent / row['expected']['path']).read_bytes()
        assert sha(actual_input) == row['stdin']['sha256'] and sha(expected) == row['expected']['sha256']
        actual = fasta(row['n']) if row['benchmark'] == 'fasta' else nucleotide(actual_input)
        assert actual == expected, (row['benchmark'], row['case'])
        references.append(dict(benchmark=row['benchmark'], case=row['case'],
                               expected_sha256=sha(expected), complete_reference_match=True))
    assert len(references) == 30
    cases = []
    for row, data, expected in fixtures():
        row.update(validation='exact-complete-bytes', expected_exit=0)
        for name, raw in (('stdin.bin', data), ('expected.stdout', expected)):
            path = HERE / 'cases' / row['benchmark'] / row['case'] / name
            if check:
                assert path.read_bytes() == raw
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(raw)
            row['stdin' if name == 'stdin.bin' else 'expected'] = dict(
                path=str(path.relative_to(HERE)), bytes=len(raw), sha256=sha(raw))
        cases.append(row)
    assert len(cases) == 14
    return dict(schema='ocaml-independent-boundary-fixture-preparation.v1',
        status='reference-fixtures-prepared-subject-not-executed',
        generator_sha256=sha(Path(__file__).read_bytes()), corpus_sha256=CORPUS_SHA,
        original_data_license='../rolling-v1/LICENSE.benchmarksgame',
        reference_replay=references, case_count=len(cases), cases=cases,
        native_processes_started=0, subject_executions=0, benchmark_samples=0,
        subject_output_qualified=False, source_work_qualified=False, chart_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build(args.check)
    path = HERE / 'manifest.json'
    if args.check:
        assert json.loads(path.read_bytes()) == result
    else:
        with path.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status='checked' if args.check else 'prepared',
                          reference_replays=30, new_fixtures=14, subject_executions=0)))
