# Private-buffer preparation and per-width diagnostics

These fresh diagnostics measure production source [`88b883b4cf`](https://github.com/mech-lang/mech/commit/88b883b4cfcdc8625440b3f075c8334bfeb09382), qualified ordinary parent `bdb3c511c`, and protected upstream Rust #7. Instrumented hosts are separate from the [primary timed executables](../private-join-buffer-v1/README.md). No observation here is a primary timing sample.

The private buffer does not remove most post-EOF work: candidate CPU remains **0.038462 s**, versus **0.039963 s** for the parent. Actual copying and mapping remain the next larger target. The instrumented cohort shows only **0.001501 s** less post-EOF CPU and reverses overall instrumented elapsed ordering; it does not explain the full first-two-session primary gain. The subsequent predetermined uninstrumented holdout reports only a small gain. None of these observations is discarded or substituted for another cohort.

## Main-thread boundaries

Six balanced sequential full runs per subject retain complete input, all seven maps, default growth, finite original limits and seven internal workers.

| Nonoverlapping median CPU interval | Candidate | Parent | Rust | Candidate / Rust |
| --- | ---: | ---: | ---: | ---: |
| Before capture | 0.007503 s | 0.007381 s | Not separately reported | — |
| Input, including scanner | 0.119614 s | 0.119112 s | 0.131419 s | 0.910× |
| EOF to spawn calls | 0.038462 s | 0.039963 s | 0.000030 s | 1269.7× |
| Actual spawn calls | 0.000065 s | 0.000073 s | 0.000075 s | 0.867× |

Width-12 worker start after main is **0.166214 s / 1.264× Rust**, compared with parent **0.166755 s / 1.268×** and Rust **0.131515 s / 1.000×**. Thread creation is not the large delay.

## Actual fused-path phases

The existing clocks now cover each actual fused copy and emitted mapping loan. Full candidate runs contain **3,848 copy preparations**, **3,847 mapping loans**, one logical map preparation and two finish intervals. The final copy preparation observes completion. The parent has one broad copy interval and one broad mapping interval. Per-chunk clock overhead is therefore different; no exact instrumentation-overhead subtraction or primary elapsed decomposition is claimed.

| Nested median CPU span | Candidate | Parent |
| --- | ---: | ---: |
| Borrow rows | 0.000992 s | 0.000992 s |
| Scalar source scan | 0.073373 s | 0.073936 s |
| Selected join admission/setup | 0.000007 s | 0.020460 s including ordinary copying |
| Actual copy intervals | **0.021474 s** | **0.020448 s** |
| Logical map preparation | 0.000003 s | 0.001888 s |
| Emitted mapping intervals | **0.013469 s** | **0.013029 s** |
| Buffer validation/handoff and logical finish | 0.002304 s | 0.002365 s |

These spans overlap main intervals; parent selected joining contains its copy. The tiny candidate selected-join admission is not evidence that copying disappeared: its copying is recorded separately. Rust does not expose directly comparable nested spans, so no Rust ratio is assigned to them.

The next implementation will load selected source bytes, apply the emitted map and store directly in their final destination. It must preserve initialized extent, capacity/account ownership, LF/CRLF geometry, deferred missing-key failure order and the original finite admissions. It must retain arbitrary-input fallbacks and every complete table update.

## Long tasks

| Width | Candidate counting CPU | Parent counting CPU | Rust counting CPU | Candidate / Rust | Candidate body finish after main |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 0.413203 s | 0.399340 s | 0.385515 s | 1.072× | 0.589343 s |
| 18 | 0.404519 s | 0.398564 s | 0.409042 s | 0.989× | 0.581619 s |

Both long tasks remain relevant. All eight nonentry generated functions are byte-identical to the ordinary parent, including these counting loops. CPU/core residence and scheduling differ, so the diagnostic task times are not evidence of changed counting code or a substitute for complete-process timings. [Analysis](analysis-v2.json) retains all seven widths, every setup/count/publication/storage-retirement interval, per-thread instructions/cycles and performance/efficiency-core residence.

## Provenance and parser correction

The diagnostic source is [`f5391eacf5`](https://github.com/mech-lang/mech/commit/f5391eacf5f4924bedf1312a3c099fb0079447ef), branch `codex/native-private-join-phase-worker-probe`. The candidate guest object is identical to the production object. The phase and worker probe files are byte-identical to the parent's; additional calls cover the actual fused path. Only the copied launcher's source pin and its build script's own pin change. All original object/resource checks remain; **zero checks are removed**.

The first candidate prefix process succeeded with exact output, work counts and complete worker traces. Its old parser rejected missing unfused map begin/end markers. The immutable `capture-v1` receipt and original parser/controller remain. Version2 validates the fused representation strictly: one admission, paired per-chunk mapping/copy counts, one extra final copy preparation, two finish intervals and the actual chronological markers. It retains the original strict ordinary-path checks. [Parser qualification](parser-qualification-v2.json) checks both actual representations and rejects wrong modes and unpaired counts.

The successful candidate prefix is reused; it is not rerun to repair analysis. Its new interpretation is stored separately as `phases-v2.json`. The remaining prefix qualifications and all eighteen full processes use the same unchanged diagnostic executables in `capture-v2`.

[Verification](verification-v2.json) checks **22 terminal native receipts**, **126 worker intervals**, all **874,999,961 original updates** and **854,497 credited original batches** per full Mech process, all fused bytes, exact outputs, source stability, input/policy/data/executable pins, inherited locking, complete reaping/group closure, and no signals or cleanup errors. Every native process succeeds. Canonical published benchmark observations remain unchanged.
