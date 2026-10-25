# Private join/map buffer ownership

The private-buffer path is correctness-qualified and retained as the foundation for direct transform-on-copy. Its measured gain varies substantially: the first two sessions show paired reductions of 2.42% and 4.36%, while a predetermined clean holdout shows only 0.24%. Every matched pair favors it across all three sessions, but a consistent 2–4% benefit is not established. The qualified ordinary parent remains a control for the next larger change.

## Complete-process timings

Production source: [`88b883b4cf`](https://github.com/mech-lang/mech/commit/88b883b4cfcdc8625440b3f075c8334bfeb09382), branch `codex/native-private-join-buffer`. Parent: `bdb3c511cd552ffc143460d6e1ae7edd04885a7f`. The unpromoted scalar counter, register and cold-origin trials are absent from this lineage.

Each session contains all six balanced subject orders, six complete observations per subject, no excluded full-input warmups and no excluded outliers. Subjects execute sequentially under the same lock. Secured Mech startup through process exit is included, as is Rust's complete process.

| Session | Private-buffer candidate | Qualified parent | Exact Rust #7 | Paired change; 95% interval |
| --- | ---: | ---: | ---: | ---: |
| [1](../full-private-join-buffer-v1/results.json) | **0.600933 s / 1.081× Rust** | 0.618196 s / 1.112× Rust | 0.556157 s / 1.000× | −2.42%; [−4.03%, −1.76%] |
| [2](../full-private-join-buffer-v2/results.json) | **0.595207 s / 1.067× Rust** | 0.625121 s / 1.120× Rust | 0.557934 s / 1.000× | −4.36%; [−5.93%, −3.32%] |
| [3: clean holdout](holdout-v1/capture/results.json) | **0.604846 s / 1.101× Rust** | 0.605346 s / 1.101× Rust | 0.549571 s / 1.000× | −0.24%; [−3.00%, −0.08%] |

All eighteen matched pairs favor the candidate, and each reported interval is below zero. The holdout does not reproduce the larger effect size. The first two Rust gaps are **0.044776 s** and **0.037273 s**; the latest holdout gap is **0.055275 s**. Parity is not established. These are contemporary controls, not ratios constructed from historical medians on another run or machine.

The holdout was fixed after the separate instrumented cohort reversed elapsed ordering and showed only a modest preparation reduction. It runs unchanged production executables without probes, retains all eighteen observations and is not repeated to obtain a preferred outcome. Its build source remains `88b883b4cf`; observer Git state is explicitly the separate diagnostic branch `f5391eacf5`, not relabeled as the production source. [Holdout verification](holdout-v1/verification.json) checks all eighteen terminal native receipts and exact executable pins.

The separate one-million-base [prefix cohort](../private-join-buffer-timing-v1/results.json), one excluded warmup and three measured complete processes per subject, gives **0.090403 s / 4.395× Rust** for the candidate, **0.088066 s / 4.281×** for the parent and **0.020570 s / 1.000×** for Rust. This smaller cohort does not show a prefix/startup gain and is not pooled with the full-input sessions.

## Physical change

The existing source-derived complete-use proof establishes that the selected join's intermediate String is consumed only by the proved copy/initializer/map chain. The earlier composition prototype still constructed a canonical frozen String, imported it into the memory account, immediately unwrapped it into owned mutable bytes, and later validated the whole UTF-8 buffer again.

The new path carries a `NativePrivateStringBuffer` containing the unique initialized allocation, its exact capacity reservation and the prepared factory's String schema key. It has no frozen Value identity or semantic arena slot. Its constructor checks the actual TextJoin factory, dimensionless String output, current work account and exact capacity. It exposes no mutable byte loan; the already transformed buffer travels directly to the original finish.

This removes intermediate canonical Value/shape/node/import construction and the immediate snapshot-to-bytes ownership conversion. One UTF-8 validation remains when the private buffer is formed; transferring that typed initialized String to the original final sink requires no second scan or allocation. Final semantic result publication still uses the maintained canonical path.

Physical chunk copying followed by emitted mapping still occurs. Transforming directly from selected source spans into the final destination is a separate next factor. This experiment compares the composed private-owner path to the qualified ordinary parent; the older prototype ran on an earlier lineage, so these primary comparisons do not isolate the owner elision from chunk-local composition. No source edit, benchmark-name/content recognition, dense-counter substitution, query-only shortcut or whole-program Rust replacement is introduced.

## Original boundaries and correctness

The original source and bytecode are unchanged, as are the resource image, finite secured launch limits, seven-worker cap and complete table workload. Every full Mech process verifies **125,000,000 fused selected bytes**, **seven complete maps**, **874,999,961 original physical updates**, **854,497 original credited batches**, original default growth and exact output.

The original full join envelope is admitted before allocation. Only the actual backing-capacity claim transfers to the private owner; unused physical canonical-construction capacity retires. Original join/map work prices and per-operation resource admissions remain. Missing-key errors stay deferred to the original selected lookup after complete input and original earlier admissions. Source/map generations, absent intermediate slots, live loan protocol, complete-use boundaries and the same memory account remain checked. Unsupported or shared/Unicode/non-byte representations keep the ordinary path.

The fixed production revision passes **401 native checks**, **28 captured-line checks**, **36 finite worker-credit checks** and **one catalog check**, with three existing manual tests ignored. Seven additional focused executions cover actual fused paths in original/decoded artifacts, Unicode/CRLF/empty fallbacks, observed-source and separator fallbacks, late IO/UTF-8 error precedence, exact/one-short original limits, global pressure, replay/generation/missing-owner rejection, and complete cleanup. New actual-factory cases reject foreign accounts, insufficient backing capacity and wrong factories with their precise expected errors.

The first qualification controller expected five focused tests; the actual successful receipt contains seven, including both captured-input differential cases. That controller stopped before attempting another native process. Its original script is retained, and `validate-v2.py` verifies the actual scope before running full qualification. No native qualification failure or output is discarded.

Typed IR86 distinguishes the new ownership path, with ABI30 and work policy69 retained from the existing composed-join machinery. The source's finite prices and original funded batch count remain intact; no allowance is renewed.

## Generated code, profiles and size

[Exact object inspection](code-inspection.json) verifies that **all eight nonentry function bodies remain byte-identical**, including the existing mapper and both long counting-loop families. The main entry changes from **43,376 to 43,636 bytes** to select the composed path. Source plans, visits, scalar aggregates, borrowed layouts and scalar loan homes/prices are identical. Raw object disassembly is retained. The private owner executes in host storage handling; it replaces no generated counting kernel.

The profiling executable's **entire machine-text section matches** the timed candidate. [Three fresh captures per subject](analysis.json) retain waits and partial unwinds; candidate worker observations are 87.33% in generated counting loops, 5.71% in storage helpers, 1.37% in active work budgeting and 0.83% in active credit handling. Budget/credit waits are 0.59%/0.13%. These observations are not wall-time or CPU-time percentages.

[Nine independent hardware-counter processes](counters/results.json), excluded from primary timings, give:

| Median diagnostic | Candidate | Parent | Rust |
| --- | ---: | ---: | ---: |
| Instructions | 24.424 billion | 24.525 billion | 33.131 billion |
| Cycles | 5.884 billion | 5.953 billion | 7.884 billion |
| User CPU | 1.66 s / 0.712× Rust | 1.68 s / 0.721× | 2.33 s / 1.000× |
| System CPU | 0.03 s / 1.000× Rust | 0.03 s / 1.000× | 0.03 s / 1.000× |

The executable is **5,484,736 bytes**, versus **5,501,200 bytes** for the parent. Machine text is **4,321,796 bytes**, down 5,116 bytes from the parent. Primary candidate peak RSS is **163.45/162.49 MB**, versus parent **162.55/162.73 MB** and Rust **140.39/141.05 MB** across the two sessions. No memory reduction is established.

[Verification](verification.json) checks **83 terminal owned-process receipts**, exact outputs/work counts, immutable source and script pins, inherited locking, complete reaping/group closure, bytecode/resources, changed-function boundaries, whole-text profile equivalence and the physical private-owner handoff in the measured source. All native processes succeed without signals or cleanup errors. The canonical benchmark dataset is unchanged. The additional eighteen holdout receipts and twenty-two fresh phase/worker receipts bring the complete retained campaign to **123 terminal native receipts**. Fresh [main/worker diagnostics](../private-join-preparation-workers-v1/README.md) verify every task width and confirm that the copy and map passes still dominate post-EOF preparation. They do not explain the full first-two-session primary gain, and their instrumented elapsed samples are never pooled with the primary timings.
