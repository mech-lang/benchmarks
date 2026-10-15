# Complete bounded correctness

All 149 shared-corpus cases have passed independent replay: 142 successful-output
cases and seven expected invalid-input rejections. The final eight cases ran
serially and passed without repeating any previously accepted case.

The [combined review](combined-bounded-review-v1.json) joins 23 preserved passes,
117 passes from the tree-corrected continuation, the separately accepted quoted
rejection, and eight new captures. There were 150 native attempts in total. The
original tree failure remains retained, and both stopped producer reports keep
their original statuses. The failed sandbox launch started no benchmark process.

The [final closure](independent-closure-v1.json) verifies the eight new captures,
their complete output files, 6,760 input pins, absence of all ten new worker,
controller and subject processes, and release of all fifteen leases.

This qualifies bounded output correctness only. Required-work observations,
updated counts for the corrected tree source, final runtime/source qualification,
and full-size timings remain pending. No benchmark timing samples are admitted
by these records.
