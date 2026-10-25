# Shared immutable String representation facts

Caching the ASCII/no-CRLF property on the immutable String owner removes
repeated worker scans and reduces diagnostic instruction counts, but **does
not establish a full-input runtime improvement**. Both timing sessions remain
about 1.25× the exact upstream Rust executable.

## Implementation and qualification

Production revision `388261c0873210eb86ed19ff0f6c06f77e584ab6` adds an inline
once-cell to canonical immutable data. String clones, rebinding, cross-budget
imports and parallel captures share the same derived fact. Non-String values
do not initialize it. The cache carries no permissions or admission authority.
Generic maintained String length and closed-map preparation use the fact after
their original schema/source checks and representation-scan charges. Unicode
and CRLF retain ordinary grapheme semantics. Consuming mutable ownership drops
the old cache; refreezing changed bytes creates a fresh fact.

The actual frozen-owner allocation grows by 16 bytes on this target. Existing
`size_of`-derived allocation bounds include that increase: every one of the
38 constant-owner bounds grows by 16 bytes and the scalar-owner inventory grows
by 64 bytes. Work-policy 67 fences the changed admission layout. The Mech
program, bytecode, resource image and **generated guest instruction bytes are
unchanged**. Object identity and descriptor size bounds change as intended;
[image qualification](image-qualification.json) checks the exact differences.

Core qualification passes 44 ownership/representation checks, including five
new lazy-initialization, ASCII boundary, cross-budget, mutable-refreezing and
concurrent-reader tests. Six existing native fact-cache checks pass. The broad
native run passes 383 cases and stops two cases at explicit old-policy-66
expectations; three existing manual diagnostics remain ignored. The test-only
revision `d23c2950d` changes those two expectations to 67. Both complete test
bodies then pass, and the catalog check passes. No production code changes
between measurement and this test correction.

## Complete-process timings

The parent is `bf10d4a51`, `counting-prepared-refill`. Candidate is
`counting-shared-string-facts`. Rust is the untouched upstream #7 binary,
SHA-256 `f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763`.
The standard input contains 254,166,745 bytes and 125 million selected bases.
Every Mech execution performs seven full histograms, 874,999,961 updates,
seven workers and five bounded lookup caches. Startup and secured shutdown are
included. All complete outputs match Rust's reference exactly.

Each session has six fixed balanced orders of parent, candidate and Rust,
with six measurements per subject. Session two reverses the order list.
There are no excluded full-input warmups or outliers. Sessions remain separate.

| Session | Parent | Candidate | Rust |
|---|---:|---:|---:|
| 1 | 0.6945 s · 1.250× | 0.6908 s · 1.243× | 0.5557 s · 1.000× |
| 2 | 0.6959 s · 1.253× | 0.6972 s · 1.255× | 0.5554 s · 1.000× |

Candidate marginal changes are −0.54% and +0.19%. Paired 95% bootstrap intervals
are [−2.73%, +1.65%] and [−0.99%, +1.87%]. Both include zero. All 36 observations,
orders, pins and intervals are retained in
[session one](../full-shared-string-facts-v1/results.json) and
[session two](../full-shared-string-facts-v2/results.json).

The separate one-million-base prefix cohort has one excluded warmup and three
measured processes per subject. Medians are candidate 0.1177 s / 5.952× Rust,
parent 0.0965 s / 4.879× and Rust 0.0198 s / 1.000×. This single noisy startup
cohort is not pooled with the full-input results or assigned a mechanism.

## Separate hardware counters and profiles

Three diagnostic counter runs per subject use the exact timed files. No
diagnostic duration enters primary medians.

| Counter median | Parent | Candidate | Rust |
|---|---:|---:|---:|
| Retired instructions | 26.117 billion | 25.714 billion | 33.183 billion |
| Cycles | 7.357 billion | 7.021 billion | 7.928 billion |
| User CPU | 2.11 s | 2.00 s | 2.34 s |
| System CPU | 0.04 s | 0.04 s | 0.03 s |
| Involuntary context switches | 5,496 | 6,055 | 1,051 |

The candidate retires about 402 million fewer instructions (1.54%) than its
parent. These aggregate counters do not establish shorter critical workers
or a repeatable elapsed-time gain.

Three fresh early-start full captures per language retain exact-PID ownership,
complete outputs and the whole-code match between the Mech profile image and
timed executable. [Analysis](analysis.json) partitions every included thread
root, with raw symbols and exact-address demangling. Waits, partial unwinds
and profiler overhead remain included. No successful process is recaptured
to repair analysis.

| Exclusive candidate worker observations | All workers | Longest pair |
|---|---:|---:|
| Generated counting loops | 75.4% | 76.4% |
| Active finite-work accounting, including bounded spins | 16.2% | 11.3% |
| Storage helper paths | 4.0% | 8.0% |
| Generated helper bridge | 2.1% | 1.9% |
| Blocked accounting waits | 1.1% | 1.7% |
| Other waits | 0.6% | 0.3% |
| Other active locations | 0.6% | 0.4% |

These are stack-location shares, not elapsed-time or CPU fractions. The longest
pair is selected by the two largest observed worker roots in each capture;
both run the ordinary hashed funded loop. The earlier parent captures had
152 exclusive worker observations in the ASCII scanner. This candidate has
none at that old leaf and five observations in the shared once-cell initializer;
the raw captures retain initialization waits too. Different capture denominators
prohibit interpreting those counts as exact saved CPU seconds.

Rust's fresh task-worker roots are 77.0% active counting and 23.0% pool waits.
Its pool threads stay alive after completing tasks; Mech workers retire.
Those shares do not establish comparable utilization or a waiting penalty.

## Worker availability and critical CPU

Three additional owned-process executions per subject poll thread CPU and
lifetimes. All outputs pass. These are coarse observations, separate from the
primary timings; CPU endpoints are lower bounds and first sightings include
polling/supervisor overhead.

| Diagnostic median | Parent | Candidate | Rust |
|---|---:|---:|---:|
| First observed counting worker | 0.2314 s | 0.2281 s | 0.1542 s |
| Observed main-thread CPU endpoint | 0.2093 s | 0.2071 s | 0.1349 s |
| Largest worker CPU endpoint | 0.4679 s | 0.4550 s | 0.3952 s |

The small first-sighting difference is below the approximate polling interval.
The candidate still has about 74 ms later observed worker availability than
Rust and a roughly 60 ms larger longest-worker CPU endpoint. These separate
diagnostic medians must not be added to reconstruct primary elapsed time.

The scan change affects worker preparation; it leaves the main thread's line
capture, record selection/join and character-map pipeline intact. It also
leaves generated hash-table instruction bytes unchanged. Those paths are the
next targets. The shared initializer itself is not a dominant sampled leaf,
so the current profile does not support predicting a large gain merely by
moving its computation again. The candidate is retained as an interaction
factor, not promoted as a measured fastest implementation.

## Reproduction and retained failures

[plan.json](plan.json) precedes native execution. The initial wrapper inherited
work-policy 66 and stopped qualification after a successful build; its stdout,
stderr and completed build remain in `shared-string-facts-timing-v1`. The copied
[measurement driver](measure-stage-driver.py) fences policy 67 and uses that
exact build for the successful prefix cohort in `shared-string-facts-timing-v2`.
No earlier timing observations existed to replace. A subsequent identical-image
assertion also stopped because concrete owner-size bounds had intentionally
grown. The exact image-difference qualification replaces that assertion without
rerunning the prefix. Both controller stops and the two old-version test failures
remain retained.

[verify.py](verify.py) checks 91 terminal process receipts, including the expected
initial failing test process and both repaired cases. Every process is reaped,
its group closed, with no cleanup errors or cleanup signals. It checks source
pins, the two test-only file differences, outputs, update counts, image identity,
timing plans and diagnostics. All native operations run serially under the
existing shared mutex; no power, priority, affinity, chunk size, allowance or
protected upstream source changes. Canonical benchmark and website data remain
unchanged. Rust parity remains unachieved.
