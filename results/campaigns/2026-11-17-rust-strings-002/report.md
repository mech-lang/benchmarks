# Paired Rust task controls

Same inputs, accepted turns, warmup and output/retention obligations, paired on the same machine. Rust is an independent AOT task implementation with typed input validation, change detection and owned publication. Rust uses native ownership; Mech additionally performs its runtime admission, dependency scheduling, budget accounting and turn summary. This measures the cost of completing the task through each path, not a language-wide speed claim. Compilation is outside the resident timer. Rust preparation is not presented as a Mech artifact or JIT metric.

| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |
| --- | ---: | ---: | ---: |
| strings / source | 2.55371591e-06 | 2.43939091e-08 | 104.687 |
| strings / bytecode | 2.54818182e-06 | 2.43939091e-08 | 104.460 |
| string-graphemes / source | 3.00039375e-05 | 5.04375e-08 | 594.874 |
| string-graphemes / bytecode | 3.0151927e-05 | 5.04375e-08 | 597.808 |
