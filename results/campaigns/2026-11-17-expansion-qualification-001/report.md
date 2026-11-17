# Mech benchmark campaign

Started: 2026-11-17T14:05:13.148685+00:00

Timings are informational. Resident turns include captured-input submission, managed execution and publication. Source-to-artifact compilation, activation, observation and teardown are separate diagnostics. These observations do not replace the historical fresh-process cross-language chart.

| Case | Backend | Worker | Outcome | Turn median | Compile median | Artifact | Managed retained |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| scalar-changed | source | candidate | ok | 0.28475 µs | 1.75275 ms | 2141 B | 352 B |
| scalar-changed | bytecode | candidate | ok | 0.28125 µs | 1.97812 ms | 2141 B | 352 B |
| scalar-unchanged | source | candidate | ok | 0.236083 µs | 1.68738 ms | 2141 B | 352 B |
| scalar-unchanged | bytecode | candidate | ok | 0.2465 µs | 1.69738 ms | 2141 B | 352 B |
| numerical-pipeline | source | candidate | ok | 0.461833 µs | 2.11617 ms | 3414 B | 448 B |
| numerical-pipeline | bytecode | candidate | ok | 0.461833 µs | 2.11508 ms | 3414 B | 448 B |
| matrix-product | source | candidate | ok | 9.20133 µs | 4.90629 ms | 5507 B | 3464 B |
| matrix-product | bytecode | candidate | ok | 9.26392 µs | 4.95692 ms | 5507 B | 3464 B |
| filter-cardinality | source | candidate | ok | 127.233 µs | 2.86854 ms | 2410 B | 5223 B |
| filter-cardinality | bytecode | candidate | ok | 126.671 µs | 2.97746 ms | 2410 B | 5223 B |
| map-lookup | source | candidate | ok | 12.2396 µs | 2.976 ms | 3487 B | 3485 B |
| map-lookup | bytecode | candidate | ok | 11.9375 µs | 2.97271 ms | 3487 B | 3485 B |
| branch-selection | source | candidate | ok | 2.85425 µs | 2.37908 ms | 2349 B | 648 B |
| branch-selection | bytecode | candidate | ok | 2.901 µs | 2.39233 ms | 2349 B | 648 B |
| function-call | source | candidate | ok | 3.29167 µs | 1.83467 ms | 2117 B | 616 B |
| function-call | bytecode | candidate | ok | 3.24308 µs | 1.89083 ms | 2117 B | 616 B |
| tail-recursion | source | candidate | ok | 418.681 µs | 2.59167 ms | 3330 B | 3648 B |
| tail-recursion | bytecode | candidate | ok | 417.233 µs | 2.54583 ms | 3330 B | 3648 B |
| state-evolution | source | candidate | ok | 0.423583 µs | 2.23933 ms | 2934 B | 896 B |
| state-evolution | bytecode | candidate | ok | 0.40625 µs | 2.13262 ms | 2934 B | 896 B |
| set-union | source | candidate | ok | 28.7257 µs | 2.26763 ms | 3055 B | 10300 B |
| set-union | bytecode | candidate | ok | 26.9271 µs | 2.19367 ms | 3055 B | 10300 B |
| record-projection | source | candidate | ok | 28.6875 µs | 2.35375 ms | 4359 B | 6848 B |
| record-projection | bytecode | candidate | ok | 30.7917 µs | 2.47754 ms | 4359 B | 6848 B |
| numerical-application | source | candidate | ok | 0.666667 µs | 2.92617 ms | 4950 B | 2992 B |
| numerical-application | bytecode | candidate | ok | 0.66325 µs | 2.935 ms | 4950 B | 2992 B |
| dependency-fanout | source | candidate | ok | 5.24308 µs | 25.0887 ms | 45725 B | 3840 B |
| dependency-fanout | bytecode | candidate | ok | 5.29167 µs | 24.8138 ms | 45725 B | 3840 B |
| touched-equal | source | candidate | ok | 0.30725 µs | 1.78887 ms | 2141 B | 352 B |
| touched-equal | bytecode | candidate | ok | 0.28125 µs | 1.70542 ms | 2141 B | 352 B |
| retained-snapshots | source | candidate | ok | 133.883 µs | 3.08942 ms | 2410 B | 18415 B |
| retained-snapshots | bytecode | candidate | ok | 128.546 µs | 2.90308 ms | 2410 B | 18415 B |
| abort-recovery | source | candidate | ok | 0.816 µs | 2.13867 ms | 2934 B | 896 B |
| abort-recovery | bytecode | candidate | ok | 0.822917 µs | 2.18312 ms | 2934 B | 896 B |
| compile-chain | source | candidate | ok | 14.7153 µs | 84.1257 ms | 117469 B | 8496 B |
| compile-chain | bytecode | candidate | ok | 14.3021 µs | 81.7371 ms | 117469 B | 8496 B |
| ekf | source | candidate | ok | 1.30111 µs | 20.9397 ms | 16594 B | 7342 B |
| ekf | bytecode | candidate | ok | 1.30651 µs | 21.072 ms | 16594 B | 7342 B |
| table-joins | source | candidate | error | — | — | — | — |
| table-joins | bytecode | candidate | error | — | — | — | — |
| graphs | source | candidate | ok | 18.6708 µs | 17.892 ms | 12995 B | 15752 B |
| graphs | bytecode | candidate | ok | 18.5708 µs | 17.8873 ms | 12995 B | 15752 B |
| strings | source | candidate | ok | 2.55114 µs | 2.22117 ms | 2800 B | 9896 B |
| strings | bytecode | candidate | ok | 2.60605 µs | 2.30458 ms | 2800 B | 9896 B |
| state-machines | source | candidate | ok | 5.3335 µs | 2.30354 ms | 3008 B | 4662 B |
| state-machines | bytecode | candidate | ok | 5.7915 µs | 2.38142 ms | 3000 B | 4662 B |
| jit | jit | candidate | ok | — | 81.8653 ms | 117469 B | — |
| capacity-growth | source | candidate | ok | 554.458 µs | 2.81029 ms | 2410 B | 5679 B |
| capacity-growth | bytecode | candidate | ok | 553.658 µs | 2.69875 ms | 2410 B | 5679 B |
| rejected-recovery | source | candidate | ok | 0.3333 µs | 1.77892 ms | 2141 B | 352 B |
| rejected-recovery | bytecode | candidate | ok | 0.35 µs | 1.79971 ms | 2141 B | 352 B |
| table-left-outer-join | source | candidate | error | — | — | — | — |
| table-left-outer-join | bytecode | candidate | error | — | — | — | — |
| table-right-outer-join | source | candidate | error | — | — | — | — |
| table-right-outer-join | bytecode | candidate | error | — | — | — | — |
| table-full-outer-join | source | candidate | error | — | — | — | — |
| table-full-outer-join | bytecode | candidate | error | — | — | — | — |
| table-left-semi-join | source | candidate | error | — | — | — | — |
| table-left-semi-join | bytecode | candidate | error | — | — | — | — |
| table-left-anti-join | source | candidate | error | — | — | — | — |
| table-left-anti-join | bytecode | candidate | error | — | — | — | — |
| string-graphemes | source | candidate | ok | 35.5416 µs | 3.35821 ms | 3753 B | 9600 B |
| string-graphemes | bytecode | candidate | ok | 35.6928 µs | 3.31333 ms | 3753 B | 9600 B |
| capacity-growth-7 | source | candidate | ok | 654.629 µs | 2.81608 ms | 2410 B | 5791 B |
| capacity-growth-7 | bytecode | candidate | ok | 1166.85 µs | 7.25887 ms | 2410 B | 5791 B |
| capacity-growth-8 | source | candidate | ok | 661.908 µs | 2.74717 ms | 2410 B | 5807 B |
| capacity-growth-8 | bytecode | candidate | ok | 663.663 µs | 2.76192 ms | 2410 B | 5807 B |
| capacity-growth-9 | source | candidate | ok | 673.742 µs | 2.84237 ms | 2410 B | 5823 B |
| capacity-growth-9 | bytecode | candidate | ok | 673.725 µs | 2.79121 ms | 2410 B | 5823 B |
| capacity-growth-15 | source | candidate | ok | 756.404 µs | 2.75042 ms | 2410 B | 5919 B |
| capacity-growth-15 | bytecode | candidate | ok | 760.579 µs | 2.80042 ms | 2410 B | 5919 B |
| capacity-growth-16 | source | candidate | ok | 767.417 µs | 2.81212 ms | 2410 B | 5935 B |
| capacity-growth-16 | bytecode | candidate | ok | 772.642 µs | 2.71571 ms | 2410 B | 5935 B |
| capacity-growth-17 | source | candidate | ok | 785.775 µs | 2.75621 ms | 2410 B | 5951 B |
| capacity-growth-17 | bytecode | candidate | ok | 784.817 µs | 2.73958 ms | 2410 B | 5951 B |
| capacity-growth-31 | source | candidate | ok | 961.825 µs | 2.82942 ms | 2410 B | 6175 B |
| capacity-growth-31 | bytecode | candidate | ok | 963.571 µs | 2.76704 ms | 2410 B | 6175 B |
| capacity-growth-32 | source | candidate | ok | 976.387 µs | 2.76108 ms | 2410 B | 6191 B |
| capacity-growth-32 | bytecode | candidate | ok | 982.087 µs | 2.74538 ms | 2410 B | 6191 B |
| capacity-growth-33 | source | candidate | ok | 982.971 µs | 2.73196 ms | 2410 B | 6207 B |
| capacity-growth-33 | bytecode | candidate | ok | 999.812 µs | 2.82729 ms | 2410 B | 6207 B |
| capacity-growth-63 | source | candidate | ok | 1388.38 µs | 2.74825 ms | 2410 B | 6687 B |
| capacity-growth-63 | bytecode | candidate | ok | 1353.41 µs | 2.75588 ms | 2410 B | 6687 B |
| capacity-growth-64 | source | candidate | ok | 1397.01 µs | 2.74808 ms | 2410 B | 6703 B |
| capacity-growth-64 | bytecode | candidate | ok | 1388.89 µs | 2.7865 ms | 2410 B | 6703 B |
| capacity-growth-65 | source | candidate | ok | 1390.11 µs | 2.73371 ms | 2410 B | 6719 B |
| capacity-growth-65 | bytecode | candidate | ok | 1403.8 µs | 2.73883 ms | 2410 B | 6719 B |

Managed counters report admitted backing, separately from whole-worker peak RSS. The worker high-water mark includes compilation and preparation, and is not an execution-interval RSS measurement. Allocation counters include the counting-allocator overhead. Object/linked sections are absent until a native recipe is qualified.

Exact source, contracts, worker hashes, toolchains, comparison order, verification outputs, requests and raw observations accompany this report.
