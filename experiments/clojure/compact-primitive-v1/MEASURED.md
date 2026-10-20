# Compact Clojure: the measured size–speed tradeoff

The compact typed-store candidate preserves the original loops and source size
and completes the full 50,000,000-step workload in a median **22.217 s**. The
six-store control has a median **2.690 s** in the same three matched rounds.
Compact is **8.26× slower**, with fewer written source units.

| Implementation | Complete-process samples (s) | Median (s) | Sample SD (s) | Retained LOC / physical | Logical units |
| --- | --- | ---: | ---: | ---: | ---: |
| Six explicit typed stores | 2.665, 2.692, 2.690 | 2.690 | 0.015 | 111 / 52 | 66 |
| Compact typed stores | 22.092, 22.217, 22.303 | 22.217 | 0.106 | 109 / 49 | 63 |

The [full report](hot-only-v2/selected-full-v1/full-v1/report.json) retains exact
precision, all six process receipts and complete streams. Every output is the
exact independent 26-byte reference, including both energy lines. All source,
runtime, class and prerequisite pins remain unchanged.

## What changed

The compact candidate changes exactly three `advance` store expressions from
`aset-double` to typed `aset`, plus its namespace. It keeps the original
`doseq` over `[[0 dx] [1 dy] [2 dz]]`, the position loop, all arithmetic groupings,
pair ordering, momentum, energy, iteration count, formatting and generic support.
This is a smaller alternative to the explicit six-store implementation.

Its actual compiled `advance` has five typed `RT.aset([DID)D` sites, while still
containing vector construction, three `Double.valueOf` sites and generic numeric
axis arithmetic. The six-store control has seven typed sites and lacks those
particular boxing/vector sites. These are bytecode locations, not measured
dynamic allocations; HotSpot can optimize some intermediate objects.

The original compact source's older saved median remains **165.365 s**. Its
historical samples are preserved. This study compares compact typed stores with
the already fast six-store control; it does not supply a freshly randomized
before/after effect estimate against that older source. The earlier
[matched original-versus-six-store experiment](../optimization-v1/primitive-v1/README.md)
retains its separate 58.56× effect estimate.

## Qualification and limits

The initial all-store variant produced a new application warning in momentum
initialization. That failed build and all warnings remain retained; the warning
was not accepted. A separate hot-only build and qualification then passed all
30 bounded complete-output cases and 348 three-way state/energy comparisons,
with all 35 floating-point slots agreeing bit for bit. The full plan selected
compact deliberately for its expressiveness tradeoff despite its slower pilot.

The [approved retained count](source-ownership-approved.json) gives 109 / 49 by
exact inheritance from the original owner ledger. A separate native-reader
capture under `logical-source-owners.clojure-v1` reports 63 application units and
18 excluded generic-support units; it requires its own explicit admission
binding. Retained LOC, logical units and future formatted lines remain distinct.
The all-store source's matching unit count does not qualify its failed build.

All six timings include a fresh JVM, class loading and JIT, every simulation
step, garbage collection, complete output/flush and exit, with one shared serial
timing lock. The result establishes these two retained choices, not minimum
possible Clojure source or the fastest possible implementation. Catalog admission
is separate and must preserve the existing fast profile and historical samples.
