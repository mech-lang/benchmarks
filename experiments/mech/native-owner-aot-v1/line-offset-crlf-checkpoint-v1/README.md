# Rejected CRLF/offset scan fusion

This report records the standalone trial. A later
[two-factor study](../preparation-combined-checkpoint-v1/README.md) retains this
change combined with private metadata regions; the decision below does not rule
out that interaction or remove either variant from further investigation.

Candidate `8c9713b5a77e44175609d5dadef5d86a8b480593` calculates CRLF payload geometry while constructing the existing admitted newline-offset array, replacing a separate CR search for retained input chunks. Sealed ranges without offset backing keep their original scan. Storage layout, work debits, source, bytecode, generated object, secured policy and seven-worker count remain unchanged. **The candidate is reverted after failing the predeclared expanded-batch threshold.**

Revert `b7f50099dc22ab435032fee4e951e4914fe0d98f` has exactly the same Git tree as accepted twelve-round code `438646017717a5c4392721f13c6f935e88c59527`: `4588ed35da25a135eded8f1bf11c7254fdccc413`. The earlier kernel improvement is retained. Rust parity remains incomplete.

## Complete-process results

Every batch uses 125 million selected bases, including startup and secured shutdown. Executables run serially under the common lock. No full-input warmup or outlier is excluded, and the three batches remain separate.

| Batch | Executable | Median seconds | × Rust time |
|---|---|---:|---:|
| Initial, six each | Rust | 0.5568 | 1.000× |
| Initial, six each | Accepted Mech | 0.7058 | 1.268× |
| Initial, six each | Candidate | 0.7100 | 1.275× |
| Repeat, six each | Rust | 0.5521 | 1.000× |
| Repeat, six each | Accepted Mech | 0.7115 | 1.289× |
| Repeat, six each | Candidate | 0.7105 | 1.287× |
| Expanded, thirty each | Rust | 0.5549 | 1.000× |
| Expanded, thirty each | Accepted Mech | 0.7088 | 1.277× |
| Expanded, thirty each | Candidate | 0.7075 | 1.275× |

The initial median regresses **0.60%**, with two of six faster matched pairs. The repeat improves **0.15%**, with three of six faster pairs. Those small opposing effects, together with lower observed main-thread CPU in separate diagnostics, motivated one larger follow-up.

The [expanded plan](../line-offset-crlf-diagnosis-v1/expanded-plan.json) fixes five shuffled balanced blocks, thirty observations per executable, no exclusions, and a promotion threshold of at least **1% lower median plus twenty of thirty faster pairs**. The expanded result improves only **0.187%**, with **fifteen of thirty** faster pairs, failing both conditions. Candidate/control standard deviations are 0.0154/0.0113 seconds. Rust has large observations retained in full, with standard deviation 0.1614 seconds; its median is not recomputed after exclusions.

All **126 full-input observations** verify complete output. Every Mech process performs 874,999,961 physical updates in seven complete maps, reaches seven peak workers, and admits five lookup caches. The [initial](../full-line-offset-crlf-cohort-v1/results.json), [repeat](../full-line-offset-crlf-replication-v1/results.json), and [expanded](../full-line-offset-crlf-expanded-cohort-v1/results.json) aggregates retain every raw observation and execution order.

The separate one-million-base prefix has Rust **0.02097 s / 1.000×**, accepted Mech **0.11159 s / 5.322×**, and candidate **0.09055 s / 4.319×**, with one excluded warmup and three measured processes per executable. This small batch is not pooled with full input and does not override the expanded-batch decision.

## Counters and preparation observations

Nine separate serial [counter processes](../line-offset-crlf-hardware-v1/results.json) give these medians:

| Executable | Instructions, billions | Cycles, billions | User CPU seconds | Kernel CPU seconds | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.135 | 7.900 | 2.33 | 0.03 | 560 |
| Accepted Mech | 26.590 | 7.205 | 2.05 | 0.04 | 6,777 |
| Candidate | 26.372 | 7.367 | 2.10 | 0.04 | 4,839 |

The candidate retires about 0.82% fewer instructions, while cycles rise about 2.26%. These counters do not establish the cause of that difference. CPU seconds and cycles sum across threads, whereas completion depends on serial work, overlap and the last workers finishing. The diagnostic elapsed medians are 0.55 seconds for Rust, 0.71 for accepted Mech and 0.70 for the candidate; their centisecond rounding is not used in the promotion decision.

Three candidate profiles match the timed executable's entire machine-code section. The worker partition contains 69.40% generated loops, 15.84% active accounting, 1.08% budget waits, 9.33% storage, and 4.35% bridge/other locations. [Kernel routes](kernel-routes.json) retain 53 worker waits and twelve release/wake observations; the main thread separately has 1,243 join-wait observations. Stack locations do not count system calls or apportion kernel CPU or elapsed time.

Six separate [read-only thread observations](../line-offset-crlf-thread-lifetimes-v1/results.json) retain full output and every sampled thread. Candidate first substantial worker appearance is bracketed by **0.216–0.232 s** and **0.219–0.235 s**, versus **0.225–0.241 s** and **0.233–0.248 s** for accepted Mech. Those bounds overlap. Observed main-thread CPU lower bounds are **0.20898–0.20900 s** for the candidate and **0.21821–0.21868 s** for the control. Rust's worker-appearance bounds are around **0.139–0.154 s**, with main-thread CPU lower bounds near 0.134 seconds. Polling affects execution, misses work after the last poll, and does not produce exact phase clocks.

The [main-thread profile partition](preparation.json) retains 1,774 observations: 1,243 joins, 182 unresolved root-only stacks, 180 input-capture/source-selection locations, 64 selected-line joining locations, 31 generated byte-map locations, 23 reads, ten string-geometry locations, six mapped-output validation locations, and 35 other locations. Unresolved root-only observations remain unattributed. These data support investigating larger repeated costs in generated selection and preparation; they do not establish a sufficient full-program benefit for this scan fusion.

## Correctness and retained failure

At the timed revision, **45 line-storage tests and 26 worker-budget tests pass**. They include Unicode/CRLF fragment splits, dense and unaligned delimiters, exact and one-short work/memory limits, optional page storage, malformed counts and release ordering. Complete native executions separately verify every output and physical update. The full native/catalog promotion suite was not run for this rejected candidate. The accepted twelve-round code retains its exact-revision 377 native tests, 26 budget tests and one catalog check.

Initial commit `6a9244ae0` failed to compile one updated test because removing a constructor parameter removed type context for its reference sum. Commit `8c9713b5a` adds the explicit `usize` annotation. The [failed compile receipt](../line-offset-crlf-diagnosis-v1/compile-correction.json) is retained; it is not counted as a successful test or timing observation.

Run `python3 verify_line_offset_crlf.py` from the study directory to reproduce [checkpoint verification](results.json). It checks all three full-input batches, the separate prefix, three exact-code profiles, eighteen malformed metadata rejections, the expanded decision threshold, the exact revert tree, and **168 terminal owned-process receipts**: 167 successful processes plus the expected compile failure. All owned processes were reaped and groups closed. Compiler source remained clean and unchanged during each native execution; canonical benchmark data is unchanged.
