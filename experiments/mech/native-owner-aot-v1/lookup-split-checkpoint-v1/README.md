# Separate cached and ordinary counting functions

Compiler [`65dfd8bef`](https://github.com/mech-lang/mech/commit/65dfd8bef29a8aef4cddd6926ff6461a959c24be),
IR78 / ABI28 / work66, emits separate helper-free functions for admitted lookup
caches and ordinary hash probes. The caller tests the actual owned cache pointer
and supported width once per funded call. Both versions emit the original
source graph and return precise continuations for missing keys, growth, refills
and failures. The source, bytecode, complete maps, finite allowances and every
original update remain.

## Complete-process results

Six balanced serial cohorts use 125 million selected bases, including secured
startup/shutdown, with no excluded full-input warmup or outlier. The denominator
is the unchanged upstream Rust executable in this cohort.

| Executable | Median seconds | × Rust time | Sample SD, seconds |
| --- | ---: | ---: | ---: |
| Exact upstream Rust #7 | 0.5517 | 1.000× | 0.0093 |
| IR77 cache parent | 0.7614 | 1.380× | 0.0085 |
| IR78 separate functions | 0.7490 | 1.358× | 0.0067 |

The candidate median is **1.64% lower**, with six faster pairs. Candidate and
parent ranges overlap: 0.7414–0.7596 and 0.7510–0.7728 seconds. Every full Mech
process verifies complete output, **874,999,961 physical updates**, seven
complete packed SSA maps, seven peak workers and five admitted lookup caches.
This is a small gain; Rust elapsed-time parity remains incomplete.

The separate one-million-base prefix batch retains one excluded warmup and
three observations per subject: Rust **0.0209 s / 1.00×**, parent **0.1147 s /
5.49×**, and candidate **0.1026 s / 4.91×**. Its median improves 10.52%; it is not
pooled with the full input or with previous prefix batches.

## Machine code and fresh profile

Three captures use a profiling executable whose entire machine-code section
matches the timed executable. Complete outputs and native
update counts are verified. Static examination retains fifty explicitly
assumed successful cycles across the four emitted functions:

| Function kind | Audited cycles | Instructions | Branches | Stack accesses |
| --- | ---: | ---: | ---: | ---: |
| Ordinary hash | 38 | 36–39 | 5 | 0 |
| Direct cache | 12 | 16–17 | 3 | 0 |

The hash-constant spill introduced by the combined function is gone. Cached
cycles also lose the optional-cache branch and repeated rolling-key work at
the hash/cache join. Every direct indexed access is bound to the actual ABI28
cache-pointer field load. Branch assumptions and exact instructions remain in
[the audit](../lookup-split-codegen-audit-v1/steady-paths-split.json). Counts
include generic/unused width arms; they are not dynamic frequencies or costs
assigned to individual instructions.

Separate complete-process counter medians are:

| Executable | Billion instructions | Billion cycles |
| --- | ---: | ---: |
| Exact upstream Rust #7 | 33.16 | 7.94 |
| IR77 parent | 30.08 | 7.75 |
| IR78 candidate | 26.93 | 7.50 |

Instructions fall **10.4%** and cycles **3.2%** against the parent. The candidate
retires approximately **18.8% fewer instructions than Rust** while remaining
35.8% slower in elapsed time. These counters cover all threads; they do not
explain the critical path by themselves and are not extra primary timings.

Three fresh profiles partition 5,131 worker observations:

| Worker location | Observations | Share |
| --- | ---: | ---: |
| Generated loops | 3,591 | 69.99% |
| Active work accounting | 559 | 10.89% |
| Work-accounting waits | 432 | 8.42% |
| Storage helpers | 339 | 6.61% |
| Helper bridge | 105 | 2.05% |
| Other activity/waits | 105 | 2.05% |

Accounting and its waits total **19.31%**, compared with 17.86% in the parent's
profiles using the same taxonomy. Refill routes contribute 385 active and 287
waiting observations. Capture windows differ; these are sampled thread
locations including waits, not elapsed-time shares or CPU utilization.

The next independent hypothesis is to shorten the existing refill transaction,
keeping its actual finite debits and 1,024-visit maximum. Earlier read-only
thread observations and an exclusive main-thread partition of the **IR77
parent** also identify preparation and the longest workers as useful targets.
The parent's main-thread leaves include selected-join copying, line-chunk
handling and generated character mapping. They do not establish precise
preparation costs and are not fresh IR78 timing observations.

## Admission, qualification and validation

The compiler includes both functions in actual code admission and uses the
larger callee stack for mutually exclusive calls. This artifact admits
**112,328 code bytes and 1,216 stack bytes**. Existing fixed/source instruction
envelopes, finite prices, lock-release bounds and runtime cache limits remain.
No additional native helper call appears in either funded function.

The original measurement gate stopped after a successful build, before timing:
one cached function had declined optional cold-state recipes at the existing
metadata bound and emitted ordinary live-word exit snapshots. Both primary
hash functions retain their cold recipes; one cache function has three recipes
and the other uses the checked ordinary snapshot form. Qualification now
records and validates those actual forms. It continues to require all original
source-node, live-continuation, width, fuel, code and stack bindings. The first
failed qualification, its exact driver and completed build remain. The retry
reuses only that byte-identical build, with **zero timing observations reused**.

At the exact timed compiler revision, **377 native checks plus one catalog
integration check pass**, with three existing manual exclusions. Three focused
checks compare split and dynamic lookup forms on changed inputs, complete maps,
growth/refill boundaries, original and decoded source, arithmetic failures,
nonempty seeds and exact work/error frontiers. Metadata tests bind cache
selection to actual owned fields, supported widths and both function limits.
The complete suite also executes compact domains and all seven source maps.

[Checkpoint verification](results.json) recomputes all 18 primary full-process
observations, checks three exact-code captures, rejects eighteen malformed
metadata variants and checks 54 terminal owned-process receipts under the
original shared mutex. No compiler source changed during native work.
Canonical benchmark data is unchanged. The complete raw trial is retained;
Rust parity is not established.
