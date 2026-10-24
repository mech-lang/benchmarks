# Cold source-state reconstruction: profile and timing

Two independent trials lower cold source state through affine recipes (IR75,
[`69fc5812f`](https://github.com/mech-lang/mech/commit/69fc5812f0ec5f96e3526cdeb51be828370a282c))
and then reload the immutable owned source/width words at exits (IR76,
[`6d2e2673e`](https://github.com/mech-lang/mech/commit/6d2e2673ea1d49d8ec16663dda012547f3ad1f4a)).
Neither establishes an elapsed-time improvement. The source and bytecode stay
identical to the preceding cursor experiment. ABI27, work65, the 19-word frame,
finite allowances and all original source continuations remain.

## Complete-process results

Each trial retains six balanced serial cohorts on 125 million selected bases,
including secured startup/shutdown, all processes and all outliers. No full-input
warmups are excluded. Denominators belong to their own cohort.

| Trial | Rust seconds | Parent seconds / × Rust | Candidate seconds / × Rust |
| --- | ---: | ---: | ---: |
| IR75 recipes against IR74 | 0.5592 | 0.7894 / 1.411× | 0.7891 / 1.411× |
| IR76 frame reloads against IR75 | 0.5577 | 0.7848 / 1.407× | 0.7847 / 1.407× |

Each candidate is faster in only three of six pairs. Median changes are 0.039%
and 0.015%, respectively. These are negligible differences with overlapping
ranges. The separate prefix cohorts retain one excluded warmup and three
observations per executable; they are not pooled with full input.

All full Mech processes verify complete output, seven complete packed SSA maps,
seven peak workers and **874,999,961 physical updates** under the unchanged
secured policy. Canonical benchmark data is unchanged.

## Where the current executable runs

Three completed [IR76 profiles](../cold-frame-remaining-profile-v2/results.json)
match the entire machine-code section of the timed executable. Three fresh
profiles of the exact protected Rust binary accompany this comparison.

| Mech worker location | Observations | Share |
| --- | ---: | ---: |
| Generated counting loops | 5,748 | 84.75% |
| Storage helpers | 412 | 6.07% |
| Active work accounting | 314 | 4.63% |
| Accounting waits | 100 | 1.47% |
| Helper bridge | 103 | 1.52% |
| Other activity | 105 | 1.55% |

These are sampled thread observations, including waits, not elapsed-time shares,
CPU utilization or individual instruction costs. Rust's fresh observations are
65.73% active counting tasks and 34.24% waits; its persistent pool keeps finished
workers available, whereas Mech's scoped workers exit. The percentages therefore
do not establish that Rust spends more elapsed time waiting. Mech's main thread
is predominantly joining workers during the counting phase.

Separate whole-process counter runs give IR76 **39.750 billion instructions /
10.585 billion cycles**, IR75 control **39.739 / 10.499**, and protected Rust
**33.153 / 7.960**. Mech retires about 20% more instructions and 33% more cycles
than Rust in this diagnostic cohort. Counter processes are not extra primary
timing observations.

The [38 retained successful paths](../cold-frame-codegen-audit-v1/steady-paths-v2.json)
still have **36–39 instructions, five branches and no stack accesses**. Source
index reconstruction remains on the hot path despite the cold recipes and
owned-frame reloads. The examined Rust path has 34 instructions and four
branches; these static paths are not dynamic frequencies. Further small changes
to exit reconstruction have no demonstrated benefit.

Larger hypotheses include a bounded direct-index lookup cache for genuinely
small finite key domains, eliminating redundant entry-address calculations and
hot success-path jumps, and shortening rolling-key dependencies. A cache would
replace repeated probes, while retaining the complete underlying map, every
source update and all finite accounting. It must be charged, bounded, refreshed
on growth and declined when its admission is unavailable. None of these
unimplemented hypotheses has an assigned speedup.

## Validation

At the exact IR76 revision, **369 native checks and one catalog integration
check pass**, with three existing manual exclusions. Both revisions separately
pass four new cold-recipe checks and six existing steady-loop checks, including
changed inputs, complete maps, arbitrary seeds and widths, original arithmetic
failures, finite work and refill frontiers. The IR75 trial has focused validation;
the full suite was run on IR76.

[Verification](results.json), produced by
[`verify_cold_reconstruction.py`](../verify_cold_reconstruction.py), recomputes
36 primary full-input observations across two independent trials, checks six
exact-code Mech captures plus three fresh Rust captures, rejects 21 malformed
metadata fixtures, binds tests to immutable revisions and checks 117 terminal
owned-process receipts under the shared mutex. No compiler source changed during
builds, tests, profiles or timings. These experiments establish correctness and
an unsuccessful optimization attempt; Rust parity remains incomplete.
