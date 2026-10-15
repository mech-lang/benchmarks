# Bounded Pi facade-call observation

[`pidigits.reb`](pidigits.reb) is an unexecuted diagnostic at the retained N27
case. It copies the original Pi main's lines 4–46 contiguously and adjusts only
the two loader paths to reach the same retained helpers. The original main,
arithmetic facade, loader, C extension and selected image remain unchanged.
The [statement map and oracle contract](pi-source-map.json) record the exact
source ranges and historical reference pins; new source hashes are not frozen.

The preamble saves the original `big/floor-divide` function and replaces that
field in this diagnostic's freshly loaded facade with an observer. Each call
copies its complete operands and current `q`, `r`, `t`, `k` and emitted-digit
state, invokes the saved original function exactly once, copies the complete
returned binary, and returns the original result value. It neither recomputes
the quotient nor substitutes a derived value into the recurrence. The two
original quotient statements are untouched. Their recorded source-line labels
15/16 come from alternating call order and the source mapping, not a native
stack or machine-instruction observation.

After the original stdout write, the diagnostic emits an ASCII TSV sidecar to
`MECH_REBOL_PI_OBSERVATION`. It requires an absolute path that does not already
exist. The additive [three-diagnostic controller](../../../tools/qualification/rebol_work_observations.py)
supplies that path inside a fresh artifact directory, pins the exact diagnostic
and unchanged source/image bundle, preserves the raw sidecar and uses the
existing bounded observer policy. The [stage README](README.md) describes its
prerequisites and limits. The controller is a source draft; its plan, captures
and tests remain pending. The diagnostic source alone supplies no exclusive
file-creation or process-ownership proof, and no native launch has occurred.

Independent review must parse every complete decimal operand and result with
unbounded integers, verify both numerator equations and both floor quotients,
and replay each equal/unequal branch from the initial state. Each adjacent
15/16 pair must have the same state and denominator. The replay must end after
exactly 27 emitted digits, contain an actual beyond-u64 operand witness in both
calls of a pair, and reproduce the complete pinned 45-byte output. Missing,
duplicate, malformed, truncated or extra observations fail; matching printed
digits alone is insufficient. The JSON contract gives the exact equations and
row format. [`pi_oracle.py`](pi_oracle.py) implements this pure integer review;
[`test_pi_oracle.py`](test_pi_oracle.py) contains twelve focused synthetic test
methods. Both are source drafts and have not been imported or executed. The
tests cover recurrence state, complete operands, floor versus truncation,
sequence and parsing faults, the beyond-u64 witness, and full output identity.
Synthetic rows are test inputs, not native observations. The oracle accepts
complete byte strings through `validate(stdout, stderr, exit_status, trace,
expected)` and performs no filesystem reads or process operations. Its result
keeps native ownership and all downstream admission gates false.

This can support a bounded observation of both source-level facade calls once
the actual capture and source/image identity are independently reviewed. It
cannot establish the number of native machine divisions, all GMP internals,
unmodified-main execution, full-size scaling or timing. All work, runtime
source-equivalence, count, timing and chart gates remain false.
