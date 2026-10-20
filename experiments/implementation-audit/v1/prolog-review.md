# Prolog: complete retained-source and idiom review

Reviewed all **twenty Prolog profiles**, ten distinct main applications, the
nucleotide record helper and the current linear reverse-complement source. Each
compact/optimized pair has identical application bytes and independently saved
observations; neither label establishes an optimized alternative. Exact hashes,
current retained compiler inputs and application/support partitions are in
[inventory.json](inventory.json) and [programs/prolog](../../../programs/prolog/).
No Prolog/QLF/native program, compilation, benchmark, browser or generator ran.

[Provenance](../../../archive/languages/prolog/20261013/PROVENANCE.md) records new
translations from local Nim/C3/Gleam structures, not copied historical SWI/YAP
submissions. The exact later source/storage/linear revisions matter more than
that initial draft. The linear reverse-complement file still contains a stale
“draft source only” comment: current admission and measurement status comes from
its hash-bound evidence, not that historical comment. Original-source/model gaps
remain explicit and do not imply AI origin.

| Workload / both retained IDs | Actual implementation, reusable strengths and hotspots | Concrete performance and smallest-idiomatic alternatives |
| --- | --- | --- |
| N-body / `prolog-nbody-compact`, `prolog-nbody-optimized` | Runtime-created body functors provide direct argument access; `nb_setarg` updates mutable numeric fields. Deterministic recursive pair/position loops retain ten pairs, exact sqrt and sequential steps. Every interaction performs many `arg` calls, arithmetic goals and three `velocity/8` calls. Median 326.14 s. | Compare specializing the three coordinate updates and destructuring each body once, reducing predicate/argument dispatch without changing pair order. A body-term constructor in a predicate head and shared coordinate predicates are smaller idiomatic alternatives, but must preserve fresh mutable body ownership rather than introduce a compiler-shared ground term. Combine arithmetic intermediates only where evaluation/order stays equivalent. Do not replace the loop with a foreign n-body predicate or parallelize time steps. |
| Mandelbrot / `prolog-mandelbrot-compact`, `prolog-mandelbrot-optimized` | Source-owned scalar `escape/6`, eight-bit packing, row recursion and `put_code` per byte. CI is already computed once per row; CR is recomputed per pixel. Execution is serial; median 816.01 s. | Compare bounded row workers, immutable coordinate storage and row/block output buffers, retaining recurrence in Prolog. Clause-head base cases and a reusable byte-packing relation are already idiomatic; further compression should factor repeated traversal rather than pack goals onto one line. Preserve every pixel, exact escape tests, at most fifty iterations and zero-padded tails. No analytic interiors or native pixel kernel. |
| K-nucleotide / `prolog-knucleotide-compact`, `prolog-knucleotide-optimized` | Current source uses the qualified line helper's exact THREE token, comments and CR/LF/EOF handling. Seven full growing `library(hashtable)` maps use rolling integer keys and explicit `ht_get`/increment/`ht_put` for every valid window. It converts assembled sequence text to atom storage before random character access; all widths are serial. Median 545.00 s. | Preserve exact parsing and real per-window maps. Compare bounded source-owned encoding once, single-lookup general counter APIs if supported, and private-width worker tasks under the shared cap. Inspect actual character-access/storage cost and lifetime of the large atom/string representations before removing the qualified storage revision. A table-driven base mapping, shared get-default relation and paired width/query data can reduce repeated branches and orchestration. A Prolog arithmetic term passed to `ht_put` is not automatically evaluated: retain actual evaluated counts. No query-only, grouped-histogram or native counting replacement. |
| Spectral norm / `prolog-spectralnorm-compact`, `prolog-spectralnorm-optimized` | Compound terms hold numeric vectors; `row/7` dispatches transpose and calls `coefficient/3` per element, while each pass allocates new output/temporary vector terms. Four visible functions perform forty dense products. Median 179.42 s. | Compare orientation-specialized deterministic row predicates, bounded independent rows and safe reusable vector storage, retaining all coefficient evaluations. `NextAccumulator is Accumulator + A*Value` is a concrete smaller expression than a separate `Term` binding if the numeric rule agrees; a pure coefficient expression can similarly reduce temporary names, with possible recomputation tradeoffs. Keep the four required functions, scalar accumulation constraints and forty products; no matrix cache or foreign eigensolver. |
| Reverse complement / `prolog-revcomp-linear-compact`, `prolog-revcomp-linear-optimized` | A 65,536-byte source state machine preserves arbitrary headers/comments/CR/LF/EOF and stores bounded string chunks in reverse arrival order. Each input block becomes a code list; pending code lists are reversed into strings, then each stored chunk becomes a reversed code list again for complement/wrapping. It avoids a whole-record per-character list. Median 70.43 s. | Preserve this bounded linear design over earlier failed forms. Compare ordinary direct string indexing inside bounded reverse blocks, a generic byte lookup, and larger output chunks while keeping every reverse/complement decision in Prolog. A carefully qualified DCG/state-transition helper may shorten repeated `state(...)` construction, but must not reintroduce whole-input list expansion or hide domain parsing as generic support. Retain invalid-IUPAC errors, empty/header-only records, trailing comments and final line behavior. |
| Fannkuch / `prolog-fannkuchredux-compact`, `prolog-fannkuchredux-optimized` | Mutable functors hold the permutation and carry counts; prefix reversal uses actual paired `nb_setarg` updates. **A fresh Work functor is allocated inside every permutation visit**, then every element is copied before flips. There are no rank workers. Median 867.88 s. | Compare one private reusable scratch functor per worker, resetting every cell before each actual flip count; D/K already retain reusable-scratch/rank-range designs worth consulting. Add bounded factorial rank tasks only with full canonical initialization and disjoint coverage. A shared argument traversal or ordinary list-prefix relation is a smaller idiomatic alternative, but compare allocation rather than assuming list syntax is fast. Preserve all permutations, real reversals, parity and maximum; no cached flip counts. |
| FASTA / `prolog-fasta-compact`, `prolog-fasta-optimized` | Each 60-character line creates a fresh list, with source-owned scalar LCG updates, direct binary64 division, recursive CDF search and `format` per line. Seed is passed continuously through both random records. ALU uses indexed text access. Median 57.56 s. | Batch ordinary output lines/strings while retaining a bounded buffer and source RNG loop. A generic state-threading/DCG generator can combine repeated line/state plumbing; retain explicit seed and output-tail behavior rather than hiding a FASTA executor. Share CDF preparation and simple repeat/random formatting where semantics overlap. Every seed/division, unscaled CDF, exact record lengths and final line remain required; no period/output cache. |
| Binary trees / `prolog-binarytrees-compact`, `prolog-binarytrees-optimized` | `functor(Tree,node,2)` deliberately creates every node, including leaves, before filling children; `check` traverses actual references. Stretch returns before long-lived construction, and the long-lived root is used after all temporary depth work. Temporary iterations are tail-recursive and serial. Median 41.08 s. | Compare bounded independent iteration/depth ranges and native term allocation/GC behavior with full root-lifetime evidence. A declarative `node(Left,Right)` clause is a smaller idiomatic source alternative only after proving distinct runtime leaves; compiler-ground-term sharing is precisely why the current constructor is explicit. Keep every equal-size node, constructor/traversal and lifetime; no flat tree, shared constant leaf, term pooling or algebraic count. |
| Regex-redux / `prolog-regexredux-compact`, `prolog-regexredux-optimized` | Uses ordinary PCRE `re_foldl` with one Prolog counter callback per match, source-visible ordered `re_replace`, whole-input strings and explicit **`jit(false)`**. Median 19.33 s. | Compare a separately recorded JIT-enabled configuration if supported/allowed, compiled-pattern reuse and bounded independent count tasks before changing engines. A general count-only primitive could avoid per-match callback dispatch; a redux-specific native orchestrator cannot. Current recursive `counts`/`replacements` relations are already concise; ordinary fold/map relations are expressive alternatives but not automatically faster. Preserve all scans, nonoverlap/case rules, replacement order and lengths. |
| Pi digits / `prolog-pidigits-compact`, `prolog-pidigits-optimized` | Tail recursion uses native unbounded integers, verifies `bounded=false`, performs two real `div` extracts and writes a digit per acceptance. Padding is another recursive loop. Median 1.646 s. | Share `Numerator3` and derive `Numerator4 is Numerator3+Q` while retaining both quotients; compare bounded ten-digit output and normal formatting directives for partial rows. These are concrete smaller idiomatic expressions, not a claim of new LOC. Retain sequential unbounded state, simultaneous arithmetic semantics, full digits and padding; no fixed precision or foreign spigot. |

## What to prioritize and preserve

The numerical per-element dispatch/boxing and fannkuch's per-permutation Work
allocation are stronger concrete candidates than another alias with an optimized
name. Nucleotide and reverse complement already underwent important storage and
bounded-parser corrections; keep those exact current sources as references.
Tree freshness, exact THREE parsing, real mutable maps, deterministic tail
recursion, direct coefficient functions and unbounded native integer arithmetic
are existing strengths to transfer.

The main workload loops are serial. General thread/process candidates require
private mutable terms/maps, bounded outstanding work, deterministic reductions,
and the common worker cap; generic library threads also count. QLF preparation
and proof tools stay outside the timed application, while startup/loading,
complete input/output, normal runtime GC and shutdown stay inside whole-process
medians. No source or runtime change has been qualified by this review.

## Counting and provenance cautions

Predicate heads, explicit control goals, arithmetic bindings, cuts, clauses,
comma/semicolon syntax and meta-predicate callbacks need a native owner policy.
Pure terms, pattern matching and ordinary higher-order/list/map primitives are
legitimate expressive constructs; do not expand their implicit work into scalar
LOC. Conversely, compressing ten independent goals onto one physical line is not
a smaller logical program. When combining arithmetic goals, keep evaluation:
`X is A+B` differs from passing the unevaluated term `A+B` to a library predicate.

General stream/argument/error handling is separately partitioned, while the
nucleotide record helper still contains counted workload-relevant parsing. The
linear reverse-complement file has both host and application sections; their
reviewed line ranges, not the filename, define the boundary. Formatter-qualified
counts, retained normalized LOC, and actual-partition bytes/gzip/BPE remain
separate evidence. Preserve local-predecessor citations and all remaining
original-origin/license gaps without calling unverified source AI-generated.
