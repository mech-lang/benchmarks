# Benchmark coverage

The current dataset contains **55 execution variants across 49 language families**, **10 workloads**, and **867 selected timed program profiles**. The source inventory retains **904 profiles**, including thirty-seven measured candidates that are not selected endpoints. Fifty execution variants cover the complete suite.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits: completed samples await catalog admission |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| R | 7 / 10 | N-body, binary trees, fannkuch-redux |
| Uiua | 7 / 10 | N-body, binary trees, fannkuch-redux |
| GNU APL | 4 / 10 | N-body, mandelbrot, k-nucleotide, binary trees, fannkuch-redux, FASTA |

Eleven of the R, Uiua and GNU APL chart gaps already have complete retained
sample sets: **60 subject observations and 33 matched controls**. The
[retained-coverage audit](../experiments/shared/retained-coverage-audit-v1/)
identifies their exact reports, aliases, exclusions and remaining publication
checks. These completed measurements can be imported after reconciliation;
replacement performance runs are unnecessary. GNU APL binary trees remains a
separate failed workload without valid full-size samples. A [bounded workspace-configuration packet](../experiments/apl/binarytrees-workspace-v1/) proposes a supported memory-limit adjustment and allocation checks before any new full-size run. No native command in that packet has executed.

Independent canonical source-count reviews now cover all twenty distinct saved
sources: [six R sources](../experiments/r/retained-source-counts-v1/qualified-source-counts-v1.json),
[nine GNU APL sources](../experiments/apl/retained-counts-v1/qualified-source-counts-v1.json),
[three Uiua tree/N-body sources](../experiments/uiua/retained-counts-v1/qualified-source-counts.json),
and [two Uiua fannkuch sources](../experiments/uiua/fann-v5-publication-v1/independent-source-review.json).
Saved-observation reconciliation and candidate exporters have passed independent
source review for [R](../experiments/r/retained-native-v1/),
[GNU APL](../experiments/apl/retained-native-v1/),
[Uiua N-body and trees](../experiments/uiua/retained-native-v1/), and
[Uiua fannkuch](../experiments/uiua/fann-v5-publication-v1/).
The checks preserve all 93 valid observations, original exclusions, aliases,
and the recovered GNU APL fannkuch observation. Physical evidence replay and
catalog admission remain pending while the serial timing run holds the machine.
New canonical minima require derived LOC-coordinate updates; stored runtimes,
samples and original source counts remain unchanged.
The [shared publication tools](../experiments/shared/retained-publication-v1/)
have passed independent review, including 23 normalization checks, 16 guarded
import checks and eight candidate-to-catalog checks. GNU APL has a separate
[recorded runtime-scope approval](../experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json);
its static dependency evidence does not claim a per-process loaded-library
inventory. These reviews have not changed the published catalog.

[Lua pi digits](../experiments/lua/retained-pidigits-v1/) also has a complete retained cohort: twelve Lua observations across four distinct source forms and six matched Mech controls. Complete application-plus-GMP-helper source counts, the Lua-only reconciler/exporter, and [shared publication support](../experiments/shared/retained-publication-v1/lua-publication-v2.md) have passed independent source review. Fifty-six pure checks cover candidate admission, guarded import and historical preservation. Physical evidence replay and catalog admission remain pending. Together with the R, Uiua and GNU APL cohorts above, **111 completed observations can fill twelve chart gaps without new timing runs**.

Prolog, Julia AOT, and Rebol are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Mech interpreted | [Fresh whole-process cohort](../experiments/mech/interpreted-whole-process-v1/): fifteen unchanged source forms, three samples each, all 45 complete outputs validated | Published with preparation and shutdown included; AOT, JIT and other language measurements are preserved. [Live Pages publication verified](../experiments/mech/interpreted-whole-process-v1/deployment.json), including all 33 chart assets and the complete dataset. |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty original forms plus a linear reverse-complement replacement; replacement passed 540 bounded cases, compiled-work review and nine native source readers with independently reviewed canonical LOC | Original quadratic reverse-complement run remains cancelled; 40 qualified observations are retained (nine earlier regex samples and 31 continuation samples). The [continuation](../experiments/prolog/full50-remaining-v1/) started on October 14 at 14:58 UTC and executes only the 50 missing full-size slots under a [durable supervisor](../experiments/prolog/full90-v1/launch_durable.py). Independent [three-cohort reconciliation](../experiments/prolog/full50-remaining-v1/reconciliation/) and [publication tools](../experiments/prolog/full50-remaining-v1/publication/) are source-reviewed; publication requires actual completion and reconciliation |
| Elixir | Twenty compiled source forms; required work, canonical and formatted source counts, runtime metadata, and independent reconciliation of sixty Elixir samples and thirty matched Mech controls | Published in the dataset; identical source aliases retain separate measurements without a distinct optimization claim |
| Kotlin | Twenty compiled source forms, source/class and helper review, all 186 bounded and supplemental workload checks, JIT/runtime observations, qualified canonical source counts, and independent reviews of all four fresh single-main tree/pi captures | [Published in the dataset](../experiments/kotlin/full90-v2/publication/) after all sixty Kotlin samples and thirty matched Mech controls passed independent reconciliation. All ten workloads have qualified canonical LOC and timings; formatted LOC remains unavailable. [Live Pages publication verified](../experiments/kotlin/full90-v2/publication/deployment.json) on October 14 at 15:21 UTC, including all 33 assets. Existing published timings remain unchanged |
| Julia AOT | Trimmed N-body pilot produced the expected output with the code-generation library disabled | [Offline native inspection controller](../experiments/julia-aot/trimmed-native-inspection-v1/) source-reviewed; tool preparation, eleven captures, execution-path/fallback qualification and the remaining suite |
| Rebol | Retained toolchain sources, resolved build specification, ten authored benchmark mains, and [eighteen source-reviewed primitive fixture cases](../experiments/rebol/primitive-fixtures-v1/) | SDK generation, extension ABI/build/load, native primitive and benchmark qualification, source counts, and measurements |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

## Planned additions

| Language | Planned runtime | Workloads | Status |
| --- | --- | --- | --- |
| Scala | JVM | All ten | [All ten programs compiled and inspected](../experiments/scala/compiled-applications-v1/run-v1/terminal.json); [all 149 correctness cases passed](../experiments/scala/bounded-v1/run-v1/terminal.json); [canonical source counts qualified](../experiments/scala/source-counts-v1/canonical-owner-review-v1/qualified-source-counts-v1.json). [Required-work review](../experiments/scala/single-entry-work-v1/actual-instruction-review-v1.json) combines 27 static contracts with actual tree allocation/lifetime and pi division evidence. The [first full cohort controller](../experiments/scala/full60-v1/) is source-reviewed; thirty Scala samples and thirty matched Mech controls remain |
| TypeScript | Node.js / V8, using emitted JavaScript | All ten | [Strict compilation and native AST capture passed](../experiments/typescript/native-stage-v1/run-v1/terminal.json): ten emitted programs and source maps, forty AST inputs. [All 149 correctness cases passed independent review](../experiments/typescript/bounded-v1/independent-results-review-v1.json); [canonical source counts qualified](../experiments/typescript/source-units-v1/qualified-source-counts-v1.json) for all ten typed programs. [Required work is qualified for all ten implementations](../experiments/typescript/required-work-v1/qualified-work-v1.json), including actual tree allocation/lifetime and both pi extractions. [Runtime metadata](../experiments/typescript/runtime-metadata-v1/qualified-runtime-metadata-v1.json) binds the retained Node binary, embedded versions and declared system dependencies. The tree capture was reused after a diagnostic-parser failure; only the missing pi invocation was launched. The [first full cohort controller](../experiments/typescript/full60-v1/) is source-reviewed; thirty TypeScript samples and thirty matched Mech controls remain |

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
