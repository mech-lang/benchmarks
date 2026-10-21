# OCaml candidate boundary fixtures

This packet prepares fourteen additional inputs and complete independent
reference outputs without launching OCaml. The string-slice nucleotide oracle
and simple ordered-draw FASTA oracle first reproduce all thirty retained shared
nucleotide/FASTA reference outputs byte for byte. That check validates reference
preparation, not any OCaml draft.

Eight nucleotide inputs split exact headers, CRLF terminators, sequence data,
comments, a stopping header or header-only EOF around 65,536-byte input chunks.
Six FASTA inputs place the TWO or THREE random record just below, exactly at or
above the proposed 1,024-row output-buffer boundary. Every expected file retains
complete bytes and a SHA-256 identity.

The resulting candidate schedule has 88 native executions pending: 22 nucleotide
cases for each of three forms, and 22 FASTA cases. No execution or native
qualification is claimed by the fixture manifest. The ordinary Python reference
program uses full output construction and naive string-key frequency counts;
it shares no rolling-key or bounded-output implementation with the OCaml drafts.

```sh
python3 experiments/ocaml/fixtures-v1/prepare.py --check
```

The standard ALU/probability data and workload descriptions originate in the
Benchmarks Game; the retained [BSD terms](../rolling-v1/LICENSE.benchmarksgame)
apply. Application source, native parser/compiler/runtime identity, required-work
witnesses, complete full-size output and fresh isolated timing remain separate
qualification requirements.
