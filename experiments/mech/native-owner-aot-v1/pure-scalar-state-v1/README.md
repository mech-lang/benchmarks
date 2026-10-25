# Pure-scalar graph and SSA state

The scalar-loop compiler at `93015bc6298b77fd10402e88baea5e3bfd89b28d`
improves complete-process runtime by approximately **5.6%** over the qualified
compact-mapper parent in both independent sessions. All twenty matched parent
comparisons are faster. Mech and Rust medians are close in both sessions, but
both paired Rust intervals include zero: a repeatable advantage or a defined
statistical equivalence claim is not established.

## Complete-process results

| Subject | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Scalar SSA, `93015bc629` | **0.557454** | **1.000×** | **0.556037** | **0.999×** |
| Compact parent, `d1ae94f684` | 0.590808 | 1.060× | 0.593407 | 1.066× |
| Byte-table anchor, `8946ccbae9` | 0.605935 | 1.087× | 0.604232 | 1.086× |
| Ordinary control, `bdb3c511c` | 0.614215 | 1.102× | 0.617455 | 1.110× |
| Exact upstream Rust | 0.557563 | 1.000× | 0.556436 | 1.000× |

| Candidate versus | Session 1 paired change, 95% interval | Faster pairs | Session 2 paired change, 95% interval | Faster pairs |
|---|---:|---:|---:|---:|
| Compact parent | −5.65% [−6.12%, −4.84%] | 10/10 | −5.62% [−6.83%, −4.37%] | 10/10 |
| Byte-table anchor | −7.41% [−9.40%, −5.57%] | 10/10 | −7.80% [−8.43%, −7.41%] | 10/10 |
| Ordinary control | −8.89% [−10.64%, −8.10%] | 10/10 | −9.50% [−10.56%, −8.80%] | 10/10 |
| Rust | +0.19% [−1.85%, +2.84%] | 5/10 | −0.20% [−1.50%, +1.83%] | 6/10 |

Each session retains ten complete processes per subject in balanced Williams
orders; the second reverses the order list. All 100 observations remain, with
no excluded full-input warmups or outliers. Processes run serially under the
original shared mutex, with complete secured startup-to-exit boundaries.
The original program, bytecode, resource image, input, finite prices, seven
complete maps and all 874,999,961 updates remain unchanged. Every Mech full
process also verifies 854,497 credited original batches and seven tasks.

Raw results: [session 1](../full-pure-scalar-state-v1/results.json),
[session 2](../full-pure-scalar-state-v2/results.json), [plan](plan.json).
Separate prefix qualification retains three measured observations and one
excluded warmup per subject; these are not full-input samples.

## Compiler change

The existing bounded tag product graph now supports admitted callback-free
scalar Tails as well as packed map Tails. Scalar loops reuse the same SSA word
homes, aggregate operations and source terminator algebra. Ordinary and SSA
borrowed-view execution share one native action emitter, and both use the same
prefix retention predicate. No second source scanner or library implementation
of the state machine is introduced.

For the unchanged benchmark, actual emission selects **107 SSA word homes**,
**163 product nodes over 123 source sites**, three actual tag variants,
**23 folded branch versions** and six known latch versions. The retained words
include real carrier fields, scalar indices/results, borrowed pointer/length
lanes and finite funding. A ready view/loan selects the body once, replacing
repeated per-site readiness dispatch. The original memory-backed path remains.

At an exhausted prefix window or insufficient loan, SSA homes synchronize
before control returns to the original header. That header performs the
original pause or fallback without repeating a debit. Errors synchronize before
owner-retiring callbacks; their later error edge cannot re-spill stale ready
words. Successful exits synchronize before original publication and loan
retirement. Pending source counts remain unavailable before EOF. Exact source
origins, bounds, arithmetic checks and opaque-helper barriers remain.

All emitted templates fit the original finite envelopes: maximum source-site
template 189 instructions against the 512-unit lane; fixed setup/boundaries
437 against 1,024. IR 92 identifies the new execution; ABI 33 and work policy
69 remain. No source memory flags or source inputs are strengthened or changed.

## Actual code, counters and profiles

The [assembly inspection](code-inspection.json) finds all **thirteen nonentry
function bodies byte-identical** to the compact parent, including all mapping,
counting and bridge functions. Plans, visits, aggregate/view layouts and closed
body prices are identical too. The root grows from 43,596 to 57,488 bytes:
the native graph coexists with fallback and cold synchronization. The allocator
also introduces stack spills. SSA homes do not imply that every word occupies
a physical register; larger static code is not evidence of a faster hot path.

Separate full-input hardware-counter medians corroborate less complete-process
work in this cohort:

| Subject | Retired instructions | Cycles | User CPU seconds | System CPU seconds |
|---|---:|---:|---:|---:|
| Scalar SSA | **23.107 B** | **5.619 B** | **1.590** | 0.030 |
| Compact parent | 24.264 B | 5.902 B | 1.665 | 0.030 |
| Byte-table anchor | 24.418 B | 5.934 B | 1.680 | 0.030 |
| Ordinary control | 24.519 B | 5.905 B | 1.665 | 0.030 |
| Rust | 33.139 B | 7.888 B | 2.330 | 0.030 |

The candidate retires about **1.157 billion fewer instructions** than its parent,
with approximately 4.8% fewer cycles and 4.5% less user CPU. These twenty
diagnostic processes remain separate from primary elapsed samples; their
rounded `time -l` elapsed values are not substituted for the primary medians.

Fresh profiles retain three completed prearmed owned-PID captures per language.
The entire profiled Mech text section matches the timed executable, not just
its guest object. Among 3,786 Mech worker observations, 87.37% are generated
counting, 5.10% storage helpers, 3.49% active accounting and 1.80% the generated
bridge. Main observations include 27 in generated entry, 25 in the actual
projected mapper, 11 in offset allocation and six in UTF-8 validation. Waits
and partial loader unwinds remain. These are observations, not CPU or elapsed
phase shares, and different Rust thread-pool persistence prevents interpreting
worker percentages as comparable time fractions. See [profile analysis](analysis.json)
and [counter receipts](counters/results.json).

The executable is **5,517,792 bytes**, 16,512 bytes larger than its compact
parent. Whole text is 4,344,912 bytes, 13,892 bytes larger. Primary peak RSS
medians are 162.71/163.00 MB, versus parent 162.70/162.62 MB and Rust
141.07/140.40 MB. No memory saving is established.

Matching actual-candidate phase/worker probes are the next measurement; the
parent's 73 ms scanner duration must not be assigned to this new code.

## Qualification and provenance

Final-source checks pass **412 native**, **30 line-storage**, **36 finite-credit**
and **one catalog** tests. Three existing manual native tests remain ignored.
The two new differential tests are included in that native total. They compare
the SSA path with a compilation that disables only scalar loops, using original
and decoded artifacts, renamed state machines, empty/missing/unfinished input,
Unicode, CRLF, incremental/EOF delivery, exact finite-work outcomes and arithmetic
failures. Window pauses also verify that every raw owner loan is cleared.

Two initial clean compile failures remain: the added evidence field exceeded
the existing large JSON macro's recursion limit, then shared graph types needed
visibility in the sibling scalar emitter. The metadata field was moved outside
the macro and the internal graph visibility corrected. Neither failed attempt
ran a benchmark. All final scopes use source `93015bc629`. The first verifier's
retained report used the older study label; `verify-v2.py` changes only that
label and reuses every native receipt.

[Verification](verification.json) checks **160 terminal owned process receipts**,
all pins, outputs, source stability, work, exact profile text and shutdown.
Every process is reaped and every owned group closed, without cleanup signals.
The [Frame audit](frame-audit.json) retains the unchanged private Frame and
emitter hashes plus the shared-word extraction diff. Machine-code comparison
checks the resulting unaffected functions directly.

Both long ordinary hash loops remain optimization targets. Final validation
and chunk administration retain lower priority pending the new phase breakdown.
