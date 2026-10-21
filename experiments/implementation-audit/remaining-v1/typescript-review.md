# TypeScript: retained designs and next alternatives

All ten retained application sources were inspected. The adjacent
[binding receipt](typescript-review.json) identifies exact profiles, complete
source bundles, citations and the catalog revision. This is a source/idiom review;
the existing native compiler, required-work and owner-count evidence remains
separately scoped. Draft-status comments inside retained source are historical;
the later recorded qualification controls its published status.

| Workload | Actual retained design | Concrete next alternative and constraints |
| --- | --- | --- |
| Binary trees | Sequential recursive two-child objects; every leaf is a fresh `TreeNode(null,null)`. One long-lived root stays reachable through the final check. | Compare bounded ordinary worker-thread jobs and a simpler object representation. Retain every distinct equal-size node, traversal, stretch release and long-lived root; include worker startup/teardown. Do not replace trees with flat storage or a computed check. |
| Fannkuch | Canonical carry rotation, ordinary number arrays and a complete scratch copy for every permutation, including first-element-zero cases. Reversals execute actual endpoint swaps. | Compare fixed typed arrays and a guard skipping only unused scratch copies. Preserve factorial rank order, all actual flips, signed checksum and n=0 behavior. V8 may already optimize small integer arrays; typed arrays are a hypothesis. |
| FASTA | Scalar LCG/direct division; cumulative object properties searched through `for-in` for every random base. `console.log` writes each60-character line. | Compare precomputed ordinary byte/CDF arrays and bounded synchronous raw output, reusing the existing Mandelbrot writer. Keep every RNG transition, binary64 threshold rule, continuous TWO/THREE seed, lengths and final partial line. No period cache or native generator. |
| K-nucleotide | Readline selects the first exact THREE header; every width creates substrings and performs get/set in a default-growing standard `Map`. Every one of the seven complete histograms is built. | The [rolling numeric-key candidate](../../typescript/rolling-map-v1/proposal.json) encodes once and uses exact integers up to36bits, avoiding32-bit bitwise truncation. Its27 bounded outputs pass; a1m-base pilot is separate from full timing. Preserve all occurrences, maps, sorting, parser and query semantics. |
| Mandelbrot | One scalar pixel at a time, up to50 recurrence steps; exact z0=0, MSB-first packing and bounded synchronous output with write-progress checks. Coordinates are recalculated inside the pixel loop. | Hoist unchanged coordinate expressions, then compare bounded independent row workers. Preserve the expression's floating-point order, all pixels, actual recurrence/escape tests and odd-width padding. No analytic interior or periodicity test. |
| N-body | Five ordinary objects, seven explicit fields each, ten pair updates in order, then position updates. No per-pair displacement arrays or vector destructuring. | Constructor parameter properties are an idiomatic source-size candidate; their authored fields still count. Compare cached body references or typed storage only with complete state/order checks. Keep both energies, momentum offset and every dependent time step; no approximate square root. |
| Pi digits | General built-in `bigint`, sequential spigot refinement, guarded pair of quotient extractions, buffered ten-digit rows with final padding. | Review temporary big integers and buffering without replacing the spigot with a foreign executor. Preserve both attempted stable-digit extractions and exact simultaneous recurrence semantics. Existing concise BigInt operators are legitimate language expressions. |
| Regex-redux | Latin1 input preserves byte lengths; nine global `String.match` calls materialize complete match arrays, followed by five dependent replacements. | Compare an ordinary global `RegExp.test` counting loop, whose lastIndex advances without retaining the full match list; all patterns are nonempty. Preserve nonoverlap, case sensitivity, all nine scans/five ordered replacements and lengths. Bounded worker orchestration is a separate candidate with its own source and startup cost. |
| Reverse complement | Complete input plus another input-sized sequence buffer; anchored CR/LF record parser, strict IUPAC validation and a bounded61KiB output buffer. All parsing and traversal remain TypeScript. | Compare compaction inside the input buffer while preserving header slices until emission. Retain invalid-byte rejection, comments, CRLF/EOF, all symbols and complete60-column output. The separate D in-place experiment supplies a technique, not TypeScript qualification. |
| Spectral norm | Four required functions, scalar coefficient evaluation and forty dense products. Ordinary arrays begin as one-element `[N]` literals and grow; AtA creates a temporary vector on every call. | Compare three reused typed numeric vectors, then bounded persistent row workers. Keep separate coefficient/forward/transpose/composition functions, all coefficients and products, exact input/output state and final nine decimals. No cached matrix or native matrix/eigen solver. |

There is one retained source per workload. A single-source pool does not establish
an optimized or minimal implementation. Type declarations, actual constructor
bindings and worker orchestration are application source; multiline arguments
and genuine array expressions must not be expanded into invented scalar LOC.
Existing TypeScript native owner qualification should be extended with exact
new-source fixtures rather than replaced by delimiter counting. Formatted LOC,
retained units, logical units, bytes, gzip and BPE remain distinct measurements.

All original notices and cited predecessors remain unchanged. Current adaptations
are identified separately as Codex GPT-6-family edits, with the exact serving model
unknown; that does not establish predecessor authorship. No source, count,
eligibility, timing or endpoint in the canonical catalog is changed by this review.
