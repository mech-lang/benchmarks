# Removing redundant native arena node bookkeeping

The shared-account snapshot witness supersedes the earlier per-slot native arena census. The account retains admitted caller roots outside the arena and shares claims across aliases. No production caller used the arena-only getter, so maintaining both counts added storage and work without completing caller geometry.

The arena now retains one generation word per slot instead of a generation/count pair. This removes eight bytes of word backing per slot and reduces declared setup work by eight units per slot. `put`, retirement and transfer no longer maintain a second running node sum. The arena-wide sum field and unused getter are removed. These are structural storage/accounting reductions, not measured process-RSS or runtime results.

Type, memory-account, work-ledger, generation and stale-handle checks remain intact. Retirement still prepays its complete ownership bound. The shared snapshot claim remains attached to its actual admitted owner. A caller-held String or taken map stays counted after every arena slot has retired, and the last admitted root releases the claim even if raw unadmitted data aliases remain.

Native work policy44 distinguishes the smaller arena prices from policy43. Typed IR30 and ABI15 remain unchanged. The normal generated path still uses canonical maps; this change does not activate retained-map storage.

Validation passes all 201 native checks, with three pre-existing exclusions. The adapted arena test covers alias insertion, replacement, failed type checks, repeated retirement, transfer, stale handles, wrong work ledgers, external root retention, and complete release. Existing exact/one-short admission, failure atomicity, source/decoded map execution and Object identity checks remain in the native suite. Preceding policy43 Objects are rejected.

The sole subject runs serially under the shared benchmark mutex with bounded owned-process control and a complete cleanup record. Core snapshot and map-library sources are unchanged from the [preceding account-witness study](../account-node-witness-v1/README.md). No quantitative benchmark samples or canonical dataset changes are admitted. Private-builder/native metadata geometry, retained-map routing, full-input qualification and fresh complete-process timings remain unfinished.
