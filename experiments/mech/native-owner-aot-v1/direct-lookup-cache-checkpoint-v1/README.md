# Bounded lookup cache: results and remaining costs

IR77 / ABI28 / work66 adds an optional direct-index lookup cache over a complete,
source-derived finite key domain. The timed production revision is
[`c7cda2018`](https://github.com/mech-lang/mech/commit/c7cda2018917a75bd014c07ee2777305d88832e7).
The Mech source, bytecode, complete underlying hash tables and every original
map update remain. The cache stores pointers to real table entries; it does not
replace histograms with query-specific counters. Admission covers allocation,
initialization and maintenance, and growth refreshes every cached address.
Unavailable admission retains ordinary hashing. No workload name or expected
answer selects this optimization.

## Complete-process timing

Six balanced serial cohorts retain every observation and outlier on 125 million
selected bases, including secured startup/shutdown, with no excluded full-input
warmup. Multiples use this cohort's own protected Rust executable.

| Executable | Median seconds | × Rust time | Range, seconds |
| --- | ---: | ---: | ---: |
| Exact upstream Rust #7 | 0.5580 | 1.000× | 0.5536–0.5654 |
| IR76 parent | 0.7854 | 1.407× | 0.7757–0.8136 |
| IR77 cache candidate | 0.7740 | 1.387× | 0.7498–0.7815 |

The candidate median is **1.45% lower**, with six faster pairs and slightly
overlapping ranges. This is a small elapsed-time gain. Each full Mech process
verifies complete output, **874,999,961 physical updates**, seven complete packed
SSA maps and seven peak workers. The candidate reports five actually admitted
caches. Finite allowances, refill bounds and security settings are unchanged.
Canonical benchmark data has not been replaced by experimental results.

A separate one-million-base prefix cohort retains one excluded warmup and three
observations per subject: Rust **0.0126 s / 1.00×**, parent **0.0994 s / 7.91×**,
and candidate **0.1135 s / 9.03×**. The candidate regresses approximately 14.2%
on that batch. Prefix data is not discarded or pooled with full input.

## Reduced instructions, remaining elapsed-time gap

Nine separate counter executions verify complete output and updates. Their
medians are diagnostic counters rather than additional primary timings.

| Executable | Billion instructions | Billion cycles |
| --- | ---: | ---: |
| Exact upstream Rust #7 | 33.13 | 7.90 |
| IR76 parent | 39.71 | 10.52 |
| IR77 cache candidate | 30.06 | 7.75 |

The candidate retires **24.3% fewer instructions and 26.3% fewer cycles than its
parent**, and approximately **9.3% fewer instructions than Rust**. Aggregate
instructions and cycles therefore no longer explain the elapsed gap by
count alone. Work distribution, preparation and the longest worker remain
important hypotheses; the counters do not establish their separate costs.

Three completed profiles match the entire machine-code section of the timed
executable. The current partition includes 5,006 worker observations:

| Worker location | Observations | Share |
| --- | ---: | ---: |
| Generated counting loops | 3,561 | 71.13% |
| Active work accounting | 520 | 10.39% |
| Accounting waits | 374 | 7.47% |
| Storage helpers | 328 | 6.55% |
| Helper bridge | 124 | 2.48% |
| Other activity/root | 99 | 1.98% |

Active accounting and accounting waits rise from approximately 6.10% in the
parent profiles to **17.86%** here. Refill routes contribute 367 active and 268
waiting observations. These are sampled thread locations, including waits,
not wall-time shares or precise causal estimates. Faster small-domain loops
may expose contention at the shared refill ledger; that remains an inference.

The guarded static auditor retains 38 source-function/width paths and all
branch assumptions. With an admitted cache, 14 small-domain paths have 19–24
instructions; the 24 remaining paths have 37–38. A declined cache retains the
ordinary hash path. The combined function introduces a stack reload of an
immutable hash constant on large-domain paths, whereas the parent paths had
no stack accesses. Some cached paths also repeat rolling-key reconstruction at
a join. Static path counts neither give dynamic frequencies nor establish
individual instruction costs. Separating cached and ordinary funded functions
is an unimplemented hypothesis to reduce that register pressure and join work.
Shortening the existing refill critical section without increasing credit is
another independent hypothesis.

Six separate read-only thread observations use the exact timed binaries and
verify complete output. In the two candidate captures, first worker
observations occur around 0.232–0.244 seconds; in Rust they occur around
0.143–0.154 seconds. The two most CPU-active Mech threads accumulate roughly
0.480–0.499 observed CPU seconds, versus 0.384–0.401 for Rust. These endpoints
are lower bounds under polling, do not identify source widths and are not
primary timings. They motivate investigating both preparation and long-running
worker work rather than equating total retired instructions with elapsed time.
Five failed monitor setup attempts remain: the first owned child was killed
and reaped after a monitor assertion; subsequent children completed correctly
but the monitor could not verify their path. The corrected trace uses the
supported path buffer and kernel birth identities. None is a primary sample.

## Validation and retained failures

Five new focused cache checks and six unchanged steady-loop checks pass at the
exact timed production revision. They exercise complete domains, generated
cache and ordinary-probe paths, zero/maximum stored values, absence, growth,
admission refusal, complete frozen maps, changed inputs and finite failure
frontiers. An initial compile attempt failed a borrow check and remains.

The first full suite has 373 passing checks and one stale exact-memory fixture:
its cap omitted the new owned cache bytes. Test-only revision
[`49bdf267d`](https://github.com/mech-lang/mech/commit/49bdf267dfdab441c69007b4f04b4088be0a0337)
adds the actual cache geometry to that fixture while preserving one-byte-short
refusal. At this revision **374 native checks plus one catalog check pass**,
with three existing manual exclusions. Its only change from the timed revision
is `program_packed_narrow_tests.rs`; production source is identical. Both the
initial fixture failure and the corrected complete run remain.

[Verification](results.json) recomputes 18 primary full-process observations,
checks three exact-code captures, eleven malformed-metadata rejections, all
counter/trace outputs and 69 terminal owned-process receipts. Builds, tests,
profiles and timings are serial under the original shared lock. No source edit
occurred during native work. Rust elapsed-time parity remains incomplete.
