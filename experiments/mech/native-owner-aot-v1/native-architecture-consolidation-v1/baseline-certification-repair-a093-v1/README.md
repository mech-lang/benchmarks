# Canonical source certification repair

PR934 head a093aea452340a70c1e72a1f58bd831f1edef70f changes only the
certification TSV and two dynamic-schema test fixtures. All 422 tests across
the original nine canonical source CI suites pass.

A controlled reversal of only the predicate-type insertion from6e53189b7
restores all ten old fingerprints. That insertion is retained: structural
control requires its Boolean schema. The diagnostic script originally
predicted one mismatch would remain and rejected the passing test in its
own post-test assertion. Raw success, the mistaken prediction, complete
process cleanup, the unused second experiment and exact source restoration
are documented without relabelling that attempt.

The first complete-suite attempt exposes two fixtures that deliberately
require two absent child schemas, including Bool. Their String/I32 replacements
retain the same missing-child, foreign/same-plan execution and arena checks.
No production compiler/runtime code changes in this repair.

The forward-publication receipt proves that the published935 architecture
patch is byte-identical to its prepared patch while preserving the published
history. The installed m4 receipt addresses only the local build-tool search
path. Timing protocols and compiler optimization settings are unchanged.
