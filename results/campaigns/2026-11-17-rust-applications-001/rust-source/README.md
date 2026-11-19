# Independent Rust task controls

This package implements the resident task definitions without linking Mech or
reading oracle answers. The Python oracles independently check complete output
trajectories, including order, duplicate rows, nulls, shapes, state evolution,
rejected/abandoned turns and retained snapshots. Unicode segmentation uses the
pinned `unicode-segmentation` implementation. EKF uses fixed row-major matrices
and the conventional Joseph covariance update.

The resident timer includes typed input validation, change detection, owned
input admission, computation and publication. An unchanged pure input may reuse
its previous result. Stateful tasks always advance. Requested snapshots retain
their published output inside the timer and are checked after later turns.
Weak ownership probes check that published output buffers are released after
the instance and retained snapshots drop. Scalar outputs own their value inline.
Preparation, warmup on a separate instance, final serialization and teardown
remain outside the resident block. Allocation counters cover the measured block.

Rust uses native ownership. It does not emulate Mech's resource ledger, scheduler
or managed artifact. These are task comparisons, not matched implementation
attribution or a claim to the fastest possible Rust solution. In particular,
Rust compiler preparation is not given a fictitious Mech artifact/JIT time.

The compressor uses genuine Rust `zlib-rs` 0.6.8 at its maximum level 9. Mech's
level-12 compressor can produce a different stream. Both must preserve input and
prefix aliases and publish a separate, complete valid stream. Output allocation,
compression, prefix copying and scratch destruction are included in the Rust
call; file IO and returned-output destruction are excluded. An earlier owned
output is held across the next call. Python independently inflates every result,
requiring exact input restoration, EOF, prefix preservation and no trailing data.
Compare output size alongside time; differing compression quality is an outcome,
not an interchangeable codec setting.

`run_rust_suite.py` rebuilds and pins the package, compiler, dependencies and
binary hashes in every campaign. It randomly interleaves fresh Mech and Rust
workers within each case/fork block. All observations are retained. It also
measures complete 1/2/4-process groups, native build/footprint, full K-nucleotide
and all 12 compressor inputs. K-nucleotide uses the unchanged retained upstream
Rust #7 source and its authorship/license record. Full N-body has its separately
retained upstream Rust #3 paired campaign.

```sh
cargo +nightly-2026-03-03 build --release --locked --manifest-path suite/controls/rust/Cargo.toml --target-dir .local/rust-controls-target
python3 tools/qualify_rust_controls.py --binaries .local/rust-controls-target/release --output .local/NEW-QUALIFICATION
python3 tools/run_rust_suite.py --group resident --worker .local/worker/worker.json --forks 5 --cycles 1000 --output results/campaigns/NEW-RESIDENT
python3 tools/run_rust_suite.py --group concurrent --worker .local/worker/worker.json --forks 5 --output results/campaigns/NEW-SCALING
python3 tools/run_rust_suite.py --group native --worker .local/native-worker/worker.json --forks 5 --output results/campaigns/NEW-NATIVE
python3 tools/run_rust_suite.py --group applications --worker .local/worker/worker.json --application-worker .local/applications/worker.json --fasta /path/to/knucleotide-25000000.fasta --corpus /path/to/reymont --forks 5 --output results/campaigns/NEW-APPLICATIONS
```

Every output directory must be new. Full application inputs are never replaced
with smoke inputs. The resident default uses 1,000 complete schedule cycles for
enough Rust work to time; the fixed EKF and suspended state-machine trajectories
retain their catalog cycle counts. Tiny state-machine clocks are particularly
sensitive to timer resolution; inspect all forks rather than treating the ratio
as a stable optimization target. Shared CI runners check correctness only.
