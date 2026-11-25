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


## Exact counts and inline cleanup

Further work tested late dead values, proved stack reads, local forwarding,
shift-count normalization, inlining choices and allocation hints. These trials
keep the compressor source and canonical bytecode fixed. None cleared all
protected timing cases, so their settings were not promoted.

Untimed native counters cover all 81 fixtures and all 12 complete corpus files,
with two matching, output-verified observations per input. The root has 3,699
instrumented machine blocks; the scorer has 61. Fixture counts use the actual
prepared-capacity interface. Full-file counts use the deployed encoder's
empty output loan. These counts and the sampled cost hints are distinct from
primary latency measurements. Counter tools, failed setups, rejected compiler
patches, tests, settings and raw observations are retained.

[Study summary](late-inline-studies-summary.json) ·
[Complete diagnostic archive](late-inline-studies.tar.gz) ·
[Member hashes](late-inline-studies.tar.gz.manifest.json)

## Paired append stores

Mech `71bb1f90b39ad0bceebf1b5871a375de19683ac8` adds an optional compiler pass
that combines two neighboring U64 writes already admitted by the exclusive
NoGrowth append contract. It preserves memory flags and guards and rejects
intervening effects, mismatched geometry, alignment claims and debug metadata.
The generated scorer contains one paired store in place of the two stores.
The compressor source and canonical bytecode remain unchanged.

A clean rebuild reproduced the baseline and candidate artifacts byte for byte,
including with host reporting enabled. Two native differential/refusal tests
and six configuration tests passed. The archived resource gates retained all
162 exact-output and alias checks, all 12 injected failures and exact recoveries,
and the same per-case native stack observations: 5,024 bytes maximum under the
5,280-byte ceiling.

| Full executable build boundary | Control median | Paired-store candidate median |
| --- | --- | --- |
| Standalone encoder | 1.803042 s | 1.797063 s |
| Rust benchmark worker | 2.440799 s | 2.454649 s |

Each median uses three alternating serial builds from the unchanged Mech source
through the final executable link. The compiler and fixed host support were
prebuilt and caches were warm. These observations do not establish a compile-time
advantage.

The first ten-case, 24-block screen missed one libdeflate comparison per order,
by 0.07% and 0.61%. Selected full-file screens measured MR at 0.994851 times
control and x-ray at 0.992986; those are two-actor screens without peer scores.
The longer 96-block fixture run then missed `16384-distribution-change`: the
candidate's paired libdeflate ratio was 1.062454, versus 1.016539 for the control.
That is about 4.5% slower than the control on that case. The forward 81-case
order finished; the all-suite attempt was stopped during reverse order after
that miss and is excluded from complete qualification. It did not run the full
Silesia qualification. No new complete 81/81 or 12/12 score is claimed.

Fresh PC samples cover the actual fixture timer boundary, including heap setup,
output transfer and cleanup, while excluding preparation, validation and
inflation. On the 16 KB control, about 32% of samples are in scoring, 32% in
matching and 22% in the generated root. The root's normalized instruction
sequence and external relocation names match between these two actors; sample
shares alone do not establish a change in its generated work. Fresh-support
screens with the original matcher also miss protected cases.

[Follow-up summary and interruption record](paired-append-followup-summary.json) ·
[Fresh rebuild, resource gates, build timings, profiles and partial observations](paired-append-followup.tar.gz) ·
[Member hashes](paired-append-followup.tar.gz.manifest.json) ·
[Exact timed executables](paired-append-recorded-actors/) ·
[Portable candidate recipe](append-store-pairs-recipe.json)

To reproduce this unqualified candidate, use the existing `rebuild.py` and
`replay.py` commands from the M3 handoff with `--recipe` pointing to
`m3-20261124/append-store-pairs-recipe.json`, and check out its pinned Mech
revision. The winning M1 recipe remains the default.

## Literal recurrence and counter loads

Further compiler trials changed literal field packing, carried the wrapping cost
independently of the packed output word, and loaded small batches of histogram
counters before storing them. The latter accounts for every earlier colliding
key and preserves source-order stores. These changes use the unchanged Mech
compressor source and canonical bytecode.

A revised profile adapter also keeps new register-copy blocks from splitting
the literal loop's exit, removing an extra branch introduced by the first
profile transfer. The adapter retains every executable machine block and the
compiler's normal permutation and branch validation.

The literal-packing and cost-carry patches passed six focused tests each, with
18 and 34 native option combinations respectively. Counter gathering passed
60,928 native differential calls covering collisions, wrapping arithmetic and
batch boundaries. The default setting reproduced the M1 artifact triple;
every final candidate passed all 162 output, inflation, capacity and alias
checks.

All timed candidates still missed protected libdeflate cases in the ten-case,
24-block screens. None was promoted, and none establishes a new complete
81-case or 12-file score. The archive includes the compiler patches, exact
timed actors, profiles, failed setups and raw timing data. Preparation build
times in these diagnostics are excluded from primary compile-time comparisons.

[Candidate summaries and timing misses](literal-carry-counter-studies-summary.json) ·
[Source, actors, tests and raw screens](literal-carry-counter-studies.tar.gz) ·
[Verified member hashes](literal-carry-counter-studies.tar.gz.manifest.json)

## Conditional increments and four-literal batches

The next compiler trial fuses addition of a single-use integer comparison into
an ARM conditional increment. Tests caught and corrected its initial option
gating; native inspection then rejected a broader form that repeated shared
comparisons. The final rule preserves shared predicates and leaves the default
M1 artifact triple unchanged, including when enabled without counter gathering.
It passes 2.88 million native arithmetic checks, also with the compressor's I32
result-reuse setting enabled.

Counter gathering was screened with ordinary boolean additions and conditional
increments. The existing four-literal append option was separately rebuilt with
the clean pinned `71bb1f90b3` compiler. Each final candidate passed all 162 output,
inflation, capacity and alias checks. One four-literal variant and one conditional-increment
variant reached 9/10 protected libdeflate wins in both orders, but still
missed the 16 KB distribution-change case. No candidate was promoted.

These are ten-case, 24-block screens, with build activity excluded from timing.
They do not replace the last complete M3 result or establish a compile-time
improvement. The archive separates the broader prepared-but-untimed rule from
the final timed candidates and includes source patches, exact actors, profile
transfers, test logs, failed setups and raw measurements.

[Trial summaries](conditional-counter-batch-studies-summary.json) ·
[Compiler patches, exact actors and raw data](conditional-counter-batch-studies.tar.gz) ·
[Verified member hashes](conditional-counter-batch-studies.tar.gz.manifest.json)

## Previous-cell cost reuse and refreshed profiles

The next compiler prototype reused an existing I32 previous-cell cost for
proved low-word consumers of full packed loop parameters. It preserved full-word
observers and introduced no additional loop state or memory operations. An
initial attempt to retain value IDs across cleanup failed before timing; the
revised implementation discovers live SSA values and proves every incoming
append edge. Its 2,160 differential native input cases passed (4,320 calls),
along with captured-configuration checks and default M1 artifact parity.

Six source/profile combinations and four additional refreshed-profile layouts
were timed. Every actor passed the 162 codec, boundary and alias checks, but
every timed variant missed at least one protected fixture in at least one
order. The prototype is not selected. These remain ten-case, 24-block screens;
there is no new full-suite or source-to-executable timing claim.

Diagnostic block counters also produced two matching, output-verified
observations for every one of the 81 fixtures and all 12 full corpus files.
The new four-literal CFG had eleven allocation blocks inheriting cold weight
one from the earlier profile, including blocks executed thousands of times on
the 16 KB input. Fresh allocation hints and layouts used 66 active non-heldout
fixtures plus Dickens, Mozilla, MR and X-ray. Named heldout fixtures and the
other eight corpus files were excluded from training. A checked CFG/label
transfer allowed those native counts to guide the newly allocated body.

An offline constrained layout reduced predicted branches on every training
input, including the 16 KB case and MR, but made the measured 16 KB latency
worse. Branch-count reductions are not reported as speedups. The solver is an
analysis tool only; it adds no compiler or project dependency. All counters,
profile producers, solver inputs, hashes, failed setups, exact actors and raw
screens are retained, and diagnostic timings are excluded from performance
claims.

[Trial summaries](current-carrier-cost-studies-summary.json) ·
[Compiler patches, actors, counts and raw screens](current-carrier-cost-studies.tar.gz) ·
[Verified member hashes](current-carrier-cost-studies.tar.gz.manifest.json)

## Masked equality lowering

An opt-in Cranelift rule replaced equal-mask Eq/Ne comparisons with a masked
XOR flag test. It kept independent observers and declined comparisons where
both masks had to remain. All 583,680 native differential calls passed, along
with seven configuration/profile checks, disabled-rule M1 artifact parity and
162 codec/alias/boundary checks for each timed actor.

The matcher emitted the intended native sequence, but all four timed variants
missed protected fixture comparisons. The compiler prototype is not selected.
The root also grew by 48 bytes, so the earlier exact root-padding profile was
rejected and disabled for these trials. Original and fixed matcher extents
were measured separately. These ten-case, 24-block screens establish no new
complete M3 score or compile-time improvement.

[Trial summaries](masked-equality-studies-summary.json) ·
[Compiler source, actors and raw screens](masked-equality-studies.tar.gz) ·
[Verified member hashes](masked-equality-studies.tar.gz.manifest.json)

## Independent prefix-cost arithmetic

The next compiler prototype computed two/four-item wrapping increments
independently of the existing previous-cell cost, while retaining every
intermediate packed output. Native code inspection confirmed one carry-dependent
ADD per batch. The prototype passed the focused native checks in 18 append
modes, default M1 artifact parity, and all 162 codec, alias and boundary checks
for each of the four timed actors.

All four variants still missed protected fixture comparisons. Shortening this
dependency did not establish a speedup, and the prototype is not selected.
These are ten-case, 24-block screens in both orders, with eligible quiet-run
telemetry. There is no new complete M3 score or compilation-time claim.
The compressor source and benchmark timing protocol remain unchanged.

[Trial summaries](prefix-cost-studies-summary.json) ·
[Compiler source, actors and raw screens](prefix-cost-studies.tar.gz) ·
[Verified member hashes](prefix-cost-studies.tar.gz.manifest.json)

## Pairing across pure packing operations

The existing admitted append-store pairing pass was extended to cross up to
eight explicitly whitelisted nontrapping I32/I64 operations. Loads, division,
guards, calls and unknown instructions remained barriers; all flags, geometry,
source-location and ownership requirements stayed intact. The native tests
covered interleaved four-word packing, full and low-word observers, wrapping
values and eight-byte alignment, with 8,192 paired/unpaired execution calls.
The focused checks, default M1 artifact triple and 162 codec checks per actor
passed.

Actual allocated code combined the four-item body's four separate stores into
two paired stores with one shared output address. The body shrank from 35 to
31 native instructions. All four timing variants still missed protected
fixture comparisons, so the compiler prototype was archived and restored.
These ten-case screens establish no new complete score or compilation-time
improvement. No additional optimization setting was introduced for this pass.

[Trial summaries](packing-pairs-studies-summary.json) ·
[Compiler source, actors and raw screens](packing-pairs-studies.tar.gz) ·
[Verified member hashes](packing-pairs-studies.tar.gz.manifest.json)

## Sharing packing across conditional stores

Native inspection found that egraph elaboration repeated a packed word's
mask, shift and OR before a conditional store and again at its join. A bounded
post-egraph compiler pass shared exact nontrapping scalar expressions when
their inputs were available before the branch. A second version restricted
sharing to complete packing trees actually written by the conditional store.
Both versions retained memory operations, guards and ownership actions in place.

Each version passed 143,360 differential native calls, seven captured-input
checks, default M1 artifact parity and all 162 codec checks per timed actor.
The small reproducer emits one packing sequence instead of two. Actual
compressor objects also remove repeated packing, but introduce additional spill
traffic elsewhere. Every one of the four timed actors still missed protected
fixture comparisons. Neither prototype is selected, and the source changes
were restored.

The archive includes both compiler versions, native selection evidence,
mechanically transferred profiles and all raw ten-case screens. An initial
root route-dump build changed native output and failed parity against an
ordinary capture; it is diagnostic only and was excluded from timing. Ordinary
matcher/scorer captures reproduce one another exactly. These subset screens
establish no new complete score or compilation-time improvement.

[Trial summaries](diamond-packing-studies-summary.json) ·
[Compiler source, actors and raw screens](diamond-packing-studies.tar.gz) ·
[Verified member hashes](diamond-packing-studies.tar.gz.manifest.json)
