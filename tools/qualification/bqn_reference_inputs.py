"""Replay exact independent BQN pilot corpora with Python Counter references."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'experiments/bqn/optimization-v1/reference-inputs'
WIDTHS=(1,2,3,4,6,12,18)
QUERIES=(b'GGT',b'GGTA',b'GGTATT',b'GGTATTTTAATT',b'GGTATTTTAATTTATAGT')


def reference(raw):
    selected=False
    dna=bytearray()
    for line in raw.splitlines():
        if line.startswith(b';'): continue
        if line.startswith(b'>'):
            if selected: break
            selected=line==b'>THREE' or line.startswith((b'>THREE ',b'>THREE\t'))
        elif selected: dna.extend(line.upper())
    dna=bytes(dna)
    counts={k:Counter(dna[i:i+k] for i in range(max(0,len(dna)-k+1))) for k in WIDTHS}
    lines=[]
    for k in (1,2):
        total=sum(counts[k].values())
        lines.extend(word.decode('ascii')+' '+format(n/total*100,'.3f') for word,n in sorted(counts[k].items(),key=lambda p:(-p[1],p[0])))
        lines.append('')
    lines.extend(str(counts[len(q)][q])+'\t'+q.decode('ascii') for q in QUERIES)
    return ('\n'.join(lines)+'\n').encode(),len(dna)


def main():
    packet=json.loads((HERE/'manifest.json').read_text())
    for row in packet['cases']:
        raw=gzip.decompress((HERE/row['input_gzip']).read_bytes())
        expected=(HERE/row['expected']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['input_sha256']
        assert hashlib.sha256(expected).hexdigest()==row['expected_sha256']
        actual,length=reference(raw)
        assert actual==expected and length==row['dna_length']
        print(json.dumps(dict(case=row['name'],status='PASS',dna_length=length)))

if __name__=='__main__':main()
