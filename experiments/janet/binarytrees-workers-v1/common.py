"""Exact source set and shared native process owner for the tree study."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('trees_owned',HERE.parent/'knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
PLAN=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
SOURCES={'parent':HERE.parent/'source-v2/binarytrees.janet',
         'cached':HERE.parent/'array-access-v1/sources/binarytrees-cached.janet',
         'threaded-cached':HERE/'sources/threaded-cached.janet'}
sys.path.insert(0,str(HERE.parent/'bounded-v1'))
from outputs import validate_success

def expected(n):
    depth=max(6,n)
    output=[f'stretch tree of depth {depth+1}\t check: {2**(depth+2)-1}\n']
    for d in range(4,depth+1,2):
        count=2**(4+depth-d);output.append(f'{count}\t trees of depth {d}\t check: {count*(2**(d+1)-1)}\n')
    output.append(f'long lived tree of depth {depth}\t check: {2**(depth+1)-1}\n')
    return ''.join(output).encode()

def work(n):
    depth=max(6,n);main=(2**(depth+2)-1)+(2**(depth+1)-1)
    short=sum(2**(4+depth-d)*(2**(d+1)-1) for d in range(4,depth+1,2))
    return main,short
