# Cold scalar source-origin stores

**Decision: retain the qualified finite-worker-credit parent. This candidate establishes no complete-process speedup.**

Candidate [`47da29a4c`](https://github.com/mech-lang/mech/tree/47da29a4c63b5658cd96180a1bd0e39171a24389) is independent of the unpromoted register experiment. Parent: `7a715c12a`. See [design.md](design.md).

For existing closed scalar proofs, 122 body sites now materialize their original source location on the actual exceptional edge, before unchanged abort/cleanup. Ordinary callbacks and loop headers retain eager writes. Header writes are required for successful input-checkpoint validation. Source actions, guards, fuel storage, original two-dimensional prices and continuations are unchanged. IR84 identifies the guest change; ABI29 and policy68 remain.

## Complete-process timings

Two separate sessions each contain all six balanced three-subject orders, six complete processes per subject. They include secured startup through exit on the full 125-million-selected-base input. No full-input warmups or outliers are excluded.

| Session | Candidate | Candidate / Rust | Parent | Parent / Rust | Rust | Paired change (95% interval) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.6297 s | 1.139× | 0.6296 s | 1.139× | 0.5529 s | +0.35% [-0.76%, +1.33%] |
| 2 | 0.6294 s | 1.135× | 0.6260 s | 1.129× | 0.5544 s | +0.30% [-0.71%, +2.12%] |

Both paired intervals include zero. The measured candidate remains unpromoted.

The separate prefix check uses one excluded warmup and three measured processes per subject. It does not substitute for full-input results.

| Prefix subject | Seconds | × Rust |
|---|---:|---:|
| Candidate | 0.0827 | 6.303× |
| Parent | 0.0857 | 6.532× |
| Rust | 0.0131 | 1.000× |

## Code, work, memory and diagnostics

[Function-byte inspection](code-inspection.json) verifies that all eight nonentry functions, including all counting functions, remain byte-for-byte identical. The main entry including alignment grows from 43,376 to 44,352 bytes. Source plan, visits, aggregates, borrowed layout and original finite fuel layout are identical.

Total admitted code is 113,332 bytes versus 112,356; admitted stack is 1,216 versus 1,216 bytes. Executable file sizes are 5,501,200 and 5,501,200 bytes. Median peak RSS is 163.08 / 162.86 MB for the candidate, 162.49 / 162.77 MB for the parent and 141.10 / 140.17 MB for Rust (decimal MB). No memory saving is established.

All full runs retain seven complete default-growing hash maps, 874,999,961 original updates, five lookup caches and the seven-worker cap. Every candidate debits exactly 854,497 original funded batches; [independent selection verification](selection-verification.json) reconciles all twelve reports. The Mech source, bytecode and resource image are unchanged. No input recognition, dense-counter substitution, query-only work or OS setting change is introduced.

Separate hardware-counter medians are diagnostic executions:

| Subject | Instructions | Cycles | User CPU | System CPU |
|---|---:|---:|---:|---:|
| Candidate | 24.674 B | 6.013 B | 1.70 s | 0.03 s |
| Parent | 24.979 B | 5.984 B | 1.69 s | 0.03 s |
| Rust | 33.139 B | 8.066 B | 2.38 s | 0.03 s |

About 306 million fewer instructions do not produce fewer measured cycles or a primary elapsed improvement. This experiment therefore does not establish that eager source-origin stores explain the remaining critical path.

[Fresh exact-code profiles](analysis.json) contain three Mech and three Rust executions. The entire machine-code section equals the timed candidate. Mech worker leaf observations are 85.12% generated counting loops, 7.31% storage helpers, 3.62% active work accounting, 1.68% generated bridges and 0.94% budget waits. Main-thread observations still include the generated entry, selected copying and normalization. Sampling perturbs execution and does not provide a phase-duration decomposition or recoverable elapsed percentages. The earlier parent phase clocks must not be assigned to this candidate.

## Verification

All 395 native tests, two focused differential tests and the catalog check pass; three existing manual tests remain ignored. Original/decoded bytecode comparisons preserve repeated prefix/resume traces, cleared homes, outputs, source error origins and original work under finite compute/comparison caps. A separate state machine checks source arithmetic overflow. All owned memory retires.

[Verification](verification.json) audits 80 terminal native receipts, both full sessions, prefix output, exact-code profiles, counters and immutable source/data pins. Focused attempt v1 correctly detected the normal checkpoint origin requirement. Its failed receipt remains; v2 preserves header writes and passes. No validation rule was removed.

Finite local worker credit remains the qualified performance checkpoint. This branch is retained for interaction experiments; Rust parity remains incomplete.
