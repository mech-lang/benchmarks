# Counting-loop strategy comparison

This study separates representation, algorithm, compiler lowering and runtime
costs in the complete nucleotide workload. The target is the protected,
unmodified Rust #7 executable on the same Mac. All primary runs retain the
125-million-base input, seven complete maps, 874,999,961 physical updates and
secured Mech startup/shutdown. Diagnostic Rust variants do not replace Mech
implementations or add canonical benchmark samples.

## Evidence that narrows the search

The earlier [strategy comparisons](../strategy-diagnosis-v1/results.json)
contain 180 complete-process observations. Wider keys and counters, decoding
inside each worker, ordinary scoped threads and an independently compiled Rust
version of Mech's table layout all remain near the protected Rust time. This
supports an important distinction: the storage algorithm can run near the
target; it does not identify a single cause of the remaining Mech overhead.
Those diagnostics omit source-state transport, managed admission, precise
errors, finite work accounting and publication.

The exact Rust executable uses a rolling integer key, an inlined entry update,
eight-byte NEON fingerprint groups, a full-key check and a direct increment.
[Retained disassembly](../rust-codegen-audit-v1/findings.txt) establishes these
properties of the actual comparison binary. Its first-candidate successful
u64 path has 34 static instructions; this is not a cycle count.

The current Mech strategy already has rolling packed keys, inlined updates,
SIMD control groups, seven independent tasks, source-derived bounds/value
proofs and a helper-free funded loop. Repeating those changes is not a new
optimization direction.

## Completed structural experiments

Each row is a separate, balanced six-cohort full-input comparison. Ratios use
Rust from that row; samples are not pooled across rows. Every process and
outlier is retained.

| Change | Rust seconds | Parent Mech seconds / × Rust | Candidate seconds / × Rust |
| --- | ---: | ---: | ---: |
| Separate incoming-edge cold snapshots, IR70 | 0.5534 | 0.8338 / 1.507× | 0.8218 / 1.485× |
| Direct entry continuation and peeled first probe group, IR71 | 0.5565 | 0.8218 / 1.477× | 0.7886 / 1.417× |
| Callee-computed prepaid extent, IR72 | 0.5661 | 0.7985 / 1.411× | 0.8173 / 1.444× |
| Caller-bound prepaid extent, IR73 | 0.5622 | 0.7902 / 1.406× | 0.7821 / 1.391× |

[IR70 observations](../full-cold-snapshots-cohort-v1/results.json) show a small
1.45% median reduction, with five faster pairs and one slower pair. Its full
native suite passed 364 checks, with three ignored, plus one catalog check.

[IR71 observations](../full-direct-entry-cohort-v1/results.json) show a 4.04%
median reduction and six faster pairs. Its focused validation passed three
generated probe tests and six source-equivalence checks. This is not a claim
that the complete native suite ran on IR71. The short-input comparison regresses
from 0.0902 s / 4.320× Rust to 0.1011 s / 4.843× Rust; Rust is 0.0209 s in that
separate prefix cohort. There is no uniform improvement across input sizes.

The [IR71 hardware diagnostic](../direct-entry-hardware-v1/results.json)
corroborates a physical change: median retired instructions fall from 44.31
billion to 40.82 billion, versus 33.14 billion for Rust. These nine diagnostic
processes are separate from the primary elapsed-time cohort. The exact-code
[static audit](../direct-entry-codegen-audit-v1/steady-paths-v2.json) finds
38–41 instructions on its assumed successful paths, versus 42–45 for IR70.
The original-source byte load, fingerprint/full-key check and actual counter
store remain in every counted path. Both source functions and every emitted
width arm are included; width is not inferred from block order.

The [IR72 experiment](../full-funded-extent-cohort-v1/results.json) replaces the
per-iteration fuel decrement with a stopping extent computed from the actual
endpoint and already prepaid visits. Exact fuel is reconstructed at every
observable exit. It regresses 2.35%, with all six pairs slower. The exact
[static paths](../funded-extent-codegen-audit-v1/steady-paths-v2.json) reveal that
Cranelift reconstructs the supposedly invariant minimum inside each iteration
and spills a hash input: 42–45 instructions, five branches and one stack load.
Separate counters rise to 44.31 billion instructions from the parent's 40.80
billion. Removing operations from source IR does not guarantee smaller machine
code. Two failed new test fixtures remain recorded; one failed to select the
existing large-input allowance and the other incorrectly required diverse-key
growth from a one-key refill test. Neither correction changes compiler logic.

The [IR73 experiment](../full-caller-extent-cohort-v1/results.json) passes the
precomputed stopping extent and fuel base as two immutable private arguments.
It also canonicalizes the source counter with its proved equal native origin.
The original helper ABI, finite prices and source failure continuations remain.
This avoids repeated extent reconstruction. Its
[38 assumed successful paths](../caller-extent-codegen-audit-v1/steady-paths-v2.json)
have 37–40 instructions, five branches, no stack access and no zero/one moves.
The median falls only 1.03% against IR71, with four faster and two slower pairs
and overlapping ranges. This is a modest full-input change, not a large win.
The separate prefix cohort has Rust 0.0193 s, parent 0.1009 s / 5.222× and
candidate 0.0874 s / 4.519×: a 13.45% reduction. All prefix warmups and samples
remain in their own receipts; they are not pooled with full input.

The [current exact-code profiles](../caller-extent-remaining-profile-v1/results.json)
partition 6,688 worker observations: 85.99% generated loops, 5.34% storage,
4.28% active accounting, 1.27% accounting waits and 3.12% bridge/other work.
These are sampled thread observations including waits, not elapsed-time shares.
[Separate whole-process counters](../caller-extent-hardware-v1/results.json)
give 39.96 billion instructions / 10.67 billion cycles, versus parent
40.82 / 10.54 and Rust 33.13 / 7.85. Fewer retired instructions did not establish
a cycle reduction in this diagnostic cohort.

The exact current compiler revision is
[`393d23b24`](https://github.com/mech-lang/mech/commit/393d23b24b80cad13e2c2b0284823290d7bafacf),
IR73 / ABI27 / work65. Its
[full native suite](../../native-owner-dispatch-v1/caller-extent-native-v1/summary.json)
passes 365 checks with three existing manual exclusions; the
[catalog integration check](../../native-owner-dispatch-v1/caller-extent-catalog-v1/summary.json)
also passes. Focused checks cover both original and decoded source, complete
maps, changed inputs, all admitted widths, collisions, wraparound, full-table
defensive bounds, precise failures and refills around 1,024/2,048 visits.
Each funded function admits 20,608 code bytes and 112 stack bytes; entry/source/
snapshot maxima are 86/77/23 inside the unchanged 512 envelope. Its caller
uses 56 instructions and the fixed template 530 inside the unchanged 1,024
envelope. Eighteen width arms and the generic arm are all included in admission.

## Matched Rust code-generation pipelines

[This separate diagnostic](../backend-comparison-v4/results.json) compiles the
unchanged upstream Rust source twice with the same Rust 1.99.0-nightly compiler,
locked dependency graph and release flags: once through its normal LLVM backend,
once through the official, unmodified `rustc_codegen_cranelift` component.
Here, **stock** means that distributed component without local backend changes.
The source is compiled independently into each pipeline; LLVM output is not
passed to Cranelift. Both builds link the same already compiled standard-library
and dependency code; application and monomorphized generic code use the selected
backend. The retained original Rust executable remains a fourth control.

| Full-input diagnostic | Median seconds | × protected Rust time |
| --- | ---: | ---: |
| Protected original Rust executable | 0.5617 | 1.000× |
| Matched Rust source through LLVM | 0.5604 | 0.998× |
| Matched Rust source through stock Rust Cranelift backend | 7.4843 | 13.324× |
| Current Mech lowering through Cranelift | 0.7861 | 1.399× |

Six predeclared orders per input size retain all 48 diagnostic executions,
including first launches and outliers. All full outputs match. Earlier attempts
remain: the March backend twice fails in Mach-O unwind emission, and the first
July LLVM command has an incorrect dependency search path after Cargo's artifact
layout changes. Only the completed fourth attempt supplies the table above.
Its rebuilt dependencies occupy a separate directory; protected binaries and
dependencies are unchanged. These observations add no canonical benchmark data.

This comparison shows a large difference between these **compilation pipelines**
for this source. It is not an isolated measurement of Cranelift's machine-code
emitter, a same-version backend ceiling, or evidence that Rust must be this slow
with Cranelift. Mech uses Cranelift 0.131.3; the official Rust component's embedded
Cranelift version has not been established here. Inlining, intermediate forms,
optimization settings and front-end integration can differ. No profile-based
cause is assigned to the Rust-backend slowdown by this experiment.

Mech's compiler derives rolling packed keys, in-place private map updates,
scalar bounds and parallel independence from the string/map source. The Rust
program explicitly specifies rolling integer keys, key widths and worker jobs.
Both still construct all seven complete maps. This supports the narrower design
hypothesis that the Mech source retains enough information to recover an
efficient representation before Cranelift. Types, immutable values and explicit
function/data dependencies supply proof opportunities; their individual causal
contributions, general language superiority and normalized source-size advantage
are not established by this backend experiment. The compiler must implement the
transformations, and Rust parity remains incomplete.

## Broader options

| Direction | Mechanism and evidence | Status |
| --- | --- | --- |
| Canonical entry/update control flow | Continue directly from a real entry; peel the common first group; normalize SIMD candidate bits only after a full-key mismatch. Removes nullable-result joins and slow-probe induction from ordinary hits. | Implemented and measured as IR71. |
| Strip-mined native loop extent | Intersect the actual source endpoint with already prepaid visits once at entry. Use one hot stopping bound and reconstruct exact unused credit only at observable exits. | IR72 regresses after backend rematerialization. IR73 caller binding fixes that machine-code issue; full-input median improves only 1.03% against IR71. |
| Cursor and affine source-state representation | Represent iteration by a source cursor; reconstruct source indices and previous-window positions at precise exits. The Rust iterator already avoids repeated index/address construction. | Later [IR74 trial](../cursor-profile-checkpoint-v1/README.md) implements the cursor, but native counter reconstruction remains in the loop. The full median is 1.52% lower with three faster/three slower pairs; no robust gain is established. Explicit cold-state recipes remain unimplemented. |
| Backend isolation | Compile the same Rust source with LLVM and the official Rust Cranelift component. Distinguish complete compiler pipelines from the machine-code emitter. Reduce individual Mech code-generation issues separately. | Completed 48 diagnostic processes; stock Rust Cranelift path is 13.324× the protected Rust reference on full input. Embedded backend versions differ or remain unestablished, so this is not a backend ceiling. |
| Immutable source facts and common preparation | Propagate the existing finite ASCII alphabet proof to avoid repeated ASCII/grapheme scans. Preserve original finite charges and retain unknown/CRLF/Unicode fallbacks. | Later [closed-map scan trial](../proved-graphemes-diagnosis-v1/README.md) passes 65 focused checks but regresses 1.54% on full input and is reverted. Broader preparation sharing remains open. |
| Shared admission traffic | Eliminate atomic writes for zero-sized reservations/releases while preserving validation against narrower views of the same shared account. | Exact runtime operation identified; unimplemented. Zero admission must still reject a view already above its limit. |
| Critical-path task analysis | Relate source widths to actual task start/finish times in a separate bounded diagnostic. Aggregate worker CPU samples do not identify the longest elapsed-time task. | Unmeasured; no worker-affinity or scheduler-priority changes. |
| Alternative complete-map algorithms | Dense storage for genuinely bounded key domains, chunked associative reductions, or independent lookup pipelining. Require generic proofs, complete maps, all updates and explicit admission/merge costs. | Research alternatives; no measured gain or implementation claim. |

The priority is to remove work introduced by lowering before replacing an
algorithm whose independent Rust implementation already approaches the target.
The alternatives remain open; no projected speedup is assigned to them.

## Source references

- [Protected upstream program](../../../../archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs).
- [Hashbrown 0.15.5 NEON control groups](https://github.com/rust-lang/hashbrown/blob/v0.15.5/src/control/group/neon.rs): eight-byte comparisons and raw matching-byte masks.
- [Hashbrown 0.15.5 raw table](https://github.com/rust-lang/hashbrown/blob/v0.15.5/src/raw/mod.rs): bounded power-of-two table probing and triangular group advancement.
- [LLVM analysis and transform passes](https://llvm.org/docs/Passes.html): loop canonicalization, strength reduction and invariant motion are distinct optimization mechanisms, not promises of performance for this workload.

All input, program, bytecode, executable and finite-policy hashes are retained
in the linked receipts. [Checkpoint verification](results.json) recomputes all
72 primary full-input observations and 48 backend diagnostic observations,
verifies twelve exact-code profiles, rejects nine malformed qualification
fixtures, checks immutable source/test revisions and confirms 281 terminal
owned-process receipts. The exploratory shortest-path audit is retained as
unqualified because it admitted incompatible branch predicates; the explicit
38-path audit above replaces it. Prefix startup sampling remains sparse and
loader-biased; no precise startup-overhead attribution is claimed. The canonical
data table is unchanged. This document describes an incomplete performance
investigation; Rust parity is not achieved.
