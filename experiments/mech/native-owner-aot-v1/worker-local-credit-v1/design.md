# Finite paired worker credits

This experiment changes distribution of the existing worker-group reservation. It does not create a root allowance, enlarge a source call cap, change a batch size or replace a source map operation. The parent is `630921324a65c385cf63e871d3241dbb0847b8d6`; join/map fusion remains an independent unpromoted experiment.

## Eligible debit

The existing packed-map refill derives a paired full-batch compute/comparison price from its actual current capacity, length and source width. Its original selector chooses 1,024 visits only with four times that full price remaining in each dimension. The new path applies only to a representable nonzero full quote with a representable next funded count, outside active call scopes and on a parent-backed worker account. Other cases retain the exact synchronized selector, including its arithmetic and error order.

A worker reserves up to 64 repetitions of this actual paired quote. Each repetition still pays exactly one original full batch. One atomic repetition count commits both u64 prices together. No dimension is truncated to fit the atomic word: the potentially very large prices remain immutable u64 values in the protected quote. Four remaining repetitions in the exclusive reservation prove the original global headroom condition at the debit point. Worker-local limits are independently checked before the atomic commit.

The generated source loop, its 1,024-visit decrement and its precise continuations are unchanged. A price change retires the old quote before another is installed. A small or uncertain allowance returns to the ordinary selector rather than shrinking a batch to fit a private quota.

## Accounting invariants

For each dimension, let `S` be settled group work, `p[i]` a quote's original price, `C[i]` its reserved repetitions, and `k[i]` its successful atomic debits. Then:

- Actual spent work is `S + sum(p[i] * k[i])`.
- Spent work plus outstanding unused credit is `S + sum(p[i] * C[i])`, which never exceeds the original group limit.
- A successful increment of `k[i]` pays both dimensions before emitted code resumes. The unique local account receives the same original debit.
- Settling atomically seals the slot, adds `p[i] * k[i]` to `S`, and removes `p[i] * C[i]` from reservations. Only the unspent difference becomes available again.

Shared allocation, reclamation and retirement use the existing escrow mutex. The admitted steady path uses its worker's own atomic slot. Slots are aligned to 128 bytes to avoid sharing a conventional 64- or 128-byte cache line between workers.

When a peer lacks sufficient free credit, unused held credit is sealed and recovered before an authoritative denial. Ordinary checked charges also recover reservations if they obstruct an otherwise valid charge. Exact remaining-work queries settle active credits first. Active call caps, root restrictions and foreign scopes retain their existing checks.

Only the unique owner resets a sealed slot, under the mutex and after its preceding atomic attempt has completed. Reclaimers seal slots without resetting them; there is no live old attempt that can observe a replacement slot. More than 32 simultaneous loans use ordinary execution for excess slots. The native scheduler's existing maximum remains 32; the benchmark still runs seven workers.

Closing a group seals and folds every registered slot before reconciling to the parent. Successful debits survive errors, worker unwind and cancellation. Attempts after sealing cannot consume old credit. The registry and pool stay admitted until their last owners retire.

## Memory and qualification

Group metadata includes the registry, the aligned atomic pool and both Arc allocations. The pool's Arc header padding is included through its actual allocation layout. Worker-account backing is admitted before the transferable loan is consumed. Constructor feasibility covers all simultaneous worker accounts, the group and the existing fixed child setup inventory. The scheduler's structural node inventory includes the extra pool owner.

The protocol suite exercises large paired prices, a steady sequence without repeated shared locking, idle-peer reclamation, ordinary debits, independent comparison denial, exact remaining observations, changed prices, local/call/foreign caps, early close, close races, concurrent exhaustion, unwind, excess-slot fallback and complete memory retirement. A compiled-source test compares serial and seven-worker outputs for original and decoded artifacts, changed inputs and all seven counting widths, checks every original update, and requires nonzero actual credit counters.

The first full regression attempt exposed an old fixture whose 4 KB view no longer fit the correctly admitted metadata. Its correction tests the exact worker-account claim and a one-byte-short failure, retaining the stricter child view and original work allowance. The failed receipt is preserved. A separate initial admission filter selected zero tests and is not qualification evidence; the corrected filter and full suite must pass.

## Measurement contract

The Mech source, bytecode, complete guest object, descriptor and resource image must match the retained parent. IR81, ABI29, work policy68 and original body prices remain. The new statistics add ordinary setup metadata rather than loosening work limits. Full runs retain all seven complete hash tables, default growth, all 874,999,961 original updates, seven workers and secured startup through exit.

Two predeclared balanced sessions run the credit candidate, independent parent and exact upstream Rust sequentially under the common lock. No full-input warmup or outlier is excluded. Every candidate execution must report actual credit claims and charged batches. Exact-text profiles, hardware counters, binary sizes and peak RSS are evaluated separately from primary elapsed times. No speedup or Rust parity is asserted in this design document.
