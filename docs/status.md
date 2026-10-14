# Benchmark coverage

The current dataset contains **52 execution variants across 46 language families**, **10 workloads**, and **834 selected timed program profiles**. The source inventory retains **843 profiles**, including nine measured candidates that are not selected endpoints. Forty-seven execution variants cover the complete suite.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| R | 7 / 10 | N-body, binary trees, fannkuch-redux |
| Uiua | 7 / 10 | N-body, binary trees, fannkuch-redux |
| GNU APL | 4 / 10 | N-body, mandelbrot, k-nucleotide, binary trees, fannkuch-redux, FASTA |

Pony, Prolog, Julia AOT, Rebol, Elixir, and Kotlin are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

## Planned additions

| Language | Planned runtime | Workloads | Status |
| --- | --- | --- | --- |
| Scala | JVM | All ten | Queued; qualification and measurements pending |
| TypeScript | Node.js / V8, using emitted JavaScript | All ten | Queued; qualification and measurements pending |

Each addition requires its own source bundles, compiler/runtime provenance,
correctness and required-work checks, source counts, and sequential fresh-process
measurements with matched Mech controls. TypeScript source and emitted JavaScript
will both be retained; existing JavaScript timings will not be reused as
TypeScript measurements.

See [methodology](methodology.md) for admission rules, timing boundaries, and reproduction limits; [language classifications](languages.md) for runtime and language metadata; and [results/current/](../results/current/) for program and sample tables.
