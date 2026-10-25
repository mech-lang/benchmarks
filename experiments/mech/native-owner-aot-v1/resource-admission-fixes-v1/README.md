# Fixed ownership and constructor admission

This revision corrects three native-runtime findings before further performance work: private window-table nodes were unclaimed, packed lookup misses lost the maintained source error, and parallel selection checked worker nodes without its combined byte-constructor envelope. It is a corrected baseline, with no speedup claim.

Source: `ce06867648d1de888c7b4a3046be70cbfdda1a9d` on `codex/native-resource-admission-fixes`, based on the qualified aligned-probe revision `8dfe57af5b116244ee8d10e1133bec95c02a4425`. The PR 911 review threads have not been marked resolved; these fixes remain on the separately qualified branch pending integration.

## Changes

- `WindowHashes` retains metadata/table and entry node claims for its full lifetime, including transient old/new entry coexistence on rehash. Both the component limit and shared account reject denied growth before mutation. Pending claims are released on failure; successfully spent work remains spent.
- Packed missing-key callbacks return the maintained `InvalidInput` library error at the actual source lookup origin. The regression checks original and decoded artifacts, restored descriptors and the malformed-success defensive continuation.
- Parallel dispatch jointly tests fixed constructor bytes and nodes before spawning. The byte envelope includes the core initialization-coverage metadata for all typed arenas and conservative existing constant-import bounds. The byte geometry calls the same core helper as the maintained initialization model. A derived descriptor cache totals constant bounds at prepare/decode time; repeated dispatch does not scan the constants table. The cache is absent from serialized images and overflow is rejected.

The preflight is a fixed-constructor feasibility check. Later dynamic map growth, builders, output publication and other source operations retain their normal finite admission. It is not a promise that every possible parallel body peak fits whenever serial execution fits.

The Mech source, bytecode, resources, descriptor image and raw generated guest object are byte-for-byte unchanged. The raw object remains `1b41df9502251b02783a4e41e86de17fe4de722d6c579400c3d4c00d031ba32c`. IR80, ABI28, work policy67 and existing operation prices remain. No caps, full-map work, source updates, worker count or OS scheduling/power settings were discounted.

## Complete-process timings

Each session contains all six three-subject permutations: six observations per subject, run serially with secured startup through complete process exit. Input contains 125,000,000 selected bases. Every Mech process retains seven complete maps and 874,999,961 source table updates. All outputs and update counts passed. There are no excluded full-input warmups or outliers; sessions are kept separate.

| Session | Corrected Mech | × Rust | Previous Mech | × Rust | Rust |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.6817 s | 1.237× | 0.6667 s | 1.210× | 0.5511 s |
| 2 | 0.6826 s | 1.237× | 0.6743 s | 1.222× | 0.5519 s |

Corrected medians are slower in both sessions. The paired change is +1.63% with a 95% bootstrap interval of [+1.56%, +4.06%] in session 1, and +0.92% [−0.28%, +2.98%] in session 2. These are correctness changes, not an elapsed-time improvement. The corrected executable is the baseline for the next preparation experiment. Rust parity remains incomplete.

| Session | Corrected peak RSS | Previous peak RSS | Rust peak RSS |
|---:|---:|---:|---:|
| 1 | 162.87 MB | 161.87 MB | 140.45 MB |
| 2 | 162.70 MB | 162.08 MB | 140.75 MB |

The corrected executable file is 5,468,128 bytes, versus 5,468,112 bytes previously (+16 bytes). File size is not mapped memory. No new exact-text profile is claimed for this executable; the separate [per-width diagnostic hosts](../worker-completion-v1/README.md) belong to their pinned earlier revisions.

The separate one-million-base prefix uses one excluded warmup and three measured complete processes per subject. Corrected Mech is 0.0875 s / 4.223× Rust; previous Mech 0.0921 s / 4.443×; Rust 0.0207 s / 1.000×. These observations are not pooled with full-input timings.

## Qualification and retained unsuccessful attempts

The final immutable source passes 392 native checks and the catalog check; three existing manual diagnostics remain ignored. New coverage includes exact and one-short global/component node ceilings, entry and rehash coexistence, failed-claim cleanup, exact typed-arena byte accounting, original/decoded source fallback and descriptor-image reconstruction/overflow rejection.

The retained failure history explains two corrections to the validation approach:

- The initial transport-only byte estimate omitted maintained arena initialization metadata and constant imports. The full receipt reports 390 passing checks and one failing new byte fallback fixture.
- The two-sibling fixture first declined the seven-task group, then retried a smaller five-task region. The retained test-only phase diagnostic shows that the smaller region passed fixed preflight but later dynamic body allocations exhausted memory and competed with a still-constructing worker. The final constructor regression uses one seven-task comprehension, isolating the fixed constructor floor from a smaller subgroup’s separate dynamic peak. The implementation does not waive any dynamic admission.
- A later compile stopped because the cached total was declared before its input bounds. A new committed revision fixes the declaration order; the failed receipt is preserved.

The complete native suite was rerun on the final revision after those changes. [verify.py](verify.py) audits 57 terminal process receipts, four preserved failures, unchanged source snapshots, all 36 full-input primary observations, nine measured prefix observations, all output/native update hashes and artifact pins. [verification.json](verification.json) contains the exact result.

Next: remove the temporary per-line row directory through borrowed compact offsets, retaining the Unicode and larger-window fallback, then separately test selected-join/source-map fusion and the confirmed long ordinary-hash loops.
