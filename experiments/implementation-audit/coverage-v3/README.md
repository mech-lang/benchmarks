# Exact-source review coverage, v3

The additive [ledger](coverage.json) extends the frozen v1/v2 reconciliation with
the F# static review. It checks every retained source identity and preserves
protected upstream programs and unresolved ownership separately.

The current catalog has 1,070 profiles: 673 editable, 351 protected upstream and
46 unresolved ownership. Of the editable profiles, 334 have static source reviews
and 339 still need them. This is source-inspection coverage, not native execution,
optimization completion, source-count qualification or chart admission.

The F# supplement covers 21 local/derived profiles sharing 17 complete source
bundles. Nine unchanged F# upstream profiles remain protected. Five source drafts
have 58 pending JIT/AOT correctness cases and no compiler/output/timing approval.
Earlier inventories and the v1/v2 builders and reports remain unchanged.
