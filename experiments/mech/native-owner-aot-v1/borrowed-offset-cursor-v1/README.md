# Borrowed compact-offset line windows

This candidate removes a temporary per-line pointer/length directory from the serial input path. It remains a separate experiment with a provisional elapsed-time benefit. The source workload is unchanged.

Source: `91f725adc16b1ba349d77cc898e6e24de4a79bf6` on `codex/native-borrowed-offset-cursor`, based on the corrected ownership/admission baseline `ce06867648d1de888c7b4a3046be70cbfdda1a9d`.

## Representation and bounds

For producer-proved ASCII windows spanning at most two physical chunks, the owning window keeps two inline chunk descriptors and lends the existing immutable bytes and compact u32 LF offsets. The generated scanner derives each row directly, including the exact one-CR-before-LF rule and a separate lone unterminated-line representation. It creates no per-line pointer table on this path. Larger physical windows and mixed-Unicode producers retain checked materialized rows. This is a general bounded line-window representation; it does not recognize FASTA, headers, the benchmark name or the input generator.

ABI29 uses one private integer discriminator bit for compact versus aligned ordinary row tables. Bounds are checked against the actual row count before accessing either representation. The original owner/producer/work identity and borrow lifetime remain mandatory. IR81 binds the new emitted row operations; work policy68 includes the larger inline owner layout while retaining the previous row/payload work and full row-capacity claims. Normalization, map algorithms, prices, limits, seven-worker cap and all source updates remain.

The Mech source, bytecode and resource image match the corrected parent exactly. The generated object changes because the row getter and ABI/work identities change. Every process retains all seven complete hash tables and the full original updates.

## Complete-process timings

Both sessions use all six three-subject permutations, six observations per subject, serial complete-process execution with secured startup and shutdown. Input has 125,000,000 selected bases; each Mech process performs 874,999,961 original table updates. No full-input warmups or outliers are excluded.

| Session | Compact offsets | × Rust | Corrected parent | × Rust | Rust |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.6713 s | 1.225× | 0.6883 s | 1.256× | 0.5479 s |
| 2 | 0.6713 s | 1.200× | 0.6855 s | 1.226× | 0.5593 s |

Median reductions are about 17 ms and 14 ms. The first paired change is −2.53% with a 95% bootstrap interval [−3.24%, −1.87%]; the repeat is −0.53% [−4.99%, +1.73%]. The repeat interval includes zero, so the candidate is retained without a reliable-win or Rust-parity claim. Its current purpose is to test the removed representation independently before combination with other factors.

| Session | Candidate peak RSS | Parent peak RSS | Rust peak RSS |
|---:|---:|---:|---:|
| 1 | 162.52 MB | 162.16 MB | 140.44 MB |
| 2 | 161.56 MB | 162.22 MB | 140.77 MB |

The executable file is 5,468,160 bytes (+32 versus the corrected parent). Peak RSS does not establish a repeatable memory reduction.

The separate one-million-base prefix excludes one warmup per subject and measures three complete processes per subject:

| Subject | Prefix median | × Rust |
|---|---:|---:|
| Compact offsets | 0.0861 s | 4.438× |
| Corrected parent | 0.0869 s | 4.479× |
| Rust | 0.0194 s | 1.000× |

Prefix results are not pooled with full input.

## Exact-code diagnostics

The symbol-preserving profile image matches every byte of the timed executable’s 4,308,344-byte machine-code text, SHA-256 `b4bdc371339cd9bf4669e5e089edb2f34ff05e61b1e9cc6e1c2421f2b510ec93`. Three fresh Mech and three Rust profiles were pre-armed before process launch; all sampled PIDs were owned direct children, and every output/update receipt passed. Profile durations include perturbation and are not primary timings. The [guest-code audit](code-audit/results.json) retains both emitted discriminator/LF-load fragments. It preserves source/native bounds qualification rather than treating an instruction pattern as a proof of elapsed savings.

Across observed Mech worker stack leaves, generated counting is 75.66%, active accounting 16.84%, accounting waits 0.86%, storage helpers 3.80%, and generated bridges 1.59%. The two most-observed workers per capture have 78.39% generated counting, 10.75% active accounting and 7.94% storage helpers. These are sampled locations with profiler overhead, not elapsed-time or CPU-time shares. Exact per-width identities were established independently in the [task-boundary study](../worker-completion-v1/README.md); observation count alone is not used as a new width identification.

The serial profile still observes generated source scanning, copying, source normalization, LF-offset construction and consuming selected joins. Main-thread leaves include 99 entry observations, 45 memmove, 32 source-map kernel, 22 LF-offset construction, 19 capture push and 16 `Chunk::line`. This motivates a finer phase diagnostic and a separate selected-join/source-map fusion candidate; the counts are not an additive wall-time decomposition.

Nine separate counter executions retain all observations. Candidate instructions are 25.258 billion versus the parent’s 25.530 billion; median cycles are 7.092 versus 7.020 billion, and user/system CPU are 2.02/0.04 s versus 2.01/0.04 s. Fewer total instructions do not establish a total-CPU or elapsed win.

The Rust diagnostic counter runs vary substantially:

| Counter round | Rust elapsed | Instructions | Cycles |
|---:|---:|---:|---:|
| 1 | 0.55 s | 33.131 B | 8.175 B |
| 2 | 2.03 s | 47.315 B | 18.458 B |
| 3 | 0.94 s | 34.791 B | 11.355 B |

The two slow Rust diagnostics are retained. The executable, source and output hashes are unchanged, but this study does not establish the cause of their additional work. Their three-run median is not substituted for the twelve primary Rust controls, whose session medians remain 0.5479 s and 0.5593 s. No speedup claim is derived from the slow diagnostic runs. Raw counters and process receipts are in [counters/results.json](counters/results.json).

## Qualification and retained checker stop

All 24 engine line-storage checks, 29 focused native prefix checks, 392 full native checks and the catalog check pass. The focused prefix set is repeated within the full native suite. Three existing manual diagnostics remain ignored. The new engine coverage exercises split boundaries, empty cells, CRLF, unterminated final lines, ordinary and compact representations, exact capacity limits, ownership and cumulative work.

The first standalone build succeeded, but the study-local packed-frame audit still listed ABI24–28 and stopped before any subject execution. The versioned second checker extends that unchanged packed-frame contract to ABI29, removes no masks/checks and reuses only the pinned successful build. It reuses no timing observations. Both the initial checker and its failure record remain. The first filesystem verifier omitted its root-helper import; [verify-v2.py](verify-v2.py) corrects the import without rerunning native processes.

[verification.json](verification.json) audits all 82 terminal native process receipts, complete outputs, original updates, source snapshots, primary and diagnostic binaries, source/bytecode/resources, profile text and the code audit. The canonical benchmark dataset is unchanged.

Next experiments remain separate: delimit borrowing/scanning/joining/normalization phases, fuse selected joining with the existing source map after input completion, prototype finite local worker credit, and inspect the confirmed long ordinary-hash loops for scoped alias facts and two-iteration pipelining. Combinations follow independent mechanism tests.
