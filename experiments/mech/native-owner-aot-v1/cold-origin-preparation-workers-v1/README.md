# Cold-origin preparation and worker-width diagnostic

This diagnostic surrounds the exact guest from the unpromoted cold-origin candidate `47da29a4c` with separately instrumented host support at `1a834927c`. It supplies no primary benchmark samples. The source, guest object, descriptor, bytecode, resources, original full-map work, finite limits and seven-worker cap remain pinned. The protected Rust primary is unchanged; Rust boundary diagnostics use the previously pinned instrumented source copy.

## Main-thread preparation

Workers start near 0.188 s after Mech main, versus 0.130 s for Rust: about 58 ms later. The spawn calls themselves take about 71 microseconds in both. These perturbed in-process milestones do not replace complete-process primary timings.

| Mech phase | Median CPU seconds |
|---|---:|
| Borrow rows | 0.001032 |
| Original source scanner | 0.072638 |
| Selected join | 0.020552 |
| Copy within join | 0.020540 |
| Normalization preparation | 0.001898 |
| Normalization kernel | 0.013019 |
| Normalization finish | 0.002293 |

Spans are nested: copy is inside join, and scanner/borrowing occur during input acquisition. They must not be added indiscriminately. The scanner remains about 73 ms in this new cohort; a material scan reduction is not demonstrated.

| Main-thread span | Mech CPU | Rust CPU | Mech / Rust |
|---|---:|---:|---:|
| Input acquisition, including Mech scanning | 0.140429 s | 0.129777 s | 1.082× |
| After input, before spawn | 0.039973 s | 0.000028 s | 1406.657× |
| Spawn calls | 0.000071 s | 0.000071 s | 0.993× |

Input spans contain different source preparation steps: Rust performs byte encoding during input collection; Mech has subsequent joining and normalization. The table identifies boundaries rather than asserting equivalent isolated algorithms.

## Per-width counting

| Width | Mech count CPU | Rust count CPU | Mech / Rust |
|---|---:|---:|---:|
| 1 | 0.147448 s | 0.297018 s | 0.496× |
| 2 | 0.137163 s | 0.296225 s | 0.463× |
| 3 | 0.135599 s | 0.300745 s | 0.451× |
| 4 | 0.136742 s | 0.305420 s | 0.448× |
| 6 | 0.157273 s | 0.264276 s | 0.595× |
| 12 | 0.402402 s | 0.388553 s | 1.036× |
| 18 | 0.402253 s | 0.403254 s | 0.998× |

Widths 12 and 18 remain the final tasks. Counting CPU is within about 3.6% of Rust at width 12 and essentially equal at width 18; the five cached widths use substantially less CPU. This does not overcome the later Mech launch. Source-width labels are read from the actual tasks rather than inferred from thread IDs.

| Final tasks | Mech count complete after main | Rust count complete after main |
|---|---:|---:|
| Width 12 | 0.590153 s | 0.521271 s |
| Width 18 | 0.591813 s | 0.532590 s |

These boundaries end counting, not publication, main formatting or process shutdown. Mech publication and private storage retirement are retained separately in [analysis.json](analysis.json). Rust workers return maps for main-thread processing. Nested spans and per-core residence differences must not be interpreted as primary elapsed gains.

## Qualification

Two prefix qualifications and twelve balanced full diagnostic processes verify every output, seven complete maps, 874,999,961 original full-input updates, actual credited batches, finite secured policy and seven peak workers. All 84 worker intervals have monotonically validated clocks/counters. The existing probe sources are copied verbatim. Only the copied launcher and its build-script self pin change; no canonical pin check is removed.

[Verification](verification.json) audits all 15 native process receipts: zero exit status, reaped children, closed groups, no signals and no cleanup errors. Whole-host diagnostic machine code differs from primary code, which is explicitly outside the identity claim. The unchanged guest object is SHA-256 `0bddcd82101b7665b7ece7d3d16d28e759a4f0eee53b5feffa719eb51dce1b35`.

The current evidence favors optimizing the complete pure scalar scanner graph and its data movement, rather than treating isolated source-location or fuel-word reductions as established elapsed wins. Ordinary hash-loop pipelining remains a separate experiment. Rust parity is incomplete.
