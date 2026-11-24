# Mechdeflate Cranelift retest

On Apple M1 with macOS 15.6.1, PR #1000 emitted both pinned level-12 encoders through Cranelift. Both objects, canonical bytecode files and descriptor files reproduced byte for byte. These results supersede the earlier M3 report for this branch. [Compiler revision](https://github.com/mech-lang/mech/commit/62363b4a341860b04bbfe11d0a1cb2ea9e3b2532) · [Exact recipe](recipe.json).

## 81-case qualification

The short-prefix build won **81/81 against both references in both orders** on the same Apple M1. Its smallest elapsed-time margins were 0.645% against libdeflate and 5.590% against the second reference. The raw verifier recomputed all 1,965,312 observations from the two 96-block orders. [Compiler revision](https://github.com/mech-lang/mech/commit/e46c6df7ee23445523cb0e30d7820b17e17526e0) · [Exact recipe](short-prefix/recipe.json) · [All case margins](short-prefix/scores.json) · [Raw observations](short-prefix/observations.json).

The build passed 162 exact byte and alias checks and 12 recoveries across 6 failure cases. It used 5,040 bytes of peak native stack. A clean rebuild produced the same 157,832-byte native object, canonical bytecode and descriptor. The packet includes the exact timed worker. The rebuilt worker has a different executable hash. With dependencies prebuilt, median source-to-executable time was 2.926 s across three rebuilds. [Native checks](short-prefix/native-checks.json) · [Build receipt](short-prefix/rebuild.json).

```sh
python3 experiments/mech/mechdeflate-cranelift-v1/rebuild.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/short-prefix/recipe.json \
  --mech-root /path/to/mech --output /tmp/mechdeflate-short-prefix
python3 experiments/mech/mechdeflate-cranelift-v1/replay.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/short-prefix/recipe.json \
  --suite 81 --output /tmp/mechdeflate-short-prefix-timing
python3 experiments/mech/mechdeflate-cranelift-v1/verify.py \
  --record experiments/mech/mechdeflate-cranelift-v1/short-prefix \
  --output /tmp/mechdeflate-short-prefix-verify
```

To retime the rebuilt worker, add `--build /tmp/mechdeflate-short-prefix --control-build experiments/mech/mechdeflate-cranelift-v1/actors` to the replay command.

## Initial 81-case retest

| Build | libdeflate forward | libdeflate reverse | Reference forward | Reference reverse |
|---|---:|---:|---:|---:|
| standard | 81/81 | 80/81 | 80/81 | 80/81 |
| direct-4 | 79/81 | 79/81 | 80/81 | 80/81 |

The same pinned inventory uses 96 balanced blocks per case in each order. A win requires the paired geometric mean of elapsed-time ratios to fall below one. The verifier recomputes all 1,965,312 observations. Both roles use exact reference streams, independent inflation, and unchanged input and borrowed-output aliases. [All case margins](81-case-margins.json) · [Results by order](81-scores.json) · [Raw observations](observations.json).

## Full Silesia at level 12

The short-prefix encoder also ran the full 12-file level-12 clock. It won 10/12 forward and 10/12 reverse against libdeflate, and 11/12 forward and 11/12 reverse against the second reference. The summed per-file medians were 28.755 s, 33.670 s and 32.616 s, respectively. All 12 streams were byte-identical and inflated independently. [Short-prefix Silesia scores](short-prefix/silesia-scores.json) · [Raw observations](short-prefix/observations.json).

The direct-4 encoder is the one timed in the 12-file run. Each order measures all six permutations of the three actors. Each file's ratio combines the forward and reverse block ratios geometrically. The total elapsed time sums the per-file medians, averaged across the two orders. All 12 inputs produced byte-identical raw streams and independently inflated. [Silesia scores](silesia-scores.json).

Mech won **10/12 against libdeflate** and **11/12 against the second reference** in both orders. The summed per-file medians were 27.971 s for Mech, 33.711 s for libdeflate, and 32.650 s for the second reference.

| File | Mech / libdeflate | Mech / reference | Reference / libdeflate |
|---|---:|---:|---:|
| dickens | 0.792093× | 0.899778× | 0.880320× |
| mozilla | 0.853960× | 0.862102× | 0.990556× |
| mr | 1.059583× | 0.937299× | 1.130464× |
| nci | 0.829639× | 0.807469× | 1.027456× |
| ooffice | 0.866611× | 0.886796× | 0.977238× |
| osdb | 0.856228× | 0.889158× | 0.962965× |
| reymont | 0.713482× | 0.871393× | 0.818784× |
| samba | 0.807910× | 0.807143× | 1.000950× |
| sao | 0.957750× | 0.918509× | 1.042722× |
| webster | 0.746761× | 0.906013× | 0.824228× |
| x-ray | 1.138262× | 1.071134× | 1.062669× |
| xml | 0.794341× | 0.781777× | 1.016071× |

## Build and replay

Use Apple Silicon macOS, the pinned Rust nightly, and Python 3.12 or later. A clean Mech checkout at `62363b4a341860b04bbfe11d0a1cb2ea9e3b2532` is required. The run uses the options and four exact profiles in the [base build recipe](../mechdeflate-81-v1/recipe.json) with the two recorded role deltas. The build verifies each input hash and all emitted Mech artifacts.

```sh
python3 experiments/mech/mechdeflate-cranelift-v1/rebuild.py \
  --mech-root /path/to/mech --output /tmp/mechdeflate-cranelift-build
python3 experiments/mech/mechdeflate-cranelift-v1/replay.py \
  --corpus /path/to/silesia --output /tmp/mechdeflate-cranelift-timing
python3 experiments/mech/mechdeflate-cranelift-v1/verify.py \
  --output /tmp/mechdeflate-cranelift-verify
```

The Silesia input manifest and fetch procedure are in the [corpus packet](../mechdeflate-silesia-v1/README.md). Replay uses the exact observed executables by default. Pass `--build /tmp/mechdeflate-cranelift-build` to time the rebuilt workers.

The standard role took 2.915 s from source through the timing executable with the compiler and runtime dependencies prebuilt. Its measured peak stack was 5,184 bytes.
The direct-4 role took 2.895 s from source through the timing executable with the compiler and runtime dependencies prebuilt. Its measured peak stack was 5,184 bytes.

[Complete build observations](build-observations.json) · [Resource, recovery and stack receipts](native-checks.json).
