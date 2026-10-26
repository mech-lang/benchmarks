# Audited optimization chart and playback

[SVG chart](https://mech-lang.org/benchmarks/mech-compiler-optimization.svg?v=42db12749dc9) ·
[60 fps video](https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4?v=42db12749dc9) ·
[Full accuracy report](https://github.com/mech-lang/benchmarks/blob/bc9caf4f9374d15a8e0f513e97cc3ee30bfc945b/experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/accuracy-audit/README.md)

The publication uses equally spaced major decades on the base-10 y axis and
equal six-hour intervals on the linear x axis. It identifies process-launch
timestamps, sample counts, history-clock holds and the separate normalized
replay scale. Timing data and recorded point coordinates are retained.

Independent audits verify 120 checkpoint medians from 732 Mech processes and
724 Rust controls, all serialized markers and annotation leaders, all 3,426
encoded frames and all 78 audio contacts. The full report distinguishes the
raw-runtime headline gain from the drop in the Rust-normalized ratio.

Benchmark commit `bc9caf4f9374d15a8e0f513e97cc3ee30bfc945b` contains the sources,
audit records and media. Website commit
`42db12749dc9db9329acd2b03728fc5483741ce9` replaces the SVG and 60 fps MP4.
No HTML page is added.

Run `python verify.py` to verify the public media hashes, content types,
successful Pages pipeline and pinned independent audit results.
