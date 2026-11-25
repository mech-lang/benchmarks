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
with the experimental record. The compiler now includes optional AArch64 immediate comparison lowering
and root allocation-profile support. The experimental build settings remain
unqualified for the complete M3 target. The Mechdeflate implementation has
not been edited.

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

## Complete conditional-immediate experiment

The clean `f15ebb6e818a8ce234575d3225af36203e442d23` compiler reproduced the
M1 baseline and the candidate artifacts. The candidate uses immediate CCMP
and CCMN instructions in the matcher. Its matcher body is 5,088 bytes versus
5,136 bytes in the baseline; the complete object is 157,136 versus 157,264
bytes. The source and canonical bytecode are identical.

Both full fixture orders used 96 balanced blocks per case and verified
1,965,312 runtime observations. Both complete Silesia orders used the original
12 manifest-verified files and pinned peers. No overlapping build or profiler
jobs were detected. All compressed streams matched and inflated independently.

| Mech actor | Fixtures vs Roc, forward / reverse | Fixtures vs libdeflate, forward / reverse |
| --- | --- | --- |
| Control in this run | 81 / 81 | 78 / 77 |
| Immediate comparisons | 81 / 81 | 78 / 78 |

| Candidate corpus result | Forward | Reverse |
| --- | --- | --- |
| Wins vs Roc | 12 / 12 | 12 / 12 |
| Wins vs libdeflate | 11 / 12 | 12 / 12 |

The fixture misses are `16384-distribution-change`, `reymont-prefix-1024`
and `prefix-natural-1024`. The forward Silesia miss is `mr`, at 1.002256 times
libdeflate; its reverse ratio is 0.989894. The corpus result formed by pairing
the two orders is 12/12, while requiring a win in each order gives 11/12.
The M3 qualification target remains open.

[Complete summary](ccmp-release-summary.json) ·
[Raw observations and build records](ccmp-release-observations.tar.gz) ·
[Member hashes](ccmp-release-observations.tar.gz.manifest.json) ·
[Exact timed actors](ccmp-recorded-actors/) ·
[Release recipe](ccmp-release-recipe.json)

## Complete source-to-executable timing

Three serial, alternating builds measured the entire compiler subprocess,
emitted files and final executable link. The compiler and fixed host support
were prebuilt, and the filesystem cache was warm. These are complete executable
builds from the same 243,209-byte Mech source.

| Executable boundary | Baseline median | Candidate median |
| --- | --- | --- |
| Standalone compression executable | 1.741574 s | 1.731905 s |
| Rust benchmark worker executable | 2.422706 s | 2.444269 s |

The candidate has no established compile-time advantage in these observations.
Earlier experimental settings enabled the register allocator's extra diagnostic
checker. That setting took 2.648335 seconds for the standalone executable and
3.315244 seconds for the worker. The release recipe uses the original setting.
A separate check reproduced both release executables byte for byte with the
extra checker enabled.

[Portable timing tool](time-encoder-builds.py) ·
[Diagnostic recipe](ccmp-candidate-recipe.json) ·
[Follow-up profiles, rejected source prototypes and parity checks](followup-experiments.tar.gz) ·
[Follow-up member hashes](followup-experiments.tar.gz.manifest.json)

One earlier full-run attempt ended before completion. Its partial data is
explicitly excluded and retained with the exploratory record. The completed
run above is the qualifying observation for this candidate.

## Updated compiler integration

The follow-up integrates upstream `8ce620d1b165b868210378ef260945ee3c398d05`.
The comparison selector consumes captured compilation inputs. The merged
compiler reproduces both complete artifact triples, including with optional
host reporting enabled. Six configuration/profile tests and three machine
execution tests passed. Further root allocation experiments use the existing
M3 Cranelift instruction samples and preserve all program checks. Their
subset screens do not establish an 81/81 or 12/12 result.


## Preparation worker counts

The updated compiler was measured three times at each worker count, with the
orders rotated. The full boundary includes source processing, emitted files
and the standalone executable link. All twelve builds produced the identical
executable, object and canonical bytecode. Count zero retains extra unused
scorer diagnostic detail in its descriptor.

| Workers | Median source-to-executable time |
| --- | --- |
| 0 | 1.808047 s |
| 1 | 1.763897 s |
| 2 | 1.775590 s |
| 4 | 1.767959 s |

The existing recipe uses two workers. These observations do not establish a
useful improvement from increasing that count.
[Raw build observations and telemetry](compile-worker-times/) ·
[Updated compiler checks and host reports](updated-compiler-checks/)

## Additional root allocation studies

The current compiler's optional root-weight hook was tested against the M3
instruction samples. The structural-only control reproduced the baseline
object, descriptor and bytecode exactly. Sample costs were then tested alone
and blended with the allocator's existing loop estimate. These are allocation
cost hints, not measured branch frequencies.

No new setting was promoted. The closest pilot, the geometric blend with the
loop estimate, won all ten protected cases against libdeflate in forward order
and eight in reverse. Its two-encoder screens measured MR at 0.988939 times
control and x-ray at 0.995693. Those screens do not establish a peer score or a
full-suite improvement. Changing root padding did not clear the remaining
misses. Removing the matcher's write-prefetch hints regressed protected cases
and was rejected. A fixed-extent no-prefetch variant was prepared but not timed.

A fresh check of the unchanged shipped M1 executable also missed protected
cases on M3: 9/10 forward and 6/10 reverse against libdeflate. The complete M3
result remains the conditional-immediate experiment above. An attempted rerun
that reused an existing output directory failed before timing; it is excluded
and the fresh `shipped-m1-fixtures-v2` record is used instead.

[Subset summary and decisions](root-allocation-summary.json) ·
[Root allocation profiles, instruction records, test harness and raw observations](root-allocation-studies.tar.gz) ·
[Verified member hashes](root-allocation-studies.tar.gz.manifest.json)
