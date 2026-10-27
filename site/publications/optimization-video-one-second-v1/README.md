# Explicit runtime comparisons and one-second replay

The file-only website update publishes a 1920×1080, 60 fps video and scalable
SVG chart. The title's 222× speedup compares Mech's initial 118.600627083-second
runtime with its final 0.5349341875-second median: 221.7106886× before rounding.
The chart instead compares Mech with each cohort's Rust median, starting at
216.164749× Rust and ending at 0.962185× Rust. The subtitle prints the raw
seconds calculation, and the timing card labels these comparisons separately.

The normalized replay uses exactly one screen second per Rust crossing.
Mech's crossing time at a fixed checkpoint equals its measured Mech/Rust ratio
in screen seconds. All 120 historical checkpoints and the fitted curve retain
their original coordinates. Both balls and all 95 collision sounds use the new
scale; phase stays continuous as Mech's measured speed changes.

- [60 fps video](https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4?v=770fa439738b)
- [Scalable chart](https://mech-lang.org/benchmarks/mech-compiler-optimization.svg?v=770fa439738b)
- [Source and audited media](https://github.com/mech-lang/benchmarks/tree/05f935062b5d0c7e8d05a5c82cd249aa18003145/experiments/mech/native-owner-aot-v1/optimization-history-animation-v1)
- [Website commit](https://gitlab.com/mech-lang/web/website/-/commit/770fa439738b11814d21cbf3baea55ed1fd89c61)
- [Pages pipeline](https://gitlab.com/mech-lang/web/website/-/pipelines/2995162023)

The receipt audit independently recomputes all 120 checkpoint medians from 732
Mech runs and 724 Rust controls. The SVG audit checks every marker, the axes
and all ten annotation leaders. The independent playback audit decodes all
3,426 frames and checks all 95 impacts against receipt-derived motion. The
encoded verifier also checks the vector artwork, antialiasing, audio alignment,
frame rate, both winning cohorts and deformed ball geometry.

`deployment.json` records the public-file checksums, MIME types, successful
Pages pipeline, pinned commits and retained accuracy reports. The versioned
video and SVG must match the committed files exactly. Pages advertises a
ten-minute cache lifetime: an unversioned GET can briefly return the prior
release while HEAD already describes the new file. The verifier requires both
video addresses to match the new file and fails until the cache updates; HEAD
must also describe its current length. Published links use versioned addresses.
Reproduce the
deployment check from this directory with:

```sh
python verify.py --pipeline 2995162023
```
