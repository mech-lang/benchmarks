# Benchmark coverage

The current dataset contains **53 execution variants across 47 language families**, **10 workloads**, and **847 selected timed program profiles**. The source inventory retains **863 profiles**, including sixteen measured candidates that are not selected endpoints. Forty-eight execution variants cover the complete suite.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| R | 7 / 10 | N-body, binary trees, fannkuch-redux |
| Uiua | 7 / 10 | N-body, binary trees, fannkuch-redux |
| GNU APL | 4 / 10 | N-body, mandelbrot, k-nucleotide, binary trees, fannkuch-redux, FASTA |

Prolog, Julia AOT, Rebol, Elixir, and Kotlin are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty source forms, required work, canonical LOC, bounded output checks, and provisional regex measurements | Full study cancelled after identifying quadratic reverse-complement copying; replacement qualification, remaining measurements, and publication review |
| Elixir | Twenty compiled source forms; all helper and 156 bounded workload checks passed; native reader completed for all sixty authored inputs and fourteen grammar fixtures | Compiled required-work witnesses, canonical source ownership review, and full measurements |
| Kotlin | Twenty compiled source forms, source/class and helper review, and all 156 bounded workload checks | Supplemental workload checks, required-work and source-count qualification, then measurements |
| Julia AOT | Trimmed N-body pilot produced the expected output with the code-generation library disabled | Execution-path qualification and the remaining suite |
| Rebol | Retained toolchain sources and resolved build specification | SDK and runtime qualification, benchmark implementations, and measurements |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

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
