# Preparation and worker boundaries after finite credits

This diagnostic instruments production checkpoint `7a715c12a055472247bab992904f43a9962cafd1`. Diagnostic source `7885f3ec85523566d94a21111d9d1e6026705931` combines the retained main-thread phase clocks and in-task per-width counters. The complete guest object, descriptor, bytecode and resource image are unchanged. Host machine code is instrumented and is **not** the primary timing executable.

Six balanced sequential observations per language verify complete output, all seven maps, all 874,999,961 original updates and 854,497 actual credit debits in every Mech run. Both diagnostic hosts first pass the independent prefix and all boundary parsers. No run is excluded; these executions supply zero primary timing observations.

## Main-thread preparation

| Measured CPU interval | Mech, s | Rust, s |
| --- | ---: | ---: |
| Before capture | 0.007281 | — |
| Input interval, including source scanning | 0.138687 | 0.127773 |
| EOF to worker launch | 0.039886 | 0.000030 |
| Spawn calls | 0.000070 | 0.000070 |

Mech reaches worker launch about 58 ms later in this diagnostic. Actual spawn calls remain around 70 microseconds. The delay chiefly precedes thread creation. The CPU and wall offsets are retained independently in the raw analysis; clocks start at their respective owned main boundaries.

| Nested Mech preparation span | CPU, s |
| --- | ---: |
| borrow_rows | 0.001025 |
| source_scan | 0.073019 |
| selected_join | 0.020438 |
| join_copy | 0.020427 |
| map_prepare | 0.001886 |
| map_kernel | 0.013021 |
| map_finish | 0.002262 |

Borrowing and scanning occur inside input capture. The copy span occurs inside selected joining. These intervals overlap and must not be added into an elapsed-time decomposition. Earlier preparation milestones remain around 0.186 s main CPU before worker launch. The scalar source scan remains about 73 ms, copying about 20 ms and the existing normalization kernel about 13 ms.

## Counting and completion

| Width | Mech count CPU, s | Rust count CPU, s | Mech / Rust | Mech task finish after main, s | Rust task finish after main, s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.145520 | 0.299403 | 0.486× | 0.335254 | 0.429262 |
| 2 | 0.137598 | 0.295756 | 0.465× | 0.327912 | 0.426802 |
| 3 | 0.137824 | 0.297438 | 0.463× | 0.327507 | 0.424988 |
| 4 | 0.133246 | 0.300367 | 0.444× | 0.320712 | 0.430993 |
| 6 | 0.153562 | 0.254816 | 0.603× | 0.343313 | 0.383939 |
| 12 | 0.408325 | 0.386548 | 1.056× | 0.604376 | 0.518607 |
| 18 | 0.395914 | 0.407035 | 0.973× | 0.592140 | 0.538492 |

Width 12 is now the latest Mech task in the median timeline. Its count CPU is about 5.6% above Rust, while width 18 is about 2.7% below Rust. The five cached widths remain much shorter. Mech publication takes about 4.0 ms for width 12 and 6.7 ms for width 18; individual setup and retirement intervals are small. Rust returns maps from its counting tasks and formats/retires them in main, so compare counting with counting rather than equating the full task bodies.

The two long Mech count intervals still execute about 5.003B and 4.845B instructions, versus Rust's 4.285B and 4.287B. Their performance/efficiency-core residence differs and is recorded, not assigned or tuned. No counter configuration, CPU priority, QoS, affinity or power setting is changed.

## Consequence and verification

The next implementation target is the scalar source scanner: current code repeatedly checks and transports its closed-region bookkeeping across source sites. Register-resident private scalar-tail state is a contained general compiler experiment. Original fuel debits, checked continuation sites, input-window pause/resume and failure order must remain. It has no measured gain yet. Ordinary-loop pipelining remains a separate opportunity; the remaining gap should not be attributed entirely to worker CPU.

`verify.py` checks 15 terminal owned native receipts: one combined diagnostic build, two prefix qualifications and twelve full processes. It verifies the preserved guest/resources, launcher/build-script pin updates with zero removed checks, exact output, all worker/phase parsers, source snapshots, original updates and actual credit selection. All processes exit normally, are reaped and have closed groups with no signals or cleanup errors. The protected primary Rust executable and canonical dataset remain unchanged.
