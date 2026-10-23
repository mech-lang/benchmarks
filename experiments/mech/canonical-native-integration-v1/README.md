# Canonical native compiler integration

This experiment integrates Mech PR #909 at
`c5b0b3a35b7537358361529aa5a6148464ec415d` with the record compaction and completed
buffer reuse changes at `fca1ba1f7462a555eb56833ad32135408a140a72`.
The resulting compiler commit is
`4c377322759352f0886e236e182f7245af5e5d00` on
`codex/benchmark-canonical-native-integration`.

A test-only follow-up at `3864005a46a8032c183308b7ddc5b6e0079b53c7` aligns
two inherited failing CI checks with the current scalar IR and prepared-resource
launcher. It strengthens same-object comparison to include the descriptor and
resource images. `corrected_contracts.py` must pass its dedicated final-head
checks before `qualify.py` can collect timings. Production compiler code is
unchanged by this follow-up.

The merge preserves PR #909's canonical native implementation exactly and changes
only `hosts/gpu/src/sequence/runtime.rs` relative to its head. That file retains
the previously qualified record runtime changes exactly. PR #909 remains
unmerged upstream. Its historical M1 measurements remain attributed to their
original revisions and hardware.

`validate.py` serially checks the retained record runtime, canonical secured host
execution, and the release public compiler build. It preserves and restores the
older frozen emitter used by previous experiments, storing the integrated emitter
separately. `qualify.py` then builds the unchanged idiomatic nucleotide fixture
through the public source and decoded-bytecode routes, checks generated pins,
requires byte-identical executables, checks bounded outputs and missing-grant
denials, and qualifies complete standard-input output before collecting samples.
All subjects inherit the existing common timing mutex; the lock is never replaced.

The standard input contains 250 million total bases and 125 million bases in
THREE. Fresh-process measurements include startup, secured input acquisition,
compiled computation, output, security report publication, and shutdown. Build
and parent-side validation are excluded. Finite policy values and all raw
observations are retained. These are warm filesystem-cache measurements.

Validation and timing status are recorded in `validation-v1/results.json` and,
when available, `qualification-v1/results.json`. No result is admitted into the
canonical dataset or website merely by creating this integration record.
