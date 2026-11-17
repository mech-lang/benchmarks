# Mech benchmark campaign

Started: 2026-11-17T02:23:01.284290+00:00

Timings are informational. Resident turns include captured-input submission, managed execution and publication. Source-to-artifact compilation, activation, observation and teardown are separate diagnostics. These observations do not replace the historical fresh-process cross-language chart.

| Case | Backend | Worker | Outcome | Turn median | Compile median | Artifact | Managed retained |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| scalar-changed | source | candidate | ok | 0.1775 µs | 1.75742 ms | 2141 B | 352 B |
| scalar-changed | source | baseline | ok | 0.18014 µs | 1.84713 ms | 2141 B | 352 B |
| scalar-changed | bytecode | candidate | ok | 0.178473 µs | 1.72167 ms | 2141 B | 352 B |
| scalar-changed | bytecode | baseline | ok | 0.180137 µs | 1.76183 ms | 2141 B | 352 B |
| scalar-unchanged | source | candidate | ok | 0.133057 µs | 1.68879 ms | 2141 B | 352 B |
| scalar-unchanged | source | baseline | ok | 0.130557 µs | 1.77146 ms | 2141 B | 352 B |
| scalar-unchanged | bytecode | candidate | ok | 0.13611 µs | 1.687 ms | 2141 B | 352 B |
| scalar-unchanged | bytecode | baseline | ok | 0.13264 µs | 1.72542 ms | 2141 B | 352 B |
| numerical-pipeline | source | candidate | ok | 0.34625 µs | 2.15446 ms | 3414 B | 448 B |
| numerical-pipeline | source | baseline | ok | 0.34389 µs | 2.24375 ms | 3414 B | 448 B |
| numerical-pipeline | bytecode | candidate | ok | 0.345693 µs | 2.13671 ms | 3414 B | 448 B |
| numerical-pipeline | bytecode | baseline | ok | 0.349307 µs | 2.22913 ms | 3414 B | 448 B |
| matrix-product | source | candidate | ok | 9.31944 µs | 4.83204 ms | 5507 B | 3464 B |
| matrix-product | source | baseline | ok | 9.39194 µs | 5.13867 ms | 5507 B | 3464 B |
| matrix-product | bytecode | candidate | ok | 9.28625 µs | 4.83367 ms | 5507 B | 3464 B |
| matrix-product | bytecode | baseline | ok | 9.37653 µs | 5.1765 ms | 5507 B | 3464 B |
| filter-cardinality | source | candidate | ok | 125.694 µs | 2.8665 ms | 2410 B | 5223 B |
| filter-cardinality | source | baseline | ok | 127.211 µs | 3.002 ms | 2410 B | 5223 B |
| filter-cardinality | bytecode | candidate | ok | 126.328 µs | 2.88225 ms | 2410 B | 5223 B |
| filter-cardinality | bytecode | baseline | ok | 126.274 µs | 2.98804 ms | 2410 B | 5223 B |
| map-lookup | source | candidate | ok | 11.526 µs | 2.92592 ms | 3487 B | 3485 B |
| map-lookup | source | baseline | ok | 11.5113 µs | 3.08688 ms | 3487 B | 3485 B |
| map-lookup | bytecode | candidate | ok | 11.5067 µs | 2.9325 ms | 3487 B | 3485 B |
| map-lookup | bytecode | baseline | ok | 11.4223 µs | 3.13837 ms | 3487 B | 3485 B |
| branch-selection | source | candidate | ok | 2.40667 µs | 2.30717 ms | 2349 B | 648 B |
| branch-selection | source | baseline | ok | 2.45 µs | 2.42479 ms | 2349 B | 648 B |
| branch-selection | bytecode | candidate | ok | 2.42146 µs | 2.36221 ms | 2349 B | 648 B |
| branch-selection | bytecode | baseline | ok | 2.44438 µs | 2.46525 ms | 2349 B | 648 B |
| function-call | source | candidate | ok | 2.95403 µs | 1.82708 ms | 2117 B | 616 B |
| function-call | source | baseline | ok | 2.99472 µs | 1.88279 ms | 2117 B | 616 B |
| function-call | bytecode | candidate | ok | 2.93278 µs | 1.82438 ms | 2117 B | 616 B |
| function-call | bytecode | baseline | ok | 2.9818 µs | 1.88683 ms | 2117 B | 616 B |
| tail-recursion | source | candidate | ok | 397.05 µs | 2.57408 ms | 3330 B | 3648 B |
| tail-recursion | source | baseline | ok | 395.553 µs | 2.662 ms | 3330 B | 3648 B |
| tail-recursion | bytecode | candidate | ok | 397.116 µs | 2.57254 ms | 3330 B | 3648 B |
| tail-recursion | bytecode | baseline | ok | 395.195 µs | 2.71567 ms | 3330 B | 3648 B |
| state-evolution | source | candidate | ok | 0.288193 µs | 2.09483 ms | 2934 B | 896 B |
| state-evolution | source | baseline | ok | 0.282777 µs | 2.17683 ms | 2934 B | 896 B |
| state-evolution | bytecode | candidate | ok | 0.29264 µs | 2.13029 ms | 2934 B | 896 B |
| state-evolution | bytecode | baseline | ok | 0.283473 µs | 2.2045 ms | 2934 B | 896 B |
| set-union | source | candidate | ok | 27.7158 µs | 2.12283 ms | 3055 B | 10300 B |
| set-union | source | baseline | ok | 27.5431 µs | 2.21846 ms | 3055 B | 10300 B |
| set-union | bytecode | candidate | ok | 27.7732 µs | 2.1375 ms | 3055 B | 10300 B |
| set-union | bytecode | baseline | ok | 27.7169 µs | 2.20692 ms | 3055 B | 10300 B |
| record-projection | source | candidate | ok | 29.3397 µs | 2.31354 ms | 4359 B | 6848 B |
| record-projection | source | baseline | ok | 29.3175 µs | 2.42558 ms | 4359 B | 6848 B |
| record-projection | bytecode | candidate | ok | 29.3863 µs | 2.37625 ms | 4359 B | 6848 B |
| record-projection | bytecode | baseline | ok | 29.3203 µs | 2.42029 ms | 4359 B | 6848 B |
| numerical-application | source | candidate | ok | 0.54028 µs | 2.90971 ms | 4950 B | 2992 B |
| numerical-application | source | baseline | ok | 0.564723 µs | 3.1165 ms | 4950 B | 2992 B |
| numerical-application | bytecode | candidate | ok | 0.54861 µs | 2.91579 ms | 4950 B | 2992 B |
| numerical-application | bytecode | baseline | ok | 0.56403 µs | 3.14792 ms | 4950 B | 2992 B |
| dependency-fanout | source | candidate | ok | 5.11222 µs | 24.8044 ms | 45725 B | 3840 B |
| dependency-fanout | source | baseline | ok | 5.07195 µs | 26.698 ms | 45725 B | 3840 B |
| dependency-fanout | bytecode | candidate | ok | 5.11986 µs | 24.7808 ms | 45725 B | 3840 B |
| dependency-fanout | bytecode | baseline | ok | 5.08417 µs | 26.8896 ms | 45725 B | 3840 B |
| touched-equal | source | candidate | ok | 0.136875 µs | 1.71958 ms | 2141 B | 352 B |
| touched-equal | source | baseline | ok | 0.13396 µs | 1.763 ms | 2141 B | 352 B |
| touched-equal | bytecode | candidate | ok | 0.136875 µs | 1.728 ms | 2141 B | 352 B |
| touched-equal | bytecode | baseline | ok | 0.13271 µs | 1.78763 ms | 2141 B | 352 B |
| retained-snapshots | source | candidate | ok | 126.368 µs | 2.90537 ms | 2410 B | 414271 B |
| retained-snapshots | source | baseline | ok | 126.921 µs | 3.05817 ms | 2410 B | 414271 B |
| retained-snapshots | bytecode | candidate | ok | 125.738 µs | 2.94242 ms | 2410 B | 414271 B |
| retained-snapshots | bytecode | baseline | ok | 126.589 µs | 3.094 ms | 2410 B | 414271 B |
| abort-recovery | source | candidate | ok | 0.64111 µs | 2.13771 ms | 2934 B | 896 B |
| abort-recovery | source | baseline | ok | 0.631943 µs | 2.22471 ms | 2934 B | 896 B |
| abort-recovery | bytecode | candidate | ok | 0.66264 µs | 2.14933 ms | 2934 B | 896 B |
| abort-recovery | bytecode | baseline | ok | 0.62986 µs | 2.18446 ms | 2934 B | 896 B |
| compile-chain | source | candidate | ok | 14.0583 µs | 81.8765 ms | 117469 B | 8496 B |
| compile-chain | source | baseline | ok | 14.0839 µs | 89.9566 ms | 117469 B | 8496 B |
| compile-chain | bytecode | candidate | ok | 14.0193 µs | 81.9453 ms | 117469 B | 8496 B |
| compile-chain | bytecode | baseline | ok | 14.0283 µs | 89.9545 ms | 117469 B | 8496 B |

Managed counters report admitted backing, separately from whole-worker peak RSS. The worker high-water mark includes compilation and preparation, and is not an execution-interval RSS measurement. Allocation counters include the counting-allocator overhead. Object/linked sections are absent until a native recipe is qualified.

Exact source, contracts, worker hashes, toolchains, comparison order, verification outputs, requests and raw observations accompany this report.
