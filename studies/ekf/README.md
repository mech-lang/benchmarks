# Mech extended Kalman filter metrics

The metrics page has one row per Mech execution path, with its execution time,
closest comparable external peer, peer time and Mech/peer multiple. External
implementations supply reference measurements; they are not standalone result
rows and there is no peer-selection interface.

The visible summary retains the single-worker resident numerical evaluator,
scalar JIT and managed SIMD AOT paths, the eight-worker fused and per-turn JIT
paths, and the native Metal path. It uses the peer campaign's own Mech result
for multi-worker JIT and Metal, rather than showing duplicate backend-campaign
measurements as separate variants. Checked execution is the default;
unchecked and both-mode views remain available.

A peer must be external to Mech and share the recorded campaign, execution
category, publication boundary and checking mode. The fastest eligible peer
supplies the reference: Julia SIMD.jl for fused CPU JIT, Taichi LLVM CPU for
per-turn CPU JIT, and Rust with hand-written MSL for Metal. Single-worker
backend measurements have no external control in their campaign and retain
absolute timings without an invented ratio. The three checked comparisons
also appear in the main metrics summary under Applications.

The underlying evidence is the three retained datasets plotted by the
[IROS executable article](https://mech-lang.org/iros-r4r-2026/index.html):
Mech backends, CPU implementations and native Metal implementations.
`provenance.json` records original results, immutable source revisions and
SHA-256 hashes. Source snapshots retain recorded hashes or the file at the
recorded implementation revision. The exact measured Mech source is distinct
from the later corrected camera EKF in the article's live demo.

All 40 underlying results and 400 samples remain unchanged and downloadable.
The summary selects 12 Mech result rows across six paths and two checking
modes, with 120 Mech samples. Medians and unscaled MAD are recomputed from
retained samples. Seconds per filter-turn use raw elapsed time when present,
or recorded throughput otherwise. Compilation and setup are outside these
warm numerical kernel timers; they do not measure the full reactive host's
admission, recording and output-delivery lifecycle.

CPU JIT paths include Julia SIMD.jl, NumPy/Numba, Taichi and Halide's
runtime-compiled callable. CPU AOT paths include Rust, Futhark/ISPC and Mojo.
The recorded commands and sources establish those execution choices;
Halide's `compile_to_callable` is documented in its
[Pipeline API](https://halide-lang.org/docs/api/generated/Pipeline.html).
Fused CPU blocks and per-turn publication are distinct reference categories.

`tools/ekf_study.py` verifies and projects evidence without running benchmarks.
The page preserves sortable columns, shared mode/filter/sort selections,
Mech-only sample plots, fixed hover details and full-precision CSV exports.
