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

The short-prefix encoder won **10/12 against libdeflate** and **11/12 against the second reference** in each timing order. Its summed per-file medians were 28.755 s against 33.670 s and 32.616 s, respectively. All 12 streams were byte-identical and inflated independently. [Complete scores](short-prefix/silesia-scores.json) · [Raw observations](short-prefix/observations.json).

Each order measures all six permutations of the three actors. Each file's ratio is the geometric mean of the two orders' paired elapsed-time ratios. The corpus total sums the per-file medians, averaged across the two orders.

| File | Mech / libdeflate | Mech / reference | Reference / libdeflate |
|---|---:|---:|---:|
| dickens | 0.818202× | 0.931023× | 0.878820× |
| mozilla | 0.880248× | 0.887119× | 0.992255× |
| mr | 1.081644× | 0.956737× | 1.130555× |
| nci | 0.863489× | 0.840328× | 1.027562× |
| ooffice | 0.896528× | 0.919429× | 0.975092× |
| osdb | 0.874971× | 0.909561× | 0.961971× |
| reymont | 0.728931× | 0.889265× | 0.819701× |
| samba | 0.827821× | 0.826959× | 1.001042× |
| sao | 0.960923× | 0.920068× | 1.044404× |
| webster | 0.766827× | 0.929730× | 0.824785× |
| x-ray | 1.131622× | 1.064817× | 1.062738× |
| xml | 0.812356× | 0.799989× | 1.015459× |

The pinned libdeflate Silesia encoder uses Apple Clang with `-O2 -DNDEBUG`, the upstream release setting. With the encoder revision and support objects fixed, `-O3` took 0.35% longer on `sao`, 0.42% longer on `mr`, and 1.07% longer on `x-ray` across six matched orders per file. Every compressed stream matched the reference and inflated independently. [Upstream build guidance](https://github.com/ebiggers/libdeflate/blob/92e6a0db9fa848d742f9eb286c92afc60f2c3dda/README.md#supported-compilers) · [Build and timing evidence](libdeflate-build-levels.json).

The earlier direct-4 run also won 10/12 and 11/12 in each order. Its summed medians were 27.971 s, 33.711 s and 32.650 s, respectively. The streams matched byte-for-byte across the three encoders. [Direct-4 Silesia scores](silesia-scores.json).

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
