# Pure scalar source execution: preparation and worker boundaries

Matching actual-path probes localize the pure-scalar improvement to the source
scanner. Scanner CPU falls from **0.073576 s to 0.031846 s**, a 56.7% reduction
against the compact parent. The enclosing input/capture CPU interval falls
from 0.119627 s to 0.077017 s. The transform/copy kernel remains near 0.0162 s.
The separate [primary campaign](../pure-scalar-state-v1/README.md) establishes
the complete-process parent improvement and practical matching Rust medians;
this diagnostic does not replace those timing samples.

## Identity and method

Production source is `93015bc6298b77fd10402e88baea5e3bfd89b28d`.
The separately instrumented host is `bab1dedbe95473bbc61606adb9cc5cd237034a2b`,
branch `codex/native-pure-scalar-phase-worker-probe`. It preserves the exact
timed guest object, SHA-256
`d612ceb28aed0c80d4102f6572205873a04a5116d891a17a75dab27b8cc29dfa`.
The diagnostic executable is
`12c1dd16f92cb143f93bede659f1c6058c4225907e572c0ebd1b4ad7ad66da8c`.

The immediate parent uses the retained compact-mapper diagnostic. Both use
identical ten-slot phase probes, worker probes and chunk boundaries. The
ordinary control retains the seven-slot probe; Rust retains its instrumented
upstream implementation. All pins are in `plan.json`, `build-candidate.json`
and `probe-compatibility.json`.

Four prefix processes qualify boundaries and output. Eight balanced full
orders give eight processes per subject, with every subject occupying each
position twice. All processes run serially under the original shared mutex.
All 874,999,961 full table updates, 854,497 credited batches, seven workers and
complete stdout pass verification. No run is excluded. These are instrumented
diagnostics with no probe-overhead subtraction and no primary timing samples.

## Main-thread preparation

The following outer CPU intervals do not overlap. Nested phases below must not
be added to them.

| Outer interval | Scalar | Compact parent | Ordinary | Rust |
|---|---:|---:|---:|---:|
| Before capture | 0.007600 s | 0.007589 s | 0.007451 s | Not separately exposed |
| Input/capture | 0.077017 s | 0.119627 s | 0.119337 s | 0.133257 s |
| EOF/input ready to spawn | 0.022454 s | 0.022534 s | 0.040220 s | 0.000030 s |
| Actual spawn calls | 0.000065 s | 0.000068 s | 0.000070 s | 0.000072 s |

| Nested phase | Scalar CPU | Compact parent CPU |
|---|---:|---:|
| Borrow row windows | 0.000978 s | 0.000995 s |
| Source scanner | **0.031846 s** | 0.073576 s |
| Source/geometry/output loan | 0.000644 s | 0.000648 s |
| Transform/copy kernel | 0.016151 s | 0.016259 s |
| Chunk receipt/retirement | 0.001592 s | 0.001583 s |
| Final validity/owner handoff | 0.002352 s | 0.002358 s |

The scanner remains inside input/capture, rather than additional overhead
on top of Rust's input interval. Both Mech subjects preserve 3,881 row-window
and scanner intervals, 3,848 loan preparations, 3,847 kernel and receipt
intervals, and 4,166,671 rows. Finalization includes ownership work as well as
UTF-8 validation.

## Long workers

| Diagnostic span | Scalar | Compact parent | Rust | Scalar / Rust |
|---|---:|---:|---:|---:|
| Width-12 worker start after main | 0.107306 s | 0.149479 s | 0.133408 s | 0.804× |
| Width-12 counting CPU | 0.405143 s | 0.415827 s | 0.384568 s | 1.054× |
| Width-18 counting CPU | 0.402731 s | 0.403498 s | 0.403744 s | 0.997× |
| Width-12 body complete after main | 0.526280 s | 0.575490 s | 0.516253 s | 1.019× |
| Width-18 body complete after main | 0.523488 s | 0.564733 s | 0.536717 s | 0.975× |

The scalar candidate now starts its long workers approximately 26.1 ms before
Rust. Width 12 finishes last in this cohort. Counting bodies remain identical
to the compact parent; different core residence and execution conditions mean
their varying CPU medians are not attributed to a new counting optimization.
Rust's return-map publication/drop boundaries differ from Mech's worker
publication and retirement. Both long loops remain performance targets.

## Verification and next target

`verify.py` independently recomputes phase medians and 224 full worker
intervals from the raw receipts. All **37 owned processes**, including the
diagnostic build, exit successfully, are reaped and have closed groups without
cleanup signals. Guest object, bytecode, resource image, source, input and
canonical dataset pins remain intact.

An initial preparation command referenced `verification-v2.json`, while the
version-two verifier writes `verification.json`. Both the setup and missing
build-spec checks stopped before launching a native process. The corrected
reference and no-launch failure record are retained. No successful native
observation was repeated to repair analysis.

The scanner saving is established and earlier preparation assumptions are
superseded by these actual-candidate measurements. The next contained compiler
experiment targets candidate payload/count loads in both ordinary long hash
loops, with bounded pipelining retained as a subsequent alternative. It must
preserve full-key equality, every original table update and source arithmetic,
finite prices, slow-path fallback and all admission/error boundaries.
