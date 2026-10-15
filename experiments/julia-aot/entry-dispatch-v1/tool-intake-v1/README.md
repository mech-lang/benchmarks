# Reviewed debugger intake and failed owned capture

The [final intake](tool-intake.json) joins the complete, zero-subject
[static tool observations](../intake-run-v2/report.json) to the selected LLDB,
debugserver, embedded Python 3.9.6, SDK declarations and declared dependency
images. Its 829 physical file pins cover the recorded source and tool inputs.
The [file-only builder](prepare-intake.py) and
[declared dependency record](declared-tool-closure.json) are retained exactly.
No native process was started by that builder.

The seven approved intake capabilities establish the local command interface,
API presence, settings, module UUIDs, 27 breakpoint locations and CodeInstance
layout. They do not establish a successful attach. The declared Mach-O record
preserves ordered physical and OS-managed alternatives, including both arm64
debugserver slices. It does not claim observed dynamic resolution, complete
Python imports, signing trust or runtime source equivalence.

The [prepared plan](../plan-v1.json) was executed once. The
[report](../run-v1/report.json) records the 120-second deadline at
04:20:12 UTC on October 15, 2026: the private debugger endpoint never appeared,
the LLDB client was never launched, and all subject/debugger output and trace
streams were empty. The suspended subject and debugserver were both killed
with SIGKILL and reaped. The [terminal record](../run-v1/terminal.json) retains
all eight artifacts and reports no closure errors. The
[independent review](../run-v1-independent-review.json) verified 830 physical
input pins, the artifact inventory, absent controller/child PIDs, empty child
process groups and an available common mutex after closure.

The seven retained [OS log records](../run-v1-os-log.json) end with
`about to task_for_pid(183)`. No return from that call is recorded. A separate
read-only `DevToolsSecurity -status` observation reported developer mode disabled;
no raw output file was retained for that command. This observation does not prove
that the setting was the sole cause of the stall. The
[next-action record](../run-v1-next-action.json) keeps permission for a machine-wide
setting change pending. Native entry ownership, serialized-IR removal, fallback
closure, AOT classification, timings and chart admission remain unqualified.

[The preservation manifest](preservation.json) maps original paths to public
copies with exact hashes and byte counts. Original receipts, plans and source
files retain their execution-time paths and bytes; these are evidence copies,
not relocated executable plans. The earlier
[failed static intake](../intake-run-v1/disposition.json) and its complete
report-declared artifacts are preserved alongside the later static capture.
Only explicitly inventoried bytecode files inside those captures are included;
unrelated writable HOME, temporary, socket and cache contents are excluded.

External toolchain, SDK, runtime, matching DWARF and Python files remain physical
prerequisites identified by the original pins; their binaries and installations
are not bundled here. The earlier private planning inventory remains identified
by its original digest in the manifest and intake. It is not an observation or
qualification receipt. The builder preserves its original paths for review and
is not a portable reproduction command from this publication checkout.
