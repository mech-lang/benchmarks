# Bounded continuation outcome

The continuation completed 117 output contracts before stopping at
`revcomp:extended-invalid-space`. Together with the 23 preserved contracts from
the earlier run, 140 of the 149 corpus cases have passed the original checker.
All four corrected binary-tree cases passed. Eight cases were not started.

The invalid-input program exited normally with status 1, wrote no stdout, and
reported `Unsupported revcomp sequence byte`. Rebol enclosed that string in
double quotes; the checker had predicted an unquoted diagnostic. The original
producer remains failed. A subsequent [checker correction and separate capture
review](../quoted-rejection-v1/retained-rejection-review-v1.json) accepted the
saved rejection without rerunning it. There are now 141 accepted corpus cases;
the final eight still require execution.

The [independent closure](failed-stage-review-v1.json) replayed all 117 new and
23 prior output contracts, 6,146 input pins, 592 run artifacts and eight durable
job artifacts. All 120 processes and process groups from the new job were absent,
and all fourteen acquired leases were released. An earlier sandbox launch failed
at its process-identity check before starting the target command; its retained
request and worker error remain separate from the native run.

These are correctness observations, not benchmark timings. Required-work
observations, final source counts, full-size timing and chart admission remain
pending. Existing language measurements are unchanged.
