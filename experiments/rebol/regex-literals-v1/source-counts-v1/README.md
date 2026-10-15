# Corrected regex source counts

This additive packet applies the existing fifteen-source owner ledger and
checker to the corrected `regex-literals-v1/main.reb`. The archived regex main,
original proposal, original count admission and original binding helper remain
unchanged. Only the regex main's source path and exact digest are substituted;
the owner decisions, fourteen other sources and ten bundle memberships remain
the same.

The corrected main still has 59 canonical units and 56 nonblank, noncomment
physical lines. Its complete bundle remains 469 canonical / 375 physical units.
The two relocated helper paths are single statements. The additional carets
occur inside existing literal-data rows and introduce no executable owners.
The corrected primitive fixture is validation material, not an additional
authored application source.

`proposal-v1.json` retains the original unreviewed proposal schema and records
the exact regex substitution. `count-review-v1.json` separately admits only
these exact source counts. It does not establish native output correctness,
required work, runtime equivalence, timing or chart admission.

The additive `tools/qualification/rebol_regex_reviewed_count_ledger.py`
validates this proposal/review route and returns an isolated ledger view. Its
only allowed replacement is the original regex path/digest to the reviewed
corrected path/digest. Unknown prior approvals reject. All other digest,
identity, reference and bundle checks are retained from the original binding
helper. Callers must pin the helper, original ledger and count review, then
replay the existing `count_source` and compare its complete owner projection.
No qualification adapter is changed by this packet.

The focused binding tests and actual owner replay are recorded separately in
`validation-v1.json`; neither launches Rebol, a compiler or a benchmark.
