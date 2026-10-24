# Longer bounded budget-mutex retry

Commit `0b4ce3e7c316ae4248399c3ce1b2ed14b8eb65e2` extends the shared work-ledger retry from eight to ten rounds: at most 1,023 pause hints instead of 255 before the original blocking mutex. This is the only production change from `2ac58b364`. The Mech source, bytecode, generated object, finite debit logic, poison recovery, seven-worker limit and secured launch policy are unchanged. **The change is retained; Rust elapsed-time parity remains incomplete.**

## Complete-process timing

Each batch uses all six balanced execution orders on 125 million selected bases, with startup and secured shutdown included. No full-input warmup or outlier is excluded. All programs execute sequentially under the common benchmark lock.

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial | Exact upstream Rust #7 | 0.5581 | 1.000× |
| Initial | Eight-round Mech | 0.7436 | 1.332× |
| Initial | Ten-round Mech | 0.7244 | 1.298× |
| Independent repeat | Exact upstream Rust #7 | 0.5545 | 1.000× |
| Independent repeat | Eight-round Mech | 0.7435 | 1.341× |
| Independent repeat | Ten-round Mech | 0.7379 | 1.331× |

The median decreases **2.58% initially and 0.74% in the repeat**, with four and five faster matched pairs respectively. Mech ranges overlap. Rust has high observations in both batches, retained in full; its sample standard deviations are 0.1073 and 0.1336 seconds. Ten-round Mech's corresponding deviations are 0.0093 and 0.0040 seconds, versus 0.0097 and 0.0111 for eight rounds. The evidence supports a modest observed full-input improvement, with a smaller replication effect.

All 36 full-input observations verify complete output. Every Mech process executes 874,999,961 physical updates across seven complete maps and seven peak workers, with five admitted lookup caches. Raw observations, execution orders and statistics remain in the [initial aggregate](../full-escrow-backoff10-cohort-v1/results.json) and [separate repeat](../full-escrow-backoff10-replication-v1/results.json).

## Small-input uncertainty

The original one-million-base prefix regressed, so one additional batch was planned to investigate that result. Both use one excluded warmup and three fresh measured processes per executable; only the pinned build is reused. The repeat reverses the initial ordering. Neither batch is discarded or pooled with the other or with full-input measurements. **No small-input performance gain is established.**

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial prefix | Rust | 0.01270 | 1.000× |
| Initial prefix | Eight-round Mech | 0.08910 | 7.014× |
| Initial prefix | Ten-round Mech | 0.10977 | 8.641× |
| Prefix repeat | Rust | 0.02219 | 1.000× |
| Prefix repeat | Eight-round Mech | 0.10699 | 4.821× |
| Prefix repeat | Ten-round Mech | 0.08832 | 3.980× |

The initial change is +23.20%; the repeat is −17.45%. The [repeat plan](../escrow-backoff10-diagnosis-v1/prefix-repeat-plan.json) records why the additional batch was added, and [its receipt](../escrow-backoff10-prefix-repeat-v1/results.json) retains every fresh observation and build identity.

## Kernel work and CPU tradeoff

Nine separate serial [counter processes](../escrow-backoff10-hardware-v1/results.json) give these medians. They are diagnostics, not additional primary timing observations.

| Executable | Instructions, billions | Cycles, billions | User CPU seconds | System CPU seconds | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.140 | 7.930 | 2.35 | 0.03 | 532 |
| Eight-round Mech | 26.770 | 7.622 | 2.10 | 0.10 | 19,421 |
| Ten-round Mech | 26.632 | 7.486 | 2.13 | 0.06 | 9,621 |

Kernel CPU decreases **40%**, involuntary switches **50.5%**, cycles **1.8%**, and retired instructions **0.5%**. User CPU rises by 0.03 seconds. These CPU times sum across threads and are rounded by the diagnostic tool; they cannot be subtracted directly from elapsed time. macOS process instruction counters include user and kernel execution, while off-CPU waiting retires no instructions in the waiting thread. See [Apple's counter documentation](https://github.com/apple-oss-distributions/top/blob/main/top.1).

Three fresh profiles match the timed executable's entire machine-code section. Of 4,824 worker observations, **70.87%** are generated loops, **15.01%** active work accounting, **1.82%** budget waits, **8.50%** storage, and **3.79%** bridge/other locations. The prior eight-round profile had 5.64% budget waits and 13.59% active accounting. These are sampled thread locations, including waits, rather than elapsed-time or CPU-time shares. Capture windows differ. The earlier Rust profile is retained as a reference and was not recollected.

[Kernel stack routes](kernel-routes.json) retain 88 worker observations at `__psynch_mutexwait` and 23 at mutex release/wake. The main thread separately has 1,192 observations at `__ulock_wait` beneath worker joining. These observations do not count system calls or apportion system CPU seconds. Of the 88 sampled budget waits, 56 occur through loop refill, 20 through missing-key charging, 11 through frozen-map reads, and one through another ledger operation. Remaining kernel investigation should prioritize these worker-ledger routes; main-thread joining must be distinguished from lock contention.

The generated object remains SHA-256 `f05eea810efaa3ffb14e0e87c754093e6cf2eed3205075dd87bd87851886aeaa`. The fifty audited productive cycles retain their earlier instruction counts and zero stack accesses. The earlier serial-preparation evidence remains in the [eight-round report](../escrow-backoff8-checkpoint-v1/README.md); this experiment changes only bounded lock retry.

## Validation and reproduction

At the exact timed revision, **26 worker-budget tests, 377 native tests and one catalog check pass**, with three existing manual native exclusions. They cover bounded fallback, poison recovery, exact concurrent spending, denial, changed inputs, complete maps and source continuations.

Run `python3 verify_escrow_backoff10.py` from the study directory to reproduce [checkpoint verification](results.json). It checks both full-input and prefix batches, three exact-code profiles, eighteen malformed metadata rejections, and **84 terminal owned-process receipts**. All owned processes were reaped and their groups closed. Compiler source remained clean and unchanged during native execution; canonical benchmark data is unchanged. The [decision record](../escrow-backoff10-diagnosis-v1/decision.json) retains the measured gains and limitations.
