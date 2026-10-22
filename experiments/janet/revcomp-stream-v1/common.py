"""Pinned shared process owner and complete-byte reverse-complement reference."""
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('revcomp_owned',HERE.parent/'knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN_PATH=HERE.parent/'bounded-v1/plan-v1.json'
PLAN=json.loads(PLAN_PATH.read_bytes())
SOURCES={'parent':HERE.parent/'source-v3/revcomp.janet',**{name:HERE/'sources'/(name+'.janet') for name in ('line-reader','dense-chunk')}}
COMPLEMENTS=dict(zip(b'ACGTUMRWSYKVHDBN',b'TGCAAKYWSRMBDHVN'))

def records(raw):
    header=None;bases=bytearray()
    for line in raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n').split(b'\n'):
        if line.startswith(b'>'):
            if header is not None:yield header,bytes(bases)
            header=line;bases.clear()
        elif header is not None and not line.startswith(b';'):bases.extend(line.upper())
    if header is not None:yield header,bytes(bases)

def oracle(raw):
    output=bytearray();work=[]
    for header,bases in records(raw):
        output.extend(header+b'\n');row=bytearray()
        for offset in range(len(bases)-1,-1,-1):
            byte=bases[offset]
            if byte not in COMPLEMENTS:return bytes(output),(byte,offset),work
            row.append(COMPLEMENTS[byte])
            if len(row)==60:output.extend(row+b'\n');row.clear()
        if row:output.extend(row+b'\n')
        work.append((len(bases),len(bases)))
    return bytes(output),None,work

def validate(stdout,stderr,exit_status,raw,source):
    expected,error,work=oracle(raw)
    assert stdout==expected,'Complete stdout mismatch'
    if error is None:assert exit_status==0 and not stderr
    else:
        byte,offset=error
        assert exit_status==1
        prefix=f'error: Invalid IUPAC nucleotide byte {byte} at record offset {offset}\n'.encode()
        assert stderr.startswith(prefix)
        import re
        # Accept only this source's write-record/main and the pinned CLI frames.
        frames=stderr[len(prefix):].splitlines()
        assert frames and re.fullmatch(rb'  in write-record \['+re.escape(str(source).encode())+rb'\](?: \(tail call\))? on line [0-9]+, column [0-9]+',frames[0]),stderr
        for frame in frames[1:]:
            assert re.fullmatch(rb'  in (?:main \['+re.escape(str(source).encode())+rb'\]|run-main \[boot.janet\]|cli-main \[boot.janet\])(?: \(tail call\))? on line [0-9]+, column [0-9]+',frame),stderr
        assert frames[-2:]==[b'  in run-main [boot.janet] on line 4956, column 16',b'  in cli-main [boot.janet] on line 5190, column 17']
    return work
