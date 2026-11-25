# Apple M3 retest and optimization record

This run starts from Mech `35784003b9149fe8059fa83dd5d0aff10dbcd631` and the
[published winning M1 recipe](../word-mismatch-order/recipe.json). The source,
canonical bytecode, corpus, references and timing boundaries stay fixed.
The full M3 baseline is complete; optimization experiments remain in progress.

## Complete baseline

The local clean compiler rebuild reproduced all three pinned artifacts:

| Artifact | SHA-256 |
| --- | --- |
| Native object | `e4325602c6a5a4507ba637eee5d34ada9bda77bbb334fefb8ff53324d720e214` |
| Canonical bytecode | `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3` |
| Descriptor | `c2448f4197863733301810dca0e8d721d1932afa32b5172e933843b07e2464ef` |

The complete 81-case suite used 96 balanced blocks per case in each order,
with 1,965,312 observations across both orders. Both complete Silesia orders
used all 12 manifest-verified inputs and the original reference executables.

| Suite | Mech wins vs Roc, forward / reverse | Mech wins vs libdeflate, forward / reverse |
| --- | --- | --- |
| 81 fixtures | 81 / 81 | 80 / 80 |
| 12 complete Silesia files | 12 / 12 | 11 / 12 |

The fixture miss is `16384-distribution-change`. The Silesia miss is `mr`
in the forward order. All streams matched their references and inflated
independently. The paired Silesia result against libdeflate is 11/12 when a
case must win in both orders.

One complete source-to-worker-executable build took **3.424792 seconds**,
including the host worker link, with the compiler and fixed runtime already
built. This is one observation, not a median. The separate clean compiler
bootstrap took 8 minutes 47 seconds and is excluded from that measurement.

[Summary and build receipt](baseline-summary.json) ·
[Raw observations](baseline-observations.tar.gz) ·
[Archive manifest](baseline-manifest.json) ·
[Portable rebuild and replay commands](../word-mismatch-order/M3.md)

## Profiling and exploratory work

The `mr` encoder samples place about four fifths of native work in the match
finder, followed by the cost scorer. The 16 KB fixture also spends substantial
time in the generated root. Fixture worker samples include validation outside
the encoder timer; they are diagnostic observations, not isolated component
timings.

Exploratory fixture screens use a six-case subset and 24 balanced blocks per
order. Exploratory corpus screens compare the baseline with a candidate on
selected complete files. These screens do not establish an 81/81 or 12/12
qualification. Final qualification must use both original complete suites on
one pinned build.

Experiments include spill-cache settings, address normalization, branch
selection, root argument forwarding, function alignment, and compiler-source
prototypes. Rejected source prototypes and their correctness checks are kept
with the experimental record. None has been adopted into the compiler by
this report. The Mechdeflate implementation has not been edited.

[Diagnostic samples and instruction records](profiles.tar.gz) ·
[Profile archive manifest](profiles.tar.gz.manifest.json) ·
[Exploratory raw data, settings and rejected source patches](experiments.tar.gz) ·
[Experiment archive manifest](experiments.tar.gz.manifest.json)

Preparation timings in exploratory build receipts are not primary compile-time
measurements. Some temporary compiler binaries contain a prototype that is
disabled for subsequent settings trials. Any selected candidate must be
rebuilt from the clean pinned source, reproduce its three encoder artifacts,
and run both complete suites before qualification. The first 64-byte-alignment
corpus screen is explicitly excluded because it overlapped candidate
preparation; its serial replacement is retained separately.
