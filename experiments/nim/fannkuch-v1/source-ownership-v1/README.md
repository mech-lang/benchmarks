# Proposed exact-source Nim ownership

These four ledgers are manual source proposals only. No native Nim frontend,
normalization tool, application or benchmark was executed. Every ledger binds
the exact candidate bytes, exact parent bytes and retained policy evidence.
The proposed retained counts are not approved application counts:
`application_loc` is null and `independent_review_approved` is false throughout.

The compact parent has 35 nonblank physical rows and 35 retained units. Its
guarded library-expression candidate has 31 of each. The parallel parent has
64 physical rows and 71 retained units. The unchanged packed declarations add
two units for the two-field `Result` type, four for the four-field `Job` type,
and one for the independent thread pragma on `run`. These same seven extra
units are proposed for each parallel candidate. The guard-only source adds one
written conditional. Guard plus standard reversal replaces the ten-row copy
and manual-flip block with six written rows, removing four units overall.
The scalar casts in the byte representation remain expressions inside existing
statements; they introduce no new written statement owner.

Every nonblank application row has an owner; dedentation adds no written
closer. This extends the retained source-local convention exactly as described
in its saved review and event arrays. It does not establish a general grammar,
uniform cross-language logical metric, accepted syntax, or compiler lowering.
Independent review and native/build qualification remain required.

The unified diffs bind the source changes for review. The library module is
existing generic Nim support and has its own unchanged source/license snapshot
in the parent packet's `vendor/` directory. Its operations are not an authored
whole-benchmark helper hidden from the application total.
