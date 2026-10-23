# Canonical native compiler integration

The current compiler is `bbd66acb9b3beacdc95356084df259ca172c8b98`, integrating
Mech PR #909 at `1e9e6aac12170dbfcc9686f95909a11e0804a8bb` with the record
compaction and completed-buffer reuse changes at
`fca1ba1f7462a555eb56833ad32135408a140a72`.
Branch: `codex/benchmark-canonical-native-integration`; draft runtime PR: #910,
stacked on `codex/canonical-native-cli`. Neither PR is merged upstream.

Relative to the current #909 head, the remaining diff contains only the record
runtime and an additional generated-launcher resource-image boundary assertion.
All canonical native production code and updated scalar Match/iteration tests
match upstream. The record runtime still matches its previously qualified source.
The upstream follow-up preserves full-width integer constants in build-owned
images; it is a correctness fix, with no new timing claim.

`validate_final.py` prepares the exact clean head and checks record-runtime tests,
canonical secured execution, and the public compiler tool build.
`corrected_contracts.py` then checks scalar Match/iteration lowering, native image
wire preservation, emitted query/histogram kernels, and same-binary policy
contracts. `qualify.py` refuses to run until both gates pass. It builds the
unchanged idiomatic nucleotide fixture through public source and decoded-bytecode
routes, checks generated pins, requires byte-identical executables, checks bounded
outputs and missing-grant denials, and qualifies complete standard-input output
before collecting samples. All subjects inherit the existing common timing mutex;
the lock is never replaced.

Tool preparation uses normal dev/test profiles with debug information removed.
The record-runtime gate reuses its completed release math cache. Timed application
builds explicitly use release Rust shell/libraries and Cranelift Object
`opt_level=speed`. Compiler-tool optimization is separate from generated-code
optimization; tool compilation and source compilation remain outside timing.

The standard input contains 250 million total bases and 125 million bases in
THREE. Fresh-process measurements include startup, secured input acquisition,
compiled computation, output, security report publication, and shutdown. Build
and parent-side validation are excluded. Finite policy values and all raw
observations are retained. These are warm filesystem-cache measurements.

Current validation status is in `validation-v2/results.json`, followed by
`corrected-contracts-v1/results.json` and `qualification-v1/results.json` when
available. No result is admitted into the canonical dataset or website merely
by creating this integration record.

The initial merge was `4c377322759352f0886e236e182f7245af5e5d00`; local test-only
corrections followed at `3864005a46a8032c183308b7ddc5b6e0079b53c7`. Upstream's
later correction was then merged, resolving duplicate fixes in favor of its
stronger assertions. `ci-inspection-v1` retains the original failing CI evidence.
`validation-v1` is an intentionally cancelled preparation attempt, not a passing
qualification: the complete compiler math catalog was being optimized before
any tests or timings. Its owned group was terminated, reaped and closed without
cleanup errors; its completed math cache remains available. The older frozen
emitter was restored unchanged. `preparation-change-v1` records the profile
decision, cancellation, first conservative ownership-guard refusal, and closure.
Historical M1 measurements from #909 remain attributed to their original
revisions and hardware.
