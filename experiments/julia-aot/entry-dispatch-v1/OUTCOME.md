# Julia entry diagnostic outcome

Julia AOT remains experimental and is not admitted to the benchmark catalog.
The retained code-generation-disabled pilot produced the expected output, and
static inspection identifies native benchmark bodies. The exported C ABI wrapper
can select a target at runtime; correct output and native symbols alone do not
exclude an interpreted fallback.

The [second owned diagnostic](run-v2/report.json) reached its 120-second deadline
on October 15, 2026 at 21:40 UTC, before the debugger endpoint appeared. Developer
mode was independently observed enabled, the account belonged to both `admin`
and `_developer`, and execution used the elevated tool context. The
[system log](run-v2-os-log.json) ends immediately before `task_for_pid(40355)`.
It contains no explicit authorization denial. Enabling developer mode therefore
did not resolve the transport failure; its root cause remains unestablished.

The [third diagnostic](run-v3/report.json) attempted a one-second stack capture
of its birth-verified owned debugserver. [Kernel-stack capture](run-v3-kernel-stack-attempt.json)
exited with code 77 because macOS requires root. The bounded
[user-space alternative](run-v3-user-stack-attempt.json) timed out after ten
seconds and produced no stack. The diagnostic itself reached its original
120-second deadline. Neither attempt produced subject output or trace events,
and neither supplied a timing sample.

Independent closure checks for [the second](run-v2-independent-review.json) and
[third](run-v3-independent-review.json) diagnostics verified all 830 input pins,
all eight retained artifacts, the released common timing mutex and the absence
of their owned processes and groups, including zombies. Both started children
were killed and reaped in each attempt. Earlier captures remain preserved.

The [administrator-assisted capture helper](admin-stack-capture-v1.py) prepares
one fresh bounded diagnostic and captures only its registered debugserver. It
requires an existing administrator authentication in the same terminal, changes
no security settings, and has not been executed. Native-path and fallback
qualification, complete-suite timing and catalog admission remain outstanding.
