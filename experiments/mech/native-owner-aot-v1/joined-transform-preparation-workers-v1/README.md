# Direct transform/copy preparation and worker boundaries

The actual direct-transform candidate now has its own verified preparation
and per-width diagnostic. Post-EOF main-thread CPU is **0.032061 s**, versus
0.038915 s for its private-buffer parent and 0.040049 s for the ordinary
control. The new combined kernel consumes 0.025861 s. This is a local
instrumented observation; the two primary sessions still do not establish an
elapsed improvement over the immediate parent or Rust parity.

## Scope and identity

Production source is [6cf5877fa9](https://github.com/mech-lang/mech/commit/6cf5877fa9377d422bb7b57b0cff3a8fd9faa636).
The separate diagnostic host is
[7fc55235f5](https://github.com/mech-lang/mech/commit/7fc55235f53386651bc526c1a853e7360451249d),
branch `codex/native-joined-transform-phase-worker-probe`. It links the exact
production guest object, SHA-256
`5d898ffbb2487628c6ff8b461345ec94a3dff4478a1b481bc43a99d77089375c`.
The bytecode, resource image and all object/build checks remain. Only the
copied launcher and its own build-source pin change for the diagnostic host.

The private-buffer parent and ordinary control reuse their separately
qualified diagnostic hosts at `f5391eacf5` and `cf80a3966e`; their objects match
their respective production artifacts. The protected instrumented upstream
Rust program and identical worker-counter probe remain unchanged. Every
binary, receipt, source, script and input is pinned in [plan.json](plan.json)
and [capture-v1/results.json](capture-v1/results.json).

Eight balanced four-subject orders provide eight full observations per
subject. Each subject occupies each position twice. All native jobs execute
serially under the original shared mutex; each process runs seven internal
workers. Four separate prefix processes qualify physical boundaries and
outputs. No diagnostic run is excluded, and none supplies a primary timing.

## Preparation

These are nonoverlapping main-thread CPU intervals from the owned boundary
records. Rust performs its input transformation before its `input_ready`
milestone; Mech retains a separate post-EOF transformation interval. The
per-phase probes below are nested inside these outer intervals.

| Interval | Candidate | Private-buffer parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| Before capture | 0.007569 s | 0.007533 s | 0.007461 s | Not separately exposed |
| Input/capture | 0.117819 s | 0.119952 s | 0.119325 s | 0.133385 s |
| EOF/input-ready to spawning | 0.032061 s | 0.038915 s | 0.040049 s | 0.000030 s |
| Spawn calls | 0.000063 s | 0.000068 s | 0.000075 s | 0.000069 s |

Width-12 workers begin approximately **0.157543 s / 1.179× Rust** after main
for the candidate, **0.166567 s / 1.247×** for the private-buffer parent,
**0.166944 s / 1.250×** for the ordinary control and **0.133576 s / 1.000×**
for Rust. The candidate therefore still launches about 24 ms later than Rust
in this cohort. This is an observed milestone from instrumented programs,
not a primary whole-process duration.

| Physical phase, CPU | Candidate | Private-buffer parent | Ordinary control |
| --- | ---: | ---: | ---: |
| Borrow row windows | 0.001003 s | 0.000989 s | 0.000992 s |
| Source scanner | 0.072811 s | 0.073308 s | 0.074000 s |
| Source chunk/geometry/output loan | 0.000645 s | Not separately instrumented | Not applicable |
| Combined transform/copy | 0.025861 s | Not applicable | Not applicable |
| Chunk receipt and retirement | 0.001544 s | Not separately instrumented | Not applicable |
| Separate copy | Not executed | 0.021737 s | 0.020561 s |
| Separate mapper | Not executed | 0.013614 s | 0.013027 s |
| Map preparation | 0.000002 s | 0.000003 s | 0.001885 s |
| Final validity/handoff and logical finish | 0.002349 s | 0.002346 s | 0.002352 s |

Rust has no separately exposed equivalent to these implementation-specific
phases. The scanner is nested in input/capture; it cannot be added to that
interval. The ordinary selected-join span includes its copy, and is likewise
not an additional cost. The finalization span includes the retained UTF-8
validation and ownership work; it is not an isolated validation-only cost.

The candidate records 3,848 source-loan preparations, 3,847 combined kernel
intervals and 3,847 chunk receipts in every full process. Its legacy separate
copy/map phases record zero calls. The private parent records 3,848 copy
preparations and 3,847 mapper intervals. The ordinary control records one
broad copy and mapper interval each. All Mech subjects expose 3,881 borrowed
windows covering 4,166,671 rows, with no cell-based windows.

The candidate's ten-slot phase probe adds three named intervals to the
controls' seven-slot implementation. [Probe compatibility](probe-compatibility.json)
and [the exact extension](probe-extension.diff) retain the unchanged read-only
clocks, aggregation, row counters, marks and worker probe. Clock-call counts
and scopes differ. Their overhead is not subtracted, and these observations
do not replace primary timings or prove that all preparation differences
transfer to complete-process elapsed time.

## Long counting tasks

All seven widths are retained in [analysis.json](analysis.json). The long
tasks have these counting CPU medians:

| Width | Candidate | Private-buffer parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| 12 | 0.402455 s / 1.049× Rust | 0.406534 s / 1.059× | 0.404320 s / 1.053× | 0.383838 s / 1.000× |
| 18 | 0.409389 s / 1.005× Rust | 0.403145 s / 0.990× | 0.405774 s / 0.996× | 0.407320 s / 1.000× |

Candidate width-12 and width-18 bodies finish at 0.570233 s and 0.575171 s
after main, versus Rust at 0.516575 s and 0.542671 s. The later candidate
task is width 18 in this cohort. Parent and ordinary-control counting
function bytes are unchanged, so their CPU variations are not attributed to
a new counting optimization.

| Width | Candidate instructions | Rust instructions | Candidate P/E CPU | Rust P/E CPU |
| --- | ---: | ---: | ---: | ---: |
| 12 | 4.962 billion | 4.285 billion | 0.3483 / 0.0597 s | 0.2659 / 0.1189 s |
| 18 | 4.869 billion | 4.288 billion | 0.3422 / 0.0597 s | 0.2842 / 0.1261 s |

Core-specific values are separate medians, so they need not add exactly to
the overall CPU median. Performance/Efficiency residence differs substantially
between implementations. Near counting-CPU parity does not establish that
the generated Mech loop is architecturally superior to the Rust loop.

## Verification and next target

[Verification](verification.json) confirms **37 terminal owned native
receipts**, all four prefix and 32 full outputs, **224 full worker intervals**,
physical phase schemas, raw counter monotonicity, respective production guest
objects, unchanged finite limits and source stability. Every full Mech run
retains seven complete maps, **874,999,961 original physical updates**,
**854,497 original credited batches** and the expected fused byte counts.
All processes exit successfully, inherit the original mutex, are reaped and
close their process groups, with no signal or cleanup error. The benchmark
dataset remains unchanged.

The next contained implementation is preparing the map's byte representation
once at its ownership boundary. The retained machine code repeats sixteen
narrowing instructions and three stack-vector reloads per active row despite
the emitter's apparent hoist. The [baseline assembly audit](../preparation-next-round-v1/byte-table-baseline-inspection.json)
records that placement and a surviving unused scanner field load. The next
object must demonstrate that the narrowing and associated reloads disappear
before another extensive timing campaign. Smaller table-derived projections,
selective/nontrapping private-home accesses, maintained scalar graph/SSA
optimization, row-cursor simplification and shared long-loop improvements
remain separate candidates.
