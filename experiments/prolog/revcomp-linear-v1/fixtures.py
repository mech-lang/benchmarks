#!/usr/bin/env python3
"""Independent byte oracles for a future bounded Prolog conformance run.

This module neither invokes Prolog nor verifies the candidate. The reference
collects whole records and uses Python byte translation and slicing; it does
not reproduce the candidate's bounded-chunk parser or traversal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


SYMBOLS = b"ACBDGHKMNSRUTWVYacbdghkmnsrutwvy"
COMPLEMENTS = b"TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR"
TRANSLATION = bytes.maketrans(SYMBOLS, COMPLEMENTS)
CHUNK_SIZES = (1, 2, 3, 7, 59, 60, 61, 64, 127)


class InvalidNucleotide(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(f"Invalid IUPAC byte: {code}")


def reference(data):
    """Preserve headers; reverse each complete sequence and wrap at 60 bytes."""
    records = []
    for line in re.split(br"[\r\n]", data):
        if line.startswith(b">"):
            records.append((line, []))
        elif records and not line.startswith(b";"):
            records[-1][1].append(line)
    result = bytearray()
    for header, lines in records:
        reversed_sequence = b"".join(lines)[::-1]
        for code in reversed_sequence:
            if code not in SYMBOLS:
                raise InvalidNucleotide(code)
        complemented = reversed_sequence.translate(TRANSLATION)
        result.extend(header + b"\n")
        for start in range(0, len(complemented), 60):
            result.extend(complemented[start:start + 60] + b"\n")
    return bytes(result)


def sequence(length):
    motif = b"ACBDGHKMNSRUTWVYacbdghkmnsrutwvy"
    return (motif * ((length + len(motif) - 1) // len(motif)))[:length]


def cases():
    rows = [
        ("empty", b""),
        ("no-header", b"ignored!?\r\nACGT\n; comment\r"),
        ("header-eof", b">header without final newline"),
        ("header-lf", b">header\n"),
        ("empty-records", b">one\r>two\n>three\r\n>four"),
        ("all-iupac", b">iupac\n" + SYMBOLS + b"\n"),
        ("mixed-records", b"preamble\r;ignored\n>one details\rACGT\r\nN\n"
                          b">empty\n; skip ACGT\r>last\rttag"),
        ("binary-header", b">header\t\x00\x80\xff bytes\r\nAcGtN"),
        ("comments-and-blanks", b">r\n\n;>fake record\rAC\r\n\n;N!\nGT\n"),
        ("unequal-records", b">a\nA\n>b\nCCGG\n>c\n" + sequence(121)),
    ]
    for ending_name, ending in (("lf", b"\n"), ("cr", b"\r"), ("crlf", b"\r\n")):
        rows.append(("line-endings-" + ending_name,
                     ending.join((b">first", b"acgt", b";comment", b"N", b">second", b"uY"))))
    lengths = (0, 1, 2, 59, 60, 61, 63, 64, 65, 126, 127, 128, 129,
               255, 256, 257, 1023, 1024, 1025, 4095, 4096, 4097,
               65535, 65536, 65537, 131073)
    for length in lengths:
        rows.append((f"single-line-{length}", b">length\n" + sequence(length)))
    for width in (1, 7, 59, 60, 61, 127):
        dna = sequence(263)
        lines = [dna[start:start + width] for start in range(0, len(dna), width)]
        rows.append((f"wrapped-{width}", b">wrapped\r\n" + b"\r\n".join(lines)))
    rows.extend([
        ("long-header", b">" + b"header\t" * 12000 + b"\r\nAcGTN"),
        ("long-comment", b">r\nA\n;" + b"ignored!?" * 16000 + b"\r\nCGTN"),
        ("invalid-space", b">r\nAC GT\n"),
        ("invalid-tab", b">r\nAC\tGT\n"),
        ("invalid-nul", b">r\nAC\x00GT\n"),
        ("invalid-high-byte", b">r\nAC\xffGT\n"),
        ("inline-header-marker", b">r\nAC>GT\n"),
        ("inline-comment-marker", b">r\nAC;GT\n"),
        ("invalid-reverse-order", b">r\n!AC?\n"),
    ])
    assert len({name for name, _ in rows}) == len(rows)
    return rows


def self_check():
    # Handwritten vectors exercise the oracle before it supplies native tests.
    assert reference(b">example\nACGTN\n") == b">example\nNACGT\n"
    assert reference(b">iupac\nuYbD\n") == b">iupac\nHVRA\n"
    assert reference(b"ignored\r>one\rAC\r\n;comment\nGT\r>two") == b">one\nACGT\n>two\n"
    assert reference(b">wrap\n" + b"A" * 61) == b">wrap\n" + b"T" * 60 + b"\nT\n"
    assert reference(b";ignored\nACGT") == b""
    try:
        reference(b">r\n!AC?\n")
    except InvalidNucleotide as error:
        assert error.code == ord("?")
    else:
        raise AssertionError("Invalid sequence was accepted")


def write_fixtures(output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema="prolog-revcomp-linear-fixtures-v1",
                    status="oracle-data-only-native-execution-pending",
                    generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    diagnostic_chunk_sizes=list(CHUNK_SIZES), native_executions=0,
                    chart_admission=False, cases=[])
    for name, data in cases():
        directory = output / name
        directory.mkdir()
        (directory / "stdin.bin").write_bytes(data)
        row = dict(id=name, stdin=f"{name}/stdin.bin", input_bytes=len(data),
                   input_sha256=hashlib.sha256(data).hexdigest())
        try:
            expected = reference(data)
        except InvalidNucleotide as error:
            # Partial output before rejection is deliberately not specified.
            row.update(expected_status="invalid-iupac", expected_invalid_code=error.code)
        else:
            (directory / "expected.stdout").write_bytes(expected)
            row.update(expected_status="success", stdout=f"{name}/expected.stdout",
                       output_bytes=len(expected), output_sha256=hashlib.sha256(expected).hexdigest())
        manifest["cases"].append(row)
    with (output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    self_check()
    rows = cases()
    if args.output:
        write_fixtures(args.output)
    valid = rejected = 0
    for _, data in rows:
        try:
            reference(data)
            valid += 1
        except InvalidNucleotide:
            rejected += 1
    print(json.dumps(dict(oracle_self_checks="passed", cases=len(rows),
                         success_cases=valid, rejection_cases=rejected,
                         native_executions=0, output=str(args.output) if args.output else None)))


if __name__ == "__main__":
    main()
