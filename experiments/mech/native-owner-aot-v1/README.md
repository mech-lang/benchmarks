# Source-map standalone performance

This study measures a Mech state machine that explicitly traverses a String, selects each window, tests map membership, reads the previous count, inserts a caller-produced count and advances its state. The compiler retains general hash storage while compiling those operations from Mech. The current source is [knucleotide-source-map.mec](knucleotide-source-map.mec), SHA-256 `ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da`.

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
