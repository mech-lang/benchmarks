# Paired Rust task controls

Same inputs, accepted turns, warmup and output/retention obligations, paired on the same machine. Rust is an independent AOT task implementation with typed input validation, change detection and owned publication. Rust uses native ownership; Mech additionally performs its runtime admission, dependency scheduling, budget accounting and turn summary. This measures the cost of completing the task through each path, not a language-wide speed claim. Compilation is outside the resident timer. Rust preparation is not presented as a Mech artifact or JIT metric.

| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |
| --- | ---: | ---: | ---: |
| concurrent / process-workers | 0.105043958 | 0.020163083 | 5.210 |
| concurrent-2 / process-workers | 0.0752885421 | 0.0251246672 | 2.997 |
| concurrent-4 / process-workers | 0.0684583341 | 0.0215662918 | 3.174 |
