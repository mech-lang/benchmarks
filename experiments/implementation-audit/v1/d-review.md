# D: complete retained-source review

Reviewed all **19 retained D profiles** and their exact application texts across
ten workloads. All are recorded adaptations, including source descended from
published Game, Crystal, Rust, Zig, Hanabi and C examples; the original contributor
comments and per-profile citations must be retained. Exact file hashes/roles are
in [inventory.json](inventory.json), with complete [D source bundles](../../../programs/d/).
No compiler, native program, browser or benchmark was executed. Current measured
winners are not proofs of global optimality, and the proposed changes below have
no measured speedup attached.

| Workload and all reviewed IDs | Actual retained implementation / existing improvement | Next candidate and required checks |
| --- | --- | --- |
| N-body: `d-unrolled` | `Body[5]` uses fixed `double[3]` position/velocity arrays. Nested `static foreach` unrolls all ten pairs; array expressions update both bodies, using ordinary `sqrt` and `dotProduct`. There is one retained source (1.17 s). | Review generated temporary storage and whether constant-size dot/array expressions fuse before adding manual SIMD or changing layout. A structure-of-arrays candidate is meaningful only with exact update-order/numerical proof. Preserve momentum offset, every sequential step, ten pair updates and both energies; no approximate reciprocal sqrt or independent time-step tasks. |
| Spectral norm: `d-compact`, `d-parallel-neon` | Compact has template-specialized orientations and three reused numeric vectors. Fast already uses ordinary parallel output rows, two-lane NEON division, a scalar odd tail and a fixed `defaultPoolThreads=7` setting (0.099 s versus 0.874 s). The main participant plus pool must fit the established total limit. | Preserve vector reuse and actual denominator recomputation. Compare row grain, input-load/denominator recurrence and scalar-tail handling; do not propose parallel/SIMD as absent. Fast's two-lane accumulated sum differs from scalar order, so retain the shared numeric rule and full-output tolerance evidence. Keep forty dense products and the coefficient/forward/transpose/composition structure; no matrix cache. |
| Mandelbrot: `d-archive-complex`, `d-parallel-array-eight` | Archive retains Dave Fladebo's contribution and uses `Complex!double`, per-pixel loops and `putchar` (10.97 s). Fast precomputes eight-lane real coordinates, processes rows through a seven-thread pool, performs five recurrence steps per escape-group test and buffers the complete PBM bitmap (0.448 s). It masks odd-width tail bits. | Retain the fixed-array/pool improvement. Compare ordinary two-lane native SIMD or compiler-vectorized arrays, row/block grain and bounded output buffering. Review the five-step escape grouping against the common prescribed-work rule, including overflow/NaN behavior; do not add analytic interior/periodicity tests. Keep z0=0, full pixels, at most fifty recurrence steps, correct lane/tail masks and PBM output. |
| Fannkuch: `d-compact-scalar`, `d-parallel-neon` | Scalar has reusable fixed 32-element arrays and canonical carry/actual flips. Fast uses precomputed reversal/rotation **index masks**, the ARM NEON table intrinsic for actual permutation shuffles, eight factorial rank intervals and a capped ordinary task pool (2.44 s versus 30.55 s). Masks are not answer/flip-count tables. | Preserve scratch reuse and SIMD gather. Review task grain and compile-time mask construction/source cost without obscuring the algorithm. Test n=0/1/2 and intervals where `permsCount/8` becomes zero before using `iota(..., lenPerTask)`; the full n=12 path alone does not qualify those boundaries. Scalar checksum uses unsigned arithmetic with signed alternating contributions; explicitly verify printing/range semantics on negative-checksum small cases. Every permutation and actual flip remains required. |
| FASTA: `fasta-d-compact`, `fasta-d-optimized` | Compact allocates a new line and range-array per output line, then `writeln`s. Fast reuses stack `char[61]` storage, a 1 MiB output buffer, incremental ALU wrap and compile-time known CDF widths with ordinary comparisons (0.631 s versus 2.76 s). Both retain each RNG update and direct binary64 division. | Transfer ordinary buffering/reused fixed storage to other workloads before changing RNG. Compare the linear unrolled CDF against a general binary/first-match implementation under the exact threshold rule. Preserve continuous seed across records, 2n/3n/5n lengths, headers and tails. Review `emit`'s maximum-input-size contract if generalized: its single flush assumes each emitted fragment fits the fixed buffer. |
| K-nucleotide: `knucleotide-d-compact`, `knucleotide-d-published-rolling` | Compact uses immutable string slices as associative-array keys and performs full maps for all seven widths (10.34 s). Fast packs each window in `Code`, uses a growing `uint[Code]` map and its single-lookup `update`, starts five width tasks explicitly in new threads and computes widths 1/2 in the main thread (2.27 s). It already has rolling keys and ordinary parallel width work. | Compare simpler packed-key source/API use and map growth/allocation before redesigning scheduling. `CodeRange.front()` mutates rolling state, so a refactor must ensure repeated front access cannot advance the key; current foreach use is not proof for all range consumers. Both parsers match a THREE prefix and can keep reading a second THREE header; require exact-token/first-record tests, empty/short records, comments and CRLF/EOF. Preserve every overlapping update, all seven maps and exact 36-bit keys; no query-only counting. |
| Regex-redux: `regexredux-d-compact`, `regexredux-d-published-3` | Compact constructs runtime regexes and iterates matches. Published-derived fast uses `ctRegex` for all patterns, an independently scheduled replacement task while main counts, and `replaceAllInto` with a reserved appender (0.695 s versus 1.76 s). All five replacements remain source-ordered. | Preserve compile-time pattern preparation and overlap of independent count/replacement streams. Review whether `to!string(sink.data)` copies, how `sink.clear()` interacts with that lifetime, and whether a safe double-buffer arrangement avoids further copies. Whole-process time still includes runtime startup/input/output; compile-time regex generation is AOT preparation. Keep nine nonoverlapping counts, case rules, five ordered substitutions and all lengths. |
| Reverse complement: `revcomp-d-compact`, `revcomp-d-optimized` | Compact's per-character `letters.countUntil` and mapped/reversed array is clear but expensive (8.29 s). Fast already replaces it with a 256-byte lookup, reverse indexing, output reservation and one `rawWrite` (0.687 s), while retaining a complete joined input plus a second full output. | Preserve O(1) translation and bounded writes; compare safe in-place or record-block storage. **Correctness review:** compact skips semicolon comments, while fast skips only CR/LF and will translate comment bytes through a mostly zero-initialized table. Fast also treats input start as a header and scans `>` without line anchoring. Reconcile preheader/comment/unknown-byte policies and test arbitrary records before any replacement. Preserve all headers/IUPAC/lowercase/U symbols, line lengths and record order. |
| Binary trees: `d-compact`, `d-fast` | Compact allocates a GC `Node` class for every node with default collection (11.22 s). Fast uses two-pointer structs and the **standard general** `Region!Mallocator`, makes one equal-size `allocate` call for each node, traverses the tree before `deallocateAll`, and uses a capped task pool across depths (0.445 s). Separate region lifetimes retain stretch and long-lived semantics. | Preserve the existing allocator/admission distinction: this is not an undisclosed custom native tree executor. Review depth/range job balance and independent region ownership; split iterations only with full allocation/traversal/lifetime evidence. Verify standard-region allocation accounting, alignment, capacity arithmetic and arbitrary odd depths before changing representations. No leaf sharing, flattened logical tree or omitted checks. |
| Pi digits: `d-compact`, `d-fast` | Compact uses expressive Phobos `BigInt` operators (3.14 s). Fast retains Mr Ledrug C #1 lineage but implements all control in D, with reusable ordinary GMP cells, multiply-add/subtract primitives, two real quotient extracts and `scope(exit)` cleanup (0.288 s). Both write per digit and pad partial rows. | Reuse arithmetic cells and consider ten-digit/whole-output buffering separately. Compare small generic arithmetic wrappers that improve clarity/source size while leaving the spigot in D and all app-specific FFI counted. Preserve unbounded state, allowed impossible-candidate guard, both attempted extracts, simultaneous update semantics and exact partial rows. No fused native spigot or answer cache. |

## Existing techniques worth transferring

D already has strong native-platform choices: compile-time pair specialization,
fixed storage, scalar tails, ordinary pool limits, ARM table-shuffle intrinsics,
single-lookup growing maps, compile-time regexes, bounded I/O buffers and reusable
GMP storage. The remaining clearest source questions are reverse-complement
input semantics/full-buffer duplication, nucleotide parser/range contracts, and
task-grain or tiny-input edge cases. A slower compact form is often an expressive
tradeoff rather than proof that the fast form is unexplored.

Seven pool workers plus an active main thread is a deliberate setting in several
sources. Explicit new threads in nucleotide/regex must be counted with any pool,
runtime or library threads before changing configuration. Keep AOT generation
outside the timing interval and startup, input, runtime work, complete output,
worker teardown and shutdown inside. Do not mix diagnostic timings into the
published whole-process comparison.

## Counting, attribution and expressiveness

The [existing D source review](../../../site/reports/d-loc-audit.md) explains real
compact advantages in regex loops, FASTA's ordinary `countUntil`, and `BigInt`
operators/string repetition. They are legitimate general-language/library
expressions, not hidden benchmark kernels. Their implicit scalar operations
should not be expanded into imaginary LOC. Conversely, `p = sum += p` contains
two updates and retains its explicit normalization adjustment. Nested comments,
array literals, template/static-foreach headers, intrinsic declarations,
callbacks and FFI need source-specific owner evidence under the retained rule;
the current totals are not a uniform whole-language logical-LOC certificate.

Standard allocator, regex and arithmetic implementation code is general library
support, while the workload loops, binders, parser and source-owned scheduling
stay counted. Preserve historical contributor notices and specific upstream
file links: comments such as “port from 1.cr” or “2-im.rs” are useful lineage
clues, not by themselves complete original-source citations. The inventory's
remaining origin/license gaps continue to apply. Qualified formatted counts and
application/submitted bytes, gzip and BPE are separate measurements, not proof of
an optimal idiomatic source or language-neutral lexical size.
