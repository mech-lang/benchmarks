# Input-size scheduling trial

Candidate `b8da46b50fd78e59dc610b4dda0b4b5adc93de81` on
`codex/native-sized-task-scheduling` starts larger independent mapped jobs first.
The parent is compact host metadata revision
`e939c8002793c03cf63a31eeb13dd78fb8855064`. Production implementation is in
`d18a2b3a1072209150e5c747f95b3f548456bbd3`; the two later commits repair test
fixtures without changing production code.

**No repeatable complete-process speedup is established.** Both paired intervals
include zero, and the marginal-median direction reverses in the repeat. The
factor remains on its pushed experimental branch for combination testing. The
accepted PR baseline and all preparation and host-metadata factors remain
available. Canonical website timings are unchanged; Rust parity is incomplete.

## Implementation

An allocation-free bounded sort orders at most 32 jobs by an existing input
element's UTF-8 byte length, with original ordinal as the tie-breaker. Scalar or
unsupported elements have unit weight. Weight discovery borrows an already
admitted element without copying or inspecting its payload. Captures, loans and
other admission occur in source order. Worker handles are restored to source
order before joining, preserving result replay and source error precedence.

The original generated worker bodies, seven workers, capability checks, source
visits and finite work/memory accounting remain. Both bounded sorts fit the
existing scheduler envelope; no limit or price is relaxed. No workload name,
query, alphabet, width, core placement, affinity, QoS or power change is used.

The Mech source, bytecode, native Object, descriptor JSON and compressed image,
resource image and complete Object identity are byte-identical to the parent.
The checked Object hash is
`f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335`.
IR79, ABI28 and work policy66 remain unchanged.

## Complete-process timings

The [plan](plan.json) was committed at
`d4db1786bc451d650087f14300a8b2eb5e48afe8` before execution. Each session runs
all six balanced sequential orders of Rust, parent and candidate. All 36
full-input observations are included, without excluded warmups or outliers.
Input contains 125 million selected bases; startup, secured execution and exit
are included. Sessions remain separate.

| Configuration | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Exact upstream Rust #7 | 0.5581 | 1.000× | 0.5651 | 1.000× |
| Compact-host parent | 0.7145 | 1.280× | 0.6998 | 1.238× |
| Size-first candidate | 0.7032 | 1.260× | 0.7049 | 1.247× |

Marginal-median changes are −1.57% initially and +0.72% in the repeat. Median
paired log-ratio changes are **−2.18% [−4.41%, +0.96%]** and
**−0.56% [−1.76%, +2.48%]**; five of six and four of six matched orders favor
the candidate. Descriptive 95% intervals resample complete matched orders
20,000 times with fixed seeds. Paired estimates differ from ratios of marginal
medians.

The separate one-million-base prefix cohort has one excluded warmup and three
measured complete processes per subject: Rust **0.01936 s / 1.000×**, parent
**0.11710 s / 6.049×**, candidate **0.08786 s / 4.539×**. This small batch is
not a repeated prefix result and is not pooled with either full-input session.

[Session 1](../full-sized-schedule-v1/results.json),
[session 2](../full-sized-schedule-v2/results.json) and
[prefix/build qualification](../sized-schedule-timing-v1/results.json) contain
all observations, deviations, source/binary/input/policy pins and native reports.
Every full Mech process verifies seven complete maps, five admitted caches,
seven peak workers and **874,999,961 physical updates**. Prefix processes verify
**6,999,961 updates** and complete output.

## Memory, size and counters

MB means 1,000,000 bytes. RSS is the median of macOS `wait4` process peaks in
each primary session; file and code sizes come from the actual timed files.

| Configuration | Session 1 RSS MB | Session 2 RSS MB | File MB | Machine-code MB |
|---|---:|---:|---:|---:|
| Rust | 140.39 | 141.06 | 0.756 | 0.347 |
| Parent | 162.74 | 161.43 | 5.468 | 4.304 |
| Candidate | 161.75 | 161.39 | 5.468 | 4.304 |

The candidate file is 16 bytes smaller while code is 384 bytes larger. These
changes do not establish a meaningful size or memory improvement. Content-free
paused worker-entry heaps contain parent 7,808 blocks / 127.47 MB, candidate
7,824 / 129.07 MB and Rust 456 / 141.23 MB. Different worker progress prevents
interpreting these live snapshots as matched allocation costs or RSS peaks.

Nine separate full-input counter processes, three per executable, give:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.169 | 8.013 | 2.36 | 0.03 | 686 |
| Parent | 26.391 | 7.236 | 2.06 | 0.04 | 7,069 |
| Candidate | 26.363 | 7.162 | 2.04 | 0.04 | 6,009 |

The separate prefix counter medians are candidate **1.521 billion instructions,
0.646 billion cycles, 0.16 user CPU s**; parent **1.517 billion, 0.542 billion,
0.13 s**; Rust **0.307 billion, 0.082 billion, 0.02 s**. Kernel CPU rounds to
0.00 s in that batch. These diagnostic counters sum threads; rounded elapsed
values do not replace primary timings.

[Full diagnostics](../sized-schedule-diagnostics-v1/results.json),
[prefix counters](../sized-schedule-prefix-counters-v1/results.json) and
[read-only thread observations](../sized-schedule-thread-lifetimes-v1/results.json)
retain raw results. Thread endpoints are sampled CPU lower bounds and do not
identify actual core assignments. The two longest Mech workers remain roughly
0.44–0.47 CPU seconds in these instrumented observations; size ordering has not
eliminated the long tail.

## Profiles and qualifications

Three completed full profiles match the timed candidate's entire machine-code
section. Across 4,757 worker observations, 75.45% are generated counting loops,
14.15% active work accounting, 1.11% accounting waits, 5.32% storage helpers,
1.58% helper bridges and 2.40% other locations. These are sampled stack-location
shares including waits, not elapsed or CPU time shares.

The normal prefix attachment missed its already completed subject and produced
no stack file. Its failed controller, successful subject/output and reaped
sampler/inventory remain retained. Three subsequent prearmed captures completed
correctly; one has an empty call graph. Analysis uses **all two nonempty
captures**, records the selection and retains all three raw files. Across only
145 observed worker stacks, 54.48% are storage helpers, 13.10% active accounting,
5.52% accounting waits and 15.17% generated counting loops. This sparse diagnostic
points toward distinct-key insertion/growth as a short-input investigation,
without assigning precise time to it. Its Rust reference is the earlier
**full-input** profile, not a matched prefix profile.

[Full profile partition](../sized-schedule-full-remaining-profile-v1/results.json),
[prefix partition](../sized-schedule-prefix-remaining-profile-v2/results.json)
and [capture inventory](prefix-observation-inventory.json) preserve scope and
limitations. Both failed analysis controllers are retained; no timings or
successful captures were repeated to repair analysis.

The exact clean revision passes **381 native host/stdlib checks, 13 parallel
checks, two focused checks and one catalog check: 397 checks**, with overlap
between filtered suites and three existing manual native exclusions. The first
two focused fixture versions each failed twice: trivial bodies lacked a source
loop, then string-accumulator bodies used unsupported private parallel storage.
The repaired fixtures use an already supported state/map loop, exercise unequal
Unicode input lengths and confirm source-order outputs and failure precedence.
All failed fixtures, exact source revisions and raw failures remain available.

[Verification](verification.json) recomputes the predeclared plan, both timing
sessions, bootstrap intervals, exact build-input equality, profiles, raw
counters, binary/heap evidence and **108 terminal, reaped, closed-group process
receipts**, including the two expected failed test processes and the missed
attachment's diagnostic error. All native work was serial under the retained
shared mutex, with clean unchanged compiler source. Run `python3
sized-schedule-v1/verify.py` from this study directory in the qualified checkout.

The earlier [host metadata trial](../host-metadata-trim-v1/README.md) isolates
the startup improvement. Descriptor loading costs approximately 7 ms after
trimming, while input capture and worker execution remain much larger targets.
