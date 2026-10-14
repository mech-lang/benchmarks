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
| Prolog | Twenty original source forms, required work, canonical LOC, bounded output checks, and provisional regex measurements | Original full study cancelled after identifying quadratic reverse-complement copying; linear replacement's 540-case bounded protocol and nine-reader source-count controller reviewed, with native qualification and remaining measurements pending |
| Elixir | Twenty compiled source forms; helper and 156 bounded workload checks; canonical and formatted source counts; fifteen native diagnostic fixtures; all 68 compiled-work obligations reviewed and qualified; sixty subject samples and thirty matched Mech controls completed | Independent reconciliation and publication review remain |
| Kotlin | Twenty compiled source forms, source/class and helper review, all 186 bounded and supplemental workload checks, JIT/runtime observations, qualified canonical source counts, and reviewed fresh single-main compact-tree capture | Three remaining tree/pi captures and the [serial full-suite controller](../experiments/kotlin/full90-v1/) prepared; complete single-main work verification and measurements remain |
| Julia AOT | Trimmed N-body pilot produced the expected output with the code-generation library disabled | [Offline native inspection](../experiments/julia-aot/trimmed-native-inspection-v1/) prepared; execution-path/fallback qualification and the remaining suite |
| Rebol | Retained toolchain sources and resolved build specification | SDK and runtime qualification, benchmark implementations, and measurements |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

## Planned additions

| Language | Planned runtime | Workloads | Status |
| --- | --- | --- | --- |
| Scala | JVM | All ten | [Source drafts](../experiments/scala/source-v1/) prepared; compiler/runtime, correctness, required work, source counts and measurements pending |
| TypeScript | Node.js / V8, using emitted JavaScript | All ten | [Source drafts](../experiments/typescript/source-v1/INVENTORY.md) prepared; compiler/runtime, correctness, required work, source counts and measurements pending |

Each addition requires its own source bundles, compiler/runtime provenance,
correctness and required-work checks, source counts, and sequential fresh-process
measurements with matched Mech controls. TypeScript source and emitted JavaScript
will both be retained; existing JavaScript timings will not be reused as
TypeScript measurements.

The [shared correctness corpus](../experiments/shared/bounded-corpus-v1/)
contains 149 prepared cases for each addition. Compiler versions are selected
as Scala 3.10.0 and TypeScript 7.0.2; local installation, runtime validation,
native source-reader checks and subject execution remain pending.
The output checker has pure regression coverage for complete output, exact
numeric tolerances and language-specific rejections. Source-count preparation
includes [a Scala reader draft with 41 fixtures](../experiments/scala/source-counts-v1/) and
[a TypeScript reader draft with 30 fixtures](../experiments/typescript/source-counts-v1/).
None of these source-only preparations grants native qualification or timings.

See [methodology](methodology.md) for admission rules, timing boundaries, and reproduction limits; [language classifications](languages.md) for runtime and language metadata; and [results/current/](../results/current/) for program and sample tables.
