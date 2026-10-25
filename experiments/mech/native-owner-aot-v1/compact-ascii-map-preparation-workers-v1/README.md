# Compact mapping: matching phases and worker boundaries

Matching actual-path probes localize a preparation improvement to the compact
mapping kernel. Kernel CPU falls from **0.023746 s to 0.016196 s** against
the retained byte-table anchor. The enclosing post-EOF CPU interval falls
from **0.029937 s to 0.022381 s**. These diagnostic measurements explain the
intended local effect; the separate [primary campaign](../compact-ascii-map-v1/README.md)
establishes complete-process gains and does not establish repeatable Rust parity.

## Identity and method

Production source is `d1ae94f68423c88602ee55794fc47ea0da0e05a3`.
The separately instrumented host is `3e756f8fb7ed729539fffb03cfa121d3b9fe3243`,
branch `codex/native-compact-ascii-phase-worker-probe`. Its guest object is
identical to the primary build, SHA-256
`90ea49092ba3f53cd57ac80305b3bdb63d2d6db2cf32519c3c80e56b9dda7c37`.
The diagnostic executable is pinned by [verification.json](verification.json).

The parent subject is the byte-table anchor's retained diagnostic host at
`5a89d492f4`, rather than the slower selective-field immediate parent. Both
subjects have identical ten-slot phase probes, worker probes and chunk
boundaries. The ordinary control uses its retained seven-slot probe. Rust uses
the retained instrumented upstream source and executable. Probe and build pins
are in [plan.json](plan.json) and [probe-compatibility.json](probe-compatibility.json).

Eight balanced orders provide eight full processes per subject; every subject
occupies every position twice. Four prefix processes separately qualify output
and boundaries. All processes run serially under the original shared mutex.
All 874,999,961 original updates, 854,497 credited batches, seven tasks and
complete stdout are checked. No observation is excluded or counted as a primary
elapsed sample. Probe overhead is retained, with no subtraction.

## Preparation CPU

The outer intervals below do not overlap. Their nested implementation phases
in the following table must not be added to them.

| Outer interval | Compact | Byte anchor | Ordinary | Rust |
|---|---:|---:|---:|---:|
| Before capture | 0.007689 s | 0.007617 s | 0.007487 s | Not separately exposed |
| Input/capture | 0.119498 s | 0.118184 s | 0.119148 s | 0.133842 s |
| EOF/input ready to spawn | **0.022381 s** | 0.029937 s | 0.040014 s | 0.000030 s |
| Spawn calls | 0.000065 s | 0.000064 s | 0.000074 s | 0.000075 s |

| Nested physical phase | Compact CPU | Byte anchor CPU |
|---|---:|---:|
| Borrow row windows | 0.000998 s | 0.000998 s |
| Source scanner | 0.073485 s | 0.073127 s |
| Source/geometry/output loan | 0.000647 s | 0.000655 s |
| Transform/copy kernel | **0.016196 s** | 0.023746 s |
| Chunk receipt/retirement | 0.001548 s | 0.001515 s |
| Final validity/owner handoff | 0.002316 s | 0.002315 s |

The scanner remains inside input/capture; its approximately 73 ms is not
additional overhead on top of Rust's whole input span. The finalization phase
contains ownership work as well as UTF-8 validation. Both subjects retain
3,881 row windows, 4,166,671 rows, 3,848 loan preparations and 3,847 kernel and
receipt intervals. The old standalone copy/map spans remain unused.

Width-12 workers start at **0.149685 s / 1.117× Rust** after main, versus the
byte anchor **0.156442 s / 1.168×**, ordinary control **0.167004 s / 1.247×**
and Rust **0.133952 s / 1.000×**. The compact candidate's remaining launch
lag is approximately 15.7 ms in this cohort.

## Long tasks

| Width | Compact counting CPU | Byte anchor | Ordinary | Rust |
|---|---:|---:|---:|---:|
| 12 | 0.410656 s / 1.056× Rust | 0.403545 s / 1.037× | 0.409985 s / 1.054× | 0.388968 s / 1.000× |
| 18 | 0.396493 s / 0.991× Rust | 0.411695 s / 1.029× | 0.404361 s / 1.011× | 0.400108 s / 1.000× |

Candidate body completion is 0.572340 s for width 12 and 0.556146 s for width
18 after main; Rust is 0.522350 s and 0.535135 s. Width 12 finishes last in
this cohort. The previous byte-table cohort had width 18 last. Every counting
body remains byte-identical, and different P/E-core residence is recorded;
these movements are not attributed to a new counting optimization. Both long
loops remain targets. Body completion precedes thread-wrapper exit, and Rust
publishes/drops its returned maps differently from Mech.

## Verification

[Analysis](analysis.json) retains every interval, per-core counter and all seven
widths. The [verifier](verify.py) recomputes worker durations and phase medians
from raw receipts, checks 224 full worker intervals, every source/object/input
pin and all **37 terminal owned processes**. All processes exit successfully,
are reaped and have closed groups, without cleanup signals.

The preliminary copied capture driver rejected the wrong candidate-object pin
before launching any benchmark. Its original script and
[failure record](capture-prerun-failure.json) remain. `capture-v2.py` corrects
that pin; its one capture supplies all observations above. No successful native
observation was repeated to repair analysis.

The compact mapper's measured preparation saving is established. The next
compiler target is pure-scalar graph/state execution: carrier/view materialization
and repeated per-site dispatch. Shared improvements to both long hash loops
follow; final validation and chunk administration have smaller measured scope.
