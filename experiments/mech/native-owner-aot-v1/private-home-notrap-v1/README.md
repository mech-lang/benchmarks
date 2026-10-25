# Nontrapping private program homes

This independent experiment adds `notrap` only to three owner-proved private storage classes: the error-origin word, appended borrowed-view metadata and appended non-map scalar-loan words. Source bytes, row offsets, map payloads, ordinary source values and callback arguments/results retain their previous contracts. Mutable state remains mutable; no readonly, alignment or arbitrary-movement promise is introduced.

Source [cfd54ab14d](https://github.com/mech-lang/mech/commit/cfd54ab14d6c016efba2a539d98626b1b15bf6bb), branch `codex/native-private-home-notrap`, follows selective-field parent `2e58f2abdf`. IR90 identifies new emitted instructions; ABI32 and work policy69 remain unchanged. Prior IR89 images are explicitly rejected. The retained good byte-table build `8946ccbae9`, ordinary control `bdb3c511c` and exact protected Rust #7 executable remain independent controls.

## Ownership and observable behavior

The [complete call-site audit](ownership-audit-v2.json) pins source-file hashes and the installed Cranelift 0.131.3 contract. The typed arena projection exactly covers its owned allocation and initializes every u64 lane before exposure. Checked layout additions reserve the metadata within the locals bank. The initialized Frame and projection remain live across each synchronous entry; invalidating a source loan clears metadata without freeing its private homes. Program-only layout derivation prevents these flags from affecting other image kinds.

Opaque helper calls remain full memory barriers. Bounds checks, exact failure sites, pauses, loan retirement, finite body prices and ordinary fallback remain. Non-map Tail accesses cover three words; map branches that use additional callback words retain default flags. The promise applies only at each existing program point and grants no permission to speculate an access across control flow.

The differential reference disables only `notrap` while retaining the existing alias regions. Both that reference and fully default flags are compared with optimized code using original and decoded programs. Incremental character delivery and first-EOF windows cover ASCII, Unicode, CRLF, empty and incomplete input. Successful snapshots, first errors and required/allowed finite-work reports agree, with complete owner and loan retirement.

Final clean-source validation passes 406 native tests, 30 line-storage tests, 36 finite-credit tests, one catalog test and eight focused window tests. Three existing manual native tests remain ignored. Every validation process is reaped with a closed group and no cleanup errors.

## Measurement plan

[Plan](plan.json) predeclares two balanced five-subject sessions, ten Williams orders per session and 100 complete-process observations. Each subject has ten observations per session. The second session reverses the order list. All processes remain serial under the original shared mutex, with no excluded full-input warmup or outlier. Mech includes secured startup through exit and retains seven complete maps, 874,999,961 physical updates, 854,497 credited batches and seven workers. No dataset timing is replaced.

Static inspection is a separate gate before primary timing. It must retain original plans, visits, layouts and finite prices, inspect actual root instructions and verify all unrelated nonentry bodies against the retained controls. Profiles and hardware counters are separate diagnostics and cannot replace primary timing observations.

## Assembly decision

The [exact object inspection](code-inspection.json) finds all ten generated function bodies byte-identical to the selective-field parent. Root code remains 43,596 bytes with SHA-256 `b052e09f1edba5bfd1e690cfe255f6a4a92d95c4619d53a1bc7c892efc0df95e`; instruction, load, store and opaque-call counts do not change. All original source plans, visits, layouts and finite prices remain identical. Object metadata still identifies IR90; identical function bodies do not imply an identical whole object or final host binary.

The [review decision](code-review.json) therefore closes the gate without executing the predeclared 100-observation full campaign. This contract is correctness-qualified and retained as a compiler foundation, with **no claimed performance improvement**. The same source has nine measured one-million-base prefix executions after three excluded warmups; those qualification observations are retained separately and do not substitute for a full-input result. The prepared full-timing procedure was not executed.

The next experiment targets a compact immutable mapping plan, shared between ordinary mapping and joined transform/copy, with exhaustive ASCII equivalence and the complete table retained as fallback. Rust parity remains unproved.
