# Direct transformation into the joined buffer

This candidate is correctness-qualified but **unpromoted**. It removes the
separate copy-then-map passes from the private-buffer foundation. Neither of
the two complete-process sessions establishes an improvement over that
immediate parent: both paired 95% intervals include zero. Rust parity remains
unproved.

## Complete-process measurements

Each session contains eight balanced four-subject orders, with eight measured
processes per subject. The second session reverses the order list. All
subjects execute serially under the existing shared mutex; seven workers
execute inside each benchmark. Mech measurements include secured startup
through exit. There are no excluded full-input warmups or outliers.

| Session | Direct transform/copy | Private-buffer parent | Ordinary control | Exact Rust #7 |
| --- | ---: | ---: | ---: | ---: |
| [1](../full-joined-transform-copy-v1/results.json) | 0.599896 s / 1.081× Rust | 0.596161 s / 1.074× | 0.600785 s / 1.082× | 0.555099 s / 1.000× |
| [2](../full-joined-transform-copy-v2/results.json) | 0.596367 s / 1.033× Rust | 0.606544 s / 1.051× | 0.612990 s / 1.062× | 0.577257 s / 1.000× |

| Paired candidate change | Session 1; 95% interval | Session 2; 95% interval |
| --- | ---: | ---: |
| Versus private-buffer parent | +0.50%; [−1.41%, +1.46%] | −1.86%; [−3.87%, +0.24%] |
| Versus ordinary control | −0.56%; [−2.79%, +1.13%] | −2.87%; [−4.73%, −1.33%] |

The Rust observations range from 0.545940 to 0.987317 seconds across these
sessions; every observation is retained. The second-session ratio therefore
does not establish a stable 3% gap or Rust parity. No further primary cohort
has been selected to obtain a preferred result.

The separate one-million-base [prefix cohort](../joined-transform-copy-timing-v1/results.json)
gives 0.088385 s / 4.552× Rust for the candidate, 0.093345 s / 4.807× for the
private-buffer parent and 0.019418 s for Rust. Each subject has one excluded
prefix warmup and three measured processes. These measurements are not pooled
with the full-input observations.

## Implementation and unchanged workload

Production source is [6cf5877fa9](https://github.com/mech-lang/mech/commit/6cf5877fa9377d422bb7b57b0cff3a8fd9faa636),
branch `codex/native-joined-transform-copy`. Its production implementation is
unchanged after `1edeacb453`; the final commit updates three exact-ABI test
fixtures and adds explicit rejection of the previous encoding. Typed IR87 and
ABI31 separate the new private geometry/initialization receipt. Work policy69
and the original finite admission prices and limits remain.

The engine moves an actual retained source chunk into a constructor-private
owner. That owner keeps the source allocation, LF offsets and original account
claims alive throughout the native call. Six checked geometry words describe
the selected rows. The generated function reads those immutable source bytes,
applies the admitted ASCII mapping and stores directly into the final
destination's spare capacity. No payload copy precedes that transformation.

A seventh word publishes the exact initialized extent only after complete
geometry and capacity checks. The host keeps the original vector length until
it verifies the receipt, immutable geometry, original allocation, capacity,
logical site and live loan. It then advances the initialized length. Replay,
changed geometry, moved allocation and incomplete or excessive initialization
are rejected. The original fixed metadata envelope covers the new owner.

The kernel handles arbitrary eligible ASCII tables and bounded physical row
geometries, including CRLF and lone EOF rows. A missing mapping preserves its
first ordinal, copies the remaining raw bytes and defers the error to the
original logical lookup boundary. Unsupported cases retain the existing path.
The private-buffer foundation's single UTF-8 validation remains; this trial
does not claim to have removed every remaining preparation scan.

Source, bytecode, resource image, full input and launch limits are unchanged.
Every full Mech process verifies the complete output, seven complete maps,
**874,999,961 original physical updates** and **854,497 original credited
batches**. Candidate and private-buffer parent both process 125 million bytes
through the fused path. There is no input-name, content or nucleotide-specific
recognition, reduced query set, replacement counting routine or altered map
growth policy. No benchmark dataset timing is replaced by this experiment.

## Qualification and code inspection

The final clean source passes 404 native tests, 30 line-storage tests, 36
finite-credit tests, one catalog test, three generated-kernel tests, seven
focused source/error tests and two focused chunk-owner tests. Three existing
manual native tests remain ignored. The kernel tests exercise all 128 ASCII
inputs, valid zero outputs, missing markers, lengths and alignments, inactive
mapping, CRLF/EOF geometry, unchanged sources and sentinel-protected output
extents. Source tests include original and decoded artifacts, finite budgets
and the original failure ordering. Fault tests reject invalid initialization
receipts, stale geometry and changed target allocations.

Two earlier failed qualification attempts remain in the record: a Rust module
visibility/report-path build failure and three stale ABI30 test fixtures. They
are not qualifying executions. All final scopes run at the exact committed
source above.

[Object inspection](code-inspection.json) verifies one new generated copy/map
function: 980 emitted code bytes, a 1,024-byte Mach-O symbol span and a
160-byte stack frame. All eight existing nonentry functions remain
byte-identical to both controls, including both long counting-loop families
and the ordinary mapper. The main entry changes at the new call while its
symbol span remains 43,636 bytes, equal to the private-buffer parent.

The candidate executable is **5,501,264 bytes**, versus 5,484,736 bytes for
the private-buffer parent. Its machine text is **4,329,140 bytes**, versus
4,321,796 bytes. Candidate primary peak RSS medians are 163.42/163.06 MB;
the private-buffer parent is 163.46/163.35 MB and Rust is 140.99/140.43 MB.
No memory or binary-size improvement is established.

## Separate profiles and counters

Three fresh captures per subject match the timed candidate's entire machine
text, not only its guest object. The [profile analysis](analysis.json) retains
waits and partial unwinds. Of 3,814 Mech worker observations, 85.79% are in
generated counting loops, 6.87% in active storage helpers, 3.28% in active
accounting and 0.73% in accounting waits. The new generated transform/copy
function appears in 64 main-thread observations. Sampling observations are
not recoverable elapsed-time shares.

Sixteen independent balanced [counter processes](counters/results.json), four
per subject, give these medians:

| Diagnostic | Candidate | Private-buffer parent | Ordinary control | Rust |
| --- | ---: | ---: | ---: | ---: |
| Instructions | 24.428 billion | 24.433 billion | 24.518 billion | 33.205 billion |
| Cycles | 5.804 billion | 5.930 billion | 5.935 billion | 8.081 billion |
| User CPU | 1.645 s | 1.675 s | 1.680 s | 2.385 s |
| System CPU | 0.030 s | 0.030 s | 0.030 s | 0.030 s |

These diagnostics do not establish a primary elapsed improvement. The long
counting functions are unchanged. The separate [actual-path phase/per-width
diagnostic](../joined-transform-preparation-workers-v1/README.md) now measures
0.032061 s after EOF, including 0.000645 s of source-loan preparation,
0.025861 s in the combined transform/copy kernel and 0.001544 s in chunk
receipt checks/retirement. Its 37 terminal receipts and 224 full worker
intervals are verified. These instrumented observations do not replace the
primary results above.

[Verification](verification.json) checks all **126 terminal owned-process
receipts**, immutable execution scripts and source pins, 64 full and nine
prefix primary samples, expected outputs and updates, exact changed-function
boundaries, full-text profile identity, counter observations, unchanged finite
limits, inherited locking, reaping and process-group closure. The two retained
qualification failures have their expected statuses. No signal or cleanup
error occurs.

The [retained object audit](../preparation-next-round-v1/byte-table-baseline-inspection.json)
confirms sixteen narrowing instructions and three stack-vector reloads per
active row. Preparing a byte table once is the next contained implementation;
its actual object must demonstrate removal of that repeated work. Selective
private-home loads, compact scanner execution, short immutable comparisons,
table-derived mapping and shared improvements to both long counting loops
remain independent candidates.
