# TypeScript nucleotide input and mutable-value candidates

The first rolling-number candidate has a full N25m median of 29.883s
(58.16× retained Mech AOT), versus 44.791s (87.17×) for its matched substring
control. The retained Mech AOT denominator is 0.513828s on the same full workload.
Those measurements remain unchanged and do not establish these new proposals.

Three source hypotheses isolate ordinary input and hash-map idioms:
mutable count cells with the existing line parser; whole byte-buffer parsing
with numeric values; and their combination. All seven growing Maps still count
every overlapping occurrence. The source owns exact first-THREE token selection,
comments, CR/LF, case conversion, all decoding, sorting and complete output. No
benchmark-specific native helper or narrowed 36-bit key is introduced.

The original [proposal](proposal.json) records their uncompiled creation state.
The subsequent [native qualification](native-v1/results.json) compiled all three
and their rolling parent with the retained strict TypeScript 7.0.2 configuration
and Node 24.19.0. All 280 complete-output checks and 12 invalid-input rejections
passed. Separate, untimed Map diagnostics retain every ordered update and final
entry for all seven widths: 980 complete histograms and 292,908 updates. The
[offline reconciliation](reconciliation-v1.json) reproduces those checks without
native execution. Seven corruption checks reject missing histograms, query-only
results, omitted updates, narrowed high keys and inconsistent mutable-cell work.

The diagnostic preloader observes unchanged emitted JavaScript with a Map
subclass and count-cell proxies. Each instrumented process produces exactly
the same complete output as its plain counterpart. Every quantitative command
uses plain Node and the emitted application without that preloader. The
[execution review](execution-review-v1.json) binds exact typed sources, emitted
JavaScript, source maps, strict configuration, standard-library imports and the
separate diagnostic/timing boundaries. This review is by the authoring agent;
independent source/count review remains pending.

## Reduced input results

The [fixed pilot](pilot-v1/plan.json) runs three shuffled rounds of all four forms,
one fresh process at a time under the common mutex. Startup, input, all seven
maps, sorting, complete output and shutdown are included. Input contains the
first one million retained THREE bases; preceding FASTA records are omitted.
All twelve outputs and process-closure checks passed.

| Form | Median seconds | Sample SD | × Mech AOT | Peak RSS |
| --- | ---: | ---: | --- | ---: |
| Rolling parent | 0.2763 | 0.0014 | Unavailable | 99.1 MB |
| Readline + count cells | 0.2747 | 0.0016 | Unavailable | 119.5 MB |
| Byte buffer + numbers | 0.2761 | 0.0052 | Unavailable | 99.1 MB |
| Byte buffer + count cells | 0.2750 | 0.0025 | Unavailable | 115.5 MB |

There is no qualified Mech AOT timing on this exact reduced input. Full-size
denominators cannot be substituted; every pilot observation retains a null
ratio and this reason. Raw samples and full process/power captures are in the
[pilot results](pilot-v1/run-v1/results.json). Power/process snapshots bracket
the cohort; they are not continuous per-sample monitoring.

These close results do not establish a useful speed advantage. Mutable values
reduce Map.set calls but add objects and indirection, and use more peak memory
in this cohort. Whole-input parsing costs remain unresolved because the pilot
omits preceding FASTA records. No new full-size candidate is selected from this
pilot, and none of these observations are admitted to the chart.

## Source measures and remaining work

All authored helpers remain in the TypeScript application. The
[source measures](source-measures-v1.json) use the catalog's existing pinned
byte/character/physical-row/gzip/BPE implementation on each entire source file.
Comments and blank rows are retained in these raw metrics.

| Form | Physical rows | UTF-8 bytes | gzip bytes | BPE tokens |
| --- | ---: | ---: | ---: | ---: |
| Rolling parent | 75 | 2,585 | 1,082 | 699 |
| Readline + count cells | 81 | 2,787 | 1,156 | 742 |
| Byte buffer + numbers | 104 | 3,811 | 1,311 | 1,089 |
| Byte buffer + count cells | 110 | 4,013 | 1,385 | 1,132 |

All three additions are larger under these raw measures. BPE tokens are
tokenizer-dependent, not programming-language lexer tokens. Normalized source
units require native owner rules for switch/case, structured type aliases and
typed assertions in these exact sources. Pinned native formatting qualification
also remains pending; physical rows are not substituted for either count.

A representative whole-input parser comparison, native source-count extension,
independent ownership/count review, any justified full-size preselection and
guarded catalog admission remain separate work. Current edits identify the
known Codex GPT-6 family; original citations and exact-model uncertainty remain.
