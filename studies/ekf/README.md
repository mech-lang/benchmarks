# IROS extended Kalman filter comparisons

This study exposes the three retained comparison datasets plotted by the
[IROS executable article](https://mech-lang.org/iros-r4r-2026/index.html):
Mech execution backends, CPU implementations and Metal implementations.
`provenance.json` identifies each original result, immutable repository
revision and SHA-256. Source snapshots preserve recorded hashes or files at
the recorded implementation revision. No benchmark is run by the projection
or website build.

The five-backend campaign uses 500,000 independent f32 filters and 40
measured turns after five warmups, with ten fresh processes for each
backend/mode. It covers the resident numerical instruction evaluator,
scalar JIT, SIMD AOT through a Mech session, eight-worker SIMD JIT and Metal.
The retained source is the exact measured program, rather than the later
corrected camera EKF used by the article's live demo.

The CPU and Metal comparisons retain their own cohorts, source identities
and publication boundaries. Their measurements are never substituted into
the five-backend campaign. The article's source-reuse chart uses a subset
of the same CPU and Metal records; it is not an additional experiment.
These numerical kernel timings do not measure the full reactive runtime's
admission, recording and delivery lifecycle.

The projection preserves 40 result rows and 400 timing observations.
Median throughput and unscaled median absolute deviation are recomputed
from every retained sample and checked against the archived summaries.
Seconds per filter-turn use raw elapsed time when present and otherwise
are derived from recorded throughput. Relative times use an external
peer in the same cohort, execution category and checked/unchecked mode.
CPU JIT peers are Julia SIMD.jl, NumPy/Numba, Taichi LLVM CPU and Halide's
runtime-compiled callable; CPU AOT peers are Rust, Futhark and Mojo. The
recorded launch commands and implementation sources establish these paths.
Halide's `compile_to_callable` performs JIT compilation, as documented in
the [Pipeline API](https://halide-lang.org/docs/api/generated/Pipeline.html).
Metal peers use their native GPU
paths. The default reference is the fastest external peer in each
category/mode, with a selector for every other eligible peer. Mech is
never its own reference, and search does not change the denominator.
The Mech-only backend study shows absolute timings without peer ratios.
These descriptive kernel ratios do not establish identical runtime
guarantees across all implementations.

`tools/ekf_study.py` exports the compact website dataset, raw records and
source snapshots. `tools/build_site.py` includes their identities in the
asset version. The page supports study/mode links, sortable tables,
independent sample and median layers, fixed hover details and CSV exports
of all observations or the current selection.
