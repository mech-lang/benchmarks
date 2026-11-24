# Rebuild the Mechdeflate 81/81 encoder

The level-12 encoder at Mech commit `2b301734f` beat libdeflate and the independent reference on all 81 named cases in both directions of two complete runs. Each direction used 96 balanced blocks per case. The source review records the full margins and correctness checks. [Source commit](https://github.com/mech-lang/mech/commit/2b301734fb43a4abff0d38d68d881e2bf85bd969) · [Qualification report](https://github.com/mech-lang/mech/pull/999#issuecomment-7122223610).

The recipe contains all 225 encoder settings and pins the codec source, compiler driver and Cargo lock, native object, canonical bytecode, metadata, timing worker, and stripped deployment executable. The four profiles contain register weights and block layouts for the matcher and path scorer. Their filenames are SHA-256 digests. [Recipe](recipe.json) · [Profiles](profiles/).

## Rebuild from source

Use Python 3.11 or later, Rustup, and Xcode on Apple Silicon. The exact link was verified with Xcode 26.0.1 (17A400), macOS SDK 26.0, and Apple linker ld-1221.4 on an M1 running macOS 15.6.1. Start in this benchmark checkout and substitute the path to your Mech checkout.

```sh
git -C /path/to/mech fetch origin pull/999/head
git -C /path/to/mech switch --detach 2b301734fb43a4abff0d38d68d881e2bf85bd969
rustup toolchain install nightly-2026-03-03 --profile minimal
python3 experiments/mech/mechdeflate-81-v1/rebuild.py \
  --mech-root /path/to/mech --output /tmp/mechdeflate-81-rebuilt
```

Use a fresh output directory. The rebuild compiles the locked driver, checks all four profile hashes, and emits `frontend/program.o`, `frontend/program.mecb`, and `frontend/metadata.json`. It links the encoder against the pinned prebuilt host support used in qualification and verifies the stripped `compressor` hash. `reproduction.json` records those checks and the rebuilt compiler hash. The compiler binary can embed checkout paths, so the byte-for-byte checks cover the three encoder artifacts and linked executable. [Host support manifest](host-support.json).

## Recheck the timings

The matched Mech control averaged 0.031151% and 0.008715% positive slowdown versus libdeflate on the fixed 18-case cohort in the two complete runs. The winning build averaged 0% in both. The recorded source-through-link time was 2.217 s with compiler and host support prebuilt. [Per-order cohort margins](case-margins.json) · [Protected wins](protected-floor.json) · [Raw evidence manifest](evidence/manifest.json).

From the benchmark checkout, recompute the recorded outcome and prepare the pinned workers and fixtures.

```sh
python3 experiments/mech/mechdeflate-81-v1/verify_results.py
python3 experiments/mech/mechdeflate-81-v1/replay_timings.py \
  --output /tmp/mechdeflate-81-timing --prepare-only
```

For a fresh measurement on Apple Silicon macOS, omit `--prepare-only` and use a new output directory. The replay uses the recorded workers and verifies their output against the original 81-case fixtures. The result records the win counts for both orders.
