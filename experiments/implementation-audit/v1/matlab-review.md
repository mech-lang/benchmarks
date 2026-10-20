# MATLAB implementation review — all ten workloads

Read-only static review, 2026-10-20. No MATLAB process, compiler, benchmark or canonical-data edit was performed. Main-source hashes below were recomputed and matched the inventory. Saved medians describe distinct retained cohorts, not new paired evidence or global optimality. Candidate changes are hypotheses requiring work/correctness checks before measurement.

## Scope, runtime, and evidence limits

`inventory.json` classifies17 selected MATLAB profiles as suite-authored based on explicit local-origin assertions, with unresolved original lineage and no inferred AI/model authorship. The original20-source cohort contains three measured losing optimized attempts omitted from endpoint inventory; they are included below so a baseline win is not mistaken for a complete search. All upstream original submissions used as comparison evidence remain protected.

The pinned runtime is MATLAB R2026b26.2.0.3386108, native Apple Silicon, normal JIT, base MATLAB and up to8 automatic computation threads. `archive/comparisons/matlab-comparison/20261010/results/builds.json` pins launcher SHA-256 `6410f261f4a31011ef767412a3541f94e1900cec158951a5e400a6cd776d710f`, engine `ed2d96026421bb1f5d0deed46b1cfefa6011e8f5e7eef678675abe64ae0df764`, input launcher `matlab-stdin.sh` `a517cc4d3838fc6a44c8075fa044701a2f87aa8d9169cd19d67718ae6effb084`, Java JVM `c0c9cc842a9d33857be8262157d19ee9c1e15caf99a9bde784033b351b5dd117` and modules `384c6a1944553e693145640a486fd1c46382904b8512586f6a7926f27715a743`. Headless `-licmode onlinelicensing -nodisplay -batch` startup/licensing, first-use JIT, full I/O and teardown are included. Stdin is duplicated to fd3 before launch; Java is a task-local Temurin25.0.4.1 runtime. No MEX benchmark kernel, MATLAB Coder, GPU or Parallel Computing Toolbox is admitted.

Consequently `parfor`, GPU arrays, a MEX loop or a Java class running a complete benchmark would change the execution policy. Ordinary built-ins and scalar JIT code are the right first candidates. Diagnostic separation of startup/kernel costs must not replace the fresh-process metric. The20-source saved cohort has three full samples per candidate and controls, source/LOC audits and specialized tree allocation evidence; it has not explored a general search over idioms, tile sizes, data layout, numeric/library choices or all compiler/runtime settings. Corrected regex evidence and the nucleotide default-growth concern require explicit follow-up before performance claims.

## binarytrees

- `archive/comparisons/matlab-comparison/20261010/sources/binarytrees_compact.m`
  SHA-256 `0cc8469fc532bf963b10d2344ae0ca70236b435b627cfabbbea6e2cb58a24a89`; saved median 350.602683 s; `binarytrees:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/binarytrees_optimized.m`
  SHA-256 `5cdbc269335343bc82f1f669ae1ccf50194e8cc6a52ee67773a3656ccdcceec0`; saved median 424.852941 s; `binarytrees:matlab-optimized`.

Both constructors allocate a fresh two-slot cell for every interior and leaf. `check` recursively follows both children; stretch is cleared before long-lived construction, and the long-lived cell graph remains reachable. The optimized attempt unrolls construction by two levels, yet is slower (424.853 vs350.603 s). The existing even/odd allocation probes and `results/final-allocation-branches.json` are valuable work evidence; one losing unroll does not exhaust MATLAB representations.

Next candidates: keep the ordinary cell representation but unroll **traversal** by two levels while reading every actual child, and compare constructor depths1/2/3 independently rather than assume deeper unrolling helps. A small handle-class node with two child properties is an alternative ordinary allocation representation, with its class source counted, but it must receive a fresh identity and storage for every leaf and interior and pass the same allocation/lifetime diagnostic. These are allocation/call-overhead hypotheses, not measured improvements. Flat numeric arrays, shared empty leaves, caching a subtree check, and custom pools fail the admitted work. A recursive make/check pair remains the compact expressive endpoint; do not replace it merely to win a baseline comparison.

## fannkuchredux

- `archive/comparisons/matlab-comparison/20261010/sources/fannkuchredux_compact.m`
  SHA-256 `39d15406548ec73d9078c43b069b6f5de5ea563d743e6fc94c21606b2d47f8e3`; saved median 1428.71034 s; `fannkuchredux:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/fannkuchredux_optimized.m`
  SHA-256 `8acb719708775bd1726173f27771e6e63d04aaa225f4acf2dce4aff382222343`; saved median 68.4318907 s; `fannkuchredux:matlab-optimized`.

The compact source allocates/indexes reversed prefixes and evaluates `(-1)^rank` for every permutation; the faster source toggles a sign, swaps a prefix in place, and rotates with scalar assignments. The 1428.71→68.432 s saved improvement is substantial but still leaves `copy = p` immediately before destructive flips, potentially causing a fresh copy-on-write buffer for every nontrivial permutation.

Test a persistent work vector allocated once outside the outer loop and refill its n elements before each flip sequence, so the first mutation need not allocate a newly aliased permutation. Compare direct scalar refill with `work(:)=p`; inspect allocation behavior diagnostically. A second candidate batches a bounded number of permutations in columns and advances active flip lanes with logical masks, preserving every actual flip and global permutation parity. Nim's retained fixed arrays and Futhark's explicit in-place reversal supply concrete comparison designs. Compact code can keep scalar rotation and a sign toggle without index-vector creation. Never change permutation enumeration/checksum parity, omit n! entries, use a precomputed maximum, or substitute a flip-count shortcut.

## fasta

- `archive/comparisons/matlab-comparison/20261010/sources/fasta_compact.m`
  SHA-256 `929a6f552e47e3c4237466b266ebcc7df0b8a45c8335fbfe614550215e4429b2`; saved median 20.7080444 s; `fasta:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/fasta_optimized.m`
  SHA-256 `98ce9f7ad215d22b161b1b6500206c5778189812b8534a348ae044513036341d`; saved median 9.53895233 s; `fasta:matlab-optimized`.

The optimized source buffers60×16384 bases, generates every LCG state sequentially into a double vector, then classifies it with `discretize` and writes a61-row byte matrix. The 20.708→9.539 s comparison already tests meaningful I/O/classification changes. It still allocates a fresh random vector and wrapped output for each block, and repeats ALU modulo-index construction.

Compare block widths60×256/1024/4096/16384, reuse preallocated random/output buffers, and test `discretize(random,edges,letters)` to return mapped bytes directly rather than build bin indices followed by a gather. Verify output type and cost; MathWorks documents this values form and default left-inclusive bins, matching the source's `<cdf` rule. A scalar four-letter branch tree for THREE can be compared to `discretize`, while preserving original cumulative doubles and division for every draw. Keep the continuous seed across TWO/THREE, exact partial-line handling and all200M fresh updates. RNG-period caching, integer threshold substitution, or jumping to chunk seeds to avoid updates changes work. The existing block helper is already a concise expressive option. [discretize documentation](https://www.mathworks.com/help/matlab/ref/double.discretize.html).

## knucleotide

- `archive/comparisons/matlab-comparison/20261010/sources/knucleotide_compact.m`
  SHA-256 `f322d78633d9ce2cce9313d0ea57475e52d3d3edca159615e669a571ec0e5f13`; saved median 28.1140398 s; `knucleotide:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/knucleotide_optimized.m`
  SHA-256 `f6b2470325420e2693fffa5a7d8c27645f9ca9e44d2e7167188390b16d4f6009`; saved median 38.226065 s; `knucleotide:matlab-optimized`.

Both sources already construct packed double keys exactly through36 bits. Compact materializes all125M−k+1 words and prepopulates `dictionary(words,0)`, then performs every explicit counter update. Optimized reads selected lines into cells, starts an empty configured dictionary, and uses `isKey` plus indexing. Its saved38.226 s loses to compact28.114 s; the excluded dictionary API probe already compared fallback lookup, indexing and membership. Repeating that same two-way comparison is not a deep search.

**Admission question, not a catalog decision:** compact supplies the complete actual key set to the dictionary constructor before counting. The public task asks for growth from a small default size; no evidence here establishes that this input-sized constructor preserves that allocation behavior. It does not omit updates, but default growth needs independent review rather than equating extra work with parity. Use the empty-map source as the unambiguous application-level starting point; this review does not change catalog status. MathWorks confirms constructor duplicate keys overwrite prior values and scalar zero broadcasts to all supplied keys; bulk `counts(words)=counts(words)+1` would also overwrite duplicate entries, not accumulate them.

Concrete candidates: bounded key blocks with rolling/prefix-composition encoding, keep one ordinary growing dictionary through all blocks, compare numeric key types only after measuring conversion/storage, and inline the frame loop to test whether dictionary value passing adds copying. Output still needs full maps at all seven widths; `histcounts`, `accumarray`, sorting counts, query-only matching, full-key presizing and prepopulated bins cannot replace that work. Tiny sequences need nonnegative window counts; require exact THREE token boundaries/comments/CRLF/EOF. [dictionary semantics](https://www.mathworks.com/help/matlab/ref/dictionary.html), [task requirement](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html).

## mandelbrot

- `archive/comparisons/matlab-comparison/20261010/sources/mandelbrot_compact.m`
  SHA-256 `a25151b82cb0b010cbfba1ba63e9cbaa9955ba8192b9503a5dd298c3cf27c763`; saved median 39.2534942 s; `mandelbrot:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/mandelbrot_optimized.m`
  SHA-256 `28a6594978613aecec61760f2099c15730a27a173d91f4f0400c2ffc72db4711`; saved median 58.5097288 s; `mandelbrot:matlab-optimized`.

Compact performs50 complex-vector iterations on every row, keeps a sticky alive mask, and resets dead z values. The attempted optimized form compacts live indices inside32-row real/imaginary tiles and loses58.510 vs39.253 s: irregular gathers/scatters and repeated live-vector creation plausibly outweigh skipped recurrence work.

Compare a real/imaginary row kernel with cached `zr2/zi2`, a sticky mask and an all-dead early exit, then dense row tiles1/4/8/16/32 that keep all lanes instead of repeatedly compacting. Another valid design groups pixels into four/eight lanes, checks all-dead at short iteration intervals, and performs complete PBM tail masking; retained Nim/Futhark programs already use those group designs. Try dense masks versus live-index compaction across escape-heavy and interior-heavy rows, not only the canonical image. Keep all requested pixels, standard recurrence and50-iteration ceiling; no analytic cardioid/bulb membership, symmetry-generated pixels, periodicity shortcuts, or reduced precision. Preserve zero padding when N is not divisible by8. The complex-row source remains the compact expressive alternative until a better candidate is measured.

## nbody

- `archive/comparisons/matlab-comparison/20261010/sources/nbody_compact.m`
  SHA-256 `133b0f5ff697569e6b6639f1713d4c3cd6ca623917e8c3627eb5255a6725456f`; saved median 577.440907 s; `nbody:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/nbody_optimized.m`
  SHA-256 `dedbc68eb8c2522e3cfeb02e451821da2e34fa9a0c054822e3225cda9dc49044`; saved median 7.4072045 s; `nbody:matlab-optimized`.

The fast source replaces ten tiny pair-matrix allocations per step with separate x/y/z/vx/vy/vz arrays and scalar cached values for body i; that explains a real structural577.44→7.407 s improvement. All50M steps remain sequential, each with ten symmetric pairs and five position updates. The initialization and two energy calculations are ordinary array operations outside the hot loop.

Next compare a bounded explicit unroll of the ten pair interactions, using local scalar state and writing it back only as needed, against the current indexed scalar loop. Futhark's retained tuple representation demonstrates what such scalarization can achieve, but MATLAB helper-call/output-tuple overhead must be measured rather than assumed negligible. Independently compare cached body-count/mass constants and vector versus scalar position updates; the original matrix-pair baseline already warns that tiny-vector syntax can lose badly. Maintain pair order, exact sqrt and double arithmetic, source constants, momentum offset and both energies. Changing step size/order, approximating reciprocal sqrt, independent per-body force reductions or parallelizing sequential time steps needs a different numeric/work review. The present cached scalar loop is the strongest compact performance candidate in this cohort.

## pidigits

- `archive/comparisons/matlab-comparison/20261010/sources/pidigits_compact.m`
  SHA-256 `292c4aad088d3f2e8084e46bf20b0352e493f1cb4ba9a8d9998bc326a071d6dd`; saved median 14.9627343 s; `pidigits:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/pidigits_optimized.m`
  SHA-256 `ee5d6b95aeed42d4eee74e255a1c06aed04eecd731f14a9f90f762c89f4daf63`; saved median 13.9170371 s; `pidigits:matlab-optimized`.

Both sources use Java BigInteger through MATLAB and do both endpoint divisions. Optimized hoists3/4/10, reuses the small odd factor, and fills a ten-character line buffer; saved14.963→13.917 s is modest and not evidence that the arithmetic boundary is efficient. Repeated MATLAB↔Java calls, immutable temporary BigIntegers, and division dominate plausible costs more than a1000-line output stream.

Compare the accepted advance-first LFT arrangement used by retained C/Nim/Futhark sources, with the same dual extraction, and derive the second numerator as first-numerator+q while still performing its actual division. Hoist all genuinely invariant BigIntegers and pre-size output for final ten-column formatting. A standard mutable arbitrary-precision library binding could be a separate runtime configuration, but no MEX/Java helper may execute the entire spigot; under the current base-MATLAB/Java policy, keep algorithm steps in .m source. Do not cache digits, bound precision from N, parallelize the spigot, or infer extract(4) without its division. Test N=0/1/9/10/11 and final spaces. The31-line optimized program is already expressive; reducing lines without changing the Java call pattern is not a meaningful performance experiment.

## regexredux

- `archive/comparisons/matlab-comparison/20261010/sources/regexredux_compact.m`
  SHA-256 `cefbed6d631f9cb83da8a3dde423ec666678fd6aec98a4a942fddcf172fbd483`; saved median 31.8718414 s; `regexredux:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/regexredux_optimized.m`
  SHA-256 `0a6b33da5a01bd571fabe43ede4a5dcce6e8a9a5e6e0d36ad8e501e21985cd01`; saved median 31.6941158 s; `regexredux:matlab-optimized`.

**Existing correction takes priority.** Current inventory hashes still use `regexpi` for the nine searches and match only canonical lowercase DNA. The official published Python3 reference uses case-sensitive `findall`, and MathWorks distinguishes `regexp` from case-insensitive `regexpi`. A completed case-sensitive repair already exists at `archive/comparisons/matlab-comparison/20261012/regex-case-sensitive-v1/`: compact SHA-256 `d41b8687b3661174be4b7c58014f0cfaaf331f6a11024135cc5dc8a561bced99`, optimized `0a59dbb911fd4e4aaa0aac8edd7380c8d5c834f4f0f3338337850b7ee3ee0846`. Its `studies/full-v1/regexredux/report.json` records medians14.853161459 and14.901873791 s; qualification records uppercase/old-witness cases. These are separate saved cohorts, not interchangeable replacement samples; review reconciliation/admission before redundant new timing.

The old optimized variant merely frees raw input early/reuses the cleaned variable and gains little31.872→31.694 s. A code-specific new candidate is `count(dna,regexpPattern(pattern))` once per prescribed pattern, avoiding a match-index vector while using the ordinary regex engine. MathWorks documents regular-expression pattern objects and non-reuse of matched text in `count`; test exact non-overlap/case behavior. Retain regex-based cleaning and five ordered case-sensitive replacements, bytes/length semantics and one pattern at a time. Do not combine all nine into a benchmark matcher, lowercase the input, or shortcut substitutions to length arithmetic. [reference source](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/regexredux-python3-1.html), [regexp](https://www.mathworks.com/help/matlab/ref/regexp.html), [regexpPattern](https://www.mathworks.com/help/matlab/ref/regexppattern.html), [count](https://www.mathworks.com/help/matlab/ref/string.count.html).

## revcomp

- `archive/comparisons/matlab-comparison/20261010/sources/revcomp_compact.m`
  SHA-256 `7663f250329dcf7807f4860fa99e3ce54c35bacad89daaa9d16a0501f3ebe9e7`; saved median 15.4133436 s; `revcomp:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/revcomp_optimized.m`
  SHA-256 `598047d327f956e991e51c2b3b2ca649ef67f008f5d74951b0090b1874ebe259`; saved median 3.43763954 s; `revcomp:matlab-optimized`.

Compact creates a string per input line and issues one output call per60 bases; optimized reads bytes, uses a256-entry IUPAC lookup, filters CR/LF, and writes61×16384-byte blocks. Its15.413→3.438 s improvement already addresses the major representational overhead. It still holds the raw file, filtered sequence, reversal and mapped sequence at once, and recognizes every `>` byte rather than only line-start headers.

Compare processing one record at a time with a reusable byte buffer, fuse reverse selection with LUT lookup on bounded windows, and write headers/wrapped chunks without a whole-record complement temporary. Nim's in-place two-ended complement loop is a concrete alternative, although MATLAB's scalar per-character loop might be much slower than its present gather. For a concise option, retain byte-vector reverse/LUT plus the existing block formatter; do not return to readlines merely for shorter syntax. Validate long/unwrapped lines, missing final newline, CRLF, empty records, all upper/lower IUPAC symbols, exact60-column tails, and `>` inside non-header content if the accepted input grammar permits it. No hardcoded three-record assumption or header rewriting.

## spectralnorm

- `archive/comparisons/matlab-comparison/20261010/sources/spectralnorm_compact.m`
  SHA-256 `70a95adaf05139b83bc30f68583f000d2548f3c5643779ae81b8c5a5f25d6e44`; saved median 4.42162042 s; `spectralnorm:matlab-compact`.
- `archive/comparisons/matlab-comparison/20261010/sources/spectralnorm_optimized.m`
  SHA-256 `c8a384fd73173769e2f9f2a7d94cfac63aea8712fe58dfa2a7319c60f0dc1b7e`; saved median 3.21299492 s; `spectralnorm:matlab-optimized`.

Compact constructs/coefficient-multiplies one row at a time; optimized uses64-row coefficient blocks followed by matrix-vector multiplication, recreating coefficients in every one of40 dense products. The4.422→3.213 s gain tests one tiling point, not MATLAB's best tile/thread configuration. Every block also allocates denominator/coefficient arrays and invokes BLAS on a relatively small matrix.

Compare block sizes16/64/128/256/512 and permitted computation-thread counts1/2/4/8, keeping the startup-inclusive endpoint. Cache only index vectors and invariant triangular algebra, reuse output buffers, and test whether larger coefficient blocks amortize BLAS scheduling without excessive memory traffic. Keep separate coefficient, A×v, transpose×v and composition functions. Retained Futhark's four-row accumulator and Nim's row workers provide independent alternatives; they do not justify matrix caching. No persistent full A matrix reused across iterations, replacement eigensolver/BLAS power shortcut, fewer products, lower precision, or reassociation beyond the established numeric policy. The row-vector coefficient helper is the compact expressive endpoint; benchmark a shared multiply helper only if it preserves the four required functions.

## Review queue

First reconcile the already measured case-sensitive regex repair; then resolve nucleotide default growth, test persistent fannkuch work storage, dense real Mandelbrot masks, and spectral tile/thread choices. Tree representation/call costs and pi library boundaries deserve separate diagnostics. Preserve compact sources as expressive alternatives even when a larger candidate wins. No candidate above has been executed in this review.
