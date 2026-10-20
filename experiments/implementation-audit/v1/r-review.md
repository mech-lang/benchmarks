# R: complete retained-source review

Source-only review of all **18 retained R profiles**, covering ten workloads.
Every profile is locally adapted according to retained evidence; upstream
notices/citations remain in place. No source, measurement or count was changed,
and no R process was started. “Optimized” in an ID is a historical label. The
observations below identify candidate experiments, not measured causes or promised
speedups. Exact complete file SHA-256s and role partitions are in
[inventory.json](inventory.json), indexed by the profile keys below; the
[source bundles](../../../programs/r/) retain the actual inspected text.

The recorded runtime is GNU R 4.6.1, ARM64, bytecode JIT enabled. Native arrays,
PCRE and GMP are already ordinary library primitives in these sources. Replacing
the application by a native benchmark executor would change the comparison.

| Workload and all reviewed IDs | Actual source behavior and useful existing technique | Concrete next candidate / required review |
| --- | --- | --- |
| N-body: `nbody-r-compact`, `nbody-r-optimized` | Compact builds ten pair differences and an incidence-matrix product each step; optimized builds 25 ordered pairs, masks the diagonal with `Inf`, and performs three small matrix products. Both repeatedly allocate small matrices/vectors. Compact is the measured winner (207.51 s versus 392.36 s), so all-pair vectorization is already demonstrated to be a poor retained choice. | Keep ten pairs. Compare ordinary scalar/column vectors and cached immutable pair/index arrays with the incidence form; check temporary copies and JIT behavior. Do not parallelize dependent time steps. Recheck exact square roots, pair contributions, momentum and both energies; simultaneous vector sums can change arithmetic order, so matching nine printed decimals is not a complete numerical-order proof. |
| Binary trees: `binarytrees-r-compact`, `binarytrees-r-optimized` | Both allocate a fresh two-slot `list` at every leaf/interior. Compact uses `vapply` over every temporary iteration. Optimized byte-compiles `make`/`check`, uses a scalar accumulation loop, and sends whole depths to eight fresh PSOCK workers (73.90 s versus 224.05 s). Fresh workers deliberately avoid inheriting the retained root. | Transfer byte compilation and scalar accumulation independently to isolate their effect. Split each depth's iteration range into bounded jobs rather than one job per depth, which can leave workers idle. Include PSOCK startup, export, shutdown and IPC in whole-process time. Keep separate equal-size nodes, complete traversal, stretch release and the retained long-lived root; no shared leaf, flat representation or custom allocator. |
| Fannkuch: `fannkuchredux-r-array-compact`, `fannkuchredux-r-array-batched` | Both materialize 8192-column permutation batches from factorial ranks. Each flip pass constructs `rep`/`ifelse` gather vectors, copies a matrix subset and filters the active-column vector. Batched already distributes eight rank intervals through `mclapply` (341.11 s versus 1488.79 s). | Retain bounded vector batches; compare batch sizes, reuse immutable row/column offsets and avoid rebuilding equivalent gather scaffolding. Separate fork startup/scheduling from array allocations diagnostically. Every rank must still produce its actual prefix reversals, parity checksum and maximum; closed-form flip counts or a period cache are invalid. |
| Mandelbrot: `mandelbrot-r-compact`, `mandelbrot-r-optimized` | Compact updates full row arrays for all fifty iterations, even after escape. Optimized retains active lanes, shrinks `zr`/`zi`, and forks eight workers for each 128-row batch (19.74 s versus 61.80 s). It rebuilds `cr` and bit weights inside every row callback, and repeatedly creates worker groups. | Hoist immutable coordinate/weight vectors outside `row`; compare a persistent bounded worker arrangement or larger ordered blocks while retaining ordinary R callbacks. Compare the allocation cost of shrinking lanes against masked fixed arrays. Preserve all pixels, escape-tested recurrence, MSB-first full PBM and odd-width padding; no analytic-interior or periodicity shortcuts. |
| Spectral norm: `spectralnorm-r-compact` | `vapply` computes each output row with vector arithmetic; the denominator is recomputed from `i+index` for every call. `step` performs both orientations and is called twice in each of ten iterations: forty dense products. There is one retained profile (4.60 s). | Compare a separately defined ordinary coefficient helper, hoisted immutable index arithmetic, and bounded row-block workers. Do not cache matrix entries or replace forty products by a native eigensolver. A future admission should explicitly reconcile the task's required coefficient/product function structure with the current combined `multiply(..., transpose=...)` closure. |
| FASTA: `fasta-r-compact`, `fasta-r-affine-hoisted-optimized-v2` | Compact executes scalar RNG updates in 60-character loops and builds strings with `paste0`/`substring`. The retained v2 source already computes generic affine-prefix coefficients once for 245,760-element blocks, materializes every seed, performs direct binary64 division and `findInterval` on the unscaled CDF, and writes wrapped raw blocks (5.51 s versus 75.53 s). | Transfer raw output/wrapping and bounded generation independently before inventing a new RNG scheme. Check coefficient storage/index copies and final-block slicing. Preserve the continuous seed across TWO/THREE, every seed and division, exact 2n/3n/5n lengths and final line. Do not replace this with a cached RNG period or precomputed output; prove integer-exact modular products and threshold behavior for any changed affine formulation. |
| K-nucleotide: `knucleotide-r-compact`, `knucleotide-r-optimized` | Compact creates 250k string-window batches, `table`s each batch, unions all key names and reallocates aligned totals. Optimized uses 1m windows, `match`, `unique`, growing key/count vectors and `tabulate` (34.06 s versus 157.27 s). Both retain complete results for all seven widths, but the implementation uses grouped bulk counting rather than a visible source-level counter update per window. Both select a `>THREE` prefix, not an exact header token. | Review an exact-token bounded parser and packed keys before further optimization. A source-owned rolling integer-key map is an independent candidate; 36-bit keys and full counts fit exact binary64 integers, but R integer bit operations need a width audit. **Work-policy question:** generic `table`/`tabulate` covers every window, yet may not satisfy a rule requiring each lookup/update in the named language; obtain explicit common-policy review, rather than treating generic `strict:true` metadata as a detailed work certificate. No query-only count or omitted width is acceptable. |
| Reverse complement: `revcomp-r-compact`, `revcomp-r-optimized` | Compact expands each record to individual strings using `strsplit`, reverses, concatenates and slices into output lines. Optimized already uses a 256-entry raw translation table, reverse indices and bounded 60×4096-byte output blocks (5.75 s versus 17.83 s). It still retains all `readLines` input plus a complete concatenated raw record. | Transfer raw lookup/wrapping elsewhere. Compare ordinary record streaming, release line storage before reversing, and reuse bounded line/output offsets. Preserve headers, all IUPAC symbols including lowercase/U, comments, CRLF/EOF, empty records and exactly 60-column output. Unknown-byte treatment differs between `chartr` and identity-initialized raw table and needs an explicit input policy. |
| Regex-redux: `regexredux-r-compact` | Uses byte-preserving `readChar`, nine `gregexpr(..., perl=TRUE, useBytes=TRUE)` calls and five ordered `gsub` calls. Every match position vector is materialized just to count entries; input has a hard one-billion-byte read cap. One retained profile (10.07 s). | Review the standard PCRE configuration/JIT evidence and bounded independent pattern workers, including copying/fork costs. A general count-only API would avoid position vectors if available in the pinned runtime; do not claim the current API already does that. Preserve nonoverlap, case rules, all five dependent replacements and all length fields. Reconcile the read cap with supported full inputs and test empty/no-match data. |
| Pi digits: `pidigits-r-compact`, `pidigits-r-optimized` | Both use general `gmp` big integers. Compact performs two separate quotients and calls `cat` per digit. Optimized stores a GMP vector of multipliers 3/4, calculates both quotients together, and buffers ten digits (20.36 s versus 25.62 s). It also moves the impossible-candidate `num > acc` guard before the quotient pair. | Retain buffered output and compare generic GMP temporary/vector costs against two scalar extracts. Confirm the same impossible-candidate guard is allowed across all languages; it cannot become a query shortcut or approximate arithmetic. Keep unbounded sequential state, both required stable-digit extractions when attempted, simultaneous recurrence semantics and partial-row padding. |

## Transfers and ordering

The first review targets are n-body's small-array allocation pattern, tree job
balance, fannkuch gather allocation, and k-nucleotide's parsing/work-policy issue.
Existing techniques worth preserving are R's raw-block I/O in reverse complement
and FASTA v2, active-lane Mandelbrot, byte-compiled tree functions, generic
bounded worker APIs, and buffered GMP output. The slower all-pair n-body program
is evidence against assuming that a more vectorized or “optimized” label wins.

Startup and generic package loading belong in final whole-process medians. They
can be diagnosed separately, but no execution-only substitution or pooled
historical cohort is proposed. PSOCK, fork workers and threaded numerical
libraries must share the established total worker limit; inspect actual BLAS
thread settings before admitting another parallel configuration.

## Source counting and lineage limits

`compiler::cmpfun`, worker callbacks, FASTA coefficient construction, parsing and
wrapping are application logic and must not disappear as “support.” Ordinary R
`table`, `match`, `findInterval`, raw-array and formatting primitives are legitimate
expressive constructs; do not expand their implied operations into invented LOC.
Conversely, packed assignments, multiline literals, expression functions and
closures need the retained rule identified, not a claim of one universal logical
counter. Application/submitted bytes, deterministic gzip and cl100k_base BPE
describe the actual retained partitions, including comments/whitespace, rather
than validating logical LOC. Qualified formatter counts remain separate.

The n-body comments name Leo Osvald and an earlier `nbody_3.R`; retained source
citations point into historical RBenchmarking/Game material. “Adapted” does not
establish the earliest author or an exact upstream revision by itself. Preserve
those notices and the per-profile unresolved-origin/license statements. No
uncited program is reclassified as AI-generated by this review.
