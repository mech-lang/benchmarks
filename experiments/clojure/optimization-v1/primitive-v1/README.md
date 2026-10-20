# Typed Clojure n-body updates

The typed-store candidate reduced the median complete-process time from
**155.866933375 s to 2.661471542 s**, or **58.56× faster**, in three matched
50,000,000-step rounds. All six complete stdout streams match the independent
26-byte reference exactly. This result establishes an improvement over the
retained compact implementation, not a globally fastest Clojure program.

| Implementation | Samples (s) | Median (s) | Sample SD (s) |
| --- | --- | ---: | ---: |
| Original compact control | 153.608345959, 156.791277292, 155.866933375 | 155.866933375 | 1.637410591 |
| Typed primitive updates | 2.661471542, 2.714510416, 2.658480875 | 2.661471542 | 0.031520828 |

The effect estimate uses these fresh matched observations. The control's older
165.364857875 s median is retained as historical evidence and is not the
denominator of the reported improvement. The comparison uses a restored exact
Temurin 25.0.4.1+1 ARM64 JDK and Clojure 1.12.6, with identical JVM options,
runtime/JAR versions, generic support and build policy for both sources.

## Change and required work

The original source constructs and destructures `[[0 dx] [1 dy] [2 dz]]` inside
every body pair and writes through `aset-double`. The candidate writes the six
velocity components explicitly and uses `aset` with the existing `^doubles`
array hints. It also uses typed `aset` in the unchanged position loop.
The retained scalar-updates intermediate isolates the first change; its pilot
was only modestly faster than the control. Compiler inspection identifies the
typed array operations as the important additional change, rather than simply
assuming that source-level type annotations guarantee efficient code.

The compiled candidate `advance` has seven typed `RT.aset([DID)D` call sites and
no `Double.valueOf` or tuple construction in that method. Bytecode establishes
the lowering of these expressions; it does not measure heap allocations after
HotSpot optimization. No native n-body helper, precomputed answer, changed
integrator, parallel time step or unchecked/fast-math option is introduced.

Each of the 50,000,000 sequential steps retains all ten body pairs in the same
order, the same floating-point evaluation groupings, six velocity writes per
pair and fifteen position writes after the pair updates. Thus the source calls
for 500,000,000 pair interactions, 500,000,000 pair square roots/divisions,
3,000,000,000 velocity stores and 750,000,000 position stores. These are
source-derived work counts; inner operations were not instrumented during the
timed runs. Momentum adjustment and both energy computations remain.

The separate state probe compares all 35 raw floating-point state components
and the energy after each tested step: all 348 tested `advance` calls agree
bit for bit across the three qualified sources. Thirty bounded output tests
also pass, including zero, odd and larger iteration counts.

## Measurement and source accounting

The [preselected plan](selected-full-v1/plan.json) chose the original compact
control and typed-store candidate before the full run, using the lowest pilot
time among the two qualified candidate forms. The scalar intermediate's source,
pilot, build and bounded results remain available; it was not timed at full size.
The initial scalar-moves proposal remains a separate unmeasured alternative.
This selection does not establish the best possible unrolling or representation.

The [full report](selected-full-v1/run-v1/report.json) retains every observation,
shuffled round order, raw process receipts, stdout/stderr and power checks.
One shared mutex prevents overlapping benchmark jobs. Every observation includes
JVM launch, class loading, JIT compilation, garbage collection, all simulation
steps, output/flush and exit. Hashing, reference validation and machine checks
are outside the timer. All 659 prerequisite/source/runtime/class pins remain
unchanged, and all six processes finish without timeout or leftover child groups.

The candidate main has **111 retained-rule application LOC / 52 significant
physical lines**, compared with **109 / 49** for the compact control. The
unchanged generic support remains visible in the submitted bundle and excluded
from application LOC under the existing reviewed scope. The
[approved line ledger](source-ownership-approved.json) extends the retained
counting convention to the exact source; it does not certify a universal logical
LOC rule, a canonical formatter or minimal expressive size. Byte, gzip and BPE
measurements must use the same reviewed application scope at catalog admission.

All earlier proposal, build, qualification, failure and pilot records remain
unchanged. The new edit's recorded authorship identifies the Codex GPT-6 family;
the exact model variant and unresolved predecessor provenance are not inferred.
Catalog admission and publication are separate from this measurement report.
