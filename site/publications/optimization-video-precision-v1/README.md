# Precise speedup labels

Speedups outside the headline use two decimal places. The final value is
221.71×, calculated from the retained 118.600627083-second initial runtime and
0.5349341875-second final median. The unrounded factor remains
221.71068863120664 in the manifest. Only the headline uses a whole-number
speedup. The initial annotation also shows its distinct 216.16× Rust ratio.

The video remains 1920×1080 at 60 fps, with one second per Rust crossing,
120 median checkpoints and the same measured ball motion and soundtrack.
SVG label checks require the precise subtitle and timing-card values and
reject the whole-number speedup outside the headline. The encoded verifier and
independent playback audit check all 3,426 frames and 95 sound contacts.

- [60 fps video](https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4?v=3c5e7fee6187)
- [Scalable chart](https://mech-lang.org/benchmarks/mech-compiler-optimization.svg?v=3c5e7fee6187)
- [Source and audited media](https://github.com/mech-lang/benchmarks/tree/8a0e82ce3c8e33b375f730209553d05bed11d1de/experiments/mech/native-owner-aot-v1/optimization-history-animation-v1)
- [Website commit](https://gitlab.com/mech-lang/web/website/-/commit/3c5e7fee6187077bdc52be1c430b945b8a5b07ba)
- [Pages pipeline](https://gitlab.com/mech-lang/web/website/-/pipelines/2995246542)

Only the video and SVG assets change in the website repository. The existing
timing receipts and fitted curve are unchanged. The thin history cursor is
located using vertical luminance contrast, which tolerates H.264 chroma
subsampling without changing the 1.5-pixel position limit.

`deployment.json` pins the source and website commits, successful pipeline,
public checksums and accuracy reports. Both the versioned and plain video
addresses must match the committed artifact exactly; the SVG must also match.
The verifier fails until any previously cached plain-address response updates.

Reproduce the publication check from this directory:

```sh
python verify.py --pipeline 2995246542
```
