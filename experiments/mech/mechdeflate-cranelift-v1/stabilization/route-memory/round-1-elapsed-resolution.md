# Round 1 compiler qualification

**The compiler gate passed for `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea`.** The source refinement skips blocks with no active branch-argument replacements and iterates the remaining instructions directly. Focused tests, the serialized graph-reuse census, and the exact encoder verification passed. The fixed encoder object, bytecode, and descriptors matched. [Encoder receipt](3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea/source-validation/encoder.json)

The first fresh assessment cleared the elapsed and memory gates against O. R's same-build elapsed calibration excluded zero. That assessment and its observations are retained. [Original assessment](3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea/B2-m1-20261126T170955Z/compiler-summary.md)

The previous runner used the same absolute launch positions for each role in every session. The corrected schedule rotates the starting slot across session ordinals. Each role occupies each absolute position once across three sessions. The batch size, estimator and decision rule are unchanged. The tool tests also verify that permuting a complete cycle into the wrong order invalidates the record. A fresh campaign used identical compiler and actor binaries and identical recipe bytes.

| Control | Compiler elapsed | Simultaneous 95% interval | Paired median peak RSS change | Decision |
| --- | ---: | --- | ---: | --- |
| R | -0.1947% | -0.3013% to -0.0879% | -499,712 bytes (-488 KiB) | Pass |
| O | -0.1246% | -0.1693% to -0.0798% | -229,376 bytes (-224 KiB) | Pass |

Both calibrations passed. The independent verifier reproduced the assessment from all 252 preplanned invocations. Runtime qualification belongs to the integrated compiler in Round 2. [Passing assessment](3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea/B2-counterbalanced-m1-20261126T175458Z/compiler-summary.md) · [Archive checksums](archives.json)
