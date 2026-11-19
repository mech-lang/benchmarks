# Mech extended Kalman filter metrics

The public summary has exactly seven Mech rows: Resident, JIT, AOT,
managed AOT, GPU, batched GPU and eight workers. Each row shows Mech's time,
its closest comparable external peer, the peer's time and Mech/peer multiple.
Other implementations are reference data, not standalone result rows. The
page has no study browser or reference selectors.

The default chooses checked measurements when available. The archived
one-submit batched GPU measurement is unchecked and is explicitly labeled.
Each row retains its machine, precision, population, source and timer scope.
Resident is the managed f64 runtime on Apple M3; it is not the separate f32
numerical instruction evaluator. All other displayed paths use the archived
Apple M1 measurements. Different populations and host boundaries are not
silently combined into one experiment.

A peer must share its Mech row's campaign, execution category, publication
boundary and checking mode. Julia SIMD.jl is the fused eight-worker JIT peer.
Rust with hand-written MSL is the per-turn Metal peer. The direct AOT library
experiment uses the same checked loader/ABI and one host thread; its Rust
control is scalar while Mech's selected AOT uses four-wide SIMD, as disclosed
in the article and the recorded protocol. This is a library diagnostic, not
the eight-worker SIMD language experiment. Other paths retain absolute times
without a fabricated cross-campaign or non-equivalent runtime ratio.

The three paired checked rows also appear under Applications in the main
metrics overview. The seven-row page preserves source links, sortable columns,
shared selections, Mech-only CSV exports and optional samples. Sample plots
normalize Mech observations by their own peer median rather than putting
unrelated hardware or workload sizes on a shared absolute-performance scale.

The [IROS executable article](https://mech-lang.org/iros-r4r-2026/index.html)
provides the backend, CPU, Metal and AOT library results. The retained archive
supplies the explicitly labeled batched GPU record, and the canonical resident
campaign supplies the managed runtime row. `provenance.json` identifies raw
records, repository revisions and SHA-256 hashes. Source snapshots preserve
recorded hashes or clearly identify the archive snapshot when the measured
compiler/source identity was not recorded.

The underlying projection preserves 45 results and 431 observations. The
selected paths contain 11 result rows across available checking modes and
97 Mech samples; the default seven rows contain 57 samples. No timing is
rerun, pooled or edited. Medians and unscaled MAD are recomputed from retained
observations. Seconds per filter-turn use raw elapsed time when present and
recorded throughput otherwise. Compilation and setup remain outside native
kernel timers; the Resident timer includes its managed execution boundary.

`tools/ekf_study.py` verifies and projects the evidence. CPU JIT paths include
Julia, NumPy/Numba, Taichi and Halide's runtime-compiled callable; CPU AOT paths
include Rust, Futhark/ISPC and Mojo. Their commands and sources establish these
choices. Halide's `compile_to_callable` is described in the
[Pipeline API](https://halide-lang.org/docs/api/generated/Pipeline.html).
