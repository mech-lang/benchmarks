# Janet native bounded validation

The audit checkout was restored from pushed commit `8ee25bda` after the prior
checkout and build products disappeared. The prior common mutex path was absent;
this run created a new mutex instance and records its inode. It did not unlink an
existing lock or claim that the old stalled process was reaped by this controller.
The verified release archive was restored and its bundled sources rebuilt with
the recorded command. The resulting Janet binary has the identical retained
SHA-256 `6732dd0bb37de61676bbdb3a8d3fb14b76b3a39fc9852e2b1f060dd21a9bc765`.
The downloaded executable was never invoked.

`run.py` hashes every frozen preparation input before starting. Its child waits
for a parent gate: the parent owns its forked PID and kernel birth identity before
allowing session creation and exec. Each invocation inherits the common mutex,
captures complete streams into regular files, has a 30-second deadline, and must
be reaped with a closed group before another invocation. The retained supervisor
provides bounded kill/reap cleanup. `test_controller.py` checks normal output,
nonzero exit and deadline termination with group closure. These tests cover those
paths, not every possible signal or uninterruptible-kernel failure.

The original `run-v1` records a version preflight and all 149 corpus cases:
141 success-output passes, one regex failure, and seven malformed-input captures.
All 150 invocations were reaped with closed groups and no cleanup errors. The
failure is preserved: Spork's `find-all` counts overlapping candidates, whereas
the workload requires non-overlapping matches.

The new `../source-v3/regexredux.janet` overlay uses the same unmodified regex
library and searches again after the end of each match. All nine specified
motifs consume eight bytes. It does not change the replacement chain. It retains
the v2 source's Apache-2.0 authorship/license and consulted predecessor provenance
in `../source-manifest-v1.json`; the correction was authored by Codex GPT-6 family,
with exact serving model unknown. `rerun_regex.py` checks the original input pins,
records the new source identity and validates all seven regex cases independently.
`regex-run-v1` contains seven passes, including the formerly failing overlap case.

Taken together, the v2 implementations for nine workloads and the v3 regex overlay
pass all 142 success-output contracts. The original manifest still describes v2;
this packet explicitly records the overlay rather than rewriting historical
source identities. Seven malformed-input captures remain unqualified. Complete
library-loader closure, required-work review, qualified source measures,
full-size output validation and serialized whole-process timing remain pending.
There are no Janet benchmark timing samples or chart admissions in this packet.
