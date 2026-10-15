# Exact count review binding

`count-review-v1.json` admits only the canonical ownership and counts of the
fifteen source files identified by the retained proposal. It preserves the
proposal's original unreviewed status and all original ledger bytes. The ten
workload bundles include their full authored support; runtime, required work,
full timing and chart admission remain separate gates.

The additive `tools/qualification/rebol_reviewed_count_ledger.py` exposes
`bind_ledger(ledger, review)`. Its caller must authenticate the original ledger,
this helper and the count review by their retained hashes. The helper validates
the exact fifteen identities and paths, approved rule, count-only disposition,
proposal/rule references and ten bundle totals. It returns copied ledger data
with only `reviewed_source_sha256` fields bound from the review. An already
approved different digest is rejected. The original module and nested source
decisions remain unchanged.

The helper performs no file reads or counting. The existing `count_source`
must still hash the actual bytes and replay every exact owner; qualification
must still compare that complete result with the retained proposal and join
the measured source identities. The qualification adapter is not wired to this
helper yet.

Focused pure tests are in
`tools/qualification/test_rebol_reviewed_count_ledger.py`. They cover isolation,
missing/swapped identities, invalid digests, conflicting prior approvals,
scope/rule/reference changes and inconsistent bundle arithmetic. Their actual
execution result is recorded separately; no native commands are part of these
tests.
