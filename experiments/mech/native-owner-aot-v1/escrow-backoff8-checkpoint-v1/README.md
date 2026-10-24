# Bounded budget-mutex backoff

Commit `2ac58b364c22be15aa0ba0e232409c1ce8c93327` extends the existing bounded work-ledger retry from six to eight rounds: at most 255 pause hints instead of 63 before the original blocking mutex. This is the only production source change from accepted IR78. All debit, error, poison-recovery and finite-budget logic remains unchanged. The Mech performance program, bytecode, generated object, seven-worker limit and secured launch policy are identical. **The change is retained after two separate timing batches; Rust parity remains incomplete.**

## Complete-process timing

Each batch uses all six balanced execution orders on 125 million selected bases. Startup and secured shutdown are included; no full-input warmup or outlier is excluded. Batches and diagnostics remain separate.

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial | Exact Rust #7 | 0.5610 | 1.000× |
| Initial | Six-round Mech | 0.7508 | 1.338× |
| Initial | Eight-round Mech | 0.7348 | 1.310× |
| Independent repeat | Exact Rust #7 | 0.5621 | 1.000× |
| Independent repeat | Six-round Mech | 0.7607 | 1.353× |
| Independent repeat | Eight-round Mech | 0.7438 | 1.323× |

The candidate median falls **2.13% initially and 2.23% in the repeat**, with five faster matched pairs in each batch. Ranges overlap: this is a modest observed improvement, not evidence of a universal gain. All 36 full observations verify complete output. Each Mech process performs 874,999,961 physical map updates across seven complete maps and seven peak workers, with five actually admitted caches.

Raw samples and standard deviations are retained in the [initial aggregate](../full-escrow-backoff8-cohort-v1/results.json) and [repeat aggregate](../full-escrow-backoff8-replication-v1/results.json). The separate one-million-base prefix has Rust **0.02119 s / 1.000×**, six-round Mech **0.10697 s / 5.049×**, and eight-round Mech **0.09051 s / 4.272×**, with one excluded warmup and three measured observations per subject. It is not pooled with the full input.

## CPU tradeoff and profiles

Nine separate [counter processes](../escrow-backoff8-hardware-v1/results.json) give these medians:

| Executable | Instructions, billions | Cycles, billions | User CPU seconds | System CPU seconds | Involuntary context switches |
|---|---:|---:|---:|---:|---:|
| Exact Rust #7 | 33.191 | 8.021 | 2.37 | 0.03 | 566 |
| Six-round Mech | 26.881 | 7.596 | 2.04 | 0.16 | 26,724 |
| Eight-round Mech | 26.771 | 7.637 | 2.11 | 0.11 | 18,889 |

Kernel CPU falls about 31% and involuntary switches about 29%, while user CPU rises. Total cycles rise about 0.5%; the optimization trades more active waiting for less parking. CPU seconds sum across threads, and their differences cannot be subtracted directly from elapsed time. macOS process instruction counters include user and kernel execution; off-CPU waiting retires no instructions in the waiting thread. See the [Apple counter documentation](https://github.com/apple-oss-distributions/top/blob/main/top.1).

Three fresh profiles match the timed executable's entire machine-code section. Their 4,929 worker observations partition into 69.41% generated loops, 13.59% active work accounting, 5.64% budget waits, 7.10% storage and 4.26% bridge/other locations. The accepted six-round IR78 profiles had 8.42% budget waits and 10.89% active accounting; the total accounting share is almost unchanged. These are sampled thread locations, not elapsed-time or CPU-time shares. The same earlier Rust capture is retained as a reference and is not described as newly collected.

[Kernel route extraction](kernel-routes.json) identifies worker waits beneath the shared ledger through `__psynch_mutexwait`, and mutex-release/wake work through `__psynch_mutexdrop`. The parent waits separately in `pthread_join` / `__ulock_wait`. Stack locations do not count syscalls or attribute all system CPU to those paths.

## Remaining preparation gap

Six separate [read-only thread observations](../escrow-backoff8-thread-lifetimes-v1/results.json) retain every sampled thread and CPU endpoint. Polling changes execution; these are not additional timing samples. In these diagnostic runs the candidate's elapsed ordering reverses relative to the control, and that result is retained rather than discarded.

For current Mech, first substantial worker appearance is bracketed by polls at **0.221–0.236 s** and **0.227–0.242 s**. Rust's brackets are **0.139–0.150 s** and **0.139–0.154 s**. The main thread's observed CPU lower bounds are **0.218–0.219 s** for Mech versus **0.134–0.137 s** for Rust. These endpoints support investigating serial preparation; they are not exact phase timers or an exact accounting of the elapsed gap. The substantial non-main threads are not mapped to source widths.

The [main-thread partition](preparation.json) retains 1,798 observations: 1,200 worker-join locations, 219 unresolved root-only stacks, 210 input-capture/source-selection locations, 65 selected-line joining locations, 32 generated byte-map locations, 16 reads, 10 string-geometry locations, five mapped-output UTF8 validation locations and 41 other locations. Unresolved `_dyld_start` leaves are not attributed to loader work. Input capture and source selection are the largest identified preparation category; mapping already has an AArch64 SIMD implementation. Further work should inspect that source traversal and its emitted guards before adding another mapping optimization.

## Validation and evidence

At the exact timed revision, **26 worker-budget tests, 377 native tests and one catalog test pass**, with three existing manual native exclusions. Tests retain bounded fallback, poison recovery, concurrent exact two-dimensional spending, finite denial, source continuations and unchanged program outputs. No budget is enlarged or bypassed, no table is omitted, and no source-query shortcut is introduced.

[Checkpoint verification](results.json), reproduced by `python3 verify_escrow_backoff8.py`, checks both timing batches, three exact-code profiles, eighteen malformed metadata rejections and **78 terminal owned-process receipts**. All native work ran sequentially under the shared benchmark lock, with clean unchanged compiler source during each execution. Canonical benchmark data is unchanged. The rejected full-refill experiment remains documented separately and is not reintroduced.
