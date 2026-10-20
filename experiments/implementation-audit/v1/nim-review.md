# Nim implementation review — all ten workloads

Read-only static review, 2026-10-20. No Nim process, compilation, benchmark or canonical-data edit was performed. All20 inventory main-source hashes were recomputed and matched. Saved medians are historical candidate measurements, not new speed claims or proof of global optimality.

## Scope, provenance, and compiler configuration

Inventory classifies all20 profiles as derived/adapted and keeps original lineage unresolved. `archive/languages/nim/20261012/PROVENANCE.md` identifies community collections at def-/nim-benchmarksgame commit466e4b8dcc9d70a6e619c6145db92dbd4f921e63 and hanabi1224/Programming-Language-Benchmarks commitad18b203dd1769724f4eea94fc3ac1e99f6593e0, with repairs required for allocation, permutation order, RNG/CDF work, parsing, PBM bytes and dual extraction. These are references, not proof that every adapted line has been traced, and no AI/model author is inferred. Protect unchanged original upstream files; new candidates get new source/build lineage.

The saved build records use Nim2.2.12 C backend, Clang22.1.8, `-d:release --mm:orc --threads:on --parallelBuild:1`, skip user/parent/project configurations, explicit SDK14.4 and `-ffp-contract=off`. Actual build.stderr commands confirm `-O3 -fno-strict-aliasing -pthread`; sampled nbody/spectralnorm commands contain **no explicit** apple-m3 target, unlike the Futhark cohort. Do not infer a CPU default from host model. A controlled explicit `--passC:-mcpu=apple-m3`/link configuration and, separately, link-time optimization are legitimate unmeasured configurations. Pin actual compiler/link arguments/generated C and preserve all old samples. `release` enables optimization but does not disable every runtime check; `danger` does. Narrow hot-loop check removal requires index proofs and boundary validation, not a blanket unrecorded flag. [compiler guide](https://nim-lang.org/docs/nimc.html).

Reference evidence: `archive/languages/nim/20261012/qualification/private-v4/builds/nim-nbody-optimized/{build.json,build.stderr}` and private-v3 spectralnorm counterpart; per-workload full-v6 reports named in inventory. ORC/reference ownership and destruction matter for threads and maps; the compiler's ARC expansion diagnostics can separate remaining bookkeeping from algorithm costs. Pure BigInts is pinned at3b5a106b88ec1baa904a059a1430c8335d885075; optimized pi uses nim-gmp0.2.4 header declarations at4e9a6a05bfc274abd02a241f2d7c9162b2300191 and GMP6.3.0. Its generic `support/gmp_ops.nim` SHA-256 is `adad6363f378372c1f54b8382193a70c8e142565589bb2511ba6567838f8b3e4`. Regex uses pinned PCRE8.45. Standard library/runtime support stays distinct from authored workload helpers.

## binarytrees

- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/binarytrees/compact.nim`
  SHA-256 `b18267a6d540e24c1db7aa002f2cc486f108e852c8d38bc3e0340a4ddcd5fabc`; saved median 8.53756371 s; `binarytrees:nim-binarytrees-compact`.
- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/binarytrees/optimized.nim`
  SHA-256 `958a643758bdb20a52da17cf3365e882b747f8d6cb42d7f2f26e272a4f73366f`; saved median 1.71282467 s; `binarytrees:nim-binarytrees-optimized`.

Compact uses an ordinary two-child `ref object`; optimized adds `{.acyclic.}` and partitions each depth across up to8 native threads. Both allocate leaves with `new`, build before check and retain the long-lived tree. Saved8.538→1.713 s conflates parallelism and cycle-collector annotation, so their independent contributions remain unmeasured. Existing `source-proofs/orc-join-parent-destruction` evidence is relevant to the result/owner lifetime across joins.

Compare serial acyclic, threaded acyclic and a persistent bounded worker group separately. Unroll constructor and checker by two levels while allocating and following every node; inspect `--expandArc:make`/`check` output before manually changing ownership. Nim's memory-management manual specifically recommends acyclic annotation for cycle-free graphs. ARC versus ORC is a separate recorded runtime candidate, with equal lifetimes and cleanup, not a free reuse of existing samples. No arenas/custom pools, flat node arrays, shared leaves, multiplied checks, leaked temporary trees or native tree executor. The26-line make/check source is already idiomatic and expressive; collapsing declarations is not a performance improvement. [memory-management documentation](https://nim-lang.org/docs/mm.html).

## fannkuchredux

- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/fannkuchredux/compact.nim`
  SHA-256 `57cc5adf96e38204127c5069077da3608bf1cd5c40965e968c3e9c3c4c894fcc`; saved median 20.7791418 s; `fannkuchredux:nim-fannkuchredux-compact`.
- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/fannkuchredux/optimized.nim`
  SHA-256 `8fc3d7d48313f9d311232cc088e62796db6a21ef1fcfde4faec3d20ff070f053`; saved median 3.5549 s; `fannkuchredux:nim-fannkuchredux-optimized`.

Optimized keeps the same fixed12-int permutation/work arrays as compact, initializes each worker from a global factoradic rank, and divides all permutations into8 contiguous chunks. Parallelism yields20.779→3.555 s, but each iteration still copies96 bytes and performs scalar prefix swaps and rotation carry. Chunk count equals worker count, so flip-count variation cannot be dynamically balanced.

Test `array[12,uint8]` permutations/work and narrow rotation counters with explicit integer index conversion, plus skip the copy when the first element already requires zero flips. This is a zero-flip case, not permission to skip a nonzero flip sequence. Compare paired-permutation generation that specializes the frequent first-two rotation while retaining every reversal. Increase tasks to a bounded64/128/150 over8 persistent workers; use global rank parity and exact factoradic chunk seeds. The official description itself discusses small chunks for load balance. Retained Futhark's swap-based flip code is a useful comparison. Preserve n! canonical order/checksum, n<=12 safety, all prefix flips and maximum; never reuse a computed flip count for other permutations. A shared `run(first,last)` helper could also give a compact serial/parallel source without duplicate algorithm bodies.

## fasta

- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/fasta/compact.nim`
  SHA-256 `9cdf085f8ed7e9fbff81544f952fa8a2b97c95a4f8e1a59cf0206c89393f5693`; saved median 3.933227 s; `fasta:nim-fasta-compact`.
- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/fasta/optimized.nim`
  SHA-256 `e5d53da87433e210ca0a989ca67294483945b8700ea5e96fd1a5a8d573b085f4`; saved median 2.94848375 s; `fasta:nim-fasta-optimized`.

Optimized changes per-line growing strings into a reusable64KiB output buffer, removes per-base ALU modulo, and inlines `randomBase(openArray)`; saved3.933→2.948 s still includes a buffer-add/capacity check and linear CDF search for each base. It correctly retains the continuous seed and fresh double-CDF classification.

Compare a pre-sized byte/string block filled by index and written once, instead of `buffer.add` on every character; use a monotonically advanced ALU pointer and preformatted complete-line blocks. A `uint32` seed safely contains the specified LCG intermediate (below2^32), so compare its arithmetic against machine-int modulo while retaining every update and double division. For THREE use a four-way comparison tree; for IUB compare linear versus binary search of the same cumulative double probabilities. MATLAB/Futhark already separate state generation from block classification; test bounded blocks rather than cached RNG periods. Keep original probability accumulation order, all200M updates, exact250M bases and60-column partial lines. The present `randomBase` plus one generic writer remains a compact expressive basis; no integer cutoffs, jump-ahead skipped draws or precomputed random outputs.

## knucleotide

- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/knucleotide/compact.nim`
  SHA-256 `c9e05510b0d09ed88dea67ea5a7a478ad66d36f8e71186804c154b17d964bfbc`; saved median 31.1244445 s; `knucleotide:nim-knucleotide-compact`.
- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/knucleotide/optimized.nim`
  SHA-256 `9b5a250702745e4ade2bd0488444aa6a4c393c198da57be7fedd7bd8b04732a8`; saved median 3.58565342 s; `knucleotide:nim-knucleotide-optimized`.

Compact slices a newly owned string for every window and retains seven `Table[string,int64]` maps. Optimized rolls masked u64 keys and creates one native thread per width, saving31.124→3.586 s. The hot statement still performs `getOrDefault` followed by indexed assignment, requiring two public table operations per window; `code(value)` is repeated in seven scans. Input preparation also holds the whole file plus `splitLines` strings before building THREE.

The first idiomatic candidate is `table.mgetOrPut(key,0'i64).inc`, or `CountTable[uint64].inc(key)`, from a genuinely empty default-sized standard table. Nim's official API returns a mutable entry, preserving every lookup/update without a second lookup. Pre-encode THREE once to0..3, stream lines instead of splitting the entire file, and compare width-parallel scheduling to bounded start-position chunks with halos and smaller maps. Release unused long-width tables after extracting their query results if this can be done without unsafe cross-thread ownership; current code retains all seven through output. Every valid overlapping window must still enter a real standard/library hash map, including k=1,2. No dense count arrays, sort/reduce replacements, query-only matching, custom tables or input-sized reservation. Test token-boundary headers, comments, CRLF/EOF, N<k and ties. [std/tables mutable-entry and CountTable APIs](https://nim-lang.org/docs/tables.html).

## mandelbrot

- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/mandelbrot/compact.nim`
  SHA-256 `36f46c4bae43b0417c8f6e97f6378908fadf3d6686aa7a6e1fbb8f30bf393efb`; saved median 11.2086102 s; `mandelbrot:nim-mandelbrot-compact`.
- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/mandelbrot/optimized.nim`
  SHA-256 `bad5606dfb97cda62517c2b1c8a2a7c4040c5ee2ae0928cbd3e5333cddcfdd3d`; saved median 1.27290708 s; `mandelbrot:nim-mandelbrot-optimized`.

Compact renders scalar pixels with per-iteration escape; optimized handles8 lanes per output byte, checks all-dead after groups of5 iterations and splits contiguous rows across8 threads. Its11.209→1.273 s win already combines real arithmetic, batching and parallelism. Static middle-row assignment can be imbalanced; arrays of8 doubles are candidates for SIMD but the source alone does not prove vectorization.

Compare block-cyclic/dynamically scheduled row chunks and inspect generated assembly/vectorization diagnostics before adding intrinsics. Hoist real-coordinate vectors or initialize row-independent lane coordinates once per worker; compare two/four/eight lanes and group checks1/2/5. A sticky escaped mask makes semantic intent explicit when other lanes continue; guard NaN/Inf and ensure an escaped lane cannot be re-admitted. Retained Futhark quads are another valid representation. Preserve all pixels and requested tails, standard recurrence and50-iteration maximum, exact PBM bit order and padding. Do not add analytic interior tests, symmetry, reduced precision or global unsafe checks without proofs. Small N needs the current min(8,n) worker bound.

## nbody

- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/nbody/compact.nim`
  SHA-256 `1076b921d678c1111b6583205921ddbc785f44898f46bda4dae32231895539a2`; saved median 1.57207779 s; `nbody:nim-nbody-compact`.
- `archive/languages/nim/20261012/qualification/private-v4/source-snapshot/sources/nbody/optimized.nim`
  SHA-256 `1ad2422f87034c2d99cfd6bd41ebf394a56b1b31f2e79f26a9a295bc2aefd097`; saved median 1.52731479 s; `nbody:nim-nbody-optimized`.

Both candidates keep five `Body` records with scalar f64 fields and perform identical ordered symmetric pairs. Optimized merely marks advance/energy inline and copies current body values into `first/second` for positions/masses; medians1.572 and1.527 s are close. This is a narrow compiler-local comparison, not evidence that the representation is close to best.

Compare locally cached i-body velocity accumulators and writeback after its j loop (as in retained MATLAB), a structure-of-arrays representation, and explicit ten-pair scalarization (as in retained Futhark tuples). Keep only positions/masses cached across an interaction; do not reuse stale velocities when updating the second body. Inspect generated C for copies and aliasing, then assembly for vectorization and sqrt/divide scheduling. An explicit apple-m3 target is also an untested configuration here. Preserve double constants, momentum offset,50M sequential time steps, exact sqrt, pair/position update order and both energies. No reciprocal-sqrt approximation or parallel time stepping. The existing record-based `advance` is a clear compact formulation; shorten shared constants/data declarations only with semantic source accounting.

## pidigits

- `archive/languages/nim/20261012/qualification/private-v2/source-snapshot/sources/pidigits/compact.nim`
  SHA-256 `5c1ba8e2ec741f1586f53d9099168f41ed94184d482c6652ad347851cc4f66bd`; saved median 43.393406 s; `pidigits:nim-pidigits-compact`.
- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/pidigits/optimized.nim`
  SHA-256 `324208b9123f369bb21a509955a2d192752a315ae546e1aa515c260770217b12`; saved median 0.43350075 s; `pidigits:nim-pidigits-optimized`.

Compact uses pure `bigints` expression temporaries, constructs small constants repeatedly and writes each output line; optimized binds GMP operations, reuses eight mpz values, uses `addmulUi` and buffers output. The43.393→0.4335 s change is mainly an arithmetic-library/representation comparison, not merely Nim optimization. The support ABI shim is generic and separately pinned.

Compare a faster pure-bigint numerator/remainder path separately from a GMP candidate; do not attribute GMP's advantage to source layout. For GMP, derive numerator4 as numerator3+q while still doing both divisions, replace `mulUi(temporary,t,digit); sub(r,r,temporary)` with an existing generic `submulUi` binding if available, and compare an accepted advance-first state loop with the current extract-first loop. Retained C `pidigits-gcc-1.c` uses fused addmul/submul and an advance guard; any port must preserve dual extraction rather than infer the second digit. Constants and output buffers are small remaining opportunities. Keep arbitrary growing precision, single-thread sequencing, exact spacing and n=0/partial lines. A thin idiomatic operator wrapper over the same GMP calls is a compact alternative, with all authored workload helpers counted.

## regexredux

- `archive/languages/nim/20261012/qualification/private-v2/source-snapshot/sources/regexredux/compact.nim`
  SHA-256 `e9a20df433b5d2bfc6fd0f7393a454fa49b455cee4ae876d31348062da50647c`; saved median 6.40109383 s; `regexredux:nim-regexredux-compact`.
- `archive/languages/nim/20261012/qualification/private-v2/source-snapshot/sources/regexredux/optimized.nim`
  SHA-256 `ed5d8982939c9f1ddb3006a1079ca8fb3001a971c519fa82840edd6062540129`; saved median 2.99774146 s; `regexredux:nim-regexredux-optimized`.

Compact materializes every matched substring with `findAll(...).len`; optimized instead loops `findBounds` and counts, then runs8 threads for9 patterns. Its6.401→2.998 s improvement changes both allocation and parallelism. The last worker receives two patterns, a predictable imbalance. Five replacements remain serial and ordered; original input is kept for its byte length.

Compare serial findBounds to threaded findBounds independently, schedule the nine patterns from a bounded task queue, and pipeline one legal substitution job concurrently with count jobs while never mutating their shared input. Inspect the pinned std/re PCRE study/JIT configuration rather than assuming regex compilation enables JIT; a standard PCRE2 library binding is a separate runtime candidate, with only general regex calls exposed. Precompile each prescribed pattern once and avoid materializing match strings. The official std/re API provides both findAll and findBounds. Keep case-sensitive semantics matching the current reference, nine independent searches, non-overlap, regex cleaning and five ordered substitutions. Do not combine patterns or replace regex processing with hardcoded byte scanners. [std/re documentation](https://nim-lang.org/docs/re.html).

## revcomp

- `archive/languages/nim/20261012/qualification/private-v2/source-snapshot/sources/revcomp/compact.nim`
  SHA-256 `18a1bd6328dfc61660deb83d0bcecf80b71208a9f9f724dc5364c4cbce9cf016`; saved median 1.60283192 s; `revcomp:nim-revcomp-compact`.
- `archive/languages/nim/20261012/qualification/private-v2/source-snapshot/sources/revcomp/optimized.nim`
  SHA-256 `52d354d69bbcb3f0ca14165d4fcfe05b17ebdf341d01aa8edf0fecba70ba25af`; saved median 0.845321916 s; `revcomp:nim-revcomp-optimized`.

Compact maps bytes while appending to a string, reverses it, and allocates a slice per60-base write. Optimized delays complement until a two-ended in-place swap, buffers output, and saves1.603→0.845 s. It still calls `stdin.readAll().splitLines()` and allocates a60-character substring on each `buffer.add(sequence[start..<...])`.

Compare streaming `stdin.lines` per record and direct `writeBuffer`/indexed block filling to remove line-object and substring allocation while retaining headers/comments/EOF handling. For very large records, bounded disjoint pairs of indices can be processed by up to8 workers before ordered output; choose a size threshold so three small records do not pay thread startup. LUT construction can be a compile-time constant without caching any input-dependent result. MATLAB/Futhark's byte LUT and bounded wrap output are independent comparison designs. Preserve all IUPAC upper/lower complements, odd center handling, empty records, headers and exact60-column tails. Reject unrecognized input explicitly if broadening the accepted grammar; the current zero-filled LUT otherwise emits NUL for unknown bytes. Keep the compact iterator-based formulation as an expressive candidate.

## spectralnorm

- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/spectralnorm/compact.nim`
  SHA-256 `aa2cab891eb092dc8f5dce9633371f71dff89a506331c2a1d1fd160052ac3be8`; saved median 1.45084454 s; `spectralnorm:nim-spectralnorm-compact`.
- `archive/languages/nim/20261012/qualification/private-v3/source-snapshot/sources/spectralnorm/optimized.nim`
  SHA-256 `ae870f723c4588b274c1b5e4512419b0d9419170dac5305f34cf2556532a1319`; saved median 0.50442475 s; `spectralnorm:nim-spectralnorm-optimized`.

Optimized parallelizes rows but creates/joins up to8 threads on **each** of40 dense products, or320 creates per run. The1.451→0.5044 s comparison does not test persistent workers, SIMD or multi-row accumulators. Each inner iteration also branches on transpose and recomputes integer triangular arithmetic.

First compare a fixed8-worker group with barriers between products to the current thread-per-product design. Specialize normal/transposed row functions outside the hot j loop and compute two/four rows together to reuse input loads and independent accumulators, as retained Futhark/Mech implementations do. Keep denominators as integers until conversion/division; recompute every requested coefficient in every product. Any triangular recurrence/common algebra must preserve the mandated coefficient/multiply/transpose/composition functions and cannot cache A across iterations. Inspect generated C for bounds checks; if they remain, prove local loop bounds before any narrowly scoped removal, rather than silently use `-d:danger`. Keep40 products, n tails and stable numeric policy. A shared parameterized multiply helper can shorten source, but its transpose branch should be specialized before inner-loop execution.

## Review queue

Prioritize mutable-entry nucleotide updates/input preprocessing, persistent spectral workers, narrow fannkuch state/task balance, and row scheduling/vectorization for Mandelbrot. Isolate CPU-target flags and individual source changes rather than combine them into one unexplained optimized label. Preserve every old source, compiler loaded helper, sample and dependency pin. No proposed candidate was executed here.
