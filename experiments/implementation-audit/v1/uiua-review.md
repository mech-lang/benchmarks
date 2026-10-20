# Uiua: complete retained-source review

Reviewed all **17 profiles and 16 distinct application texts** across ten
workloads, using the exact retained SHA-addressed source. Compact/optimized tree
labels share one text and one recorded timing owner; other pairs have distinct
source or independently recorded observations. Bindings for every profile remain
in [inventory.json](inventory.json) and the [Uiua source bundles](../../../programs/uiua/).
No interpreter, compiler, browser or benchmark was run. Findings are source-level
hypotheses and work-review questions, not measured causal explanations.

The catalog records local applications/ports, with original lineage unresolved
for several profiles. The two Mandelbrot records remain origin-unverified. This
review does not infer an AI author. Preserve original notices, retained snapshots
and per-profile general-library/source-boundary evidence.

| Workload and every reviewed profile ID | Actual source and existing good techniques | Next valid candidate and checks |
| --- | --- | --- |
| N-body: `nbody-uiua-native-denominator-compact-v3`, `nbody-uiua-native-denominator-optimized-v3` | Both use full all-pair outer differences, masks for diagonal/upper triangle, array reductions and source-owned fifty-million-step iteration. The compact `Advance` invokes `NewVelocity` through both its position and velocity branches; fast uses a combinator that shares the result. Fast is 472.77 s versus 772.87 s with the same 21 retained LOC. | Preserve the shared-result form. Review whether the same single-evaluation pattern can share positions, differences, norms and other expensive derived arrays without changing step dependencies. Compare an ordinary ten-pair representation against all 25 differences, and check whether generic power in the denominator creates avoidable work. Keep exact square roots/divisions, all pair contributions, initial momentum, both energies and numerical-order constraints; do not use independent-time-step parallelism. |
| Binary trees: `binarytrees-uiua-compact`, `binarytrees-uiua-optimized` | The same 15-LOC source constructs recursive `Tree {Id Left Right}` records, builds/checks actual descendants, retains `Long` and folds all temporary checks serially. Both labels reference identical bytes; this is not two optimization designs. Saved time is 2627.88 s. | Review record/box allocation, recursive field access and bounded independent iteration ranges, borrowing the ordinary `spawn`/`wait` pattern already used by fannkuch/Mandelbrot. Prove fresh equal-size nodes including leaves, complete traversal and correct stretch/long-lived lifetimes before changing the record representation. Do not delete `Id` merely because it is not used by `Check`: its allocation/identity purpose needs the retained work evidence reviewed first. No flat tree or shared leaf. |
| Fannkuch: `parallel-study:uiua-compact`, `parallel-study:uiua-fast` | Both already split factorial rank ranges across at most eight `spawn` callbacks and process 1024 permutations per block. Compact flips by row-wise mapping; fast computes a flattened gather and reshapes once in `FlipPermutations`. Fast is 558.23 s versus 1668.21 s. Both count actual prefix flips and reduce rank-parity checksums. | Transfer flattened indexing rather than adding redundant “parallelism.” Compare bounded block sizes, immutable row-offset reuse and temporary array volume. Preserve every permutation and actual flip; shared gathered data cannot become precomputed flip counts. Check tiny rank ranges, factorial interval boundaries, worker joins, maximum and checksum independently. |
| Mandelbrot: `uiua-parallel-study:whole11`, `uiua-parallel-study:whole16-parallel` | Both use full-row numeric arrays and a persistent live mask, stopping a row when all lanes escape or fifty iterations finish. Parallel distributes interleaved row groups to at most eight `spawn` workers, gathers complete row bytes, then reorders them with `Order`. It improves the retained median from 55.28 s to 13.55 s. | Reuse ordinary bounded worker and output-order techniques elsewhere. Compare contiguous/interleaved bounded blocks and peak gathered-output storage; current parallel code retains the complete worker results before writing. Preserve all pixels, exact escape recurrence, PBM header, byte order and zero-padded odd-width tails. No analytic-interior or periodicity test. The origin-unverified source labels remain so. |
| Spectral norm: `spectralnorm-uiua-vectorized-compact9-v3`, `spectralnorm-uiua-vectorized-optimized-v3` | Compact constructs full outer-sum/triangle coefficient arrays per product. Fast computes 128-row blocks, reducing peak coefficient arrays while recomputing them for each pass (3.48 s versus 3.78 s). Nineteen `Step`s plus one final `Step` give twenty ATA compositions, i.e. forty dense products; the coefficient matrix is not cached across passes. | Keep blocking and assess fusion/reuse of temporary row/index arrays within one product. Consider bounded parallel row blocks only if the pinned runtime supports ordinary source callbacks with controlled storage. Preserve the separate required coefficient/forward/transpose/composition structure and all forty recomputations. Do not replace the application with a native matrix cache or eigensolver. |
| FASTA: `fasta-uiua-compact`, `fasta-uiua-batched-output-optimized-v2` | Compact generates only sixty draws at a time and prints wrapped lines. Fast already uses 65,520-element generic affine-prefix coefficient scans, direct seed division, vector CDF comparisons and one packed raw write per chunk (15.13 s versus 206.17 s). It carries the final seed across random records and generates ALU chunks separately. | Preserve buffered writes and generic coefficient work; compare chunk sizes, prefix-array reuse and packing indices. Test 0/1/59/60/61 and final-chunk sizes, continuous RNG state and exact output lengths. Every seed and binary64 division must still be materialized; a period/output cache or integer-threshold substitution is not an alternative. Verify modular arithmetic remains exact under the chosen Uiua numeric representation. |
| K-nucleotide: `knucleotide-uiua-bounded-optimized-v3`, `knucleotide-uiua-native-group-optimized-v3` | Both build all seven full maps from 65,536-window chunks with overlap. Bounded folds `AddCount` once per window; native-group classifies windows with ordinary array grouping, then folds one weighted update per class. The grouped median is 886.63 s versus 933.03 s. Both materialize string windows and use a `^>THREE[^\n]*` regex rather than exact header-token matching. Invalid symbols pass through an alphabet-index/modulo mapping instead of an explicit validation branch. | Review exact token/boundary parsing, packed rolling keys and bounded ordinary width workers. Preserve the bounded per-window candidate as the reference. **Work-policy question:** grouping covers every window but reduces visible map updates; a common rule requiring every lookup/update in Uiua must explicitly adjudicate it, not rely on the word “native” or a generic admission summary. No query-only counts or omitted widths. Check missing/empty THREE, comments, CRLF, EOF and windows crossing chunk boundaries. |
| Reverse complement: `revcomp-uiua-optimized` | Cleans comments/CR, uses a regex to obtain all records, maps the complete alphabet through ordinary array indexing, reverses each sequence and constructs wrapped output. The whole input and record-capture arrays coexist. Saved time is 29.83 s. | Compare ordinary bounded record/chunk parsing and raw output packing, borrowing FASTA's chunked `&w` pattern. Preserve complete headers and IUPAC mapping including lowercase/U. The record regex requires a newline after the header, so an unterminated header/empty last record needs a fixture. Verify comment-at-EOF handling and unknown-symbol policy before any parser replacement. |
| Regex-redux: `regexredux-uiua-compact` | Reads the whole source, materializes regex match/capture collections to take their length, and performs five source-visible sequential replacement transforms. The nine patterns and five pairs are compact array literals; current time is 6.22 s. | Review a general count-only regex API if supported, ordinary independent count workers, and copying between replacements. Preserve nonoverlap/case rules, all nine counts and all five dependent substitutions. `⧻` measures Uiua text elements; retained canonical input is ASCII, so make the byte-versus-character input contract explicit for adversarial tests rather than silently changing length semantics. |
| Pi digits: `pidigits-uiua-compact` | Six GMP cells are allocated once through general FFI; source-owned `Triple`/`Quadruple`, two actual floor divisions, consume/emit recurrences and ten-digit flush operate on those cells. The 46-LOC source frees them at the end; saved time is 2.79 s. The absolute dylib path is historical. | Preserve reused cells and buffered output. Compare stack/combinator duplication and general FFI temporary/call overhead without fusing a pi algorithm into C. Recheck pointer alias ordering, both extracts before acceptance, unlimited arithmetic, padding and error-path cleanup. Relocate the generic library through a recorded build/run recipe; moving application FFI declarations outside counted source would require the same boundary rule used for other languages. |

## What can transfer now

The source already supplies several genuine idiomatic alternatives: shared
evaluation in n-body, flattened gather in fannkuch, bounded coefficient blocks in
spectral norm, ordinary `spawn`/`wait` scheduling, and packed output in FASTA.
These are stronger starting points than assuming every glyph-level operation is
cheap or that a historical “optimized” label represents exhaustive tuning.

Prioritize k-nucleotide's work/parser review and tree recursion/allocation, then
n-body's repeated all-pair arrays. Scheduling and output buffers can be reviewed
without changing algorithms. Worker startup, interpreter loading, general FFI
loading, IPC, complete I/O and shutdown remain part of the recorded whole-process
metric. No compiled/native candidate or new timing is admitted here.

## Counting and provenance traps

Uiua records, forks, folds, array primitives and pure compositions are legitimate
expressive source. Do not expand a reduction into imaginary scalar statements or
count punctuation as separate operations. Conversely, a long packed definition
may contain several independent binding/side-effect owners; current retained
LOC is not a certified whole-language grammar. Record declarations, callbacks,
literal arrays, FFI definitions, formatting and application parsing need one
explicit owner policy. Line wrapping alone must not be presented as a semantic
increase in work.

Use the source-metrics packet's exact application/submitted line partitions for
bytes, gzip and cl100k_base BPE. BPE is vocabulary/Unicode dependent and counts
text, not logical statements or Uiua lexical tokens. Missing qualified formatter
counts remain absent. General installed runtime/library code is outside the
application, while workload-specific parsing, packing, coefficient construction
and map operations remain inside it. All citations, unresolved original-origin
statements and library notices should travel with any isolated replacement.
