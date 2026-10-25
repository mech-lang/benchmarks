# Prepared-byte-table phases and worker boundaries

Matching phase probes isolate a modest preparation improvement. The combined
kernel uses **0.023698 s** of main-thread CPU, versus **0.025892 s** for its
direct-transform parent. Post-EOF CPU falls from **0.032114 s to 0.029920 s**.
The approximately 2.2 ms difference is an instrumented phase observation;
the two primary sessions still do not establish an incremental elapsed gain
over that parent or repeatable Rust parity.

## Identity and scope

Production source is [8946ccbae9](https://github.com/mech-lang/mech/commit/8946ccbae9ef213e52832b3847c7c019a8e112e2).
The separate diagnostic host is
[5a89d492f4](https://github.com/mech-lang/mech/commit/5a89d492f4f72aaf0093af7cf449d63aefcb6387),
branch `codex/native-joined-byte-table-phase-worker-probe`. Its generated guest
object is identical to the primary executable's object, SHA-256
`0b89b17da711305d88e284a8deef548f5a68dd1273acad703d818b43108d2254`.
The bytecode, resource image, original finite prices and limits remain.

The immediate parent reuses the verified direct-transform diagnostic at
`7fc55235f5`. Both direct subjects have **identical ten-phase probe code,
worker-counter code and chunk boundaries**. The ordinary control retains its
seven-phase probe; clock calls and scopes therefore differ for that comparison.
No clock overhead is subtracted. Probe and binary pins are recorded in
[plan.json](plan.json) and [probe-compatibility.json](probe-compatibility.json).

Eight balanced four-subject orders provide eight full observations per
subject, with every subject in each position twice. Four separate prefix
processes qualify output and boundaries. All native executions are serial
under the original shared mutex; each benchmark runs seven internal workers.
No diagnostic run is excluded, and none is a primary timing observation.

## Preparation CPU

These outer intervals do not overlap. Rust performs transformation before its
input-ready mark; Mech retains a separate transformation interval after EOF.
The scanner and detailed phases below are nested inside these intervals.

| Interval | Candidate | Direct-transform parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| Before capture | 0.007618 s | 0.007515 s | 0.007422 s | Not separately exposed |
| Input/capture | 0.117975 s | 0.118814 s | 0.119334 s | 0.133306 s |
| EOF/input-ready to spawning | 0.029920 s | 0.032114 s | 0.040281 s | 0.000030 s |
| Spawn calls | 0.000068 s | 0.000066 s | 0.000077 s | 0.000076 s |

Width-12 workers start **0.155715 s / 1.167× Rust** after main for the
candidate, **0.158145 s / 1.186×** for the direct parent,
**0.167311 s / 1.254×** for the ordinary control and
**0.133393 s / 1.000×** for Rust. The candidate still launches about 22 ms
later than Rust in this cohort.

| Physical phase, CPU | Candidate | Immediate parent |
| --- | ---: | ---: |
| Borrow row windows | 0.000997 s | 0.001004 s |
| Source scanner | 0.072816 s | 0.073092 s |
| Selected-join admission | 0.000009 s | 0.000009 s |
| Source chunk/geometry/output loan | 0.000648 s | 0.000648 s |
| Combined transform/copy | **0.023698 s** | **0.025892 s** |
| Chunk receipt and retirement | 0.001553 s | 0.001574 s |
| Logical map preparation | 0.000003 s | 0.000002 s |
| Final validity/handoff and logical finish | 0.002340 s | 0.002347 s |

Both direct subjects record 3,848 loan preparations, 3,847 kernel intervals,
3,847 chunk receipts, one map preparation and two finalization intervals.
Their old separate-copy and separate-map phases have zero calls. All Mech
subjects expose 3,881 borrowed windows covering 4,166,671 rows and no cell
windows. Rust has no separately exposed equivalent to these implementation
phases.

The scanner remains near 73 ms; that span is inside input/capture and is not
an additional 73 ms of excess over Rust. The finalization span includes UTF-8
validation and ownership work, so it is not an isolated validation-only cost.

## Long tasks

All seven task widths and raw counter intervals are retained in
[analysis.json](analysis.json). The two long tasks have these counting CPU
medians:

| Width | Candidate | Direct parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| 12 | 0.398554 s / 1.037× Rust | 0.405746 s / 1.056× | 0.407441 s / 1.061× | 0.384152 s / 1.000× |
| 18 | 0.404301 s / 0.995× Rust | 0.400909 s / 0.987× | 0.414878 s / 1.021× | 0.406346 s / 1.000× |

Candidate width-12 and width-18 bodies finish at 0.564545 s and 0.571260 s
after main; Rust finishes at 0.517305 s and 0.540298 s. Width 18 is the later
candidate task in this cohort. All long generated counting functions are
byte-identical to the immediate parent; worker variation is not attributed
to a counting optimization.

Candidate performance/efficiency CPU is 0.3419/0.0593 s for width 12 and
0.3434/0.0598 s for width 18; Rust is 0.2636/0.1200 s and 0.2826/0.1197 s.
Core-specific figures are separate medians and need not sum exactly to the
overall median. Different core residence limits architectural comparisons
from counting CPU alone. Body completion is an in-task boundary before the
OS thread wrapper exits; Rust also retains formatting/drop work in main.

## Verification and next work

[Verification](verification.json) checks **37 terminal owned native
receipts**, all four prefix and 32 full outputs, **224 full worker intervals**,
raw phase schemas and counter monotonicity, respective production objects,
source stability, and all original finite work/resource invariants. Every full
Mech run retains seven complete maps, **874,999,961 original physical updates**
and **854,497 original credited batches**. Each direct subject processes
125 million fused bytes. All processes exit successfully, inherit the mutex,
are reaped and close their groups without signals or cleanup errors. The
canonical benchmark dataset is unchanged.

The next independent compiler experiment makes borrowed-view field access
selective. `Length` currently loads a pointer that it discards before loading
the length. The broader private-home audit must prove allocation, extent,
initialization and lifetime before testing nontrapping flags separately.
Source bounds, callback barriers and finite prices remain required; readonly,
alignment and arbitrary movement promises are not part of that proposal.
