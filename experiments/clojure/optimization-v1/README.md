# Clojure n-body source candidates

This file retains the **initial source-only proposal**. Subsequent separately
authorized runtime restoration, compilation and bounded state/output checks are
recorded in [primitive-v1/QUALIFICATION.md](primitive-v1/QUALIFICATION.md). The
current comparison pool isolates the parent, scalar updates and typed `aset`
updates; the initial scalar-moves alternative remains retained separately.
No existing program, compiler, catalog entry, source count or timing is changed
by this packet. [plan.json](plan.json) binds the initial proposed files, historical inputs,
runtime evidence and future gates. [source-ownership.json](source-ownership.json)
contains a proposed per-line retained-rule ledger, with approval explicitly false.

The correct starting point is the retained compact source
[`clojure-nbody-compact`](../../../programs/clojure/nbody/clojure-nbody-compact/compact.clj),
SHA-256 `193e26ad8dfd011fd1835d9d67be04bb223d088e6cdd3e2d6302ca8cae2f46d4`.
Its three saved full-process observations are 158.278659625, 165.364857875 and
165.417084500 seconds: median **165.364857875 seconds**, 109 application LOC / 49
physical LOC. The separately retained `clojure-nbody-optimized` is slower at
**207.674197292 seconds**, 121 / 56 LOC. It computes and saves pair displacements
and magnitudes in one pass, then loads/destructures persistent pair descriptors
in another pass. Both historical observations and sources remain unchanged.
Those historical numbers describe the saved JVM cohort; no fresh effect estimate
exists for these proposals.

| Proposed complete main | Isolated change | Proposed retained-rule application LOC / physical LOC |
| --- | --- | ---: |
| [scalar-updates](sources/clbg/nbody/scalar_updates.clj) | Replace the per-pair `doseq` and `[[0 dx] [1 dy] [2 dz]]` with six explicit primitive-array stores in the same order | 111 / 52 |
| [scalar-moves](sources/clbg/nbody/scalar_moves.clj) | The same six stores, then replace the three-axis position loop by three explicit stores, still after all pair impulses | 111 / 53 |

The namespace is unique for each isolated compiled application. All initialization,
momentum, energy, argument parsing, `Math/sqrt`, division, pair loops, time-step
loop and output calls otherwise retain the compact source. There is no foreign
n-body kernel, new application helper, library substitution, table of answers,
parallel time step, cached force or changed integration scheme. Ordinary general
Clojure/JVM array and math operations remain the execution boundary.

## Arithmetic and primitive representation

For each step, the unchanged loops visit `(0,1), (0,2), (0,3), (0,4), (1,2),
(1,3), (1,4), (2,3), (2,4), (3,4)`. Each pair evaluates dx, dy, dz; then
`sqrt(dx*dx + dy*dy + dz*dz)`; then `0.01/(distance*distance*distance)`.
Each candidate stores a.x, b.x, a.y, b.y, a.z, b.z velocities in exactly the
parent's order, retaining `(* delta (aget other 6) magnitude)` rather than
reassociating it into a shared mass/magnitude factor. Only after all ten pairs
are complete are positions moved in body order and x, y, z order. The second
candidate specializes the fixed axis indices without changing that order.

At 50,000,000 steps the source still requires 500,000,000 pair interactions,
500,000,000 pair square roots/divisions, 3,000,000,000 velocity stores and
750,000,000 position stores, plus momentum adjustment and both energy evaluations.
These are source-derived work counts, not an executed witness.

The original `^objects` / `^doubles` array hints remain. Direct `aget` results,
binary64 arithmetic and `aset-double` are ordinary Clojure primitive-array idioms.
The candidate removes four persistent-vector constructor expressions and sequence
destructuring from each pair. That establishes a source change, not the number of
actual heap allocations: HotSpot escape analysis and the original compiler may
already eliminate some temporary objects. Primitive scalar inference and JIT
inlining must be checked in real compiler output before attributing a speedup.
No redundant `^double` hint is added to an already inferred primitive local, and
no unchecked-math or fast-math mode is introduced.

The first actual build must retain all compiler stdout/stderr and warnings.
An initial diagnostic compile can bind `*warn-on-reflection*` true without
claiming that type hints prove the absence of boxing. Inspect `javap -c -p -s`
for the actual `advance` class: typed array accesses, primitive arithmetic and
the absence of vector/sequence construction in that body are the intended result.
Also inspect the parent under identical options. If a separate
`*unchecked-math* :warn-on-boxed` diagnostic is useful, keep its classes and
warnings separate: it can change lowering and is not the measured build.
Every warning, failed compile and resulting source revision must remain in an
exclusive attempt directory; none has been run for this packet.

## Exact runtime restoration and build boundary

[runtime-restoration.json](runtime-restoration.json) extracts the existing pinned
Temurin **25.0.4.1+1 ARM64 full JDK**, Clojure **1.12.6**, spec.alpha **0.5.238**
and core.specs.alpha **0.4.74** evidence. The original absolute executable/JAR
paths are absent in this checkout. This is a restoration recipe and historical
hash record, not a claim that the runtime has been restored or reverified here.

The retained full JDK archive SHA-256 is
`61979887f7506a24a57439ff99adb8b3a7fc89977d9cfe3b8984f58a981b7b9d`.
The frozen proposal also pins the whole extracted runtime and the actual
`java`, `javac`, `javap`, `libjvm` and release files. A future restoration must
match the archive, safely extract a new isolated tree, check the complete tree
against these receipts, and verify all three JAR hashes before loading them.
Existing saved architecture, linked-image and version evidence stays intact;
new verification must be retained separately. No system Java or newer Clojure is
an equivalent replacement without a separate runtime experiment.

Use the saved JVM flags for the matched parent and both candidates:
`-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`. Use a controlled
environment with empty `CLASSPATH`, `JAVA_TOOL_OPTIONS`, `JDK_JAVA_OPTIONS` and
`_JAVA_OPTIONS`, `LC_ALL=C`, `LANG=C`, and the restored `JAVA_HOME`; retain the
original one-thread BLAS/OpenMP environment fields. The application itself is
serial; eight available processors does not mean eight n-body workers.

Compile the exact isolated main plus byte-identical `clbg.support` using
`clojure.main`, `*compiler-options* {:direct-linking true}`, and a new per-source
`*compile-path*`. Preserve compiler/JDK/JAR hashes, complete command/environment,
all class-file hashes, source-copy hashes, compiler-input inventory and diagnostic
output. Generated classes are compiled artifacts, not newly authored application
source. Measured commands must load only their own classes plus the three pinned
JARs; source paths or another candidate's classes must not leak onto that classpath.

## Boundaries, source count and provenance

The unchanged shared [support source](../../../programs/clojure/binarytrees/clojure-binarytrees-compact/support.clj)
has SHA-256 `ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446`.
Current application accounting excludes that generic argument, formatting/flush,
input and Callable-pool support: 46 retained-rule / 23 physical support LOC.
Preserve its exact bytes and submitted-bundle visibility. All n-body logic remains
in the candidate main. The source must retain Locale.ROOT formatting and explicit
flush; Clojure generated main alone did not provide the required flush in the
historical cohort. No private workload helper is moved into support.

The old compiler-bound grammar-v3 ledger gives the parent 109 application LOC.
Its three-line per-pair `doseq` block owns five units: loop header, two stores,
loop close and containing-let close. Six scalar stores plus the same let close
own seven, so the first proposal is 111. Position unrolling removes one axis-loop
header and close while adding two stores, leaving 111 for the second proposal.
All other owner units are copied by exact source-line correspondence. This is
an explicit proposed extension of the retained rule: **application_loc is null,
independent_review_approved is false**, and native grammar replay has not run.
It is not a new universal logical-LOC policy, formatted LOC or a claim of minimum
idiomatic size. The scalar duplication is a speed/source-size tradeoff to test.

The retained Clojure provenance describes local adaptations of task descriptions
and independent references, while the catalog leaves earliest original
implementation/model and inherited terms unresolved. Those gaps remain.
The new edits are authored in the current OpenAI Codex session; developer identity
establishes the Codex GPT-6 family only, with no exact model version asserted.
This draft is not authorship verification for any predecessor. Existing source
notices, references and Apache-2.0 scope for local changes must survive intake.

## Initial qualification and measurement plan

The initial source-only proposal granted no execution. The later native window
was separately authorized; its records distinguish completed gates from future
pilot/full work. The guarded protocol requires these gates:

1. Seal hashes of this packet, the exact parent, support, restored runtime/JARs,
   controller and independent reference. Acquire the established common timing
   mutex before runtime restoration, compiling or any native work. No concurrent
   compiler, browser/performance job or other benchmark may overlap measured runs.
2. Compile the retained compact parent and both candidates in exclusive packages;
   retain warnings, full class manifests and `advance` bytecode. First reject
   malformed/reflective or unexpectedly boxing hot paths as review findings;
   retain their failure artifacts instead of silently rewriting the candidate.
3. Run the shared six bounded corpus cases N=0,1,2,10,1000,10000 against exact
   independent reference output, comparing both printed energies and complete
   stdout bytes. Add odd step boundaries 3,7,31,1001 with a separately pinned
   independently generated reference. Confirm exactly two output lines, decimal
   formatting, complete flush and clean stderr/exit.
4. For small N only, a separately hashed source-instrumented twin should record
   step count, the ten-pair order, six velocity stores per pair and fifteen moves
   per step; compare full primitive state after each step against the original
   compact source. Remove neither momentum nor energy work. Do not time the twin
   or treat its altered bytecode as the application. Source review of the sealed
   measured loop must establish that every requested step reaches this work.
5. Run one bounded/pilot size before any 50-million-step attempt, with explicit
   time/RSS limits. Use sequential shuffled fresh-process rounds for the exact
   parent and surviving candidates, at least three samples each at full N.
   Include JVM launch, class loading, HotSpot compilation, GC, all 50 million
   sequential steps, both energies, stdout flush and process exit. No in-process
   warm-up or execution-only timer may replace this metric. A matched Mech control
   may describe cross-language gaps only if its complete required-work/source
   identity and timing boundary are separately qualified.
6. Require full-output equality at N=50,000,000; the retained independent full
   output is `-0.169075164\n-0.169059907\n` (26 bytes). Preserve all valid
   observations and all attempted sources, report medians/spread and source cost,
   and select only within this qualified retained experiment pool. Independent
   source-count approval and a separate guarded append are prerequisites for any
   catalog admission; the older sources and observations remain intact.
