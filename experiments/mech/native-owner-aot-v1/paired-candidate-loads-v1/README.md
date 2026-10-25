# Paired candidate key and count loads

Compiler source `d8d9a7d64944cd3de78fe3f8190284924069c508` emits one
scalar 128-bit load and splits its two complete u64 words for an admitted,
initialized 16-byte narrow hash slot. The actual AArch64 code uses `LDP`
before the full-key comparison. A mismatching candidate never consumes the
count. Pointer changes, mutations, helpers and source-state reloads retain
the previous candidate-value invalidation. Wide keys retain separate loads;
direct caches are unchanged. Neither counts nor source work are narrowed.

The pass applies from ownership and layout proofs, without benchmark names,
input constants or DNA-specific dispatch. Its differential corpus includes a
renamed, parameterized function with an unrelated eight-letter immutable
producer, complete maps, growth, refill boundaries, changed extents and
source/bytecode execution. The paired-load pass can be disabled independently
of the earlier separate candidate-value pass. Existing wide-key, overflow,
failure-origin and resource-limit comparisons remain in the native suite.

Ten focused tests, 415 native checks (with three existing ignored tests),
30 line-processing checks, 36 worker-credit checks and the catalog check pass
at one clean source. Compiler v94 and the unchanged one-million-base prefix
are qualified. Guest IR is 94, host ABI is 33 and work policy is 69. Source,
bytecode, canonical resources, complete maps, all updates and finite prices
are retained.

Assembly inspection finds 38 actual paired candidate loads in each of the
two hashed funded functions. All twelve other object functions, including
the pure scalar scanner, are byte-identical to the retained production
parent. Across both hashed functions there are 11,072 static instructions,
4,108 load instructions and 2,482 stores, versus 11,200 / 4,146 / 2,482 for
the production parent and 11,328 / 4,184 / 2,482 for the unpromoted separate
load trial. These static totals do not establish a runtime improvement.

`qualify-code.py` verifies the regression receipts, source pins, exact guest
object and actual paired-load windows before creating the primary timing
gate. `plan.json` predeclares two serial six-subject sessions, each with twelve
balanced orders: candidate, retained pure-scalar production parent, separate
load trial, byte-table anchor, ordinary finite-credit anchor and unchanged
upstream Rust. No full-input warmups or outliers are excluded.

## Complete-process results

Both sessions use the standard 125-million-base THREE record from the
254,166,745-byte FASTA input. Mech includes secured startup and shutdown,
capability checks, input processing, all seven tables and 874,999,961 physical
updates. The same owned-process controller times all subjects from before
fork through exit. Each session retains twelve observations per executable.

| Executable | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Paired-load candidate | **0.531768** | **0.95484×** | **0.534934** | **0.96219×** |
| Retained pure-scalar parent | 0.549310 | 0.98634× | 0.544855 | 0.98003× |
| Separate-load trial | 0.575186 | 1.03280× | 0.572752 | 1.03021× |
| Byte-table anchor | 0.611017 | 1.09714× | 0.606306 | 1.09056× |
| Ordinary finite-credit anchor | 0.608436 | 1.09250× | 0.609355 | 1.09605× |
| Unchanged upstream Rust | 0.556920 | 1.00000× | 0.555958 | 1.00000× |

Paired median log-ratio comparisons distinguish incremental benefit from the
ratio of separate medians above:

| Candidate comparison | Session 1 change [95% interval] | Session 2 change [95% interval] |
|---|---:|---:|
| Versus production parent | −2.19% [−3.84%, −0.76%] | −2.03% [−3.13%, −0.03%] |
| Versus separate-load trial | −7.58% [−8.31%, −4.71%] | −6.03% [−7.43%, −4.91%] |
| Versus Rust | **−4.41% [−6.09%, −2.21%]** | **−2.65% [−4.30%, −2.03%]** |

Both paired Rust intervals and both parent intervals are below zero. The
candidate wins 10/12 and 12/12 matched Rust pairs, and 10/12 and 9/12 parent
pairs. This meets the predeclared promotion rule. The retained full-input
candidate is now source `d8d9a7d64944cd3de78fe3f8190284924069c508`; the
pure-scalar and separate-load executables remain comparison controls.

## Profiles, counters and footprint

Three fresh pre-armed captures per language use the exact timed guest object.
The symbol-preserving Mech profile executable has byte-identical entire text
to the primary executable. All captures check the owned PID, complete stdout
and work. No diagnostic duration enters the primary table.

Mech worker stack observations are 85.70% generated counting, 6.59% storage,
3.50% active work accounting and 1.80% helper bridges; budget waits account
for 0.85%. These are sampled stack observations, not fractions of wall time,
CPU time or instruction counts. Rust has 67.88% counting observations and
32.08% waiting observations under its thread-pool contexts.

Twenty-four additional serial counter executions use the exact timed files:

| Executable | Instructions retired | Cycles | User CPU seconds | Kernel CPU seconds |
|---|---:|---:|---:|---:|
| Paired-load candidate | **22.607 billion** | **5.622 billion** | **1.595** | 0.030 |
| Pure-scalar parent | 23.113 billion | 5.650 billion | 1.605 | 0.030 |
| Separate-load trial | 23.368 billion | 5.900 billion | 1.665 | 0.030 |
| Rust | 33.184 billion | 8.053 billion | 2.380 | 0.030 |

The candidate retires about 506 million fewer instructions than its good
parent, and about 10.58 billion fewer than Rust in this diagnostic cohort.
These counters support the measured reduction in work without substituting
for the primary elapsed comparisons.

The actual timed Mech file is 5,517,792 bytes, unchanged in file size from its
parent because of layout/padding. Entire executable text shrinks by 512 bytes
to 4,344,400 bytes. Primary median peak RSS is 163.37/162.91 MB versus Rust
140.75/141.03 MB, using decimal MB. Mech therefore still uses more memory
and a larger executable than Rust; its retained Rust file is 755,872 bytes.

## Correctness and verification

The unchanged candidate and parent AOT executables also pass seven new input
cases against an independent direct string-window oracle. Cases include mixed
case, one-character versus ordinary versus single-row wrapping, repeated
wide keys, table growth and partial credit batches. All fourteen executions
match complete output and exact update counts. These are correctness checks,
not extra performance observations. Existing native differential tests cover
complete maps, original/decoded source, wide-key fallback, overflow, precise
failure origins and resource retirement.

`verify-v2.py` validates all **221 terminal owned-process receipts**, 144
full-input observations, nine prefix observations, the three excluded prefix
warmups, source/resource/code identity, full output, exact updates, profiles,+counters and changed-input oracles. It independently recomputes every paired
interval. The first verifier's stale inspection-status spelling is retained;
v2 corrects that analysis label without rerunning any executable.

The one-million-base prefix remains a separate startup-sensitive diagnostic:
the candidate's 0.088967 s is 4.64796× Rust's 0.019141 s in that cohort. The
full-input result is not a claim about every input size, machine or language
implementation. No canonical suite or website timing is overwritten by this
experiment packet.
