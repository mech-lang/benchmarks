# Mech application and execution-mode review

This is a read-only source/evidence review of all ten workloads, **44 retained
profiles and 17 distinct application source files** in the current catalog:
15 AOT, 14 JIT and 15 interpreted. It does not run, compile, edit or remeasure a
benchmark or compiler. Every existing timing, source, normalized count and
endpoint remains unchanged. Suggested changes below are audit/optimization
candidates, not newly qualified implementations or optimality claims.

## Scope and exact source roots

`data/benchmarks.json` supplies the full source hashes and exact profile records.
The SHA column below is a distinguishing prefix of that full hash. A/J/I mean
AOT/JIT/current whole-process interpreted. Profiles sharing a source hash are
execution configurations of the same authored application; generated Rust/C,
native objects, parsed graphs and JIT code are representations of it, not extra
application implementations or additional source-size charges.

| Workload and source root | SHA prefix | Retained LOC | Modes |
| --- | --- | ---: | --- |
| `archive/workloads/binarytrees/binarytrees-parallel.mec` | `61e30dc7a1dc` | 26 | A/J/I |
| `archive/workloads/fannkuchredux/fannkuchredux.mec` | `0a5bee0d6263` | 39 | A/J/I |
| `archive/workloads/fannkuchredux/fannkuchredux-even.mec` | `b8a2ce6509db` | 59 | A/J/I |
| `archive/workloads/fasta/fasta.mec` | `5a6e55ee2002` | 32 | A/J/I |
| `archive/workloads/fasta/fasta-optimized.mec` | `b98ea612ac4c` | 43 | A/J/I |
| `archive/workloads/knucleotide/knucleotide-compact.mec` | `3a2f773f1ebc` | 17 | A/J/I |
| `archive/workloads/mandelbrot/mandelbrot-compact-program.mec` | `75a6ef040661` | 20 | J/I |
| `archive/workloads/mandelbrot/mandelbrot-program.mec` | `c8131e57450a` | 29 | J/I |
| `archive/workloads/mandelbrot/experiments/20261011-array-state/mandelbrot-array-state-scalar-canonical.mec` | `4e4b881e9c23` | 11 | A |
| `archive/workloads/mandelbrot/experiments/20261011-array-state/mandelbrot-array-state-five-rows-canonical.mec` | `baf1cc933c9d` | 16 | A |
| `archive/comparisons/array-comparison/nbody-20261009/sources/nbody-matrix-short.mec` | `f6a7f25aefb9` | 20 | A/J/I |
| `archive/comparisons/array-comparison/nbody-20261009/sources/nbody-matrix-pairwise.mec` | `5551286c12ce` | 25 | A/I |
| `archive/workloads/pidigits/pidigits.mec` | `db8b2e388e9f` | 35 | A/J/I |
| `archive/workloads/pidigits/pidigits-advance.mec` | `7079dab9ee52` | 38 | A/J/I |
| `archive/workloads/regexredux/regexredux.mec` | `69b4a43724ae` | 24 | A/J/I |
| `archive/workloads/revcomp/revcomp.mec` | `7ca0b4ff377c` | 7 | A/J/I |
| `archive/validation/work-audit/20261009/sources/spectralnorm-four-functions.mec` | `eb5d5a828c79` | 12 | A/J/I |

Canonical identifiers are the recorded source roots plus `:jit` or `:resident`
where applicable. The current JIT catalog has no `pairwise-mass-tails` profile.
Historical cohorts contain additional mode/control observations; they do not
automatically become current profiles. In particular, the six-profile Mandelbrot
`source-modes-study/full-study/report.json` is complete and propagates scalar11
and row16 to JIT/interpretation, but its interpreted score is loaded
`kernel_seconds`. It cannot replace the current whole-process interpreted
cohort without a separate admission using the required timing boundary.

These are suite-owned Mech applications and compiler/library compositions for
audit purposes. That ownership does not establish exclusive original authorship,
an exact historical model, or upstream lineage. Retain each profile's authorship
record. The pi advance guard has a specific retained Rust #4 reference; a
workload description alone is not an implementation-origin citation.

## Execution and application/library boundaries

The main historical work records are
`archive/validation/work-audit/20261009/{audit.json,builds.json,timings.json}`.
`experiments/mech/timing-boundaries-v1/aot-jit-review.json` traces all 29 selected
AOT/JIT profiles and 103 observations to process-launch-through-exit producers.
It also discloses where historical runner hashes, expanded arguments or ambient
environment records were not retained; a later source inspection does not
recreate those execution-time facts.

Current interpreted measurements come from
`experiments/mech/interpreted-whole-process-v1/run-v1/report.json`: status
`complete`, 45 samples, all 15 sources, three fresh processes each. They charge
startup, parsing, graph preparation, activation, interpretation, input, complete
output, flush and shutdown. Internal preparation/kernel diagnostics are retained
and not ranked. Older documentation under `archive/compiler/execution-modes/`
describes loaded resident timings; those statements concern that historical
cohort, not the current interpreted chart. AOT charges application/runtime
startup without source compilation; JIT charges source admission and native
compilation in the fresh process. These are admitted typed subsets, not a claim
that every general Mech construct is supported identically in every backend.

The inspected generic executor is
`archive/compiler/execution-modes/20261010-final/runtime-snapshot/hosts/gpu/src/execution.rs`.
It parses a canonical source once, tries sequence/control/grid admission by
types and operations, and otherwise uses the autonomous numeric graph runner.
Its JIT branches compile the admitted graph; resident branches interpret typed
sequence/control/grid/numeric representations. Interpreted execution still uses
ordinary native library operations, typed elementwise loops, GMP and regex
libraries. It does not mean every byte or arithmetic primitive is executed by a
scalar bytecode instruction.

The inspected sources and retained admission evidence do **not** show a native
whole-benchmark replacement for the Mech algorithms. The distinction is concrete:

| Application-owned work | General runtime/library work |
| --- | --- |
| Tree node type, recursive construction/check, iterations and lifetimes | Arena/frame allocation and generic range scheduling |
| Permutation order, factoradic initialization, carry, flips, checksum | Fixed byte-vector get/set/rotation/reversal and generic while/range execution |
| FASTA LCG and probability comparisons, alphabets and output requests | Generic scans, source callback execution and buffered output |
| Seven k values, frequency/query composition, ordering/formatting | Generic packed windows, growing hash tables, encoding and map storage |
| Mandelbrot recurrence/escape predicates and state | Generic grid mapping, source-derived native/typed loops and PBM packing |
| N-body masses, pair forces, energy and updates | Generic array graph lowering, gather/scatter, scheduling and turn loop |
| Pi spigot state, both candidate extractions and recurrence | General mutable bigint/GMP operations and output |
| Nine regex counts and five ordered replacements | General regex compilation/count/substitution services |
| Complement alphabets, reversal/translation/wrap composition | General byte tables, buffered records, fusion and writes |
| Spectral coefficient and four source functions | Generic shaped-producer fusion, reductions, tiling and parallelism |

A native histogram loop is a real and substantial library primitive; describe it
as such rather than suggesting that its scalar hash updates are authored in the
17-line main. Conversely, replacing all seven histogram/query expressions with a
native nucleotide benchmark function would cross this boundary. The same rule
applies to tree, gravity, pi, Mandelbrot and permutation executors. Generic
compiler improvements must be exercised on unrelated fixtures and preserve
effects, allocation identities, errors and required work.

## Retained performance evidence and priorities

These are the current fastest retained medians in seconds, not one synchronized
three-mode experiment. Source selection differs in the noted cases; the table
does not isolate compilation/startup cost or establish a global optimum.

| Workload | AOT | JIT | Interpreted | Comparison qualification |
| --- | ---: | ---: | ---: | --- |
| N-body | 1.039486 | 1.380457 | 16.023823 | A/I use pairwise (25 LOC); J uses compact (20) |
| Mandelbrot | 0.442217 | 0.783310 | 12.304361 | A uses row16; J/I use older lane29 |
| K-nucleotide | 0.513828 | 0.612304 | 0.696738 | Same 17-line main |
| Spectral norm | 0.086075 | 0.237050 | 0.617069 | Same four-function main |
| Reverse complement | 0.149273 | 0.174436 | 0.294770 | Same 7-line main |
| Fannkuch redux | 1.702457 | 2.020614 | 61.825631 | A/J use paired (59 LOC); I uses default (39) |
| FASTA | 0.541193 | 0.765849 | 19.246664 | Same expanded main (43 LOC) |
| Binary trees | 0.394411 | 0.525069 | 10.008148 | Same pool main (26 LOC) |
| Regex redux | 0.489612 | 0.564493 | 0.570618 | Same 24-line main |
| Pi digits | 0.300272 | 0.447466 | 0.447955 | Same advance main (38 LOC) |

The strongest compiler-gap candidates are the same-source interpreted even
Fannkuch at 81.062691 s versus AOT 1.702457 s (about 47.6×), expanded FASTA
(about 35.6×), pool trees (about 25.4×), and pairwise N-body (about 15.4×).
These descriptive ratios mix retained cohorts and cannot apportion VM dispatch,
allocation, startup or scheduling without a new controlled study. K-nucleotide,
regex and bigint programs have much smaller mode gaps because substantial work
already resides in general library primitives. Preserve the measured samples;
do not use native workload bridges to make those ratios disappear.

## Workload reviews

### Binary trees

`Make` lines 2–4 allocates the same ordinary two-reference record for a leaf and
an interior node. `Count` lines 5–7 performs the recursive traversal. `Tree`
constructs then checks; `AllocatedChunk` line 9 wraps **each** tree in a frame,
while `Chunk` lines 11–12 owns its capacity-bounded worker arena. `Long`
lines 17–20 constructs its root before all `Depth` calls and checks it after them.
The stretch arena at line 23 ends before the long-lived arena at line 25 begins.
The full recorded work is 613,766,494 constructed-and-walked nodes. Source line 21
explicitly bounds supported input to 0..21; this is not unrestricted arbitrary
depth support.

The arena strategy is a material implementation choice: distinct 16-byte node
slots and per-tree frame release, not a default GC comparison or a separate OS
allocation for every node. `archive/workloads/binarytrees/README.md` and its
conformance programs/results distinguish abandoned registry/Box experiments from
the admitted generic pool. Distinct leaf/child identities, nested live regions,
bounded frame reuse and allocation-effect handling are tested there. Older
29-line variants are not the selected 26-line source count.

Optimize the general interpreter's recursive call frames, typed record field
access and arena allocation dispatch; retain distinct writes/addresses and the
long-lived outer arena. A compiler that memoized `Make(depth)`, shared identical
leaves, or replaced `Count` with a formula would remove required work. Source
compression by merging the capacity/frame/lifetime bindings is not a measured
improvement; its ownership and lifetime meaning must remain visible.

### Fannkuch redux

Both roots use fixed 16-byte permutations/counters. `Chunk` un-ranks its starting
factoradic position, then the application enumerates every permutation and
performs actual prefix reversals. The full N=12 domain has 479,001,600 permutations.
The default root uses grain 4096; the even root chooses an even grain near
`total/128`, processes two successive permutations together, and retains a
single-permutation tail. Its paired checksum assumes even chunk starts; the
source's even grain establishes that property. A future scheduler must not
silently repartition those starts at odd ranks.

The 59-line root exposes two independent flip chains, reducing task/unranking
overhead and giving compiled code more instruction-level parallelism. It is
faster in AOT/JIT but **slower** than default in current interpretation
(81.06 versus 61.83 s). That inversion is actionable evidence against blindly
selecting the expanded source for every mode. Inspect typed tuple/state copying,
prefix-operation buffer ownership, generic while dispatch and result marshalling.
General last-use/register lowering and reuse of fixed byte arrays are appropriate
compiler work. Keep alias checks for the original permutation and independent
flip copies. A native permutation/flip/checksum benchmark procedure is not.

The code repeats predicates, carry state and Preserve/Advance tuple plumbing;
structural loop-state support could express the same algorithm more directly.
Any smaller proposed form needs actual admission, parity/tail and full checksum
checks before receiving a new count or timing. Hoisting factorial constants per
unranking setup and testing fewer larger default chunks are legitimate source
alternatives; their profitability is not established here.

### FASTA

Both sources explicitly advance the LCG once per random letter and perform
floating division and cumulative-probability comparisons. The compact root's
`Choose` is a binary-search while; the expanded root replaces it with 14 IUB and 3 human
threshold comparisons and a sum. At canonical N=25,000,000 the source requests
50 million fixed ALU bytes plus 200 million fresh random nucleotides. Caching
the supplied fixed repeat is allowed; caching random periods or changing random
selection into integer cutoffs is not the admitted comparison.

This was a real earlier work issue, not a hypothetical one:
`archive/validation/work-audit/20261009/README.md` records disabling the general
exact-float-cutoff transform with `MECH_CONTROL_EXACT_FLOAT_COMPARE=0`, corrected
full runs and disassembly retaining floating division/comparisons. Retain those
pins for AOT/JIT; a numerically equal full output does not independently prove
the required floating work.

The source constructs constant cumulative arrays/alphabets inside callbacks.
Check general constant capture/hoisting and typed scan-state dispatch in the
interpreter before adding an algorithm bridge. Reuse of constants is legitimate;
skipping the LCG or floating comparisons is not. The expanded root already supplies the
retained branchless alternative and is faster in all three modes. A generic
array/comprehension threshold sum could reduce the repeated fourteen bindings
if admitted with the same floating predicates; it is a source/frontend candidate,
not a qualified new LOC result. Buffered scan output must retain seed chaining
from TWO into THREE and partial 60-column output.

### K-nucleotide

The main lines 1–9 own frequency decoding, ordering, percentages and query output;
lines 11–17 visibly request all seven histograms before extracting their results.
The general packed-window producer and hash-table primitive perform the inner
work. The selected policy is standard-library HashMap with FxHash, narrow keys
and proven-safe u32 counters, four partitions per histogram and an eight-worker
Rayon pool; wider input bounds select wider counters. This is a disclosed
library/container choice, not a comparison of handwritten scalar loops.

The retained `archive/compiler/execution-modes/20261010-final/runtime-snapshot/hosts/gpu/src/sequence/counts.rs` has ordinary
empty map constructors and `entry(...).or_insert(0) +=1` for each key, plus real
merge updates. Its `resident.rs` lines 467–527 splits complete window-start
ranges, overlaps only the necessary source suffix, generates rolling keys in
512-key batches, increments every batch, merges tables and asserts histogram
totals. The full sum is 874,999,961 updates. No observed-key prepopulation or
query-only long-string search is visible. Narrowing follows admitted bounds,
not nucleotide-specific frequency assumptions.

`archive/workloads/knucleotide/README.md` documents generic all-key checks,
non-DNA alphabets, arbitrary packing widths, invalid encodings, tails, CRLF,
lowercase, absent keys and EOF consumption. Its removed host frequency/query
wrappers and old indexed/query-only BQN/K prototypes are historical exclusions,
not current accepted alternatives. This review does not assert a new shared
14-case Mech replay merely because the BQN/Nim candidates passed that corpus.
The exact THREE-token/comment behavior of `text/record` remains worth comparing
against the common corpus before expanding the claim beyond saved conformance.

Optimization candidates are general histogram task scheduling, merge order,
bounded key batches, allocation reuse and packed-window traversal. The API is
already expressive: the seven widths and queries remain application data.
Do not replace it with a native whole nucleotide workload or a dense/query-only
shortcut. The existing optional NEON packing study did not establish a retained
benefit, so SIMD eligibility alone is not an optimization result.

### Mandelbrot

All four roots author the complex recurrence and escape predicate. The older
20-line root uses scalar reactive variables; the 29-line root uses eight lanes
and five explicit recurrences per loop step. Current scalar11 instead keeps a
three-element state array; row16 keeps a 2×8 state with one explicit recurrence
followed by four calls to its reusable `advance` helper.
The state representation and helper expressions are application source. Generic
grid/PBM traversal is runtime support. Loop-only FMA policy is explicit for the
fast roots; it is not a claim of identical floating instructions across forms.

The row16 source tests all lane predicates and stops at its 50-iteration bound;
it can keep arithmetic running for escaped lanes while other lanes remain live.
That differs from claiming every pixel executes exactly 50 updates. Full PBM,
partial-byte tails and the source-defined escape semantics are what its retained
independent references check. `validation-current/report.json` and the AOT
`full-study/manifest.json` bind scalar11/row16 source, generated driver, native
object, flags and complete images. Generated C owns generic argument/row/PBM
plumbing; the recurrence is in the source-derived native object.

This is the clearest existing smaller idiomatic alternative: the scalar source
goes from 20 to 11 units, and the lane source from 29 to 16, reducing exposed
scalar state/duplication while retaining the algorithm. The array-state
source-modes study also reports JIT row16 at 0.719230 s and scalar11 at 2.323236 s,
with unchanged-source AOT controls, but its loaded
interpreted values must not be presented as current end-to-end replacements.
Future work should propagate the exact source roots through each mode with
whole-process interpretation and preserve all prior samples. Compiler targets
are fixed-array state scalar replacement, elementwise vector lowering, capture
handling and typed interpreter dispatch, not a native Mandelbrot executor.

### N-body

Both sources own all five masses/initial coordinates, momentum correction,
ten pair differences, squared distances, inverse-distance force, velocity and
position updates, and energy. The 20-unit root performs two indexed velocity
updates. The 25-unit root explicitly represents twenty signed body contributions with
`interaction`, `sibling`, `body`, `other`, `sign` and `weighted-m`, then scatters
their sum. Repeated indices must accumulate correctly; a last-write scatter is
not equivalent. Imported `combinatorics` and `stats` are general primitives.

The autonomous host supplies a turn count and observes energy; it is not where
the gravitational formula resides. The current AOT records point to
`archive/workloads/nbody/experiments/20261011-shared-products/replication-50m.json`
and its summary: general shared-product/dependency scheduling, complete state-bit
checks, and 50 million steps with ten pairs each. Do not infer arithmetic-work
qualification merely from the two rounded energy lines, and do not transplant
older runtime snapshots onto this newer AOT compiler revision.

The pairwise source is slightly faster in AOT and interpretation; the published
JIT catalog retains only the compact root. A controlled same-source JIT candidate would
be a separate measurement, not an alias of pairwise AOT. General graph liveness,
reuse of gathered operands, shared products, duplicate-index reductions and
register-pressure scheduling are appropriate compiler gaps. Reassociation/FMA
changes must retain the recorded numerical policy and full-state checks.
Recognizing five bodies and dispatching to a Rust/C gravity loop would remove
the language work rather than improve its lowering.

### Pi digits

The main declares `q/r/t` plus reusable GMP scratch. `Extract` performs ordinary
bigint multiply/add/floor; the compact Step evaluates both 3 and 4 every tested
candidate. The advance root consumes first and uses the retained Rust #4 impossible-
candidate guard before calling the same two extractions. Both still run a
sequential unbounded spigot, emit 10,000 digits, and format ten-digit labels.
The source owns the recurrence; mutable bigint operations are general library
facilities. `archive/compiler/function-application-audit/20261009T171437Z/application-v3/`
retains function-application/effect/alias validation and rebuilt object evidence.

Scratch reuse and mutate-into operations are already strong techniques worth
transferring to other bigint applications. Preserve signed intermediate/floor
semantics, aliasing and the two extracts; a precomputed digit stream, native pi
spigot or combined candidate shortcut is not a compiler optimization. Smaller
structural state-update syntax could reduce repeated record fields, but must
retain identity and mutation order. General buffered output can amortize small
digit/label writes; these current mode gaps are small enough that startup and
library work must be separated before assigning a numeric-kernel bottleneck.

### Regex redux

Source lines 8–16 perform nine independent prescribed counts. Lines 17–21 apply
the five substitutions in order to successive strings; lines 22–24 print the
required original/cleaned/final lengths. This is a sequence of generic regex
operations with source-owned patterns, not one combined native matcher. The
source's explicit `Count` function and common `dna` make buffer sharing and
independent scheduling available without changing required scans.

The near-equal current interpreted/JIT times are consistent with substantial
work already in the regex library, but those medians do not identify a detailed
profile. Inspect copies/Arc retention, compiled-pattern lifetime and output
assembly before changing algorithms. A generic pattern list/map could replace
the nine repeated output statements while retaining nine matches and order;
qualify its source ownership/admission rather than promising a smaller count.
Combined-pattern counting, sample-specific matches or dropping any replacement
would be different work. Keep byte length, regex flags and LF/CRLF behavior tied
to actual retained references; this review adds no new malformed-input claim.

### Reverse complement

The 7-line source owns both complement alphabets, error-on-missing table policy,
reversal, translation, width 60, record mapping and output. The general record
reader grows from buffered input; the admitted path does not stat stdin for an
input-size reserve. The callback transforms the entire record and emits its
header and all wrapped bases. Unknown symbols, comment filtering and alternate
record conventions must follow the actual generic reader/table contract; their
behavior is not inferred from passing the generated full FASTA.

`archive/workloads/revcomp/README.md` describes analysis of all 256 table entries,
general record/translation conformance, scalar tails, exclusive-ownership reuse,
parallel disjoint byte pairs, fusion and native wrapping. Its paired ablations
show that line compaction, output reconstruction and memory passes remain
material after the core byte transform becomes fast. Those historical ablations
are not additive speedups or the current 0.149273 s observation.

This is already a compact idiomatic pipeline. The useful next compiler/library
candidate is a validated general strided/line-layout view that can preserve
regular newline structure and serialize bounded transformed chunks, with alias,
CRLF, odd/tail, arbitrary table and streaming-error tests. A native FASTA reverse-
complement procedure, hardcoded alphabet in the host, or workload-specific width
test would cross the boundary. Normalized LOC must not shrink merely by hiding
the callback or moving those source constants into a private helper.

### Spectral norm

The 12-line main has coefficient, apply, apply-transpose and step as separate
source functions. `sequence/iterate(seed,19,step)` plus the final `step` executes
twenty applications of AᵀA, hence forty matrix-vector products and 1,210,000,000
weighted contributions at N=5500. The visible `A :=` binding is not sufficient
by itself to prove whether the matrix is cached; that is an admission/lowering
question.

The retained
`archive/compiler/execution-modes/20261010-final/runtime-snapshot/src/engine/src/native_sequence/matrix.rs` documents generic
shaped-producer fusion rather than a dense coefficient allocation. Lines 285–321
lower `**` to apply/apply-transpose with the source coefficient callback and
shape; lines 499–528 validate transitive scalar helpers and reject recursive coefficient
calls; lines 635–646 resolve global producers inside named functions and retain error
checks instead of silently dropping unused producers. Together with source-
bound objects, the work audit and execution conformance, this supports recomputed
coefficients/products rather than an answer/matrix cache. The tiny generated
Rust main only creates a general Context and calls the linked source entry.

Interpretation uses typed coefficient tiles up to 32 elements with per-invocation
unsigned-range proofs, preserved scalar accumulation order, transposed indices
and tails. `archive/compiler/execution-modes/20261010-final/conformance.py` and its retained
results cover rectangular matrices, both orientations,1/31/32/33/65 tails,
variable division, captures, eager errors and effects. This is generic batching
and dispatch amortization, not a spectral-native formula. Capture fusion must
not cache coefficient values across products or skip the intermediate vectors.

The four-function source is already short; returning to the historical 9-line
rewrite would remove an explicit requirement. Current frontend limits include
unsupported materialized matrix operands, filtered/qualified comprehensions,
some matrix orientations and recursive coefficient functions. Improving those
general constructs, bounds proofs, scalar call inlining and producer-capture
handling is the compiler-gap direction. A native spectral evaluator, a stored
N×N matrix, algebraically skipping products or a special coefficient formula in
Rust would change the admitted work.

## Source-size and audit conclusions

All 17 mains are application-owned, including parser/composition choices,
probability/key/complement data, function bodies, state arrays and explicit
memory lifetimes. General compiler/runtime source, standard libraries and
generated representations are not extra application LOC. A private helper
containing benchmark composition would be application code even if placed next
to the host. The explicit k-nucleotide frequency/query and revcomp callback
boundaries are useful precedents for applying that rule consistently.

Retained normalized LOC is a versioned cohort metric. N-body's multiline literal
data, tuple/record fields, function headers, pipeline expressions, state writes,
case bodies and generic library calls require the retained owner policy, not a
new claim that each physical line is a universal logical statement. Pi's written
state record is not counted as an expansion of every GMP implementation; a
comprehension or array expression must not be scalarized into implied iterations.
No current Mech profile has a qualified formatted LOC count. Additive UTF-8,
deterministic gzip and BPE measures describe their selected application/submitted
partitions and include comments/whitespace; they are not lexical instruction
counts. No new count is assigned to any suggested alternative here.

The queue is **source-and-idiom reviewed; candidate alternatives not newly
measured**. Highest-value follow-ups are generic interpreter state/call lowering
for Fannkuch/FASTA/trees/N-body, exact whole-process propagation of the newer
Mandelbrot roots, and explicit common-corpus evidence for record semantics.
Every candidate still needs exact source/host-boundary accounting, effects and
allocation checks, full required-work/output qualification, pinned runtime and
commands, and repeated fresh-process observations before admission. The existing
best retained endpoints and all rejected/historical evidence remain intact.
