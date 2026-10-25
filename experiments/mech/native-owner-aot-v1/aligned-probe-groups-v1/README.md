# Aligned private probe groups and candidate addressing

The native Mech candidate is faster in all six matched pairs in each of two
full-input sessions. Median complete-process runtime falls **5.55% initially
and 1.81% in the repeat**, reaching 1.180× and 1.223× the unchanged upstream
Rust executable. The longest observed worker CPU endpoint also falls. Rust
parity remains unachieved; serial input preparation is now the larger measured
remaining difference.

## Source and implementation

Source revision `8dfe57af5b116244ee8d10e1133bec95c02a4425`, branch
`codex/native-aligned-probe-groups`, builds on the shared-String-fact parent
`d23c2950d` (whose production code is `388261c08`). The Mech program and resource
image remain byte-identical to the parent. All window iteration, source
branches, count arithmetic and replacement values remain generated Mech code.
No Rust diagnostic program or whole-workload function is linked into Mech.

The private fixed-width String/U64 table now starts probes at aligned groups
of eight buckets. Runtime insertion, rehashing, frozen reads and generated
probes use the same partition. A bounded cycle visits every bucket; full-key
comparisons remain mandatory. Seven mirrored controls and their admission
remain, although aligned loads never cross a group boundary.

Generated probes calculate the payload-group base before the control result.
The first set comparison bit is `8 * lane`; multiplying it by `stride / 8`
directly obtains its payload-byte displacement for both 16- and 24-byte slots.
No candidate lane can wrap within an aligned group, removing the dependent
lane-conversion/wrap/address sequence. IR80 fences the changed private placement.
ABI28, work-policy67, body-price formulas, per-group charges, quotas, source
failure sites and allocation sizes remain unchanged. Actual probe counts can
vary with placement. This coupled trial does not isolate placement from address
scheduling as separate causal factors.

Two new adversarial checks exercise runtime probing and the actual generated
lookup code: both payload strides, concentrated same-group/fingerprint
collisions, zero/MAX counts, wrapping from the last group to group zero,
absence, full-table bounded failure and first-group admission rejection. Both
peeled and checked generated paths execute. The broader native suite passes
387 cases, with three existing manual diagnostics ignored; the catalog check
also passes. All checks use the same clean source revision.

## Complete-process timings

The standard full input has 254,166,745 bytes and 125 million selected bases.
Every Mech execution performs seven full histograms and 874,999,961 physical
updates, with seven workers and five bounded lookup caches. Startup and
secured shutdown are included. Exact upstream Rust #7 remains byte-identical,
SHA-256 `f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763`.

Each session has six predeclared balanced orders of candidate, parent and Rust.
Session two reverses the order list. There are no excluded full-input warmups
or observations. Every completed stdout and native report passes.

| Session | Parent Mech | Aligned Mech | Exact Rust |
|---|---:|---:|---:|
| 1 | 0.6982 s · 1.249× | **0.6595 s · 1.180×** | 0.5590 s · 1.000× |
| 2 | 0.6836 s · 1.246× | **0.6712 s · 1.223×** | 0.5488 s · 1.000× |

All six candidate/parent pairs favor the candidate in each session. Paired
median changes are −3.73% and −2.19%; paired 95% bootstrap intervals are
[−7.54%, −2.32%] and [−2.94%, −1.54%]. All 36 observations and calculations
remain in [session one](../full-aligned-probe-groups-v1/results.json) and
[session two](../full-aligned-probe-groups-v2/results.json). Sessions are not
pooled or presented with one another's Rust denominator.

The independent prefix cohort uses one excluded warmup and three measured
processes per subject. Medians are candidate 0.0861 s / 4.215× Rust, parent
0.1214 s / 5.941×, and Rust 0.0204 s / 1.000×. It is a single startup-sensitive
cohort and is not evidence that this probe change accelerated serial input.

## Separate counters, worker CPU and memory

Three fresh whole-process counter diagnostics per subject retain exact outputs.
Their elapsed values do not enter the primary medians.

| Counter median | Parent | Candidate | Rust |
|---|---:|---:|---:|
| Retired instructions | 25.717 billion | 25.521 billion | 33.161 billion |
| Cycles | 7.130 billion | 6.998 billion | 7.979 billion |
| User CPU | 2.03 s | 1.99 s | 2.36 s |
| System CPU | 0.04 s | 0.04 s | 0.03 s |
| Involuntary context switches | 6,284 | 6,325 | 640 |

The candidate retires about 196 million fewer instructions. These are aggregate
process totals, not counters assigned to individual functions or workers.

Three further executions per subject use read-only polling of owned,
birth-and-path-verified direct children. Complete outputs pass. Endpoints are
CPU lower bounds; first sightings are coarse and include polling overhead.

| Diagnostic median | Parent | Candidate | Rust |
|---|---:|---:|---:|
| First counting worker observed | 0.2295 s | 0.2341 s | 0.1518 s |
| Main-thread CPU endpoint | 0.2060 s | 0.2076 s | 0.1285 s |
| Largest worker CPU endpoint | 0.4533 s | **0.4220 s** | 0.3916 s |

The candidate's largest worker endpoint is 6.9% below the parent's. Worker
availability and main CPU do not improve; their small parent/candidate
differences are within the coarse observation scale. These diagnostics cannot
be added to reconstruct primary elapsed time. They support targeting serial
input capture, selection/join and mapping before the next dispatch improvement.

Executable file size remains 5,468,112 bytes. Native text changes from
4,302,220 to 4,302,204 bytes, with no material size reduction. Full-input peak
RSS medians are parent/candidate 162.55/160.87 MB in session one and
161.33/161.35 MB in session two; a repeatable memory reduction is unestablished.

## Exact-code profiles and assembly

Three fresh early full-input captures per language retain owned sampled PIDs,
complete outputs, all thread roots and exact-address demangling. The candidate
profile image's entire `__TEXT,__text` section matches the timed executable,
SHA-256 `e1908a5b9f71a85c178e7107fec0536fc8c95be7f1df5b2ab715d0594b5c80ad`.
Raw captures and [analysis](analysis.json) remain separate from timing cohorts.

| Exclusive Mech worker stack locations | All workers | Longest pair |
|---|---:|---:|
| Generated counting loops | 75.9% | 80.1% |
| Active work accounting, including bounded spins | 17.0% | 10.1% |
| Storage helper paths | 2.8% | 6.1% |
| Generated helper bridge | 1.9% | 1.7% |
| Blocked accounting waits | 1.1% | 1.1% |
| Other waits | 0.4% | 0.3% |
| Other active locations | 1.0% | 0.6% |

These partition sampled observations, not elapsed-time or CPU fractions.
The longest pair is selected by the two largest worker roots per capture and
both execute the ordinary hashed funded loop. Rust's corresponding pool roots
contain 73.9% active counting, 25.7% waiting and 0.4% other active locations.
Its pool stays alive after tasks finish; those denominators are not directly
comparable utilization measures. Partial startup unwinds and profiling overhead
remain retained.

[Exact disassembly](code-audit/results.json) retains both complete raw images
and four extracted funded functions per image. A representative first-match
chain through the first scalar key load shrinks from eight instructions:

```text
rbit; clz; lsr #3; add index; and mask; lsl #4; add payload; ldr key
```

to five:

```text
rbit; clz; lsl #1; add ready-group-base; ldr key
```

The ordinary funded functions contain 5,632 instructions in the parent and
5,600 in the candidate. Cache-funded instruction counts remain 1,184 and 1,120.
Static counts and representative address windows do not establish dynamic
frequency or attribute the entire timing gain to those three instructions.

## Reproduction and retained setup failure

[plan.json](plan.json) and the copied IR80-aware measurement driver precede
native execution. [verify.py](verify.py) qualifies 90 terminal processes,
all reaped with closed groups, no cleanup errors or cleanup signals. It checks
all source pins, primary outputs and update counts, current image versions,
complete-code identity, three profile subjects per language, the counter and
worker records, and extracted assembly hashes.

The first thread-only driver retained a stale prepared-refill parent path.
Its binary hash guard stopped before launching a subject. The corrected
[driver](threads-v2.py) uses the actual shared-String-fact parent and stores
nine observations in `thread-observations-v2`; the failed wrapper remains
retained. No successful profiles, counters or timings were repeated to repair
that check. The earlier [two-backend policy pilot](../aligned-probe-pilot-v1/README.md)
and all its failed setup attempts remain distinct from this native trial.

All native activity is serial under the existing shared lock. No power,
priority, affinity, worker count, chunk size, work allowance or protected
upstream source changes. Canonical benchmark and website data are unchanged.
The parent and candidate branches remain available for further interaction
experiments. The next profile-backed target is the serial input pipeline;
its approximate 0.08-second main-thread CPU difference exceeds the remaining
roughly 0.03-second largest-worker endpoint difference in these diagnostics.
