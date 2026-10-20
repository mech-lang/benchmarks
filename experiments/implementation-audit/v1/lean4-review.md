# Lean4 implementation review — all ten workloads

Source-only review, 2026-10-20, covering all23 retained Lean4 profiles and their
exact application/support sources. No Lean process, compiler, benchmark,
formatter, count-tool execution or canonical-data edit was performed for this
review. Historical medians below describe the existing pool, not new matched
comparisons or proof that an implementation is optimal. The separate
[source-review binding proposal](lean4-source-review-proposal.json) records the
source hashes, roles and evidence scope; it is not a new admission or count proof.

The most consequential finding is that both suite-authored k-nucleotide
applications omit the required library hash-table work. Their dense short-key
counters and query-only long-key scans warrant the separate
[exact-source eligibility correction](../../lean4/library-map-review-v1/README.md).
Their correct historical outputs and timings remain evidence, with current
eligible coverage now9/10 and all23 historical profiles retained. Several other “optimized” profiles retain
the same algorithm as their native predecessor; their names do not establish
that a substantive source optimization occurred.

## Source, runtime and measurement boundaries

The pool contains10 native applications,10 optimized applications and3 additional
compact applications. There are69 recorded whole-process observations. All23
application hashes differ; no timing alias is recorded. The source review does
not turn similar algorithms into additional independent observations. Binary
trees is adapted from the official Lean benchmark, rather than an unchanged copy:
the retained upstream reference SHA is
`d1a18ef9921e82a2dc4773894d6253902184a8f6229719e01ee109829ed4bfe7`, distinct from
both retained applications. Other lineage and AI/model assertions remain exactly
as recorded in the catalog. A collection citation or a similar algorithm does
not supply a new source attribution. No unchanged upstream source is proposed
for editing or exclusion by this review.

[toolchain-v1.json](../../lean4/toolchain-v1.json) records official Lean4.35.0
arm64, commit`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`, native C backend and
Clang23.1.0. The saved release archive digest is
`c0c6f34f35ba1dcc5c4a5fd106fefab9eb5e8469712624dd2c868d51b63177c2`.
The [native](../../lean4/compilation-v4/report.json),
[optimized](../../lean4/optimization-v1/build-fast-v5/report.json) and
[compact](../../lean4/optimization-v1/build-concise-v1/report.json) build records
retain commands and generated-C/executable identities. They use `lean -j1`
outside timing and `leanc -O3 -DNDEBUG -fno-fast-math -ffp-contract=off`, with an
explicit macOS14.4 deployment target/SDK. The recorded application commands have
no explicit `-mcpu=apple-m3` or LTO option; that does not prove every default
chosen inside the compiler driver. CPU targeting and LTO would be separate,
unmeasured configuration candidates, preserving the strict floating-point policy.

Lean's ordinary `let mut` array style is already a legitimate performance idiom:
unique arrays may be updated in place, while shared values require copying.
Source syntax alone does not establish exclusivity or allocation frequency.
Inspect compiler IR/C for reference-count operations and sharing before replacing
clear code with unsafe access. `Nat` is not intrinsically a heap-allocated Peano
counter in native execution; bounded `USize`/UInt arithmetic may still remove
tagging, generic arithmetic and checks, at the cost of explicit bounds/overflow
obligations. Current primary documentation explains
[reference counting and IR inspection](https://lean-lang.org/doc/reference/latest/Run-Time-Code/Reference-Counting/)
and [array ownership](https://lean-lang.org/doc/reference/latest/Basic-Types/Arrays/).
These are programming guidance, not a fresh observation of the pinned4.35.0
machine code.

The direct `(args.headD "0").toNat!` entry points also differ from Common's
exactly-one-nonnegative-argument validation for missing or extra arguments.
Their retained valid-workload timings do not prove identical error/CLI behavior;
future replacements should specify and test that boundary explicitly.

`Common.lean` (`316669c9…`) supplies generic argument, stream, flush and fixed-point
formatting declarations. `Format.c` (`efa69b65…`) calls `snprintf`; `Regex.c`
(`80243f18…`) exposes PCRE2 compilation and a **single** next-match result.
Application traversal, numerical loops, RNG, counts, substitutions and output
assembly stay in Lean. Current application accounting excludes those generic
support files while retaining submitted-source sizes. There is no workload
executor hidden in these leaves. Any new authored workload helper must remain
in the application scope. The FFI uses borrowed string/byte-array arguments and
an external-object finalizer for regex code; ownership and lifetime are part of
the [FFI contract](https://lean-lang.org/doc/reference/latest/Run-Time-Code/Foreign-Function-Interface/).
Runtime metadata explicitly lacks per-timed-process loaded-image inventories;
this review does not upgrade the old runtime closure.

The current retained LOC rule is native-token/independent-statement accounting,
not the partial Python/Julia/Clojure logical-owner metric. Lean has no newly
qualified formatter or uniform logical-owner count here. Packed `for ... do`
statements are already expanded in the saved ledgers; moving them onto one line
does not justify a smaller count. Array constants, records, folds and a single
composed expression can be expressive source without hiding independent work.
Do not reinterpret existing literal-row wrapping as new universally normalized
units or infer a new count from this source review.

## Retained source index

Each row identifies the complete application, independently of attached generic
support. Exact files and support roles are listed in the proposed binding.

| Workload / variant | Application SHA-256 | Application LOC | Saved median s |
| --- | --- | ---: | ---: |
| binarytrees native | `22e0ee3eaf9a51150551bbcc0dc46b97577bbd02d547481e0d85547d0960add2` |31|1.7463145|
| binarytrees optimized | `37c5cacf2a55d3d29508c243b85642f52cda415ec7f248106ec69bc2c13cffff` |31|1.743682875|
| fannkuchredux native | `c1f2a999c5061d73fbd4bd89e67db3d5b2a546afb44c0098c0fb1bd52157e3d0` |52|167.883290042|
| fannkuchredux compact | `243853074499673a192757e2f76b1829105abcb567ac8140ff3099d0a7250b56` |52|168.387707125|
| fannkuchredux optimized | `470794d8d3d26ed06adb64dadf7ce97c203de93207a448d8fba67225b107465f` |75|4.409777708|
| fasta native | `d30b5ddaf146ce8388ad91fbd691ca9a8c1c066b90fc25bce7e3033f8c8a2f31` |51|13.041498167|
| fasta optimized | `11e733b0fc105d63ad2796a9cc7a841158907607eb3cdc1318dc913ec0c0c5c8` |51|14.021512166|
| knucleotide native | `e3aa2ec057ae485f939062523f90e5427cf214cfc5c36a8e090a4e5ecd7a2e3a` |81|6.74196675|
| knucleotide optimized | `e2cb4dc950de63f0cb3ceded840eda8057c71a8307d82fe80e6928a3d9bb33c0` |83|6.785259833|
| mandelbrot native | `bde5c2c94308778097ad25c25ab847f5b46ce5d8dedabbf203556e82f4ae963f` |41|252.292709583|
| mandelbrot compact | `4dc9807e0fadb7bc15b3ff86a74585e1568952c675ef068324de0fc2f398dc0e` |38|9.884991459|
| mandelbrot optimized | `99d1ca436eea51646be4a86fd5336684b89e972792fb5e059224c5217cb4f927` |46|4.962521583|
| nbody native | `2c1161aa2e2640d92ff230ca1daf1924cbf9051542e50a913769b3dc7c8013bd` |72|63.094330375|
| nbody compact | `225cda480b5955f098ac3c65c2823565bfdeb00f99f11ee8d03757687997fde3` |59|50.830504792|
| nbody optimized | `1ed1a1a662844116ae9b86ea590ab203e7bca5d2a16346f5c761bf9a39d6c57c` |88|2.043684834|
| pidigits native | `d62dbb2131ecbc9ce7d3992a5e83a253b79ca8ce816df8eb22557571821d7f74` |30|1.299604792|
| pidigits optimized | `955909290c1f738af044d78843356661c9b854109d1fb614af3fc3b7785ea532` |30|1.391086125|
| regexredux native | `7c459f6bc218eeaad815bbebf3cd0362bf2ec5b1ca0c043781a2b32e8038040c` |48|10.146873833|
| regexredux optimized | `0466c6444a340c5b06cecc230d6fc2055eba5a6fa4f633738cf88ad49b2d244e` |48|10.49628025|
| revcomp native | `8da6c1182e7bffe67c315252934fe692299073ce55b15e5c488f7a7cabf0bd06` |63|6.451956333|
| revcomp optimized | `83c63f1968b7e7b15078ab7d8dfb5663df9419865c22839a6ba56c5fae6d9ae8` |63|6.644223792|
| spectralnorm native | `3ee691cdf86d4b262e26bdce7d6fe52e523a0968ed2e2eb2744248d076d7e137` |41|10.196589583|
| spectralnorm optimized | `a46df1de9384458dfedd33d61f8ac540a5bedeecdf35b2a61d06667b91ee3337` |40|0.185175458|

## binarytrees

Both retained sources use an ordinary recursive `Tree` inductive with a dynamic
UInt64 serial in **every** node, noinline construction/checking, a temporary
stretch tree, a retained long-lived tree and tasks for the requested depths.
The optimized source replaces Common wrappers with Std IO/argument operations;
its make/check/manyTrees algorithm is the same. The close historical medians
do not establish a new tree algorithm improvement.

The saved [native work proof](../../lean4/required-work-v1/review.json) and
[optimized proof](../../lean4/optimization-v1/work-fast-v5/review.json) count
51,550 actual node allocations at depth9 and review temporary/long-tree lifetimes.
Dynamic serials avoid constant leaf/subtree sharing; do not remove them merely
to shorten source without renewing that generated-code/allocation proof.
Ordinary next experiments are bounded task chunks within each depth, and
two-level constructor/checker unrolling that still allocates and traverses every
node. Inspect RC reuse/destruction before replacing the idiomatic inductive.
Flat encodings, shared leaves, cached checks, arenas and native tree executors
would change the required work rather than improve this source formulation.

## fannkuchredux

Native/compact retain the same serial `Array Nat` carry enumeration and mutable
prefix-flip loops. The compact source mainly removes Common wrappers; both
retain52 units and nearly identical historical time. The optimized source is a
different ordinary low-level Lean formulation: packed ByteArray permutation,
counts and scratch; USize/UInt64 ranks; Int64 checksum; UInt32 flips; tail-recursive
`reversePrefix`/`rotatePrefix`; mutually recursive enumeration/flip/carry phases;
and8 factoradic contiguous task chunks. Its75 units represent actual additional
state/scheduling code, not a physically packed version of the serial program.

The optimized [work proof](../../lean4/optimization-v1/work-fast-v5/review.json)
records40,320/362,880 distinct valid permutations at n8/9 with no duplicates,
alongside source review of prefix swaps/checksum/maximum. That is valuable
bounded visit evidence; it is not a new full-size trace of every flip. Preserve
the global start parity and chunk seeds, all prefix reversals and every maximum
contribution when changing scheduling.

The optimized enumeration currently calls `copySlice` into scratch even when the
first element already yields zero flips; a guarded copy is a concrete separate
candidate. Compare more bounded chunks over the standard pool to8 static chunks
for load balance, and inspect generated C for tail-call lowering, buffer
uniqueness and copy behavior. A source-local reversal helper is already clear;
moving its body into an excluded helper is not a valid size reduction. The
optimized API rejects n>16; USize/byte conversions and unchecked accesses need
the exact input-domain proof rather than extrapolation to arbitrary n.

## fasta

Both applications implement the same buffered writer, per-base ALU modulo,
UInt64 LCG update, Float division and linear cumulative-probability search.
The second mostly substitutes direct Std IO/argument expressions and is not a
new RNG or classifier algorithm. The seed returned by TWO is passed into THREE;
all draws and double-CDF decisions remain visible in source. Fixed64KiB buffers
avoid one system write per base but still execute push/capacity and line-modulo
logic for each base.

Compare a reused/pre-sized ByteArray block filled by index, an ALU position reset
instead of modulo, and explicit line counters instead of i%60. Cache the output
handle outside hot loops. Compare a four-way classifier for THREE and a balanced
search of the **same** cumulative Float probabilities for IUB. Retain every LCG
update, continuous seed, division, accumulation order, full output and60-column
tails; no cached RNG period, skipped draws or integer thresholds. UInt64 is
already fixed-width, so describing a future Nat→UInt change as the missing
optimization here would be inaccurate. The single parameterized sequence writer
is a legitimate concise Lean abstraction; shorter independent declarations do
not supply a new count.

## knucleotide

Both sources first parse THREE into encoded0..3 bytes with token-boundary header
checks, case folding, comment handling and invalid-letter rejection. Widths1/2
then use a dense `Array Nat` of size4^k. The five long-width queries use rolling
UInt64 equality scans and scalar counters. Neither performs a standard map
lookup/update per overlapping key. The optimized variant changes wrappers and
adds the fixed-format declaration, while retaining this algorithm.

This is a confirmed current-policy issue, not merely an unexplored speed option.
The [separate policy packet](../../lean4/library-map-review-v1/README.md) binds the
exact same primary rule used for Futhark, both main hashes, excluded support and
the conflicting broad historical required-work claims. The separately applied
correction preserves all historical records and removes only these two profiles' eligibility. No
unchanged upstream program is implicated.

A replacement should use the pinned version's public `Std.HashMap` facilities
from a small default size and accumulate **all** overlapping keys at all seven
widths; UInt64 rolling key encoding is permitted, query-only accumulation is
not. Confirm the actual update API/ownership path from the exact release before
claiming a one-lookup idiom, then qualify collisions/growth, every window,
boundary fixtures and full output. Preserve complete measured input processing;
the existing pre-encoding can be reused, but does not make dense/query-only
counting eligible. No existing timing can be transferred to that new algorithm.

## mandelbrot

Native keeps Nat counters and scalar mutable Float state in its inner pixel
loop. Compact extracts the recurrence into a `partial` tail-recursive `inside`
function with UInt32 remaining iterations, preserving the Float operations and
50-step limit. This is a real source formulation change, not just line packing.
Optimized reuses that function, precomputes horizontal Float coordinates once,
and uses USize unchecked coordinate reads and byte-sized packing state. All
variants create8 standard tasks and emit row chunks in order; all requested
pixels and partial PBM bytes remain explicit.

The historical252.29/9.88/4.96s comparison combines representation, function
shape and hoisting; it does not identify each cost separately or prove SIMD.
Compare row-chunk scheduling for center/edge imbalance and two/four-pixel
independent accumulators. Inspect C/assembly before claiming vectorization.
Keep strict doubles, escape semantics, maximum50 iterations, bit order and tail
padding; no analytic interior tests, symmetry or approximate arithmetic.
Coordinate precomputation is legitimate shared input-independent arithmetic;
caching pixel answers is different required work. The existing `inside` helper
already offers a compact ordinary Lean expression without concealing iteration.

## nbody

Native uses a35-element FloatArray with Nat indexing and `set!`. Compact uses
Vec3 Add/Sub/scale operations, a Body record array, `foldl` momentum offset,
record `modify`, `map` positions and `Nat.repeat`. This59-unit representation is
a genuine expressive alternative to scalar indexing, despite its historical
50.83s time. Optimized returns to FloatArray but uses USize tail-recursive
`pairs`/`velocities`/`positions` and small unsafe `uget`/`uset` helpers; it caches
the current body's position/mass and keeps all pair velocity updates visible.
Its88 units and2.04s median are a different representation/performance tradeoff.

Inspect generated RC/C behavior to distinguish array sharing, record allocation,
generic index overhead and tail-call lowering. A concrete next candidate caches
the current i-body velocity through its j-loop and writes it back once while
updating each j-body in order; positions/masses can remain cached, velocities
cannot be read from a stale whole-body snapshot. Compare a fixed five-body
tuple/scalar formulation or structure of arrays separately, counting all written
pair/update logic. Preserve50M sequential steps,10 symmetric pairs per step,
momentum offset, strict sqrt/divide, update order and both energies. New CPU/LTO
flags or approximate reciprocal square roots must not be smuggled into a source
comparison. Unsafe bounds assumptions need a source-specific proof for35slots.

## pidigits

The30-unit native and optimized implementations retain the same arbitrary-Int
spigot: independent `(3*q+r)/t` and `(4*q+r)/t` extractions, equality gate,
ordinary grow/emit transitions and correctly padded ten-digit lines. The saved
work proofs identify two separate generated runtime division calls before
emission. The optimized candidate mostly replaces wrappers and is historically
slower; no new arithmetic method follows from its label.

Keep Lean's arbitrary-precision Int rather than narrowing the growing state to
UInt64. Inspect native Int temporary ownership before replacing readable
arithmetic with an FFI layer. Deriving the second numerator from the first plus
q could share ordinary arithmetic while retaining **both divisions**, and output
can be assembled into a reusable byte/string builder instead of repeated line
concatenation. Do not assume each String append reallocates without IR evidence:
Lean may reuse unique buffers. A generic arithmetic-library binding would be a
separate runtime/source candidate, with every authored forwarding helper counted;
a native pi executor or inferred second extraction would violate the boundary.

## regexredux

Both use identical Lean traversal: compile cleaning regex, count9 patterns
serially with `findNext`, perform5 ordered regex substitutions and assemble
output. Native/optimized differ primarily in Common versus direct IO wrappers;
both retain48 application units. The generic C leaf uses PCRE2 10.49 with compile
options0, allocates/frees match data for **each** next-match call, and returns an
Option/pair of Lean Nat bounds. No PCRE2 JIT compilation call appears in this
binding. These are concrete possible costs, not evidence that C performs the
whole benchmark.

A generic compiled-regex object with reusable match data is worth testing,
preserving independent objects/lifetimes per worker. Nine independent count
tasks and one ordered substitution chain are another ordinary Lean Task design.
Before compiling regexes concurrently, address the current C leaf's lazily
initialized static external class; the sequential implementation does not prove
that initialization is thread-safe. Compare ordinary PCRE2 study/JIT only as a
separately pinned library configuration. Preserve9 searches, non-overlap,
cleaning,5 ordered substitutions, input/output lengths and the retained case
policy; do not infer a new case-flag requirement from the MATLAB review or
replace regex processing with a specialized byte scanner.

## revcomp

Both implementations read all input, gather a record with repeated `extract`
and ByteArray append, then emit its complemented bytes in reverse order through
a64KiB buffer. They share the same LUT, strict IUPAC rejection, CR/LF/header/
comment handling,60-column lines and explicit flush-on-error behavior. Optimized
again mainly removes Common wrappers; there is no new reversal algorithm in its
historical6.64s result relative to6.45s native.

Compare direct indexed append from the input span to avoid allocating each line
slice, and a reusable output block with a cached output handle. A source-local
two-ended in-place complement/reversal is another candidate if unique ByteArray
ownership is shown; disjoint parallel ranges must still preserve every base and
ordered output. Streaming complete records can reduce the whole-file buffer
while retaining header/comment/EOF behavior. Keep uppercase output for both
cases and the U/u complement, odd centers, empty records and invalid-input
behavior. Do not count a streaming parser or workload writer as generic excluded
support merely because several variants share it.

## spectralnorm

Both have named coefficient/apply/step functions and perform40 dense products
in10 iterations. Native computes integer denominators with Nat and uses Nat
inner loops/checked FloatArray reads. Optimized uses an inline USize coefficient,
a tail-recursive `dot`, unchecked `uget`, and a fold to concatenate task results.
This is a substantial native representation/control change at40 versus41units;
it does not cache A or omit products. Both still spawn8 tasks on **every**
application, yielding320 task creations per run, and allocate partial/result
arrays for each product.

Compare reusable output/scratch buffers with clearly proved ownership, a bounded
persistent worker organization, normal/transposed dot specializations outside
the hot j-loop, and two/four-row accumulators. Each needs generated C/RC evidence
before claiming fewer copies or vectorization. Preserve every requested
coefficient and multiplication, integer triangular denominator semantics,
transpose/composition structure, all40 products, reduction order and final
strict Float result. The existing short coefficient and fold are legitimate
expressions; expanding them into scalar helper boilerplate is not inherently
more representative Lean. USize denominator arithmetic is bounded by the
tested input domain and must not be extrapolated to arbitrary Nat inputs.

## Practical next sequence

First resolve the exact k-nucleotide eligibility correction and qualify a genuine
standard-map replacement. Then isolate the largest ordinary opportunities:
regex match-data allocation/independent tasks; FASTA byte-block/line-counter
costs; reverse-complement slicing; and fannkuch scratch copy/task balance.
Treat compiler targeting, tail-call/ownership diagnostics and numerical loop
changes as separately recorded candidates. N-body's compact record form and
Mandelbrot's extracted recurrence already demonstrate meaningful expressiveness;
they should remain available alongside faster low-level variants.

The retained149-case bounded reports and source/work proofs are useful evidence,
with source-specific limits described above. They are not an automatic
whole-language certificate or proof of best performance. Every future source,
build configuration, helper boundary or count needs its own exact provenance
and appropriate qualification, while preserving the existing observations.
