# Extended Kalman filter comparisons

This study exposes the retained EKF experiments behind the
[IROS executable article](https://mech-lang.org/iros-r4r-2026/index.html),
alongside its earlier execution-strategy and AOT library measurements.
`provenance.json` identifies each original result, immutable repository
revision and SHA-256. The source snapshots preserve recorded source hashes
or files at the recorded implementation revision. No benchmark is run by
the projection or website build.

The main five-backend campaign uses 500,000 independent f32 filters and
40 measured turns after five warmups, with ten fresh processes for each
backend/mode. It covers the resident numerical instruction evaluator,
scalar JIT, SIMD AOT through a Mech session, eight-worker SIMD JIT and Metal.
The source snapshot is the exact measured program, rather than the later
corrected camera EKF shown by the article's live demo.

CPU implementations, cross-system Metal, session AOT/JIT, direct AOT
libraries and earlier GPU batching retain separate cohorts. Different
publication and synchronization boundaries are disclosed with each study;
the page does not splice their fastest values into a synthetic experiment.
The separate f64 managed-resident episode runs on Apple M3 and remains
Mech-only, without a bare-Rust performance ratio.

The projection preserves 66 result rows and 536 retained timing observations.
Median throughput and unscaled median absolute deviation are recomputed
from every retained sample and checked against the archived summaries.
Seconds per filter-turn use raw elapsed time when present and otherwise
are derived from the recorded throughput. Relative times use the fastest
result in the same cohort and checked/unchecked mode; search does not
change that denominator. These descriptive ratios do not establish
identical runtime guarantees across all implementations.

`tools/ekf_study.py` exports the compact website dataset, raw records and
source snapshots. `tools/build_site.py` includes their identities in the
asset version. The page supports study/mode links, sortable tables,
independent sample and median layers, fixed hover details and CSV exports
of all observations or the current selection.
