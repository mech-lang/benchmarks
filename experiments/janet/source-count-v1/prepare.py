"""Prepare native reader probes; lexical wrapping must not alter the result."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
pairs=[
 ('independent-forms','(def a 1)(def b 2)\n','(def a 1)\n(def b 2)\n'),
 ('matrix-data','(def matrix [[1 2] [3 4]])\n','(def matrix\n  [[1 2]\n   [3 4]])\n'),
 ('quoted-code',"(def data '(do (set a 1) (set b 2)))\n","(def data\n '(do\n (set a 1)\n (set b 2)))\n"),
 ('comment-and-string','(def text "#(not-code)\\n\\x00;[]")\n','# source comment\n(def text\n "#(not-code)\\n\\x00;[]") # trailing\n'),
 ('mutable-values','(def data @[@[1 2] @{"b" 2 "a" 1}])\n','(def data\n @[@[1\n 2]\n @{"b" 2\n "a" 1}])\n'),
 ('long-literal','(def data ['+' '.join(map(str,range(200)))+'])\n','(def data [\n'+'\n'.join(map(str,range(200)))+'])\n'),
 ('deep-tree','(def data '+ '['*20+'1'+']'*20+')\n','(def data\n '+ '[\n'*20+'1'+'\n]'*20+')\n'),
 ('function-body','(defn add [a b] (def total (+ a b)) total)\n','(defn add [a b]\n (def total (+ a b))\n total)\n'),
]
rows=[]
for name,a,b in pairs:
 for label,text in [('packed',a),('wrapped',b)]:
  p=HERE/'fixtures'/f'{name}-{label}.janet';p.write_text(text)
 rows.append(dict(name=name,packed=f'fixtures/{name}-packed.janet',wrapped=f'fixtures/{name}-wrapped.janet',expected_same_native_format=True))
(HERE/'fixtures/paren-call.janet').write_text('(def value (f x))\n')
(HERE/'fixtures/bracket-data.janet').write_text('(def value [f x])\n')
(HERE/'fixtures/malformed.janet').write_text('(def broken [1 2)\n')
(HERE/'probes.json').write_text(json.dumps(dict(equivalent_pairs=rows,distinct_pair=['fixtures/paren-call.janet','fixtures/bracket-data.janet'],malformed='fixtures/malformed.janet'),indent=2)+'\n')
print('Prepared eight equivalent pairs, bracket/call distinction and malformed input')
