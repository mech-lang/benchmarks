"""Independent direct-window reference and selected-record prefix derivation.

Uses ordinary Python bytes/Counter windows, independent of the candidate rolling
integer recurrence. This preparation never invokes an Elixir/OTP process.
"""
from collections import Counter
from pathlib import Path

WIDTHS=[1,2,3,4,6,12,18]
QUERIES=[b'GGT',b'GGTA',b'GGTATT',b'GGTATTTTAATT',b'GGTATTTTAATTTATAGT']


def prefix(path,length):
    if length<=0:raise ValueError('Positive DNA prefix length required')
    chunks=[];remaining=length;selected=False;header=None;start=None;end=None
    with Path(path).open('rb') as stream:
        while line:=stream.readline():
            position=stream.tell()-len(line)
            text=line.rstrip(b'\r\n')
            if text.startswith(b'>'):
                if selected:break
                selected=text[1:].replace(b'\t',b' ').split(b' ',1)[0]==b'THREE'
                if selected:header=text;start=position
            elif selected and text and not text.startswith(b';'):
                part=text[:remaining]
                if any(c not in b'ACGTacgt' for c in part):raise ValueError('Unsupported source nucleotide')
                chunks.append(part);remaining-=len(part);end=position+len(part)
                if remaining==0:break
    if remaining or header is None:raise ValueError('Shared input does not contain requested selected-record prefix')
    dna=b''.join(chunks)
    # Keep the exact original header/base bytes, reconstruct60-column lines and
    # terminate the partial final line. Prior records are deliberately excluded
    # from this diagnostic; full-size input parsing is not claimed measured here.
    raw=header+b'\n'+b'\n'.join(dna[i:i+60] for i in range(0,len(dna),60))+b'\n'
    return raw,dna.upper(),dict(selected_header=header.decode('ascii'),source_record_start_offset=start,
        source_prefix_end_offset=end,selected_dna_length=length,
        construction='THREE selected-record prefix only; exact shared base bytes/original header,60-column newline reconstruction; preceding records omitted.')


def reference(dna):
    output=[];summaries=[]
    for k in WIDTHS:
        counts=Counter(dna[i:i+k] for i in range(max(0,len(dna)-k+1)))
        summaries.append(dict(width=k,updates=sum(counts.values()),distinct=len(counts)))
        if k<=2:
            total=sum(counts.values())
            output.extend(key.decode('ascii')+' '+format(100.0*amount/total,'.3f')+'\n'
                for key,amount in sorted(counts.items(),key=lambda p:(-p[1],p[0])))
            output.append('\n')
        else:
            query=next(q for q in QUERIES if len(q)==k)
            output.append(str(counts[query])+'\t'+query.decode('ascii')+'\n')
    return ''.join(output).encode(),summaries
