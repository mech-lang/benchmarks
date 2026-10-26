# LLM Optimizes Mech Compiler 222× Over 50 Hours

**99.55% Runtime Reduction · 4% Faster Than Rust Baseline**

The animation reveals the full-input optimization history above two benchmark
replay lanes. Mech's ball uses its logo yellow (`#F6C04E`); Rust's uses the
[GitHub Linguist Rust color](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml)
(`#DEA584`). The white-background chart keeps blue markers and includes
120 median timing checkpoints: the original 118 cohorts plus both later
qualified sessions in which Mech beats unchanged Rust. The 732 individual
process observations remain in the source data and are not drawn. Its
base-10 logarithmic runtime axis, ten annotated changes and line of best fit show the
path from 216× Rust to 0.962× Rust.

[1080p video](media/mech-rust-optimization-timelapse.mp4) ·
[Animated preview](media/mech-rust-optimization-timelapse.gif) ·
[Decoded-frame overview](media/encoded-contact-sheet.png)

The approximately 57-second video uses two explicitly separate clocks:

- The optimization clock runs at 3,600×: one recorded elapsed hour per video
  second, including intervening gaps. A two-second introduction and five-second
  ending hold keep the initial and final speeds visible.
- The replay clock assigns 1.2 screen seconds to one Rust crossing. A Mech
  crossing takes `1.2 × (Mech seconds / contemporaneous Rust median seconds)`.
  One one-way crossing represents one full benchmark execution.

Rust's speed stays constant. Mech's speed changes discretely at each original
cohort coordinate and stays constant until the next checkpoint. Its position
remains continuous across updates and reflects at the lane ends. The fitted
curve never controls the ball's motion. All trials and measured regressions
are retained; this is not a best-so-far envelope.

Each wall contact has a quiet, rounded keyboard-style tap: Mech has a lighter
sound, Rust a deeper, muted sound. The original synthesized impacts use short,
damped resonances and filtered noise, with a soft attack and slight stereo
placement toward the contacted wall. No third-party sound recordings are used.
The soundtrack contains 31 Mech and 47 Rust contacts. Collision times come from
the integrated ball motion, quantized to the nearest 48 kHz audio sample.

The initial checkpoint is 118.6006 seconds, or 216.1647× Rust. The two qualified
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
the chart and bundled fonts; Pillow composes the frames; imageio-ffmpeg supplies
the H.264 encoder, AAC audio encoder and silent GIF preview. The recorded output
uses 1920×1080, 30 fps, H.264 with 4:2:0 pixels, stereo 48 kHz AAC audio, and MP4
fast-start metadata. `bounce_audio.py` creates the deterministic soundtrack;
`media/bounce-soundtrack.flac` retains its lossless master, and
`media/bounce-audio.json` records every impact and its source hash.

`media/animation.json` records both clock scales, source and artifact hashes,
package versions, exact endpoints, frame count, and motion checks. Every speed
interval is checked against its measured ratio, phase continuity is verified,
and all 120 median points are visible at the end. The individual-run layer and
bottom caption are omitted from the video. The encoded MP4 was decoded
at ten timestamps, including the first visible frame of each winning cohort;
both balls' observed centers agree with their expected
positions to within one pixel. Those checks and decoded video metadata are
retained in `media/encoded-verification.json`. The verifier also checks all wall
contacts, the audio stream's format, quiet peak levels, absence of clipping, and
alignment of the decoded AAC track with the lossless master.
