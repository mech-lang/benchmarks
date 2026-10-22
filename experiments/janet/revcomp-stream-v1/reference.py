"""Independent full-input FASTA reference; not a benchmark subject."""
import sys

codes=b'ACGTUMRWSYKVHDBN'
table=bytes.maketrans(codes,b'TGCAAKYWSRMBDHVN')

def write(header,bases):
    if header is None:return
    assert not set(bases)-set(codes)
    result=bytes(bases).translate(table)[::-1]
    sys.stdout.buffer.write(header+b'\n')
    stride=60*16384
    for start in range(0,len(result),stride):
        block=result[start:start+stride]
        sys.stdout.buffer.write(b'\n'.join(block[i:i+60] for i in range(0,len(block),60))+b'\n')

header=None;bases=bytearray()
for raw in sys.stdin.buffer:
    line=raw.rstrip(b'\r\n')
    if line.startswith(b'>'):
        write(header,bases);header=line;bases.clear()
    elif header is not None and not line.startswith(b';'):bases.extend(line.upper())
write(header,bases)
