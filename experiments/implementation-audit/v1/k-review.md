# K (Growler): complete retained-source review

Reviewed all **ten retained K applications**, one per workload, and the shared
`standard.k` binding/process-map source. Exact hashes and application/support
roles are preserved in [inventory.json](inventory.json); source bundles are in
[programs/k](../../../programs/k/). No K/native process, compilation or timing was
run. Ports/local edits are documented, but earliest source authorship remains
unresolved for several programs. Missing citations do not establish AI origin.

The source n-body shebang/comment names Amber, while the recorded comparison
variant is Growler. Preserve the historical text, and use the actual pinned
runtime/command evidence rather than inferring execution from the shebang.
`standard.k` contains ordinary GMP arithmetic, one-key khash get/set, PCRE2 and
POSIX process bindings. Its `peach` divides items across at most eight children;
callbacks execute in K and results are serialized through the pipes. This is
already parallel scheduling, not a missing feature to propose again.

| Workload / reviewed ID | Code-specific findings and existing strengths | Candidate and semantic constraints |
| --- | --- | --- |
| N-body / `array-k-growler` | Uses flattened coordinate arrays, immutable ten-pair gather indices, three precomputed component ranges, scaled velocity/mass state, and a vector update. Pair displacements/norms/force arrays are rebuilt each step; the 36-LOC count includes source initialization. Median 23.31 s. | Preserve ten-pair and cached-index techniques. Review array temporary reuse, gathering/fusion and repeated index access in `adv` without changing dependent step order. The scaled `dt`/mass formulation and energy rescaling deserve explicit common numerical-rule review; do not silently substitute approximate sqrt, change pair contributions or parallelize time steps. Both energies and momentum remain required. |
| Spectral norm / `array-k-faithful` | Four visible functions `A`, `Av`, `Atv`, `AtAv` recompute coefficients per row/product. Nineteen ATA applications plus one final application perform forty dense products. Only row vectors, not a cached matrix, are retained. Median 2.75 s. | Compare row-block scheduling through ordinary K callbacks, reuse immutable `!n`, and inspect temporary coefficient arrays. Repeated process creation/serialization may outweigh row parallelism and must remain timed. Preserve all products/functions and per-pass coefficients; a matrix cache or native eigensolver is invalid. |
| Mandelbrot / `array-k-faithful` | A three-element state holds real/imaginary/live row arrays. `50 step/` always updates every lane for all fifty iterations, including escaped lanes. It packs eight bits per output byte and writes each row serially. Median 34.49 s. | Compare live-lane filtering or whole-row early termination, and bounded ordinary row workers using the existing process map. Transfer immutable coordinates/weights outside hot callbacks and aggregate output in bounded row blocks. Preserve every pixel, escape-tested recurrence, full PBM order and odd-width zero padding; no analytic interior/periodicity shortcut. |
| K-nucleotide / `array-k-faithful` | Packs base-4 keys by transposing `rows × width` frame pieces and folding columns, then `inc/[h;keys]` makes a real one-key get and set for every window. Each frame has eight pieces and its own default-capacity growing khash. Seven `count` calls each create another process-map cohort; all key arrays are materialized. Median 22.80 s, 52 retained LOC. | Compare bounded packing or rolling-key chunks, immutable encoded DNA reuse, per-window generic FFI crossing and grouping jobs across widths. Preserve every update and private map ownership; do not move the counting loop into C or replace maps with query-only/histogram shortcuts. Current six-character THREE selection accepts a prefix; add exact token, missing/empty record, comments, CRLF/EOF and chunk-boundary cases. Validate all 36-bit keys in the pinned integer representation. |
| Fannkuch / `array-k-faithful` | Eight factorial rank intervals are already initialized and dispatched through `peach`. Each prefix flip constructs reverse/take/drop/concatenated lists; global permutation/count/checksum variables are private because workers are separate processes. Median 226.72 s. | Compare ordinary scratch storage/array amend and bounded batches with immutable row indices, while retaining actual prefix reversal and canonical carry. The flattened gather strategy already retained in Uiua is a possible language-level design reference, not permission to port a native kernel. Preserve every rank, parity and maximum; verify small intervals and disjoint coverage before timing. |
| FASTA / `array-k-faithful` | `rand\seed` materializes an entire random record, then vector CDF comparisons create more full-length arrays. ALU repetition and `wrap` similarly build full records before writing; RNG state is continuous and division remains binary64. Median 16.56 s. | Transfer bounded raw-output and seed-carry techniques already present in R/Uiua FASTA: generate ordinary scan chunks, keep last seed, wrap/output bounded blocks. Compare a generic affine-prefix implementation only with full seed/division/exactness evidence, not a cached period. Preserve all 2n/3n/5n bases, headers, CDF thresholds and final-line behavior. Explicitly test n=0 before dereferencing `*|r`. |
| Binary trees / `array-k-faithful` | `N`, `T`, `C` allocate/check nested pair nodes, including leaves; `long` survives temporary work. Independent depths already run through `peach`. `iterations#x` and `one'` materialize depth/result vectors before reduction, and one job per depth can leave workers idle. Median 39.50 s. | Compare a source-owned streaming accumulator over iteration counts, and split depth iteration ranges into bounded jobs. Review equal-size distinct pair nodes, full traversal, stretch release and root lifetime under fork/copy-on-write; do not flatten trees, share leaves or count checks algebraically. Keep process serialization and startup inside whole-process time. |
| Reverse complement / `array-k-faithful` | Reads all lines, detects header boundaries, concatenates every sequence, maps through an alphabet lookup, reverses and wraps. Complete sequence/result strings coexist; output creates a list of 60-character lines. Median 1.09 s. | Compare a 256-byte generic lookup table and bounded raw block writes, borrowing R's retained reverse-complement technique, or ordinary record streaming. Current source does not visibly remove semicolon comments/CR bytes; check common input rules, missing/empty records, trailing header without LF and unknown IUPAC symbols rather than assuming canonical-output success covers them. Preserve every header and full record order. |
| Regex-redux / `array-k-faithful` | Uses the already count-only general `rxcount` primitive for nine independent scans, and five ordered `rxreplace` calls; it does not materialize all match positions in K. The whole source and replacement results are retained. Median 2.41 s. | Preserve count-only PCRE2, a good existing primitive to emulate in other language bindings. Review compiled-pattern lifetime/reuse, generic PCRE2 JIT evidence and optional bounded count jobs while including input-copy/IPC cost. Keep substitution order, case/nonoverlap rules and all three length fields. Do not fuse the redux orchestration into native support. |
| Pi digits / `array-k-faithful` | Reuses five ordinary GMP cells, performs source-controlled term updates and both `extract 3`/`extract 4` on candidate attempts after the impossible-candidate guard. It appends all requested digits to one string, then formats ten-column lines. Median 0.42 s. | Preserve reusable cells; compare bounded ten-digit output buffering and ordinary generic arithmetic/FFI call overhead. Recheck mutable-cell alias ordering and the guard policy common to other languages. Keep unlimited sequential arithmetic, both actual extracts when attempted, row counts and partial-line padding; no native spigot or precomputed digits. |

## Transfers, source cost and provenance

Useful retained techniques include n-body's fixed ten-pair gathers, spectral
norm's explicit recomputed coefficient functions, count-only regex primitives,
reused GMP cells, one-key growing maps, and the generic eight-child process map.
The largest unexplored source/runtime questions are repeated small-array work in
the numerical loops, full-record materialization in FASTA/reverse complement,
tree job balance and nucleotide's key arrays/FFI crossings. These are hypotheses;
saved measurements do not isolate their individual cost.

Original absolute `\l`/dylib paths are reproduction gaps that need relocation and
pinning, not application algorithm changes. Generic process-map and primitive
bindings remain separately identified; application parsing, packing, RNG,
permutation work, tree construction/checking and orchestration remain counted.
Changing the boundary just to shorten K would be inconsistent.

K projections, adverbs, vector arithmetic, list construction and pure expressions
are valid expressive constructs. Do not expand hidden scalar operations into LOC.
Independently sequenced assignments/side effects in a packed lambda still need
explicit retained owner treatment; list separators, arguments and literal matrix
rows are not automatically executable statements. Existing manual adjustments
are source-specific and do not certify the Growler grammar. Use qualified
formatter evidence separately, and use exact application/submitted partitions
for bytes/gzip/BPE without claiming that BPE is language-neutral lexical size.
