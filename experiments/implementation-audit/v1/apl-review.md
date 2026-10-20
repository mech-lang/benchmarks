# GNU APL: complete retained-source review

Source-only review of all **19 retained APL profile labels across ten workloads**.
The n-body, fannkuch and binary-tree optimized labels alias the corresponding
compact source/timings; these are not independent optimization designs. All
sixteen distinct main application files and the binary-tree setup file were
inspected. Exact hashes, source paths, ownership assertions and saved pool
comparisons are indexed in [inventory.json](inventory.json) and the
[source bundles](../../../programs/apl/). No APL process, benchmark, compiler or
browser was started, and no source/count/timing was changed.

The recorded runtime is native ARM64 GNU APL 2.0, interpreted, with **serial
numerical primitives on the recorded macOS build**. A recorded `--cc 8` ceiling
does not establish eight parallel application workers or parallel primitives.
The [retained runtime review](../../apl/retained-native-v1/runtime-publication-scope-review-v1.json)
qualifies the recorded launcher/runtime and declared dependencies, with explicit
limits on inherited environment and per-process loaded-image coverage. Ports
assert local authorship in retained source/manifests; the catalog's
`local-origin-unverified` authorship labels do not establish an original author
or AI model. Preserve that distinction and the cross-language references.

| Workload and every retained ID | What is actually implemented | Concrete candidate / acceptance work |
| --- | --- | --- |
| N-body: `nbody-apl-compact-canonical-v2`, `nbody-apl-optimized-canonical-v2` | One 32-unit source, with ten unordered pairs, five-by-three position/velocity arrays, a precomputed mass/incidence matrix, and ten pair differences per step. `V←V+T+.×F` is already compact array math. The 293.48 s median is shared by aliases. | Keep ten pairs and all dependent time steps. Compare smaller temporary sets, indexed pair accumulation versus the tiny matrix product, and supported runtime primitive configurations in isolated variants. Current source already vectorizes the pair work; calling that a new optimization would be inaccurate. Check momentum, exact square-root law, both energies and arithmetic-order effects. No time-step parallelism or approximate reciprocal shortcut. |
| Mandelbrot: `mandelbrot-apl-compact`, `mandelbrot-apl-active-v2-compact`, `mandelbrot-apl-active-v2-optimized` | Original carries a full row and masks escaped lanes (1503.52 s). Active compact compresses indices and z arrays as pixels escape (649.46 s). Active optimized batches sixteen rows, also with stable live-index compression (660.30 s). All recurrence and PBM packing remain APL. | Active-set compaction is already present and the sixteen-row candidate is already slightly slower. Compare bounded tile sizes and compact/scatter allocation volume, with the same z0, up-to-50 iterations, squared-radius test, row order and padding. Do not introduce symmetry, known-interior tests or fixed-input escape tables. |
| K-nucleotide: `knucleotide-apl-v2-compact`, `knucleotide-apl-v2-optimized` | Both stream 64 KiB chunks, retain k−1 carry codes, and keep seven independently growing open-addressed maps through output. Compact rolls integer keys and calls `MapAdd` for each window (3912.67 s). Optimized forms every key with arrays, sorts/combines duplicate incoming keys and batch-probes/scatters exact accumulated amounts (768.13 s). This is a materially different dictionary operation trace, discussed below. | Resolve the historical batching/per-key-work policy before treating the two as equivalent prescribed work. For strict per-window dictionary updates, retain compact's update event trace while batching only key construction; review single-key generic map interfaces and bounded source-owned workers separately. The six-character target-header storage also needs the exact-token fixtures below. Keep seven widths, collision/growth semantics and complete map populations. |
| Spectral norm: `spectralnorm-apl-compact`, `spectralnorm-apl-optimized` | Compact computes one coefficient row per call; optimized computes blocks of 64 rows and uses `A+.×U`. Forty dense A/transpose products are retained; no matrix is cached between products. Optimized is already the measured winner, 73.94 s versus 95.64 s. | Tune bounded row blocks and temporary K/A arrays, and compare supported primitive parallelism as a runtime variant. Preserve coefficient recomputation for every product, both transpose modes and forty passes. Keep concise outer products/reductions as expressions; scalarizing their source would not be a fair size metric. |
| Reverse complement: `revcomp-apl-v2-compact`, `revcomp-apl-v2-optimized` | Both spool each record to an ordinary scratch file, then seek backwards in 245,760-byte blocks, complement with a complete both-case alphabet including U, and bulk-wrap output. Compact parses physical lines/chunks (39.91 s); optimized scans bounded chunks for record/comment lines (24.31 s). This is already a bounded-memory design, not whole-input retention. | Compare scratch I/O costs with bounded record storage choices only under the same input policy. Check scratch-file lifecycle, final header without LF, CRLF, comments across block boundaries, empty records and output order. Reusing a general scratch handle is not a native reverse-complement executor. Do not claim that ordinary in-place record reversal is an untried design without comparing its higher record-memory requirement. |
| Fannkuch-redux: `fannkuchredux-apl-compact`, `fannkuchredux-apl-optimized` | Both labels share one scalar label/branch permutation enumerator. Each permutation is copied into `Copy`; each actual flip gathers and reverses the prefix. It tracks all ranks, checksum and maximum, with a shared 7813.68 s median. The two labels show one retained strategy. | A bounded array-of-permutations candidate with factoradic rank initialization, per-lane active flip state and full actual reversals is a genuine idiomatic alternative. Compare bounded independent rank jobs and copy/reversal volume. Preserve all 479,001,600 permutations, checksum signs and each flip; no closed-form flip counts or precomputed permutation results. Memory must remain bounded rather than materializing n! states. |
| FASTA: `fasta-apl-compact`, `fasta-apl-affine-hoisted-optimized-v3` | Compact advances the LCG one state at a time and emits 60-character lines (332.74 s). Optimized precomputes generic affine-prefix coefficients for 60,000 positions, materializes each chunk's states from its current seed, divides every value by 139968.0, compares the original unscaled CDF, and bulk-wraps output (38.80 s). It already uses the important batching alternative, without a generator-period/output cache. | Preserve the retained [affine-prefix work decision](../../../archive/comparisons/r-apl-uiua-comparison/20261011/apl-fasta-v3/manifest.json). Compare chunk sizes, CDF comparison temporaries and bulk output conversions. Do not propose affine generation as new work or silently replace it by integer-threshold or period-cached draws. Retain exact inter-record seed state and every output base. |
| Binary trees: `apl-workspace200-compact`, `apl-workspace200-optimized` | One unchanged recursive source plus a counted one-line workspace-limit setup. Each call builds a fresh marker/left/right node; leaves and branches have the same three-cell shape. Stretch is released before the long-lived root, and repeated trees are actually built/checked. The later retained cohort completes at 1239.68 s; original workspace failures remain historical failures. | Review a genuinely fresh two-slot nested pair representation and ordinary bounded independent iteration jobs, with identity/size/lifetime witnesses for the new source. Do not flatten trees, share leaf nodes, reuse an arena in place of required fresh allocations, or substitute the arithmetic node-count formula. The [workspace setup/source review](../../apl/binarytrees-workspace-v1/source-counts-v1/README.md) counts 40 tree owners plus one setup unit; increasing a limit is a runtime configuration change, not evidence that the allocation problem vanished. |
| Regex-redux: `regexredux-apl-v3-optimized` | APL owns input reading, cleanup, the nine independent pattern traversals, five ordered substitutions and length output. General PCRE2 count/substitution modules request ordinary JIT and carry no benchmark patterns. The count module retains one match frame and does not materialize all matches. Median 14.45 s. | `Read` repeatedly concatenates the accumulated character input; compare a bounded chunk list followed by one join, and general stable-byte-buffer/regex interfaces that avoid converting/copying the whole APL subject for each pattern. Keep arbitrary-pattern primitives generic and the entire nine-pattern/five-substitution orchestration visible in APL. Do not fuse the benchmark into a native helper. |
| Pi digits: `pidigits-apl-compact` | The APL spigot reuses six generic GMP cells and controls every q/r/t transition and both real extract(3)/extract(4) divisions; output/padding and cell release remain APL. Median 0.922 s. General native code supplies ordinary arithmetic and opaque-handle lifetime only. | Reused cells are already present. Compare ordinary generic add-multiply/multiply-by-small-integer APIs to reduce wrapper crossings, keeping both explicit extractions, unbounded arithmetic and all source-controlled consume/produce decisions. A native digit generator or benchmark-specific extract/transition executor would cross the source boundary. |

## Two correctness/work questions need explicit disposition

The [historical nucleotide manifest](../../../archive/comparisons/r-apl-uiua-comparison/20261011/apl-knucleotide-v2/manifest.json)
and [README](../../../archive/comparisons/r-apl-uiua-comparison/20261011/apl-knucleotide-v2/README.md)
explicitly approve grading incoming keys, combining equal-key amounts and
batch-probing. In optimized `AddBatch`, lines 18–25 sort and aggregate duplicate
keys before updating the persistent maps. Thus it counts every overlapping
window's contribution but does **not** perform a distinct dictionary lookup/update
for every window. That historical approval and the primary Game's per-key hash
work requirement are an **unresolved eligibility-policy conflict for this owned
variant**. Complete output and seven complete maps do not settle the operation
trace question. Preserve the saved result and admission evidence while resolving
the policy; do not describe its work as equivalent to BQN's explicitly required
874,999,961 individual window updates, and do not invalidate unchanged upstream
submissions by analogy.

Both nucleotide sources also clamp the accumulated header to six characters
(`Header←(6⌊⍴...)↑...`) before `Selected←Header≡'>THREE'`. Consequently `>THREEX`
and `>THREE` are indistinguishable to this recognizer. The equality operation
does not establish an exact header token once the delimiter was discarded.
Add exact-target/misleading-prefix, description/whitespace, absent/empty target,
unterminated target and chunk-boundary fixtures to a separate candidate review.
The saved chunk/collision/adversarial evidence remains useful, but it must not
be cited as proof of an untested token distinction. No fresh failing APL run was
made in this source audit.

## Runtime/library boundary and source expressiveness

The [general launcher](../../../archive/comparisons/r-apl-uiua-comparison/20261011/run-apl.sh)
redirects normal application output to descriptor 3 and interpreter diagnostics
to stderr. It contains no workload loop. Generic
[GMP bindings](../../../archive/comparisons/r-apl-uiua-comparison/20261011/support/apl/gmp-native.cpp),
[regex substitution](../../../archive/comparisons/r-apl-uiua-comparison/20261011/support/apl/regex-native.cpp)
and [count-only matching](../../../archive/comparisons/r-apl-uiua-comparison/20261011/apl-regex-v3/support/regex-count.cpp)
are retained dependency/support implementations. Their arbitrary operands,
patterns and subjects are supplied by APL; the reviewed files contain no
workload recognizer, pattern list, RNG, tree/permutation loop or pi spigot.
Application call sites, parsing, constants and sequencing stay counted.

The generic-looking nucleotide map implementation remains inside counted
application files under the current review. A future reusable-library partition
could be considered only after an explicit content/API review and qualified
counts; naming it a library cannot remove the required application work. That
distinction matters when other languages call installed generic maps whose
implementations are outside application LOC. Authored library size should remain
separately visible if a reusable general APL map is introduced.

APL's reductions, scans, indexing, outer/inner products, array construction and
pure dfns are legitimate compact expressions. Matrix rows and header-local names
must not become invented executable units. Conversely, diamonds or independent
assignments need native/exact-source ownership. Retained APL owner evidence is
hash-specific and charges written `∇` closers; the new Python/Julia logical rule
does not. No universal logical ranking or qualified formatter is supplied for
APL by this audit. Use the exact application/submitted byte, gzip and pinned BPE
metrics as complementary views with their Unicode/tokenizer biases disclosed.
