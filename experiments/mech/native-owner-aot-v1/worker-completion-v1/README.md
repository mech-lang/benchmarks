# Complete task-boundary and per-width diagnostics

This study identifies the critical source widths and separates input preparation, worker setup, table counting, publication and storage retirement. It uses separate instrumented hosts. It supplies no primary timing samples and does not replace the qualified complete-process measurements.

## Method

All six permutations of aligned-probe Mech, UTF-8-fragment-facts Mech and protected-source Rust were run serially: six observations per subject, eighteen total. Every process ran under the common benchmark lock with the unchanged full input. Both Mech hosts preserved all seven maps, seven workers and 874,999,961 original table updates. Every output matched the reference hash. No process was excluded.

The probes read per-thread CPU, instructions, cycles and Performance/Efficiency residency counters at actual task boundaries. They do not configure counters, CPU priority, affinity, power or scheduling. The local availability pilot verified two core levels and the 125/3 ns Mach timebase. Counter records are buffered and printed after worker joins. There is no live thread polling.

The aligned host is based on compiler `8dfe57af5b116244ee8d10e1133bec95c02a4425` with instrumentation commit `f160e819766a77159def337b90867a9b6f49ac14`; the fragment-facts host is based on `76d17b03f7536132369b7d221f18727a1a045d03` with the identical probes in `349bc914a2cde19bb770e49e3390fb32f0c3e501`. Both reuse their unchanged generated guest object. The Rust source differs from the protected program only by the retained instrumentation diff. Instrumentation changes host code layout, so none of these hosts is claimed to match the primary binary text.

## Results

The previously suspected tail is confirmed: source widths 12 and 18 finish last. The thread-spawn interval itself is about 75 microseconds for aligned Mech. The delayed worker appearance chiefly precedes spawning. These observations do not establish a causal speedup for the fragment-facts candidate.

| Source width | Aligned count CPU | Rust count CPU | Aligned / Rust | Aligned task finish after main | Rust task finish after main |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.197272 s | 0.299609 s | 0.658× | 0.407128 s | 0.433663 s |
| 2 | 0.180548 s | 0.337159 s | 0.535× | 0.392190 s | 0.467589 s |
| 3 | 0.182478 s | 0.313618 s | 0.582× | 0.384400 s | 0.445410 s |
| 4 | 0.177905 s | 0.299669 s | 0.594× | 0.380089 s | 0.432894 s |
| 6 | 0.194856 s | 0.255741 s | 0.762× | 0.403295 s | 0.390532 s |
| 12 | 0.426245 s | 0.392227 s | 1.087× | 0.645463 s | 0.525581 s |
| 18 | 0.421774 s | 0.400414 s | 1.053× | 0.648586 s | 0.535046 s |

Values are medians of six diagnostic observations. Counting CPU is a CPU duration; task completion is a wall-clock offset. Rust returns a map from each counting job and formats/retires maps in main; Mech workers additionally complete source result publication. Compare counting with counting rather than treating total worker bodies as identical. Task completion is recorded before the standard library thread wrapper exits.

| Main-thread phase | Aligned Mech CPU | Fragment-facts Mech CPU | Rust CPU |
|---|---:|---:|---:|
| Before capture | 0.007332 s | 0.007403 s | Included in input |
| Capture / Rust input preparation | 0.150878 s | 0.131736 s | 0.133177 s |
| After input, before spawn | 0.045360 s | 0.045414 s | 0.000030 s |
| Spawn calls | 0.000075 s | 0.000072 s | 0.000069 s |

Mech capture and Rust input preparation have different boundaries: Mech performs selected joining and source normalization after capture. The roughly 45 ms post-capture interval still needs finer phase probes before assigning its time between joining, normalization and other generated work. The fragment-facts candidate reduces observed capture CPU here but has slower counting observations; its previous primary campaigns did not establish a reliable complete-process gain.

The full per-width setup, preparation, counting, publication, generated post-work and retirement counters, including core-kind CPU, are in [analysis.json](analysis.json). These are sampled experimental runs; differing core residency is observed rather than assigned by this study.

## Qualification and retained failure

Each diagnostic host first passed the retained prefix output and all seven source-width traces. The original aligned build failed with Cargo status 101 because adding the copied launcher probe left its source-integrity pin stale. No subject was launched by that failed build. The corrected version updates only the diagnostic launcher pin and build-script self-pin; it removes no checks and leaves guest objects, bytecode and resources pinned. The failed receipt is retained.

All process receipts, birth identities, termination, cleanup, binaries, source states, input, policies, trace parsing, native update counts and canonical dataset pins are audited by [verify.py](verify.py). [verification.json](verification.json) records the result.

## Follow-up

Remove the borrowed row directory using the existing compact offsets, independently test selected-join/source-map fusion after input acquisition, then investigate finite local worker credit and two-iteration pipelining on the confirmed long widths. Preserve the independent candidates and their interaction tests. Resolve the three retained-node, lookup-error-origin and simultaneous worker-byte-admission review findings before promotion.

Read-only counter API: [Apple XNU recount documentation](https://github.com/apple-oss-distributions/xnu/blob/main/doc/observability/recount.md).
