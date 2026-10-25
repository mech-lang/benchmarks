# Selective borrowed-view field loads

The intended machine-code cleanup is verified, but this isolated change is **not promoted as a performance improvement**. The first complete-process session regresses against its byte-table parent; the second is inconclusive. The unchanged parent remains available for interaction experiments.

## Complete-process results

Each session contains eight balanced four-subject orders, with eight observations per subject. Session 2 reverses the order list. Processes run serially under the shared benchmark mutex; Mech includes secured startup through exit. No full-input warmup or outlier is excluded. Rust is the exact unchanged upstream #7 executable.

| Session | Selective-field candidate | Byte-table parent | Ordinary control | Rust #7 |
| --- | ---: | ---: | ---: | ---: |
| [1](../full-borrowed-field-loads-v1/results.json) | 0.607514 s / 1.090× Rust | 0.590231 s / 1.059× | 0.616664 s / 1.106× | 0.557531 s / 1.000× |
| [2](../full-borrowed-field-loads-v2/results.json) | 0.605106 s / 1.080× Rust | 0.599552 s / 1.070× | 0.614446 s / 1.097× | 0.560362 s / 1.000× |

| Paired candidate change | Session 1; 95% interval | Session 2; 95% interval |
| --- | ---: | ---: |
| Versus byte-table parent | +2.83%; [+1.30%, +3.59%] | +0.73%; [−1.66%, +3.53%] |
| Versus ordinary control | −1.47%; [−2.48%, +1.45%] | −2.31%; [−3.12%, −0.05%] |

The candidate wins zero of eight and four of eight matched pairs against its immediate parent. The separate one-million-base [prefix cohort](../borrowed-field-loads-timing-v1/results.json) gives 0.123317 s / 10.047× Rust, versus parent 0.106395 s / 8.668× and Rust 0.012274 s / 1.000×. Its three excluded warmups and nine measured processes are separate from the full input.

## Compiler and assembly

Source [2e58f2abdf](https://github.com/mech-lang/mech/commit/2e58f2abdfd39ef296b5c9bb470be3aa4dfad925), branch `codex/native-borrowed-field-loads`, follows byte-table parent `8946ccbae9`. A borrowed Length action loads only its length home instead of loading a pointer/length pair and discarding the pointer. Other pair callers consume both fields. IR89 distinguishes the new instructions; ABI32 and work policy69 remain unchanged. The prior IR88 identity is explicitly rejected.

The [assembly gate](code-inspection.json) ran before full timings. It confirms removal of both identified discarded-pointer sequences and retention of the required length loads and result stores. The root function span shrinks by 40 bytes, from 43,636 to 43,596 bytes. All nine nonentry functions remain byte-identical, including the joined-map kernel and all counting variants. Plans, visits, aggregate/borrowed layouts, finite prices, original source, bytecode, resources and inputs remain identical. No memory flags changed.

Root register allocation also changes, including its locals base register. A shorter root function does not imply a runtime improvement. The measured regression cannot be assigned to a particular instruction without further evidence.

## Correctness and exact-binary diagnostics

All 405 native tests, 30 line-storage tests, 36 finite-credit tests, one catalog test and eight focused window tests pass at the final clean source. Three existing manual native tests remain ignored. Original and decoded programs cover incremental callbacks and EOF, Unicode and CRLF, precise errors and finite work, rejected foreign producers/ledgers/extents, and complete loan and owner retirement.

Every full Mech run matches the independent output and retains seven complete maps, 874,999,961 physical updates, 854,497 credited batches and seven workers. Candidate and byte-table parent transform 125 million fused bytes. This change introduces no workload recognition and replaces no canonical dataset timing.

The [profile build](../profile-borrowed-field-loads-build-v1/results.json) has the same entire machine-code text as the timed executable. Six fresh completed captures profile the exact candidate and exact Rust executable. Profiles include sampling overhead and are excluded from primary timings. Of 3,705 Mech worker observations, 88.34% occur in generated counting loops, 4.67% in storage helpers, 3.35% in active work accounting, 1.84% in generated helper bridges and 0.40% in accounting waits. Main-thread observations include 59 in the joined-transform kernel and 97 in the generated root. These are observations, not a wall-time decomposition; no parent profile was captured in this study.

Separate four-order [counter diagnostics](counters/results.json) retain all sixteen runs:

| Executable | Instructions | Cycles | Summed user CPU | System CPU |
| --- | ---: | ---: | ---: | ---: |
| Selective-field candidate | 24.387 billion | 6.025 billion | 1.705 s / 0.727× Rust | 0.030 s |
| Byte-table parent | 24.382 billion | 5.913 billion | 1.675 s / 0.714× | 0.030 s |
| Ordinary control | 24.514 billion | 5.905 billion | 1.665 s / 0.710× | 0.030 s |
| Rust #7 | 33.152 billion | 7.918 billion | 2.345 s / 1.000× | 0.030 s |

The candidate's counters likewise provide no positive isolated result. Timed executable size is 5,501,280 bytes. Session peak RSS medians are approximately 162.9–163.0 MB, versus Rust 140.4–140.8 MB. Instruction, CPU and RSS figures measure distinct quantities from complete-process elapsed time.

[Verification](verification.json) validates 119 terminal owned-process receipts, all outputs and work counts, source pins, assembly, exact-code profiles, counters and all 64 primary full-input observations. Every process is reaped with a closed group, no signals and no cleanup errors. The next independent experiment is narrowly proved nontrapping private homes, with alias-only compilation retained as a differential reference. No readonly, alignment or arbitrary-movement promise is implied.
