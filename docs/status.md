# Benchmark coverage

The canonical Mech nucleotide compiler work remains on draft
[PR #911](https://github.com/mech-lang/mech/pull/911). The
[batched lowering](../experiments/mech/native-hashmap-batch-v1/README.md)
passes all 168 native tests, public source/decoded standalone qualification,
permission denials and exact full-input output checks. Every full execution
retains seven tables and 874,999,961 actual updates. Its CPU profile is a
separate diagnostic; final timing runs are deferred while optimization continues.
The preceding canonical-native branch retains ordinary dense-counter and
direct-query optimization. No new nucleotide profile or website result is admitted.

The [direct map membership study](../experiments/mech/general-map-lookup-v1/README.md)
removes key-set construction from the Mech counting procedure. All seven widths
now pass the same 26-character diagnostic under the unchanged resident work
limit, including bytecode round-trip execution and every-key reference checks.
The candidate passes 151 distinct focused runtime/source/type/catalog/linkage
tests. The [preceding pure-entry study](../experiments/mech/general-map-entry-v1/README.md)
retains the earlier resource-denial evidence. An explicit general hash-table
contract, native ownership/lowering and complete-input work qualification remain
pending. No new benchmark timings or nucleotide results are admitted.
The [original map audit](../experiments/mech/general-map-counting-v1/README.md)
retains the empty-map constructor and assignment-gap evidence.
The [initial conforming baseline](../experiments/mech/native-hashmap-work-v1/README.md)
is retained as historical evidence, not a final performance result.

The [Mech pi-digits study](../experiments/mech/pidigits-performance-v1/RESULTS.md)
reuses the extraction numerator, reducing the current AOT median from 0.3128s
(1.08× optimized Mech) to 0.2901s (1.00×). In seven fresh shuffled rounds, unchanged
Rust #3 takes 0.3097s (1.07×) and Janet 0.3083s (1.06×). All 35 full outputs match;
actual GMP call witnesses verify both divisions and 22,454 saved multiplications.
The new study is separate from the historical catalog ratios below.

The [native Mech owner proof](../experiments/source-normalization/mech-v1/README.md)
now qualifies logical counts 38, 39 and 37 for its three source forms. Eighteen
manual fixtures and all native-token ownership checks pass. The catalog now
retains all 21 fresh Mech samples and selects the shorter candidate as its fastest
pi-digits result. Native logical counts bind to six exact Mech profiles.
The [Pages deployment](../experiments/mech/pidigits-pages-v1/README.md) is live:
build `66e4796d6f7171fd`, all 41 assets verified against the tested manifest.

Janet has full-size studies for seven workloads, with repeated fresh-process samples
per tested source and all full outputs verified. All application helpers remain
in scope; the standard Janet VM is unchanged. Timings below are parent → fastest
tested alternative, with ratios to retained same-input Mech AOT references:

| Workload | Parent seconds (× Mech AOT) | Candidate seconds (× Mech AOT) |
|---|---:|---:|
| Spectral norm | 66.827 (776.4×) | 16.531 (192.1×) |
| FASTA | 38.648 (71.4×) | 23.047 (42.6×) |
| k-nucleotide | 73.965 (143.9×) | 24.651 (48.0×) |
| Reverse complement | 13.380 (89.6×) | 12.712 (85.2×) |
| n-body | 105.393 (101.4×) | 23.864 (23.0×) |
| Binary trees* | 102.899 (260.9×) | 20.715 (52.5×) |
| Pi digits | 0.402 (1.34×) | 0.295 (0.98×) |

*Binary-trees allocation policies differ: Janet uses default GC, whereas the
Mech reference uses a general library pool with distinct node slots. Its 4.97×
improvement is within Janet. All fifteen full-size samples and 66 bounded
node-identity/visit checks pass.

The pi-digits study adds seven source alternatives. Its final eight-way cohort
has seven sequential shuffled rounds per source; all 56 outputs match. Earlier
35- and 49-observation cohorts remain separate. Both extraction calls and exact
integer states are verified. The shorter positive-division form takes 0.299s
(1.00× retained Mech AOT) with 417 lexical tokens versus 454. Its close historical
Mech ratios do not establish a current cross-language ordering.

The n-body register/macro form is 4.42× faster with all pair arithmetic retained.
The reverse-complement candidates also meet line-by-line input requirements that
the historical parent does not, with about 91% lower peak RSS. All 149 original
bounded contracts pass across the active draft set. New binary-trees/fannkuch
candidates add 35 complete output checks and 35 work witnesses, including unique
node allocation and every permutation/flip through N=8. The tree candidate now
has full-size timings above; the fannkuch alternatives remain unmeasured at full
size. Native lexical measures now cover 40 unique Janet sources.

Three workloads still lack full-size studies. Normalized logical and canonical
formatted LOC, remaining qualification and chart admission remain pending.
No Janet profile is admitted. The [Janet packet](../experiments/janet/README.md)
retains every source-size tradeoff, original lineage/license, raw sample and
ownership receipt. Mech references are historical, not freshly paired controls;
recorded desktop activity and live telemetry prevent pristine-idle/continuous
thermal claims. The [boundary clarification](../experiments/janet/measurement-boundary-review-v1.json)
changes no elapsed values or prior sealed captures.

The [application-LOC correction](source-size-correction.md) resolves the reviewed
host/binding/library inconsistencies in 183 profiles, including embedded source
sections. The earlier [audit](source-size-audit.md) remains a snapshot of the
previous accounting. Source bytes and timing observations are unchanged. Current
source details and exports expose the corrected counts and previous totals.

The current chart catalog contains **1,014 program profiles**, **63 execution
variants across 54 language families**, and **10 workloads**. The full reconciled
inventory contains **1,077 profiles across 973 source identities**. Its
[exact-source review inventory](../experiments/implementation-audit/coverage-v5/README.md)
separates 385 protected upstream profiles, 641 editable profiles and 51 profiles
with unresolved ownership. Of the editable profiles, 336 have static source
inspections and 305 remain unreviewed. An inspection is not a completed
optimization study or proof that an implementation is globally fastest.

Three reviewed Crystal regex scan implementations are now admitted with nine new
full-process observations. The parallel block form has a 1.651s median
(3.37× the retained Mech AOT time), versus 34.991s (71.47×) for the freshly
measured retained-source control. Parallel inline scan is 1.686s (3.44×), and
compact inline scan is 2.572s (5.25×). Retained-policy counts are 54/47/32 units,
respectively. The [admission](../experiments/crystal/regex-byte-offsets-v1/admission-v1/results.json)
and [preservation proof](../experiments/crystal/regex-byte-offsets-v1/admission-v1/preservation.json)
retain every older profile, source, count and sample. Mech AOT’s 0.489612s
baseline is historical and is separate from the matched Crystal comparison.
Native formatted and uniform logical Crystal counts remain pending. Explorer
build `d99c08066acbc1db`, website commit
`1754e93bdde2471d4963f01083d339f4b86ffacd`, is
[live and verified](../site/publications/crystal-scan-v1/live-pages.json):
all 41 public assets match, and all 14
[live Data/export/mobile/shared-selection checks](../site/publications/crystal-scan-v1/live-browser.json)
passed with no page errors.

The [TypeScript input/Map audit](../experiments/typescript/hash-and-input-v1/README.md)
compiled four forms and passed 280 complete-output checks, 980 complete
histogram witnesses, 292,908 ordered update checks and 12 invalid-input
rejections. Twelve reduced-input observations show no clear speed advantage
for the three new forms; mutable count cells use more peak memory. Their raw
source-size measures are retained. Native normalized/formatted counts and a
representative whole-input parser comparison remain pending. These diagnostic
observations do not change catalog timings or chart selections.

[Janet](../experiments/janet/README.md) is being added for all ten workloads.
Ten source drafts have clean compile-only diagnostics with a locally built
Janet 1.42.1 runtime, with original-source lineage and licenses retained.
Correctness, required work, normalized/formatted counts and full timing remain
pending. No Janet profile is included in the measured coverage totals above.

Janet's [149-case bounded-output schedule](../experiments/janet/bounded-v1/README.md)
is prepared with 697 pinned files and six passing pure checker tests. This
starts no Janet process: 142 success contracts await native execution, and seven
malformed-IUPAC cases require capture and a Janet-specific diagnostic adapter.
The owned-process controller and release of the existing shared mutex remain
prerequisites; source counts and timings are unqualified.

The [Odin source review](../experiments/odin/source-review-v1/README.md) inspects
thirteen local/derived bundles across nine workloads and preserves two unchanged
upstream N-body sources. A cited, uncompiled spectral-norm candidate reuses its
scratch vector; parser boundary findings and other performance/idiom hypotheses
remain unmeasured. Raw size measures are retained for all inspected files and
the candidate, with normalized/formatted counts left unqualified.

The [OCaml source review](../experiments/ocaml/source-review-v1/README.md) covers
six local/derived sources and preserves twelve upstream submissions. Four
uncompiled drafts explore exact-record parsing, rolling numeric keys, a shorter
ordinary-library form and bounded FASTA output buffering. Independent Python
oracles reproduce all thirty shared nucleotide/FASTA references and prepare
fourteen extra buffer-boundary cases; the resulting 88 native candidate
executions remain pending. Raw source measures are retained; normalized and
formatted counts and timings remain unqualified.

The [C# source review](../experiments/csharp/source-review-v1/README.md) covers
ten local/derived source bundles shared by twenty JIT/AOT profiles and preserves
nineteen upstream profiles. Five uncompiled drafts address scratch reuse,
nucleotide input/block handling, ordinary and source-generated managed regex,
and reverse-complement short reads. A private-helper diagnostic is prepared;
no new native execution, timing or source-count qualification is claimed.

The additive [source-review coverage report](../experiments/implementation-audit/coverage-v5/README.md)
reconciles all 1,077 current profiles. It records 336 reviewed and 305 unreviewed
editable profiles, 51 unresolved ownership records and 385 protected published
profiles, with 572 distinct editable source bundles. The seven recent Mech
profiles comprise five exact-source inspection reuses and two inspected local
pi-digits derivatives. All 1,070 earlier coverage records remain unchanged;
source-origin and licensing gaps are preserved. These are inspection counts,
not completed optimization or native qualification totals.


Explorer rollover and highlighting now batch pointer changes once per animation frame and update language groups instead of individual dots. Opacity animations and repeated ranking readouts are removed. The [matched profile](../site/publications/chart-hover-v1/comparison.json) and [performance notes](explorer-performance.md#rollover-and-highlighting) retain the measurements; browser data and reproduction payloads are byte-identical. Build `f360c8bf40c2e010` is [live and verified](../site/publications/chart-hover-v1/deployment.json), with all 41 public assets matching and all 42 [live browser checks](../site/publications/chart-hover-v1/live-browser.json) passing.

Ruby 4.0.7 now has separate YJIT and ZJIT configurations across all ten workloads. The [Ruby cohort](../experiments/ruby-jit/README.md) adds 57 complete-process ZJIT observations and 12 YJIT observations, including three first-call compilation measurements of the unchanged compact Fannkuch source. All 69 full outputs passed. Its first-call YJIT median is 316.7 seconds versus the retained default median of 1,079.7 seconds, a 3.41× speedup at the same 46 application LOC. Default-policy observations and original Benchmarks Game authorship remain available. The [comparison](ruby-jit.md) and [reconciled records](../experiments/ruby-jit/results-v1.json) identify stock thresholds, first-call policy, source and runtime hashes, and original measurement dates. No other language was remeasured. The Ruby update was published as build `bdc5daa263faf1c4`, website commit `a60af669f18a9359bfa7b9e11651ebb296abf85d`. The [deployment receipt](../site/publications/ruby-jit-v1/deployment.json) verifies the successful Pages pipeline and all 41 public assets. Thirteen [live Data/export checks](../site/publications/ruby-jit-v1/live-browser.json) and fifteen [live shared-view checks](../site/publications/ruby-jit-v1/live-view-links.json), including the separate Ruby YJIT and ZJIT language pages, passed with no page errors.

Luau 0.743 is admitted for all ten workloads in separate interpreted and arm64 native-JIT series. Twenty-two retained candidates have sixty-six serial, fresh complete-process observations, with all full outputs validated. All 420 bounded cases and four node-allocation/permutation witnesses passed. Application LOC excludes the reusable C++ embedding and general-library bindings; all remain available in source inspection. Original Lua submissions, consulted Lean references, source hashes, licenses, toolchain/dependency versions and timed commands are retained. The [primary admission](../experiments/luau/catalog-admission-v2/receipt.json) and [guarded-error admission](../experiments/luau/catalog-guarded-admission-v2/receipt.json) preserve earlier observations and chart baselines. The guarded reverse-complement form is 2.14× faster interpreted and 2.49× faster with the JIT at two additional normalized source units; its smaller predecessor remains available. The update was published as build `358a442b433b2f90`, website commit `5863365586cde84f0910cbc9ed3f4f5742eb1821`. The [deployment receipt](../site/publications/luau-v1/deployment.json) verifies the successful pipeline, Pages jobs, all 41 assets and the final manifest. All fourteen [live Data/export scenarios](../site/publications/luau-v1/live-browser.json) and thirteen [live shared-view scenarios](../site/publications/luau-v1/live-view-links.json), including both Luau language pages on desktop/mobile, passed with no page errors.

The preceding Data provenance and reproduction update was published as build `329d69947afcb1bf`, website commit `4b28cd2b050ba11c4e998356a4c09e236c921e83`. The [deployment receipt](../site/publications/provenance-final-v1/deployment.json) verifies successful pipeline and Pages jobs, all 41 live assets and the final manifest. All thirteen [live table/export scenarios](../site/publications/provenance-final-v1/live-browser.json) passed against the exact dataset and separately loaded reproduction bytes, including source predecessors and the Mojo reference chain. All eleven [live shared-view scenarios](../site/publications/provenance-final-v1/live-view-links.json) also passed, with no page errors. The [publication validation](../site/publications/provenance-final-v1/validation.json) preserves the remaining historical evidence gaps.

The preceding [compiler-version recovery](../site/publications/compiler-version-recovery-v1/recovery.json) added 21 source-bound version records from existing evidence, increasing coverage from 907 to 928 profiles. It recognizes compiler executables independently of library paths, historical toolchain aliases and multi-line array captures. That provenance update covered 931 profiles after three further evidence recoveries; the timing observations and source bytes are unchanged.

The [successful push record](../site/publications/provenance-final-v1/push.json) identifies the reviewed website commit and assets. A project-specific SSH deploy key now provides authenticated publishing for the website checkout; the [access verification](../site/publications/provenance-final-v1/access-restored.json) records a successful push. The earlier authentication failure and pending publication record remain historical evidence. The verified Git bundle preserves both website commits that were prepared before access was restored.

The [compiler-evidence correction](../site/publications/provenance-precision-v1/preservation.json) separates report-wide Mech compiler metadata from 58 competitor profiles, recovers Rust and Chapel N-body build versions by exact executable and source hashes plus a direct Rust compiler capture for FASTA, and cites both original files and the BSD-2-Clause license of the official Pony Mandelbrot example. The retained index covers 931 version records.

The [source-predecessor audit](../data/source-predecessor-evidence.json) records twelve Prolog profiles' explicitly named Nim predecessors and binds both source bundles for those links and twenty existing C3 links. Labels distinguish local predecessors from published upstream submissions. Earlier unresolved external lineage stays unresolved. These records are included in the published website build.

Three Mojo profiles cite their specific retained upstream implementation files. The scalar spectral-norm chain also includes the upstream file's explicit Benchmarks Game Python #6 reference. The source check matches both pinned Mojo files byte for byte, and all three new citations are reachable. Root license files were not located at either pinned Mojo repository revision; no upstream license grant is inferred. These records are included in the published build. All thirteen [local Data-table and export scenarios](../site/publications/mojo-lineage-v1/local-browser.json) and their live counterparts passed against its exact dataset and reproduction payloads.

The **[Data view](https://mech-lang.org/benchmarks/#v=1&view=data)** exposes all **3,282 distinct recorded runs** with twenty-one sortable columns, sidebar filters, search, row selection and source inspection. CSV and JSON exports cover all rows, filtered rows or checked rows at full precision. JSON includes counted source bundles. Shared links retain filters, sort, pagination, row selection and open source. Full reproduction records load separately from the ordinary chart dataset.

[Original-source metadata](authorship.md) now distinguishes specific upstream files and translation predecessors from collections, workload descriptions and historical copies. All 502 cited implementation/reference URLs were reachable in the recorded primary-host checks, whose individual dates are retained. Every measured source has an immutable retained-file citation and SHA-256. Original lineage is cited for 643 profiles, 34 have explicit suite-authored origin records, and 393 retain unresolved lineage; missing citations do not establish AI originality. Source-license evidence is identified for 662 profiles, partial for 321, and unverified for 84. The [source audit](../data/authorship-audit.json) replaces the earlier broad language-based authorship assumptions.

[Reproduction records](reproduction.md) cover all 1,058 profiles. Recorded release or development-commit information is indexed for 976; the other 82 explicitly lack an established compiler/runtime version in the recovered evidence. Each record retains available build stages, timed commands, inputs, environment, dependency pins, output checks, platform and report hashes. There are 409 recorded recipes and 649 with explicit information gaps. These are historical records, not clean-machine replay claims. The [preservation check](../site/publications/data-reproduction-v1/preservation.json) confirms every non-authorship catalog field is unchanged, including all timings, source bytes, LOC and baselines. That earlier metadata audit reran no benchmarks; the Ruby cohort adds fresh observations while preserving the historical records.

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

The application-LOC correction was published in website build `2b461e654c745e35`. GitLab Pages deployment and all 41 public asset hashes were verified; the live Data and sharing checks each passed 13 cases with no page errors. Publication evidence is retained under `site/publications/source-accounting-v1/`.
