# Completing retained Lua coverage

The Lua publication entry point is
`tools/qualification/import_lua_retained_publication_target.py`. It retains the
original saved-evidence reviewers and pins while writing only to a distinct
publication checkout. The existing nine measured Lua workload groups are
mandatory; a partial-suite aggregate may be absent. Admission preserves that
absence as `aggregate_change.before: null` and creates the first ten-workload
aggregate from the qualified endpoint coordinates. An existing nine-workload
aggregate is expanded without changing its other metadata.

The exact four pi implementations, their complete application-plus-GMP-helper
counts, twelve subject observations and six matched controls are unchanged.
LuaJIT records, other languages and all benchmark baselines are preserved.
Any new minimum requires separate review.

The additive `lua_retained_publication.py` leaf retains the original candidate
validator. `tools/normalization_history_v2.py` replays both absent and present
prior aggregate cases and all earlier admissions. The original publication,
history and target-adapter files remain immutable historical dependencies.

Use the flags documented in
[TARGET-CHECKOUT-V2.md](../../shared/retained-publication-v1/TARGET-CHECKOUT-V2.md)
with the Lua entry point, `--cohort lua`, and its exact `--adapter-sha256`.
Retain exact copies of both additive modules and the adapter in the publication
checkout. Create fresh preview and apply paths, then pass all six digests from
that preview when applying. The publication verifier must use
`normalization_history_v2.py` to replay the resulting history. Existing
successful receipts and failed preview attempts are preserved.

Source review and synthetic tests do not perform physical prerequisite replay
or application. Actual preview and apply still reproduce the candidate under
the original evidence lock, verify every copied public link and dependency,
and retain the existing rollback and final-closure checks.
