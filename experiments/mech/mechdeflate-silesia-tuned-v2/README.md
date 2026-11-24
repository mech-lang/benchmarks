# Level-12 Silesia tuning for Mechdeflate

Direct literal tallying with groups of four reduced summed file medians from **28.84 s** to **28.02 s**. The same-run libdeflate 1.26 total was **33.67 s**. The lead grew from **14.33%** to **16.76%**, a gain of 2.43 percentage points. The tuned build improved all twelve files in both directions. It won ten in each direction against libdeflate. [Raw timing observations](timings.json) · [Full results](scores.json).

The source is Mech PR #999 at `2b301734f`. The recipe switches from seeding counts and subtracting match-covered bytes to tallying the chosen literals directly. It also changes the packed tally group size from sixteen to four. [Source commit](https://github.com/mech-lang/mech/commit/2b301734fb43a4abff0d38d68d881e2bf85bd969) · [Recipe](recipe.json) · [Base build and its four profiles](../mechdeflate-81-v1/README.md).

| File | Published Mech time vs libdeflate | Tuned Mech time vs libdeflate |
|---|---:|---:|
| `dickens` | 17.52% less | 21.22% less |
| `mozilla` | 11.67% less | 14.38% less |
| `mr` | 8.62% more | 5.91% more |
| `nci` | 13.77% less | 16.20% less |
| `ooffice` | 9.35% less | 13.37% less |
| `osdb` | 12.04% less | 14.40% less |
| `reymont` | 26.89% less | 28.77% less |
| `samba` | 16.97% less | 18.82% less |
| `sao` | 2.44% less | 4.08% less |
| `webster` | 23.02% less | 25.11% less |
| `x-ray` | 16.72% more | 13.65% more |
| `xml` | 19.03% less | 20.24% less |

Per-file results use the geometric mean of the two directional paired elapsed-time ratios. The corpus total sums each file’s mean of the two directional medians. On an Apple M1 running macOS 15.6.1, each direction measures three cyclic execution orders. Each actor occupies each slot once per direction. The harness loads the full file before the encode timer and validates and releases output after it. All 12 output streams matched byte for byte and independently inflated to the input. [Timing and input bindings](binding.json).

## Where time goes

Time Profiler samples cover the original pinned binaries inside the encoder call. The stage estimates use the corresponding unprofiled medians.

- On `x-ray`, Mech spent about **50 ms** emitting bits versus libdeflate’s **13 ms**, and **72 ms** tallying frequencies versus **46 ms**. The checked payload loop and its byte-append continuation account for the emission gap.
- On `mr`, Mech spent about **1.94 s** in the matchfinder versus **1.65 s** in libdeflate’s matcher and controller. Libdeflate spent about **1.35 s** advancing the binary tree under long matches. Mech’s faster path scoring recovered about **179 ms** of the difference.
- On `sao`, Mech’s path scoring had an estimated **53 ms** lead. Extra matcher work, tallying and emission consumed most of it.
- Mech’s backward path scoring saved an estimated **1.72 s** on `nci` and **1.92 s** on `webster`. Those are important contributors to its corpus-wide lead.

[Phase estimates and sample hashes](profiles.json).

## Rebuild and replay

Use Apple Silicon, Python 3.11 or later, Xcode 26.0.1 with macOS SDK 26.0, and the pinned Rust nightly. Run from the benchmark checkout with a clean Mech checkout at `2b301734fb43a4abff0d38d68d881e2bf85bd969`.

```sh
python3 experiments/mech/mechdeflate-silesia-tuned-v2/rebuild.py \
  --mech-root /path/to/mech --output /tmp/mech-silesia-rebuilt
```

The rebuild verifies the encoder object, canonical bytecode and metadata, then links the exact timed executable using the pinned host support. The replay checks the measured binaries by hash and verifies each raw stream. Prepare the pinned Silesia files using the linked input recipe. [Input preparation](../mechdeflate-silesia-v1/README.md#reproduce-on-arm64-macos).

```sh
python3 experiments/mech/mechdeflate-silesia-tuned-v2/replay.py \
  --corpus /path/to/silesia --output /tmp/mech-silesia-timings.json
python3 experiments/mech/mechdeflate-silesia-tuned-v2/score.py \
  /tmp/mech-silesia-timings.json
```

The tuned encoder passed 162 linked fixture checks, six named errors, and twelve recovery checks. Peak stack was 5,184 bytes. [Native checks](native-checks.json).

The tuned build won all 81 cases against both references in both directions of the 96-block regression check. It took 10.38% longer than the prior Mech build on `prefix-random-16384`, the largest increase in the check. [81-case timing check](81-case-check.json).
