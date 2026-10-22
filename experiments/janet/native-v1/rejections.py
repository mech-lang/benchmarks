"""Independent byte oracle and explicit Janet invalid-IUPAC diagnostic contract."""
import re

COMPLEMENT=dict(zip(b'ACGTUMRWSYKVHDBN',b'TGCAAKYWSRMBDHVN'))

def oracle(raw):
    records=[]; header=None; bases=bytearray()
    for line in raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n').split(b'\n'):
        if line.startswith(b'>'):
            if header is not None: records.append((header,bytes(bases)))
            header=line; bases.clear()
        elif header is not None and not line.startswith(b';'):
            bases.extend(line.upper())
    if header is not None: records.append((header,bytes(bases)))
    output=bytearray()
    for header,bases in records:
        output.extend(header+b'\n'); row=bytearray()
        for offset in range(len(bases)-1,-1,-1):
            byte=bases[offset]
            if byte not in COMPLEMENT:
                return bytes(output),byte,offset
            row.append(COMPLEMENT[byte])
            if len(row)==60: output.extend(row+b'\n');row.clear()
        if row: output.extend(row+b'\n')
    raise ValueError('No invalid IUPAC byte')

def validate(case,raw,stdout,stderr,exit_status,source):
    expected,byte,offset=oracle(raw)
    assert byte==case['expected_invalid_byte'], 'Independent invalid-byte pin differs'
    assert exit_status==1 and stdout==expected
    diagnostic=f'error: Invalid IUPAC nucleotide byte {byte} at record offset {offset}\n'.encode()
    stack=(rb'  in write-record \['+re.escape(str(source).encode())+
           rb'\] \(tail call\) on line [0-9]+, column [0-9]+\n'
           rb'  in run-main \[boot.janet\] on line 4956, column 16\n'
           rb'  in cli-main \[boot.janet\] on line 5190, column 17\n')
    assert stderr.startswith(diagnostic) and re.fullmatch(stack,stderr[len(diagnostic):]), 'Unrelated, incomplete or mismatched diagnostic'
    return dict(case=case['case'],expected_invalid_byte=byte,record_offset=offset,
                partial_stdout_bytes=len(stdout),janet_rejection_contract_pass=True)
