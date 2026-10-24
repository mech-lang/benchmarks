# Source alphabet proof at closed-map admission

The finite alphabet of a successful source producer can prove that every
grapheme occupies one byte. ASCII has only one multi-byte grapheme, CRLF, so
excluding either CR or LF is a sufficient condition. The original source-domain
proof includes mapped values and separators; the fallback packing domain does
not preserve that distinction.

Compiler revision `f1323c0383927e461a0c70f34872b1e6e44f9657` uses that proof to
avoid the physical closed-map source scan. It retains the entire original setup
charge and denial frontier. Unknown, Unicode and possibly-CRLF sources retain
the existing guard. This runtime-only trial emits the exact same entire Mech
object as its IR73 parent, SHA-256
`f9cf0c1ee3674fa44e5b626a0a1e3112a7d4d6ebb53b6ac4c749c7eac9e634f8`.
The Mech source, bytecode, input, finite launch policy and complete-map algorithm
are unchanged.

## Measurements

Six balanced serial full-input cohorts retain all eighteen observations,
including startup/shutdown and every outlier. There are no excluded full-input
warmups.

| Executable, 125 million selected bases | Median seconds | × Rust time |
| --- | ---: | ---: |
| Protected Rust | 0.5523 | 1.000× |
| IR73 parent | 0.7952 | 1.440× |
| Source-proof candidate | 0.8075 | 1.462× |

The candidate median is **1.54% higher**, with two faster and four slower pairs.
No full-input gain is established. Every Mech execution verifies the complete
output, seven packed SSA maps and peak workers, and 874,999,961 physical updates.
The [full cohort](../full-proved-graphemes-cohort-v1/results.json) and every raw
process remain.

The separate [one-million-base prefix cohort](../proved-graphemes-timing-v1/results.json)
has Rust 0.0223 s, parent 0.0873 s / 3.917× and candidate 0.0918 s / 4.116×.
It retains one excluded warmup and three observations per subject. Prefix and
full timings are not pooled.

[Separate counters](../proved-graphemes-hardware-v1/results.json) give candidate
39.746 billion instructions / 10.491 billion cycles, parent 39.960 / 10.583,
and Rust 33.136 / 7.890. The reductions against the parent are only 0.53% in
instructions and 0.87% in cycles. These diagnostic processes are not additional
primary timing observations and do not establish an elapsed-time gain.

One [completed exact-code profile](../proved-graphemes-remaining-profile-v1/results.json)
has 2,317 worker observations: 87.40% generated loops, 4.36% storage, 4.06%
active accounting, 1.38% accounting waits and 2.80% bridge/other work. These are
sampled thread observations including waits, not wall-time shares. A single
capture does not identify the cause of the small timing regression. The first
capture used a nonexistent policy path and exited before the workload; its
failed process and capture remain separately recorded. The corrected retry uses
the exact verified full-input policy.

## Validation and disposition

One check covers all 16,384 ASCII pairs. The 64-check closed-map cluster also
passes at the exact committed revision. It includes real source-map-join runs
with this proof enabled and disabled, exact prepublication work, complete
outputs, unknown runtime sources, wide keys, original/decoded programs and
restored build-owned descriptors. Final canonical map sorting can have
seed-dependent work, so the equality test checks work at its prepublication
frontier and compares every other execution-report field and all map entries.

The candidate is not promoted. Commit `36914cd38f513a553fb2f6e5c6c6efb2a4afdf1a`
restores the exact validated IR73 tree
`47d9431c97ba2db8543e3ea43d4d46f3fdf26010`; the experiment and raw evidence remain
in history. Canonical benchmark data is unchanged. The next experiment targets
source-index/address operations inside the counting loop rather than this
small preparation cost. No projected speedup is assigned.
