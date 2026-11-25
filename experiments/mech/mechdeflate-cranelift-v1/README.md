# Mechdeflate Cranelift retest

On Apple M1 with macOS 15.6.1, PR #1000 emitted both pinned level-12 encoders through Cranelift. Both objects, canonical bytecode files and descriptor files reproduced byte for byte. These results supersede the earlier M3 report for this branch. [Compiler revision](https://github.com/mech-lang/mech/commit/62363b4a341860b04bbfe11d0a1cb2ea9e3b2532) · [Exact recipe](recipe.json).

## Admitted word mismatch order

At level 12, the same Cranelift encoder won all 81 benchmark cases and all 12 Silesia files against both pinned references in each timing order. [Compiler revision](https://github.com/mech-lang/mech/commit/35784003b9149fe8059fa83dd5d0aff10dbcd631) · [81-case scores](word-mismatch-order/scores.json) · [Silesia scores](word-mismatch-order/silesia-scores.json).

| File | Mech / libdeflate forward | Mech / libdeflate reverse | Mech / reference forward | Mech / reference reverse |
|---|---:|---:|---:|---:|
| mr | 0.984546× | 0.982758× | 0.871051× | 0.862303× |
| sao | 0.916720× | 0.918871× | 0.878861× | 0.880605× |
| x-ray | 0.997789× | 0.996632× | 0.938304× | 0.937609× |

Summed Silesia per-file medians were 27.861 s for Mech, 33.670 s for libdeflate and 32.616 s for the second reference. All 12 streams matched byte for byte and inflated independently. The smallest 81-case margins were 1.451% against libdeflate and 6.764% against the second reference. The verifier recomputed all 1,965,312 observations. [Raw observations](word-mismatch-order/observations.json).

The native gate passed 162 output and alias checks and 12 recoveries across 6 failure cases. Peak native stack was 5,024 bytes. Three source-to-executable rebuilds reproduced the object, canonical bytecode and descriptor. With dependencies prebuilt, the median build took 2.915 s. The packet includes the exact timed executables, profile pins and build receipt. [Native checks](word-mismatch-order/native-checks.json) · [Build receipt](word-mismatch-order/rebuild.json) · [Timed executables](actors/word-mismatch-order) · [Exact recipe](word-mismatch-order/recipe.json).

```sh
python3 experiments/mech/mechdeflate-cranelift-v1/rebuild.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/word-mismatch-order/recipe.json \
  --mech-root /path/to/mech --output /tmp/mechdeflate-word-mismatch-order
python3 experiments/mech/mechdeflate-cranelift-v1/replay.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/word-mismatch-order/recipe.json \
  --corpus /path/to/silesia --output /tmp/mechdeflate-word-mismatch-order-timing
python3 experiments/mech/mechdeflate-cranelift-v1/verify.py \
  --record experiments/mech/mechdeflate-cranelift-v1/word-mismatch-order \
  --output /tmp/mechdeflate-word-mismatch-order-verify
```

## Adaptive packed tally

This Cranelift encoder won all 81 cases against both pinned references in each timing order. The same native object won 11/12 Silesia files against libdeflate forward and 11/12 in reverse at level 12. It won all 12 in both orders against the second reference. The libdeflate reference used `-O2 -DNDEBUG`. [Compiler revision](https://github.com/mech-lang/mech/commit/728ea55ec3ba9b35ff80420a01e3207af0b916df) · [81-case scores](adaptive-tally/scores.json) · [Silesia scores](adaptive-tally/silesia-scores.json).

| File | Mech / libdeflate forward | Mech / libdeflate reverse | Mech / reference forward | Mech / reference reverse |
|---|---:|---:|---:|---:|
| mr | 1.049218× | 1.049534× | 0.928910× | 0.927972× |
| sao | 0.918660× | 0.922409× | 0.881971× | 0.884650× |
| x-ray | 0.999593× | 0.999323× | 0.936103× | 0.939664× |

Summed Silesia per-file medians were 27.718 s for Mech, 33.668 s for libdeflate and 32.615 s for the second reference. All 12 streams matched byte for byte and inflated independently. The smallest 81-case margins were 0.449% against libdeflate and 1.228% against the second reference. The verifier recomputed all 1,965,312 observations. [Raw observations](adaptive-tally/observations.json).

The native gate passed 162 output and alias checks and 12 recoveries across 6 failure cases. Peak native stack was 5,024 bytes. Three source-to-executable rebuilds reproduced the object, canonical bytecode and descriptor. With dependencies prebuilt, the median build took 2.959 s. The packet includes the exact timed executables, profile pins and build receipt. [Native checks](adaptive-tally/native-checks.json) · [Build receipt](adaptive-tally/rebuild.json) · [Timed executables](actors/adaptive-tally) · [Exact recipe](adaptive-tally/recipe.json).

```sh
python3 experiments/mech/mechdeflate-cranelift-v1/rebuild.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/adaptive-tally/recipe.json \
  --mech-root /path/to/mech --output /tmp/mechdeflate-adaptive-tally
python3 experiments/mech/mechdeflate-cranelift-v1/replay.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/adaptive-tally/recipe.json \
  --corpus /path/to/silesia --output /tmp/mechdeflate-adaptive-tally-timing
python3 experiments/mech/mechdeflate-cranelift-v1/verify.py \
  --record experiments/mech/mechdeflate-cranelift-v1/adaptive-tally \
  --output /tmp/mechdeflate-adaptive-tally-verify
```

## Guarded byte appends

The new Cranelift encoder won 81/81 against both references in both orders. The same native object won all 12 Silesia files against the second reference and 10 against libdeflate at level 12 in both orders. Libdeflate used the pinned `-O2 -DNDEBUG` encoder. [Compiler revision](https://github.com/mech-lang/mech/commit/ff48d9360c5edc8cebc8d1bfeef1c721f9266225) · [81-case scores](guarded-byte-appends/scores.json) · [Silesia scores](guarded-byte-appends/silesia-scores.json).

| Silesia file | Mech / libdeflate | Mech / reference |
|---|---:|---:|
| mr | 1.052716× | 0.931862× |
| sao | 0.931410× | 0.891894× |
| x-ray | 1.048433× | 0.986138× |

Summed per-file medians were 27.790 s for Mech, 33.656 s for libdeflate and 32.607 s for the second reference. All 12 compressed streams were byte-identical and inflated independently. The smallest 81-case margins were 0.196% against libdeflate and 2.477% against the second reference. The verifier recomputed all 1,965,312 observations across both orders. [Raw observations](guarded-byte-appends/observations.json).

The build passed 162 output and alias checks and 12 recoveries across 6 failure cases. Peak native stack was 5,024 bytes. Three clean source-to-executable builds reproduced the 155,216-byte object, canonical bytecode and descriptor. With compiler and support dependencies prebuilt, the median build took 2.928 s. The packet carries the exact two timed executables and SHA-256 pins for each profile. [Native checks](guarded-byte-appends/native-checks.json) · [Build receipt](guarded-byte-appends/rebuild.json) · [Timed executables](actors/guarded-byte-appends) · [Exact recipe](guarded-byte-appends/recipe.json).

```sh
python3 experiments/mech/mechdeflate-cranelift-v1/rebuild.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/guarded-byte-appends/recipe.json \
  --mech-root /path/to/mech --output /tmp/mechdeflate-guarded-byte-appends
python3 experiments/mech/mechdeflate-cranelift-v1/replay.py \
  --recipe experiments/mech/mechdeflate-cranelift-v1/guarded-byte-appends/recipe.json \
  --corpus /path/to/silesia --output /tmp/mechdeflate-guarded-byte-timing
python3 experiments/mech/mechdeflate-cranelift-v1/verify.py \
  --record experiments/mech/mechdeflate-cranelift-v1/guarded-byte-appends \
  --output /tmp/mechdeflate-guarded-byte-verify
```

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
