# Twelve-round bounded budget-mutex retry

Commit `438646017717a5c4392721f13c6f935e88c59527` extends the shared work-ledger retry from ten to twelve rounds, at most 4,095 pause hints instead of 1,023 before the original blocking mutex. This is the only production change from `0b4ce3e7c`. Source, bytecode, generated object, every debit, poison recovery, finite launch policy and seven-worker limit remain identical. **The change is retained; Rust elapsed-time parity remains incomplete.**

## Complete-process timing

Each separate batch uses all six balanced execution orders on 125 million selected bases. Startup and secured shutdown are included. No full-input warmup or outlier is excluded; executables run sequentially under the common lock.

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial | Exact upstream Rust #7 | 0.5546 | 1.000× |
| Initial | Ten-round Mech | 0.7213 | 1.301× |
| Initial | Twelve-round Mech | 0.7051 | 1.271× |
| Independent repeat | Exact upstream Rust #7 | 0.5537 | 1.000× |
| Independent repeat | Ten-round Mech | 0.7198 | 1.300× |
| Independent repeat | Twelve-round Mech | 0.7107 | 1.284× |

The median decreases **2.24% initially and 1.27% in the repeat**, with five and four faster matched pairs respectively. Ranges overlap. Candidate sample standard deviations are 0.0163 and 0.0118 seconds, versus 0.0091 and 0.0097 for the control. Rust's corresponding deviations are 0.0164 and 0.0087 seconds. These are modest observed improvements in two separately reported batches.

All 36 full-input observations verify complete output. Every Mech process performs 874,999,961 physical updates, seven complete packed SSA maps and seven peak workers, with five admitted lookup caches. The [initial aggregate](../full-escrow-backoff12-cohort-v1/results.json) and [repeat](../full-escrow-backoff12-replication-v1/results.json) retain all raw observations, orders and identities.

The separate one-million-base prefix uses one excluded warmup and three observations per executable:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Rust | 0.02090 | 1.000× |
| Ten-round Mech | 0.10997 | 5.261× |
| Twelve-round Mech | 0.10072 | 4.818× |

The prefix median decreases 8.41%. This single small cohort is not pooled with full input and does not establish a universal small-input gain; the prior ten-round experiment's conflicting prefix batches remain retained.

## Counters and remaining lock activity

Nine fresh serial [counter processes](../escrow-backoff12-hardware-v1/results.json) give these medians. They remain separate from primary benchmark samples.

| Executable | Instructions, billions | Cycles, billions | User CPU seconds | Kernel CPU seconds | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.146 | 7.927 | 2.34 | 0.03 | 608 |
| Ten-round Mech | 26.629 | 7.567 | 2.14 | 0.05 | 9,418 |
| Twelve-round Mech | 26.581 | 7.360 | 2.10 | 0.04 | 6,009 |

Kernel CPU decreases **20%** in the rounded diagnostics; involuntary switches decrease **36.2%** and cycles **2.7%**. User CPU also falls slightly in this batch. CPU seconds and counters sum across threads; fewer total instructions, cycles or CPU seconds do not imply a shorter critical path. Off-CPU waiting retires no instructions in the waiting thread. These diagnostic elapsed medians are 0.53 seconds for Rust, 0.72 for ten-round Mech and 0.70 for twelve rounds; their centisecond precision is not substituted for primary timing.

Three fresh profiles match the timed executable's entire machine-code section. Their 4,772 worker observations partition into **69.74%** generated loops, **16.83%** active work accounting, **0.80%** budget waits, **8.63%** storage and **4.00%** bridge/other locations. Of 38 budget-wait observations, 34 occur through loop refill and four through missing-key charging. The earlier ten-round profile has 1.82% budget waits. These are sampled thread locations, not CPU-time or elapsed-time shares. The earlier exact Rust capture remains a reference and was not recollected.

Active accounting is largely synchronization rather than price arithmetic: 427 exclusive observations end in the bounded lock helper, 133 in `pthread_mutex_trylock`, and 113 in `pthread_mutex_unlock`. These locations can include active waiting. [Kernel routes](kernel-routes.json) retain 38 worker wait observations and five at release/wake, versus 1,186 main-thread observations in joining. Stack observations neither count system calls nor apportion kernel CPU.

The generated object is still SHA-256 `f05eea810efaa3ffb14e0e87c754093e6cf2eed3205075dd87bd87851886aeaa`. All fifty audited productive cycles retain their earlier instruction counts and zero stack accesses.

## Worker startup and the serial path

Six fresh [read-only thread observations](../escrow-backoff12-thread-lifetimes-v1/results.json) inspect the exact executables. Polling affects execution; these are not additional benchmark samples or exact phase timers. Thread CPU endpoints are lower bounds, and substantial non-main threads are not mapped to source widths.

For current Mech, first substantial worker appearance is bracketed by **0.222–0.238 seconds** and **0.228–0.243 seconds**. Rust's corresponding brackets are **0.124–0.139** and **0.133–0.148 seconds**. Observed main-thread CPU lower bounds are **0.208–0.218 seconds** for Mech, versus **0.125–0.130** for Rust. The ten-round control's bounds are comparable to current Mech's. These results support targeting work before the workers begin, rather than treating that entire delay as thread-creation cost.

The [main-thread profile partition](preparation.json) retains 1,796 observations: 1,186 worker-join locations, 229 unresolved root-only stacks, 210 input-capture/source-selection locations, 66 selected-line joining locations, 33 generated byte-map locations, 14 reads, nine string-geometry locations, five mapped-output validation locations and 44 other locations. Unresolved root-only stacks remain unattributed; they are not labeled loader overhead. Among identified input-processing locations, emitted selection code and line framing merit further inspection. Existing optimizations include ASCII row qualification, whole-chunk payload facts, sequential directory hints and in-place SIMD mapping.

## Validation and reproduction

At the exact timed revision, **26 worker-budget tests, 377 native tests and one catalog check pass**, with three existing manual native exclusions. Worker tests run before native timing; full native and catalog validation run before promotion. Checks cover bounded fallback, poison recovery, concurrent exact two-dimensional spending, finite denial, changed inputs, source failures and complete maps.

Run `python3 verify_escrow_backoff12.py` from the study directory to reproduce [checkpoint verification](results.json). It checks both full-input batches, the separate prefix, three exact-code profiles, eighteen malformed metadata rejections and **78 terminal owned-process receipts**, including the six separate thread diagnostics. All owned processes were reaped and their groups closed. Compiler source remained clean and unchanged during native execution, and canonical benchmark data is unchanged. The [decision record](../escrow-backoff12-diagnosis-v1/decision.json) records the measured effects and next investigation.
