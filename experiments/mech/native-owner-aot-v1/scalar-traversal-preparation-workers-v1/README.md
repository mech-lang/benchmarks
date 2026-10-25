# Exact traversal-counter preparation and per-width diagnostics

This is a fresh diagnostic of production candidate [`f1b9e17f15`](https://github.com/mech-lang/mech/commit/f1b9e17f15f6b0b17ccc7845389c80f7902158c9), qualified fragment-fact/credit parent `bdb3c511c`, and the protected upstream Rust #7 implementation. Instrumented executables are separate from [primary timed binaries](../scalar-traversal-count-v1/README.md). No observation here is a primary timing sample or establishes an elapsed speedup.

The candidate-specific result does not show a useful scanner improvement. Its nested scalar scan is **0.073775 s**, versus **0.073956 s** for the parent. The post-EOF serial interval remains about **0.040 s**. The counter candidate is not promoted; the next larger target is removal of join/map buffer passes and intermediate canonical String construction.

## Main-thread boundaries

Six balanced sequential runs per subject use the original full input, unchanged finite limits, seven complete maps and seven internal workers.

| Nonoverlapping interval, median CPU | Candidate | Qualified parent | Rust | Candidate / Rust |
| --- | ---: | ---: | ---: | ---: |
| Before capture | 0.007534 s | 0.007552 s | Not separately reported | — |
| Input, including scanner | 0.120047 s | 0.119203 s | 0.134068 s | 0.895× |
| EOF to spawn calls | 0.040398 s | 0.040145 s | 0.000032 s | 1274.9× |
| Actual spawn calls | 0.000072 s | 0.000071 s | 0.000076 s | 0.954× |

The capture boundaries differ in the separately reported pre-capture setup, so the input interval alone is not the complete preparation comparison. Width-12 worker start after main is **0.168085 s / 1.253× Rust**, versus **0.167118 s / 1.246×** for the parent and **0.134169 s** for Rust. Thread creation remains too short to explain the preparation gap.

Nested source phases below overlap the main intervals and each other; do not add them. Rust does not expose corresponding nested operations.

| Nested CPU span | Candidate | Qualified parent |
| --- | ---: | ---: |
| Borrow rows | 0.000991 s | 0.000999 s |
| Scalar source scan | 0.073775 s | 0.073956 s |
| Selected joining | 0.020919 s | 0.020642 s |
| Copy inside selected joining | 0.020906 s | 0.020631 s |
| Map preparation | 0.001903 s | 0.001899 s |
| Emitted map kernel | 0.013032 s | 0.013021 s |
| Map finish | 0.002383 s | 0.002369 s |

## Long tasks

| Counting width | Candidate CPU | Parent CPU | Rust CPU | Candidate / Rust | Candidate body finish after main |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 0.407613 s | 0.411909 s | 0.386444 s | 1.055× | 0.585388 s |
| 18 | 0.399255 s | 0.406676 s | 0.406677 s | 0.982× | 0.577123 s |

All seven widths and all setup/count/publication/storage-retirement intervals are retained in [analysis.json](analysis.json), including per-thread instructions, cycles and performance/efficiency-core residence. CPU spans and body-finish boundaries are not complete-process elapsed times. The counting function bytes are unchanged, and per-core residence differs, so these spans do not establish better generated loop code. Both long tasks remain relevant to completion.

## Provenance and verification

The separate probe branch is [`b5a3959d5c`](https://github.com/mech-lang/mech/commit/b5a3959d5c972da89afcdec231eea102a8ea75a6), `codex/native-scalar-traversal-phase-worker-probe`. The phase and worker probe files are byte-identical to the prior qualified-parent diagnostic. The candidate guest object is identical to its production object; the parent guest object is identical to its production object. The candidate scalar entry differs from the parent while all eight other functions remain identical, as qualified in the primary study.

Only the copied diagnostic launcher's source pin and its build script's own pin change. All canonical object/resource/source checks remain; **zero checks are removed**. No source program, bytecode, complete map, update, finite allowance, seven-worker cap, input or OS setting changes.

[Verification](verification.json) qualifies **22 terminal native receipts**: one diagnostic build, three separate prefix qualifications and eighteen full diagnostic processes. It verifies all **126 worker intervals**, all **874,999,961 updates** and **854,497 original credited batches** per full Mech process, exact outputs, source stability, account/guest pins, inherited locking, reaping and process-group closure. Every native process succeeds without a signal or cleanup error. Canonical published benchmark observations remain unchanged.
