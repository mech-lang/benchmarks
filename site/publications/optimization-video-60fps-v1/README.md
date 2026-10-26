# Compiler optimization video: 60 fps edition

[Direct 60 fps video](https://mech-lang.org/benchmarks/mech-compiler-optimization-60fps.mp4?v=a765c034a145)

The 1920×1080 video contains 3,426 individually rendered frames at 60 fps.
It retains the 57.1-second duration, median timing history, brown and yellow
balls, restrained impact deformation and synchronized keyboard-style taps.
Its lossless audio master is identical to the 30 fps edition's master.
The existing 30 fps video remains available at its original URL.

Benchmark commit `b52f2858242ecbe1ffcad1541315f08fd8fc47cd` contains the source,
60 fps media and encoded verification under
`experiments/mech/native-owner-aot-v1/optimization-history-animation-v1/media-60fps`.
Website commit `a765c034a1452298ce28a2534b5730c95eb60c74` adds a single MP4
asset. No HTML page is added.

Run `python verify.py` to check the successful Pages pipeline, complete public
video hash, content type and byte-range response. `deployment.json` records the
published video and pinned checks of its frame rate, motion and audio.
