# Fragment-fact interaction: preparation and task boundaries

The fresh three-subject diagnostic supports lower input-capture work in the qualified fragment-fact/worker-credit combination. Input CPU falls from 0.138886 s to 0.119344 s, about 19.5 ms. Main CPU falls by about 19.7 ms. The post-EOF region remains about 40 ms. These perturbed diagnostics do not substitute for the separately established [primary elapsed improvement](../credit-fragment-facts-v1/).

## Nonoverlapping main-thread CPU intervals

| Interval | Credit parent | Combination | Rust |
| --- | ---: | ---: | ---: |
| Before capture | 0.007480 s | 0.007495 s | — |
| Input, including scanner | 0.138886 s | 0.119344 s | 0.133927 s |
| After input, before spawn | 0.040159 s | 0.040203 s | 0.000029 s |
| Actual spawning | 0.000071 s | 0.000078 s | 0.000094 s |

Width-12 worker start after the diagnostic main origin moves from 0.186845 s to 0.167094 s, versus 0.134074 s for Rust. All seven task starts remain close. Actual spawn calls are under 0.1 ms; the remaining delay is in preparation.

## Nested preparation CPU spans

| Span | Credit parent | Combination |
| --- | ---: | ---: |
| borrow_rows | 0.001032 s | 0.001006 s |
| source_scan | 0.072867 s | 0.074021 s |
| selected_join | 0.020662 s | 0.020702 s |
| join_copy | 0.020650 s | 0.020691 s |
| map_prepare | 0.001902 s | 0.001905 s |
| map_kernel | 0.013028 s | 0.013021 s |
| map_finish | 0.002354 s | 0.002359 s |

These spans nest: the scanner is inside input capture, the join-copy span is inside joining, and map preparation/kernel/finalization have their own original boundaries. They must not be added together or added to the main intervals. Separate preparation and worker roots use different clock origins.

## Actual source-width tasks

| Width | Parent count CPU | Combination count CPU / Rust | Rust count CPU | Combination start after main | Combination body finish |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.1439 s | 0.1465 s · 0.492× | 0.2975 s | 0.1672 s | 0.3183 s |
| 2 | 0.1343 s | 0.1358 s · 0.460× | 0.2950 s | 0.1672 s | 0.3090 s |
| 3 | 0.1367 s | 0.1369 s · 0.456× | 0.2999 s | 0.1672 s | 0.3072 s |
| 4 | 0.1374 s | 0.1361 s · 0.455× | 0.2991 s | 0.1672 s | 0.3086 s |
| 6 | 0.1547 s | 0.1499 s · 0.575× | 0.2607 s | 0.1671 s | 0.3205 s |
| 12 | 0.4031 s | 0.4065 s · 1.064× | 0.3821 s | 0.1671 s | 0.5865 s |
| 18 | 0.4087 s | 0.4041 s · 0.991× | 0.4076 s | 0.1671 s | 0.5839 s |

Width 12 and width 18 body endpoints differ by about 2.7 ms. A width-12-only improvement has little isolated headroom before width 18 determines completion. Both long tasks therefore remain counting-side targets.

| Count instructions | Combination | Rust |
| --- | ---: | ---: |
| Width 12 | 4.965 billion | 4.285 billion |
| Width 18 | 4.858 billion | 4.288 billion |

Near CPU parity does not establish a superior loop: the long Mech tasks still execute more instructions, and performance/efficiency-core residence differs. Count completion, map publication, generated-body completion and storage retirement remain separately recorded. Body completion precedes OS thread-wrapper exit; Rust returns maps to main, while Mech publishes inside workers.

## Qualification

Production source `bdb3c511cd552ffc143460d6e1ae7edd04885a7f` and separately instrumented source `cf80a3966ebbaf76439a72b9196eab7e3f1ab879` remain distinct. The preparation and worker probes are copied byte for byte from the retained study. The new diagnostic host preserves the primary guest object, bytecode, descriptor and resource image. Guest SHA-256: `7b1fa85e74cc23a88ce5d9937ad68c7bf003fe5038b4da4e9039171cee3210ea`. Only the copied launcher and its build-script self-pin change; no canonical check is removed. The credit-parent diagnostic is reused with its exact pinned build receipt and identical probes. Exact upstream Rust primary remains untouched; its separately instrumented counterpart retains its original source pin.

All three prefix qualifications and all eighteen balanced full-input executions verify output and every original map update. Six observations per subject preserve all seven source-width intervals: **126 worker intervals**. Every full Mech execution retains seven complete maps, 874,999,961 original updates and 854,497 credited batches under the original finite limits. No primary timing sample comes from this campaign.

The [verifier](verification.json) checks **22 terminal native process receipts**. Every process exits successfully, is reaped and has a closed group with no signals or cleanup errors. No CPU frequency, QoS, priority, affinity or power settings change. Canonical benchmark data remains unchanged.

The result reinforces the next targets: simpler scalar traversal accounting, compact source/view execution, removal of real post-EOF buffer passes and intermediate String construction, followed by changes that help both ordinary long loops. No proposed gain is inferred before its own implementation and measurement.
