# Odin implementation source review

The [review](review.json) inspects thirteen retained local/derived source bundles
across nine workloads. Two unchanged upstream N-body programs remain protected;
this packet does not rewrite them or claim a fresh native review of them.
All findings are source hypotheses. No native process or new timing is produced,
and the frozen database-wide queue remains historical evidence.

The first executable-source candidate is
[spectral-norm scratch reuse](../spectral-scratch-v1/README.md). It retains the
known original implementation citation and MIT license. Unresolved original
lineage in other locally labelled programs is preserved explicitly; a workload
description is not promoted to an implementation citation.

| Workload | Existing technique | Alternatives and validation priorities |
| --- | --- | --- |
| Binary trees | Per-node construction and traversal in a standard arena; serial and eight-worker batches | Compare a persistent worker pool with per-depth thread creation, retaining every tree/node allocation and check. Verify per-worker arena lifetime and long-lived-tree retention. |
| Fannkuch | Reused fixed arrays and in-place prefix flips | Avoid copying the permutation when its first element is zero; consider complete permutation chunks for parallel execution. Retain all permutations, signed checksum and maximum flips. |
| FASTA | Buffered output, linear or binary cumulative-probability search | Compare bulk ALU slice copies with per-byte modulo and general distribution lookup alternatives. Preserve all RNG draws, exact state order, probabilities and row wrapping. |
| K-nucleotide | Numeric rolling keys, seven growable maps; serial and one worker per width | Compare indexed increment with the existing entry-pointer idiom after native lowering inspection; do not assume the compiler performs duplicate lookups. Preserve every full histogram. Audit exact THREE header tokens, comments and record boundaries before optimizing parsing. |
| Mandelbrot | Eight-element arithmetic, batched escape checks and full output buffer | Preserve requested dimensions and mask the final partial byte: current source rounds the requested size to a multiple of eight. Inspect native vector lowering before making SIMD claims; parallel rows remain a candidate. |
| Pi digits | Two-extraction GMP spigot with counted Odin FFI declarations | Keep general arithmetic leaves in GMP and complete spigot/control/output in Odin. Preserve both candidate extractions and all digit decisions; review arithmetic temporaries and ABI before measuring alternatives. |
| Regex-redux | Standard regex iterator or PCRE2 JIT FFI, repeated output-buffer construction | Compare independent count jobs and reusable replacement buffers with owned regex/match-data per worker. Retain all nine scans, five sequential substitutions, intermediate/final lengths and native library identities. |
| Reverse complement | In-place record compaction, a switch for complement and buffered 60-column output | Compare a general byte lookup and symmetric in-place transformation. Audit line-start markers, comments, header-only EOF and strict invalid-byte behavior. The current source's missing-newline path can leave the record offset unchanged; native confirmation is pending. |
| Spectral norm | Scalar matrix-vector loops with a temporary vector per AᵀA call | Reuse one scratch vector first. Outer-row parallelism can keep each inner reduction order; transposition specialization and generated code need separate inspection. |

The source-size audit includes all application declarations, imports, struct
fields, helpers and FFI declarations. One-line structs, semicolon-separated
statements and multiline probability/matrix literals need consistent owner
rules; neither manual reflow nor raw rows constitutes a native normalized count.
A pinned formatter/parser policy remains pending. Unknown values remain absent
instead of being presented as qualified counts.

Retained full-workload medians are reference points, not results from this source
review. Each ratio uses the cited historical Mech AOT profile on the same
workload/input. The exact source, samples, denominator and report references
remain in `review.json`.

| Retained Odin implementation | Seconds | × Mech AOT |
| --- | ---: | ---: |
| binarytrees-odin-arena-compact | 5.571199 | 14.13× |
| binarytrees-odin-arena-parallel | 1.073160 | 2.72× |
| fannkuchredux-odin-compact | 28.116074 | 16.51× |
| fasta-odin-binary | 0.746829 | 1.38× |
| fasta-odin-linear | 2.135921 | 3.95× |
| knucleotide-odin-growable-maps | 8.538036 | 16.62× |
| knucleotide-odin-parallel-entry | 2.093316 | 4.07× |
| mandelbrot-odin-1-faithful | 2.212999 | 5.00× |
| pidigits-odin-gmp | 0.550815 | 1.83× |
| regexredux-odin-jit-pcre2 | 1.895714 | 3.87× |
| regexredux-odin-stdlib | 25.701571 | 52.49× |
| revcomp-odin-compact | 0.384478 | 2.58× |
| spectralnorm-odin-1-faithful | 0.743546 | 8.64× |
