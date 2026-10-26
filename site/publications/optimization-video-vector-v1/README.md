# Vector optimization chart and antialiased video

[SVG chart](https://mech-lang.org/benchmarks/mech-compiler-optimization.svg?v=0669d99beb08) ·
[60 fps video](https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4?v=0669d99beb08)

The axes, markers, lines, callouts and font outlines share one vector scene.
The SVG retains 120 median markers with no embedded bitmap layers. Video
frames use antialiased rendering at 3840×2160 followed by Lanczos downsampling
to 1920×1080. The 60 fps video retains its 57.1-second duration, measured timing
history, ball deformation and synchronized soft impact sounds.

Benchmark commit `fc7f9a620fb1d5d9ff30c7481fbc514daf486a87` contains the source,
SVGs, video and verification under
`experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/media-vector-60fps`.
Website commit `0669d99beb08a3ac0c16f656088a76c15e564fae` publishes the SVG chart
and replaces the 60 fps MP4. No HTML page is added.

Run `python verify.py` to verify the successful Pages pipeline, public video and
SVG hashes, content types and video byte-range behavior. `deployment.json`
records the public responses and pinned vector, motion and audio checks.
