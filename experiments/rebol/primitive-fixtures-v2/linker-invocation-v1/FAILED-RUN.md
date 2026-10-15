# Stopped primitive fixture run

The linker-option continuation started four native processes. Diagnostic interposer compilation, arithmetic, and formatting passed. The regex fixture then exited 1 at its “LF multiline boundary” assertion; the remaining 15 fixtures were not started. The [original report](run-v1/report.json), [terminal](run-v1/terminal.json), and [durable command evidence](../../../shared/owned-jobs-v1/owned-jobs/rebol-primitive19-linker-v1/terminal.json) retain the failed status.

The [independent closure review](failed-stage-review-v1.json) replayed 5,124 input pins, the exact 46 run artifacts and 8 durable files, and the successful compiler dependency/image checks and arithmetic/formatting outputs. All six recorded process identities and their groups were absent; all ten prerequisite/cohort leases were acquired and released. The three successful captures and interposer outputs are preserved for explicitly checked reuse.

[Source diagnosis](source-diagnosis-v1.json) identifies an unescaped Rebol caret in the two multiline fixture patterns. It also records separate caret errors in two original regexredux substitution patterns. Original sources remain unchanged; no repaired fixture or benchmark was executed. Full primitive correctness, benchmark work, source counts, timings, and chart admission remain unqualified.
