# Clojure n-body: exact primitive-store qualification

This records pre-screen qualification, before any 1-million-step pilot or full
50-million-step timing. No existing source, catalog profile or observation is
changed. Root owns subsequent measurements and any admission. Application LOC
remains **proposed, not independently approved**.

The initial [source packet](../README.md) retained scalar-updates and scalar-moves.
Actual bytecode revealed a further ordinary Clojure idiom: `aset-double` is a
general Clojure function call whose value argument is boxed, whereas `aset` on
the existing `^doubles` locals resolves to the primitive Java overload. The
new [primitive-updates source](sources/clbg/nbody/primitive_updates.clj) replaces
the seven `aset-double` call sites inside `advance` only. It keeps the scalar
six-store pair update and the original position loop. Initialization, momentum,
energy, pair order, store order, multiplication grouping, division, square root,
time-step loop and output remain unchanged. Its exact SHA-256 is
`12d61dd8a07254f6ba94652fb30b63cc305ec0145e482f1136044a1dc8c88fe2`.

The matched pool is:

| Source | Proposed retained-rule application LOC / physical LOC | Role |
| --- | ---: | --- |
| Original compact | 109 / 49 (already retained count) | Matched parent; historical median 165.364857875 seconds |
| Initial scalar-updates | 111 / 52 (unapproved proposal) | Isolate vector/destructuring removal |
| Primitive-updates | 111 / 52 (unapproved proposal) | Further remove generic `aset-double` stores in `advance` |

The historical two-pass optimized source remains 207.674197292 seconds. The
initial scalar-moves source remains available with its initial raw-state proof;
it is not silently substituted for either source in this matched pool.

## Runtime and compiled inputs

The [restored runtime receipt](runtime-build.json) matches the exact retained
Temurin 25.0.4.1+1 ARM64 full-JDK archive, all **403** extracted JDK file hashes,
and all three Clojure/spec JAR hashes. Actual `java`, `javac`, `javap`, version,
architecture, linked-image, Clojure 1.12.6, available-processor and G1 collector
records are under [the restoration attempt](../build-v1/). No system Java or
newer dependency is used. The copied receipt hash is
`8a77c406dacff8f397359bba295d2f92ece05ee2270c2f7c83f517ac576e9f3a`.

All three complete mains and byte-identical support compile in isolated packages
with direct linking true, reflection warnings enabled, the same JVM flags and
controlled environment. Each build has 21 pinned generated class files. The
[build receipt](builds.json), raw compiler output and actual `javap` output are
retained in [build-v1](build-v1/). Its hash is
`1f3099f38ebc295bfb3173c3ead7cde039b0204ba7891e41c5a0687a6445c159`.
The build-time process helper's exact source snapshot and its relation to the
later execution controller are retained in [build-proof-closure.json](build-proof-closure.json);
the old build receipt is unchanged. The later additions extend plan evidence
closure and do not alter the process helper used by compilation.

The only accepted compiler warning is the exact pre-existing
`clbg/support.clj:19:16` unresolved `.get` in the generic worker-pool helper.
N-body does not call that helper. No application reflection warning is accepted,
and no source/support rewrite hides it. Earlier failures remain separate:
the sandbox denied the first process-list preflight; the first parent build
stopped at this warning gate; a build-only continuation stopped before compilation
on a metadata path join that was then corrected. Their records are retained in
[preflight-v1](../preflight-v1.json), [build-v1](../build-v1/report.json) and
[build-v2](../build-v2/report.json). The completed initial scalar builds remain
in [build-v3](../build-v3/report.json).

Actual `advance` bytecode shows:

- The parent creates three two-element Tuples and one three-element Tuple in
  the pair loop, then uses Object/long index arithmetic and Object/double
  multiplication for the destructured values.
- Scalar-updates removes those Tuple operations and uses primitive double
  arithmetic, but still boxes store values through `Double.valueOf` before
  `clojure.core$aset_double.invokeStatic`.
- Primitive-updates has seven static `RT.aset:([DID)D` call sites, primitive
  double loads/arithmetic, and no Tuple construction or `Double.valueOf` in
  `advance`. This is a general typed array operation, not a native n-body helper.

Those are compiler-output facts. HotSpot may inline the functions or eliminate
some boxes/allocations in any version. This inspection supplies no measured heap
allocation count, machine-code instruction count or speedup claim.

## Bounded output and state evidence

[bounded-v1/report.json](bounded-v1/report.json) passes **30/30** checks: all
three sources at N=0,1,2,3,7,10,31,1000,1001,10000. Six expected outputs come
from the unchanged shared corpus; four odd-boundary outputs are generated outside
timers by the exact pinned independent shared C3/Python reference. Its formula
and representation are independent of the candidate edits. All thirty complete
outputs happen to match reference bytes exactly. The established n-body contract
is still two finite energy lines with absolute tolerance 1e-8; byte equality is
reported separately rather than redefining that cross-language contract. The
bounded report hash is
`c3f0777f69307134fe9383e4aab8fe1b10e59d9a55d185dd10e785ce9b288d56`.

The [untimed raw-state probe](state-probe-report.json) passes independent cases
N=0,1,2,3,10,100. It uses the actual compiled application functions, compares all
35 state slots (including masses and signed zero) by raw double bits before and
after momentum and after every step, and compares energy bits at each checkpoint.
It makes **348 actual calls** to the three `advance` functions. Its hash is
`9cbbb2b59c533207e624f51723c0a986f4a2ab8b087bd5bbc17754e9d3ea3805`.
This is stronger than comparing rounded final energies. Inner pair/store counts
remain source-derived; the probe does not claim dynamically instrumented inner
counters or a full-size work trace.

The unchanged source loop requires every requested step, ten pairs in canonical
order, six velocity stores per pair, and fifteen position stores after all pair
impulses. Full N therefore requires 500,000,000 pair interactions and square roots,
3,000,000,000 velocity stores and 750,000,000 position stores, plus momentum and
both energies. No closed-form state, force cache, changed arithmetic grouping,
parallel time steps or foreign workload executor is introduced.

## Root-owned screening and full measurements

[execution-plan.json](execution-plan.json) pins the exact runtime, inputs, generated
classes, state proof, shared references, controller and dependencies. Its hash is
`cb43a5a01cfafa8c441e0c9ee8a13d1abcfe84cc1b14f3ff247bc74f96c92195`.
The controller uses the common lock, sequential fresh process groups, inherited
lock descriptors, watchdog limits, complete streams, raw process receipts and
before/after power checks. No pilot or full sample was taken during qualification.

The root can run the diagnostic 1-million-step screen:

```
python3 experiments/clojure/optimization-v1/primitive-v1/run_serial.py --mode pilot --bounded-report experiments/clojure/optimization-v1/primitive-v1/bounded-v1/report.json --output experiments/clojure/optimization-v1/primitive-v1/pilot-v1 --timeout 120
```

The screen requires all three sources. It checks two finite energy lines and
agreement with the matched parent; it is explicitly diagnostic, not independent
output qualification or chart data. Startup, class loading, JIT, GC, output and
process exit remain included. Every observation stays in the report.

After that, three shuffled sequential full rounds can compare all three sources
or `--sources parent primitive-updates` after retaining the screen's complete
pool. The full invocation is:

```
python3 experiments/clojure/optimization-v1/primitive-v1/run_serial.py --mode full --bounded-report experiments/clojure/optimization-v1/primitive-v1/bounded-v1/report.json --pilot-report experiments/clojure/optimization-v1/primitive-v1/pilot-v1/report.json --output experiments/clojure/optimization-v1/primitive-v1/full-matched-v1 --timeout 600
```

Only full N=50,000,000 complete-process observations are eligible for future chart
review. Keep the source-count proposal, required-work review, independent output
checks, candidate comparison and publication admission as separate gates. There
is no globally optimal or fully idiomatic claim.
