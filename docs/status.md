# Benchmark coverage

The current dataset contains **55 execution variants across 49 language families**, **10 workloads**, and **867 selected timed program profiles**. The source inventory retains **904 profiles**, including thirty-seven measured candidates that are not selected endpoints. Fifty execution variants cover the complete suite.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| R | 7 / 10 | N-body, binary trees, fannkuch-redux |
| Uiua | 7 / 10 | N-body, binary trees, fannkuch-redux |
| GNU APL | 4 / 10 | N-body, mandelbrot, k-nucleotide, binary trees, fannkuch-redux, FASTA |

Prolog, Julia AOT, and Rebol are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Mech interpreted | [Fresh whole-process cohort](../experiments/mech/interpreted-whole-process-v1/): fifteen unchanged source forms, three samples each, all 45 complete outputs validated | Published with preparation and shutdown included; AOT, JIT and other language measurements are preserved. [Live Pages publication verified](../experiments/mech/interpreted-whole-process-v1/deployment.json), including all 33 chart assets and the complete dataset. |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty original forms plus a linear reverse-complement replacement; replacement passed 540 bounded cases, compiled-work review and nine native source readers with independently reviewed canonical LOC | Original quadratic reverse-complement run remains cancelled; 40 qualified observations are retained (nine earlier regex samples and 31 continuation samples). The [prepared continuation](../experiments/prolog/full50-remaining-v1/) schedules only the 50 missing full-size slots. Independent [result reconciliation](../experiments/prolog/full81-linear-v1/reconciliation.md), [runtime metadata review](../experiments/prolog/full81-linear-v1/runtime-metadata.md) and [publication tooling](../experiments/prolog/full81-linear-v1/publication.md) are source-reviewed; publication requires completing and reconciling the remaining samples |
| Elixir | Twenty compiled source forms; required work, canonical and formatted source counts, runtime metadata, and independent reconciliation of sixty Elixir samples and thirty matched Mech controls | Published in the dataset; identical source aliases retain separate measurements without a distinct optimization claim |
| Kotlin | Twenty compiled source forms, source/class and helper review, all 186 bounded and supplemental workload checks, JIT/runtime observations, qualified canonical source counts, and independent reviews of all four fresh single-main tree/pi captures | [Published in the dataset](../experiments/kotlin/full90-v2/publication/) after all sixty Kotlin samples and thirty matched Mech controls passed independent reconciliation. All ten workloads have qualified canonical LOC and timings; formatted LOC remains unavailable. Existing published timings remain unchanged |
| Julia AOT | Trimmed N-body pilot produced the expected output with the code-generation library disabled | [Offline native inspection](../experiments/julia-aot/trimmed-native-inspection-v1/) prepared; execution-path/fallback qualification and the remaining suite |
| Rebol | Retained toolchain sources and resolved build specification | SDK and runtime qualification, benchmark implementations, and measurements |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

## Planned additions

| Language | Planned runtime | Workloads | Status |
| --- | --- | --- | --- |
| Scala | JVM | All ten | [All ten programs compiled and inspected](../experiments/scala/compiled-applications-v1/run-v1/terminal.json); [all 149 correctness cases passed](../experiments/scala/bounded-v1/run-v1/terminal.json); [canonical source counts qualified](../experiments/scala/source-counts-v1/canonical-owner-review-v1/qualified-source-counts-v1.json). [Required-work review](../experiments/scala/single-entry-work-v1/actual-instruction-review-v1.json) combines 27 static contracts with actual tree allocation/lifetime and pi division evidence. First full measurements remain |
| TypeScript | Node.js / V8, using emitted JavaScript | All ten | [Strict compilation and native AST capture passed](../experiments/typescript/native-stage-v1/run-v1/terminal.json): ten emitted programs and source maps, forty AST inputs. [All 149 correctness cases passed independent review](../experiments/typescript/bounded-v1/independent-results-review-v1.json); [canonical source counts qualified](../experiments/typescript/source-units-v1/qualified-source-counts-v1.json) for all ten typed programs. Required work and first full measurements remain |

Each addition requires its own source bundles, compiler/runtime provenance,
correctness and required-work checks, source counts, and sequential fresh-process
measurements with matched Mech controls. TypeScript source and emitted JavaScript
will both be retained; existing JavaScript timings will not be reused as
TypeScript measurements.

The [shared correctness corpus](../experiments/shared/bounded-corpus-v1/)
contains 149 prepared cases for each addition. Scala 3.10.0 is retained and its
compiler/JDK versions have been observed locally. TypeScript 7.0.2 and its
declaration dependencies are retained; native version checks also verify
Node 24.19.0. Both additions have passed all 149 bounded correctness cases.
Neither addition has full-size timings.
The output checker has pure regression coverage for complete output, exact
numeric tolerances and language-specific rejections. Source-count preparation
includes [41 Scala owner fixtures and 29 capture fixtures](../experiments/scala/source-counts-v1/) and
[a TypeScript reader draft with 30 fixtures](../experiments/typescript/source-counts-v1/).
Reader diagnostics and prepared correctness cases do not grant benchmark qualification or timings.

See [methodology](methodology.md) for admission rules, timing boundaries, and reproduction limits; [language classifications](languages.md) for runtime and language metadata; and [results/current/](../results/current/) for program and sample tables.
