# Compact Clojure typed-array stores

Source-only preparation, 2026-10-20. No compiler, JVM, diagnostic, bounded program
or timing controller has been invoked for this packet. Existing sources, sealed
builders, plans, reports and catalog entries remain unchanged. Native execution
must wait for the root agent's explicit shared-window clearance.

The hypothesis is narrow: replacing the generic `aset-double` call with the
ordinary compiler-recognized `aset` operation on already hinted double arrays
may preserve the original compact expression while improving the compiled
update. The original `doseq` destructuring and three two-element vectors remain.
Their collection construction and boxed values may still dominate; source type
hints do not prove primitive lowering, eliminated allocation or speed.

The exact original parent is SHA-256
`193e26ad8dfd011fd1835d9d67be04bb223d088e6cdd3e2d6302ca8cae2f46d4`.
The two isolated sources differ only in their namespace and these operations:

| Candidate | Changed parent lines | Scope |
| --- | --- | --- |
| `compact-hot-aset` | 36, 37, 42 | Three static `advance` store sites |
| `compact-all-aset` | 17, 36, 37, 42 | The same sites plus the explicitly hinted momentum store |

The complete one-line substitutions are recorded in the adjacent `.patch` files
and [plan.json](plan.json). Both retain 49 nonblank physical lines and propose
109 units under the exact historical constructor/control/closer owner rule.
[source-ownership-proposed.json](source-ownership-proposed.json) carries every
line's inherited units; approval remains false. The original parent's separately
qualified 63 logical units are only an expectation for these new exact sources;
neither candidate has a native-reader count certificate yet.

All original initialization, momentum, energy calculations, argument parsing,
formatting and support calls remain. Every step visits the ten pairs in the
original order, traverses axis/delta pairs 0, 1, 2, writes `a` then `b`, and only
then advances all positions. At 50 million steps this is 500 million pair
interactions and square roots, three billion velocity stores, and 750 million
position stores. These are source-derived counts, not a dynamically instrumented
inner-loop observation. No workload-specific helper or native kernel is added.

The current qualified scalar primitive source is retained unchanged as
`primitive-control` (111 retained units / 52 physical lines). Its matched whole
process median was 2.661471542 seconds, versus 155.866933375 for the historical
compact source in that cohort. Those observations supply context; they are not
measurements of either new compact candidate. The new control will be compiled
and launched under the same protocol as the candidates. No globally fastest
implementation claim is made.

## Prepared execution boundaries

The local [runtime-build.json](runtime-build.json) is a byte-identical copy of the
qualified Clojure 1.12.6 / Temurin 25.0.4.1+1 / spec.alpha 0.5.238 /
core.specs.alpha 0.4.74 receipt. Its paths deliberately identify the already
restored exact toolchain, rather than create another unpinned runtime. Before any
build, the controller verifies the receipt copies and all retained runtime/JAR
pins. Licenses and version evidence remain in that complete original receipt.

The newly copied controllers have their own stable experiment paths; no sealed
controller module or global constant is mutated. All child processes inherit the
common timing lock, use fresh process groups and retain complete streams,
commands, environment, exit/resource/power records and exclusive attempt
directories. Builds use direct linking, reflection warnings and the same JVM
flags. Only the exact previously reviewed warning in the unchanged, unused
generic jobs helper is allowed; application warnings stop qualification. Failed
attempts are preserved and require a new output directory.

After root clearance, the prepared order is:

1. Compile four isolated applications: original compact, qualified primitive
   control, compact hot-store variant, compact all-store variant. Save every
   class hash and `javap` output for both `advance` and `offset-momentum`.
2. Inspect the actual generated `advance` methods. Compare typed `RT.aset` array
   overloads, generic setter calls, primitive versus boxed math, vector/sequence
   construction and remaining loop structure against both controls. Retained
   bytecode evidence is not proof of measured heap allocation: HotSpot may
   eliminate allocations later.
3. Compare all 35 raw double slots and raw energy bits for fresh bodies, after
   momentum and after every advance for N = 0, 1, 2, 3, 10, 100. The probe invokes
   the actual compiled application functions: 464 total advance calls across
   four implementations. It does not substitute a transition helper or claim
   dynamically counted inner pair/store operations.
4. Prepare the execution plan only after those exact build/state receipts exist.
   Run all four sources against six shared independent reference cases and the
   four odd cases 3, 7, 31, 1001: 40 complete JVM processes. Retain both the
   established absolute 1e-8 rule and exact byte-equality results.
5. Only after all bounded checks pass, screen the primitive control and the two
   compact candidates at one million steps. The slow original parent is omitted
   from this new timing screen. All three fresh-process observations are retained
   and compared to the matched, already qualified primitive control. This is a
   diagnostic screen, not chart data or independent full-output qualification.
6. If a compact candidate is promising, the root agent may prepare a separate
   explicit selection/full protocol for three shuffled, complete 50-million-step
   rounds against the primitive control. The present runner exposes no full mode.
   A full run requires complete output and exact source/count review before any
   additive admission. Avoid paying for another slow original-parent full cohort.

The controllers are prepared but have not been run:

```sh
python3 experiments/clojure/compact-primitive-v1/build_candidates.py --output experiments/clojure/compact-primitive-v1/build-v1
python3 experiments/clojure/compact-primitive-v1/run_state_probe.py --output experiments/clojure/compact-primitive-v1/state-probe-v1
python3 experiments/clojure/compact-primitive-v1/run_serial.py --prepare
python3 experiments/clojure/compact-primitive-v1/run_serial.py --mode bounded --output experiments/clojure/compact-primitive-v1/bounded-v1
python3 experiments/clojure/compact-primitive-v1/run_serial.py --mode pilot --bounded-report experiments/clojure/compact-primitive-v1/bounded-v1/report.json --output experiments/clojure/compact-primitive-v1/pilot-v1
```

Source authorship is the current Codex GPT-6 family context only; exact model
version is unknown. The original local predecessor's source lineage and inherited
terms remain unresolved. This packet does not infer an old author or license
from the new substitutions.
