# Rejected full-refill fast path

Commit `36a0d26e05b92f0f3fb21bdbd3605af2108ec882` precomputes full refill thresholds and charges before the shared work-budget transaction. It preserves the original small-batch fallback, finite limits, error precedence and 1,024-update maximum. **The apparent speedup did not reproduce; commit `c4db5641680c171f362f79b809fd80f57c6e7639` reverts it.** The resulting production tree exactly matches accepted IR78 commit `65dfd8bef29a8aef4cddd6926ff6461a959c24be`.

## Complete-process timing

Both batches use the same 125-million-base input and all six balanced orders, including startup and secured shutdown. No full-input observation is excluded. The batches remain separate.

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial | Exact Rust #7 | 0.5464 | 1.000× |
| Initial | Accepted IR78 | 0.7511 | 1.375× |
| Initial | Refill candidate | 0.7408 | 1.356× |
| Independent repeat | Exact Rust #7 | 0.5566 | 1.000× |
| Independent repeat | Accepted IR78 | 0.7408 | 1.331× |
| Independent repeat | Refill candidate | 0.7559 | 1.358× |

The initial median falls 1.38%, with six faster matched pairs. The repeat rises 2.03%, with only two faster pairs. No performance improvement is established. Raw observations and standard deviations are retained in the [initial aggregate](../full-refill-fastpath-cohort-v1/results.json) and [repeat aggregate](../full-refill-fastpath-replication-v1/results.json).

The separate one-million-base prefix has Rust 0.01981 s / 1.000×, parent 0.10216 s / 5.158× and candidate 0.08905 s / 4.496×. Its one excluded warmup and three observations per executable are recorded separately; they are not pooled with full input.

## Counters and kernel routes

Nine separate complete-process diagnostic runs give these median counters. These are not the primary elapsed-time observations.

| Executable | Instructions, billions | Cycles, billions | User CPU seconds | System CPU seconds | Involuntary context switches |
|---|---:|---:|---:|---:|---:|
| Exact Rust #7 | 33.147 | 7.986 | 2.36 | 0.03 | 629 |
| Accepted IR78 | 26.868 | 7.525 | 2.02 | 0.16 | 25,835 |
| Refill candidate | 26.908 | 7.599 | 2.04 | 0.16 | 26,279 |

macOS process retired-instruction counters include user and kernel execution. Off-CPU waiting contributes no retired instructions in the waiting thread. CPU time sums across threads and cannot be subtracted directly from elapsed time. See Apple's [time implementation](https://github.com/apple-oss-distributions/shell_cmds/blob/main/time/time.c), [counter documentation](https://github.com/apple-oss-distributions/top/blob/main/top.1) and [Recount architecture](https://github.com/apple-oss-distributions/xnu/blob/main/doc/observability/recount.md).

Three exact-code candidate profiles retain 5,025 worker observations: 67.50% generated loops, 11.28% active work accounting, 9.00% budget waits, 8.04% storage and 4.18% bridge/other active work. These are sampled thread locations, including waiting, not elapsed-time or system-CPU shares.

[Kernel route extraction](kernel-routes.json) finds worker `__psynch_mutexwait` beneath the shared work ledger (452 observations), and `__psynch_mutexdrop` during mutex release/wake (63). The parent also waits for worker completion through `pthread_join` and `__ulock_wait` (1,207); that is a distinct route. Smaller samples cover input reads, memory release and thread creation. These observations neither count syscalls nor establish that all 0.16 system CPU-seconds are mutex overhead. The next isolated hypothesis is a slightly longer bounded spin before parking on the existing mutex.

## Validation and reproducibility

Five focused tests, **382 native tests and one catalog test** pass at the exact timed candidate revision; three pre-existing manual native tests remain excluded. Coverage includes the original expression at arithmetic boundaries, small-batch fallback, finite debits, error precedence and concurrent escrow consistency. Every full observation verifies output, 874,999,961 physical map updates, seven maps and peak workers, and five admitted caches. The original Mech program, bytecode, finite policy and canonical dataset are unchanged. The emitted Mech object is identical to IR78; only the runtime refill selection and its tests changed.

All three profiling copies match the timed executable's complete machine-code section. Static inspection retains 50 generated paths and both runtime refill implementations, including the candidate's fallback divisions. Static instruction counts do not establish dynamic frequency or time saved.

Run `python3 verify_refill_fastpath.py` from the study directory to recheck retained receipts and binaries. [Verification](results.json) covers 36 full-input observations across the two separate batches, three profiles, eighteen malformed metadata rejections and 72 reaped processes with closed groups under the shared serial benchmark mutex. The compiler build, validation, raw timings, counter runs, failed performance hypothesis and revert remain in history. Rust runtime parity remains incomplete.
