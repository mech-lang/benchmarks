# Benchmark coverage

The current catalog contains **60 execution variants across 53 language families**, **10 workloads**, and **954 selected timed program profiles**. The source inventory retains **1,013 profiles** across **945 source files**, including fifty-nine measured candidates that are not selected endpoints. Fifty-nine execution variants cover the complete suite. The catalog retains **3,123 sample entries representing 3,111 distinct recorded runs**; **2,946 runs belong to selected profiles**. Four program labels explicitly share another program’s measurements.

The Data provenance and reproduction update is live as build `dd11f044ce0e37cd`, website commit `7bc50a8ab7b3e2718cc18187c495be6bc49445a5`. The [deployment receipt](../site/publications/data-reproduction-v1/deployment.json) verifies successful pipeline and Pages jobs, all 40 live assets and the final manifest. [Live table/export checks](../site/publications/data-reproduction-v1/live-browser.json) verify the actual dataset and separately loaded reproduction bytes; [eleven shared-view scenarios](../site/publications/data-reproduction-v1/live-view-links.json) also passed.

The **[Data view](https://mech-lang.org/benchmarks/#v=1&view=data)** exposes all **3,111 distinct recorded runs** with twenty-one sortable columns, sidebar filters, search, row selection and source inspection. CSV and JSON exports cover all rows, filtered rows or checked rows at full precision. JSON includes counted source bundles. Shared links retain filters, sort, pagination, row selection and open source. Full reproduction records load separately from the ordinary chart dataset.

[Original-source metadata](authorship.md) now distinguishes specific upstream files and translation predecessors from collections, workload descriptions and historical copies. All 497 cited implementation/reference URLs were reachable in the recorded primary-host check. Every measured source has an immutable retained-file citation and SHA-256. Original lineage is cited for 590 profiles, 34 have explicit suite-authored origin records, and 389 retain unresolved lineage; missing citations do not establish AI originality. Source-license evidence is identified for 612 profiles, partial for 317, and unverified for 84. The [source audit](../data/authorship-audit.json) replaces the earlier broad language-based authorship assumptions.

[Reproduction records](reproduction.md) cover all 1,013 profiles. Recorded release or development-commit information is indexed for 907; the other 106 explicitly lack an established compiler/runtime version in the recovered evidence. Each record retains available build stages, timed commands, inputs, environment, dependency pins, output checks, platform and report hashes. There are 364 recorded recipes and 649 with explicit information gaps. These are historical records, not clean-machine replay claims. The [preservation check](../site/publications/data-reproduction-v1/preservation.json) confirms every non-authorship catalog field is unchanged, including all timings, source bytes, LOC and baselines. No benchmarks were rerun.

Lean 4 (AOT) is live across all ten workloads with thirty validated complete-process samples. The [Lean deployment](../site/publications/lean4-v1/deployment.json), build `c8fa2c7d786dcc2e` at website commit `e254f0db5968d3a1ee6a18b7e2f152fd6ca54792`, passed verification of all 36 live assets and the final manifest on October 17, 2026 at 13:55 UTC. [Pipeline 2958546501](https://gitlab.com/mech-lang/web/website/-/pipelines/2958546501), the Pages job and the deployment job succeeded. The [browser gzip response](../site/publications/lean4-v1/gzip.json) matches the exact prepared dataset and includes all 60 execution variants across 53 language families. No fresh visual browser check is claimed for this deployment.

The [sidebar deployment](../site/publications/sidebar-scroll-v1/deployment.json), build `4af76df8e4d2ee4e` at website commit `e0be9fe85a77e116f87995f7045ce66a16be4ae4`, added pinned desktop filters with independent wheel and keyboard scrolling. Mobile filters retain a separate scrollable drawer. [Live browser checks](../site/publications/sidebar-scroll-v1/live-browser.json) passed at 1280, 900, 721 and 390 pixels, including the last language, scroll boundaries, page-position restoration and resizing an open drawer to desktop. All 36 deployed assets and the final manifest matched.

The [sharing deployment](../site/publications/view-links-v1/deployment.json) is build `99b2a8c55fe8e460`, website commit `db9da9ae851356103f45c62fb41ff4dc20b0bec2`. The address bar and Copy link preserve active language and comparison views, selected benchmarks and languages, year windows, filters, layers, profile visibility, axes, covariance selections, excluded programs, source files and table sorts. Saved language tabs retain their benchmark selections. Links restore before the first chart render; rapid slider changes coalesce URL updates, and browser Back/Forward restores selections. Eleven [live fresh-context scenarios](../site/publications/view-links-v1/live-browser-with-tab.json), desktop/mobile restoration, clipboard fallback and malformed-link checks passed. All 37 public assets and the final manifest matched on October 17 at 15:47 UTC. Timing observations and dataset bytes are unchanged.

The [Lean implementation study](lean4-implementations.md) adds thirteen measured candidates and thirty-nine serial whole-process samples. All 149 bounded cases, per-node allocation and permutation-coverage diagnostics, full outputs and normalized source counts passed. Twenty-three Lean programs now retain sixty-nine measurements; original candidates and all other-language observations remain unchanged. The fastest and fewest-LOC endpoints select observed winners independently. The [new catalog admission](../experiments/lean4/optimization-v1/catalog-admission-v1/receipt.json) preserves historical baselines. The [Lean endpoint deployment](../site/publications/lean4-endpoints-v1/deployment.json), build `25936292ef4caea7` at website commit `c0d9ff504ca44fcc4622c6f5d8a62d2e22637fff`, passed all 37 asset checks and the final manifest. [Live browser checks](../site/publications/lean4-endpoints-v1/live-browser.json) confirm the exact build, 23 Lean programs, 69 runs and all eleven sharing scenarios.

Julia (AOT) is live as a separate series alongside Julia (JIT). The [publication verification summary](../site/publications/julia-aot-full81-v1/verification-summary.json) confirms 59 execution variants across 52 language families and 2,877 selected runs. All seventeen Julia AOT profiles and their 51 independent subject samples remain inspectable. No active Rebol catalog, source, filter, marker, comparison-table or ranking entries remain; historical Rebol evidence is preserved.

The live explorer has persistent language tabs with comparison controls, the main graph, stacked ranking charts, per-benchmark results, and an all-language table relative to the selected execution variant at 1.0×. Language-page rankings center both speed and LOC at the selected variant’s 0σ, including variant changes and program navigation; global Rankings retain the coordinate-median origin. Reset preserves the selected language page; the Rankings reset remains in Rankings. Median hover and keyboard focus highlight that language’s visible samples; Samples Off remains hidden. Benchmark filters combine resource emphasis (compute, memory, I/O) with workload type (numerical, strings/sequences, allocation, data structures, combinatorial, graphics). Resource tags describe exercised work rather than claiming a measured bottleneck. The [Julia AOT deployment](../site/publications/julia-aot-full81-v1/deployment.json), build `1b021c21ca65c531` at website commit `8e87c9020ebe1a37eeac7b4c36fea11fa2efb75a`, passed verification of all 36 live assets and the final manifest on October 16, 2026 at 00:45 UTC. [Pipeline 2953247653](https://gitlab.com/mech-lang/web/website/-/pipelines/2953247653), Pages job 17219124758 and deployment job 17219135717 succeeded. [Mobile and desktop checks](../site/publications/julia-aot-full81-v1/browser.json) confirmed solid sample dots, Dim/Highlight visibility, Samples Off, median hover/focus, independent density and global layers, both Julia execution labels, source inspection, comparison tables and language-page rankings. The [fresh live mobile check](../site/publications/julia-aot-full81-v1/live-browser.json) passed at 00:46 UTC with all 59 variants, 52 families and 2,877 selected runs; the [gzip check](../site/publications/julia-aot-full81-v1/gzip.json) verified both compressed and decoded dataset bytes.


The [profile-selection deployment](../site/publications/profile-selection-v1/validation.json) is build `21dcbb5405ae1684`, website commit `74d9a588ff4c89d02295c42156e5e0be193b51c0`. Fastest and Fewest LOC select the same program observations for samples, summary markers, and density. Samples, medians, and density retain independent brightness controls. [Live desktop and mobile checks](../site/publications/profile-selection-v1/live-browser.json) verified all four profile combinations and all nine sample/median brightness combinations at both widths, with no page errors. [Pipeline 2956249210 and both Pages jobs](../site/publications/profile-selection-v1/deployment.json) succeeded; all 36 deployed assets and the final build manifest matched. The selected timing observations and dataset bytes are unchanged.

| Partial coverage | Measured workloads | Missing workloads |
| --- | ---: | --- |
| Futhark | 9 / 10 | Binary trees: array representation does not meet the per-node allocation contract |

Both [explorer performance passes](explorer-performance.md) are live. The first
reduced the browser payload from 73.8 MB to 8.3 MB before compression. The second
reduced synchronous interaction time under a simulated mobile 4× CPU slowdown:
filtering 170 → 128 ms, Rankings 190 → 56 ms, reset 201 → 35 ms, and density
contrast 138 → 1 ms. Language-page opening changed little, 403 → 396 ms. These
[matched measurements](../site/publications/explorer-performance-v2/comparison.json)
apply to build `7bba6e95588940c0`; they were not repeated for the subsequent
marker-style change or the subsequent Rebol catalog changes. The retained
[compression check](../site/publications/rebol-removal-v1/gzip.json) confirms
a 1.215 MB transferred body decoding to the 8.406 MB browser dataset.

Twelve chart gaps have been filled from **111 preserved observations: 72 subject
observations and 39 matched Mech controls**. No replacement timing run was needed.
These admissions completed Lua, R and Uiua and brought GNU APL to nine workloads;
the binary-trees cohort below completes its coverage. The admission
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

GNU APL binary trees has completed a qualified full-size cohort. The
[workspace-configuration packet](../experiments/apl/binarytrees-workspace-v1/)
observed the supported memory-scale change from 90 to 200. Earlier shutdown and
allocation-witness failures remain retained. Two subsequent
[scoped ownership diagnostics](../experiments/apl/binarytrees-workspace-v1/scope-isolated-v1/actual-ownership-review-v1.json)
passed: the recorder control retained no values, and distinct leaves plus a
seven-node tree were retained and released with the expected counts. The unchanged
whole subject then passed [complete N=4 and N=10 checks](../experiments/apl/binarytrees-workspace-v1/whole-subject-v1/actual-bounded-work-review-v1.json).
These are bounded qualification results, not timing samples. The unchanged main
plus workspace setup has [41 canonical source units](../experiments/apl/binarytrees-workspace-v1/source-counts-v1/qualified-source-counts-v1.json).
The [N=21 cohort](../experiments/apl/binarytrees-workspace-v1/full6-v1/plan-v1.json)
completed three APL samples and three matched Mech controls, serially, with setup
inside the measured process. [Independent reconciliation](../experiments/apl/binarytrees-workspace-v1/full6-v1/reconciliation/actual-v1.json)
passed for all six observations. APL's median was 1,239.684 seconds; the matched
Mech median was 0.411950 seconds. The [publication candidate](../experiments/apl/binarytrees-workspace-v1/full6-v1/publication/export-v1/candidate.json)
retains the raw evidence and source counts. [Catalog admission](../experiments/apl/binarytrees-workspace-v1/full6-v1/publication/apply-target-v1/SUCCESS.json)
adds the tenth APL workload without changing earlier measurements or baselines.
The public explorer includes this cohort. The optimized label
shares the compact program's measurements and does not represent another run
or a distinct optimization.

Julia (AOT) is admitted as a separate selectable series across all ten workloads. All seventeen standard PackageCompiler profiles passed three full-workload samples each, with thirty fresh matched Mech AOT controls: 81 independently reconciled observations. Fourteen profiles supply the selected endpoints; all seventeen remain inspectable. [Results and comparison limits](../experiments/julia/packagecompiler-v1/RESULTS.md) retain the FASTA slowdown and distinguish fresh matched controls from historical Julia JIT measurements. Existing Julia JIT and other-language observations, sources, exclusions and baselines are unchanged. The [actual import receipt](../experiments/julia/packagecompiler-v1/publication/apply-v1/import-receipt.json) records no new global minima.

| Implementation | Completed qualification | Remaining before timing publication |
| --- | --- | --- |
| Mech interpreted | [Fresh whole-process cohort](../experiments/mech/interpreted-whole-process-v1/): fifteen unchanged source forms, three samples each, all 45 complete outputs validated | Published with preparation and shutdown included; AOT, JIT and other language measurements are preserved. [Live Pages publication verified](../experiments/mech/interpreted-whole-process-v1/deployment.json), including all 33 chart assets and the complete dataset. |
| Pony | Twenty source forms, required work, canonical LOC, runtime metadata, and independent reconciliation of sixty Pony samples and thirty matched Mech controls | Published in the dataset |
| Prolog | Twenty source forms, required work, canonical counts, recorded runtime metadata, and [independent reconciliation](../experiments/prolog/full36-knucleotide-v1/reconciliation-v1.json) of sixty Prolog samples and thirty matched Mech controls | [Published for all ten workloads](../experiments/prolog/full36-knucleotide-v1/publication/apply-receipt-v1.json). The final 36 observations completed on October 15 at 01:25 UTC, preserving 54 earlier qualified observations. Both interrupted attempts remain excluded; their original producer reports retain their stopped status. Every timing covers a fresh complete process. Equivalent source aliases retain separate samples. Canonical LOC includes all authored helpers; formatted LOC remains unavailable. [Publication storage](../experiments/prolog/full36-knucleotide-v1/publication/storage-import.md) preserves exact compressed evidence and its decoded identities. |
| Elixir | Twenty compiled source forms; required work, canonical and formatted source counts, runtime metadata, and independent reconciliation of sixty Elixir samples and thirty matched Mech controls | Published in the dataset; identical source aliases retain separate measurements without a distinct optimization claim |
| Kotlin | Twenty compiled source forms, source/class and helper review, all 186 bounded and supplemental workload checks, JIT/runtime observations, qualified canonical source counts, and independent reviews of all four fresh single-main tree/pi captures | [Published in the dataset](../experiments/kotlin/full90-v2/publication/) after all sixty Kotlin samples and thirty matched Mech controls passed independent reconciliation. All ten workloads have qualified canonical LOC and timings; formatted LOC remains unavailable. [Live Pages publication verified](../experiments/kotlin/full90-v2/publication/deployment.json) on October 14 at 15:21 UTC, including all 33 assets. Existing published timings remain unchanged |
| Lean 4 | [Ten native implementations](../experiments/lean4/plan-v1.json) compiled with Lean 4.35.0; all 149 bounded correctness cases passed, with generated-code review and a 51,550-node allocation witness | [All thirty full-size samples reconciled](../experiments/lean4/results-v1.json), three per workload, including startup, complete work/output and shutdown. [Canonical source counts](../experiments/lean4/source-counts-v1/qualification-v4/qualified-counts.json) include all authored Lean and C helpers. [Catalog admission](../experiments/lean4/catalog-admission-v1/receipt.json) preserves every historical observation and baseline; [Live publication](../site/publications/lean4-v1/deployment.json) verifies all 36 deployed assets, the final manifest and the browser gzip response. Algorithms are Lean; C leaves provide general formatting and PCRE2 compile/next-match operations |
| Scala | Ten distinct compiled implementations; all 149 correctness cases, required work, canonical source counts and runtime metadata qualified | [Admitted for all ten workloads](../experiments/scala/full60-v1/publication/apply-receipt-v1.json) after independent reconciliation of thirty Scala samples and thirty matched Mech controls. Every sample covers fresh-process startup, class loading, JIT, complete work/output and shutdown. Existing measurements and baselines are preserved; no older measurement was rerun |
| TypeScript | Ten typed implementations; strict compilation, native AST capture, all 149 correctness cases, canonical source counts, required work and static runtime metadata qualified | [Admitted for all ten workloads](../experiments/typescript/full60-v1/publication/apply-receipt-v1.json) after independent reconciliation of thirty TypeScript samples and thirty matched Mech controls. Fresh Node processes include startup, emitted JavaScript loading, JIT, complete work/output and shutdown. Typed sources determine canonical counts; emitted JavaScript, source maps and native ASTs retain their execution/provenance roles. Existing JavaScript and other measurements are preserved; no older measurement was rerun |
| Julia AOT | Seventeen native profiles, 51 full-workload subject samples and 30 fresh matched Mech controls independently reconciled; every complete output validated | Admitted across ten workloads with fourteen selected endpoint profiles. [Results](../experiments/julia/packagecompiler-v1/RESULTS.md) retain all observations and comparison limits; [Live Pages publication verified](../site/publications/julia-aot-full81-v1/verification-summary.json). |

Current qualification tools and results are organized by implementation under
[`experiments/`](../experiments/); earlier evidence remains under
[`archive/languages/`](../archive/languages/).

The APL binary-trees, Julia entry-dispatch and Rebol tooling has
[250 passing pure test methods across 21 scripts](../experiments/shared/pure-validation-20261015/README.md).
The initial three script failures and their repaired results are retained.
These checks cover synthetic receipt, ownership, source-count and publication
contracts; they perform no native intake or benchmark execution and do not
grant native, timing or chart admission. The implementations' remaining gates
are separate from the native and publication results above. A later
[helper validation](../experiments/shared/follow-up-pure-validation-20261015/README.md)
passed 17 APL publication, five Rebol relocation and six Julia transport methods.
The APL set extends the earlier suite; these counts are not an additional set of
28 distinct methods.

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
