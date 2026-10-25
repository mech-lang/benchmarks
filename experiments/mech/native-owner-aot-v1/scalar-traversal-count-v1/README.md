# Exact scalar traversal accounting

This independent trial is correct but **unpromoted**. The two primary sessions show paired changes of **+2.18%** and **+1.82%** versus the qualified fragment-fact/worker-credit parent. The first 95% interval excludes zero; the second includes it. Neither session establishes an improvement. The qualified parent remains `bdb3c511cd552ffc143460d6e1ae7edd04885a7f`.

## Complete-process timings

All subjects execute sequentially under the existing shared lock, with complete secured Mech startup through exit, the unchanged full input and seven internal workers. Each session contains all six balanced subject orders, six observations per subject and no excluded full-input warmups or outliers.

| Session | Counter candidate | Qualified parent | Exact Rust #7 | Paired candidate change; 95% interval |
| --- | ---: | ---: | ---: | ---: |
| [1](../full-scalar-traversal-count-v1/results.json) | 0.618798 s / 1.113× Rust | 0.605073 s / 1.088× Rust | 0.555989 s / 1.000× | +2.18%; [+1.07%, +4.27%] |
| [2](../full-scalar-traversal-count-v2/results.json) | 0.616968 s / 1.106× Rust | 0.605255 s / 1.085× Rust | 0.557760 s / 1.000× | +1.82%; [−1.04%, +5.94%] |

The separate one-million-base [prefix cohort](../scalar-traversal-count-timing-v1/results.json), with one excluded warmup and three measured processes per subject, gives 0.126670 s / 6.057× Rust for the candidate, 0.088852 s / 4.248× for the parent and 0.020914 s / 1.000× for Rust. Prefix measurements are not combined with full-input results.

## Change and qualification

Production source: [`f1b9e17f15`](https://github.com/mech-lang/mech/commit/f1b9e17f15f6b0b17ccc7845389c80f7902158c9), branch `codex/native-scalar-traversal-count`. The production implementation is unchanged after `d7eac00fce`; two subsequent commits correct bounds-test fixtures. Typed IR85 separates the private encoding; ABI29 and work policy68 remain.

The existing readiness word encodes zero for an inactive loan or one plus its remaining traversal count. The original compute and comparison homes retain their starting balances. The original header decrements the count once for each admitted traversal, including terminal or failing traversals. Before pause, exit, error or fallback, emitted code reconstructs both original remaining balances and passes them through the existing runtime reconciliation. A zero comparison price contributes no comparison limit. Compute price above one proves the positive encoding cannot overflow for any u64 allowance; unsupported cases keep the old balance path.

All three existing homes, frame geometry, original prices, checks and finite limits remain. The source, bytecode and resource image are unchanged. Every full Mech process verifies the complete output, seven complete maps, **874,999,961 original physical updates** and **854,497 original credited batches**.

The three focused generated old/new differential tests, **396 native tests** and one catalog test pass, with three existing manual tests ignored. Coverage includes original and decoded artifacts, repeated prefixes, Unicode/CRLF, exact and one-short independent allowances, maximum finite u64 allowances, terminal traversals, arithmetic and bounds failures, original work/error/output traces and complete memory retirement. Two earlier bounds fixtures failed the assertion that the existing optimization was actually selected; their immutable failed receipts remain and are not qualifying runs. The final fixture exercises the established scanner with an oversized bound; the eligibility proof was not weakened.

[Exact object inspection](code-inspection.json) verifies that the scalar entry changes from **43,376 to 44,312 bytes**, while **all eight nonentry functions are byte-identical**, including the mapper and both long counting-loop families. Original source plans, visits, aggregates, borrowed layouts and loan homes/prices are identical. Raw object disassembly is retained. This identifies what changed without assuming that a smaller header produces a faster complete scanner.

## Separate diagnostics

The [fresh profile](analysis.json) matches the timed candidate's entire machine-text section. Three captures per subject retain waits and partial unwinds. Candidate worker observations are 88.70% in generated counting loops, 4.52% in storage helpers, 3.07% in active work accounting and 0.73% in accounting waits. These are sampling observations, not elapsed-time shares.

[Nine independent counter processes](counters/results.json) give:

| Median diagnostic | Counter candidate | Qualified parent | Rust |
| --- | ---: | ---: | ---: |
| Instructions | 24.531 billion | 24.516 billion | 33.144 billion |
| Cycles | 6.032 billion | 5.932 billion | 8.020 billion |
| User CPU | 1.70 s | 1.68 s | 2.37 s |
| System CPU | 0.04 s | 0.03 s | 0.03 s |

The intended accounting simplification therefore did not produce a useful measured whole-process instruction or cycle reduction. Counter diagnostics are excluded from the primary timings. Fresh candidate-specific preparation and task-width instrumentation is recorded separately in [scalar-traversal-preparation-workers-v1](../scalar-traversal-preparation-workers-v1/).

The candidate file is **5,501,200 bytes**, unchanged from the parent. Machine text is **4,327,848 bytes**, 936 bytes larger. Primary peak RSS is 162.99/162.46 MB for the two candidate sessions, 162.16/162.59 MB for the parent and 140.69/140.43 MB for Rust; no memory improvement is established.

[Verification](verification.json) checks **83 terminal owned-process receipts**, immutable scripts and source pins, exact outputs, unchanged workload and finite limits, object identity boundaries, full-text profile equivalence, complete source stability, inherited locking, reaping and process-group closure. The two retained fixture failures have expected status101; every qualifying run succeeds. No signal or cleanup error occurs. No benchmark dataset observation is replaced by this experiment.

The counter remains available as an independent experimental branch. Removing the remaining buffer passes and canonical String round trip is the next larger implementation; this counter is not included in that baseline.
