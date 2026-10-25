# Aligned probe policy diagnostic

This diagnostic tests a private table's probe policy before a native Mech
compiler trial. It is never linked into Mech and does not change a benchmark
submission. The copied program constructs all seven full histograms. A
sixteen-byte u64-key/u64-count table retains full-key equality, eight-byte NEON
control comparisons, the same folded hash, mirrored controls and 7/8 growth.
The only selected policy difference is aligned eight-bucket group starts and
nonwrapping candidate lanes.

Both ordinary and aligned tables pass the three storage-oracle tests, covering
complete maps, growth/replacement, zero/MAX counts, colliding fingerprints and
wrapping. All 72 full/prefix diagnostic executions produce exact reference
stdout. Current Mech retains its secured startup, seven workers and complete
update counts. No warmups or observations are excluded.

| Full-input subject, median of 6 | Seconds | × exact upstream Rust |
|---|---:|---:|
| Exact upstream Rust | 0.5595 | 1.000× |
| Current Mech control | 0.6973 | 1.246× |
| LLVM, ordinary table | 0.5791 | 1.035× |
| LLVM, aligned table | 0.5550 | 0.992× |
| Rust/Cranelift, ordinary table | 3.9511 | 7.061× |
| Rust/Cranelift, aligned table | 3.9434 | 7.047× |

The LLVM median changes by −4.15%; its standard deviations and Rust's are
large, and this single cohort does not establish a repeatable gain. The
Cranelift median changes by −0.20%, essentially unchanged. This diagnostic
retains Rust's generic table interfaces; Mech's generated source CFG has already
removed much of that abstraction overhead. Neither Rust/Cranelift result is
Mech or a Cranelift performance ceiling. The actual Mech trial additionally
changes candidate-address scheduling and must be measured independently.

On the independent prefix, ordinary/aligned LLVM medians are 0.0209/0.0206 s
(1.075×/1.060× Rust), ordinary/aligned Rust/Cranelift 0.0540/0.0548 s
(2.779×/2.820×), Mech 0.0878 s (4.516×), and Rust 0.0194 s (1.000×).

[timing-results.json](timing-results.json) retains each sample and all six fixed
orders. Both diagnostics use the exact July 31 nightly compiler, component and
dependency artifacts recorded in [execution-plan.json](execution-plan.json).
The protected upstream Rust control and Mech's independently built standalone
executable remain unchanged; this is a within-diagnostic policy comparison.

The initial build incorrectly selected the March compiler for July dependency
artifacts and failed before timing; its incompatible-version errors are retained.
The corrected driver completes all four builds and both LLVM oracle suites,
then stops before timing because a cohort parent directory was missing. The
measurement-only driver creates those directories and reuses the exact completed
builds, retaining both earlier controllers and replacing no measurements.
All native activity is serial under the shared timing lock, with bounded
owned-process cleanup. Canonical benchmark data is untouched.
