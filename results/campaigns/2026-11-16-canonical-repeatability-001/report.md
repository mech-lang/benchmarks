# Mech benchmark campaign

Started: 2026-11-17T02:29:51.247077+00:00

Timings are informational. Resident turns include captured-input submission, managed execution and publication. Source-to-artifact compilation, activation, observation and teardown are separate diagnostics. These observations do not replace the historical fresh-process cross-language chart.

| Case | Backend | Worker | Outcome | Turn median | Compile median | Artifact | Managed retained |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| scalar-changed | source | candidate | ok | 0.177917 µs | 1.72729 ms | 2141 B | 352 B |
| scalar-changed | bytecode | candidate | ok | 0.18 µs | 1.70058 ms | 2141 B | 352 B |
| scalar-unchanged | source | candidate | ok | 0.13361 µs | 1.659 ms | 2141 B | 352 B |
| scalar-unchanged | bytecode | candidate | ok | 0.132223 µs | 1.68908 ms | 2141 B | 352 B |
| numerical-pipeline | source | candidate | ok | 0.345277 µs | 2.11983 ms | 3414 B | 448 B |
| numerical-pipeline | bytecode | candidate | ok | 0.340697 µs | 2.12133 ms | 3414 B | 448 B |
| matrix-product | source | candidate | ok | 9.35889 µs | 4.84413 ms | 5507 B | 3464 B |
| matrix-product | bytecode | candidate | ok | 9.24208 µs | 4.8225 ms | 5507 B | 3464 B |
| filter-cardinality | source | candidate | ok | 125.552 µs | 2.88025 ms | 2410 B | 5223 B |
| filter-cardinality | bytecode | candidate | ok | 126.237 µs | 2.85583 ms | 2410 B | 5223 B |
| map-lookup | source | candidate | ok | 11.2308 µs | 2.91229 ms | 3487 B | 3485 B |
| map-lookup | bytecode | candidate | ok | 11.0796 µs | 2.91371 ms | 3487 B | 3485 B |
| branch-selection | source | candidate | ok | 2.40313 µs | 2.30146 ms | 2349 B | 648 B |
| branch-selection | bytecode | candidate | ok | 2.42292 µs | 2.29212 ms | 2349 B | 648 B |
| function-call | source | candidate | ok | 2.95292 µs | 1.8215 ms | 2117 B | 616 B |
| function-call | bytecode | candidate | ok | 2.93167 µs | 1.80758 ms | 2117 B | 616 B |
| tail-recursion | source | candidate | ok | 395.599 µs | 2.52983 ms | 3330 B | 3648 B |
| tail-recursion | bytecode | candidate | ok | 397.228 µs | 2.51771 ms | 3330 B | 3648 B |
| state-evolution | source | candidate | ok | 0.29139 µs | 2.06792 ms | 2934 B | 896 B |
| state-evolution | bytecode | candidate | ok | 0.28847 µs | 2.06887 ms | 2934 B | 896 B |
| set-union | source | candidate | ok | 27.6432 µs | 2.11071 ms | 3055 B | 10300 B |
| set-union | bytecode | candidate | ok | 27.5085 µs | 2.10275 ms | 3055 B | 10300 B |
| record-projection | source | candidate | ok | 29.1058 µs | 2.33596 ms | 4359 B | 6848 B |
| record-projection | bytecode | candidate | ok | 29.1314 µs | 2.33862 ms | 4359 B | 6848 B |
| numerical-application | source | candidate | ok | 0.550833 µs | 2.90612 ms | 4950 B | 2992 B |
| numerical-application | bytecode | candidate | ok | 0.5425 µs | 2.865 ms | 4950 B | 2992 B |
| dependency-fanout | source | candidate | ok | 5.14639 µs | 24.7055 ms | 45725 B | 3840 B |
| dependency-fanout | bytecode | candidate | ok | 5.10875 µs | 24.7145 ms | 45725 B | 3840 B |
| touched-equal | source | candidate | ok | 0.136875 µs | 1.68712 ms | 2141 B | 352 B |
| touched-equal | bytecode | candidate | ok | 0.1375 µs | 1.69042 ms | 2141 B | 352 B |
| retained-snapshots | source | candidate | ok | 126.328 µs | 2.85938 ms | 2410 B | 414271 B |
| retained-snapshots | bytecode | candidate | ok | 125.801 µs | 2.8695 ms | 2410 B | 414271 B |
| abort-recovery | source | candidate | ok | 0.643613 µs | 2.11763 ms | 2934 B | 896 B |
| abort-recovery | bytecode | candidate | ok | 0.663473 µs | 2.11687 ms | 2934 B | 896 B |
| compile-chain | source | candidate | ok | 14.1139 µs | 81.7535 ms | 117469 B | 8496 B |
| compile-chain | bytecode | candidate | ok | 13.9639 µs | 81.7965 ms | 117469 B | 8496 B |

Managed counters report admitted backing, separately from whole-worker peak RSS. The worker high-water mark includes compilation and preparation, and is not an execution-interval RSS measurement. Allocation counters include the counting-allocator overhead. Object/linked sections are absent until a native recipe is qualified.

Exact source, contracts, worker hashes, toolchains, comparison order, verification outputs, requests and raw observations accompany this report.
