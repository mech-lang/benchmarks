# OCaml retained-source review

The [bound review](review.json) covers six complete local/derived application
sources across binary trees, Fannkuch, FASTA and k-nucleotide. Twelve unchanged
upstream submissions are protected and receive no new source/runtime claim from
this packet. All original citations and notices remain attached to their exact
source hashes; draft alternatives do not replace them in the catalog.

| Retained design | Source findings and alternatives |
| --- | --- |
| Binary trees #2 and #5 | Both construct every leaf using `Sys.opaque_identity` and recursively allocate/check the entire tree. #2 forks one task per depth, #5 is serial. Compare bounded standard OCaml domain scheduling and collector/runtime policies while retaining every node, stretch release and live long-lived root. A closed-form check or shared leaf would violate the required work. |
| Fannkuch #4 | Factorial rank chunks, scratch arrays and 32 forked workers are already present; this is more than a naive permutation baseline. Worker count and process/pipe cleanup deserve review. Preserve all rank intervals, final-rank guard, actual flips, checksum and maximum; do not infer that fewer workers are faster without a fresh comparison. |
| FASTA #6 | Cumulative selection and direct binary64 division remain in OCaml. The random output buffer grows with the complete record. At zero random bases the source reaches a negative final-byte index; this is a source-derived path, not a newly observed native failure. The bounded-buffer draft retains the arithmetic and addresses the empty-write path. |
| K-nucleotide #1 | Reused string scratch keys and mutable count cells already avoid copying a key on every successful lookup. New keys still allocate strings; each window is recopied and rehashed. The parser's prefix-only THREE test, empty lines, comments and CR-only input need boundary validation. |
| K-nucleotide #3 | Numeric keys and mutable entries are already implemented, with forked independent maps and a pair-key fallback for 32-bit hosts. Each window is repacked from its full width. Small initial maps retain the required growable-map work. The rolling draft changes this recurrence, not the counting requirement; parser and source-size changes are kept separate. |

The retained Fannkuch source declares 32 workers. Its command, affinity and
process lifetime need reconciliation before calling it an eight-worker
configuration. Candidate worker-count comparisons must also close and reap
their owned child processes, retaining the full assigned rank range.

The [nucleotide drafts](../rolling-v1/README.md) retain full histograms and
ordinary standard-library APIs. The [FASTA draft](../fasta-buffer-v1/README.md)
retains all generated bases and draws. These are source-only experiments; no
compiler or benchmark process runs during this review.

OCaml's modules, algebraic data types, pattern matches, functional composition,
arrays and native expression functions are legitimate concise forms. Native
normalization must distinguish independent `let`/`and` bindings and sequence
expressions from tuple/record fields, literal separators and expression
continuations. Pattern-match alternatives are structural clauses, not invented
scalar work. Pinned native parser/formatter ownership and exact counts remain
pending. Raw source rows, text size, gzip and BPE do not substitute for them.

The raw nucleotide measures illustrate why these metrics remain separate. The
compact draft uses fewer physical rows than the retained string-key source,
but more bytes, gzip bytes and BPE tokens. That is not an admitted normalized-LOC
win. These totals include notices, comments and whitespace in each complete file.

| Nucleotide source | Physical rows | UTF-8 bytes | Gzip bytes | BPE tokens |
| --- | ---: | ---: | ---: | ---: |
| Retained string keys #1 | 84 | 2,754 | 1,251 | 839 |
| Retained numeric keys #3 | 235 | 5,957 | 2,009 | 1,983 |
| Parser repair | 255 | 6,741 | 2,305 | 2,171 |
| Parser plus rolling keys | 258 | 6,870 | 2,369 | 2,221 |
| Compact rolling keys | 75 | 3,018 | 1,384 | 876 |

These are retained full-workload medians, not new results. Ratios use the exact
historical Mech AOT profile on the same workload/input, bound with its samples
and report in `review.json`.

| Retained OCaml implementation | Seconds | × Mech AOT |
| --- | ---: | ---: |
| binarytrees-ocaml-2-faithful | 2.097798 | 5.32× |
| binarytrees-ocaml-5-faithful | 5.887777 | 14.93× |
| fannkuchredux-ocaml-4-faithful | 3.928386 | 2.31× |
| fasta-ocaml-6-faithful | 2.607959 | 4.82× |
| knucleotide-ocaml-1-faithful | 19.679618 | 38.30× |
| knucleotide-ocaml-3-faithful | 5.158998 | 10.04× |
