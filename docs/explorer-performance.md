# Explorer performance

The explorer's browser payload contains the fields needed for charts, filters,
source inspection and displayed audits. The complete measurement and admission
records remain in the [canonical catalog](../data/benchmarks.json). Projection
does not recalculate observations or remove programs, samples or source files.

The build emits compact JSON and a deterministic gzip sidecar. GitLab Pages
[serves precompressed assets](https://docs.gitlab.com/user/project/pages/introduction/#serving-compressed-assets)
according to the browser's accepted encodings. The data URL carries the same
build version as the application; the version includes the projection code and
emitted data. Ordinary JSON remains available for clients without compression.

Chart updates reuse derived selection data. Layer, profile and axis-range changes
redraw the chart without rebuilding the language controls, tables and rankings.
Recorded sample circles are reused across selections, with shared handlers on
their current layer. Hidden samples are detached from the chart; each visible
run still has its own coordinates, readout, source action and keyboard target.
SVG labels are inserted together, measured together, then positioned, avoiding
one layout per label. Hover handlers reuse a language-to-mark index. Resize
handling ignores changes that leave the chart's width and responsive layout
unchanged.

Density uses separable Gaussian factors instead of evaluating a two-dimensional
exponential for every sample in every cell. Every observation still contributes
to every cell with its original weight, including coincident observations and
distant tails. The field is reused while its inputs and domain are unchanged.

## Validation

The projected and canonical catalogs produce identical endpoints, chart
coordinates, covariance, rankings, fixed domains and language comparisons.
Checks cover 971 unique programs, 900 complete source files, 1,178 rendered LOC
audits, 1,660 source/link cases, 48 selection models, 1,392 language comparisons
and 4,624 inspector selections. Ordered source navigation and every recorded
sample are preserved. The original canonical catalog is unchanged.

The [validation record](../site/publications/explorer-performance-v1/validation.json)
binds the tested source and generated assets to the captured check outputs.
Independent density checks compare the optimized estimator with the direct
two-dimensional formula. The layer and ranking suites also exercise selection
changes, cache invalidation, independent visibility, hover restoration and
target-relative ranking origins.

The browser audit uses the same host, Chrome version, loopback server and
instrumentation before and after the change. Each configuration has three fresh
browser contexts: desktop at 1,280 px, mobile layout at 390 px, and the mobile
layout with 4× CPU throttling. Loopback timing excludes Internet latency and uses
uncompressed data for both builds. CPU throttling is a simulation, not a physical
phone measurement. Event timings measure synchronous work; separate measurements
wait for two animation-frame callbacks, allowing intervening rendering work.
They do not guarantee that every CSS transition has completed. Response JSON time
includes body consumption and parsing. Heap readings do not force garbage
collection.

## Browser measurements

The [per-run measurements and browser checks](../site/publications/explorer-performance-v1/performance.json)
compare build `80f03cc4ba6ce434` with `381120eba12efd76`. Values below are medians
of three runs on an Apple M1 Mac mini with 8 GiB RAM and Chrome 155. Control rows
report synchronous event processing; readiness includes loading and initialization.
Later dataset additions are outside this comparison.
The evidence also retains elapsed times through two animation-frame callbacks,
layout counts and individual observations.

| Measurement | Desktop before → after | Mobile layout, 4× CPU slowdown, before → after |
| --- | ---: | ---: |
| Explorer ready | 403 → 216 ms | 1,253 → 671 ms |
| JS heap after initialization | 70.1 → 13.7 MiB | 72.0 → 13.7 MiB |
| Resource filter | 58 → 44 ms | 226 → 170 ms |
| Enable density | 185 → 60 ms | 703 → 244 ms |
| Open language page | 149 → 120 ms | 565 → 447 ms |
| Reset | 47 → 46 ms | 186 → 153 ms |

Desktop reset changed little. Opening a language page remains the slowest
measured control under CPU throttling. Repeated-hover measurements include a
geometry lookup; its occasional layout flush is retained in the individual
observations and distinguished from the separately measured pointer handlers.

Real pointer and keyboard checks passed at 390 px and 1,280 px, including median
highlighting, sample readouts and source selection after layer and filter
changes. Samples Off attaches no sample dots. Independent layers, global
statistics, axis ranges, mobile filters and language-page navigation remain
covered by the regression checks.

## Payload

The previous browser JSON was 73,826,163 bytes. The projected JSON is 8,335,571
bytes, an 89% reduction before compression. Its gzip sidecar is 1,210,607 bytes.
All 900 source files remain available in the inspector. The canonical catalog
retains its original bytes and hash.

## Publication

Build `381120eba12efd76` was published at
[mech-lang.org/benchmarks](https://mech-lang.org/benchmarks/).
[Deployment verification](../site/publications/explorer-performance-v1/deployment.json)
passed all 35 live assets and the final manifest on October 15, 2026 at
04:05 UTC. The [compression check](../site/publications/explorer-performance-v1/gzip.json)
confirmed an exact 1,210,607-byte gzip response decoding to the tested JSON.
A [fresh mobile browser](../site/publications/explorer-performance-v1/live-browser.json)
also received that compressed body and passed sample visibility, language-page
and filter checks with no page errors.

The first Pages deployment stalled after its asset build. An
[identical-content retry](../site/publications/explorer-performance-v1/publication-retry-v1.json)
completed successfully; both revisions have the same complete website tree.

The subsequent APL coverage and timing-alias update, build `72094b4bd8833f60`,
has its own [verified deployment](../site/publications/apl-timing-aliases-v1/deployment.json).
All 35 live assets matched on October 15 at 05:29 UTC. A
[fresh mobile check](../site/publications/apl-timing-aliases-v1/live-browser.json)
verified all 2,835 selected runs, Samples Off, language pages and resource
filters without page errors. Its 8,369,808-byte JSON arrived as a 1,213,325-byte
gzip body. This deployment check does not extend the earlier performance
comparison to the enlarged dataset.

## Second interaction pass

Build `7bba6e95588940c0` reduces work during view and layer changes:

- Rankings skips the hidden scatter plot and results table. Reset selects its
  destination before rendering once; returning to a chart refreshes its geometry.
- Language comparisons select their endpoints directly, avoiding covariance
  contours that the relative-comparison table never uses.
- Label placement checks nearby rectangles through a spatial index. Candidate
  order, overlap summation order, scoring, ties and mobile crowding are preserved.
- Global covariance is calculated when its overlay is displayed. Changing an
  already visible density layer between Dim and Highlight updates contrast in
  place, preserving points, cells, keyboard focus and hover details.

The [matched measurements](../site/publications/explorer-performance-v2/comparison.json)
compare the frozen live build `72094b4bd8833f60` with this build. Both use the
same byte-for-byte browser dataset, Chrome 155 and Node 24 on the separate M1 Mac
mini. Each configuration has three fresh, serial browser contexts using the
same loopback server and [profiling harness](../site/publications/explorer-performance-v2/profile.mjs).
The language timing host performs no browser profiling. The throttled mobile
configuration simulates slower hardware; it is not a physical phone measurement.

| Synchronous interaction | Desktop before → after | Mobile layout, 4× CPU slowdown, before → after |
| --- | ---: | ---: |
| Resource filter | 44 → 32 ms | 170 → 128 ms |
| Enable density | 50 → 40 ms | 196 → 157 ms |
| Density Dim → Highlight | 34 → <1 ms | 138 → 1 ms |
| Open Rankings | 51 → 16 ms | 190 → 56 ms |
| Reset Rankings | 79 → 11 ms | 201 → 35 ms |
| Return to All benchmarks | 48 → 29 ms | 179 → 116 ms |
| Language axes: medians | 72 → 54 ms | 226 → 163 ms |
| Language axes: all samples | 57 → 38 ms | 166 → 130 ms |
| Open program details | 66 → 54 ms | 210 → 173 ms |
| Open language page | 109 → 104 ms | 403 → 396 ms |

Language-page opening remains the slowest measured interaction and changed
little. Initialization changed from 190 to 198 ms on desktop and 674 to 640 ms
under mobile CPU throttling. These measurements establish interaction gains,
not a uniform improvement to every operation. Raw observations retain ranges,
CPU samples, layout counts and elapsed times through two animation-frame
callbacks. Sub-millisecond synchronous work still requires a rendering frame.

The [regression receipt](../site/publications/explorer-performance-v2/validation.json)
includes 1,300 exact label placements against the previous exhaustive search,
800 relative comparisons, 960 complete models, 432 layer renders and canonical
catalog projection checks. A [Chrome comparison](../site/publications/explorer-performance-v2/behavior-v2.json)
matches 25 visible states at both 390 and 1,280 px, including samples, medians,
density, global statistics, axes, rankings, filters, language pages and source
inspection. Hidden chart geometry and tables are refreshed when shown again.

Uncollected heap readings varied with garbage-collection timing, including a
higher candidate reading in the throttled configuration. A separate
[retention diagnostic](../site/publications/explorer-performance-v2/retention.json)
explicitly collects garbage outside timing measurements: initial retained heap
is 13.5 → 13.4 MiB. After 20 view/layer/reset cycles it is 18.3 → 18.2 MiB,
with identical DOM-node and listener counts and little growth
after warmup. This pass does not claim a retained-memory reduction.

Build `7bba6e95588940c0` was
[published and verified](../site/publications/explorer-performance-v2/deployment.json)
at [mech-lang.org/benchmarks](https://mech-lang.org/benchmarks/). All 36 live
assets and the final manifest matched on October 15 at 14:05 UTC. The
[compression check](../site/publications/explorer-performance-v2/gzip.json)
and [fresh mobile browser](../site/publications/explorer-performance-v2/live-browser.json)
passed with the unchanged dataset, all 2,835 selected runs, Samples Off,
language pages and resource filters, with no page errors.

Build `caf8560f1e184762` retains these optimizations and renders recorded
samples as solid dots in each language's color. Its
[deployment check](../site/publications/sample-dots-v1/deployment.json) matched
all 36 live assets, and the
[fresh mobile browser check](../site/publications/sample-dots-v1/live-browser.json)
confirmed all 2,835 markers were filled, Samples Off removed them, and no page
errors occurred. The interaction measurements above apply to build
`7bba6e95588940c0`; they were not repeated for this marker-style change.

## Rollover and highlighting

Build `f360c8bf40c2e010` batches pointer changes into one animation-frame update.
Leaving one dot for another no longer clears and reapplies the whole chart
between events. Consecutive sample nodes share language groups, so highlighting
changes those groups and an inherited contrast value instead of rewriting each
run. Paint order and coordinates are preserved.

Hit testing resolves the final pointer position once per frame, before SVG
style writes. Hover covariance paths are reused within a render. Opacity changes
are immediate; thousands of concurrent opacity transitions are removed. Repeated
readouts are skipped in both scatter and ranking charts. Replacing or hiding the
chart cancels pending hover work; pointer exit restores keyboard focus and its
readout.

The [matched measurements](../site/publications/chart-hover-v1/comparison.json)
use the same 3,024 default-chart dots, unchanged dataset/reproduction payloads,
Chrome 155.0.8059.85 and serial contexts on the same Mac. Each configuration
has three repetitions. Mobile uses a 390 px viewport with simulated 4× CPU
slowdown, rather than a physical phone.

| Native pointer sweep, 70 moves | Before | After | Less renderer work |
| --- | ---: | ---: | ---: |
| Desktop, 1,280 px | 3,995 ms | 301 ms | 92% |
| Mobile layout, 4× slowdown | 7,061 ms | 914 ms | 87% |

These are total Chrome renderer task times for each sweep, including deferred
hover and style/layout work. They are not per-event response times or frame-rate
guarantees. Raw [before](../site/publications/chart-hover-v1/before.json) and
[after](../site/publications/chart-hover-v1/after.json) records retain every
observation, frame interval, long task, mutation count and CPU setting. The
[profiling harness](../site/tests/hover-performance.mjs) also includes deliberately
dense dispatch bursts: 200 within-language transitions fall from about 2.5 million
chart mutations to about 400 when first entering a language. Once highlighted,
200 transitions within that language produce zero chart mutations. A 200-move
marker burst performs one coordinate-transform lookup instead of 201.

The [browser regression](../site/publications/chart-hover-v1/behavior-after.json)
covers desktop/mobile median and sample hover, keyboard focus, Samples Off,
independent density/global layers, language-page restoration, retired callbacks,
native pointer input and selection of the exact clicked implementation. The
[control](../site/publications/chart-hover-v1/behavior-before.json) provides 38
settled states for exact comparison of geometry, paint, domains, readouts and
selections. Independent layer tests retain 432 renderer cases. No language
benchmark, source, LOC or timing observation changes.
