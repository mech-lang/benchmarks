"""Exact source set, unchanged shared owner and an independent integer reference."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('pi_owned',HERE.parent/'knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
SOURCES={'parent':HERE.parent/'source-v2/pidigits.janet',**{name:HERE/'sources'/(name+'.janet') for name in ('unsigned-digit','fused','fused-combine','combined')}}
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success

# Python integers are independently implemented arbitrary precision, not GMP.
def reference(n,trace=False):
    q,r,t,k,printed=1,0,1,0,0;digits=[];events=[];tests=0;removed=0
    def state(tag):events.append(f'{tag} {k} {printed} {q} {r} {t}\n')
    while printed<n:
        k+=1
        old_q=q;q=q*k;r=(r+2*old_q)*(2*k+1);t=t*(2*k+1)
        if trace:state('A')
        if r>q:
            a=(3*q+r)//t;b=(4*q+r)//t;tests+=1
            if trace:events.append(f'E {k} {a} {b}\n')
            if a==b:
                assert 0<=a<=9
                if trace:events.append(f'D {printed+1} {k} {a}\n')
                digits.append(str(a));printed+=1
                if printed<n:
                    r=(r-t*a)*10;q*=10;removed+=1
                    if trace:state('R')
    if trace:
        state('F');events.append(f'C {k} {tests} {tests} {printed} {removed}\nL 6 6\n')
    output=''
    for start in range(0,n,10):
        line=''.join(digits[start:start+10]);output+=f'{line:<10}\t:{min(n,start+10)}\n'
    return output.encode(),''.join(events).encode(),dict(advance_steps=k,extract3_calls=tests,extract4_calls=tests,emitted_digits=printed,removal_steps=removed)
