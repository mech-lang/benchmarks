# Scoped-read load observation

This [one-process continuation](../load-only-plan-v1.json) reused the successful
extension build and layout probe from [the original stage](../run-v1/README.md).
The command added process-local read exceptions for the two pinned Rebol helper
paths, leaving the benchmark sources, C extension and compiled image unchanged.
No compilation or benchmark timing ran.

The interpreter passed the earlier file-read failure, then exited 1 while
importing the dylib. Its [stderr](00-load-nine-commands-scoped-reads/stderr.bin)
reports a missing REBOL script header at the dylib path. There was no stdout.
The [report](report.json) and [terminal](terminal.json) remain
`stopped-unqualified`; no extension command behavior is qualified by this result.
Extension import dispatch requires further diagnosis.

The [independent closure review](independent-closure.json) verified all 5,011
input pins, original prerequisite inventories, new capture and durable-job
artifacts. All three recorded processes and their groups were absent, and all
seven leases were released. The two failed load observations and the successful
build artifacts remain separate, immutable records.
