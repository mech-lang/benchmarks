# Axis, evidence and playback accuracy audit

The audit independently checks the original process receipts, the serialized
SVG geometry and every decoded video frame. No benchmark executable is run.

## Findings and presentation changes

The previous axis mapping was mathematically consistent. Its equally weighted
1–2–5 tick sequence had unequal visual gaps on a logarithmic axis: consecutive
ratios alternate between 2 and 2.5. The major labels now mark 1×, 10× and 100×,
with equal decade spacing. The 2× and 5× minor gridlines are faint and unlabeled.
The horizontal scale retains equal six-hour intervals. Data points retain
their actual, irregular measurement timestamps.

The time origin is the first recorded process launch. Each checkpoint uses the
median launch timestamp of its observations. It is not the implementation's
commit time or the last run's completion time. This basis is now in the x-axis
label. The history clock marks its introduction and ending pauses as `HOLD`.
The ball replay explicitly states its separate normalization to Rust.

Four initial checkpoints have one observation each. Visible sample counts now
identify these single-run checkpoints. The headline speedup uses raw elapsed
seconds, whereas the chart and replay use each cohort's contemporaneous Rust
median. The subtitle and timing card now distinguish these quantities.

| Quantity | Independently recomputed value |
|---|---:|
| First Mech complete-process time | 118.600627083 s |
| Initial Rust control | 0.5486585 s |
| Initial Mech / Rust runtime | 216.164749× |
| Final Mech median | 0.5349341875 s |
| Final Rust median | 0.5559576875 s |
| Final Mech / Rust runtime | 0.962185× |
| Raw-runtime speedup | 221.7107×, rounded to 222× |
| Raw-runtime reduction | 99.54896%, rounded to 99.55% |
| Final speed advantage over Rust | 3.9301%, rounded to 4% |
| Drop in the normalized plotted ratio | 224.6603× |

The headline is `118.600627083 / 0.5349341875 = 221.7107×`, rounded to 222×.
The chart begins at `118.600627083 / 0.5486585 = 216.164749× Rust` and ends
at `0.5349341875 / 0.5559576875 = 0.962185× Rust`. It therefore starts at
216× Rust without implying a 216× improvement in Mech itself. The subtitle now
prints the raw-seconds calculation, and the card separately names the Rust
runtime ratio and Mech's speedup since the start.

The last table row differs from the raw-runtime speedup because the Rust
denominator changes by 1.33037% across those cohorts. It is not a second
estimate of the same quantity.
The 222× headline is an observed historical ratio with a single-run initial
checkpoint, not a confidence bound on a replicated initial baseline.

## Evidence checks

`audit_evidence.py` verifies 2,276 pinned files and recomputes 120 checkpoint
medians, ratios and timestamps from 732 unique Mech processes and 724 unique
Rust controls. Every process completed successfully; all observations use the
same 125-million-base input hash. Where exclusions are recorded, warmup and
outlier exclusion counts are zero. Results are in `receipt-audit.json`.

All 732 Mech receipts identify controller SHA-256
`e0c6c1260af4900cd4b307252b54461b3f7cee90e2c102ec157d9b1429a5ce3b`, matching
`experiments/janet/knucleotide-bytes-v1/process.py`. The shared controller starts
its monotonic timer immediately before `fork` and stops when `wait4` observes
exit. It includes launch supervision, executable startup and shutdown. Its exit
observer polls every millisecond. The retained measurement drivers use that
same controller for Mech and Rust; the values are complete-process timings.

`audit_axes.py` reads the actual SVG tick-label text and grid coordinates,
recovers the linear x mapping and logarithmic y mapping, then checks all 120
serialized median markers. The largest marker discrepancy is below
0.000002 logical pixels. It also checks both sets of major gaps, all minor-grid
values, all ten annotation leader endpoints and the final highlighted marker.
Results are in `axes.json`.

`audit_playback.py` imports no renderer code. It integrates speed directly from
the receipt-derived medians and decodes every frame to check both balls and the
history frontier. At a fixed checkpoint, one Rust crossing takes one screen
second and one Mech crossing takes its Mech/Rust ratio in screen seconds. The
earlier 1.2-second scale was an arbitrary presentation choice; both lanes and
the impact soundtrack now use the simpler one-second convention. Between
checkpoints the speed changes immediately while phase remains continuous.
A crossing spanning a speed update is an illustrative work unit rather than a
measurement of one executable version.

The previous 1.2-second editions retain their audit reports in
`previous-release/playback-audit.json` and `current-release/playback-audit.json`.
The one-second edition is checked separately in
`one-second-release/playback-audit.json`.
The history advances one recorded hour per video second, preceded by a
two-second hold and followed by a 5.02644-second hold after frame rounding.
All 95 impact times are checked independently (38 Mech, 57 Rust). Audio event
quantization is within half a 48 kHz sample; a contact can fall up to half a
60 fps frame from its nearest frame. Per-contact comparisons of decoded AAC against the
lossless master detect no additional lag at the audit's 83-microsecond
resolution. The change affects the illustrative replay speed and soundtrack;
all 120 historical timing checkpoints and the fitted curve remain unchanged.

## Reproduction

From the animation source directory:

```sh
python audit_evidence.py accuracy-audit
python audit_axes.py media-one-second-60fps/mech-compiler-optimization.svg accuracy-audit/one-second-axes.json
python audit_playback.py media-one-second-60fps accuracy-audit/one-second-release
python verify_video.py media-one-second-60fps
```

Earlier editions can be independently replay-audited with
`--rust-crossing-seconds 1.2`; the default is now one second.

The existing encoded verifier additionally checks the vector structure,
antialiasing, exact deformed ball geometry, frame rate, both winning cohorts,
audio format and quiet levels. Antialiased ellipse extents are detected at
half coverage rather than using a near-solid-color inset contour.
