# Benchmark coverage

The current dataset contains **55 execution variants across 49 language families**, **10 workloads**, and **884 selected timed program profiles**. The source inventory retains **927 profiles**, including forty-three measured candidates that are not selected endpoints. Fifty-two execution variants cover the complete suite.

The live explorer has persistent language tabs with comparison controls, the main graph, stacked ranking charts, per-benchmark results, and an all-language table relative to the selected execution variant at 1.0×. Reset stays within the active view. Its [current deployment](../site/publications/language-hero-v1/deployment.json), build `f8fd1024ae7b55d9`, passed verification of all 33 live assets on October 14, 2026 at 20:51 UTC. [Mobile, desktop and interaction checks](../site/publications/language-hero-v1/validation.json) also passed.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Lua interpreter | 9 / 10 | Pi digits: completed samples await catalog admission |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| GNU APL | 9 / 10 | Binary trees: the full-size run exceeded its workspace allocation |

Eleven chart gaps have been filled from **93 preserved observations: 60 subject
observations and 33 matched Mech controls**. No replacement timing run was needed.
R and Uiua now cover all ten workloads, and GNU APL covers nine. The admission
receipts retain exact source counts, output validation, original exclusions,
source aliases, and the recovered GNU APL fannkuch observation:

- [R: N-body, binary trees and fannkuch](../experiments/r/retained-native-v1/publication/apply-target-v2/SUCCESS.json).
- [Uiua: fannkuch](../experiments/uiua/fann-v5-publication-v1/publication/apply-target-v1/SUCCESS.json) and [N-body/binary trees](../experiments/uiua/retained-native-v1/publication/apply-target-v2/SUCCESS.json).
- [GNU APL: five additional workloads](../experiments/apl/retained-native-v1/publication/apply-target-v2/SUCCESS.json).

The [normalization history](../data/normalization-history.json) records new
canonical LOC minima: fannkuch 31 → 20, N-body 20 → 19, and binary trees 16 → 15.
Only derived LOC coordinates change; saved runtimes, samples, source counts and
best-time baselines are preserved. The [publication adapter](../experiments/shared/retained-publication-v1/TARGET-CHECKOUT-V2.md)
validates evidence in its original checkout and writes a separate publication
checkout. GNU APL's [runtime-scope review](../experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json)
records static dependency evidence without claiming a per-process loaded-library inventory.

[Lua pi digits](../experiments/lua/retained-pidigits-v1/) has twelve retained Lua
observations across four source forms and six matched Mech controls. Its
[candidate export](../experiments/lua/retained-pidigits-v1/publication/export-v1/candidate.json)
and complete application-plus-GMP-helper source counts are verified. Catalog
admission remains pending. A [reviewed additive publication adapter](../experiments/lua/retained-pidigits-v1/PUBLICATION-TARGET.md) supports the existing nine-workload series with no stored aggregate row; its publication, history and transaction checks passed. No timing rerun is required.

GNU APL binary trees remains a separate failed workload without valid full-size
samples. A [bounded workspace-configuration packet](../experiments/apl/binarytrees-workspace-v1/)
proposes a supported memory-limit adjustment and allocation checks before a new
full-size run; its native commands have not executed.

Prolog, Julia AOT, and Rebol are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Mech interpreted | [Fresh whole-process cohort](../experiments/mech/interpreted-whole-process-v1/): fifteen unchanged source forms, three samples each, all 45 complete outputs validated | Published with preparation and shutdown included; AOT, JIT and other language measurements are preserved. [Live Pages publication verified](../experiments/mech/interpreted-whole-process-v1/deployment.json), including all 33 chart assets and the complete dataset. |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty original forms plus a qualified linear reverse-complement replacement; a [k-nucleotide correction](../experiments/prolog/knucleotide-linear-v1/) is prepared for native qualification | **54 completed observations are preserved**: 40 earlier observations plus 14 from the [latest continuation](../experiments/prolog/full50-remaining-v1/). Its unfinished k-nucleotide attempt was deliberately stopped after the retained runtime source revealed a full-string copy on every indexed character read. The [closed stop record](../experiments/prolog/knucleotide-linear-v1/stop-v1/closure.json) verifies unchanged completed receipts and released process ownership; the interrupted attempt supplies no timing. Corrected k-nucleotide qualification, the 36 unfinished slots, reconciliation and import remain. Earlier quadratic reverse-complement work is also excluded. The existing [separate-checkout adapter](../experiments/prolog/full50-remaining-v1/publication/TARGET-CHECKOUT.md) is source-reviewed; the [36-slot continuation](../experiments/prolog/full36-knucleotide-v1/) and [corrected native qualification](../experiments/prolog/knucleotide-linear-v1/qualification/) have passed independent source review; actual preparation and execution remain |
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

Compiler improvements are tracked separately in [Mech PR #897](https://github.com/mech-lang/mech/pull/897). At head `4c420233`, [CI run 38624354538](https://github.com/mech-lang/mech/actions/runs/38624354538) passed 153 tests in the Linux native-regression step before its 25-minute limit interrupted compilation for the final CLI test. The CLI regression remains unverified; the workflow budget correction and macOS checks are pending. The retained [earlier CI snapshot](../migration/compiler-ci-status.json) describes head `3445f901` and its completed checks.

See [methodology](methodology.md) for admission rules, timing boundaries, and reproduction limits; [language classifications](languages.md) for runtime and language metadata; and [results/current/](../results/current/) for program and sample tables.
