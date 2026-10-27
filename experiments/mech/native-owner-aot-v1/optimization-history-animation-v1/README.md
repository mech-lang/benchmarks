# LLM Optimizes Mech Compiler 222× Over 50 Hours

**99.55% Runtime Reduction · 4% Faster Than Rust Baseline**

The animation reveals the full-input optimization history above two benchmark
replay lanes. Mech's ball uses its logo yellow (`#F6C04E`); Rust's uses a deeper
brown (`#8B4A2D`) to distinguish the two lanes. The white-background chart keeps blue markers and includes
120 median timing checkpoints: the original 118 cohorts plus both later
qualified sessions in which Mech beats unchanged Rust. The 732 individual
process observations remain in the source data and are not drawn. Its
base-10 logarithmic runtime axis, ten annotated changes and line of best fit show the
path from 216× Rust to 0.962× Rust.

[SVG chart](media-one-second-60fps/mech-compiler-optimization.svg) ·
[1080p 60 fps video](media-one-second-60fps/mech-rust-optimization-timelapse.mp4) ·
[Animated preview](media-one-second-60fps/mech-rust-optimization-timelapse.gif) ·
[Decoded-frame overview](media-one-second-60fps/encoded-contact-sheet.png) ·
[Accuracy audit](accuracy-audit/README.md)

The complete artwork uses vector paths, including the axes, circles, connecting
lines, callouts, cards, balls and font outlines. The SVG contains no embedded
bitmap images. Video frames are rasterized at 3840×2160 with antialiasing and
downsampled with Lanczos to 1920×1080 at 60 fps. The SVG remains scalable at any
zoom level.

Major y labels are equally spaced decades (1×, 10×, 100×); faint 2× and 5×
minor grids preserve logarithmic reading. Equal six-hour x intervals use median
process-launch times. Visible sample counts, clock holds and the replay scale
identify the measurement and timing conventions. The independent accuracy
audit rechecks all source timings, every marker and every encoded frame.

The current 60 fps edition runs for 57.1 seconds. Every frame is rendered at
its own timestamp. Earlier editions used a 1.2-second Rust crossing; the current
edition uses one second and regenerates every collision sound from that motion.
The retained
30 fps packet was generated from benchmark commit
`273fcdbad2340bf21a965f7edbec4597a064355f`; its pinned source hashes remain intact.
The initial 60 fps packet is retained in `media-60fps` at benchmark commit
`b52f2858242ecbe1ffcad1541315f08fd8fc47cd`. The vector edition is in
`media-vector-60fps`. The earlier audited presentation is in `media-audited-60fps`;
the current one-second replay is in `media-one-second-60fps`.

The video uses two explicitly separate clocks:

- The optimization clock runs at 3,600×: one recorded elapsed hour per video
  second, including intervening gaps. A two-second introduction and five-second
  ending hold keep the initial and final speeds visible.
- The replay clock assigns one screen second to one Rust crossing. A Mech
  crossing takes `(Mech seconds / contemporaneous Rust median seconds)` screen seconds.
  At a fixed checkpoint, one one-way crossing represents one benchmark
  execution at the replay scale. Crossings spanning an update integrate both
  successive speeds.

Rust's speed stays constant. Mech's speed changes discretely at each original
cohort coordinate and stays constant until the next checkpoint. Its position
remains continuous across updates and reflects at the lane ends. The fitted
curve never controls the ball's motion. All trials and measured regressions
are retained; this is not a best-so-far envelope.

The balls have no direction arrows. At each wall contact they compress
horizontally by up to 14%, preserve their elliptical area, then recover with
a 4% stretch and a two-pixel lift. The effect settles within 0.21 seconds.
Radius compensation keeps the compressed edge against the wall. These small
surface and position offsets do not change the measured phase, crossing times
or impact sounds. Ball outlines and highlights are vector ellipses.

Each wall contact has a quiet, rounded keyboard-style tap: Mech has a lighter
sound, Rust a deeper, muted sound. The original synthesized impacts use short,
damped resonances and filtered noise, with a soft attack and slight stereo
placement toward the contacted wall. No third-party sound recordings are used.
The soundtrack contains 38 Mech and 57 Rust contacts. Collision times come from
the integrated ball motion, quantized to the nearest 48 kHz audio sample.

The headline compares Mech with its own initial runtime, while the chart compares
Mech with Rust. These are different quantities:

| Comparison | Calculation | Result |
|---|---|---:|
| Mech's own runtime improvement | 118.600627083 / 0.5349341875 | 221.7107× ≈ 222× |
| Initial Mech / initial Rust runtime | 118.600627083 / 0.5486585 | 216.1647× |
| Final Mech / final Rust runtime | 0.5349341875 / 0.5559576875 | 0.962185× |

Dividing the chart's first ratio by its final ratio gives 224.6603× rather than
221.7107× because the Rust control median changed by 1.3304% between those
measurements. The headline uses Mech's raw seconds. The subtitle prints its
118.60 → 0.5349-second calculation, and the timing card separately labels the
current Rust comparison and Mech's speedup since the start.

The two qualified
paired-load sessions occur at 50.056996 and 50.068763 elapsed hours, recovered
from the retained process births. Their results are:

| Executable | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Mech, paired key/count loads | 0.5318 | 0.955× | 0.5349 | 0.962× |
| Previous best Mech control | 0.5493 | 0.986× | 0.5449 | 0.980× |
| Unchanged Rust control | 0.5569 | 1.000× | 0.5560 | 1.000× |

The final Mech ball is therefore about 4% faster than the Rust ball. Raw Mech
runtime has improved by about 222× from the first checkpoint. Both sessions
include secured startup and shutdown, retain twelve observations per
executable, and have paired 95% intervals favoring Mech over Rust. Parent and
anchor retimings remain comparison controls rather than new implementation
changes. The original unpromoted trials remain visible earlier in the history.

## Sources and reproduction

`build_timeline.py` retains the original measurements and recovered launch times
from [`optimization-history-hours-v1/analysis.json`](../optimization-history-hours-v1/analysis.json)
and appends the two later candidate cohorts from the verified
[`paired-candidate-loads-v1`](../paired-candidate-loads-v1/README.md) packet. It
checks receipt hashes, terminal process state, source identity, input identity,
medians and paired intervals. The merged source is `timeline.json`.
`fit_curve.py` computes the line of best fit from all 120 median timings and
records the parameters in `best-fit.json`. The model is an offset plus two
exponential components. It minimizes squared errors in runtime ratios with
equal weight per median. Five positive-parameter starting points converge to
the same optimum, and analytic first derivatives are checked. The fitted
curve is drawn over the observed elapsed-hour range.
No benchmark is executed to render this animation.

With Python 3.12, create an isolated environment, install the versions in
`requirements.txt`, run `python build_timeline.py` and `python fit_curve.py`, then
`python render.py --output media` and `python verify_video.py media`. `--preview-only`
renders six still frames and an overview before encoding. Matplotlib supplies
the vector scene and bundled fonts; Pillow downsamples the frames; imageio-ffmpeg supplies
the H.264 encoder, AAC audio encoder and silent GIF preview. The recorded editions
use 1920×1080 at 30 or 60 fps, H.264 with 4:2:0 pixels, stereo 48 kHz AAC audio, and MP4
fast-start metadata. `bounce_audio.py` creates the deterministic soundtrack;
`media-one-second-60fps/bounce-soundtrack.flac` retains its lossless master, and
`media-one-second-60fps/bounce-audio.json` records every impact and its source hash.
Render the current 60 fps edition with `python render.py --fps 60 --output
media-one-second-60fps`, run `python normalize_svg.py media-one-second-60fps` to remove
trailing line whitespace from the generated SVGs, then run
`python verify_video.py media-one-second-60fps`. Its manifest and
checks are stored alongside the 60 fps video, including a decoded intervening
frame that verifies its position against the 60 Hz motion clock.

`media-one-second-60fps/animation.json` records both clock scales, source and artifact hashes,
package versions, exact endpoints, frame count, and motion checks. Every speed
interval is checked against its measured ratio, phase continuity is verified,
and all 120 median points are visible at the end. The individual-run layer and
bottom caption are omitted from the video. The encoded MP4 checks include
the first visible frame of each winning cohort;
both balls' observed centers agree with their expected
positions to within one pixel. Those checks and decoded video metadata are
retained in `media-one-second-60fps/encoded-verification.json`. The verifier also checks all wall
contacts, the audio stream's format, quiet peak levels, absence of clipping, and
alignment of the decoded AAC track with the lossless master. It checks encoded
frames around all 95 impacts for deformation, center position and
absence of arrows, and verifies wall contact and recovery analytically.
For the vector edition it also checks the SVG path structure, all 120 marker
IDs, absence of embedded raster layers, outlined fonts and intermediate
edge-coverage colors in the uncompressed preview. `vector_scene.py` supplies
the shared SVG and video drawing primitives.
