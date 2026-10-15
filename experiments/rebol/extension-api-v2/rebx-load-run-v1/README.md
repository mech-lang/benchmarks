# Extension load with the supported suffix

The [one-process plan](../rebx-load-plan-v1.json) completed successfully on
October 15, 2026 at 04:44 UTC. The unchanged smoke exercised all nine general
extension operations, including signed arithmetic, byte matching, fixed
formatting and raw-byte I/O. Its [stdout](00-load-nine-commands-scoped-reads/stdout.bin)
is exactly `00 80 ff` followed by `ok extension-load-v2` and a newline; stderr
is empty and the native process exited 0.

The loaded `.rebx` file is a regular, byte-identical copy of the previously
built dylib. Both files have SHA256
`245e6834c1719e15f888af5ac073854f917bd685ae0ca2dee0eff095028a8539`.
Only the image path in the environment changed from the previous scoped-read
attempt. The [source diagnosis](../extension-import-v1/source-diagnosis.json)
records why this runtime recognizes `.rebx` as an extension while treating
`.dylib` as source. No recompilation or benchmark-source change was needed.

The [report](report.json) and [terminal](terminal.json) preserve the actual
observation separately from the original build/probe success and both failed
load attempts. This smoke result is not a benchmark timing, a complete primitive
test suite, or a proof of runtime/source equivalence. Bounded workload checks,
required-work checks, source counts and full measurements remain separate.

The [independent closure review](independent-closure.json) replayed 5,031 input
pins and all prior/current artifact inventories. All three new process IDs and
their groups were absent, and all eight leases were released. The observed RSS
peak is retained without claiming complete memory-usage measurement.

The [combined review](../extension-import-v1/combined-extension-review-v1.json)
qualifies the exact extension ABI, layout/export and nine-operation load scope.
It joins four successful logical stages from six actual native attempts and
retains both failed loads. All full-suite, work, source-count, timing and chart
admission gates remain false.
