# Prepared refill interaction retest

Candidate `bf10d4a51c6af5e1f212548f136a51f97f60ff4a` on
`codex/native-prepared-refill` prepares an exact full-batch price threshold
before entering shared worker accounting. It builds on decoder-validation
revision `1b7c79b3e1d6713f0648cbe59794fab8b091d245`.

**No repeatable speedup is established.** The first complete-process session
improves 1.18% by marginal medians; the repeat regresses 0.64%. Both paired
intervals include zero, and separate counters do not improve. Keep this factor
on its pushed experimental branch, together with every prior factor and the
earlier outcomes. Canonical website timings are unchanged; Rust parity remains
incomplete.

## Implementation and retained antecedent

The original fuel formula remains authoritative:

`max(1, min(1024, remaining_compute / max(price_compute,1) / 4, remaining_comparison / max(price_comparison,1) / 4))`.

When both positive prices have representable `price * 4096` thresholds and
both remaining allowances meet those thresholds, the result is exactly 1024.
The candidate prepares those thresholds before acquiring the worker mutex.
Inside the transaction, comparisons select the same full batch and two shifts
recover its exact debits. Zero prices, overflowing thresholds or limited
headroom retain the original division path and arithmetic-error order.

Pricing failures stay deferred until the original scope/remaining-allowance
check reaches its callback. Local/root checks, paired ledger commitment,
fourfold headroom, batch bound, funded count and every charged amount remain.
No allowance is minted, reserved or refunded. No heap allocation or persistent
metadata is added. The Mech source, bytecode, Object identity, native Object,
descriptor JSON/compressed image and resource metadata remain byte-identical
to the parent; Object SHA-256 is
`f25ada28ff389713076fcb342b3b13f807741bfda91ca2274e6eb4d8ebc36335`.
IR79, ABI28, work policy66 and the 64 KiB host buffer remain unchanged.

This is an **interaction retest**, not a new mathematical idea. Retained
candidate `36a0d26e05b92f0f3fb21bdbd3605af2108ec882` previously tried the full-batch
threshold shortcut, improved initially and regressed in its repeat. The current
version stores only unit prices and optional thresholds, deriving debit by
shifting and checking the funded addition inside the callback. Its actual
private quote is **40 bytes**, versus **72 bytes in that historical candidate**.
The immediate parent has no equivalent prepared quote. These are stack-value
type sizes, not heap savings or measured stack traffic; LLVM can scalar-replace
their fields.

[The antecedent annotation](retained-antecedent.json) was committed before any
new full-input observations. It preserves both earlier timing sessions and
explains why this smaller-quote variant is tested with the later preparation,
metadata, scheduling and key-validation factors.

## Complete-process results

The [plan](plan.json) and drivers were committed at
`cef716ce863d0747e282643a295f262f11d1d436` before execution. Two independent
sessions use all six balanced sequential orders of Rust, parent and candidate.
All **36 full-input observations** are retained, with no excluded warmups or
outliers. Each execution includes fresh secured startup through process exit,
on 125 million selected bases. No subjects run concurrently.

| Configuration | Session 1 seconds | × Rust | Session 2 seconds | × Rust |
|---|---:|---:|---:|---:|
| Exact upstream Rust #7 | 0.5622 | 1.000× | 0.5544 | 1.000× |
| Decoder-proof parent | 0.7004 | 1.246× | 0.6900 | 1.245× |
| Prepared refill | 0.6921 | 1.231× | 0.6945 | 1.253× |

Median paired log-ratio changes are **−1.08% [−5.66%, +3.17%]** and
**+0.65% [−3.57%, +3.54%]**. Four of six and three of six matched orders favor
the candidate. Descriptive 95% intervals resample whole matched orders 20,000
times with fixed seeds. Paired estimates differ from ratios of marginal
medians; sessions remain separate.

The separate one-million-base prefix has one excluded warmup and three measured
complete processes per executable: Rust **0.02050 s / 1.000×**, parent
**0.11724 s / 5.720×**, candidate **0.08746 s / 4.267×**. This small unreplicated
batch does not establish a prefix improvement. Separate prefix counters below
move in the opposite direction. No prefix observation is pooled with full
input or used to replace its results.

[Session 1](../full-prepared-refill-v1/results.json),
[session 2](../full-prepared-refill-v2/results.json) and
[prefix/build qualification](../prepared-refill-timing-v1/results.json) retain
all observations, deviations, source/input/policy/binary pins and native
reports. Every full Mech execution verifies complete output, seven complete
maps, seven peak workers, five admitted caches and **874,999,961 physical
updates**. Prefix executions verify complete output and **6,999,961 updates**.

## Counters, memory and code

Nine separate full-input counter processes, three per executable, give:

| Configuration | Instructions billions | Cycles billions | User CPU s | Kernel CPU s | Involuntary switches |
|---|---:|---:|---:|---:|---:|
| Rust | 33.151 | 7.970 | 2.37 | 0.03 | 612 |
| Parent | 26.114 | 7.335 | 2.09 | 0.04 | 5,908 |
| Prepared refill | 26.123 | 7.426 | 2.11 | 0.04 | 5,828 |

Instructions increase about 0.04% and cycles about 1.23% in this diagnostic
batch. The kernel CPU median is unchanged. The separate prefix medians are
candidate **1.310 billion instructions / 0.697 billion cycles / 0.17 user CPU s**,
parent **1.255 billion / 0.530 billion / 0.13 s**, and Rust
**0.307 billion / 0.081 billion / 0.02 s**. Candidate kernel CPU rounds to 0.01 s,
parent/Rust to 0.00 s. These counters sum threads and include scheduling
variation; rounded counter elapsed values are not primary timings.

Peak RSS is the median of each original timing process's macOS `wait4` peak.
MB denotes 1,000,000 bytes.

| Configuration | Session 1 RSS MB | Session 2 RSS MB | File MB | Machine-code MB |
|---|---:|---:|---:|---:|
| Rust | 140.40 | 140.51 | 0.756 | 0.347 |
| Parent | 161.55 | 161.60 | 5.468 | 4.304 |
| Prepared refill | 161.49 | 161.42 | 5.468 | 4.307 |

The candidate file is 32 bytes smaller while its code section is 2,352 bytes
larger. Neither a meaningful RSS nor executable-size improvement is established.
[Full diagnostics](../prepared-refill-diagnostics-v1/results.json) and
[prefix counters](../prepared-refill-prefix-counters-v1/results.json) retain raw
observations. No new paused heap capture is needed for the stack-only quote.

Three fresh profiles match the candidate's entire timed code section. Across
4,741 worker observations, 73.74% are generated counting loops, 16.52% active
accounting, 1.24% accounting waits, 4.91% storage helpers, 1.50% helper bridges
and 2.09% other locations/waits. These are sampled stack-location shares,
including waits, not elapsed-time or CPU-time shares.
[Profile partition](../prepared-refill-full-remaining-profile-v1/results.json)
retains complete classification context and the unchanged earlier Rust reference.

[The code audit](code-audit/results.json) retains exact-image runtime assembly.
The parent has a 372-instruction refill body and a 47-instruction callback with
two divisions. The candidate has a 457-instruction refill body and a
63-instruction `Prepared::select` function, with two divisions retained only
on its fallback path. The candidate still calls that function inside the
worker transaction. Static counts and division presence do not establish
dynamic frequencies, critical-section duration or the cause of timing changes.
The audit also compiles the actual new private quote module and extracts the
old field declarations verbatim to verify the 40/72-byte layouts. All tools
are bounded, supervised and serial under the shared mutex.

## Validation and retained state

The exact clean revision passes **385 native checks, two focused checks and
one catalog check: 388 check executions**, with focused-suite overlap and
three existing manual native exclusions. New checks compare the original and
prepared selection at threshold edges, every combination of representative
prices/remaining allowances/funded counters, zero prices, multiplication and
funded-count overflow, and 40,000 deterministic arbitrary cases. They compare
the exact selected batch, both debits, funded count and overflow result.

[Verification](verification.json) recomputes the immutable plan, retained
antecedent, both balanced timing sessions, bootstrap intervals, exact build-input
equality, outputs/updates, profiles, counters, binary sizes, raw assembly and
**89 terminal, reaped, closed-group process receipts**. Compiler source stays
clean and unchanged throughout, all native work is serial under the retained
shared lock, and canonical benchmark data remains unchanged. Run `python3
prepared-refill-v1/verify.py` from this study directory in the qualified checkout.

The branch remains available for future combinations. This result does not
justify replacing the parent as a measured fastest configuration. The larger
remaining target is generated hash-loop execution; neither this study nor the
[input-buffer comparison](../host-input-chunk-v1/README.md) establishes a large
host-support speedup.
