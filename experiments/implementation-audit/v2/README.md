# Current implementation-ownership inventory

`tools/audit_owned_implementations.py` now writes this v2 inventory, preserving
the original v1 inventory used by frozen review packets. The schema adds a
complete external application-identity guard: runner/adaptation metadata cannot
authorize modifying an application whose bytes match published source.

The inventory retains historical origin classifications separately from edit
protection. Thus a record may preserve its `derived-adapted` metadata while
`preserve_upstream_source` is true and `protection_metadata_conflict` is explicit.
No AI attribution is inferred or rewritten. This is a source-editing boundary,
not a new performance, source-count or native-runtime qualification.

Use the additive [v4 coverage reconciliation](../coverage-v4/README.md) for current
source-inspection totals, including C#, F# and other supplements. The base
inventory's audit statuses alone do not include every later static supplement.
The [published-source evidence](../upstream-protection-v1/README.md) verifies the
34 newly protected profiles against captured original sources.

```sh
python3 tools/audit_owned_implementations.py --check
```
