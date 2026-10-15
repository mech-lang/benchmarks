# Extension build and first load observation

The [four-process plan](../plan-v1.json) ran serially on October 15, 2026.
Both compilations and the layout/export probe passed. The interpreter's first
load attempt exited 1 at the read of the common Rebol fixture, before exercising
the extension commands. The [original report](report.json) and
[terminal](terminal.json) retain their `stopped-unqualified` status.

| Command | Exit | Observation |
| --- | ---: | --- |
| Build extension | 0 | Dylib, dependency rule and linker map retained |
| Build layout probe | 0 | Executable, dependency rule and linker map retained |
| Layout and exports | 0 | Expected layout; `RX_Init`, `RX_Quit` and `RX_Call` resolve to the built dylib; GMP 6.3.0 and PCRE2 10.49 observed |
| Load nine commands | 1 | Process-local Rebol security policy denied reading the external common fixture |

The [probe output](02-layout-and-exports/stdout.bin) records loaded image names,
layout values and library versions. The [load error](03-load-nine-commands/stderr.bin)
is retained verbatim. This establishes the probe's observed binary layout and
exports, but does not qualify interpreter behavior or supply benchmark timings.

The [independent closure review](independent-closure.json) replayed the input
pins, native captures, six build artifacts and the
[durable job](../../../shared/owned-jobs-v1/owned-jobs/rebol-extension4-v1/).
All six recorded processes and their groups were absent, and all six leases
were available. The successful builds and probe can be reused unchanged for a
separate load-only continuation. The failed producer record remains immutable.

The [typed-image adapter](../typed-image-closure-v1/) allows regular Mach-O dylib
roots in the static dependency walk. The concrete
[toolchain intake](../toolchain-intake-v1.json) and its
[builder](../intake-builder-v3.py) retain the selected headers, tools and linked
library provenance. The original [build specification](../BUILD.md) describes
the pre-execution plan; this directory records its actual outcome.
