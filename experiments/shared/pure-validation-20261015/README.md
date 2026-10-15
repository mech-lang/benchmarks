# Pure validation records

All 250 pure test methods across 21 scripts passed after the three fixture
repairs recorded in the [summary](post-prolog-pure-validation-summary-v1.json).
The [initial run](post-prolog-pure-validation-run-v1/report.json) retains its
three script failures and 213 passing methods. The
[repaired run](post-prolog-pure-validation-repaired-v1/report.json) retains the
passing Julia controller 4, Rebol qualification 17 and Rebol reconciliation 16
methods. Both directories include every original stdout and stderr capture.

These are byte-for-byte copies of the original private records. Their absolute
paths, original statuses, command arguments and private provenance have not been
rewritten. The summary's stdout/stderr names refer to the initial run directory;
the three repaired scripts have their captures in the repaired run directory.
All commands used the retained Python with `-I -S -B`.

This validation performs no native intake or benchmark execution. It does not
qualify compiler or debugger compatibility, actual source projections, native
outputs, runtime/source equivalence, full timings or publication. The original
Julia fixture's initiating error was not retained, so the socket-bind cause
remains an inference; its original failed stderr remains available.

[source-docs-transfer-paths.txt](source-docs-transfer-paths.txt) lists the exact
additive source, test, fixture and document paths associated with these suites,
relative to the evidence repository. It includes diagnostic and native source
files needed by the packets; inclusion is not a claim that each was executed.
The inventory excludes frozen shared helpers, archived/measurement inputs,
completed native output directories, and publication catalogs/history. Those
remain external dependencies and are not selected for replacement. Transfer
this validation directory separately with that source inventory; no transfer
or publication is performed by this record.
