# Diagnostic compilation stopped before primitive fixtures

The first scheduled command exited 1 on 2026-10-15 UTC. Clang 22 rejected the
absolute-path `-fuse-ld=` spelling under the retained `-Werror` policy and
requested `--ld-path=`. The [raw diagnostic](run-v1/00-compile-io-interposer/stderr.bin)
and [process receipt](run-v1/00-compile-io-interposer/process.json) are preserved.
No compiler outputs were created and none of the eighteen Rebol fixture
processes started.

The [independent closure](failed-stage-review-v1.json) verifies the failed report,
all 5,085 recorded input pins, eighteen prepared input files, owned process/group
cleanup and release of nine leases. The [producer terminal](run-v1/terminal.json)
remains `stopped-unqualified`. No primitive, benchmark, work, count, timing or
chart admission follows from this attempt. Any corrected invocation requires a
separate entrypoint and plan; the original source, plan and failure stay intact.
