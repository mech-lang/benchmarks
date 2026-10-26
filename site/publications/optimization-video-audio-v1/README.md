# Compiler optimization video with synchronized audio

[Direct video](https://mech-lang.org/benchmarks/mech-guided-llm-optimization.mp4?v=2e239b2)

The 57.1-second animation presents 120 median timing checkpoints over 50 elapsed
hours, with stepwise benchmark-speed replay beneath the chart. Mech uses its
logo yellow; Rust uses its GitHub language color. Quiet, distinct keyboard-style
impacts mark every wall contact. The title describes a 222× runtime improvement,
99.55% runtime reduction and a final result 4% faster than the Rust baseline.

The website publication replaces a single MP4 asset; no HTML page is added.
The video source, lossless soundtrack and encoded motion/audio checks are
retained in benchmark commit `77b64762a3b740c433fd859487059ce17819da7f` under
`experiments/mech/native-owner-aot-v1/optimization-history-animation-v1`.
Website commit `2e239b2c39763ba30fae9f58ae5bd81623f0230c` publishes that MP4.

Run `python verify.py` to check the successful Pages pipeline, complete video
hash, content type and byte-range behavior. `deployment.json` records the
verified public responses and the pinned media's audio checks.
