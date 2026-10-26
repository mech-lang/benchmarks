# Post-architecture native cleanup

This is the primary evidence study for the cleanup following mech-lang/mech
#935 and preceding the 19 downstream PRs. The audited source is
`01b8b397011b6a774b7d9f730578a4ef92bf30f6`. Its retained public AOT executable
and build receipt in `../native-architecture-consolidation-v1/` are the
before-cleanup subject. The candidate is not fixed or performance-qualified.

`audit/` retains the complete 363-file inventory, exact-body candidates,
256 resolved default-module paths, 19 inherited feature guards, and original
migration/architecture documents with hashes. These records preceded code edits.
They establish provenance and candidate deletions; existing semantic contracts
and exact before/after evidence determine whether a consolidation is acceptable.

Manual window/histogram timings and region inspection are maintained under
`tools/native-compiler-probes/` in this repository. Their exact original Rust
source is preserved. They are diagnostic tools with a pinned test overlay;
complete-process performance qualification remains a separate study gate.

The final plan must pin the actual after-cleanup source and public AOT file,
verify unchanged source/output/resource contracts, and compare before/after
k-nucleotide timings using the retained W/R controls and the same two-session
192-observation acceptance policy. There are zero primary timing samples for
this cleanup. Full raw receipts and unsuccessful attempts remain part of the
study. No historical performance claim is transferred to the new candidate.
