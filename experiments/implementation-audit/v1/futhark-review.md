# Futhark implementation review — all ten workload decisions

Read-only static review, 2026-10-20. No Futhark process, compilation, benchmark or canonical-data edit was performed. Inventory main-source hashes were recomputed and matched. Nine workloads have admitted profiles; binary-trees is explicitly unsupported. Additional retained losing/baseline attempts are included where relevant. Historical medians establish only which measured candidates won their saved cohort.

## Runtime, support, and evidence limits

Inventory classifies selected sources as derived/adapted, with local-port assertions and unresolved original lineage; no AI/model author is inferred. Protect unchanged original community sources. `archive/comparisons/additional-languages/20261009-full-suite/{README.md,source-audit.json,results/builds.json}` pins Futhark0.27.1 multicore CPU, compiler SHA-256 `5ee05389c9bc9a27bbb91b540f3e13caeae8db8c5e56282332913dd900796d5e`. Builds use `futhark multicore --library`, then LLVM22 `-O3 -mcpu=apple-m3 -ffp-contract=off`, ordinary math/pthread libraries, and a generic adapter that fixes8 runtime workers. The adapter reads all stdin, creates the runtime context, calls the Futhark entry and writes complete returned bytes; it contains no benchmark executor. Whole-process copies, context startup, output and cleanup are included.

Support is material: common formatting `stdlib/common.fut` SHA-256 `56b559f220977ddb2dfe2b6c4b847081fbba71bb181e9aaa5fac58cedbb3342d`; adapter `adapters/futhark.c` `0014598c2062c35c3e0ad2b527e8ce6f359dead2ab2b558bfd9c10b5828ebad9`; hash table `stdlib/hashmap.fut` `0c1b898695cbe779412defe8208936b59631d4689f2b0230175575e5fe6ddcbf`; byte regex `stdlib/regex.fut` `e2e210be516999df38defd6ee473d8b80746b66818e6de048d41d5670bacffe4`; pure signed integers `stdlib/bigint.fut` `6a1dd08fc56091a66d6e78a058a974ee5daeb028531c45659783c0503d853a50`; fast integers `stdlib/bigint-fast.fut` `7b13bc13bd760401d46db9dfb209c5ccb252b403de288dcc7dd3061a1e07708a`. All paths are under that cohort directory. Short application LOC excludes these separately inspectable libraries; it is not a count of all code written to enable the workload.

The [official performance documentation](https://futhark.readthedocs.io/en/stable/performance.html) explains that only explicit parallel constructs create parallel work, multicore nested parallelism has alternative scheduler-selected versions, and tiny arrays/reductions often benefit from scalar tuples. Uniqueness enables in-place updates; it does not prove allocation-free code or successful vectorization. CPU generated C/assembly, allocation traces and controlled shape changes are needed. GPU results or moving work into the C adapter would be different policies. Existing general regex/arithmetic/hash tests are useful correctness evidence but do not establish performance optimality or settle the custom-hash-table task conflict below.

## binarytrees

- `archive/comparisons/additional-languages/20261009-full-suite/snapshots/pre-allocation-audit/sources/binarytrees.fut`
  SHA-256 `f98ac786ef0c4fc89a29c40ff3ea6cf07ef68279672424a5b42787dae2c27a1e`; no admitted timing claimed; `rejected / archived attempt`.
- `archive/comparisons/additional-languages/20261009-full-suite/snapshots/pre-allocation-audit/sources/binarytrees-optimized.fut`
  SHA-256 `8000e9548221e5f87ee87fa616303b303e64ce0408c4c04a1f695e4d0cd6a068`; no admitted timing claimed; `rejected / archived attempt`.

No admitted Futhark profile exists in the inventory. The two archived attempts materialize a flat child-index array for every tree and traverse it; the optimized attempt narrows child indices to i32. `results/tree-work-audit.json` and source-audit unsupported metadata explicitly reject both because array construction does not perform the required separate heap/library-pool allocation per node. Opaque annotations that prevent hoisting do not supply those allocations.

Do not resurrect these sources as optimized endpoints or implement the tree algorithm in the C adapter. A new candidate requires a supported ordinary Futhark allocation/reference representation with evidence of every distinct equal-size interior/leaf allocation and required lifetimes. The reviewed0.27.1 runtime/model supplies no such admitted route in this cohort. A community array/tree container remains an array representation unless its actual allocation behavior meets the task; a package name does not settle it. Keep the workload explicitly unsupported while investigating, and compare other languages only over the nine genuinely shared tasks. Nim's ordinary reference nodes are a correct contrast, not a transferable Futhark trick.

## fannkuchredux

- `archive/comparisons/additional-languages/20261009-full-suite/sources/fannkuchredux.fut`
  SHA-256 `5189c4cc14658a14bc631ce9db54cc2a05df12ec11bcd965b2d3f36adfb094d6`; saved median 70.9893024 s; `fannkuchredux:futhark-fannkuchredux`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/fannkuchredux-optimized.fut`
  SHA-256 `6c66c90cfc679873ecfc1a125a55f7619f08951983e0bc6a09dbb50396b11b00`; saved median 5.63026321 s; `fannkuchredux:futhark-fannkuchredux-optimized`.

Default uses reverse/take/concatenate for flips and prefix rotation; optimized swaps elements and shifts in place. Saved70.989→5.630 s is a real representation improvement. Both map only8 worker-sized rank ranges, keep dynamic i64 arrays, copy the permutation for each flip sequence and initialize factoradic seeds with array rotations.

Compare64/128/150 work chunks over the same8 runtime workers to balance variable flip work, retaining global rank parity and exact chunk seeds. Compare narrower permutation values (u8/i32) and reuse a unique work array across iterations by explicit refill rather than allocate/free a fresh dynamic work array. A tiny fixed tuple can expose scalar registers, but its larger source cost and runtime-n handling must be recorded; do not hardcode n=12 as the only supported size. Keep every actual prefix reversal and all n! permutations; no cached flip counts. A shared work(first,last) function with a configurable task count is already a compact expressive structure. The official task discusses chunk scheduling, and Futhark's compiler only parallelizes explicit SOACs, so sequential loop changes alone do not create more workers.

## fasta

- `archive/comparisons/additional-languages/20261009-full-suite/sources/fasta-compact.fut`
  SHA-256 `1c55d5e56aca8c5cd0c984e1691cd37137a9763a153d725983f55af03f23518a`; saved median 2.13692117 s; `fasta:futhark-fasta-compact`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/fasta-optimized.fut`
  SHA-256 `18c0a10f25017766f56fd896f92abfde786f95f9ce20390fc6c70a9582162370`; saved median 0.984710375 s; `fasta:futhark-fasta-optimized`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/fasta.fut`
  SHA-256 `cc63dba4a1cbc95e327288bf28846ca31e032d294abc76d37266a92405fefcb0`; saved median 2.35648375 s; `fasta:futhark-fasta`.

Compact builds bytes serially during fresh LCG/CDF work; optimized stores every state as u32 in a serial loop, then parallel-maps floating CDF selection and wrapping. Saved2.137→0.9847 s already exploits that division of work. The older direct-wrapped default is2.356 s and is a distinct retained attempt. The optimized source still holds a whole-record state vector (up to500MB for THREE), its byte vector, wrapped record and final concatenated output.

Test bounded state blocks inside Futhark, write mapped/wrapped bytes directly into one final output array, and reuse a unique state buffer while preserving every LCG update and the continuous TWO→THREE seed. Tune block sizes and keep the C adapter generic; host-side chunk-seed computation or a host FASTA generator would move algorithm work out of language. Compare straight CDF comparisons for the four-symbol distribution to the current search loop, without integer thresholds. For the ALU record, directly construct wrapped output from modulo positions as the older source does, rather than allocate an unwrapped array first. No RNG-period reuse, jump-ahead skipped draws, affine-prefix replacement of required sequential updates, reduced bases or cached output. `random_record` plus common `wrap` remains the compact expressive option.

## knucleotide

- `archive/comparisons/additional-languages/20261009-full-suite/sources/knucleotide-compact.fut`
  SHA-256 `83dda7809af2c2884e0e977d3a90ad11b6c04f63593aa2860d1f9ed29090b06c`; saved median 29.0691723 s; `knucleotide:futhark-knucleotide-compact`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/knucleotide-optimized.fut`
  SHA-256 `86279a96aff35f6dc90a7ffff727c33cf9da642e647856e341139836aea97dc6`; saved median 9.04021937 s; `knucleotide:futhark-knucleotide-optimized`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/knucleotide.fut`
  SHA-256 `089ef1d8565758568fd66c3f3e32b187f62061ec582a7e2b602c66e3dafaa4e5`; saved median 16.7053486 s; `knucleotide:futhark-knucleotide`.

All three retained sources roll u64 keys and perform all seven complete passes. Default partitions32 ranges with separate get/put; compact uses one growing map per width and `increment`; optimized uses32 range maps plus `reserve` batches of1024 and fixed-shape `increment_slots`. Saved29.069/16.705/9.040 s compares substantial shapes, but not a broadly established library backend. Parsing is also fragile: substring search is not a header-token match; compact/optimized stop at any `>` byte; the older default consumes all records after THREE; tiny/absent sequences can make negative limits/slices. Repair those before admission of new variants.

**Admission question, not a catalog decision:** Does the locally authored generic `stdlib/hashmap.fut` qualify as a library table under the current Game ban on implementing a custom table? This file implements open-addressed SplitMix hashing itself. The local audit treats generic reusable support as sufficient, but supplies no independent established library provenance. Correct growth/update counts do not settle that interpretation. No status change follows from this review. An independently maintained package, such as DIKU's containers map modules, is a concrete alternative to investigate and pin; verify actual mutable accumulation and default growth before claiming compatibility.

Conditional on an admitted library, tune8/16/32/64 partitions, reserve batches0/64/256/1024, and compare per-width versus per-chunk scheduling. Reserving1024 potential new keys grossly overallocates tiny alphabets; preserve every individual update rather than substituting `reduce_by_index`, sorting, dense bins or wanted-only counts. Keep36-bit keys and32/64-bit counts, default-size growth and exact ties. [official rule](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html), [independent Futhark containers package](https://github.com/diku-dk/containers).

## mandelbrot

- `archive/comparisons/additional-languages/20261009-full-suite/sources/mandelbrot.fut`
  SHA-256 `8547b78195437f90dc4891e208bad4c8e4c907879754fbf7739cb8a4cee4d6b0`; saved median 2.11141962 s; `mandelbrot:futhark-mandelbrot`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/mandelbrot-optimized.fut`
  SHA-256 `916bf3f136b0d2444382082acd3580ce8b74e33abea81de5cebdb78b88732765`; saved median 0.890895916 s; `mandelbrot:futhark-mandelbrot-optimized`.

Default maps output bytes and runs8 separate scalar escape loops per byte; optimized computes two four-lane tuple recurrences, with a sticky four-bit mask, saving2.111→0.8909 s. This is idiomatic small-state scalarization, not a proof that the multicore compiler emits optimal vector instructions. Output-byte maps already provide many scheduling tasks.

Compare two/four/eight lanes and short unroll/check intervals while preserving the same sticky mask and50-step ceiling. Hoist/reuse row imaginary coordinates and x coordinates in row/block maps only if generated-code inspection shows the compiler does not already do so. Compare outer maps over rows, byte tiles and flat bytes to expose efficient grain sizes; retain tail masks for every N. Futhark performance docs specifically warn about tiny array reductions and recommend tuples for small state, supporting the current direction. No analytic interior/symmetry/periodicity shortcuts or precision reduction. The scalar `inside` definition remains a concise readable alternative; helper tuples plus pointwise operations are expressive enough without converting the entire image to a giant nested while loop.

## nbody

- `archive/comparisons/additional-languages/20261009-full-suite/sources/nbody.fut`
  SHA-256 `acb4b2efced80f24056cf317aecf6d15b1763024736cbd1d276fb73d3f5d4a6a`; saved median 34.7639043 s; `nbody:futhark-nbody`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/nbody-optimized.fut`
  SHA-256 `753c0eb6e2506436f155022591d76b5d247aef6b2124498e8bf489ca4b3f7125`; saved median 1.07908233 s; `nbody:futhark-nbody-optimized`.

Default operates on a[5][7]f64 array with tiny map/reduce temporaries inside pair loops; optimized uses nested scalar tuples, explicitly lists all ten symmetric interactions, and updates five positions. The34.764→1.079 s improvement follows the official small-array/tuple guidance and exposes the time loop as a scalar dependency chain. Both energies remain outside that loop.

Next inspect generated C/assembly to confirm pair/position helpers inline and state stays in scalar registers. Compare tuple-of-seven-fields to seven fixed five-tuples or a record with named scalar fields; benchmark whether cached mass products/magnitude scheduling can shorten the dependency chain without changing pair order. A compact macro/module helper is valid only if its generated source/accounting stays inspectable; do not return to tiny parallel reductions just to reduce visible lines. Keep50M sequential steps, exact sqrt, original constants, momentum offset, both energies and all ten pair/five position operations. No GPU/native host executor or parallel time stepping. The optimized tuple source is already a substantive idiomatic alternative; new work should improve its actual scheduling/register behavior, not merely replay the slow array baseline.

## pidigits

- `archive/comparisons/additional-languages/20261009-full-suite/sources/pidigits-optimized.fut`
  SHA-256 `724e938fc9837346d2721f28119aafd3e783815b0f857d48b144d1731ae3e363`; saved median 2.91706642 s; `pidigits:futhark-pidigits-optimized`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/pidigits.fut`
  SHA-256 `e01ba1ef73392dca5a087d46f0f0c6f173ba72cb12ae8856744d43288a277d25`; saved median 4.11374042 s; `pidigits:futhark-pidigits`.

Main programs are nearly identical; the4.114→2.917 s improvement comes from `bigint-fast.fut`'s corrected leading-limb estimate for a one-limb quotient, with exact correction and general long-division fallback. Support stores signed arbitrary-length little-endian u32 limbs. Both endpoint extractions remain real divisions, after an advance guard also present in the retained C source. The23-line application alone does not describe the cost/complexity of the100+line library.

Compare numerator4= numerator3+q while keeping its quotient, add a generic fused small-multiply/add and subtract-multiply operation to reduce limb temporaries, and avoid allocating `add_abs(product,divisor)` merely to decide whether correction is needed. A reusable capacity-plus-used-length unique limb buffer may reduce repeated replicate/take/normalize allocation while still growing without an N-derived precision bound. Validate signed arithmetic, aliases, carry/borrow chains, divisor boundaries and large quotients through the existing independent library tests before spigot timing. Do not replace dual extraction, use fixed-size precision, table digits or move the spigot into C. A common formatting helper can simplify lines but must not hide workload arithmetic. GMP in Nim is a separate library comparison, not evidence that pure Futhark's remaining work is language overhead.

## regexredux

- `archive/comparisons/additional-languages/20261009-full-suite/sources/regexredux.fut`
  SHA-256 `a3643da919031ec8e0277afe58d2c7ab77e8aa7c72c3e9761e2de219a6392203`; saved median 2.62034725 s; `regexredux:futhark-regexredux`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/regexredux-compact.fut`
  SHA-256 `3cd6d69e2b47f68249c7ce0281819b3568553e6bb924ca1830464f5a40f34cd1`; saved median 2.62701487 s; `regexredux:futhark-regexredux-compact`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/regexredux-optimized.fut`
  SHA-256 `3d40dec6a287d4bd8dd802ee7e3f8c21afe75445d88e0f0bc7229adfdd33365d`; saved median 2.64180992 s; `regexredux:futhark-regexredux-optimized`.

Three retained forms perform the same nine searches/five substitutions. The attempted parallel pattern map is slightly slower2.642 s than the prior2.620 s default; compact2.627 s differs mostly in text construction. Underneath, the general byte-regex library parallel-maps a boolean match at every start for fixed-width alternatives, then serially selects non-overlapping matches. Each replacement allocates a worst-case `length+(length+1)*replacement_length` buffer and scans/moves text serially.

Concrete library candidates: bounded fixed-width matching blocks with the proper width−1 halo, parallel block summaries composed with exact non-overlap state; a reusable growable output buffer or exact-size two-pass generic replacement instead of repeated worst-case allocations; and compile-once regex values outside text-construction loops. Every change must remain a general regex operation tested on unrelated patterns, not recognize these nine literals or derive final lengths without replacements. Parallelize independent pattern jobs without multiplying large per-pattern temporaries beyond memory limits; profile counts versus replacements before choosing where to spend effort. Preserve one prescribed pattern at a time, byte/case semantics, alternative priority, greedy quantifiers, non-overlap, zero-length progress, cleaning and five ordered substitutions. No combined benchmark matcher or native host regex executor under this language-source policy.

## revcomp

- `archive/comparisons/additional-languages/20261009-full-suite/sources/revcomp-compact.fut`
  SHA-256 `e5794e32b3f625af40e83e68fc890baaa4866747d5d71bf718b8ede7b5cd7106`; saved median 0.6504365 s; `revcomp:futhark-revcomp-compact`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/revcomp-optimized.fut`
  SHA-256 `0fce51daead5923b094bb1f2282c2ff7dbeae76457d11a37eea78a514dc96cae`; saved median 0.392229083 s; `revcomp:futhark-revcomp-optimized`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/revcomp.fut`
  SHA-256 `e935b10ec4e24335c0c1802586221dc8e8e623e2b14a5a8fa2626ae5694ff710`; saved median 0.809018834 s; `revcomp:futhark-revcomp`.

Optimized builds a256-byte complement LUT and exact output offsets; default calls a linear scan through32 symbols per base, while compact repeatedly concatenates record output. Saved0.809/0.650→0.392 s demonstrates meaningful gains. Optimized still scans each record to count non-newline bytes, scans/filters again to materialize a reversed sequence, and then maps to wrapped output; records are processed sequentially because their clean lengths are irregular.

Compare one pass creating compacted byte positions plus per-record prefix counts, then direct reverse/LUT gathers into final output, or bounded per-record byte blocks to reduce simultaneous copies. Avoid materializing both reversed bytes and complements when one gather can combine them. A generic segmented flattening approach can parallelize records/chunks while preserving exact output offsets, but its extra scans/metadata need measurement. Fix header-without-final-LF bounds and explicitly define comments/empty-record behavior; existing code recognizes line-start headers and removes CR/LF. Keep all IUPAC mapping, untouched header bytes,60-column output and tails. Common wrap plus reverse/map is the compact expressive alternative; do not hardcode three records or assume60-column input.

## spectralnorm

- `archive/comparisons/additional-languages/20261009-full-suite/sources/spectralnorm.fut`
  SHA-256 `a1a180bd455baba4a8627d47250c7c91f2f7b5679bb7f6ffa86e7c14e1d8c661`; saved median 0.234290791 s; `spectralnorm:futhark-spectralnorm`.
- `archive/comparisons/additional-languages/20261009-full-suite/sources/spectralnorm-optimized.fut`
  SHA-256 `6a6c6cf422da41079e8b10db8dc322409d98def979d9ab2edf594e0d608a2d4d`; saved median 0.218352875 s; `spectralnorm:futhark-spectralnorm-optimized`.

Default has nested map/reduce for rows and columns; optimized maps four-row tiles, uses four scalar accumulators in a sequential inner j loop, and truncates the final tile. The0.2343→0.2184 s difference is small, so tuple tiling is not a settled best design and timing variation matters. Extra i>=n coefficient evaluations in the last tile are harmless work, not permission to skip requested rows.

Compare two/four/eight-row tuples, sequential j loops versus parallel chunk reductions, and row/tile granularity under the same eight-worker runtime. Hoist index/transpose selection outside the inner loop and reuse input loads while recomputing all coefficients in all40 products; inspect generated C for integer division strength reduction, vectorization and bounds checks. Futhark's multicore scheduler chooses among nested parallel code versions, so source-level map nesting is not sufficient performance evidence. No cached A matrix, fewer power iterations, replacement eigen-solver or changed precision. Maintain coefficient, av, atv and composition procedures and exact tail handling. The16-line map/reduce version is the compact expressive endpoint; compare a shared specialized multiply helper before adding extensive tuple boilerplate.

## Review queue

First resolve k-nucleotide library admissibility and parsing, keep binary-trees unsupported, then test bounded FASTA memory, fannkuch task/state shapes and general regex replacement allocation. Scalar n-body and four-lane Mandelbrot are already meaningful optimized designs; demand generated-code/new-candidate evidence before claiming further gains. No proposed candidate was executed here.
