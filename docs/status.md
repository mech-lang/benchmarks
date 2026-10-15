# Benchmark coverage

The current dataset contains **58 execution variants across 52 language families**, **10 workloads**, and **916 selected timed program profiles**. The source inventory retains **971 profiles** across **900 source files**, including fifty-five measured candidates that are not selected endpoints. Fifty-six execution variants cover the complete suite. The catalog retains **2,997 samples**, of which **2,832 belong to selected profiles**.

The live explorer has persistent language tabs with comparison controls, the main graph, stacked ranking charts, per-benchmark results, and an all-language table relative to the selected execution variant at 1.0×. Language-page rankings center both speed and LOC at the selected variant’s 0σ, including variant changes and program navigation; global Rankings retain the coordinate-median origin. Reset preserves the selected language page; the Rankings reset remains in Rankings. Its [current verified deployment](../site/publications/hero-ranking-origin-v1/deployment.json), build `b132586a64ed8dff`, passed verification of all 33 live assets and the final manifest on October 14, 2026 at 22:22 UTC. [Mobile, desktop and interaction checks](../site/publications/hero-ranking-origin-v1/validation.json) and a [fresh live-browser check](../site/publications/hero-ranking-origin-v1/live-browser.json) passed. Scala and TypeScript are included in the live dataset.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |
| GNU APL | 9 / 10 | Binary trees: the full-size run exceeded its workspace allocation |

Twelve chart gaps have been filled from **111 preserved observations: 72 subject
observations and 39 matched Mech controls**. No replacement timing run was needed.
Lua, R and Uiua now cover all ten workloads, and GNU APL covers nine. The admission
receipts retain exact source counts, output validation, original exclusions,
source aliases, and the recovered GNU APL fannkuch observation:

- [Lua: pi digits](../experiments/lua/retained-pidigits-v1/publication/apply-target-lua-v1/SUCCESS.json).
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

[Lua pi digits](../experiments/lua/retained-pidigits-v1/) retains four distinct
applications, their shared GMP helper, twelve subject observations and six
matched Mech controls. Its [admission](../experiments/lua/retained-pidigits-v1/publication/apply-target-lua-v1/SUCCESS.json)
adds the tenth workload and a complete-suite aggregate while preserving the
absence of a historical partial aggregate. LuaJIT and existing timings are unchanged.

GNU APL binary trees remains without valid full-size samples. The
[workspace-configuration packet](../experiments/apl/binarytrees-workspace-v1/)
observed the supported memory-scale change from 90 to 200. Earlier shutdown and
allocation-witness failures remain retained. Two subsequent
[scoped ownership diagnostics](../experiments/apl/binarytrees-workspace-v1/scope-isolated-v1/actual-ownership-review-v1.json)
passed: the recorder control retained no values, and distinct leaves plus a
seven-node tree were retained and released with the expected counts. The unchanged
whole subject then passed [complete N=4 and N=10 checks](../experiments/apl/binarytrees-workspace-v1/whole-subject-v1/actual-bounded-work-review-v1.json).
These are bounded qualification results, not timing samples. Full N=21 execution,
setup-plus-subject canonical counts and timing qualification remain pending;
the small-input results do not establish full-size resource sufficiency.

Julia AOT and Rebol are not selectable series in this dataset. Their experimental sources and qualification records are retained in the archive. The existing Julia series is JIT. A toolchain installation or incomplete study is not an admitted timing.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Mech interpreted | [Fresh whole-process cohort](../experiments/mech/interpreted-whole-process-v1/): fifteen unchanged source forms, three samples each, all 45 complete outputs validated | Published with preparation and shutdown included; AOT, JIT and other language measurements are preserved. [Live Pages publication verified](../experiments/mech/interpreted-whole-process-v1/deployment.json), including all 33 chart assets and the complete dataset. |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty source forms, required work, canonical counts, recorded runtime metadata, and [independent reconciliation](../experiments/prolog/full36-knucleotide-v1/reconciliation-v1.json) of sixty Prolog samples and thirty matched Mech controls | [Published for all ten workloads](../experiments/prolog/full36-knucleotide-v1/publication/apply-receipt-v1.json). The final 36 observations completed on October 15 at 01:25 UTC, preserving 54 earlier qualified observations. Both interrupted attempts remain excluded; their original producer reports retain their stopped status. Every timing covers a fresh complete process. Equivalent source aliases retain separate samples. Canonical LOC includes all authored helpers; formatted LOC remains unavailable. [Publication storage](../experiments/prolog/full36-knucleotide-v1/publication/storage-import.md) preserves exact compressed evidence and its decoded identities. |
| Elixir | Twenty compiled source forms; required work, canonical and formatted source counts, runtime metadata, and independent reconciliation of sixty Elixir samples and thirty matched Mech controls | Published in the dataset; identical source aliases retain separate measurements without a distinct optimization claim |
| Kotlin | Twenty compiled source forms, source/class and helper review, all 186 bounded and supplemental workload checks, JIT/runtime observations, qualified canonical source counts, and independent reviews of all four fresh single-main tree/pi captures | [Published in the dataset](../experiments/kotlin/full90-v2/publication/) after all sixty Kotlin samples and thirty matched Mech controls passed independent reconciliation. All ten workloads have qualified canonical LOC and timings; formatted LOC remains unavailable. [Live Pages publication verified](../experiments/kotlin/full90-v2/publication/deployment.json) on October 14 at 15:21 UTC, including all 33 assets. Existing published timings remain unchanged |
| Scala | Ten distinct compiled implementations; all 149 correctness cases, required work, canonical source counts and runtime metadata qualified | [Admitted for all ten workloads](../experiments/scala/full60-v1/publication/apply-receipt-v1.json) after independent reconciliation of thirty Scala samples and thirty matched Mech controls. Every sample covers fresh-process startup, class loading, JIT, complete work/output and shutdown. Existing measurements and baselines are preserved; no older measurement was rerun |
| TypeScript | Ten typed implementations; strict compilation, native AST capture, all 149 correctness cases, canonical source counts, required work and static runtime metadata qualified | [Admitted for all ten workloads](../experiments/typescript/full60-v1/publication/apply-receipt-v1.json) after independent reconciliation of thirty TypeScript samples and thirty matched Mech controls. Fresh Node processes include startup, emitted JavaScript loading, JIT, complete work/output and shutdown. Typed sources determine canonical counts; emitted JavaScript, source maps and native ASTs retain their execution/provenance roles. Existing JavaScript and other measurements are preserved; no older measurement was rerun |
| Julia AOT | Trimmed N-body pilot produced the expected output with the code-generation library disabled; all eleven offline captures are retained, including [both object/image disassemblies](../experiments/julia-aot/trimmed-native-inspection-v1/remaining-two-actual-review-v1.json) | The [static owner-chain review](../experiments/julia-aot/trimmed-native-inspection-v1/static-owner-chain-review-v1.json) connects the native main, driver and work loop. Actual entry world-age/ABI dispatch and serialized-IR/fallback qualification remain unresolved, followed by the remaining suite. The original nine-command stage's failure on unavailable RSS observation remains preserved; none of those captures was repeated |
| Rebol | Retained toolchain sources, resolved build specification, ten authored benchmark mains, [eighteen source-reviewed primitive fixture cases](../experiments/rebol/primitive-fixtures-v1/), and 29 retained generated SDK outputs | The [actual generator](../experiments/rebol/sdk-generation-v1/failed-generation-closure-review-v1.json) exited 1 after all six vendor stages and `DONE`: the wrapper attempted to assign an unset return value. Its failure is preserved. [Independent zero-native review](../experiments/rebol/sdk-generation-v1/generated-output-reuse-review-v1.json) approved reuse of the exact generated outputs for header/API review, with no generation retry. Header/API semantics, extension ABI/build/load, native primitive and benchmark qualification, source counts, and measurements remain |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

The pending APL binary-trees, Julia entry-dispatch and Rebol tooling has
[250 passing pure test methods across 21 scripts](../experiments/shared/pure-validation-20261015/README.md).
The initial three script failures and their repaired results are retained.
These checks cover synthetic receipt, ownership, source-count and publication
contracts; they perform no native intake or benchmark execution and do not
grant native, timing or chart admission. The implementations' remaining gates
above are unchanged.

## Scala and TypeScript evidence

Both additions retain their own source bundles, compiler/runtime provenance,
correctness and required-work checks, source counts, and sequential fresh-process
measurements with matched Mech controls. TypeScript sources and emitted JavaScript
are retained separately; existing JavaScript timings were not reused as
TypeScript measurements.

The [shared correctness corpus](../experiments/shared/bounded-corpus-v1/)
contains 149 prepared cases for each addition. Scala 3.10.0 is retained and its
compiler/JDK versions have been observed locally. TypeScript 7.0.2 and its
declaration dependencies are retained; native version checks also verify
Node 24.19.0. Both implementations have passed all 149 bounded correctness cases
and their first full cohorts are admitted. TypeScript's [required-work review](../experiments/typescript/required-work-v1/qualified-work-v1.json)
retains the original failed diagnostic producer, its independently reviewed tree
capture, and the separate missing-pi capture; these are not timing samples.
The output checker has pure regression coverage for complete output, exact
numeric tolerances and language-specific rejections. Source-count preparation
includes [41 Scala owner fixtures and 29 capture fixtures](../experiments/scala/source-counts-v1/) and
[a TypeScript reader draft with 30 fixtures](../experiments/typescript/source-counts-v1/).
Reader diagnostics and prepared correctness cases do not grant benchmark qualification or timings.

Compiler improvements are tracked separately in [Mech PR #897](https://github.com/mech-lang/mech/pull/897). For head `f6280e4f`, the [Linux native/engine and CLI job](https://github.com/mech-lang/mech/actions/runs/38636427209/job/116114770395) passed 153 native/engine tests and the separate CLI regression. The [macOS ownership/cache job](https://github.com/mech-lang/mech/actions/runs/38636427209/job/116114771542) passed all six AOT and one JIT regression tests. The [retained named-test records](../migration/compiler-ci-f628-native-tests.json) include actual nonzero test counts and identify the tested PR merge `c8773329`, containing this head and base `c4777b70`. The overall [CI run](https://github.com/mech-lang/mech/actions/runs/38636427209) completed successfully on October 14 at 23:36 UTC: **132 jobs passed, one was skipped, and none failed**. The [final workflow and job records](../migration/compiler-ci-f628-complete.json) include the language suites and final PR gate; the skipped Native plan job is identified separately. The [earlier CI snapshot](../migration/compiler-ci-status.json) remains historical evidence for head `3445f901`.

See [methodology](methodology.md) for admission rules, timing boundaries, and reproduction limits; [language classifications](languages.md) for runtime and language metadata; and [results/current/](../results/current/) for program and sample tables.
