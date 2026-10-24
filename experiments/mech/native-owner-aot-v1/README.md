# Source-map standalone performance

This study measures a Mech state machine that explicitly traverses a String, selects each window, tests map membership, reads the previous count, inserts a caller-produced count and advances its state. The compiler retains general hash storage while compiling those operations from Mech. The current source is [knucleotide-source-map.mec](knucleotide-source-map.mec), SHA-256 `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`.

## Current twelve-round budget-mutex retry

Extending bounded retry from ten to twelve rounds reduces the full-input median
**2.24% initially and 1.27% in an independent repeat**. The repeat gives Rust
**0.5537 s / 1.000×**, ten-round Mech **0.7198 s / 1.300×**, and current Mech
**0.7107 s / 1.284×**. Separate counters give kernel CPU **0.05 → 0.04 seconds**,
involuntary switches **9,418 → 6,009**, and 2.7% fewer cycles.

The [report](escrow-backoff12-checkpoint-v1/README.md) retains both batches, the
separate prefix, fresh exact-code profiles and new worker-appearance observations.
Current Mech workers appear near 0.22–0.24 seconds, versus 0.12–0.15 for Rust in
separate polling diagnostics. Serial preparation is the next investigation;
those bounds are not exact phase timers. All 404 checks pass, and
[verification](escrow-backoff12-checkpoint-v1/results.json) checks 78 terminal
owned processes. Source, bytecode, generated object and finite debit logic remain
unchanged. Rust parity is incomplete.

## Earlier ten-round budget-mutex retry

Extending bounded retry from eight to ten rounds cuts kernel CPU from **0.10 to
0.06 seconds** and involuntary switches from **19,421 to 9,621** in separate
counter runs. Full-input medians improve **2.58% initially and 0.74% in a separate
repeat**. The repeat gives Rust **0.5545 s / 1.000×**, eight-round Mech
**0.7435 s / 1.341×**, and current Mech **0.7379 s / 1.331×**.

The change is retained. Small-input direction reverses between two separate
batches, so no prefix gain is established. The [report](escrow-backoff10-checkpoint-v1/README.md)
retains both full-input batches, both prefix batches, fresh profiles, counters
and limitations. All 26 worker-budget tests, 377 native tests and one catalog
check pass at the exact timed revision. [Verification](escrow-backoff10-checkpoint-v1/results.json)
checks 84 terminal owned processes. Source, bytecode, generated object, debit
logic and canonical data remain unchanged; Rust parity is incomplete.

## Earlier eight-round budget-mutex backoff

Extending the existing bounded retry from six to eight rounds reduces the full-input
median **2.13% initially and 2.23% in an independent repeat**, with five faster
matched pairs in each six-order batch. The repeat gives Rust **0.5621 s / 1.000×**,
six-round Mech **0.7607 s / 1.353×**, and current Mech **0.7438 s / 1.323×**.
Kernel CPU falls from 0.16 to 0.11 seconds and involuntary switches about 29%;
user CPU rises. The change is retained, with every budget check unchanged.

The [report](escrow-backoff8-checkpoint-v1/README.md) records both batches,
exact-code profiles, separate counters and the remaining serial-preparation gap.
All 26 worker-budget tests, 377 native checks and one catalog check pass at the
exact timed revision. [Verification](escrow-backoff8-checkpoint-v1/results.json)
checks 36 full-input observations, three exact-code profiles and 78 terminal
processes. The generated Mech object, performance source, bytecode and canonical
data remain unchanged; Rust parity is incomplete.

## Rejected runtime refill experiment

Precomputing full-batch charges outside the budget mutex initially reduced the
median 1.38%, but an independent repeat regressed 2.03%. The candidate is reverted;
accepted IR78 remains the production implementation. In the repeat, Rust takes
**0.5566 s / 1.000×**, accepted Mech **0.7408 s / 1.331×**, and the rejected
candidate **0.7559 s / 1.358×**. Both batches, exact-code profiles, counters and
validation are retained in the [experiment report](refill-fastpath-checkpoint-v1/README.md).
Worker stacks identify budget-mutex parking/waking as a remaining hypothesis;
those samples do not establish how much elapsed time can be saved.

## Earlier separate lookup functions

IR78 separates admitted cached and ordinary hash loops. Six balanced full-input
cohorts give Rust **0.5517 s / 1.000×**, IR77 parent **0.7614 s / 1.380×**, and
candidate **0.7490 s / 1.358×**: **1.64% lower median**, with six faster pairs
and overlapping ranges. Full output, 874,999,961 updates, seven maps/workers and
five cache admissions are verified. The separate prefix improves 10.52%.

Fresh exact-code inspection confirms **zero stack accesses** on all fifty
audited cycles; cached paths have 16–17 instructions and ordinary paths 36–39.
Whole-process instructions fall another 10.4%, but elapsed time remains above
Rust. Work accounting and waits occupy 19.31% of fresh worker observations;
these are not wall-time shares. **377 native checks plus one catalog check pass
at the exact timed revision.** The [report](lookup-split-checkpoint-v1/README.md)
records the profile, resource admission, optional snapshot fallback and initial
qualification failure. [Verification](lookup-split-checkpoint-v1/results.json)
checks 18 primary full observations, three exact-code profiles, eighteen malformed
metadata rejections and 54 terminal owned processes. Source and canonical data
are unchanged; Rust parity remains incomplete.

## Earlier bounded lookup-cache experiment

IR77 / ABI28 / work66 adds an admitted cache over a complete finite key domain,
while retaining the underlying hash maps and every original update. Six balanced
complete-process cohorts give Rust **0.5580 s / 1.000×**, IR76 parent
**0.7854 s / 1.407×**, and candidate **0.7740 s / 1.387×**. The median improves
**1.45%**, with six faster pairs and slightly overlapping ranges. Separate
counters fall **24.3% in instructions** and **26.3% in cycles** against the
parent; the candidate now retires fewer instructions than Rust while remaining
slower in elapsed time. The separate prefix cohort regresses 14.2% and remains.

Three exact-code profiles show more work-budget contention. Static examination
also finds a newly spilled hashing constant in large-domain loops and redundant
join work in some cached paths. Read-only thread observations motivate checking
preparation and the longest workers. These are hypotheses, not established cost
attributions. The [report](direct-lookup-cache-checkpoint-v1/README.md) records
all results, failed attempts and remaining options. Production-equivalent full
validation passes **374 native checks plus one catalog check**; its revision
differs from the timed production source only in an exact-memory test fixture.
[Verification](direct-lookup-cache-checkpoint-v1/results.json) checks 18 primary
full observations, three exact-code profiles and 69 terminal owned processes.
Canonical benchmark data and the performance source are unchanged; Rust parity
is incomplete.

## Earlier cold-reconstruction experiments and profile

IR75 and IR76 attempt to reconstruct original source/frame values at cold exits. Neither produces a measurable improvement. In the latest independent six-cohort comparison, Rust is **0.5577 s / 1.00×**, IR75 control **0.7848 s / 1.407×**, and IR76 candidate **0.7847 s / 1.407×**, with only three faster pairs. Three exact-code Mech captures put **84.75%** of worker observations in generated counting loops; the source-index reconstruction remains on the actual hot path. Separate counters give **39.750 billion instructions** against Rust's **33.153 billion**. Three fresh protected Rust profiles accompany the comparison. Worker samples include waits and are not elapsed-time shares.

At the exact IR76 revision, **369 native checks plus one catalog check pass**, with three existing manual exclusions. The [profile report](cold-reconstruction-checkpoint-v1/README.md) records both separate cohorts, all six Mech profiles, fresh Rust profiles, counter comparisons and remaining hypotheses. [Verification](cold-reconstruction-checkpoint-v1/results.json) checks 36 complete-process primary observations, 21 malformed metadata rejections and 117 terminal owned processes. Canonical benchmark data is unchanged; no speedup or Rust parity is established.

## Earlier cursor experiment and profile

Compiler [`c7574fa95`](https://github.com/mech-lang/mech/commit/c7574fa952a9981e1b2b0659a510fc05eff1c2ff), **IR74 / ABI27 / work65**, uses the source-certified adjacent byte cursor while preserving the original scalar continuations and exact finite fuel. Six balanced [full-input cohorts](full-affine-cursor-cohort-v1/results.json) give Rust **0.562 s / 1.00×**, IR73 parent **0.798 s / 1.42×**, and cursor candidate **0.786 s / 1.40×**. The candidate median is 1.52% lower, with only three faster pairs and overlapping ranges; no robust speedup is established. Every full Mech execution verifies complete output, 874,999,961 physical updates, seven maps and peak workers, and secured startup/shutdown.

Three fresh [exact-code profiles](affine-cursor-remaining-profile-v1/results.json) contain 6,844 worker observations: **84.40%** generated loops, **6.84%** storage, **4.37%** active accounting, **1.49%** accounting waits and **2.91%** bridge/other work. These are thread samples including waits, not wall-time shares. The [static paths](affine-cursor-codegen-audit-v1/steady-paths-v2.json) remain **37–39 instructions/five branches/no stack accesses**: source-counter reconstruction is still present inside the native loop. Separate counters fall only 0.27% in instructions and 0.63% in cycles. Explicit cold source-state recipes remain the next unimplemented hypothesis.

At the exact timed revision, **365 native checks plus one catalog check pass**, with three existing manual exclusions. [The profile report](cursor-profile-checkpoint-v1/README.md) records the tentative timing result, admitted code/stack and remaining machine instructions. [Verification](cursor-profile-checkpoint-v1/results.json) checks 36 full-input observations across two independent trials, four completed exact-code profiles, twelve malformed-metadata rejection cases and 106 terminal owned-process receipts. The preceding source-alphabet scan trial regresses 1.54% and is reverted; its raw evidence remains. Canonical benchmark data is unchanged and Rust parity remains incomplete.

## Retained counting-loop checkpoint

Compiler [`393d23b24`](https://github.com/mech-lang/mech/commit/393d23b24b80cad13e2c2b0284823290d7bafacf), **IR73 / ABI27 / work65**, retains the unchanged string/map source and bytecode. It adds separate precise cold snapshots, direct entry/update continuations, a peeled first probe group and a caller-bound prepaid stopping extent. The [full strategy report](strategy-search-v2/README.md) records each stage, the rejected callee-bound extent and the exact-code evidence.

| 125-million-base executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.562 | 1.00× |
| Direct-entry IR71 control | 0.790 | 1.41× |
| Caller-bound extent IR73 | 0.782 | 1.39× |

Six balanced [complete-process cohorts](full-caller-extent-cohort-v1/results.json), including secured startup/shutdown, retain every process and outlier. The latest stage is only a **1.03%** median reduction against IR71, four faster/two slower pairs with overlapping ranges. All Mech full processes verify complete output, **874,999,961 physical updates**, seven complete maps and peak workers under the unchanged finite policy. Full validation at the exact timed source revision passes **365 native checks plus one catalog check**, with three existing manual exclusions. Three profiles match the entire timed machine-code section. Canonical benchmark data is unchanged; Rust parity remains incomplete.

A [separate matched compiler diagnostic](backend-comparison-v4/results.json) compiles the same unchanged Rust source through LLVM and the official unmodified Rust Cranelift backend. In that cohort, the protected Rust control is **0.562 s / 1.00×**, matched LLVM **0.560 s / 1.00×**, stock Rust Cranelift **7.484 s / 13.32×**, and current Mech **0.786 s / 1.40×**. Shared precompiled library code, different or unestablished embedded backend versions and different compiler pipelines prevent treating this as an isolated backend ceiling. It supports further investigation of lowering/inlining rather than a claim of general language superiority. All failed setup attempts and all 48 completed diagnostic observations remain.

[Checkpoint verification](strategy-search-v2/results.json) checks 72 primary full-input observations across four separate stage cohorts, twelve exact-code profiles, nine malformed-metadata rejection cases, the backend diagnostic and 281 terminal owned-process receipts. The stages are not pooled. The historical checkpoints below retain their own controls and measurements.

## Earlier checkpoint: bounded width versions and productive source-header entry

Compiler [`9dd35e68a`](https://github.com/mech-lang/mech/commit/9dd35e68a5e46b77823ce86c98a2252bdb2be9fe) retains the unchanged Mech source and bytecode with **IR69 / ABI27 / work65**. Six balanced [complete-process full-input cohorts](full-productive-entry-cohort-v1/results.json), including secured startup and shutdown, give:

| 125-million-base executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.558 | 1.00× |
| Validated IR65 Mech reference | 0.870 | 1.56× |
| Width versions and productive-header candidate | 0.832 | 1.49× |

The median falls **4.39%**, with a faster Mech result in all six pairs. Candidate/reference ranges are 0.816–0.846 / 0.846–0.884 seconds. Every observation remains. All Mech full executions verify complete output, **874,999,961 physical updates**, seven packed SSA maps and peak workers, guarded bounds/calls, five complete frozen maps and ten original reads. No source window, map update, final traversal, debit, finite allowance or security setting is omitted or increased. Canonical benchmark data is unchanged, and Rust parity remains incomplete.

The compiler emits all **18 widths admitted by the private storage format**, plus its original generic arm, from the same source graph. A one-time switch tests the actual immutable width; constructor-derived masks become constants. The original fuel check moves onto each incoming active-header edge. A source-certified productive guard admits the hot traversal; a terminal traversal returns **before its original header** so the outer source implementation performs the exact debit, guards, state transition and terminal visit. Missing keys still return at their exact source successor after completing membership once; growth, precise failures and refills remain in the original implementation. The funded function has no native helper call.

The native code/stack admission includes all arms and nested calls: **92,272 code bytes / 1,232 stack bytes** overall, with **17,092 / 96 bytes** per funded function. The actual fixed template is 518 instructions inside the unchanged 1,024 envelope; source/snapshot maxima are 51/20 inside the unchanged 512 envelope. The 19-word frame, Rust helper ABI27, finite ledgers, refill limit and lock-release bounds remain.

The [width-only stage](width-specialization-diagnosis-v1/results.json) measured Rust **0.559 seconds**, IR65 **0.871 / 1.56×**, and candidate **0.857 / 1.53×**: only a 1.50% median reduction, four faster/two slower pairs and overlapping ranges, for approximately eighteen-fold function growth. Its separate counter cohort reduces instructions 6.72% and cycles 2.65%. The [fuel-edge stage](fuel-edges-diagnosis-v1/results.json), compared with the width-only parent in its own cohort, measured Rust **0.556 seconds**, parent **0.859 / 1.55×**, and candidate **0.838 / 1.51×**: a 2.46% reduction, five faster/one slower pairs. These stages are not pooled or treated as additive effects.

Two fresh one-million-base prefix cohorts for the final candidate remain separately recorded, with one excluded warmup and three observations per subject. The [original comparison against IR68](productive-entry-timing-v1/results.json) has Rust **0.0177 seconds**, parent **0.1087 / 6.15×**, candidate **0.1207 / 6.83×**, an 11.04% median regression. A [direct comparison against IR65](productive-entry-reference-prefix-v1/results.json), reusing only the identical completed build, has Rust **0.0131 seconds**, reference **0.0998 / 7.62×**, candidate **0.0856 / 6.54×**, a 14.22% reduction. Prefix ranges overlap and absolute times vary substantially. Neither batch is discarded or pooled with full input; these results limit claims about small-input performance.

Three [exact-code full profiles](productive-entry-remaining-profile-v1/results.json) partition 7,372 worker observations: **85.96%** generated loops, **1.34%** budget waits, **4.22%** active accounting, **5.87%** storage helpers and **2.60%** bridge/other active work. The profiling copy matches all **4,312,408 machine-code bytes** of the timed executable. Samples include waiting threads and are not wall-time shares or CPU utilization. The [nineteen actual steady paths](productive-entry-codegen-audit-v1/steady-paths.json) retain **44–48 instructions, six branches and no stack accesses** under recorded productive/funded/first-hit conditions, versus Rust's **34/four/two**. Three or five zero/one moves still occur in those hot paths for cold-state handling. Static counts do not establish individual instruction costs.

[Separate complete-process counters](productive-entry-hardware-v1/results.json) give current **46.70 billion instructions / 11.31 billion cycles**, the IR68 parent **46.92 billion / 11.40 billion**, and Rust **33.14 billion / 7.89 billion**. The counter parent differs from the primary IR65 control; rounded counter timers are not primary timings. Whole-process instruction and cycle gaps remain substantial.

[Full native validation](../native-owner-dispatch-v1/productive-entry-native-v1/summary.json) passes **364 tests**, plus the [catalog integration test](../native-owner-dispatch-v1/productive-entry-catalog-v1/summary.json), with three existing manual exclusions, at the exact timed source revision. Focused checks also execute every admitted width through original/decoded source, complete maps, arbitrary seeds/starts, growth/refills, exact finite work and original failure frontiers. [Checkpoint verification](strategy-compiler-checkpoint-v1/results.json) retains all **72 full-input observations** from four compiler trials, recomputes their independent statistics, verifies entire profile/timed code identity, negative metadata fixtures, protected source/input/reference/policy/data pins and terminal owned process receipts. The rejected immutable-snapshot trial remains below.

The [current diagnosis](productive-entry-diagnosis-v1/results.json) prioritizes broader **cold source-state reconstruction**: separate cold snapshots per incoming edge, retire invocation context pointers from hot registers, and reconstruct proved affine values at exact exits. Source-certified cursor representation and generic native selection/probe improvements remain further candidates. [Pinned backend inspection](width-specialization-diagnosis-v1/backend-inspection.json) confirms that generic single-value phi propagation already exists; duplicating it is not a supported optimization hypothesis. None of the remaining candidates has an assigned speedup. Separate decoded-source standalone qualification and secured/trusted startup comparison also remain incomplete.

## Helper-free source continuations and the remaining compiler gap

At the preceding stage, compiler [`f02fbe82f`](https://github.com/mech-lang/mech/commit/f02fbe82f3b0dbf178ffc2f6b1c5431ce3643e63) retains the unchanged Mech source and bytecode, **IR65 / ABI27 / work65**, and every original source window, membership/read/replacement, finite debit and failure origin. A source-derived native counting function runs after a certified completed recurrence. Fuel exhaustion returns before its original header; a membership miss completes that action once and returns to its original successor. Growth, refill, unsupported states and precise failures remain in the outer source continuation. Storage pointers refresh after helpers. The counting function contains no native helper call and retains every physical table update.

Six [balanced full-input cohorts](full-steady-fold-cohort-v2/results.json) retain every process, including secured startup and shutdown, with no excluded warmup or outlier:

| 125-million-base executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.552 | 1.00× |
| Retained bounded-backoff Mech | 0.899 | 1.63× |
| Mech with funded source continuations and scalar/control folding | 0.855 | 1.55× |

The latest build is **4.91% lower in median runtime**, with a faster Mech observation in all six matched pairs. Mech ranges are 0.817–0.867 seconds for the candidate and 0.882–0.918 for the control; Rust ranges 0.546–0.666. All observations remain. Each Mech process reports **874,999,961 physical updates**, seven packed SSA maps, seven peak workers, guarded bounds/calls, five complete frozen maps and ten original reads. Source, input and the established full launch policy are unchanged. Canonical benchmark data is unchanged; Rust parity is incomplete.

The preceding [IR64 stage](full-steady-cohort-v1/results.json), before the extra scalar/control folding, measured Rust **0.559 seconds**, retained Mech **0.899 / 1.61×**, and candidate **0.870 / 1.56×** in three separate matched cohorts: a modest 3.21% median reduction. The two full cohorts have their own controls and denominators; they do not isolate the incremental wall-time effect of the extra data pass. On a fresh one-million-base [prefix comparison against the retained build](steady-fold-reference-prefix-v1/results.json), Rust is **0.0194 seconds**, retained Mech **0.0995 / 5.13×**, and latest Mech **0.1022 / 5.27×**. Prefix ranges overlap; no prefix gain is established. Earlier [IR64](steady-timing-v1/results.json) and [IR65 versus IR64](steady-fold-timing-v1/results.json) prefix cohorts remain separately recorded.

Three [current exact-binary profiles](steady-fold-remaining-profile-v1/results.json) partition 7,673 worker observations: **87.05%** generated counting loops, **1.03%** budget waits, **4.04%** active budget work, **5.59%** storage helpers, **1.02%** generated helper bridges and **1.28%** other active work. Of 6,679 generated-loop observations, 6,616 occur in the new funded functions. The profiling executable has the timed executable's exact entire machine-code section. These are sampled thread observations, including waits, not wall-time shares or CPU utilization.

The [IR64 static first-hit path](steady-codegen-audit-v1/steady-path-comparison.json) drops from the retained loop's 66 instructions/eight branches/three stack loads to 54/seven/zero. The [IR65 path](steady-fold-codegen-audit-v1/steady-path-comparison.json) is **55 instructions/six branches/zero stack accesses**, versus Rust's **34/four/two**, under each recorded productive, funded, first-fingerprint/full-key-hit condition. The extra pass removes two literal-true branches but changes register allocation and adds moves; smaller code is not a proportional runtime result. [Separate counters](steady-hardware-v1/results.json) measure IR64 at 54.51 billion instructions and 12.13 billion cycles versus 64.82 billion/12.74 billion for the retained build: approximately 16% fewer instructions but 5% fewer cycles. A separate [IR65 versus IR64 counter cohort](steady-fold-hardware-v1/results.json) has 55.42 billion/11.64 billion versus 54.53 billion/11.94 billion. Counter timer rounding is not used for primary timings.

Each IR65 funded function occupies 984 code bytes and 96 stack bytes. Its code and maximum nested stack remain included in native admission. Source/setup/snapshot/caller instruction bounds remain inside the original 512/1,024 envelopes; no work allowance, chunk size, fuel cap or security policy is increased. [Full native validation](../native-owner-dispatch-v1/steady-fold-native-v2/summary.json) passes **364 tests**, plus the [catalog integration check](../native-owner-dispatch-v1/steady-fold-catalog-v1/summary.json), with three existing manual exclusions. The validated head `8eb6db853` differs from the timed production revision only in two corrected identity-version test expectations. Focused tests cover changed inputs, complete maps, growth/refills, source/decoded artifacts, arbitrary seeds, exact work, finite limits and original overflow/failure frontiers.

All initial failures remain: [two module-path compilation errors](../native-owner-dispatch-v1/steady-focused-v1/summary.json), [over-conservative work-envelope pairing](../native-owner-dispatch-v1/steady-focused-v2/summary.json), [two incorrect new test expectations](../native-owner-dispatch-v1/steady-focused-v3/summary.json), and [two stale identity assertions in the first full run](../native-owner-dispatch-v1/steady-fold-native-v1/summary.json). The [first full timing attempt](full-steady-v1/failure.json) accidentally inherited the prefix comparison-work cap and correctly failed on finite work; its orphan Rust timing and failed Mech process are excluded from qualified cohorts. Subsequent full runs restore the previously established policy, SHA-256 `73a693c1a1f107a6546bddf943d62ff4b20ee0611efb4bd823a7ee35b4770aa9`.

The [source-bound diagnosis](steady-fold-remaining-profile-v1/diagnosis.json) prioritizes larger loop transformations: source-certified affine cursor/index coalescing, bounded partial evaluation of invariant widths/masks, direct present/missing probe continuations, and rolling-key dataflow reassociation. These remain unimplemented and have no assigned gain. Rust's short loop and constants are supported by its actual source/disassembly; [LLVM's loop strength reduction and invariant unswitching](https://llvm.org/docs/Passes.html) provide established compiler techniques to investigate. [Checkpoint verification](steady-checkpoint-v1/results.json) recomputes both full cohorts, checks immutable pins and all retained owned-process receipts, and preserves the failures. Separate decoded-source standalone qualification and secured/trusted startup comparison also remain incomplete.

## Rejected experiment: unchanged source inputs in cold snapshots

The [IR66 experiment](invariant-snapshot-diagnosis-v1/results.json) proves that six active-entry words per region are never written by any node in the complete source graph. Their initialized caller storage can remain exact across cold continuations. Code shrinks **984 → 872 bytes** per funded function and stack **96 → 80 bytes**, but six balanced full-input comparisons show a regression:

| Full-input executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.554 | 1.00× |
| Retained IR65 Mech | 0.845 | 1.53× |
| Immutable-snapshot candidate | 0.863 | 1.56× |

The candidate median is **2.04% higher**, with five slower pairs and one faster pair. All observations remain, including the 1.250-second Rust process. The separate prefix medians are Rust **0.0209 seconds**, parent **0.0889 / 4.26×** and candidate **0.0858 / 4.11×**; that small prefix difference does not offset the full-input result. Six focused checks pass; the first attempt's missing test import remains in the raw evidence. The rejected trial did not proceed to the full native suite.

A [single exact-code full-input profile](snapshot-remaining-profile-v1/results.json) retains seven observed workers and complete output. Generated loops account for 87.30% of its 2,441 worker observations; budget waits account for 0.78%. This one diagnostic capture cannot attribute the small regression to a particular instruction or runtime component. A zero-interval profiler setup attempt launched no process; the positive-interval retry is retained separately. Compiler commit `aff3f28bb` restores the exact validated IR65 tree, `c832b33d844696e17c8f501f64d0fb4ee264d1c9`. The smaller candidate is not retained. [Verification](invariant-snapshot-diagnosis-v1/verify.py) recomputes the unfiltered statistics and checks all trial process receipts, output hashes and immutable data pins.

## Strategy comparison with the exact Rust implementation

These diagnostics use Mech source tree `90395fc5a8486a5c040c99a9c023b47de10bc968`, the bounded-backoff implementation below. Commit `0f623b9b8` restored that exact tree after two rejected follow-ups. The following experiments broaden the search across representations, input processing, table algorithms and execution topology. The diagnostics themselves establish **no new Mech speedup** and change no canonical benchmark data; the subsequent compiler experiment is recorded above.

The [protected upstream Rust source](../../../archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs) decodes input bytes once, shares that buffer through `Arc`, constructs seven complete maps with `entry(...).or_insert(...)`, and submits decreasing widths to a Tokio pool. Keys use `u8` for widths 1–4, `u16` for 6, `u32` for 12 and `u64` for 18; counts use `u32`. Its [exact dependency manifest and lock](../../../archive/workloads/knucleotide/rust-deps/Cargo.toml) select hashbrown 0.15.5, foldhash 0.1.5 and tokio-threadpool 0.1.18. The recorded Rust build uses native CPU targeting, optimization level 3 and one codegen unit. Mech already has source-derived rolling keys, folded-product hashing, eight-byte SIMD control probes, cached entries and seven workers. Hashbrown uses quadratic group advances; Mech advances groups linearly. The [upstream table implementation](https://github.com/rust-lang/hashbrown/blob/v0.15.5/src/raw/mod.rs) supplies the comparison algorithm; the exact local dependency source supplies the architecture-specific eight-byte NEON implementation.

[Representation/decoding/thread diagnostics](strategy-comparison-v3/results.json) retain **108 complete process observations**: six per executable for each of two separate inputs. Three predeclared random orders are paired with their reverses. All full-input medians below use this batch's own Rust denominator:

| 125-million-base executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.551 | 1.00× |
| Unchanged-source Rust rebuild | 0.554 | 1.00× |
| Rust with all keys widened to `u64` | 0.554 | 1.01× |
| Rust with counts widened to `u64` | 0.566 | 1.03× |
| Rust with both widened | 0.561 | 1.02× |
| Rust decoding each byte in each worker | 0.554 | 1.01× |
| Rust combining wide keys/counts and per-worker decoding | 0.561 | 1.02× |
| Rust using seven scoped threads | 0.569 | 1.03× |
| Retained secured Mech AOT | 0.902 | 1.64× |

The small differences overlap and are not established gains or precise causal cost estimates. Newly built variants include slower first launches; **no warmup, outlier or process is excluded**. Candidate maxima reach 0.748–1.107 seconds, while the exact Rust range is 0.545–0.562 seconds. The combination that resembles Mech's payload width and decoding placement still does not reproduce Mech's large slowdown. Rust keeps seven complete tables and every window/update in all variants. [Generated source copies and exact diffs](strategy-comparison-v1/sources/) preserve the transformations. The prefix cohort has its own denominator: exact Rust **0.0177 seconds**, unchanged rebuild **0.0191 / 1.08×**, combined wide/decoding variant **0.0193 / 1.09×**, scoped threads **0.0196 / 1.11×**, Mech **0.0867 / 4.89×**. Prefix observations are not pooled with full input.

A second, independent [table-algorithm comparison](table-strategy-v1/results.json) retains **72 complete process observations**. A [diagnostic table written in Rust](diagnostic_packed_table.rs) reproduces Mech's 16-byte key/count payloads, folded constants, eight-byte NEON groups, mirrored controls and 7/8 growth threshold. It retains all windows and complete histograms. One variant uses linear group probing, one uses quadratic advances, and one combines linear probing with seven scoped threads started in ascending-width source order. All use wide keys/counts and decode bytes in each worker.

| Separate 125-million-base cohort | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.554 | 1.00× |
| Hashbrown with wide payloads and per-worker decoding | 0.555 | 1.00× |
| Diagnostic Mech table algorithm compiled by Rust | 0.547 | 0.99× |
| Diagnostic quadratic probing | 0.549 | 0.99× |
| Diagnostic linear probing and source-order scoped threads | 0.543 | 0.98× |
| Retained secured Mech AOT | 0.903 | 1.63× |

These overlapping small differences do not establish that either probe policy is faster. The important finding is that the table algorithm itself does not reproduce the large gap. Diagnostic table ranges include first-launch observations up to 0.733–0.741 seconds; all remain. Its separate prefix medians are Rust **0.0177 seconds**, hashbrown control **0.0191 / 1.08×**, linear table **0.0177 / 1.00×**, quadratic table **0.0177 / 1.00×**, linear/scoped **0.0200 / 1.12×**, and Mech **0.0865 / 4.88×**.

The diagnostic table is **never linked into Mech**. It omits Mech's source-state transport, precise source failures, managed memory and finite work accounting, capability startup and publication. The residual gap cannot be assigned to one of those components by this experiment. [Nine storage checks](table-strategy-v1/checks-linear/stdout.bin), three per compiled variant, verify complete maps against a separate ordered-map oracle, repeated replacements including zero/maximum values, growth, colliding fingerprints, wraparound and payload/group geometry. Every timed process verifies complete output. Every Mech full execution still reports all **874,999,961 physical updates**, seven packed SSA maps, seven peak workers, guarded bounds/calls, five full frozen maps and ten original reads. Short prefix processes may observe fewer overlapping workers while retaining all seven source tasks; one observed six and is retained.

Two initial setup failures collected no timings: a [sandbox-denied hardware query](strategy-comparison-v1/failure.json), then a [missing receipt parent directory after successful compilation](strategy-comparison-v2/failure.json). The representation study subsequently paused after 81 recorded observations because its prefix qualifier unnecessarily demanded all seven workers overlap. The [initial report](strategy-comparison-v3/pre-resume-results.json) and controller remain; the resumed run retains every earlier process, includes the completed six-worker prefix observation and runs only the remaining planned processes. No observation was rerun or discarded. [Checkpoint verification](strategy-diagnosis-v1/results.json) recomputes both cohorts' statistics, parses 254 JSON artifacts, checks **219 terminal owned process receipts**, retains all **180 quantitative observations**, verifies source/input/binary/policy/data pins and confirms the unchanged compiler tree and lock inode. It also verifies the exact initial/resume controllers and all nine storage checks.

These diagnostics motivated the **separate funded counting function with rare source continuations**, now implemented and measured above. Rust's short iterator/entry loop does not carry Mech's multiple state/mode joins through each update. Every original action, physical map update, terminal traversal, finite debit and error origin remains; storage-moving helpers refresh pointers before reentry. Affine cursor representation and state coalescing remain unimplemented related options. Shared decoded input, narrower storage and work-stealing remain possible general features, but these diagnostics do not support prioritizing them as the main route to closing the current full-input gap.

## Bounded escrow backoff and current profile

Current compiler/runtime candidate [`dae3141ba`](https://github.com/mech-lang/mech/commit/dae3141bae18edca1ac67a181df49b9ca5438c82) retains **IR62 / ABI27 / work65** and the previous stage's byte-identical generated Object. The runtime tries the original escrow mutex at most six times, with at most 63 bounded pause hints, before using its original blocking lock. Poison recovery is unchanged. Every debit still reaches the same finite ledgers; the 1,024-traversal refill bound and 32-charge/32,768-work leaf lock-release bounds remain. Source, bytecode, every window/map update, launch allowances and worker count are unchanged.

Three rotated **125-million-base** cohorts retain every complete process, including secured startup/shutdown, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.557 | 1.00× |
| Previous IR62 runtime | 1.009 | 1.81× |
| Current bounded-backoff runtime | 0.891 | 1.60× |

The median is **11.8% lower**, a **1.13× speedup**. Current/previous ranges are **0.890–0.916 / 1.001–1.025 seconds**; current is lower in every paired cohort. Sample standard deviations are **0.015 / 0.012 seconds**. The [full aggregate](full-escrow-spin-cohort-v1/results.json) retains all observations, orders and identities. Every Mech process verifies output, all **874,999,961 updates**, seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers. Subjects run sequentially under the common lock.

The [one-million-base comparison against the previous IR62 runtime](escrow-spin-timing-v1/results.json) excludes one warmup per executable and retains three fresh complete processes per executable:

| One-million-base prefix | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.0131 | 1.00× |
| Previous IR62 runtime | 0.1072 | 8.18× |
| Current bounded-backoff runtime | 0.0845 | 6.45× |

The median is **21.2% lower**. A [separate fresh prefix comparison against the earlier IR60 reference](escrow-spin-reference-timing-v1/results.json), reusing only the pinned current build, gives Rust **0.0199 seconds**, reference **0.1117 seconds / 5.61× Rust**, and current **0.0965 seconds / 4.84× Rust**: **13.7% lower**, with current lower in every pair and nonoverlapping ranges. These batches have separate Rust denominators and are not pooled. Small absolute times vary between batches. The previous caller-constant stage's six-observation prefix regression remains documented below; the new runtime improves on both controls in these fresh matched comparisons. Canonical benchmark data remains unchanged.

Three [fresh full-input profiles](escrow-spin-remaining-profile-v1/results.json) each verify complete output and seven workers. All **4,276,008 machine-code bytes** of the [profiling copy](profile-escrow-spin-build-v1/results.json) match the timed executable, SHA-256 `8183eaec66499ffc41ca587b1e48dbb3f3f3140e7128703b80318fccc88f8dce`. Three fresh Rust captures retain its exact unchanged timed executable. The current partition contains **8,351 worker observations**:

| Observed worker location | Observations | Share |
|---|---:|---:|
| Generated counting loops | 7,426 | 88.9% |
| Active storage helpers | 388 | 4.6% |
| Active work accounting | 263 | 3.1% |
| Waiting for work-budget escrow | 95 | 1.1% |
| Helper bridge and other active frames | 179 | 2.1% |

These are sampled thread observations including waits, rather than wall-time shares or CPU utilization. The [previous runtime captures reclassified with the same taxonomy](loop-constants-remaining-profile-v2/results.json) have **14.1% escrow waits**, versus **1.1%** now. Current blocked observations originate in refill (68) and missing-key charging (27). The five query-histogram workers contribute 5,917 generated-loop observations, and the two frequency-histogram workers contribute 1,509; shared functions do not identify individual query widths. Taxonomy 5 recognizes active spins and blocked fallback through the new lock helper. The parser fixture covers both cases and preserves repeated thread-phase denominators.

[Separate full-input counter executions](escrow-spin-hardware-v1/results.json), nine serial diagnostic processes, give current **64.8 billion instructions / 12.6 billion cycles**, previous **66.0 billion / 14.0 billion**, and Rust **33.1 billion / 7.91 billion**. Instructions decrease **1.8%**, cycles **9.9%**; current instructions remain **1.96× Rust**. System CPU time falls **0.53 → 0.05 seconds**. User CPU increases **3.61 → 3.69 seconds**, while total CPU decreases **4.14 → 3.74 seconds**. These all-thread CPU times are not elapsed times, and counter executions are separate from primary timing cohorts.

The [exact successful generated path](escrow-spin-codegen-audit-v1/steady-path-comparison.json) is unchanged: **66 instructions, eight branches and three stack reads**, versus Rust's **34, four and two**. Every relocated instruction and branch target matches the parent; the complete generated Object has SHA-256 `115cf45d68d0be375c949cf4db5a10b514828bf328581fad9126cc937f9445a3`. Remaining source-state moves, index/width address arithmetic, stack reads and repeated present-entry branches are visible in that path. Collapsed sampled PCs cannot assign individual-instruction costs. Each loop remains 6,024 code bytes / 256 stack bytes, and combined native stack metadata remains 1,152 bytes.

The [full native suite](../native-owner-dispatch-v1/escrow-spin-native-v1/summary.json) passes **359 GPU checks plus one catalog check**, with three existing exclusions. The [worker-budget suite](../native-owner-dispatch-v1/escrow-spin-engine-v1/summary.json) passes **26 checks**, including uncontended acquisition, deterministic exhausted-backoff/blocking fallback, exact ledger reconciliation and poison recovery. All bind clean immutable current source and finish with owned groups reaped. Existing original/decoded changed-input, full-map, growth/refill, arbitrary seed/start, wide-key, finite-cap, overflow/failure and exact/one-short code/stack checks remain.

The [prefix diagnostic comparison](escrow-spin-prefix-comparison-v1/results.json) contains one prearmed exact-code executable-copy capture per subject: **139 current / 128 previous worker observations**, with seven workers each. Cold-copy loader/sampler overhead and low counts limit causal attribution. [Prefix counters](escrow-spin-prefix-hardware-v1/results.json) remain separate from direct-launch observations.

The [source-bound diagnosis](escrow-spin-remaining-profile-v1/diagnosis.json) now prioritizes the generated steady loop. Source-certified affine cursor/index representation, SSA coalescing and separating a pure present-entry trace from rare helper paths are candidates for reducing repeated state/address work and live values. They are **unimplemented and unmeasured**. Every source window, actual map update, finite work debit, original continuation and error frontier must remain. Rust parity, separate decoded-source standalone qualification and secured/trusted comparison remain incomplete.

## Rejected experiment: current-key states at source joins

Experimental compiler [`4b52fcaaa`](https://github.com/mech-lang/mech/commit/4b52fcaaa452a3f31c00b8e435faf97ec217c4e0), **IR63 / ABI27 / work65**, kept present/absent current-key states separate through source joins. Each product node emitted its original action and successor. Selection/header cleared old predicates; insertion refreshed the entry and invalidated earlier membership aliases. Expansion retained the existing 256-base/1,024-versioned-node and 4,096-record limits. Original source, bytecode, every map update and finite policies were unchanged.

The [initial three full-input cohorts](full-lookup-thread-cohort-v1/results.json) had a 2.5% lower median, with overlapping ranges. A second complete balanced cycle followed that uncertainty. The [complete six-cohort aggregate](full-lookup-thread-cohort-v2/results.json), with no excluded warmup or timed observation, gives:

| 125-million-base executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.547 | 1.00× |
| Previous bounded-backoff runtime | 0.897 | 1.64× |
| Current-key state experiment | 0.895 | 1.64× |

The difference is only **0.3%**, with three faster and three slower pairs. Candidate/control ranges **0.866–0.911 / 0.880–0.923 seconds** overlap; sample standard deviations are **0.020 / 0.014 seconds**. This establishes **no useful runtime gain**. All complete processes include secured startup/shutdown, run sequentially under the common lock and verify all **874,999,961 updates**, seven packed SSA maps and workers, guarded bounds/calls, five full frozen maps and ten original reads.

The separate [one-million-base cohort](lookup-thread-timing-v1/results.json), three observations and one excluded warmup per executable, gives Rust **0.0208 seconds**, control **0.0841 seconds / 4.05× Rust**, and candidate **0.0844 seconds / 4.06× Rust**. The overlapping 0.3% difference establishes no prefix gain. Its denominator is separate from the full input.

[Whole-process counters](lookup-thread-hardware-v2/results.json), nine separate diagnostic executions, show only **1.3% fewer instructions**. The [exact successful path](lookup-thread-codegen-audit-v1/steady-path-comparison.json) changes **66 → 65 instructions** and **eight → seven branches**, but stack accesses increase **three → six**: four loads and two stores. Source-index traffic offsets the removed present-entry branch. Each loop has 5,996 code bytes / 256 stack bytes; its base graph grows 90 → 92 nodes, and actual fixed-template work grows 365 → 389 within the unchanged envelope.

Three [fresh candidate profiles](lookup-thread-remaining-profile-v1/results.json) verify complete output and seven workers, with exact profiling/timed machine-code identity. Of **8,162 worker observations**, **87.7%** remain in counting loops, **5.7%** in storage helpers, **3.4%** in active accounting, **1.2%** in escrow waits and **2.1%** in bridge/other frames. Three fresh Rust captures use its unchanged executable. These are thread observations including waits, not wall-time shares; collapsed PCs cannot assign instruction costs.

[Six focused checks](../native-owner-dispatch-v1/lookup-thread-focused-v3/summary.json) pass, including actual source-bound product metadata, original/decoded changed inputs, complete maps, growth/refills, finite caps, arbitrary indices/seeds, original overflows/errors, stale-predicate invalidation and bounded expansion. The rejected candidate did not proceed to the full native suite. Earlier fixture failures remain: [an outdated receipt-call API](../native-owner-dispatch-v1/lookup-thread-focused-v1/summary.json), then [five passes and an incorrect baseline selector expectation](../native-owner-dispatch-v1/lookup-thread-focused-v2/summary.json), corrected before the successful run. An [initial counter attempt](lookup-thread-hardware-v1/failure.json) completed its owned Rust child but the sandbox denied `kern.clockrate`; its terminal receipt remains, and the successful counter retry uses read-only escalated access.

The experiment was [reverted](https://github.com/mech-lang/mech/commit/4269694e9f2bfb9a208a4f9a9152b412c8fad6c7) to the exact previously validated bounded-backoff tree. The [diagnosis](lookup-thread-remaining-profile-v1/diagnosis.json) prioritizes reducing steady-loop state/address traffic through separation from rare helper paths. Generic task launch ordering and source-proved narrower storage remain independent unmeasured candidates. Canonical benchmark data is unchanged.

## Rejected experiment: reverse task launch

Runtime candidate [`6721ccc72`](https://github.com/mech-lang/mech/commit/6721ccc72c3e2e2688e34f2f7d9426353666e435) retained **IR62 / ABI27 / work65** and the original generated Object byte-for-byte. All finite worker loans, captures and constructor claims remained in source order. The bounded independent job batch launched in reverse order, then reversed handle iteration again to preserve source-order results/errors. No task, worker, allocation container, allowance, QoS, affinity or power setting changed.

Three rotated [125-million-base cohorts](full-launch-order-cohort-v1/results.json), including complete secured startup/shutdown with no excluded warmup or outlier, give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.552 | 1.00× |
| Existing source-order launch | 0.899 | 1.63× |
| Reverse-launch experiment | 0.918 | 1.66× |

The candidate is slower in every paired cohort, with a **2.1% higher median** and overlapping ranges. Sample standard deviations are **0.012 / 0.009 seconds** for candidate/control. The **0.666-second Rust observation is retained**. Every Mech process completes all **874,999,961 updates** with seven packed SSA maps and active workers, guarded bounds/calls, five complete frozen maps and ten original reads. Subjects execute sequentially under the common lock.

The separate [one-million-base cohort](launch-order-timing-v1/results.json), three observations and one excluded warmup per executable, gives Rust **0.0224 seconds**, existing Mech **0.0889 seconds / 3.97× Rust**, and candidate **0.1129 seconds / 5.04× Rust**: a **27.0% higher median**. Its denominator is separate from the full cohort. The regression does not justify further runs seeking a favorable subset.

Three [fresh profiles](launch-order-remaining-profile-v1/results.json) verify complete output and seven workers each. The [profiling copy](profile-launch-order-build-v1/results.json) matches the timed executable's entire machine-code section. Of **9,049 worker observations**, **88.4%** are in generated loops, **3.2%** in storage helpers, **3.6%** in active accounting, **3.0%** in accounting waits and **1.8%** in bridge/other frames. Three fresh Rust captures use the unchanged reference. These are thread observations including waits, not wall-time shares. The [successful generated path](launch-order-codegen-audit-v1/steady-path-comparison.json) remains **66 instructions, eight branches and three stack reads**; all relocated instructions/branch targets and the complete generated Object match the reference.

[Eleven existing parallel checks](../native-owner-dispatch-v1/launch-order-focused-v1/summary.json) pass, covering actual original/decoded source and checked images, all source maps/updates, captures, source-order values/errors, earlier parent push versus later worker arithmetic failure, finite admission/fallback, child authority and cleanup. The rejected variant did not proceed to the full native suite.

The change was [reverted](https://github.com/mech-lang/mech/commit/0f623b9b860cac388ba270bb43ae97a5adf3b12a) to the exact previously validated bounded-backoff tree, `90395fc5a8486a5c040c99a9c023b47de10bc968`. The [diagnosis](launch-order-remaining-profile-v1/diagnosis.json) rejects plain reverse launch; broader cost-guided scheduling remains unimplemented and unmeasured. The main remaining target is generated-loop state/address traffic. Source-certified direct storage for small packed key spaces and narrower key/count storage are additional unimplemented representation candidates. No gain is assigned to them, and every actual map update, membership/value semantic, finite resource check and fallback must remain. Rust parity is incomplete; canonical benchmark data is unchanged.

## Previous stage: caller-owned loop constants and a prefix regression

Compiler candidate [`f1b49a5da`](https://github.com/mech-lang/mech/commit/f1b49a5da39b1a11ed5c6a0755ce054ad02a6dfd), **IR62 / ABI27 / work65**, initializes the existing folded-hash constants and the source-certified loop endpoint in **24 caller-owned stack bytes** before invoking each outlined counting function. Hash literals are unchanged; the endpoint is computed at runtime from the actual source width/limit words. The local native function receives a seventh pointer argument, while the original Rust helper ABI and 19-word packed frame remain. Helpers never receive the packet pointer, and no write aliases it during the callee's lifetime, satisfying the backend's readonly-load contract. Inline or disabled outlining retains the prior arithmetic. Source, bytecode, all window/map operations and finite launch policies are unchanged.

Three rotated **125-million-base** cohorts retain every complete process, including secured startup/shutdown, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.557 | 1.00× |
| IR60 reference Mech | 1.092 | 1.96× |
| IR62 caller-constant candidate | 1.021 | 1.83× |

The candidate median is **6.5% lower**, a **1.07× speedup**. Candidate/reference ranges are **1.003–1.029 / 1.092–1.101 seconds**, with candidate lower in every paired cohort. Sample standard deviations are **0.014 / 0.005 seconds**. The [full aggregate](full-loop-constants-cohort-v1/results.json) retains all observations, orders and identities. Every Mech process verifies output, all **874,999,961 updates**, seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers. Subjects execute sequentially under the common lock.

The separate one-million-base protocol **regresses**. Both the [initial batch](loop-constants-timing-v1/results.json) and [repeat using only the pinned existing build](loop-constants-timing-v2/results.json) retain three fresh observations per executable and one excluded warmup per executable. The [six-observation aggregate](loop-constants-prefix-cohort-v1/results.json) excludes no timed observation:

| One-million-base prefix | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.0193 | 1.00× |
| IR60 reference Mech | 0.0896 | 4.65× |
| IR62 caller-constant candidate | 0.1133 | 5.88× |

The candidate median is **26.4% higher**. At this stage, the draft candidate had an **unresolved prefix regression**; the subsequent bounded-backoff stage above improves fresh matched prefix comparisons. The historical observations remain intact, and the canonical benchmark dataset is unchanged. Full and prefix inputs and denominators remain separate.

[Full-input counters](loop-constants-hardware-v1/results.json), nine separate serial diagnostic executions, give candidate **66.1 billion instructions / 13.9 billion cycles**, reference **76.4 billion / 15.1 billion**, and Rust **33.1 billion / 8.35 billion**. Instructions decrease **13.6%**, cycles **7.9%**; candidate instructions remain **1.99× Rust**. The [specified successful first-lane path](loop-constants-codegen-audit-v1/steady-path-comparison.json) falls **78 → 66 instructions** and **nine → three stack accesses**, retaining eight branches. Hash-constant reconstruction and `n-width+1` rematerialization leave that path; the source index stays in a register. Rust's comparable path has 34 instructions, four branches and two stack accesses. Static paths do not represent every dynamic iteration or assign individual-instruction costs.

Each loop has **6,024 code bytes / 256 stack bytes**, versus reference **6,176 / 240**. Actual root caller templates use **28 instructions** within the unchanged 64-instruction lane. Combined native stack metadata increases **1,088 → 1,152 bytes**, including caller packet storage and actual callee/bridge requirements. No production allowance or work price is raised. The [full native suite](../native-owner-dispatch-v1/loop-constants-native-v1/summary.json) passes **359 GPU checks plus one catalog check**, with three existing exclusions. Its [five focused checks](../native-owner-dispatch-v1/loop-constants-focused-v1/summary.json) are included, covering actual packet/load metadata, original/decoded changed inputs, complete maps, wide keys, arbitrary starts/seeds, terminal/full-refill headers, finite caps and original failures. Exact and one-short native stack/code limits also pass.

[Three full-input profiles](loop-constants-remaining-profile-v1/results.json) verify seven workers and complete output each. The [profiling copy](profile-loop-constants-build-v1/results.json) matches all **4,273,704 machine-code bytes** of the timed executable, SHA-256 `b66881135523d8baaaff0f2fc48d4a870cb37ba5d0d8f43d08f69af7f4144696`. [Three Rust captures](rust-full-profile-v13/analysis.json) retain its exact timed executable. Of **10,321** Mech worker observations, **77.9%** are in generated loops, **14.1%** waiting for work-budget escrow, **4.1%** active in accounting and **2.3%** in storage helpers. These include waits and differing windows; they are not wall-time shares or CPU utilization. [Reference captures reclassified with the same taxonomy](vector-control-remaining-profile-v3/results.json) retain the earlier distribution.

The short-input investigation remains limited. A normal attachment missed the completed subject; pre-arming `sample -wait` for an exact executable copy captured workers. Startup/queue sections repeat a thread ID, so the updated parser and classifier taxonomy 4 merge disjoint root phases, normalize the colon suffix and preserve observation totals; a regression fixture verifies this. An initial controller PID-field error and empty/partial later captures remain retained. The [prefix comparison](loop-constants-prefix-comparison-v1/results.json) explicitly selects the first seven-worker capture per subject, **125 / 148 observations**, and records that explicit selection alongside all attempted captures. Cold-copy loader/sampler overhead limits causal conclusions. These worker captures concentrate in storage/accounting. [Separate prefix counters](loop-constants-prefix-hardware-v1/results.json) have fewer instructions/cycles and faster wrapped elapsed time, while both primary direct-launch batches regress; diagnostic elapsed times do not replace primary measurements.

The [source-bound diagnosis at this stage](loop-constants-remaining-profile-v1/diagnosis.json) prioritized resolving this discrepancy and the prefix cost, then reducing the remaining source-state/index-address overhead and shared accounting. The later bounded-backoff stage above measures a runtime improvement; source-certified affine cursor/index representation, SSA copy coalescing and cost-guided launch ordering remain unimplemented candidates with no assigned gains. Rust parity, separate decoded-source standalone qualification and secured/trusted comparison remain incomplete.

## Direct SIMD control loads and remaining loop costs (IR60 reference)

Compiler [`83012637f`](https://github.com/mech-lang/mech/commit/83012637fb0f5fab98460385fbde822a263fa3c4), **IR60 / ABI27 / work65**, reads an admitted eight-byte AArch64 control group directly into a vector register. The original path loaded an integer and transferred it to SIMD before comparing fingerprints. The current code emits `ldr d1; cmeq` and converts the raw controls to an integer only on the empty-mask path. The memory extent, byte masks, lane order, storage semantics and original work debits remain unchanged. x86 retains its existing bounded eight-byte load. This follows the optional source-count proof described below.

Six rotated **125-million-base** cohorts retain every complete process, including secured startup/shutdown, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.552 | 1.00× |
| Previous best Mech, single-transaction refill / IR58 | 1.126 | 2.04× |
| Current Mech, count proof + vector load / IR60 | 1.082 | 1.96× |

The median is **3.9% lower**, a **1.04× speedup**. Current/control ranges are **1.078–1.091 / 1.110–1.146 seconds**, and the current executable is lower in every paired cohort. Their sample standard deviations are **0.005 / 0.014 seconds**. The unusually slow **0.760-second Rust observation is retained**. A second complete balanced cycle followed the initial Rust dispersion; both the [initial three-cohort aggregate](full-vector-control-best-cohort-v1/results.json) and [complete six-cohort aggregate](full-vector-control-best-cohort-v2/results.json) remain. Every process verifies complete output, all **874,999,961 updates**, seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers. Subjects execute sequentially under the common lock. Source, bytecode, input and finite launch policies match the prior stages.

An [isolated three-cohort vector-load comparison](full-vector-control-cohort-v1/results.json) against IR59 gives Rust **0.544 seconds**, control **1.131 seconds / 2.08× Rust**, and current **1.081 seconds / 1.99× Rust**: **4.5% lower**. This has its own matched Rust denominator. The separate [one-million-base prefix protocol](vector-control-timing-v2/results.json), with one excluded warmup per executable and three observations, gives Rust **0.0194 seconds**, control **0.1150 seconds / 5.93× Rust**, and current **0.0889 seconds / 4.58× Rust**. Prefix and full-input observations are not combined.

The [full native suite](../native-owner-dispatch-v1/vector-control-native-v1/summary.json) passes **354 GPU checks plus one catalog check**, with three existing exclusions. A [new direct emitted-code check](../native-owner-dispatch-v1/vector-control-focused-v1/summary.json) exercises all 128 fingerprint tags, all 256 matching-lane masks, offsets 0–7 and empty controls against independent expected words, while asserting exactly one eight-byte IR load. [Count-proof checks](../native-owner-dispatch-v1/vector-control-counts-v1/summary.json) include nonempty storage already containing `u64::MAX`, which must decline guarded packing and retain its original overflow. These focused checks are included in the full suite. All validation processes bind clean source snapshots and finish with owned groups reaped.

[Whole-process counters](vector-control-hardware-v1/results.json), nine separate serial diagnostic executions, give current **76.4 billion instructions / 15.1 billion cycles**, IR59 control **76.4 billion / 15.7 billion**, and Rust **33.1 billion / 8.33 billion**. Vector-load instructions are essentially unchanged, while cycles decrease **3.6%**. Current instructions remain **2.31× Rust**. These are diagnostic executions, rather than additional timing-cohort samples. The improvement is consistent with removing a dependency between register classes; individual-instruction latency is not measured.

Three [initial](vector-control-remaining-profile-v1/results.json) and three [fresh repeated](vector-control-remaining-profile-v2/results.json) Mech captures verify complete output and seven workers each. The [profiling copy](profile-vector-control-build-v1/results.json) matches the timed executable's entire **4,273,836-byte** machine-code section, SHA-256 `659bab0be202140b246aeefe0bc1ad2ba1cffb2be5f9e878762e61349c57cf67`. The [three fresh Rust captures](rust-full-profile-v11/analysis.json) retain its exact timed executable and observe seven counting workers each. No compiler or benchmark source changed between the initial and repeated current profiles.

| Fresh Mech worker observations | Count | Share |
|---|---:|---:|
| Generated counting loops | 8,935 | 79.4% |
| Waiting for work-budget escrow | 1,408 | 12.5% |
| Active budget/refill operations | 442 | 3.9% |
| Active storage helpers | 274 | 2.4% |
| Generated helper bridge | 76 | 0.7% |
| Other active frames | 120 | 1.1% |

The denominator is **11,255 worker observations**. These include waits and are not elapsed-time fractions or CPU utilization. The earlier same-code capture places **79.9%** in generated loops and **12.3%** in escrow waits. In the repeated capture, **1,111** blocked observations originate in refill and **282** in distinct-key charging. The five query-histogram workers contribute **6,843 loop observations / 60.8%** of all worker observations; the two frequency-histogram workers contribute **2,092 / 18.6%**. The main thread is in joins for **89.6%** of its observations. Shared generated functions do not identify individual query widths.

The [source-bound diagnosis](vector-control-remaining-profile-v2/diagnosis.json) prioritizes generated-loop state traffic and invariant handling, followed by shared accounting. The [specified successful first-lane iteration](vector-control-codegen-audit-v1/steady-path-comparison.json) still has **78 instructions, eight branches and nine stack accesses**, versus Rust's **34, four and two**. IR59 has 78/eight/eight: the direct vector load removes one transfer, but changed allocation adds state traffic. Eight instructions still reconstruct two hash constants on each specified iteration; endpoint calculations and private cache/source-state traffic recur. Current loops retain **6,176 code bytes / 240 stack bytes**. [Fresh sampled-PC groups](vector-control-codegen-audit-v4/hot-offset-groups.json) repeatedly list fingerprint preparation and full-key slot loads, but collapse other addresses and cannot assign a unique cost to either instruction.

A subsequent private-cache canonicalization experiment is measured and rejected below. The next target is binding immutable hash constants and the guarded source endpoint in the owned caller before entering the loop, rather than relying on backend placement to retain them. Caller-owned invariant bindings remain **unimplemented and unmeasured**. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Rejected experiment: clearing the cache at every header

Experimental compiler [`8e1710880`](https://github.com/mech-lang/mech/commit/8e171088092df6f5a8841c328985b834c8510ca0), IR61/ABI27/work65, cleared both private entry-pointer/cache-known fields at every emitted header when lookup analysis proved its header invalidation. The intended effect was reducing carried SSA state. [Five focused checks](../native-owner-dispatch-v1/header-cache-focused-v1/summary.json) passed, including actual source-bound emission metadata and original/decoded runtime equivalence across changed inputs, complete maps, narrow/wide keys, arbitrary starts/seeds, refills, terminal headers, finite caps and exact arithmetic/failure frontiers. The experiment was not promoted and did not run the full native suite.

Three rotated complete-process **125-million-base** cohorts retain all observations and include secured startup/shutdown:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Exact upstream Rust #7 | 0.571 | 1.00× |
| Retained best Mech, IR60 | 1.083 | 1.90× |
| Header-cache experiment, IR61 | 1.085 | 1.90× |

The experimental median is **0.12% higher**. Overlapping ranges and mixed paired observations establish **no runtime gain**. The **1.357-second Rust observation remains included**; these ratios use this cohort's own median. The [full aggregate](full-header-cache-cohort-v1/results.json) retains every observation and execution order. All candidate executions verify output, all 874,999,961 updates, seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers. Subjects execute sequentially under the original shared lock, with unchanged source, bytecode, inputs and finite policies.

The separate [one-million-base prefix](header-cache-timing-v1/results.json), with one excluded warmup per executable and three observations, gives Rust **0.0193 seconds**, prior best **0.0892 seconds / 4.61× Rust**, and experiment **0.1103 seconds / 5.70× Rust**. Its median is **23.7% higher**. These prefix observations do not enter the full-input cohort.

[Nine serial diagnostic executions](header-cache-hardware-v1/results.json) give experimental **75.6 billion instructions / 14.9 billion cycles**, prior best **76.4 billion / 15.3 billion**, and Rust **33.2 billion / 8.06 billion**. Retired instructions decrease **1.1%** and cycles **2.7%**, while full-process elapsed improvement remains unestablished. These are separate counter runs rather than additional timing-cohort observations.

[Three exact-code profiles](header-cache-remaining-profile-v1/results.json) verify complete output and seven workers each; [three Rust captures](rust-full-profile-v12/analysis.json) use its unchanged timed binary. Of **11,003** Mech worker observations, **78.7%** are in generated loops, **12.8%** waiting for work-budget escrow, **4.3%** active in accounting and **2.5%** in storage helpers. The observations include waits and are not elapsed-time fractions. The [static successful path](header-cache-codegen-audit-v1/steady-path-comparison.json) falls from **78 to 77 instructions** while retaining **eight branches and nine stack accesses**. It removes only one carried-state move; all eight hash-constant construction instructions, endpoint rematerialization and stack traffic remain. Each loop grows from **6,176 to 6,308 code bytes**, with the same **240-byte stack**.

The [rejection diagnosis](header-cache-remaining-profile-v1/diagnosis.json) binds these distinct findings. Revert [`0e8d2d933`](https://github.com/mech-lang/mech/commit/0e8d2d933) restores the **exact source tree** of prior best `83012637f`, retaining the experiment and its measurements in history. The canonical dataset is unchanged. The next candidate will bind invariant values outside the counting function and verify actual machine-code placement, native stack/work admission and measured runtime before promotion.

## Optional source-count bounds: fewer instructions without a full runtime gain

Compiler [`15910224f`](https://github.com/mech-lang/mech/commit/15910224f) adds an optional bounded inductive proof, qualified at [`5c38b96ad`](https://github.com/mech-lang/mech/commit/5c38b96ad80b14e355f1096697bf8202683032b0), **IR59 / ABI27 / work65**. Empty owned storage, aligned source index/update tally, guarded source reads and exactly one insertion per productive recurrence constrain stored counts. Every inserted replacement must preserve the bound; only actual source additions of literal one that feed those insertions may omit overflow checks in guarded modes. Arbitrary replacements, nonempty seeds and unsupported control flow retain checked arithmetic. All original windows, lookups, count arithmetic, physical map updates and debits remain.

[Three full-input cohorts](full-count-values-cohort-v1/results.json) give Rust **0.548 seconds**, parent **1.1192 seconds / 2.04× Rust**, and candidate **1.1191 seconds / 2.04× Rust**. The approximately **0.01%** median difference, overlapping ranges and mixed paired results establish **no elapsed-time gain**. [Separate counters](count-values-hardware-v1/results.json) show **79.9 → 76.5 billion instructions**, about **4.3% fewer**, with cycles essentially flat at **15.6 → 15.7 billion**. The static successful path falls from 82 to 78 instructions and nine to eight branches. These reductions are compiler effects, not an established full-input speedup.

[Six focused checks](../native-owner-dispatch-v1/count-values-focused-v2/summary.json) pass; the later full 355-check suite ran at IR60 rather than this IR59 head. Metadata names actual source read/add nodes and emitted omitted checks; qualification separately verifies source ownership, unit operands and guarded entry receipts. It does not claim an independent reimplementation of the complete compiler proof or dynamic substitution frequencies. The [count-stage diagnosis](count-values-remaining-profile-v1/diagnosis.json) retains the distinct evidence and limitation.

Two unsuccessful attempts remain visible. The [first focused run](../native-owner-dispatch-v1/count-values-focused-v1/summary.json) passed five checks and failed a selector expectation because disabling only the count proof leaves other bounds enabled; the corrected expectation preserves those independent optimizations. The [first vector qualification](vector-control-timing-v1/qualification-failure.json) completed its build but rejected IR60 because one driver version allowlist omitted it, before collecting any timing samples. The corrected driver reused only that completed exact build for [qualified timing](vector-control-timing-v2/results.json). Neither failed attempt supplies timing observations.

## One transaction per finite fuel refill

Runtime [`779581405`](https://github.com/mech-lang/mech/commit/779581405c58839612f454f2210bed9aa0013a36) combines the remaining-work decision and its existing debit under one worker-escrow lock. The generic `NativeLibraryWorkBudget::with_unscoped_debit` callback performs bounded scalar preparation; both local and shared compute/comparison limits are checked before either ledger commits. Active scopes, sealed groups, denied debits and preparation errors cannot spend fuel. Unwinding releases the lock without refunding earlier successful work.

`PackedMap::refill` retains its original quarter-headroom policy and maximum **1,024 traversals**. Pricing remains pure arithmetic outside the shared lock; any pricing error is retained until the original remaining-allowance check succeeds. The frame/funded fields change only after the transaction succeeds. There is no new allowance, larger chunk, skipped debit or resource-policy increase.

Three rotated **125-million-base** cohorts retain every complete process, including secured startup/shutdown, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.553 | 1.00× |
| Previous two-lock refill Mech | 1.149 | 2.08× |
| Single-transaction refill Mech | 1.122 | 2.03× |

The median decreases **2.4%**, a **1.02× speedup**. Candidate/control ranges are **1.114–1.126 / 1.133–1.166 seconds**. The candidate is lower in every paired cohort; its sample standard deviation is **0.006 seconds**, versus the control's **0.017**. The [aggregate](full-escrow-transaction-cohort-v1/results.json) retains all observations, orders, identities and checks. Every candidate process verifies complete output, all **874,999,961 updates**, seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers. Subjects execute serially under the common lock. Source, bytecode, input and finite launch policies match the parent.

The [one-million-base prefix](escrow-transaction-timing-v1/results.json), a separate protocol with one excluded warmup per executable and three timed observations, gives Rust **0.0208 seconds**, parent **0.0951 seconds / 4.57× Rust**, and candidate **0.0907 seconds / 4.36× Rust**. The candidate median is **4.6% lower**; its range is 0.0891–0.0922 seconds versus the control's 0.0935–0.0968.

Validation passes [24 worker-budget checks](../native-owner-dispatch-v1/escrow-transaction-engine-v1/summary.json), [37 focused packed-map checks](../native-owner-dispatch-v1/escrow-transaction-packed-v1/summary.json), and the [full native suite](../native-owner-dispatch-v1/escrow-transaction-native-v1/summary.json): **348 GPU tests plus one catalog test**, with three existing exclusions. The 37 checks are a subset of the full suite. Six new engine tests compare exact debits with the separate-query reference across tight/maximum limits and parent reservations; reject own/foreign call scopes; retain root restrictions and tighter worker-local limits; commit concurrent two-dimensional charges once; preserve failures and sealed groups; and recover after an owned preparation unwind. All validation runs bind clean source snapshots before/after execution and terminate with their process groups reaped.

IR58/ABI27/work65 remain: the generated native Object is **byte-for-byte identical** to the parent, SHA-256 `c92728c16aecb53532cf814e53e816eb203b08f2711fb8aa97810f8e90a856db`. Generated instructions, private frame/helper effects and work prices are unchanged; the improvement is in the host runtime. Each loop retains **6,280 code bytes / 240 stack bytes**. The [current disassembly/path check](escrow-transaction-codegen-audit-v1/steady-path-comparison.json) verifies every instruction at its relocated address: the specified funded, productive, first-hit existing-key path still has **82 instructions, nine branches and eight stack accesses**, versus Rust's **34, four and two**.

Three fresh exact-code profiles ([first](full-profile-escrow-transaction-v1/analysis.json), [second](full-profile-escrow-transaction-v2/analysis.json), [third](full-profile-escrow-transaction-v3/analysis.json)) each observe seven workers and verify complete output. The [profiling copy](profile-escrow-transaction-build-v1/results.json) matches all **4,274,092 machine-code bytes** of the timed executable, SHA-256 `933e59145d7151c78e23e3d22df10621867e5e730b0203334226cac779cc9e6c`. [Three fresh Rust captures](rust-full-profile-v8/analysis.json) retain its exact unchanged binary and seven observed counting workers each.

The [candidate partition](escrow-transaction-remaining-profile-v2/results.json) and [retained parent captures reanalyzed](mutation-remaining-profile-v4/results.json) use the same classifier:

| Worker observations | Parent | Candidate |
|---|---:|---:|
| Generated counting loops | 78.8% | 82.1% |
| Waiting for work-budget escrow | 13.0% | 10.7% |
| Active budget/refill operations | 4.1% | 3.5% |
| Active storage helpers | 2.4% | 2.2% |
| Generated helper bridge | 0.9% | 0.6% |
| Other active frames | 0.8% | 1.0% |

The denominators are **12,154 / 11,633 worker observations**. These distributions include waiting threads and different capture windows; they are not elapsed-time fractions or per-instruction costs. The transaction is inlined into `PackedMap::refill`, whose only mutex is the worker escrow. Classifier version 3 includes this helper's validation/pricing on both sides so inlining cannot hide its waits or active work. This moves 47 parent observations previously assigned to storage into refill/accounting. The [unrefined candidate analysis](escrow-transaction-remaining-profile-v1/results.json) remains retained; it classified 961 inlined refill waits as `other_wait`. In the refined candidate, **961** blocked observations originate in refill, **269** in distinct-key debits and **ten** in other accounting.

[Nine separate serial whole-process counter executions](escrow-transaction-hardware-v1/results.json) give candidate **79.9 billion instructions / 15.7 billion cycles**, parent **80.3 billion / 16.2 billion**, and Rust **33.1 billion / 7.90 billion**. Instructions decrease **0.4%**, cycles **3.3%**. Median system CPU time decreases **0.57 → 0.47 seconds** and involuntary context switches **91,591 → 80,008**. These are separate diagnostic executions, not timing-cohort observations. Candidate instruction count remains **2.41× Rust**, consistent with the unchanged generated-loop gap.

The [source-bound diagnosis](escrow-transaction-remaining-profile-v2/diagnosis.json) prioritizes the remaining generated-loop work and escrow contention. Empty storage and one insertion per recurrence do not constrain arbitrary stored replacement values: removing count-overflow checks requires a separate source-value proof. Count bounds and cost-guided launch ordering remain unimplemented candidates, with no assigned gains. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Certified insertion progress and nonempty storage

Compiler [`5474f214a`](https://github.com/mech-lang/mech/commit/5474f214a78f711880ce266637ef35d2f3a6e5bc), IR58/ABI27/work65, uses a bounded source-CFG proof of exactly one insertion before each index+1 recurrence. Productive prefixes may not insert twice; stop paths remain total; certified insertion nodes are dominated by the original source guards; other state variants may not enter the active recurrence. For an active initial state, a runtime guard checks equality between the source index and private update tally. Unaligned entries retain the checked native path.

Under that certificate, active guarded headers reuse the exact source index for the internal tally. A productive index is below the proved endpoint, so its corresponding insertion tally cannot overflow. Only a certified completed insertion establishes nonempty storage for the next steady iteration. Every actual key lookup, count computation, map write and original fuel debit remains. Steady adjacency also now uses certified product-graph nodes rather than source sites that different state variants can share. Source, bytecode, inputs, capabilities and finite policies are unchanged.

Three rotated **125-million-base** cohorts retain every complete process, with secured startup/shutdown and no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.552 | 1.00× |
| Previous invocation-binding Mech, IR57 | 1.243 | 2.25× |
| Certified-progress Mech, IR58 | 1.149 | 2.08× |

The median is **7.6% lower**, a **1.08× speedup**. Candidate observations span **1.142–1.150 seconds**, below the control's **1.243–1.270 seconds**. The [aggregate](full-mutation-facts-cohort-v1/results.json) retains every observation, standard deviation, order and identity. Complete output and the aggregate **874,999,961 updates** pass; all seven packed SSA maps, seven guarded bounds/call entries, five complete frozen maps, ten original reads and seven peak workers are verified. Subjects execute serially under the common lock. The original one-million-base and full inputs remain separate protocols.

The [one-million-base prefix](mutation-facts-timing-v1/results.json), with one excluded warmup per executable and three timed observations, gives Rust **0.0194 seconds**, parent **0.0921 seconds / 4.75× Rust**, and candidate **0.0920 seconds / 4.75× Rust**. Its approximately 0.1% median change and overlapping ranges establish no prefix gain.

[Five focused checks](../native-owner-dispatch-v1/mutation-facts-focused-v3/summary.json) and the [full native suite](../native-owner-dispatch-v1/mutation-facts-native-v1/summary.json), **348 GPU tests plus one catalog test**, pass; three existing exclusions remain. Original/decoded programs cover runtime inputs, arbitrary seeds and starting indices, narrow/wide keys, growth, complete refills, finite caps and original arithmetic/error frontiers. Three negative source variants exercise skipped insertions, double insertions and entry from another state: their complete maps match independent expected keys/counts and their actual insertion tallies are **3, 10 and 4**, rather than being inferred from window count. All decline the new proof. Exact source work and remaining fuel are compared before independently hash-seeded publication. Existing exact/one-short stack/code checks run in the full suite.

Two unsuccessful fixture attempts remain: [first](../native-owner-dispatch-v1/mutation-facts-focused-v1/summary.json), four checks passed and one negative fixture stopped at malformed match syntax; [second](../native-owner-dispatch-v1/mutation-facts-focused-v2/summary.json), the skipped-insertion case produced the correct map/tally but a post-publication total-work assertion included independently seeded sorting. The corrected fixture checks the exact pre-publication work/fuel frontier, structural receipts and every final key/count.

[Build qualification](mutation-facts-timing-v1/results.json) binds both actual mutation regions to their original source headers, U64 index words and insertion sites. Each records three guarded counter headers, three omitted private counter-overflow checks and one steady nonempty probe. All seven runtime guarded entries must be selected before a timing can succeed. These are static emission records plus runtime entry receipts, not dynamic per-substitution frequencies. Counting functions shrink from **6,740 code bytes / 256 stack bytes** to **6,280 / 240**. Each emits 36 preserving-call templates rather than 39; the existing largest source template is **472**, within the unchanged 512-unit lane. The entry guard fits the unchanged fixed traversal envelope. No production allowance is raised.

[Nine separate whole-process counter executions](mutation-facts-hardware-v1/results.json) give candidate **80.2 billion instructions / 16.3 billion cycles**, parent **88.1 billion / 17.9 billion**, and Rust **33.1 billion / 7.88 billion**. Candidate instructions decrease **8.9%**, cycles decrease **9.1%**, and candidate instructions remain **2.42× Rust**. These diagnostic executions include all target threads and startup/shutdown and are not additional timing-cohort samples.

Three initial profiles ([first](full-profile-mutation-facts-v1/analysis.json), [second](full-profile-mutation-facts-v2/analysis.json), [third](full-profile-mutation-facts-v3/analysis.json)) and three repeated captures ([fourth](full-profile-mutation-facts-v4/analysis.json), [fifth](full-profile-mutation-facts-v5/analysis.json), [sixth](full-profile-mutation-facts-v6/analysis.json)) each observe seven workers and verify complete output. The [profiling copy](profile-mutation-facts-build-v1/results.json) matches the timed executable's entire **4,269,072-byte** code section, SHA-256 `5400e0eb58b07d28910f46e68fff2f455aa4d67549e1fa4e94a2b8e8e241d0eb`. [Three repeated Rust captures](rust-full-profile-v7/analysis.json) also use the exact unchanged executable and observe seven counting workers each. Every subject is complete and reaped before the next execution.

The [repeated exclusive partition](mutation-remaining-profile-v3/results.json) combines **12,154 Mech worker observations**:

| Observed worker location | Observations | Share |
|---|---:|---:|
| Generated counting loops | 9,581 | 78.8% |
| Waiting for the shared work-budget mutex | 1,578 | 13.0% |
| Active work-budget operations | 452 | 3.7% |
| Active storage helpers | 336 | 2.8% |
| Generated helper bridge | 104 | 0.9% |
| Other active frames | 103 | 0.8% |

These are sampled thread observations, including waits, rather than elapsed-time shares or instruction costs. The main thread is in worker joins for **90.8%** of its combined observations. The five query-histogram workers contribute **7,320 generated-loop observations / 60.2%** of all worker observations, and the two frequency-histogram workers contribute **2,261 / 18.6%**. Samples from a shared generated function do not identify an individual query width.

The refined taxonomy recognizes remaining-work queries as work-budget operations. The [initial partition](mutation-remaining-profile-v1/results.json) and [unrefined repeated partition](mutation-remaining-profile-v2/results.json) counted their mutex waits as `other_wait` and their active query frames as storage helpers. The raw stacks are retained. In the corrected repeated partition, **1,029** waits originate in `PackedMap::refill → unscoped_remaining → NativeWorkerWorkLoan::remaining`, **331** in a missing-key debit, **217** in a refill debit, and **one** in frozen-map accounting. All use the same worker-group escrow mutex. Budget operations total **16.7%** of observations, with **13.0%** blocked; this is a classification correction, not a compiler or runtime change.

The [source-bound diagnosis](mutation-remaining-profile-v3/diagnosis.json) retains the relevant code hashes and static evidence. A current refill independently locks the shared escrow to query remaining work and then locks it again to commit its already bounded charge. The existing batch is at most **1,024 traversals**. Combining these operations under one checked transaction is a concrete contention candidate; changing the finite allowance or omitting debits is not required. Its performance effect remains unmeasured. Larger generated-loop work remains the primary target: stack state traffic, repeated hash-constant materialization, dynamic width/end calculations and presence/error branches still exceed the Rust path.

[Exact disassembly and sampled-PC groups](mutation-facts-codegen-audit-v1/results.json), [second](mutation-facts-codegen-audit-v2/results.json), [third](mutation-facts-codegen-audit-v3/results.json), retain the remaining probe/count path. The [specified first-hit successful iteration](mutation-facts-codegen-audit-v1/steady-path-comparison.json) drops from **91 to 82 instructions** and **ten to nine branches**. Rolling-key construction appears once rather than twice. Stack accesses rise from **seven to eight**, despite the smaller frame; the new path reloads/stores source-index state. Rust retains **34 instructions, four branches and two stack accesses**. Static paths and collapsed groups do not assign individual-instruction runtime costs.

A [separate task-order observation](mutation-facts-codegen-audit-v1/task-order-evidence.json) records an Apple M3 with four performance and four efficiency cores. The unmodified Rust source launches widths **18, 12, 6, 4, 3, 2, 1**; Mech's current scheduler traverses source regions/indices in **1, 2, 3, 4, 6, 12, 18** order. CPU placement and the performance effect of this difference are unmeasured. A future cost-guided scheduling candidate must retain source-order admission, result/error replay and the existing worker/resource bounds. Remaining loop costs include source checks, hash-constant materialization and source-state spills. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Invocation-constant helper bindings

Compiler [`ba2db6d9b`](https://github.com/mech-lang/mech/commit/ba2db6d9b4f94a9a149edac21c0a3bb18758de18), IR57/ABI27/work65, initializes the private helper function, context and result-pointer words once in each caller-owned scratch area. Source sites, operations and operands remain per call. Only the exact original SSA function/context pair can reuse those words; a distinct pair calls its supplied helper through the ordinary C ABI. The bridge writes only its separate status word. Original source, bytecode, input and finite policies remain unchanged.

Six rotated **125-million-base** cohorts retain every complete process, including secured startup/shutdown, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.551 | 1.00× |
| Previous scratch-call Mech, IR56 | 1.256 | 2.28× |
| Invocation-binding Mech, IR57 | 1.239 | 2.25× |

The median is **1.4% lower**, and the candidate is faster in each paired cohort. Candidate/control ranges overlap: **1.212–1.260 / 1.250–1.269 seconds**. The first three cohorts had only a 0.5% median reduction and overlapping ranges; a second balanced cycle followed the instruction-counter evidence and unresolved timing difference. Both the [initial aggregate](full-binding-calls-cohort-v1/results.json) and [complete six-cohort aggregate](full-binding-calls-cohort-v2/results.json) remain. This is a small runtime change, not Rust parity. Every candidate execution verifies output, all **874,999,961 updates**, seven packed SSA maps, seven bounds/call-guard entries, five complete frozen maps, ten original reads and seven peak workers. All subjects execute serially under the common lock.

The [one-million-base prefix](binding-calls-timing-v1/results.json), with one excluded warmup per executable and three timed observations, gives Rust **0.0207 seconds**, parent **0.0903 seconds / 4.36× Rust**, and candidate **0.0893 seconds / 4.31× Rust**. The 1.1% median reduction has overlapping ranges. Its Rust denominator remains separate from the full cohort.

[Six focused checks](../native-owner-dispatch-v1/binding-calls-focused-v1/summary.json) and the [full native suite](../native-owner-dispatch-v1/binding-calls-native-v1/summary.json), **343 GPU tests plus one catalog test**, pass; three existing exclusions remain. A new direct execution test repeatedly changes source arguments, changes the helper and context independently, verifies each actual context's visit count, and exercises errors including a nonzero upper status word. Existing checks retain live scalar/vector values, arbitrary seeds and inputs, growth/refills, exact work, original failures, declined proofs and exact/one-short resource limits. The stale-identity fixture also rejects IR56 and restores its distinct historical work-version cases.

Each counting function shrinks from **7,252 to 6,740 code bytes**; stack remains **256 bytes**, including the 72-byte scratch. Bridge code/stack remain **408 / 688 bytes**. The largest emitted source-site template decreases from **481 to 472**, within the same 512-unit lane. Three initialization stores are counted in the original fixed traversal envelope. No production allowance changes.

[Nine serial whole-process counter executions](binding-calls-hardware-v1/results.json) give candidate **88.0 billion instructions / 17.7 billion cycles**, parent **94.2 billion / 18.2 billion**, and Rust **33.1 billion / 8.48 billion**. Candidate instructions decrease **6.5%**, cycles decrease **2.6%**, and candidate instructions remain **2.66× Rust**. These separate diagnostic executions include every target thread and startup/shutdown and are not extra timing samples. The instruction reduction is larger than the elapsed-time reduction in this stage.

Three fresh full-input profiles ([first](full-profile-binding-calls-v1/analysis.json), [second](full-profile-binding-calls-v2/analysis.json), [third](full-profile-binding-calls-v3/analysis.json)) each observe seven workers. The [profiling copy](profile-binding-calls-build-v1/results.json) matches the timed executable's entire **4,269,840-byte** code section, SHA-256 `16f52fa3805f28417f07b56414cd320cdc5cd53a88669dcc20af951ae4889e7e`. The [exclusive partition](binding-remaining-profile-v1/results.json) combines **13,148 worker observations**: **81.4%** generated counting loops, **6.8%** work accounting including its waits, **6.7%** other waits, **3.7%** active storage helpers, **0.7%** bridge and **0.8%** other active frames. These are sampled thread observations, not elapsed-time shares. [Three fresh Rust captures](rust-full-profile-v5/analysis.json) verify its exact unchanged executable and seven counting workers each.

[Exact disassembly and sampled-PC groups](binding-calls-codegen-audit-v1/results.json), [second](binding-calls-codegen-audit-v2/results.json), [third](binding-calls-codegen-audit-v3/results.json), retain the loop and probe/count sequence. The [specified first-hit successful path](binding-calls-codegen-audit-v1/steady-path-comparison.json) decreases from **98 to 91 instructions** and **14 to seven stack accesses**; ten branches remain. The same Rust path has **34 instructions, two stack accesses and four branches**. These static paths and collapsed groups do not assign individual-instruction runtime costs.

The next proof candidate concerns a source traversal with exactly one successful insertion before every index+1 recurrence. A proved insertion establishes nonempty storage for the next steady iteration; a checked initial equality between the source index and the private update tally could preserve that relation across the loop. This could remove repeated storage checks and separate tally maintenance while retaining every actual map update and original fuel debit. Both the source-path proof and runtime entry guard must precede any substitution; unknown shapes, multiple/skipped insertions and unaligned initial state retain checked code. This candidate is unimplemented and has no assigned gain. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Caller-owned words for cold helper calls

Compiler [`0eb2745bc`](https://github.com/mech-lang/mech/commit/0eb2745bcededcbe2f4a265fb8bc61d6f06b8b28), IR56/ABI27/work65, passes one invocation-local scratch pointer to the preserving bridge. The scratch contains the original function pointer, context, source site, operation, three arguments, result pointer and a separate status word. The installed Rust helper retains its original seven-argument C ABI. The change reduces argument-register demand without changing the source, bytecode, operations, errors or launch policies.

Three rotated **125-million-base** cohorts retain every complete process, with secured startup/shutdown and no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.550 | 1.00× |
| Previous preserving-call Mech, IR55 | 1.306 | 2.37× |
| Scratch-call Mech, IR56 | 1.256 | 2.28× |

The median is **3.8% lower**, a **1.04× speedup**. Candidate observations span 1.253–1.263 seconds, below the parent's 1.291–1.317 seconds. The [aggregate](full-scratch-calls-cohort-v1/results.json) retains raw observations, standard deviations, execution order and identities. Every candidate execution verifies complete output, all **874,999,961 updates**, seven packed SSA maps, seven bounds/call-guard entries, five complete frozen query maps, ten original reads and seven peak workers. Subjects execute serially under the common lock.

The [one-million-base prefix](scratch-calls-timing-v1/results.json), with one excluded warmup per executable and three timed observations, gives Rust **0.0131 seconds**, parent **0.0914 seconds / 6.95× Rust**, and candidate **0.0937 seconds / 7.13× Rust**. The candidate median is **2.5% higher**, with overlapping ranges; this protocol establishes no prefix gain. Its denominator remains separate from the full-input cohort.

[Five focused checks](../native-owner-dispatch-v1/scratch-calls-focused-v1/summary.json), the [full native suite](../native-owner-dispatch-v1/scratch-calls-native-v1/summary.json), **342 GPU tests**, and the [catalog test](../native-owner-dispatch-v1/scratch-calls-catalog-v1/summary.json) pass; three existing exclusions remain. They execute live scalar/vector values across the real bridge and a helper that overwrites their backing memory; independent result/status words and argument order; changed runtime inputs, seeds, growth/refills, exact work, original errors, declined proofs and exact/one-short stack/code limits. Each loop now has **7,252 code bytes / 256 stack bytes**, versus the parent's **7,256 / 288**. The **72-byte caller scratch** is included in the actual compiled frame. The bridge has **408 code bytes / 688 stack bytes**, within its checked 128-instruction bound. All emitted source-site templates remain within the original 512-unit lane, with an observed maximum of **481**; the extra initial bridge work remains **128**, within the existing 1,024-unit lane. No production allowance changes.

[Nine separate whole-process counter executions](scratch-calls-hardware-v1/results.json) give candidate **94.2 billion instructions / 18.3 billion cycles**, parent **96.8 billion / 18.9 billion**, and Rust **33.2 billion / 8.15 billion**. Candidate instructions decrease **2.7%**, cycles decrease **3.3%**, and candidate instructions remain **2.84× Rust**. These diagnostic executions include all threads and startup/shutdown and are not extra timing-cohort samples.

Three fresh full-input profiles ([first](full-profile-scratch-calls-v1/analysis.json), [second](full-profile-scratch-calls-v2/analysis.json), [third](full-profile-scratch-calls-v3/analysis.json)) each observe seven workers. The [profiling copy](profile-scratch-calls-build-v1/results.json) matches all **4,270,864 machine-code bytes** of the timed executable, SHA-256 `586963dfdde80440b1f10c5822c9be049891a62a8d67149b5c125386178ed462`. The [exclusive partition](scratch-remaining-profile-v1/results.json) combines **13,309 worker observations**: **82.5%** generated counting loops, **6.4%** work accounting including its waits, **6.3%** other waits, **3.3%** active storage helpers, **0.6%** generated bridge and **0.9%** other active frames. These are sampled thread observations, not elapsed-time shares or instruction costs. [Three new captures](rust-full-profile-v4/analysis.json) verify the exact unchanged Rust executable and seven counting workers each.

[Exact disassembly and sampled-PC groups](scratch-calls-codegen-audit-v1/results.json), [second](scratch-calls-codegen-audit-v2/results.json), [third](scratch-calls-codegen-audit-v3/results.json), retain the remaining counting-loop loads and probe/count sequence. The [specified first-hit successful path](scratch-calls-codegen-audit-v1/steady-path-comparison.json) decreases from **101 to 98 instructions** and **19 to 14 stack-access instructions**; ten branches remain. The corresponding Rust path retains **34 instructions, two stack accesses and four branches**. Static paths and collapsed PC groups do not establish per-instruction runtime costs.

The remaining gap is concentrated in generated counting code. It still rematerializes hash constants, reconstructs the rolling key twice and reloads invariant/source state. Hoisting immutable cold-call bindings is a further register-pressure candidate; reducing per-window bookkeeping needs separate source and resource proofs. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Validated-head profiles and remaining costs

Compiler [`0aab5c81b`](https://github.com/mech-lang/mech/commit/0aab5c81b0b989b3c7b6ff78abc84ef06df844aa), IR55/ABI27/work65, passes the [full native suite](../native-owner-dispatch-v1/preserving-calls-native-v3/summary.json): **342 GPU tests and one catalog test**, with three existing exclusions. It restricts preserving helper calls to loops with the required proofs and charges nested stack only for the bridge actually used. Unsupported or disabled proofs retain ordinary calls and the original limits. The final test correction verifies both eligible and declined fixtures.

Three new rotated **125-million-base** cohorts retain every complete process, with secured startup/shutdown and no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.557 | 1.00× |
| Original-source Mech control, IR54 | 1.438 | 2.58× |
| Validated preserving-call Mech, IR55 | 1.299 | 2.33× |

The candidate median is **9.7% lower** than its control. All three candidate observations, 1.287–1.309 seconds, precede the control range of 1.428–1.440 seconds. The [aggregate](full-preserving-calls-qualified-cohort-v1/results.json) retains every observation, standard deviation, execution order and identity. Output, all **874,999,961 updates**, seven packed SSA maps, seven bounds/call-guard entries, five complete frozen query maps, ten original reads and seven peak workers pass on every candidate run. Source, bytecode, input and finite launch policies match the control. All benchmark subjects execute serially under the common lock.

The [fresh one-million-base prefix](preserving-calls-qualified-timing-v1/results.json), with one excluded warmup per executable and three timed observations, gives Rust **0.0194 seconds**, control **0.1043 seconds / 5.37× Rust**, and candidate **0.0968 seconds / 4.98× Rust**. This is a separate protocol and does not replace the older retained prefix regression below.

Three fresh complete-input captures ([first](full-profile-preserving-calls-qualified-v1/analysis.json), [second](full-profile-preserving-calls-qualified-v2/analysis.json), [third](full-profile-preserving-calls-qualified-v3/analysis.json)) each observe seven workers. The [profiling copy](profile-preserving-calls-qualified-build-v1/results.json) matches all **4,270,864 bytes** of the timed executable's machine-code section, SHA-256 `4db1f5e69da5d02b04e65a864e69da2bf727de2746852724c2bae75488afe556`. The [exclusive worker partition](remaining-profile-v1/results.json), reproduced by [profile_hotspots.py](profile_hotspots.py), combines **14,723 observations**:

| Observed worker location | Observations | Share |
|---|---:|---:|
| Generated counting loops | 12,433 | 84.4% |
| Work-budget operations, including their waits | 862 | 5.9% |
| Other waits | 783 | 5.3% |
| Active storage helpers | 457 | 3.1% |
| Generated helper bridge | 69 | 0.5% |
| Other active frames | 119 | 0.8% |

Budget observations split into **557 waiting / 305 active**. The main thread is in worker joins for **84.2%, 92.0% and 92.2%** of its observations. These are thread samples, including waits and profiler overhead; they are not percentages of elapsed time or instruction costs. Startup includes loader/debugger-notification artifacts, so no precise startup duration is inferred. [Three new Rust captures](rust-full-profile-v3/analysis.json) use its exact unchanged executable, verify every complete output and observe seven counting workers in every capture.

[Fresh whole-process hardware counters](preserving-calls-qualified-hardware-v1/results.json), collected in nine separate serial diagnostic executions, give Mech **96.8 billion instructions / 19.1 billion cycles**, control **104.4 billion / 21.8 billion**, and Rust **33.1 billion / 7.91 billion**. Mech still retires **2.92× Rust's instructions**. These executions include all threads and startup/shutdown; they are not additional timing-cohort observations.

The [exact disassembly and sampled-PC groups](preserving-calls-qualified-codegen-audit-v1/results.json), [second capture](preserving-calls-qualified-codegen-audit-v2/results.json), [third capture](preserving-calls-qualified-codegen-audit-v3/results.json), place the large groups in the counting-loop fuel entry and SIMD probe/match sequence. Collapsed groups contain multiple PCs and do not assign individual-instruction costs. The native Object and all four generated-function disassemblies are identical to the first preserving-call candidate; the complete host binaries differ. The [specified first-hit successful path](preserving-calls-qualified-codegen-audit-v1/steady-path-comparison.json) therefore remains:

| Static existing-key iteration | Mech | Rust |
|---|---:|---:|
| Instructions | 101 | 34 |
| Branches | 10 | 4 |
| Stack-access instructions | 19 | 2 |

The path retains repeated loads/stores of table state, source bounds and rolling-key state; two rematerialized hash constants; duplicate rolling-key construction; and source overflow/accounting checks. This evidence prioritizes reducing register pressure and repeated work in the generated loop. Narrowing the cold bridge to one scratch-pointer argument is an unmeasured register-allocation candidate. Moving invariant guards or deriving accounting values from source induction variables requires independent correctness and resource proofs. No speedup is assigned to any next candidate. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Register-preserving private helper bridge: initial candidate

Compiler [`35c634db0`](https://github.com/mech-lang/mech/commit/35c634db0937c32ceb9895036cdb5f70a47a74c3) emits an owned AArch64 `PreserveAll` bridge around the installed private helper. Only the generated bridge has that calling convention; it calls the original Rust helper through the unchanged seven-argument native C ABI. The helper result word and the caller-owned status word remain separate. The bridge has no return registers, keeps full vector register contents, and retains every helper argument, source site, error and original frame-effect synchronization.

IR55 identifies the generated-call change. ABI27, work65, original source/bytecode, inputs and finite launch policies remain. The bridge has **404 code bytes / 688 stack bytes**, within a checked 128-instruction native template. Every source-site emission plus all its emitted bridge templates must fit the existing 512-unit lane; the extra initial call fits the existing 1,024-unit traversal lane. Each loop records 39 emitted call templates, at most 457 source-site units and 128 additional initial units. Total code includes the bridge once; nested stack admission includes the parent, its actual outlined callee and the bridge. No allowance is raised.

Three rotated **125-million-base** cohorts retain all complete-process observations, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.545 | 1.00× |
| Previous original-source Mech | 1.441 | 2.64× |
| Register-preserving Mech | 1.308 | 2.40× |

The candidate median is **9.2% lower**, a **1.10× speedup**. Candidate observations span 1.295–1.310 seconds, below the parent's 1.433–1.450 seconds. The [aggregate](full-preserving-calls-cohort-v1/results.json) retains all seconds, standard deviations and identities. Every candidate execution verifies complete output, all **874,999,961 updates**, seven packed SSA maps, seven bounds/call-guard selections, five complete frozen query maps, ten original reads and seven peak workers. Source and bytecode match the control. Secured startup/shutdown are included; subjects execute serially under the shared lock.

The [one-million-base prefix](preserving-calls-timing-v1/results.json) regresses: Rust **0.0192 seconds**, original Mech **0.0936 seconds / 4.87× Rust**, and the candidate **0.1102 seconds / 5.74× Rust**. This median is **17.8% higher**, with non-overlapping candidate/control ranges. That protocol has one excluded warmup per executable, unlike the full cohorts. The regression is retained.

[Five focused tests](../native-owner-dispatch-v1/preserving-calls-focused-v2/summary.json) pass. They directly execute live scalar/vector values across a native helper that overwrites their backing memory, verify independent full-width result/status words, and compare ordinary versus preserving calls across original/decoded source, arbitrary seeds, changed inputs, bounds, growth, full-loan refills, exact work, original arithmetic failures and precise error frontiers. Exact combined stack/code limits pass and each one short fails. A [retained compile attempt](../native-owner-dispatch-v1/preserving-calls-focused-v1/summary.json) exceeded the existing JSON metadata macro recursion limit before tests; the correction builds the two added receipt fields separately.

[Separate hardware-counter executions](preserving-calls-hardware-v1/results.json) give **96.8 billion instructions / 19.1 billion cycles**, versus **104.4 billion / 21.8 billion** for the control and **33.1 billion / 7.96 billion** for Rust. Instructions decrease **7.3%**, cycles decrease **12.6%**, and Mech still retires **2.92× Rust's instructions**. These nine diagnostic executions verify every output/update and are separate from timing cohorts.

The [fresh profile](full-profile-preserving-calls-v1/analysis.json) observes seven workers and 4,632 worker samples, of which 3,928 (**84.80%**) end in generated code. Inclusive library-debit/wait shares are **5.57% / 9.33%**, with no publication observed. Categories overlap and are not elapsed-time shares. The profiling copy matches all **4,270,864 machine-code bytes**, SHA-256 `0c6374489d21b29c9c84d0e6f7708987ecd0573a92482c7a022206583ae381d4`. [Exact disassembly](preserving-calls-codegen-audit-v1/results.json) covers the parent, both loops and the bridge. Each loop shrinks from 7,612 code bytes / 336 stack bytes to **7,256 / 288**.

The [documented successful steady path](preserving-calls-codegen-audit-v1/steady-path-comparison.json) falls from 110 instructions and 34 stack accesses to **101 instructions and 19 stack accesses**, with ten branches in both. The same unchanged Rust executable has 34 instructions, two stack accesses and four branches under the stated first-hit/funded conditions. These are static paths, not dynamic frequencies. The new path still reloads source bounds and key state, rematerializes hash constants, and computes the rolling key twice. Reducing the preserving bridge's argument-register demands is the next unmeasured candidate.

The [first full regression attempt](../native-owner-dispatch-v1/preserving-calls-native-v1/summary.json) passes 330 tests and fails 12 deliberately less-proven/disabled-pass cases at the unchanged source-site envelope. Follow-up compiler `d5b510543` gates bridge selection on the required bounds, tag, lookup and frame-effect proofs; other loops retain ordinary native calls. Stack admission adds the bridge only to the callees that actually use it. The [next full attempt](../native-owner-dispatch-v1/preserving-calls-native-v2/summary.json) passes 341 GPU tests and fails one assertion that incorrectly required bridge selection for a deliberately declined arithmetic fixture. The test correction retains an explicit eligible-case requirement and the declined-case fallback, and the final full suite passes above. This section's timings and profile belong to `35c634db0`; the validated-head observations remain separate above.

## Source-shape comparison: no established full-input gain

Three sources are compiled with the **same compiler**, [`75609235b`](https://github.com/mech-lang/mech/commit/75609235ba6301952d63315413b827ac337f3fea), IR54/ABI27/work65. This revision changes only a test relative to `59782769d`; the [rebuilt public compiler](compiler-v33/results.json) has the same executable SHA-256 as compiler-v32. The [new original-source control](source-control-timing-v1/results.json) retains the original source and bytecode hashes. Both changed sources and their different bytecodes are explicitly pinned rather than represented as unchanged-source compiler improvements:

- [Direct-match insertion](knucleotide-source-match-insert.mec) makes each membership branch return its updated map. It removes the intermediate previous-count binding and retains `Present`/`Absent` facts through the corresponding insertion, instead of merging to `Cached`.
- [Precomputed loop end](knucleotide-source-loop-end.mec) calculates the number of valid windows once, with guarded handling of zero/oversized widths. The state machine has one stopping comparison. Its increment function is unchanged.

Both still traverse every overlapping window, store every key, perform every count update and build all seven histograms. Neither changes the input, queries, compiler, executable launch policy or security/accounting machinery. Each candidate is compared separately with the freshly built original-source control and upstream Rust #7.

Each row below aggregates three rotated **125-million-base** cohorts, retaining every complete-process observation with no excluded warmup. The Rust denominator is from that row's own cohort:

| Source change | Rust seconds | Original Mech seconds | Changed Mech seconds | Original × Rust | Changed × Rust |
|---|---:|---:|---:|---:|---:|
| Direct-match insertion | 0.564 | 1.438 | 1.454 | 2.55× | 2.58× |
| Precomputed loop end | 0.557 | 1.435 | 1.432 | 2.57× | 2.57× |

The direct-match median is **1.1% higher**; the precomputed-end median is **0.2% lower**. Both candidate/control ranges overlap, so **neither establishes a full-input runtime gain**. [Direct-match aggregate](full-source-match-insert-cohort-v1/results.json) and [precomputed-end aggregate](full-source-loop-end-cohort-v1/results.json) retain all seconds, standard deviations, identities and executable receipts. Secured startup/shutdown are included and subjects execute serially under the shared lock. Every full execution verifies output, all **874,999,961 updates**, seven packed SSA maps, five complete frozen query maps, ten original reads and seven peak workers.

The [direct-match prefix trial](source-match-insert-timing-v3/results.json) gives Rust **0.0209 s**, original Mech **0.0981 s / 4.70× Rust**, and changed Mech **0.0921 s / 4.41× Rust**. Its approximately 6% prefix reduction does not carry over to the full-input cohorts. The [precomputed-end prefix](source-loop-end-timing-v1/results.json) gives Rust **0.0208 s**, original **0.0937 s / 4.51× Rust**, and changed **0.0952 s / 4.58× Rust**. Prefix observations include one excluded warmup per executable, unlike the full cohorts.

An [independent all-entry validation](source-variants-correctness-v3/results.json) executes all three actual histogram definitions against seven runtime-supplied strings and nine widths: **189 histograms**, with every key and count compared with Python `Counter` over all overlapping windows. Cases include empty input, zero width, oversized width, repetitive data, random DNA and a fifth ASCII symbol. The fixture reads its inputs at runtime. [Two retained all-constant fixture failures](source-variants-correctness-v1/results.json), [second attempt](source-variants-correctness-v2/results.json), stopped during canonical resource planning before execution; they are not counted as correctness passes.

The direct-match source has 91 graph nodes per original region instead of 90, and each outlined loop has **8,020 code bytes / 336 stack bytes**, versus **7,612 / 336** for the control. It retains all seven actual bounds/call-guard selections. Precomputing the end reduces the graph to 59 nodes and each loop to **2,620 code bytes / 288 stack bytes**, but produces **zero** bounds/call-guard selections. The current proof recognizes the original three-stop shape; the precomputed-end variant uses checked code, with its original per-call checks active. Smaller generated code is not evidence of fewer executed instructions.

Separate hardware-counter runs verify every output/update and retain all nine diagnostic executions per source trial:

| Diagnostic cohort | Rust instructions | Original Mech instructions | Changed Mech instructions | Changed / Rust instructions |
|---|---:|---:|---:|---:|
| [Direct-match](source-match-insert-hardware-v1/results.json) | 33.14 billion | 104.38 billion | 102.65 billion | 3.10× |
| [Precomputed end](source-loop-end-hardware-v1/results.json) | 33.14 billion | 104.41 billion | 122.77 billion | 3.70× |

Direct-match instructions decrease **1.7%**, while cycles rise from **21.70 to 22.35 billion**. Precomputed-end instructions increase **17.6%**, with cycles rising from **21.80 to 22.38 billion**. These counters include all target threads and startup/shutdown and are not additional timing-cohort samples. No fresh sampled profile or reduced dynamic-check frequency is claimed for either source rewrite.

The [first direct-match attempt](source-match-insert-timing-v1/results.json) failed source parsing before compilation; its original candidate is retained. The [next attempt](source-match-insert-timing-v2/results.json) built successfully but encountered an original-source qualification rule requiring a `Cached` insertion. The changed source legitimately emits stronger `Present`/`Absent` insertions. The successful retry checks those facts against their exact source operations, reuses only the pinned completed build, and takes entirely fresh timing observations. No timing observation is reused or silently discarded.

Source simplification remains useful for clarity and for exposing compiler gaps: presence through joins and precomputed-end range proofs should not require a particular source spelling. These trials do not establish a performance win or Rust parity. The original source remains the optimization control; canonical published benchmark data and historical timings are unchanged.

## Control cleanup before one backend data pass: identical hot loops

Compiler [`59782769d`](https://github.com/mech-lang/mech/commit/59782769d0ebb27fc8edc93e6e3620e65d8bf8ac) performs bounded literal control cleanup before the backend's single ordinary data/speed pass. It no longer invokes the full egraph repeatedly during cleanup. IR54 identifies the order; ABI27, work65, source, bytecode, inputs and finite launch limits are unchanged.

[Four cleanup checks](../native-owner-dispatch-v1/cfg-prepass-focused-v1/summary.json) and [four loop-invariant checks](../native-owner-dispatch-v1/loop-invariants-prepass-v1/summary.json) pass, including source effects, dynamic conditions, edge arguments, exact work, arithmetic errors, runtime seeds, refills and actual call-limit transitions. The [full native suite](../native-owner-dispatch-v1/cfg-prepass-native-v2/summary.json) passes **337 GPU tests and one catalog test**, with three existing exclusions. A [retained first attempt](../native-owner-dispatch-v1/cfg-prepass-native-v1/summary.json) passed 336 tests and stopped at a stale guarded-range metadata expectation. The test-only correction in [`75609235b`](https://github.com/mech-lang/mech/commit/75609235ba6301952d63315413b827ac337f3fea) binds that expectation to the actual emitted version stride; production code is unchanged.

Three rotated **125-million-base** cohorts retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.554 | 1.00× |
| Previous guarded steady loops | 1.455 | 2.63× |
| Cleanup before data optimization | 1.466 | 2.65× |

The candidate median is **0.8% higher**, with overlapping ranges; **no runtime gain** is established. The [aggregate](full-cfg-prepass-cohort-v1/results.json) retains raw observations and standard deviations. The [one-million-base prefix](cfg-prepass-timing-v1/results.json) gives 0.0193 seconds for Rust, 0.1071 for the parent (**5.55× Rust**) and 0.1103 for the candidate (**5.71× Rust**). All output/update, seven initial guarded-call selections, bounds/SSA selection, full-map, original-read and peak-worker checks pass. Secured startup/shutdown are included and subjects execute serially.

[Exact object-text comparison](cfg-prepass-code-identity-v1/results.json) shows that **both 7,612-byte hot-loop functions are byte-for-byte identical** to the prior stage. The complete generated program text differs elsewhere (58,712 versus 58,764 bytes), so no whole-program identity is claimed. A new matched hot-loop profile is unnecessary for this order change: it cannot explain or fix the already observed steady-loop duplication and stack accesses. No instruction-counter gain is inferred.

The [prior exact steady-path comparison](loop-invariants-codegen-audit-v1/steady-path-comparison.json) counts **110 instructions, ten branches and 34 stack-access instructions** in Mech, versus **34 instructions, four branches and two stack accesses** in Rust, under its explicitly stated first-key-hit, productive, funded conditions. These are static paths, not dynamic frequencies. The next structural target is state kept live across fail-only callbacks, followed by isolating cold callbacks from the hot native loop if necessary. These targets have no assigned gain. Rust parity, full qualification of subsequent changes, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Guarded calls and peeled rolling keys: no runtime gain

Compiler [`f0ae06384`](https://github.com/mech-lang/mech/commit/f0ae063843856d45ac09eb3cf7a917c07ebfd702) emits four bounded source-graph versions: checked; proved bounds; proved bounds/call flags; and proved bounds/call flags/steady adjacency. The first selection retains its original rolling check. Only certified index+1 active recurrence edges enter the steady version. Every storage-changing insertion, including a non-growing insertion, refreshes to its exact source successor with current call flags; it cannot repeat or skip a funded header or source operation. Invalid or unsupported proofs retain the checked graph. Generated spills retire every generated Frame word; runtime-owned words are already current in memory and cannot be written by the generated setter.

IR53 and ABI27 identify the change. The existing op14 receipt records the actual initial call-guard selection and independently validates all three flags; source, bytecode, inputs, work65 and finite launch limits remain unchanged. Emission qualification binds each removed call check, steady range, certified latch and post-insertion refresh to the original sites. Each of the two compiled regions has 360 product nodes (stride90) and 224 fixed template instructions within the unchanged 1,024-unit envelope.

Three rotated **125-million-base** cohorts retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.551 | 1.00× |
| Previous isolated loops, `7f0bf64de` | 1.437 | 2.61× |
| Guarded steady loops, `f0ae06384` | 1.442 | 2.62× |

The candidate median is **0.4% higher**, with overlapping ranges. This establishes **no runtime gain**. The [aggregate](full-loop-invariants-cohort-v1/results.json) retains all raw observations and standard deviations. The [one-million-base prefix](loop-invariants-timing-v1/results.json) gives 0.0115 seconds for Rust, 0.0915 for the parent (**7.95× Rust**) and 0.1083 for the candidate (**9.41× Rust**): the candidate median is **18.3% higher** in that protocol. Each protocol uses its own Rust cohort.

Every candidate execution verifies seven actual initial guarded-call selections alongside seven packed SSA maps, seven selected bounds guards, five complete frozen maps, ten original reads, seven peak workers, complete output and all **6,999,961 prefix / 874,999,961 full updates**. Subjects execute serially under the shared lock, including secured startup/shutdown. No production allowance changes.

[Four focused tests](../native-owner-dispatch-v1/loop-invariants-focused-v3/summary.json) pass across original/decoded source, arbitrary seeds, changed runtime inputs, growth/full-loan refills, exact work, original arithmetic failures and declined proofs. The width18 transition fixture funds the first 278-unit missing-key insertion, which raises the next write price to 300; the following existing-key write fails at its original source site, with equal reference work, status, origin and helper frontiers. The [first retained attempt](../native-owner-dispatch-v1/loop-invariants-focused-v1/summary.json) stopped at an old one-versus-three emitted-range expectation. The [second](../native-owner-dispatch-v1/loop-invariants-focused-v2/summary.json) exposed an underfunded transition fixture that could not pay its original missing-key maintenance. Both failures remain. A full native-suite qualification for this revision is not claimed.

[Separate hardware-counter executions](loop-invariants-hardware-v1/results.json) show **104.4 billion instructions / 21.7 billion cycles**, versus **107.9 billion / 21.5 billion** for the parent and **33.1 billion / 7.94 billion** for Rust. Instructions decrease only **3.2%**, cycles rise slightly, and Mech still retires **3.15× Rust's instructions**. Diagnostic executions are separate from the timing cohorts. Each compiled loop still uses 336 stack bytes, with code increasing from 5,136 to 7,612 bytes.

The [fresh full profile](full-profile-loop-invariants-v1/analysis.json) observes seven workers and 5,111 worker samples; 4,551 (**89.04%**) end in generated code. Inclusive library-debit/wait shares are **4.48% / 5.73%**, with no publication observed. Categories overlap and are not elapsed-time shares. The profiling copy matches the timed executable's entire **4,271,068-byte** code section, SHA-256 `33a9255451ab414294feb55d59835f3cb9c44cc3b573d8f39d85ae828e79abad`. [Exact disassembly](loop-invariants-codegen-audit-v1/results.json) shows the remaining fuel/induction bookkeeping, stack traffic, hash-constant materialization, and a repeated rolling-key expression on the successful steady path. Removing source-level checks did not by itself produce efficient machine code.

The subsequent prepass trial above moves literal CFG cleanup before the single ordinary backend data pass and establishes no runtime gain. Further failure-path live ranges remain a target, without an assigned gain. Rust parity, full qualification of subsequent candidates, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Isolated closed-loop functions

Compiler [`7f0bf64de`](https://github.com/mech-lang/mech/commit/7f0bf64dee07734402d4c00c25ac3fe392038adc) isolates each eligible closed packed loop in a local native function emitted from the same source body as its inline fallback. The caller retains the original selector and one packed-SSA receipt. Each synchronous call returns only at its original exit/error boundary; the original source locals, private owner, helper/context, transport context and finite loan remain. Total stack admission includes the parent plus the largest emitted callee, and total code includes every callee. Fixed caller/loader/return templates fit the unchanged per-traversal work envelope. IR52 identifies the change; ABI26 and work65 remain.

Three rotated **125-million-base** cohorts retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.548 | 1.00× |
| Previous CFG cleanup, `40e86c965` | 1.455 | 2.66× |
| Isolated loops, `7f0bf64de` | 1.405 | 2.56× |

The candidate median is **3.4% lower**, with overlapping candidate/parent ranges (1.379–1.430 versus 1.420–1.472 seconds). This is a small observed gain. The [aggregate](full-loop-outlining-cohort-v1/results.json) retains raw observations and standard deviations. The [one-million-base prefix](loop-outlining-timing-v1/results.json) gives 0.0195 seconds for Rust, 0.0965 for the parent (**4.94× Rust**) and 0.0994 for the candidate (**5.08× Rust**), with overlapping ranges and no established prefix gain. All candidate executions verify every output and **6,999,961 prefix / 874,999,961 full updates**, seven packed SSA maps, seven guarded selections, five complete frozen maps, ten original reads and seven peak workers. Source, bytecode, inputs and finite launch limits match the parent. Subjects execute serially, including secured startup/shutdown.

[Four focused tests](../native-owner-dispatch-v1/loop-outlining-focused-v1/summary.json) compare inline and outlined execution across runtime inputs, arbitrary seeds, source overflow/errors, growth, full-loan/refill and exact-work boundaries. Metadata/admission checks accept exact combined stack/code limits and reject each one short. The [full native suite](../native-owner-dispatch-v1/loop-outlining-native-v1/summary.json) passes **333 GPU tests and one catalog test**, with three existing exclusions.

Two source-bound functions are emitted, at headers 173 and 284, each with 336 stack bytes and 5,136 code bytes. Their bounded cleanup reports 17 constant branches removed each. [Separate hardware-counter executions](loop-outlining-hardware-v1/results.json) give medians of **107.9 billion instructions / 21.5 billion cycles**, versus **111.5 billion / 22.3 billion** for the parent and **33.2 billion / 7.98 billion** for Rust. Mech still retires **3.26× Rust's instructions**. These complete-process diagnostic counters are separate from the timing cohorts.

The [fresh full profile](full-profile-loop-outlining-v1/analysis.json) observes seven workers and 5,042 worker samples; 4,449 (**88.24%**) end in generated code. Inclusive library-debit/wait shares are **4.86% / 6.27%**, with no publication observed. Categories overlap and are not elapsed-time shares. The profiling executable matches the timed executable's entire **4,263,740-byte** code section, SHA-256 `e8fd6ee9be7e88e8e7c431823da431dd2e7cda749fe99695f07386c8ed9e7462`. [Exact disassembly](loop-outlining-codegen-audit-v1/results.json) covers the parent entry and both local loop functions; sampled-PC groups resolve into those actual functions, including stack reloads and SIMD probing.

Isolation alone leaves most of the gap. The next candidate targets repeated call-limit checks and rolling-window adjacency checks through guarded loop versions, with rechecks after storage-changing callbacks and the original checked path retained. No gain is assigned to that candidate. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Bounded constant control-flow cleanup

Compiler [`40e86c965`](https://github.com/mech-lang/mech/commit/40e86c965464d18a6ca990fa9e4b7a0c6af51e1b) runs bounded constant-branch cleanup after Cranelift data optimization. It folds only literal integer conditions, preserves the selected edge's arguments, and uses the backend's unreachable-block and constant-phi cleanup before register allocation. Dynamic conditions, source effects, failures, capabilities and finite work remain. The ordinary final speed pipeline still runs. IR51 identifies the change; ABI26, work65, source, bytecode, inputs and launch policies are unchanged.

Six rotated **125-million-base** cohorts retain every complete-process observation, with no excluded warmup or outlier:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.550 | 1.00× |
| Previous current-key lookup stage, `bebf57769` | 1.538 | 2.80× |
| Constant CFG cleanup, `40e86c965` | 1.463 | 2.66× |

The median is **4.9% lower**, a **1.05× speedup**. Candidate observations span 1.451–1.481 seconds, below the parent's 1.525–1.550 seconds. A 0.991-second Rust observation in the first three cohorts prompted three additional balanced cohorts; all six observations remain in the [aggregate](full-cfg-cleanup-cohort-v1/results.json). This remains far from Rust parity.

The [one-million-base prefix](cfg-cleanup-timing-v1/results.json), with three alternating observations and one excluded warmup per executable, gives 0.0209 seconds for Rust, 0.0937 for the parent (**4.49× Rust**) and 0.0964 for the candidate (**4.62× Rust**). The candidate median is **2.9% higher**, with overlapping ranges, so this protocol establishes no prefix gain. Every candidate execution independently verifies seven packed SSA maps, seven selected guarded loops, five entire frozen maps, ten original reads, seven peak workers, complete output and all **6,999,961 prefix** or **874,999,961 full-input updates**. Subjects execute sequentially under the shared lock, including secured startup/shutdown.

[Four focused tests](../native-owner-dispatch-v1/cfg-cleanup-focused-v2/summary.json) compare enabled and disabled compilation across selected effects, noncanonical boolean words, block arguments, runtime inputs, growth/refills, finite limits and source errors. The [full suite](../native-owner-dispatch-v1/cfg-cleanup-native-v1/summary.json) passes **329 GPU tests and one catalog test**, with three existing exclusions. A [retained compile failure](../native-owner-dispatch-v1/cfg-cleanup-focused-v1/summary.json) exposed entry-point visibility before tests ran; the correction changes no runtime behavior. No production allowances changed.

The emitted function reports 56 literal branches removed in two rounds. Its combined data/control optimization reports 3,249 remaining blocks and 12,073 instructions, versus 3,643 and 17,183 before those passes. Those compiler counts are not machine instructions or isolated CFG-pass savings. [Separate macOS hardware-counter executions](cfg-cleanup-hardware-v1/results.json) give medians of **111.6 billion instructions and 22.6 billion cycles** for the candidate, versus **119.9 billion / 24.0 billion** for its parent and **33.1 billion / 7.86 billion** for Rust. Candidate instructions are 7.0% lower than the parent and still **3.37× Rust**. These complete-process diagnostic counters include every target thread and startup/shutdown; they are not extra timing-cohort observations.

The [fresh full-input profile](full-profile-cfg-cleanup-v1/analysis.json) observes seven workers and 5,328 worker samples; 4,740 (**88.96%**) end in generated code. Inclusive library-debit and wait shares are **4.41%** and **5.69%**, with no publication observed. Categories overlap and are not elapsed-time shares. The profiling copy matches the timed executable's entire **4,273,372-byte** machine-code section, SHA-256 `4e6a88d11058f18ae23b487c9fc0976a99b0467c147373ea10a43129a5579b4c`. [Exact-entry disassembly and sampled-PC groups](cfg-cleanup-codegen-audit-v1/results.json) still identify stack reloads in the counting loop. The next structural candidate isolates each proved closed loop in its own emitted native function to reduce unrelated live state; it has no assigned gain. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Current-key lookup facts and the remaining instruction gap

Compiler [`bebf57769`](https://github.com/mech-lang/mech/commit/bebf5776902092e13bececb99aaed3e8a5f14fc8) derives bounded facts about the current selected key's cache and presence through the original tag graph. A new range or header invalidates the corresponding facts; membership branches establish presence/absence; insertion refreshes the pointer and invalidates old predicates. Copies are simultaneous and joins retain only common facts. Unknown or unsupported cases keep the original lookup. Original per-call checks, arithmetic, errors, source updates and work charges remain. IR50 identifies the change; ABI26, work65, source, bytecode, inputs and finite launch limits are unchanged.

Three rotated **125-million-base** cohorts retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.554 | 1.00× |
| Previous complete-private-map stage, `78007ae6f` | 1.551 | 2.80× |
| Current-key lookup facts, `bebf57769` | 1.522 | 2.75× |

The candidate median is **1.9% lower**. Its 1.520–1.528-second range is below the parent's 1.547–1.556-second range in these cohorts. The [complete aggregate](full-lookup-facts-cohort-v1/results.json) retains raw observations and standard deviations. This is a small gain and does not establish Rust parity.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, gives:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0194 | 1.00× |
| Previous complete-private-map stage | 0.0982 | 5.07× |
| Current-key lookup facts | 0.0952 | 4.91× |

The prefix median is **3.1% lower**, with overlapping candidate/parent ranges. [Prefix receipts](lookup-facts-timing-v1/results.json) retain all observations; the ratios use each protocol's own Rust cohort.

[Emission qualification](lookup-facts-timing-v1/emission-audit.json) binds six substitutions in each of two compiled regions to the exact source membership/get/insert sites: fresh probe, proved present get, and cached insert, in both checked and guarded versions. These are source-bound emission records, not dynamic per-substitution frequencies. Every candidate execution independently verifies seven packed SSA maps, seven selected guarded loops, five complete frozen maps, ten original reads, seven peak workers, complete output and all **6,999,961 prefix** or **874,999,961 full-input updates**. Secured startup/shutdown are included and subjects execute sequentially.

[Focused validation](../native-owner-dispatch-v1/lookup-facts-focused-v2/summary.json) passes six tests covering predicate copies/joins/invalidation, metadata, changed runtime inputs, growth/refills, finite limits and original arithmetic errors. The [full suite](../native-owner-dispatch-v1/lookup-facts-native-v2/summary.json) passes **325 GPU tests and one catalog test**, with three existing exclusions. The retained [focused failure](../native-owner-dispatch-v1/lookup-facts-focused-v1/summary.json) was an overly strict substitution-count assertion on a single-version error fixture. The [first full attempt](../native-owner-dispatch-v1/lookup-facts-native-v1/summary.json) stopped one execution test at its stale IR49 identity assertion; the corrected full run executes it. No production allowances changed.

The [exact-code full profile](full-profile-lookup-facts-v2/analysis.json) observes seven workers and 5,740 worker samples; **89.46%** end in generated code. Inclusive library debit and wait shares are **4.09%** and **5.37%**, with no publication observed. Categories overlap and are not elapsed-time shares. The profiling binary matches all **4,274,648 bytes** of the timed machine-code section, SHA-256 `db0995405bbd125473db311dd6255972f12dd5fda28ef10b6ae3098ddebc30ba`. The first capture attempt was stopped and reaped after the sandbox denied its process inventory; its failed receipt remains. [Three new Rust captures](rust-full-profile-v2/analysis.json) use the exact timed Rust executable and observe seven counting workers on the same full input.

[Separate hardware-counter executions](lookup-facts-hardware-v1/results.json) rotate all three executables, verify every complete output/update receipt and retain all observations:

| macOS whole-process counter, median | Rust | Previous Mech | Current Mech | Current / Rust |
|---|---:|---:|---:|---:|
| Instructions retired | 33.2 billion | 124.2 billion | 119.9 billion | 3.61× |
| CPU cycles | 8.06 billion | 25.1 billion | 24.0 billion | 2.98× |

These include complete process startup/shutdown and all target threads. They are diagnostic counter runs, not extra observations in the timing cohorts. The instruction reduction from the parent is 3.46%, consistent with a small improvement. A [specified existing-key path comparison](lookup-facts-codegen-audit-v1/steady-path-comparison.json), bound to both exact disassemblies, counts **129 Mech instructions, 21 branches and 40 stack-access instructions**, versus **34 Rust instructions, four branches and two stack-access instructions**. Both paths use an initialized rolling key, a first-candidate full-key hit and another productive iteration; Mech's original calls are allowed and its finite loan has fuel. This is a static path comparison, not a measurement of how frequently that path executes.

The next priority is the excess counting-loop instructions and stack traffic. The retained Mech code still has literal constant tests and unreachable continuations from failure helpers despite the speed backend setting. Bounded native CFG cleanup before register allocation is a new candidate under validation; no gain is assigned to it yet. Further loop isolation, invariant state/check placement and source-derived storage bounds remain possible targets. Rust parity, separate decoded-source executable qualification and secured/trusted comparison remain incomplete.

## Retaining complete maps for private reads

Compiler [`78007ae6f`](https://github.com/mech-lang/mech/commit/78007ae6f26e5bb8f7d1c2fec318e5b102304e7d) retains an entire immutable packed map when a complete-use proof permits only private membership and scalar lookup operations in its original parent visit. Every key and count remains, including entries never queried. The five query histograms select this representation; the two frequency histograms still publish canonical maps because they enumerate their keys and values. Source, bytecode, inputs and finite launch limits are unchanged. IR49/ABI26 identify the implementation. Work policy65 prices complete packed-table validation and actual bounded queries; physically removed decoding, copying and sorting no longer incur their old implementation charges. Mutation-body charges and logical result limits remain.

Six **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.556 | 1.00× |
| Previous proved-window stage, `99942aea4` | 1.927 | 3.46× |
| Complete private maps, `78007ae6f` | 1.536 | 2.76× |

The candidate median is **20.3% lower**, a **1.25× speedup**. Candidate observations span 1.518–1.569 seconds, below the parent range of 1.906–1.987 seconds. A slow Rust observation of 1.351 seconds in the first three cohorts prompted three additional balanced cohorts; all six observations per executable remain, including that observation. The [initial three-cohort aggregate](full-frozen-map-cohort-v1/results.json) and [complete six-cohort aggregate](full-frozen-map-cohort-v2/results.json) retain observations, execution order, standard deviations and qualification. This establishes a gain in these cohorts, not Rust parity or a universal speedup.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, gives:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0209 | 1.00× |
| Previous proved-window stage | 0.492 | 23.58× |
| Complete private maps | 0.0968 | 4.64× |

The prefix median is **80.3% lower**, a **5.08× speedup**. Candidate observations span 0.0967–0.1011 seconds, below the parent range of 0.479–0.508 seconds. Median peak resident memory is 28.6 MB for the candidate versus 101.8 MB for its parent. [Prefix receipts](frozen-map-timing-v1/results.json) retain every observation; prefix and full-input ratios use their respective Rust cohorts.

[Emission qualification](frozen-map-timing-v1/emission-audit.json) identifies the complete-use layout, original parent/exit/read sites and prior guarded-loop, scalar-state and Frame proofs. Runtime receipts independently verify **five frozen maps and ten frozen reads**, seven packed SSA maps, seven selected guarded loops, one batch with an observed peak of seven workers, complete output and all **6,999,961 prefix** or **874,999,961 full-input updates** in every candidate run. The frontend elides the source alias in this plan; no private-copy-hook execution is claimed. Complete key/control/fingerprint, uniqueness and probe-reachability validation precedes later source actions. Logical result checks stay at their original result-copy boundary after its source debit. Subjects run sequentially, including secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/frozen-map-focused-v5/summary.json) passes **14 tests**; the [full native suite](../native-owner-dispatch-v1/frozen-map-native-v1/summary.json) passes **319 GPU tests and one catalog test**, with three existing manual exclusions. Coverage includes runtime queries, missing versus zero-valued entries, corruption, proof rejection, finite accounting, private lifetime/retirement, original/decoded/restored plans and concurrent workers. Earlier [compile](../native-owner-dispatch-v1/frozen-map-focused-v1/summary.json), [fixture](../native-owner-dispatch-v1/frozen-map-focused-v2/summary.json), [diagnostic](../native-owner-dispatch-v1/frozen-map-focused-v3/summary.json) and [remaining fixture](../native-owner-dispatch-v1/frozen-map-focused-v4/summary.json) failures remain. In particular, a map crossing an activation boundary correctly declines freezing; it is retained as an executing canonical-fallback case. These receipts do not claim that unsupported function-local captured collection forms gained native lowering.

The [profiling build](profile-frozen-map-build-v1/summary.json) matches the timed executable's entire **4,277,028-byte** machine-code section, SHA-256 `255614b3f5a2f21f53f8c67fa100c79526e6aa7a406957ae6b997864a1508972`. The [full-input capture](full-profile-frozen-map-v1/summary.json) observes seven workers and 6,117 worker samples: **90.76%** have generated program code as their innermost recorded frame. Inclusive shares are **3.63%** for library work debits and **4.69%** for waiting. No canonical publication appears in this capture; the two frequency maps still perform it. Both [prefix](prefix-profile-frozen-map-v1/summary.json) [attempts](prefix-profile-frozen-map-v2/summary.json) complete correctly but capture empty call graphs, so they provide no hotspot observations. Categories overlap and include waits, partial unwinds and profiling overhead; they are not elapsed-time shares or matched baseline profiles.

[Exact-code disassembly](frozen-map-codegen-audit-v1/results.json) maps the retained full-input sampled-PC groups to SIMD table probing, entry-presence tests and stack reloads, including a duplicated entry-pointer reload before a count store. A collapsed group's count cannot be assigned to each listed instruction. The remaining priority is to simplify the generated counting loop: prove cache state across source calls, reduce loop-carried state and stack traffic, and remove repeated checks only where their original behavior is proved. These are next targets, not measured speedups. Separate decoded-source executable qualification, secured/trusted comparison and Rust parity remain incomplete.

## Proved window bounds

Compiler [`99942aea4`](https://github.com/mech-lang/mech/commit/99942aea47a938b30b06196d0fab1d8b88e32962) selects a guarded native version when the source's invariant width and limit fit the actual pinned String. A bounded proof follows the original unsigned stop conditions, exact index recurrence, selected range and unchanged stop payload. The selected version uses one trip-end decision and omits certified range bounds; unsupported conditions retain the original checked graph. Every original header, refill, terminal visit, source count update, overflow check and source error origin remains. IR48/ABI25 identify the actual-selection helper; work policy64, source, bytecode and finite launch policies are unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.555 | 1.00× |
| Previous helper-synchronization stage, `f2bb3c924` | 2.091 | 3.76× |
| Proved window bounds, `99942aea4` | 1.977 | 3.56× |

The candidate median is **5.4% lower**. Candidate observations span 1.975–1.980 seconds, below the parent range of 2.010–2.120 seconds. [Full cohort receipts](full-guarded-loop-cohort-v1/results.json) retain all observations and standard deviations. This establishes a gain in these cohorts, not Rust parity or a universal speedup.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, gives:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0214 | 1.0× |
| Previous helper-synchronization stage | 0.514 | 24.0× |
| Proved window bounds | 0.497 | 23.3× |

The prefix median is **3.2% lower**, with overlapping ranges: 0.488–0.512 seconds for the candidate versus 0.506–0.535 for its parent. [Prefix receipts](guarded-loop-timing-v1/results.json) retain every observation; the full-input and prefix ratios use their respective Rust cohorts.

[Emission qualification](guarded-loop-timing-v1/emission-audit.json) binds both compiled regions to their exact source guards, carrier projections, invariant width/limit, inclusive range and original recurrence latch. Each region emits 180 checked/fast product nodes, one certified fast range version and 140 bounded fixed-template instructions. These are emitted records rather than dynamic instruction counts. The original Frame synchronization, scalar proofs and complete fallback remain qualified. A separate runtime receipt verifies that **all seven guarded selectors actually chose the fast version** in every candidate warmup and timed run, alongside seven packed SSA maps, seven concurrent workers, complete output and all **6,999,961 prefix** or **874,999,961 full-input updates**. Subjects run sequentially, including secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/guarded-loop-focused-v3/summary.json) passes six tests, including arbitrary seeds, wrong limits, zero/oversized widths, source overflow locations, negative proof cases, decoded/restored artifacts and finite-budget refill boundaries. The [full suite](../native-owner-dispatch-v1/guarded-loop-native-v1/summary.json) passes **307 GPU native tests and one catalog test**, with three existing manual exclusions. The retained [first](../native-owner-dispatch-v1/guarded-loop-focused-v1/summary.json) and [diagnostic](../native-owner-dispatch-v1/guarded-loop-focused-v2/summary.json) failures identify an underfunded expected-success fixture: both implementations reach the same ComparisonWork denial at the unchanged default 65,536 limit with equal errors, origins, work and helper frontiers. Those original denial cases remain; separate explicitly finite test budgets add successful full-loan/refill cases. No production allowance changes.

The [profiling build](profile-guarded-loop-build-v1/summary.json) matches the timed executable's entire **4,132,772-byte** machine-code section, SHA-256 `9ad93a11d8af21a8cfd55b2aadb35da81d14e874726ab13ec0949adb64f9b6f2`. The [full-input capture](full-profile-guarded-loop-v1/summary.json) observes seven workers and 6,480 worker samples: **81.27%** have generated program code as their innermost recorded frame. Inclusive shares are **2.41%** for publication, **6.00%** for library work debits and **8.52%** for waiting. The [prefix capture](prefix-profile-guarded-loop-v1/summary.json) observes two remaining workers and 530 samples: publication appears in **23.40%**, work debits in **28.49%**, and waiting in **38.30%**; none end in generated code. Both executions verify actual guarded selection, complete output and every update. [Offline disassembly](guarded-loop-codegen-audit-v1/results.json) retains the exact entry for further loop-state and register-allocation analysis.

Categories overlap and include waits, partial unwinds and profiling overhead; they are not wall-time shares or matched baseline profiles. The prefix capture covers the tail rather than earlier counting. Remaining targets are generated-loop state/check overhead for the full input and complete packed-map retention for private read-only uses, especially the prefix tail. Packed-map retention, separate decoded-source executable qualification, secured/trusted comparison and Rust parity remain unqualified at this stage.

## Narrow helper synchronization

Compiler [`f2bb3c924`](https://github.com/mech-lang/mech/commit/f2bb3c924051524b09c213404dea6a6a63184e47) synchronizes only the private Frame words each checked storage helper reads or changes. The generated refill template stores two words and reloads three; insertion stores six and reloads nine, versus fourteen stores and fourteen reloads previously. Cap-error helpers store two words and reload none. Terminal/error spills, unknown operations and memory-mode fallback retain complete synchronization. IR47 identifies the change; ABI24, work policy64, source, bytecode and finite launch policies remain unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.552 | 1.00× |
| Previous folded-hash stage, `c871644b0` | 1.968 | 3.57× |
| Narrow helper synchronization, `f2bb3c924` | 1.998 | 3.62× |

The candidate median is **1.5% slower**. Candidate observations are 1.998, 2.052 and 1.940 seconds; parent observations are 2.013, 1.968 and 1.959 seconds. Their ranges overlap, so these cohorts establish **no runtime gain**. [Full cohort receipts](full-frame-effects-cohort-v1/results.json) retain every observation, order and standard deviation.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, also regresses:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0130 | 1.0× |
| Previous folded-hash stage | 0.507 | 39.2× |
| Narrow helper synchronization | 0.529 | 40.8× |

Its median is **4.3% slower**, with candidate observations at 0.528–0.538 seconds and parent observations at 0.499–0.509 seconds. [Prefix receipts](frame-effects-timing-v1/results.json) retain all measurements, including the wider Rust spread: 0.0115, 0.0130 and 0.0208 seconds. No cause is assigned to the regression from these observations alone.

[Actual-emission metadata](frame-effects-timing-v1/emission-audit.json) verifies the exact store/reload word sets for all eight emitted helper operations in each of the two compiled packed-map regions, with object, descriptor and linked-manifest hashes. These are **compiler-emitted template counts**, not measured dynamic call frequencies or post-register-allocation machine-instruction savings. Both regions retain the source-state and scalar proofs. Runtime receipts independently verify seven packed SSA instances, one batch of seven tasks, an observed peak of seven workers, complete output and all **6,999,961 prefix** or **874,999,961 full-input updates**. Subjects run sequentially and include secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/frame-effects-focused-v1/summary.json) passes **two tests** comparing enabled and disabled synchronization across changed inputs, narrow/wide keys, growth, refills, arithmetic failures and exact source work before publication. The [full validation](../native-owner-dispatch-v1/frame-effects-native-v1/summary.json) passes **301 GPU native tests and one standard-library catalog test**, with three existing manual exclusions. Coverage includes exact emitted masks, unknown-operation fallback, unchanged terminal/error spills and original failure locations. Both runs have clean, unchanged before/after source snapshots.

The [profiling build](profile-frame-effects-build-v1/summary.json) matches the timed executable's entire **4,129,412-byte** machine-code section, SHA-256 `656d619fbf2dc8dab4c30ceaf5e657959aa9cb8e0815ced705c0a207bb0f2016`. The [full-input capture](full-profile-frame-effects-v1/summary.json) observes seven workers and 7,163 worker samples: **83.39%** have generated program code as their innermost recorded frame. Inclusive shares are **2.12%** for publication, **4.97%** for library work debits and **7.08%** for waiting. The [prefix capture](prefix-profile-frame-effects-v1/summary.json) observes 649 samples from two remaining workers: **20.80%** include publication, **29.89%** include work debits and **37.44%** include waiting; none have generated program code as their innermost frame. Both ordinary and batched debit APIs are included.

Categories overlap and include waits, partial unwinds and profiling overhead; they are not wall-time shares or matched baseline profiles. The prefix capture covers its tail rather than the earlier counting phase. Guarded-loop normalization and private packed-map retention remain unmeasured at this stage, alongside separate decoded-source executable qualification, secured/trusted comparison and Rust parity.

## Folded unsigned-product hashing

Compiler [`c871644b0`](https://github.com/mech-lang/mech/commit/c871644b02586b52ffe60aef4a27ea81d0010a78) replaces the packed table's two dependent mixing multiplies with a folded unsigned 128-bit product: multiply the two key words after XOR with fixed constants, then XOR the product's upper and lower halves. The runtime and generated code use the same function. Full-key equality, collision handling, bounded probing, every table entry and all source updates remain. The constants are unchanged; the hash does not depend on benchmark names, query strings or measured input. IR46/ABI24 prevent pairing generated code with the previous runtime hash; work policy64, source, bytecode and finite launch policies remain unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.555 | 1.00× |
| Previous source-state stage, `d9cc2f6dc` | 2.018 | 3.64× |
| Folded hash, `c871644b0` | 1.975 | 3.56× |

The observed median speedup is **1.02×**, reducing elapsed time by **2.1%**. Candidate observations are 1.957, 1.975 and 2.029 seconds; parent observations are 1.978, 2.018 and 2.057 seconds. Each candidate is lower than its parent in the same cohort, but the ranges overlap. [Full cohort receipts](full-folded-hash-cohort-v1/results.json) retain all observations, order and standard deviations. This is a modest result from three cohorts, not a universal speedup or Rust parity.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, also improves in this run:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0192 | 1.0× |
| Previous source-state stage | 0.568 | 29.6× |
| Folded hash | 0.518 | 26.9× |

The median is **8.8% lower**. Candidate observations span 0.517–0.527 seconds, below the parent range of 0.545–0.577 seconds. [Prefix receipts](folded-hash-timing-v1/results.json) retain every observation. Neither protocol isolates the cause of the difference beyond this compiler-stage comparison.

[Offline code inspection](folded-hash-codegen-audit-v1/summary.json) finds twelve generated probe sites with an unsigned `mul`/`umulh`/XOR sequence; the parent object has no `umulh`. Each inspected 192-byte instruction window matches the exact timed executable. [Emission metadata](folded-hash-timing-v1/emission-audit.json) retains both source-state regions, each with 90 product nodes, three header versions, fourteen branch-specialization records over five original sites, four latch routes, nine distinct payload-guard substitutions and four arithmetic substitutions. Runtime receipts separately verify seven packed SSA instances, one batch of seven tasks, a peak of seven workers, exact output and all **6,999,961 prefix** or **874,999,961 full-input updates**. Subjects run sequentially, including secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/folded-hash-focused-v1/summary.json) compares the actual generated hash with the runtime on **17,689 pairs** spanning both unsigned key words. The [full validation](../native-owner-dispatch-v1/folded-hash-native-v1/summary.json) passes **296 GPU native tests and one standard-library catalog test**, with three existing manual exclusions. Coverage retains wrapped collisions, wide keys, growth, failure cleanup and finite resource limits. Clean before/after source snapshots identify the focused production revision and its subsequent test-only identity-expectation correction.

The [profiling build](profile-folded-hash-build-v1/summary.json) matches the timed executable's entire **4,133,468-byte** machine-code section, SHA-256 `3d305b20a55de5993cddea925bce9771a77aa02f34d9a79a8869af5408ddefa6`. The [full-input capture](full-profile-folded-hash-v1/summary.json) observes seven workers and 7,093 worker samples: **82.60%** have generated program code as their innermost recorded frame. Inclusive shares are **2.07%** for publication, **6.01%** for library work debits and **7.82%** for waiting. The [prefix capture](prefix-profile-folded-hash-v1/summary.json) observes 542 samples from two remaining workers: **24.72%** include publication, **31.55%** include work debits and **36.53%** include waiting; none have generated program code as their innermost frame. Both ordinary and batched debit APIs are included.

These categories overlap and include waits, partial unwinds and profiling overhead; they are not wall-time shares or matched baseline profiles. The prefix capture covers its tail, not the earlier counting phase. Further loop simplification, narrower helper synchronization and private packed-map retention remain unmeasured at this stage, alongside separate decoded-source executable qualification, secured/trusted comparison and Rust parity.

## Paths specialized by source state

Compiler [`d9cc2f6dc`](https://github.com/mech-lang/mech/commit/d9cc2f6dc6dbd43152fa75a5707310addf921876) carries proved enum state across loop latches and emits separate paths for known states. It specializes the original Mech control flow; unknown or invalid tags retain checked behavior. Each new traversal discards other transient facts, and original header visits, work charges, table updates and error locations remain. The source, bytecode and finite launch policies match the narrow-slot parent. IR45 identifies this code-generation change; ABI23 and work policy64 remain unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.559 | 1.00× |
| Previous narrow-slot stage, `ee2e5ed39` | 2.194 | 3.92× |
| Paths specialized by source state, `d9cc2f6dc` | 2.059 | 3.68× |

The observed median speedup is **1.07×**, reducing elapsed time by **6.1%**. Candidate observations are 1.985, 2.059 and 2.099 seconds, below all parent observations at 2.142, 2.194 and 2.225 seconds. [Full cohort receipts](full-tag-threading-cohort-v1/results.json) retain every observation, execution order, standard deviation and evidence hash. This establishes a gain in these cohorts, not Rust parity or a universal speedup.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, regresses:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.0× |
| Previous narrow-slot stage | 0.500 | 24.1× |
| Paths specialized by source state | 0.566 | 27.3× |

Its median is **13.2% slower**. Candidate observations span 0.547–0.570 seconds, above all parent observations at 0.498–0.523 seconds. [Prefix receipts](tag-threading-timing-v1/results.json) retain all observations; these measurements do not establish a prefix improvement or explain its regression.

[Actual-emission metadata](tag-threading-timing-v1/emission-audit.json) identifies two compiled regions, at headers 173 and 284. Each contains **90 specialized nodes over 67 source sites**, with three header versions. Its **14 folded-branch emission records** cover **five distinct original branch sites** across state versions; four known-state routes lead to its single original latch. These are emitted specializations, not fourteen branches removed from every runtime iteration. Each compiled region also retains nine distinct payload-guard substitutions and four proved arithmetic substitutions, the two-bit source alphabet proof and narrow slots. Object, descriptor and linked-manifest hashes pin the records to the timed executable.

Runtime receipts independently verify seven packed SSA instances, one batch of seven tasks, a peak of seven workers, exact outputs and all **6,999,961 prefix** or **874,999,961 full-input updates**. Subjects execute sequentially, including secured startup/shutdown and capability checks. The remaining gap to Rust is not attributed wholesale to those checks.

[Focused validation](../native-owner-dispatch-v1/tag-threading-focused-v1/summary.json) passes **eight tests**, and the [full native suite](../native-owner-dispatch-v1/tag-threading-native-v1/summary.json) passes **295 tests**, with three pre-existing manual exclusions. Coverage includes conservative unknown/invalid states, simultaneous carrier copies, latch fact reset, renamed and reordered variants, initial terminal states, original later-iteration error locations, exact source work before publication and actual-emission records. Clean, unchanged source snapshots bracket both runs.

The [profiling build](profile-tag-threading-build-v1/summary.json) preserves the timed executable's entire **4,133,580-byte** machine-code section, SHA-256 `49cb949d13095e582d73fac08846a31d4e47bd43f93a193e726f9f292758b9e7`. A [full-input capture](full-profile-tag-threading-v1/summary.json) observes seven workers and 7,110 worker samples: **83.07%** have generated program code as their innermost recorded frame. Inclusive shares are **2.14%** for publication, **5.34%** for library work debits and **7.40%** for waiting. Both ordinary and batched debit APIs are included.

The [prefix capture](prefix-profile-tag-threading-v1/summary.json) observes 634 samples from two remaining workers: **21.92%** include publication, **31.55%** include library work debits and **36.44%** include waiting; none have generated program code as their innermost frame. Both executions verify complete output and every update. Categories overlap and include waits, partial unwinds and profiling overhead; these are not wall-time shares or matched baseline profiles. The prefix capture covers the tail, not the earlier counting phase, and does not establish the cause of the 13.2% regression.

Hashing, further loop simplification and private packed-map retention remain separate optimization candidates. Separate decoded-source executable qualification, secured/trusted comparison and Rust parity also remain unfinished at this stage.

## Narrow table payloads

Compiler [`ee2e5ed39`](https://github.com/mech-lang/mech/commit/ee2e5ed39b2e39f65061fe01c6c18ec7f208ab08) stores a packed key and its **64-bit count in 16 bytes**, instead of a 24-byte payload with an unused high key word. The source-derived alphabet proof must fit every admitted width into one key word; other domains retain the wider layout. Hashing, full-key comparison, collision handling, count-overflow checks and complete map publication remain. IR44/work policy64/ABI23 identify the layout and accounting change; the Mech source and program bytecode are unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.554 | 1.00× |
| Previous scalar-proof stage, `b08ab3cda` | 2.221 | 4.01× |
| Narrow table payloads, `ee2e5ed39` | 2.229 | 4.03× |

The candidate median is **0.4% slower**, with overlapping ranges: 2.184–2.261 seconds versus 2.191–2.313 seconds. These cohorts establish **no runtime improvement**. [Full cohort receipts](full-narrow-slots-cohort-v1/results.json) retain all observations, execution orders and standard deviations.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, also regresses:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0205 | 1.0× |
| Previous scalar-proof stage | 0.507 | 24.7× |
| Narrow table payloads | 0.524 | 25.5× |

Its median is **3.3% slower**; candidate observations span 0.517–0.538 seconds, above all parent observations at 0.488–0.511 seconds. The [prefix receipts](narrow-slots-timing-v1/results.json) retain every observation. No cause is assigned to the regression from these timings alone.

The payload reduction is real: slot/control backing changes from **`25 × capacity + 7` to `17 × capacity + 7` bytes**. This is not a one-third reduction in whole-process memory. The [measured full-process RSS medians](full-narrow-slots-cohort-v1/summary.json) are **233.3 MB** for the candidate and **235.9 MB** for its parent, using decimal MB. Captured inputs, canonical publication, worker contexts and other allocations remain.

[Offline code inspection](narrow-slots-codegen-audit-v1/summary.json) verifies twelve generated SIMD probe windows using 16-byte bucket strides, plus SSA count loads/stores at offset eight; the parent's corresponding windows use 24-byte strides and offset sixteen. The instruction bytes match the exact linked timing executables. Both compiled regions retain the two-bit source alphabet proof and [nine omitted payload guards plus four proved arithmetic substitutions](narrow-slots-timing-v1/emission-audit.json). Runtime receipts separately verify seven packed SSA instances, one batch of seven tasks, a peak of seven workers, exact outputs and all **6,999,961 prefix** or **874,999,961 full-input updates**. Inputs and finite launch policies match the parent. Subjects run sequentially, including secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/narrow-slots-focused-v1/summary.json) passes eight tests, including one unrelated test matched by the broad filter. The [first full run](../native-owner-dispatch-v1/narrow-slots-native-v1/summary.json) passes 285 tests but fails two assertions still expecting ABI22. A test-only correction updates them to ABI23; the [repeated full suite](../native-owner-dispatch-v1/narrow-slots-native-v2/summary.json) passes **287 tests**, with three pre-existing manual exclusions. Before/after source-provenance sidecars pin each run to its clean, unchanged compiler revision; the original process receipts remain intact.

The [profiling build](profile-narrow-slots-build-v1/summary.json) preserves the timed executable's entire **4,132,912-byte** machine-code section, SHA-256 `be0e0c52b5ed47b1d3178559d2152bf4341e128cab35f8afb388e9592f682339`. A [full-input capture](full-profile-narrow-slots-v1/summary.json) observes seven workers and 8,123 worker samples: **85.20%** have generated program code as their innermost recorded frame. Inclusive shares are **1.83%** for publication, **5.38%** for library work debits and **6.59%** for waiting. Both ordinary and batched debit APIs are included.

The [prefix capture](prefix-profile-narrow-slots-v1/summary.json) observes 652 samples from two remaining workers: **21.32%** include publication, **30.21%** include library work debits and **35.58%** include waiting; none have generated program code as their innermost frame. Both profile executions verify complete output and every update. Categories overlap and include waits, partial unwinds and profiling overhead; these are not wall-time shares or matched baseline profiles. The prefix capture covers the tail rather than the earlier counting phase and does not establish the cause of the 3.3% regression.

Further loop simplification and private packed-map retention remain unmeasured in this stage, alongside separate decoded-source executable qualification, secured/trusted comparison and Rust parity.

## Current-traversal scalar proofs

Compiler [`b08ab3cda`](https://github.com/mech-lang/mech/commit/b08ab3cdae723fa760ba7d0000db920977de7c0d) uses preceding source control flow to prove enum payload access and unsigned index arithmetic within the current loop traversal. Proven checks are omitted from the generated packed SSA loop; unknown facts, invalid enum alternatives, changed aliases and unsupported arithmetic retain the checked path. String bounds and count-increment overflow checks remain. Source operations, every table update and finite work accounting are preserved. IR43 identifies the generated-code change; work policy63 and ABI22 remain unchanged.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.552 | 1.00× |
| Previous publication-debit stage, `5e92487ad` | 2.685 | 4.86× |
| Current-traversal scalar proofs, `b08ab3cda` | 2.222 | 4.02× |

The observed median speedup is **1.21×**, reducing elapsed time by **17.2%**. Candidate samples are 2.222, 2.204 and 2.229 seconds; parent samples are 2.685, 2.570 and 2.693 seconds. All three candidate observations are below all three parent observations. [Full cohort receipts](full-source-edge-facts-cohort-v1/results.json) retain samples, standard deviations, execution orders and evidence hashes. This establishes a gain in these cohorts, not Rust parity or a universal speedup.

The **one-million-base prefix** regresses, with three alternating observations and one excluded warmup per executable:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0224 | 1.0× |
| Previous publication-debit stage | 0.477 | 21.3× |
| Current-traversal scalar proofs | 0.508 | 22.6× |

Its median is **6.4% slower**. Candidate observations span 0.494–0.523 seconds; parent observations span 0.464–0.485 seconds. The [prefix receipts](source-edge-facts-timing-v1/results.json) retain all observations; this stage does not establish a prefix improvement.

[Actual-emission records](source-edge-facts-timing-v1/emission-audit.json) identify **nine omitted payload guards and four proved arithmetic substitutions in each of two compiled source regions**, at headers 173 and 284. Every record is checked against its exact source site, aggregate guard offset/ordinal or scalar operation/operands. These are two compiled bodies used by seven runtime tasks, not seven separately compiled bodies. Object, descriptor and linked-manifest hashes pin the records to the measured executable; runtime receipts separately verify seven packed SSA instances, a peak of seven workers, complete outputs and all **6,999,961 prefix** or **874,999,961 full-input updates**. Source, bytecode, inputs and finite launch policies match the parent. Subjects execute sequentially, including secured startup/shutdown and capability checks.

[Focused validation](../native-owner-dispatch-v1/edge-facts-focused-v2/summary.json) passes seven tests, and the [full native suite](../native-owner-dispatch-v1/edge-facts-native-v1/summary.json) passes **281 tests**, with three pre-existing manual exclusions. The [first focused run](../native-owner-dispatch-v1/edge-facts-focused-v1/summary.json) failed an equality assertion because independently seeded map-publication orders changed heapsort work by 32 compute units. The corrected test checks exact source work and remaining fuel before publication for all cases; empty/one-key results and source failures also retain exact end-to-end work equality. Complete outputs, update counts and original error locations remain checked. No production debit or limit was relaxed, and no observed difference was subtracted.

The [profiling build](profile-source-edge-facts-build-v1/summary.json) preserves the timed executable's entire **4,131,568-byte** machine-code section, SHA-256 `65d23784cb2c63c9ac33dc7dc81ae4c73c0f0e3e1f8d441dd02721797a82735b`. A [completed full-input capture](full-profile-source-edge-facts-v1/summary.json) observes seven workers and 8,206 worker samples: **86.64%** have generated program code as their innermost recorded frame. Inclusive shares are **1.49%** for publication, **4.42%** for library work debits and **5.41%** for waiting. Both ordinary and batched debit APIs are included.

The [prefix capture](prefix-profile-source-edge-facts-v1/summary.json) observes 526 samples from two remaining workers: **21.86%** include publication, **27.38%** include library work debits and **37.45%** include waiting; none have generated program code as their innermost frame. Both profiling executions verify complete output and every update. The prefix capture does not cover the earlier counting phase or establish the cause of the 6.4% elapsed-time regression. Categories overlap and include waits, partial unwinds and profiling overhead; these are not wall-time shares, independent benchmark observations or matched baseline profiles.

Narrower table slots and private packed-map retention remain unmeasured in this stage, alongside separate decoded-source executable qualification, secured/trusted comparison and Rust parity.

## Bounded publication debit batches

Compiler [`5e92487ad`](https://github.com/mech-lang/mech/commit/5e92487ad02e776baa7ed938154ad206b8325518) reuses the shared worker-account lock across bounded groups of publication-sort debits. Every original debit is still checked and committed individually; no allowance is reserved or renewed. The lock is released after at most 32 charges or 32,768 charged work units, and on denial or unwind. Sorting, complete map publication and source operations remain unchanged. The generated program object, descriptor and bytecode are byte-identical to the SIMD parent; IR42/work policy63/ABI22 remain valid.

Three **125-million-base** cohorts rotate execution order and retain all observations, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.585 | 1.00× |
| Previous SIMD stage, `d760b334f` | 2.986 | 5.10× |
| Publication debit batches, `5e92487ad` | 2.690 | 4.59× |

The observed median speedup is **1.11×**, reducing elapsed time by **9.9%**. Candidate samples are 2.732, 2.690 and 2.579 seconds; parent samples are 3.004, 2.949 and 2.986 seconds. Rust varies from 0.552 to 0.753 seconds; all three Rust observations, including 0.585 seconds, are retained. Ratios use the median Rust observation from this same cohort. [Full cohort receipts](full-publication-batches-cohort-v1/results.json) retain all samples, standard deviations and orders.

The **one-million-base prefix**, with three alternating observations and one excluded warmup per executable, improves more:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.0× |
| Previous SIMD stage | 0.818 | 39.4× |
| Publication debit batches | 0.471 | 22.7× |

The prefix median falls **42.4%**, a **1.74× speedup**. Candidate observations span 0.459–0.496 seconds; parent observations span 0.808–0.837 seconds. [Prefix receipts](publication-batches-timing-v1/results.json) retain every observation. This improvement does not establish parity with Rust or eliminate the earlier regression relative to the historical serial stage.

Every candidate run verifies exact output, all seven tables and packed SSA regions, seven actual concurrent workers, and **6,999,961 prefix** or **874,999,961 full-input updates**. Source, inputs and finite launch policies match the parent. Subjects run serially, including secured startup/shutdown and capability checks. [Native validation](../native-owner-dispatch-v1/publication-debit-native-v1/summary.json) passes **273 tests**, with three pre-existing manual exclusions. [Resource validation](../native-owner-dispatch-v1/publication-debit-resources-v1/provenance.json) passes **43 checks**, including exact local/call/shared denials, concurrent batches, lock-release bounds, unwind behavior and publication order/work preservation.

The [profiling build](profile-publication-batches-build-v1/summary.json) preserves the timed executable's entire **4,132,524-byte** machine-code section, SHA-256 `035b11e0203ee3bd08f97366a77433aa154e4ca8987e700b3daaf3e63a54f4e0`. The [full capture](full-profile-publication-batches-v1/summary.json) observes seven workers and 9,999 worker samples: **88.59%** have generated program code as their innermost recorded frame. Inclusive shares are **1.23%** for publication, **3.62%** for library debits and **4.67%** for waiting. The debit category includes the new batched meter as well as the existing API; omitting its new symbol would undercount debit observations.

A [prefix capture](prefix-profile-publication-batches-v1/summary.json) records 535 observations across two remaining workers: **22.06%** include publication, **28.41%** include library debits and **39.63%** include waiting, with no generated-entry innermost observations. The [innermost-function inventory](prefix-profile-publication-batches-v1/innermost-functions.json) also identifies memory-budget evaluation and planning. Their caller stacks include the original guarded map lookup and canonical footprint measurement after histogram publication. Retaining packed maps through private reads or reusing proved footprint metadata are possible targets; neither is measured in this stage. All profile executions verify complete outputs and updates. Categories overlap and include waiting, partial unwinds and profiling overhead; these percentages are not wall-time shares or directly recoverable speedups.

At this stage, the full-input profile still places most observed worker frames in generated counting code. Current-traversal loop proofs are measured in the subsequent stage above. Narrower slots, representation retention, decoded-source executable qualification, secured/trusted comparison and Rust parity remained separate work.

## SIMD hash-table controls

Compiler [`d760b334f`](https://github.com/mech-lang/mech/commit/d760b334f148d2b7fb05abea64f874613e56e38e) compares eight hash-control bytes together, then checks each matching full key. A separate control array replaces the occupancy word, reducing table slots from 32 to 24 bytes. Bounded probing, collision checks, insertion/growth, source errors and shared finite accounting remain. The unchanged program still computes all seven histograms. IR42/work policy63/ABI22 identify this stage.

Three **125-million-base** cohorts rotate execution order, retain every complete-process observation and exclude no warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.552 | 1.00× |
| Previous compact-key stage, `100f2ec89` | 3.292 | 5.96× |
| SIMD hash-table controls, `d760b334f` | 2.913 | 5.28× |

The observed median speedup is **1.13×**, reducing elapsed time by **11.5%**. Candidate samples are 2.913, 2.919 and 2.828 seconds; parent samples are 3.397, 3.292 and 3.151 seconds. All three candidate observations are below all three parent observations. The [cohort results](full-parallel-simd-cohort-v1/results.json) include all samples, standard deviations, orders and receipt hashes. This establishes a gain in these cohorts, not Rust parity or a universal speedup.

The [one-million-base prefix](parallel-simd-timing-v1/results.json), with three alternating complete-process observations and one excluded warmup per executable, gives Rust **0.0209 s (1.0×)**, parent **0.832 s (39.9×)** and candidate **0.808 s (38.8×)**. The candidate median is 2.9% lower, but its 0.779–0.840-second range overlaps the parent's 0.792–0.833-second range. This does not resolve the earlier prefix regression relative to serial execution.

Every candidate execution verifies exact output, seven packed SSA regions, one batch containing two source regions and seven tasks, a peak of seven concurrent workers, and all **6,999,961 prefix** or **874,999,961 full-input updates**. Two-bit source-derived key proofs remain selected. Source, program bytecode, inputs and finite launch policies match the parent; secured startup/shutdown and capability checks are included. Subjects run sequentially under the common lock. [Validation](../native-owner-dispatch-v1/parallel-simd-validation-v1/summary.json) passes **272 native tests**, with three pre-existing manual exclusions, including wrapped collisions, full-key verification, growth, exact/one-short shared limits, compact encoding, seven-worker composition and failure cleanup.

[Offline inspection](simd-codegen-audit-v1/summary.json) finds twelve ARM64 `cmeq.8b` control-group comparisons in the generated program entry, versus none in the compact parent, and matches their instruction windows into the exact timed executable. Mech already vectorizes the source map/join input normalization in 16-byte batches; this is distinct from the new hash-control SIMD. The [remaining Rust differences](simd-codegen-audit-v1/remaining-rust-differences.txt) include smaller entries/counts, different hashing, fewer steady-loop checks and avoiding Mech's canonical String-map publication. Their individual timing contributions have not been isolated.

The [profiling build](profile-parallel-simd-build-v1/summary.json) has identical entire machine code to the timed executable: **4,128,804 bytes**, SHA-256 `4cd933ef7feaf470dda12f89fc612bf2a00deb92797d1949a604f482e57070e4`. A [completed full-input capture](full-profile-parallel-simd-v1/summary.json) observes seven workers and 10,313 worker samples: **84.42%** have generated program code as their innermost recorded frame. Inclusive shares are **4.94%** for map publication, **8.09%** for library work debits and **6.51%** for waiting. A [prefix capture](prefix-profile-parallel-simd-v1/summary.json) observes 1,121 samples from two remaining workers after the other five finish: **56.29%** include publication, **54.59%** include library debits and **41.30%** include waiting; none have generated program code as their innermost frame. Both executions verify complete output and all updates. These overlapping categories include waits, partial unwinds and profiling overhead; they are not wall-time shares or matched baseline profiles. The prefix capture supports publication/shared-budget contention in the tail, without attributing the entire regression.

[Mapping the retained worker offsets](simd-loop-profile-audit-v1/summary.json) identifies count stores, window bounds/overflow checks, SIMD match extraction and a fuel/refill guard in the generated loop. The sampler merges and truncates instruction offsets within each symbol node, so its counts cannot rank these individual operations or measure their separate costs.

Publication/debit improvements were a subsequent stage, measured above. Additional loop simplification, narrower storage, separate decoded-source executable qualification, secured/trusted comparison and Rust parity remained unfinished at this stage.

## Source-derived character encoding

Compiler [`100f2ec89`](https://github.com/mech-lang/mech/commit/100f2ec894424b7b54f5e4c602e5a9aeb2916cdb) derives finite character alphabets from immutable source maps, copies and joins. When a shift-and-mask encoding is injective for that alphabet, generated loops pack each character into fewer bits and decode every retained key during canonical publication. Unknown or unsupported producers retain the full ASCII representation. This is a source proof, not a scan for nucleotide data. The unchanged program selects two-bit keys in all seven workers; cold failure origins remain active. IR41/work policy62/ABI21 identify the stage.

Three **125-million-base** cohorts rotate execution order and retain every complete-process observation, with no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.551 | 1.00× |
| Previous cold-origin stage, `8afcd192c` | 3.393 | 6.15× |
| Source-derived character encoding, `100f2ec89` | 3.234 | 5.87× |

The observed median speedup is **1.05×**, a **4.7%** reduction in elapsed time. Candidate samples are 3.340, 3.234 and 3.214 seconds; parent samples are 3.393, 3.617 and 3.298 seconds. Their ranges overlap. This is a modest gain in three cohorts, not evidence of a large or universal improvement. The [cohort results](full-parallel-compact-cohort-v1/results.json) retain all samples, standard deviations, execution orders and receipt hashes.

The **one-million-base prefix** has three alternating complete-process measurements per executable, with one excluded warmup each:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0209 | 1.0× |
| Previous cold-origin stage | 0.781 | 37.3× |
| Source-derived character encoding | 0.824 | 39.3× |

Its candidate median is **5.4% slower**, with overlapping ranges: 0.795–0.855 seconds versus 0.752–0.808 seconds for the parent. [Prefix receipts](parallel-compact-timing-v1/results.json) retain all nine timed processes. These measurements do not establish a prefix improvement or resolve the earlier slowdown relative to serial execution.

Qualification records both selected map-region proofs: **two bits per character, shift one**, with a lossless alphabet mapping and no ASCII fallback. Every candidate run verifies exact output, seven actual packed SSA regions, one batch of seven tasks, a peak of seven concurrent workers and all **6,999,961 prefix** or **874,999,961 full-input updates**. Source, program bytecode, inputs and finite launch policies match the parent. Secured startup, shutdown, capability checks and shared resource accounting remain included; subjects run sequentially under the common lock.

[Validation](../native-owner-dispatch-v1/parallel-compact-validation-v1/summary.json) passes **268 native tests**, with three pre-existing manual exclusions. Coverage includes original and decoded programs, restored descriptors, non-nucleotide alphabets, unused codes, word-boundary widths, fallback, complete map publication, seven-worker composition and shared cleanup. Earlier profiles concern earlier executables; no profile of this compact candidate is claimed here. SIMD probing was a subsequent stage, measured above. Publication/budget contention, separate decoded-source executable qualification, secured/trusted comparison and Rust parity remained unfinished at this stage.

## Cold failure origins

Compiler [`8afcd192c`](https://github.com/mech-lang/mech/commit/8afcd192c708f450136d939769ca8b7c4edbfaf7) moves error-location writes from successful packed SSA blocks to their failing edges. Source arithmetic, branches, bounds, map operations, work charges and rejection behavior are unchanged. Each failure still reports its original source location. Seven-worker execution and IR40/work policy61/ABI21 remain in use.

Three full **125-million-base** cohorts rotate the order of the candidate, previous seven-worker executable and upstream Rust. Every observation is retained, with fresh complete processes and no excluded warmup:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.566 | 1.0× |
| Previous seven-worker stage, `a99910795` | 4.540 | 8.0× |
| Cold failure origins, `8afcd192c` | 3.391 | 6.0× |

The measured median speedup is **1.34×**, reducing elapsed time by **25.3%**. Candidate samples are 3.391, 3.503 and 3.387 seconds; the parent samples are 4.540, 4.550 and 4.368 seconds. Rust samples are 1.291, 0.546 and 0.566 seconds. Its unusually slow first run is retained, which is why the median cohort ratio is more informative than the first single-run ratio. [Cohort summary](full-cold-origin-cohort-v1/results.json) includes all raw samples, standard deviations, execution orders and receipt hashes.

Every full execution verifies exact output, all **874,999,961 updates**, seven packed SSA maps and a peak of seven concurrent workers. Program source, bytecode, input and finite launch policy match the parent. Capability checks and secured startup/shutdown remain included; subjects run sequentially under the common lock.

The [one-million-base prefix](cold-origin-timing-v1/results.json) has three alternating complete-process medians: Rust **0.0207 s (1.0×)**, previous parallel **0.815 s (39.5×)** and candidate **0.764 s (37.0×)**. Samples overlap, and this modest change does not resolve the earlier regression relative to serial execution. One warmup per executable is excluded only in this prefix protocol.

All 255 existing native tests passed with the compiler change. The new failure-origin fixture initially contained a misplaced source terminator in its direct-lookup case; after that fixture was corrected, its focused test passed for original, decoded and restored execution, including arithmetic, rejection, selection, missing-key, malformed-helper and finite-budget failures with cleanup. [Initial validation](../native-owner-dispatch-v1/cold-origin-validation-v1/summary.json) and [corrected fixture validation](../native-owner-dispatch-v1/cold-origin-validation-v2/summary.json) preserve that distinction. The preceding stage's exact-code profiles motivated the change; they are not profiles of this new executable.

At the cold-origin stage, compact source-derived key domains and SIMD probing were subsequent stages; their measurements now appear above. Reducing measured publication/budget contention, Rust parity and secured/trusted comparison remained unfinished at this stage.

## Parallel source comprehensions

Compiler [`a99910795`](https://github.com/mech-lang/mech/commit/a999107959d91428e25ea5a55f6db41ece79ff12) executes independent pure comprehension elements in scoped native workers. A source-derived dependency proof groups the two frequency tasks and five query tasks into one batch. Each worker executes the original generated Mech body with its own mutable state; results return through the original ordered publication points. All seven histograms and every source update remain. The source and program bytecode are unchanged. IR40/work policy61/ABI21 identify this stage.

This stage's **125-million-base** cohort measures one complete process per executable:

| Executable | Seconds, one run | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.553 | 1.00× |
| Serial native register loops, `35da7a27e` | 14.019 | 25.35× |
| Parallel source comprehensions, `a99910795` | 4.446 | 8.04× |

The parallel stage shows a **3.15× speedup** over the serial compiler stage, reducing elapsed time by **68.3%** in this cohort. These are single full-input executions, with no excluded warmup; they are not repeated medians or evidence of a sevenfold speedup. Executables run sequentially, with secured Mech startup, shutdown and capability checks included. The finite launch policy matches the preceding full-input SSA qualification. [Full receipts](full-parallel-v2/results.json) retain all exact seconds, executable identities and process records.

On the **one-million-base prefix**, three alternating complete-process measurements per executable give a different result:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.0× |
| Serial native register loops, `35da7a27e` | 0.358 | 17.2× |
| Parallel source comprehensions, `a99910795` | 0.794 | 38.1× |

The prefix median is **2.22× slower** than the serial stage. The profile below identifies publication and shared-budget contention in its tail, but their contribution to the complete regression has not been isolated. The [prefix receipts](parallel-timing-v2/results.json) include all nine timed processes and one excluded warmup per executable. Ratios in each table use Rust from that same cohort; the prefix ratio is not the full-input ratio.

Every candidate execution reports **one batch, two source comprehension regions, seven tasks and seven observed concurrent workers**, plus seven actual packed SSA regions. Outputs match the independent reference, with **6,999,961 updates** on the prefix and **874,999,961 updates** on the full input. Worker entry adds original setup visits: 478 native visits versus the serial baseline's 443. Finite work and memory admission remain shared across the invocation.

The corrected parallel implementation passed [255 native checks](../native-owner-dispatch-v1/parallel-native-validation-v3/summary.json), with three pre-existing manual exclusions, and [worker-resource checks](../native-owner-dispatch-v1/worker-resource-validation-v2/summary.json). Follow-up validation covers [variable-width String queries and guarded lookup](../native-owner-dispatch-v1/parallel-query-validation-v1/summary.json) and [13 finite-budget checks](../native-owner-dispatch-v1/incremental-budget-validation-v1/summary.json). The initial executable failed uncached map access before timing; the corrected finalization uses the active finite call allowance. The [failed warmup](parallel-timing-v1/summary.json) and [three diagnostic reproductions](parallel-runtime-diagnostic-v1/summary.json) remain recorded and supply no valid timing samples.

The [profiling build](profile-parallel-build-v2/results.json) preserves the timed executable's entire machine-code section: 4,104,724 bytes, SHA-256 `989a7d1ca5511a12f3e7cd3c349fea6f67abb0d308ec78096bdabcf51746c377`. One [all-thread capture during a completed full-input execution](full-profile-parallel-v3/analysis.json) observes seven workers and verifies the full output and all updates. Of the observed worker-thread samples, **92.65%** have the generated program as their innermost recorded frame. Inclusive sample shares are **3.37%** for library work debits, **2.71%** for waiting and **2.08%** for canonical map publication.

A [prefix capture of the same executable](prefix-profile-parallel-v1/summary.json) records **1,067 samples across two remaining workers**, after the other five have finished; the completed execution still verifies seven concurrent workers, exact output and all 6,999,961 updates. In this sampled tail, **61.95%** of worker observations include map publication, **58.86%** include library work debits and **41.33%** include waiting. No observation has the generated entry as its innermost recorded frame. This supports publication and shared-budget contention as optimization targets for the prefix tail. It does not measure the initial computation, isolate the complete 2.22× regression or establish how much elapsed time any one change would recover.

These profile categories overlap. The observations include waits, partial unwinds and profiling overhead; their percentages are neither CPU utilization nor wall-time shares, and thread totals cannot be added as elapsed time. An [earlier profiling attempt](full-profile-parallel-v2/summary.json) failed when the sandbox denied process inventory, captured no stacks and cleaned up its owned processes; it supplies no profiling or timing evidence.

At this stage, repeated full-input cohorts, moving error-origin stores off the hot loop, compact character encoding and SIMD table controls were unfinished; subsequent stages above measure them. Isolation and correction of the prefix regression, separate decoded-source executable qualification, secured/trusted comparison and Rust parity remained unfinished. Historical sections retain the results and limitations of their respective compiler stages.

## Native register loops

Compiler [`35da7a27e`](https://github.com/mech-lang/mech/commit/35da7a27ea0f0543ce531544359c1da5c4d12f5a) versions proved closed map loops into native SSA control flow. Source scalar and aggregate values and mutable table state stay in registers between runtime boundaries. Every original branch, checked arithmetic operation, rejection arm and map update remains. Growth, finite fuel refill and failure boundaries synchronize the owned frame. IR38/work policy59/ABI20 identify this stage. The Mech source and program bytecode are unchanged.

Three alternating complete-process measurements on **one million bases** give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0206 | 1.0× |
| Previous generated table operations, `17938cecd` | 0.451 | 21.9× |
| Native register loops, `35da7a27e` | 0.361 | 17.5× |

Elapsed time falls **20.0%**, a **1.25× speedup**. All outputs match the independent reference. Every candidate execution reports seven actual SSA regions and all 6,999,961 source updates; a silent fallback fails qualification. Both Mech executables retain 443 admissions. [Prefix receipts](packed-ssa-timing-v1/results.json) include every fresh process and one excluded warmup per executable, all run serially.

A fresh full-input cohort uses one complete process per executable on **125 million bases**:

| Executable | Seconds, one run | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.567 | 1.0× |
| Previous generated table operations, `17938cecd` | 27.761 | 49.0× |
| Native register loops, `35da7a27e` | 15.005 | 26.5× |

This single full-input cohort shows a **1.85× speedup**, with elapsed time down **46.0%**. These are single complete processes, not repeated medians; no warmup is excluded. All full outputs match, and the candidate completes seven actual SSA regions and **874,999,961 updates**. Peak RSS is 227.1 MB versus 226.8 MB for the parent. [Full receipts](full-packed-ssa-v1/results.json) retain unchanged executable/input identities and the same finite secured execution policy as the preceding qualification. Startup, shutdown, capability grants and resource checks remain included. The canonical benchmark dataset is unchanged.

[Validation](../native-owner-dispatch-v1/packed-ssa-validation-v5/summary.json) passes **238 native checks**, with three pre-existing manual exclusions. Tests cover original, decoded and restored-descriptor execution, non-DNA inputs, complete maps, caller-produced replacement values, branch joins, multiple growth and refill boundaries, actual path selection, finite limits, fallback and cleanup. Earlier receipts retain compile visibility, source rejection-arm and stale identity-test failures; an interrupted run is excluded from passing evidence.

The [profile build](profile-packed-ssa-build-v1/results.json) has byte-identical complete machine code to the timed executable: 4,010,920 bytes, SHA-256 `86a971df855b19c6699929bf60400f8973803c15dc32f00106c7b18505f1c47f`. Three two-second captures across a completed full execution put 100% of main-thread samples beneath the generated entry; closed-map storage callbacks occupy 0.13–1.02%, and the last capture includes 2.81% canonical map publication. These inclusive categories overlap and do not precisely attribute total runtime. [Profile analysis](full-profile-packed-ssa-v1/analysis.json) verifies exact output and all updates; profiling times are excluded from benchmarks.

At the register-loop stage, source-derived finite character encoding, SIMD table controls and independent-comprehension parallel execution were separate unfinished stages. Their performance is not included in this historical cohort; the later parallel results appear above. Rust parity, repeated full-input cohorts, a separate decoded-source executable qualification and secured/trusted comparison remain unfinished.

## Generated compact-key table operations

Compiler [`17938cecd`](https://github.com/mech-lang/mech/commit/17938cecd500bc5a570f3ac15daf3a64d62ad02d) compiles fixed-width ASCII key packing, hashing, table probing, reads and existing-entry updates directly into the native source loop. Source branches, arithmetic and values are unchanged. Distinct-key insertion, growth, finite batch refill and complete canonical publication remain runtime operations. The representation applies to arbitrary ASCII keys of up to 18 characters, without recognizing nucleotide data or requested queries. IR37/work policy58/ABI20 identify the stage; its [design and validation](../native-owner-dispatch-v1/README.md#generated-compact-key-table-operations) describe the proof and budget boundaries.

Three alternating complete-process measurements on **one million bases** give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.0× |
| Previous Mech AOT, `e4d3ed4da` | 1.147 | 55.2× |
| Generated table operations, `17938cecd` | 0.451 | 21.7× |

The measured prefix speedup is **2.54×**. All nine outputs match the independent reference. Every candidate run reports seven actual packed regions and all 6,999,961 source updates; this rules out silent fallback. Both Mech binaries retain 443 admissions. The source and program bytecode are identical. [Raw prefix receipts](packed-timing-v1/results.json) include fresh secured startup/shutdown and one excluded warmup per executable; all subjects run serially.

A fresh full-input cohort uses one complete process per executable on **125 million bases**:

| Executable | Seconds, one run | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.564 | 1.0× |
| Previous Mech AOT, `e4d3ed4da` | 117.186 | 207.8× |
| Generated table operations, `17938cecd` | 27.491 | 48.7× |

The observed full-input speedup is **4.26×**. These are single complete processes, not repeated medians, with no excluded warmup. All outputs match the full independent reference, and the candidate reports seven actual packed regions and **874,999,961 updates**. Peak RSS is 226.9 MB versus 220.3 MB for the previous Mech binary. The [full receipts](full-packed-v1/results.json) retain the identical finite policy used by the prior successful full qualifications. Capability grants and all resource accounting remain active; the canonical benchmark dataset is unchanged.

[Validation](../native-owner-dispatch-v1/packed-map-validation-v3/summary.json) passes **237 native checks**, with three pre-existing exclusions. The [profiling executable](profile-packed-build-v1/results.json) has exactly the same complete machine code as the timed binary: 4,000,248 bytes, SHA-256 `977eda9f056eb0114291d839b02488595a06b42f131b75f11c708d7a9a18d461`. Three two-second captures across a completed full-input execution place **99.9–100%** of main-thread samples beneath the generated entry, with the former closed-map callback category at **0–0.13%**. Categories are inclusive; this is sample evidence, not a precise attribution of total runtime. [Profile analysis](full-profile-packed-v1/analysis.json) verifies exact code identity, complete output and every source update; profiling elapsed time is excluded from timings.

[Inspection of the exact Rust executable](rust-codegen-audit-v1/findings.txt) confirms rolling two-bit integer keys, inlined hashing/updates, SIMD hash-control probing, SIMD input encoding and seven task submissions. The common first-candidate existing-key path has 34 instructions counted statically, not measured cycles. This Mech stage remained serial and used two-word ASCII keys. General native-loop SSA improvements, compact domains/SIMD probing, and independent-comprehension parallelism were its next implementation targets; those changes are absent from this historical cohort. Rust parity, repeated full-input cohorts, separate decoded-source executable qualification and secured/trusted comparison remain unfinished.

## Same-key lookup reuse

Compiler [`e4d3ed4da`](https://github.com/mech-lang/mech/commit/e4d3ed4da3aec10a70dfb17d58442bafa78d3ec3) retains the last lookup result for an immutable pinned key inside a closed map loop. Reuse requires the same table token, mutation version, key address and key length. Every mutation invalidates the observation; each cache hit still pays the complete original lookup debit under the same call and root limits. The generated caller still computes every inserted value. IR36/work policy56/ABI20 identify this stage.

Three alternating complete-process measurements on the **one-million-base** prefix give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0209 | 1.0× |
| Previous Mech AOT, `cb9d6913c` | 1.154 | 55.2× |
| Lookup reuse, `e4d3ed4da` | 1.151 | 55.1× |

The observed reduction is only **0.3%**, with overlapping samples; this does not establish a material speedup. All nine outputs match the independent reference, with seven tables and 6,999,961 updates for each Mech execution. Both retain 443 admissions. Source and program bytecode are unchanged. [Raw prefix measurements](lookup-timing-v1/results.json) include three fresh processes per executable and one excluded warmup, executed serially with secured startup/shutdown included.

A fresh full-input comparison uses one complete process per executable on **125 million bases**, with no excluded warmup:

| Executable | Seconds, one run | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.551 | 1.0× |
| Previous Mech AOT, `cb9d6913c` | 119.059 | 216.0× |
| Lookup reuse, `e4d3ed4da` | 117.746 | 213.6× |

This single pair is **1.1%** lower; repeated full-input measurements are needed to distinguish a small gain from variation. Every output matches the independent full reference, and both Mech executions perform seven tables and **874,999,961 updates**. The [full receipt](full-lookup-v1/results.json) preserves all executable identities, inputs, policies and process records. The finite execution policy is identical to the preceding successful full qualification. The lookup candidate uses 220.3 MB peak RSS. Rust parity remains unfinished.

[Native validation](../native-owner-dispatch-v1/lookup-reuse-validation-v1/summary.json) passes **220 tests**, with three pre-existing exclusions. Tests check equal debit for cold and cached reads, stale mutation versions, foreign tables, zero values, missing keys, exhausted comparison limits, growth and actual generated use through original/decoded/restored execution. Every reservation is released after completion. An independent read-only review found no correctness issue.

The [matching profiling build](profile-lookup-build-v1/results.json) has byte-identical complete machine code to the timed executable: 3,969,308 bytes, SHA-256 `002e696eb34e421109fd6fa42d8a3fe50ac7a2b1d5b1c4224f90de6499e95652`. Three captures across a completed full execution show [map storage calls at 76–78%](full-profile-lookup-v1/analysis.json) of main-thread samples, reads at 20–25%, insertions at 18–20%, selected ranges/endpoints at 10–13%, and work debits at 11–12%. Categories overlap. This profile also verifies exact full output and all updates; profiling elapsed time is excluded from timing results. It motivated the generated compact-key stage above; the small intermediate range/selection fusion was validated but not separately timed.

## Combined native library-call setup

Compiler [`cb9d6913c`](https://github.com/mech-lang/mech/commit/cb9d6913c129c217cf96c8ad7e7c35174b41213c) combines native library-call setup and teardown. The call retains the three thread-local addresses for its account, work observer and relative limits, avoiding repeated address lookups during setup and restoration. The same work debits, fresh per-call observation, foreign-account rejection and enclosing caps remain in force. Stack guards restore the caller's state on normal return and unwinding. IR36, work policy55 and ABI20 identify this version.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0207 | 1.00× |
| Previous Mech AOT, `30dd67991` | 1.224 | 59.0× |
| Combined call setup, `cb9d6913c` | 1.160 | 56.0× |

Elapsed time falls by **5.2%**. All nine outputs match the independent reference; both Mech executables perform seven tables and 6,999,961 updates with 443 runtime admissions. Source and program bytecode are unchanged. Runs are serial and include secured startup/shutdown, with one excluded warmup per executable. [Raw measurements](call-scope-timing-v1/results.json) retain every sample and identity. Each comparison uses Rust from its own cohort.

Validation passes [53 budget tests](../native-owner-dispatch-v1/call-scope-budget-v1/summary.json), [67 collection tests](../native-owner-dispatch-v1/call-scope-collection-v1/summary.json) and [218 native tests](../native-owner-dispatch-v1/call-scope-native-v1/summary.json), with three pre-existing native exclusions. The new unwind case verifies the parent's observation high-water mark, relative limits and account restoration after an inner failure, including foreign-account rejection and no work refund. The eight focused native-work checks are included in the 53-test budget total.

The same executable also completes the **125-million-base** workload. This first full qualification uses one serial complete process per executable, with no excluded warmup:

| Executable | Seconds, one run | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.549 | 1.00× |
| Mech AOT, `cb9d6913c` | 118.601 | 216.2× |

Both complete outputs match the independent full-input reference. Mech reports seven tables and **874,999,961 actual updates**, with 443 runtime admissions and 220.3 MB peak RSS. [Full qualification](full-call-scope-v2/results.json) retains the exact executable, input, command, resource policy and process receipts. This is a single full-input pair, not a repeated median result. The full-size gap is 216.2×; the 56.0× prefix ratio must not be presented as the full-input ratio.

The full run retains secured startup/shutdown, capability grants, memory limits and all work checks. Its finite root compute allowance is increased from 2^56 to 2^60, and its comparison allowance from 2^50 to 2^56. Actual reported use is 242,638,720,263,944,870 compute units and 3,789,652,434,638,483 comparison units. The [first full attempt](full-call-scope-v1/results.json) retained the earlier comparison allowance and stopped at that limit after 94.827 seconds; it is excluded from completed timings. Only execution allowances change; the executable is identical to the prefix-timed candidate. Repeated full-input measurements, separate decoded-source build qualification, secured/trusted comparison and Rust parity remain unfinished.

The [matching profiling executable](profile-call-scope-build-v1/results.json) has identical complete machine code to the timed candidate: 3,968,100 bytes, SHA-256 `ffe1ee366898112d85d4ec69576946477ab31f5a254f7e167f51c2f1011ef425`. Its [full execution profile](full-profile-call-scope-v1/analysis.json) takes three two-second captures at roughly 30, 62 and 94 seconds, then completes with exact full output and all updates verified. Map storage calls occupy 77–81% of main-thread samples, including reads at 21–26%, insertions at 21–22%, selected range/endpoints at 10–12%, and work debits at 12–13%. Categories overlap and cannot be added. Profiling elapsed time is excluded from timing results. Repeated lookup of the same immutable key across membership, access and insertion was the next target at this stage.

## Reused range shapes

Compiler [`30dd67991`](https://github.com/mech-lang/mech/commit/30dd67991bfb03a24c36303115f33f5ece78cc24) reuses a successfully validated range shape within a closed native map loop. Every call still computes the current range cardinality with the maintained endpoint semantics and checks current String bounds. Reuse requires the exact output schema key and cardinality; a changed width runs the full shape/layout resolver. The invocation-owned selector retains only that shape proof, with the original scratch reservation and full work debit. IR36, work policy54 and ABI20 identify the protocol.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0205 | 1.00× |
| Previous Mech AOT, `7091f025d` | 1.978 | 96.5× |
| Reused range shapes, `30dd67991` | 1.230 | 60.0× |

Elapsed time falls by **37.8%**, a **1.61× speedup**. All nine timed outputs exactly match the independent reference. Both Mech executables perform seven tables and 6,999,961 updates, with 443 runtime admissions. Source and program bytecode are unchanged. Runs are serial and include secured startup/shutdown, with one excluded warmup per executable. [Raw measurements](shape-timing-v1/results.json) retain every sample and identity. Ratios use Rust from this cohort. These prefix measurements do not qualify the full 125-million-base workload.

[Engine validation](../native-owner-dispatch-v1/shape-reuse-engine-v3/summary.json) passes 67 tests, and the [full native suite](../native-owner-dispatch-v1/shape-reuse-native-v2/summary.json) passes 218 with three pre-existing exclusions. Inclusive/exclusive ranges are compared against ordinary materialized ranges across changed widths, shifted endpoints and integer limits. Native original/decoded and restored-image execution checks changing widths, current bounds failures after reuse, unchanged accounting and complete cleanup. Earlier failed validation receipts retain a test-only error-name correction, a work-metadata lifetime assertion correction and two stale version expectations.

The [profiling build](profile-shape-build-v1/results.json) has identical complete machine code to the timed executable: 3,949,744 bytes, SHA-256 `af86a9f9b805421628a7d09ab19aed2c79dae6641dae5f4866ee58a6cb3b1148`. Three samples during early full-input counting and three separate, completed one-million-base executions show:

| Path | Early full-input sample share | Complete-prefix sample share |
|---|---:|---:|
| Closed map storage calls | 80–81% | 67–69% |
| Private map reads | 22–23% | 19–20% |
| Private map insertions | 21–22% | 18–20% |
| Range selector, including fresh endpoints | 11–12% | 8–10% |
| Work-scope guard setup/teardown | 13–14% | 10–12% |
| Canonical map publication | 0% observed | 10% |

Categories overlap. No samples contain the full range shape validator, although it still runs at the first or changed shape. The [full-input profile](full-profile-shape-v1/analysis.json) retains the 45-second bounded stop; the [prefix profiles](prefix-profile-shape-v1/analysis.json) each complete, match the independent output and perform all 6,999,961 updates. Prefix sampling begins shortly after launch and may omit early startup. Neither profile set supplies benchmark timings. Repeated map lookup and call setup were the next measured targets at this stage; full-input qualification and Rust parity were then unfinished.

## Closed native map loops

Compiler [`7091f025d`](https://github.com/mech-lang/mech/commit/7091f025d2489ef511c4650b2c5e6d6dfe29102b) binds a proved closed map loop to invocation-owned storage and a pinned String. The generated Mech code still traverses the input, chooses branches, computes counts and updates every window. Private storage calls use the existing hash library. Entry validates the source representation and caller ownership; the same finite work account funds bounded batches of generated iterations and individual storage operations. Unsupported representations retain canonical execution. A suspended parent comprehension does not prevent a closed child map loop from selecting this path. IR36, work policy53 and ABI20 identify the protocol.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0211 | 1.00× |
| Previous Mech AOT, `32a3a7b44` | 7.336 | 347× |
| Closed map loops, `7091f025d` | 1.985 | 94× |

The new executable is **3.70 times faster**, reducing elapsed time by **72.9%**. All nine timed outputs exactly match the independent reference. Both Mech executables perform seven tables and 6,999,961 updates. Runtime admissions fall from 55,717,707 to 443; individual private storage calls remain. Source and program bytecode are unchanged. Runs are serial, include secured startup/shutdown, and exclude one warmup per executable. [Raw measurements](closed-map-timing-v2/results.json) retain every sample and identity. Ratios use Rust from this cohort; its changing short-run denominator does not establish a change in the unchanged parent. This diagnostic is not full-input qualification, Rust parity or a comparison with interpreted execution.

[Validation](../native-owner-dispatch-v1/closed-map-nested-validation-v1/summary.json) records 217 native checks passing with three pre-existing exclusions. New original/decoded and restored-image tests cover ordinary non-DNA keys and caller-produced increments, finite fuel, admission refusal, repeated nested invocations, protocol rejection and complete cleanup. The 84 counting cases also execute through guarded, native and restored-image paths, including empty strings, Unicode and CRLF. An [IR36 follow-up](../native-owner-dispatch-v1/closed-map-nested-identity-v1/process.json) follows the version-only identity update.

The [matching profiling build](profile-closed-build-v1/results.json) has identical complete machine code to the timed executable: 3,949,076 bytes, SHA-256 `10a1b5d0337d396ccbffcb1449673930d47229dc5835d4c027438cc717c8b33f`. Three two-second samples during the beginning of full-input counting show:

| Path | Inclusive main-thread sample share |
|---|---:|
| Private map/key storage binding | 88–90% |
| Selected range cardinality/shape validation | 43–46% |
| Private map reads | 13–14% |
| Private map insertions | 12–13% |
| Library work debits | 5.5–6.2% |

Categories overlap and must not be added. [Analysis](full-profile-closed-v1/analysis.json) counts unions of matching stacks and uses all main-thread samples, including partial unwinds. The subject was stopped and reaped at its planned 45-second deadline. These are bounded profiles, not completed full-input timings. At this stage, repeated range shape/cardinality validation was the largest identified remaining category; reducing it had to preserve the maintained range semantics and failure behavior. Packed keys, independent-loop parallelism, full-input qualification and same-binary secured/trusted measurements were then unfinished.

The preceding [`bc6fdbce8` attempt](closed-map-timing-v1/results.json) measured 7.634 seconds against a 7.356-second parent and selected no closed map regions. Its top-level-only admission restriction missed both counting loops inside parent comprehensions. The [selection analysis](closed-map-timing-v1/selection-analysis.json) retains that failed optimization result; it is not counted as a gain. The corrected timing harness requires both closed map regions and an actual reduction in runtime admissions before collecting the reported cohort.

## Native paths and fused helper admission

Compiler [`32a3a7b44`](https://github.com/mech-lang/mech/commit/32a3a7b449f64740ecf137ba3539a08cda2240e2) prepays native paths across scalar branches and joins between runtime boundaries. Every interior has the same entry; headers cut backedges, and helpers cut effects. A native Tail latch retains its original retirement at the following header. The next callback must match a proved frontier, and arithmetic failures retain their original source location. Selected map and key helpers admit their own boundary in the helper callback, eliminating the separate admission round trip. Refused owner entry preserves canonical execution. IR34, work policy52 and ABI19 identify this protocol.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0222 | 1.00× |
| Previous Mech AOT, `913450a68` | 8.988 | 405× |
| Native paths, `32a3a7b44` | 7.331 | 330× |

Elapsed time falls by **18.4%**. All nine timed outputs match the independent reference; both Mech executables perform seven tables and 6,999,961 updates. Runtime admissions fall from 139,717,328 to 55,717,707. The latter includes admission fused into map/key helper callbacks; it is not a count of standalone admission-function calls. Source and program bytecode are unchanged. Runs are serial, include secured startup/shutdown, and exclude one warmup per executable. [Raw measurements](map-path-timing-v1/results.json) retain every sample, configuration and executable identity. Ratios use Rust from this cohort only. This diagnostic does not qualify the full 125-million-base workload or Rust parity.

[Validation](../native-owner-dispatch-v1/map-path-validation-v2/summary.json) passes 215 native checks with three pre-existing exclusions. Original/decoded and restored build-image tests exercise branches with multiple runtime successors, actual callback reduction, exactly-once fused admission, canonical fallback, helper replay and foreign-frontier rejection, insufficient fuel before state/storage changes, exact interior arithmetic failures and complete cleanup. The existing 84 independently checked counting cases remain correct. The first broad run passed 214 checks and failed only an outdated ABI18 expectation; the ABI19 expectation passes in the complete rerun.

The [profiling build](profile-path-build-v1/results.json) has the identical complete machine-code section as the timed executable: 3,943,088 bytes, SHA-256 `9dab5e6a7d578c5151ad1a931899d3dc380021be8ce854ae27c08fa084d19947`. Three two-second samples during the beginning of full-input counting show:

| Path | Inclusive sample share |
|---|---:|
| Retained map/key helpers | 65–67% |
| Runtime boundary validation, including fused admission | 27–29% |
| Standalone admission callback | 17–18% |
| Native work debits | 11–14% |
| Selected range cardinality/shape validation | 10–11% |

Categories overlap and must not be added. [Analysis](full-profile-path-v1/analysis.json) records symbol patterns and union counting. The subject was stopped and reaped at the planned 45-second deadline; these are bounded samples from the beginning of execution, not a completed full-input timing or a matched before/after profile.

This compiler stage still admitted about eight runtime boundaries per table update and separately validated/projected keys and checked map operations. Its next targets were reducing repeated work inside these helpers and extending native finite-fuel execution across map boundaries. Packed keys, independent-loop parallelism, practical full-input source/decoded qualification and same-binary secured/trusted measurements were then unfinished. The counting algorithm remains source-written Mech.

## Cached caller inventory

Compiler [`913450a68`](https://github.com/mech-lang/mech/commit/913450a68c609070b2f12f8f5f5bbf742fa11b75) retains the outer caller's fixed node inventory for each proved closed map-loop invocation. The region may contain native scalar/state operations, selected map operations and selected key projections; other managed operations and nested loops decline reuse. Snapshot holdings and call-cache metadata are read afresh, and every operation still includes current private table and key-view nodes and actual memory use. Work policy51 identifies the changed setup/accounting; IR33 and ABI18 are unchanged. Source and generated program bytecode are unchanged.

Three alternating complete-process measurements on the first **one million bases** of the standard THREE record give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0208 | 1.00× |
| Previous Mech AOT, `a3b1ddfcd` | 9.679 | 465× |
| Cached caller inventory, `913450a68` | 8.944 | 430× |

This change reduces elapsed time by 7.6%. All nine timed outputs exactly match the independent reference, and both Mech executables perform seven tables and 6,999,961 updates. Runs are serial, with startup/shutdown included and one excluded warmup per executable. Mech uses secured execution. [Raw measurements and reproduction configuration](caller-census-timing-v1/results.json) retain every sample and artifact identity. Ratios use Rust from this cohort only; its short runtime varies between cohorts. This diagnostic does not qualify the full 125-million-base source-map workload or Rust parity.

[Validation](../native-owner-dispatch-v1/caller-census-validation-v2) passes 215 native checks with three pre-existing exclusions. During actual generated-code tests, every reused inventory is compared with an independent full census, including after cache population, table growth and view retirement. All 84 original/decoded counting cases pass, including Unicode and CRLF. New original/decoded cases also verify that managed key construction and nested scalar control select the full inventory path. The earlier validation record failed only because the new nested-control fixture placed a state-machine invocation inside an unsupported arithmetic position; the corrected fixture uses an ordinary binding, and the complete suite passes.

The [matching profiling build](profile-caller-build-v1/results.json) has the identical complete `__TEXT,__text` section as the timed executable: 3,923,740 bytes, SHA-256 `e0bdc9ec58411a8a5e51c21c1aee2b6646a7942c1e04f3cfbcaa6e80c68c0336`. Three two-second samples during the beginning of the full-input count show:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Retained map/key helpers | 55–56% |
| Generated-block admission | 40–41% |
| Native work debits, across paths | 17–20% |
| Selected range cardinality/shape validation | 8–10% |

Categories overlap and must not be added. [Analysis](full-profile-caller-v1/analysis.json) retains the symbol patterns and union counting. These samples describe only the bounded beginning of the full-input execution, not every window width or a matched before/after profile. The subject was stopped and reaped after 45 seconds; its elapsed time is not a benchmark result. The one-million-base complete process still makes 139,717,328 actual admission callbacks, unchanged from its parent, for 6,999,961 table updates.

The [exact timed Rust binary was also profiled](rust-full-profile-v1/results.json), without rebuilding it, in three serial full-input runs. All three complete outputs match the full reference. [Per-thread analysis](rust-full-profile-v1/analysis.json) finds counting-task stacks on seven worker threads in each capture; the main thread waits for results in 305/307, 307/308 and 305/306 samples. These are stack observations, not CPU-utilization percentages or new timing measurements. The [protected source](../../../archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs) uses rolling two-bit keys and hash-table entry updates inside those native worker loops.

At this stage, the structural gap was larger than the caller census: Mech still crossed runtime admission boundaries about twenty times per table update and separately checked range, key and map operations. The next target was an entry-bound closed map loop with native finite fuel and simpler storage calls, retaining source-written traversal and arithmetic. Packed key representation and independent-loop parallelism also differed from Rust. Those later changes are absent from this historical cohort.

## Grouped native admission

Compiler [`a3b1ddfcd`](https://github.com/mech-lang/mech/commit/a3b1ddfcdf501f4bc3c6eb81a7e975849295fcc4) admits a straight-line group of native map-owner instructions once before its first instruction. Group interiors have a single predecessor and contain no library helper or loop/ownership boundary. Every source instruction is still emitted, including its original arithmetic failure location. Refused owner entry retains the canonical per-block callbacks. The full original instruction work plus group-proof overhead is prepaid on the same finite ledger. IR33, work policy50 and ABI18 identify this protocol.

This diagnostic comparison uses the first **one million bases** of the standard THREE record. Three alternating complete-process measurements per executable give:

| Executable | Median seconds | × Rust time |
|---|---:|---:|
| Unmodified upstream Rust #7 | 0.0184 | 1.00× |
| Mech AOT before grouping, `7aa1bea1b` | 12.570 | 682× |
| Mech AOT after grouping, `a3b1ddfcd` | 9.600 | 521× |

The compiler change reduces elapsed time by 23.6%. All nine timed outputs exactly match the independent reference; Mech uses secured startup and shutdown, and each executable has one excluded warmup. Source and generated program bytecode are unchanged. Ratios use Rust measured in this same cohort; its short complete-process timings vary between runs. Raw seconds and all samples are in [map-admission-timing-v1](map-admission-timing-v1/results.json).

| Observed work on one million bases | Before | After |
|---|---:|---:|
| Runtime admission callbacks | 321,998,942 | 139,717,328 |
| Hash tables | 7 | 7 |
| Actual hash-table updates | 6,999,961 | 6,999,961 |

[Validation](../native-owner-dispatch-v1/map-admission-validation-v1) passes 213 native checks with three pre-existing exclusions. New original/decoded and restored-image tests observe fewer actual callbacks, retained canonical fallback, refusal with one unit less than the group work requirement, rejection of group replay/interior entry, exact interior arithmetic errors and complete owner cleanup. The existing 84 counting cases remain correct. Rust parity is not reached; this is not a full 125-million-base source-map result.

The [matching profiling build](profile-groups-build-v1/results.json) retains symbols with the public CLI's final-host FatLTO settings. Its entire `__TEXT,__text` section is byte-identical to the timed candidate: 3,919,368 bytes, SHA-256 `bc38c7feb54e6ece3c7dd2f58a3d814549c5e749473f61a223e2b36d7700ebc2`. Three two-second samples on the full input identify the remaining overhead:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Retained map/key helpers | 59–60% |
| Generated-block admission | 35–37% |
| Native work debits, across paths | 20–23% |
| Library work debits, across paths | 18–21% |
| Selected-key projection, within the helpers | 9–10% |
| Selected range cardinality/shape validation | 8–9% |

Categories overlap and must not be added. [Reproducible analysis](full-profile-groups-v1/analysis.json) counts the union of matching stacks within each category. These samples characterize the grouped candidate; they are not a matched before/after profile. The subject was stopped and reaped at the planned 45-second deadline ([receipt](full-profile-groups-v1/results.json)), so this is not a full-input timing. Further work targets the repeated admission, map-binding and accounting checks while retaining general map storage, source-written operations and finite resource accounting.

The attempted 100,000-base Rust comparison was excluded before quantitative timing: the upstream program prints tied `AG` and `GT` frequencies in the opposite order from the required ascending-key tiebreak ([specification](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html), [failed warmup](rust-span-diagnostic-v1/results.json)). The published Rust program is unchanged. The one-million-base prefix passes exact output comparison for both executables. [rust-span-diagnostic-v2](rust-span-diagnostic-v2/results.json) retains the separate first paired cohort; its Rust median is not used as a denominator for later cohorts.

## Selected String keys

Compiler [`7aa1bea1b`](https://github.com/mech-lang/mech/commit/7aa1bea1b5565113cd07ddeaeea2bed30ed84a54) borrows selected String map keys instead of materializing a range and substring on every window. Selection still uses the maintained String index, including Unicode and CRLF behavior. The compiler selects this representation only when every key use belongs to the same closed map region; an extra observer retains the canonical path. Source control flow, all hash-table updates and caller-produced counts remain unchanged. IR32, work policy49 and ABI17 identify the new representation and checked helper protocol.

Three alternating measurements per executable on the same 100,000-base prefix give:

| Mech AOT compiler | Input | Median seconds | × latest Mech AOT |
|---|---:|---:|---:|
| Parent `f6ee09e63` | 100,000 bases | 4.686 | 3.40× |
| Latest `7aa1bea1b` | 100,000 bases | 1.380 | 1.00× |

This is a 3.40× speedup, or 70.6% less wall time, on the diagnostic input. Every timed process includes secured startup and shutdown, matches the independent reference output, and the candidate reports seven hash tables with 699,961 actual updates. One warmup per executable is excluded. The [raw measurements](key-span-timing-v1/results.json) retain all six samples, source/input/executable hashes and the launch policy. No full-input speedup is inferred from this small-input result.

[Validation](../native-owner-dispatch-v1/key-span-validation-v2) passes 211 native checks with three pre-existing exclusions. The counting fixture now covers 84 original/decoded cases: seven widths and six inputs, including empty strings, Unicode and CRLF. Checks observe both projection visits, require zero canonical range/key calls on the selected path, compare every count to an independent oracle, and exercise admission refusal, bounds errors and failure cleanup.

The [selected-key profiling build](profile-spans-build-v1/results.json) retains symbols with the same public-CLI link settings. Its entire `__TEXT,__text` machine-code section matches the timed candidate: 3,917,028 bytes, SHA-256 `c5a3d39743b09105608a0f0efe9bd84887c05af6f439f6a4a2d6d08e998810c6`. Three two-second samples on the standard 125-million-base input identify the remaining costs:

| Path | Inclusive share across the three sample windows |
|---|---:|
| Generated-block admission | 46–49% |
| Retained map/key helpers | 46–50% |
| Selected-key projection, within those helpers | 23–24% |
| Native work debits, across paths | 21–23% |
| Selected range cardinality/shape validation | 7–8% |
| Ordinary range snapshot / canonical String selection | 0 observed samples |

These categories overlap and must not be added. [Analysis](full-profile-spans-v1/analysis.json) counts each observed stack at most once within a category, including nested generic symbols. [Process receipts and stacks](full-profile-spans-v1/results.json) retain the evidence. The subject was stopped and reaped at the 45-second profiling deadline; profiling overhead is included, and this is not a completed full-input benchmark. Reducing repeated admission/accounting and projection checks was the next target at this stage. Full-input correctness, practical full-input runtime and Rust parity were then unqualified for this source-map implementation.

## Previous cache metadata improvement

Compiler [`f6ee09e63`](https://github.com/mech-lang/mech/commit/f6ee09e631048fb831d2032e8013a56d876efc63) maintains library call-cache metadata totals when each cache changes. Previously every retained-map operation rescanned all caches. It preserves the source, generated program image, map operations and security account; work policy 48 identifies the changed accounting protocol. All 209 native checks pass, with three pre-existing exclusions, including independent observation of the maintained totals ([validation](../native-owner-dispatch-v1/cache-census-v1)).

Each row below is the median of three fresh secured processes. The source and input are identical within each paired cohort. Runs are serial, alternate candidate/parent order and include startup and shutdown. Every complete output matches the reference. Build, profiling and reference generation are outside the timed interval.

| Input | Compiler | Seconds | × `f6ee09e63` Mech AOT on this input |
|---|---|---:|---:|
| 1,000 bases, deterministic diagnostic | Parent `9e2d1a29c` | 0.3966 | 1.09× |
| 1,000 bases, deterministic diagnostic | `f6ee09e63` | 0.3651 | 1.00× |
| 100,000 bases, prefix of standard THREE record | Parent `9e2d1a29c` | 8.4683 | 1.81× |
| 100,000 bases, prefix of standard THREE record | `f6ee09e63` | 4.6755 | 1.00× |

The 100,000-base improvement is 44.8% less wall time. It is a diagnostic result, not a completed 125-million-base benchmark. Results, process receipts, complete outputs and launch policies are in [cache-timing-v2](cache-timing-v2/results.json) and [cache-scale-v1](cache-scale-v1/results.json). These cohorts have different inputs and cannot share a timing denominator.

The `9e2d1a29c` source-map executable exceeded the 180-second limit on the full 125-million-base input ([receipt](full-timing-v1/results.json)); it was killed and reaped. The `f6ee09e63` candidate was sampled on that input for a bounded 45 seconds, then killed and reaped. Neither is a completed full-input timing. No full-input candidate-versus-parent speedup is inferred from those stops.

## Historical #909 source and compiler distinction

The [recorded #909 checkpoint](https://github.com/mech-lang/mech/blob/c5b0b3a35/docs/validation/canonical-knucleotide-word-source-checkpoint-v1.json) used compiler `f2268e482` and reports 0.4828 seconds for 125 million bases on the earlier M1, with a 4,806,512-byte executable and 146.1 MB peak RSS. Its executable SHA-256 is `ff781abb8d10b40374ddba318f9386e124a08b645ac2c84d4be7d60c84b2bb1e`. That exact executable has not been rerun in this study. The historical record is not a paired hardware comparison or the denominator for current timings.

The same historical **source**, SHA-256 `12cadfcd00e25605f190e9d360f7f7bb661be8a02754961055ee5b6dfa84b60f`, was also rebuilt with the **cache-stage compiler `f6ee09e63`** as a separate regression control. This is not the original #909 compiler/executable. The old compiler selected dense-counter and direct-query lowering; the cache-stage build selected library hash-table updates. The old lowering remains test-only. Those paths perform materially different work even though the source and output agree.

On the current machine, the rebuilt histogram-source control performs seven full hash tables and 874,999,961 updates. Its complete stdout and native execution report are checked on every run. Three paired complete-process measurements on the standard 125-million-base input give:

| Executable | Seconds | × Rust time |
|---|---:|---:|
| Same historical Mech source, compiler `f6ee09e63` | 4.2816 | 7.77× |
| Unmodified upstream Rust #7 | 0.5511 | 1.00× |

These measurements are the `full-preserved-control` cohort in [cache-timing-v2](cache-timing-v2/results.json); “preserved” refers only to source. Rust is 7.77 times faster in this cohort. This control neither measures the new source-map program nor demonstrates a hardware regression from historical #909. It also does not isolate the cache-total optimization: earlier compiler changes already altered the histogram path.

The workload distinction follows the [Game's k-nucleotide specification](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html): count every window for all seven widths using library hash tables, then query the resulting counts. Encoding keys is allowed; eliminating required table updates changes this prescribed work. The Rust source remains untouched.

## Cache-stage executable profile

[profile-cache-build-v2](profile-cache-build-v2/results.json) relinks the exact generated Mech object with the public CLI's final-host FatLTO and one codegen unit, retaining symbols. [analyze_profile.py](analyze_profile.py) verifies that its entire Mach-O `__TEXT,__text` section is byte-identical to the timed candidate: 3,896,484 bytes, SHA-256 `085fe0295086bdd5cb608db625616b4a9dd8cdb33c474c3e6380a29acd417689`.

Three 2-second stack samples from the full-input counting loop are retained in [full-profile-cache-v1](full-profile-cache-v1/results.json), with [reproducible analysis](full-profile-cache-v1/analysis.json). Ordinary library invocation accounts for 57–59% of inclusive main-entry samples. Within that path, range snapshot construction accounts for about 13%, and canonical String selection about 6–7%. The retained-map helper accounts for 12–13%; the maintained caller-cache metadata total accounts for less than 1%. These inclusive categories overlap and must not be summed. Samples describe the cache-stage candidate only; no matched baseline profile is available.

That profile selected per-window range/String materialization and library invocation overhead as the next target; the selected-key change above addresses it. It preserves ordinary range/index error behavior, lifetime and accounting checks, Unicode fallback and caller-produced map values. The counting algorithm remains expressed in Mech.

## Evidence and reproduction scope

- `compiler-v2` through `compiler-v18` pin successive compiler builds and their environments, including native register loops, parallel execution, cold failure origins and compact character encoding. Generated standalone binaries and retained Cargo projects are local build artifacts under `.build`; their hashes and build commands are in the receipts.
- `build_and_time.py`, `measure_cache.py`, `measure_scale.py`, `measure_spans.py`, `compare_rust_spans.py`, `measure_admission.py` and `measure_stage.py` retain the exact build/run procedures. Output directories are versioned and guard against overwriting samples. `measure_stage.py` uses the configuration saved in each result and verifies its parent executable against the parent cohort's recorded hash. `measure_cache.py` reuses the candidate build receipt from `cache-timing-v1`; that attempted cohort stopped before quantitative timing because unmodified Rust used a different tie order on the synthetic input. Rust is excluded from that diagnostic, and its full standard-input output passes.
- `profile_full.py`, `build_profile.py` and `analyze_profile.py` retain the sampled process procedure, matching-link settings and code-identity check. Earlier `profile-build-v2`, `full-profile-v2` and `profile-cache-build-v1` used a ThinLTO final link and are explicitly marked as exploratory mismatches. Their percentages are not a matched before/after comparison. `profile-build-v1` and `full-profile-v1` retain failed preparation/monitor diagnostics, not benchmark samples.
- `profile_rust.py` and `analyze_rust_profile.py` capture and summarize the exact timed upstream Rust binary on the complete input; the original program and binary are unchanged. Profiling process durations are excluded from benchmark cohorts.
- `available-timing-v1` records the earlier canonical-map implementation at compiler `f6fb76f5f`: 5.4684 seconds on the 1,000-base diagnostic. `candidate-timing-v1` records the subsequent retained-map change. These historical diagnostic measurements are not full-input results.
- Every build, test, profile and timed process uses the existing common mutex and owned-process cleanup. The canonical benchmark dataset, website data and protected upstream submissions are unchanged.

The latest source build completes the full workload with exact output and table-update qualification. A separate decoded-source executable qualification and secured/trusted timings of the same executable remain unfinished. The source-map implementation has not reached Rust's performance.
